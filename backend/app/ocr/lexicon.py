"""Model bahasa ringan untuk menyaring hasil OCR (beam search per karakter).

Pengenalan per-aksara sering tertukar pada pasangan mirip (``na``/``da``/``ta``,
``wa``/``la``). Alih-alih mempercayai argmax per kotak, pipeline OCR menyimpan
*kandidat* tiap posisi lalu memilih rangkaian yang paling mungkin menurut model
n-gram karakter + kamus kata yang dibangun dari data repo sendiri
(``aksara_master.json``, ``dictionary.json``, materi & kuis) — jadi tidak perlu
korpus eksternal dan tetap bisa dipakai offline.

Ruang simbol:
• tugas aksara → urutan **label kelas** (``ha``, ``na``, ``ulu`` …)
• tugas latin  → urutan **huruf** (``a``…``z``, ``0``…``9``, spasi)
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_ALPHA = 0.35        # smoothing additif
_WORD_BONUS = 1.9    # bonus log-prob bila rangkaian membentuk kata/kamus dikenal
_MIN_COUNT = 1


def _iter_strings(obj) -> Iterable[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _iter_strings(v)


def _load_json(path: Path) -> dict | list:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):  # pragma: no cover - data rusak
        return {}


def _balinese_only(s: str) -> str:
    return "".join(ch for ch in s if 0x1B00 <= ord(ch) <= 0x1B7F)


class NgramLM:
    """Model bigram+trigram log-prob dengan backoff sederhana (diambil dari korpus)."""

    def __init__(self, counts: Optional[Dict] = None, total: int = 0, unigram: Optional[Dict] = None,
                 vocab: Optional[Sequence[str]] = None, words: Optional[Dict[str, int]] = None) -> None:
        self.bi: Dict[Tuple[str, str], float] = {}
        self.tri: Dict[Tuple[str, str, str], float] = {}
        self.uni: Dict[str, float] = {}
        self.ctx_bi: Dict[str, float] = {}
        self.ctx_tri: Dict[Tuple[str, str], float] = {}
        self.total = 0.0
        self.words: Dict[str, int] = words or {}
        self.vocab: List[str] = list(vocab or [])
        self._n = len(self.vocab) or 1
        if counts:
            self.fit(counts)

    def to_dict(self) -> Dict:
        j = lambda d: {"\x1f".join(k) if isinstance(k, tuple) else k: v for k, v in d.items()}
        return {"uni": self.uni, "bi": j(self.bi), "tri": j(self.tri),
                "ctx_bi": self.ctx_bi, "ctx_tri": j(self.ctx_tri), "total": self.total,
                "words": self.words, "vocab": self.vocab}

    @classmethod
    def from_dict(cls, d: Dict) -> "NgramLM":
        un = lambda dd, n: {tuple(k.split("\x1f")): v for k, v in (dd or {}).items()} if n > 1 else dict(dd or {})
        lm = cls(vocab=d.get("vocab"))
        lm.uni = dict(d.get("uni") or {})
        lm.bi = un(d.get("bi"), 2)
        lm.tri = un(d.get("tri"), 3)
        lm.ctx_bi = dict(d.get("ctx_bi") or {})
        lm.ctx_tri = un(d.get("ctx_tri"), 2)
        lm.total = float(d.get("total") or 0.0)
        lm.words = dict(d.get("words") or {})
        return lm

    def fit(self, sequences: Sequence[Sequence[str]]) -> None:
        for seq in sequences:
            toks = list(seq)
            for t in toks:
                self.uni[t] = self.uni.get(t, 0.0) + 1.0
                self.total += 1.0
            prev: List[Optional[str]] = [None, None]
            for t in toks:
                a, b = prev
                if b is not None:
                    self.bi[(b, t)] = self.bi.get((b, t), 0.0) + 1.0
                    self.ctx_bi[b] = self.ctx_bi.get(b, 0.0) + 1.0
                if a is not None and b is not None:
                    self.tri[(a, b, t)] = self.tri.get((a, b, t), 0.0) + 1.0
                    self.ctx_tri[(a, b)] = self.ctx_tri.get((a, b), 0.0) + 1.0
                prev = [b, t]
            # token penutup → mengajarkan "akhir kata"
            if toks:
                self.bi[(toks[-1], "</w>")] = self.bi.get((toks[-1], "</w>"), 0.0) + 1.0
                self.ctx_bi[toks[-1]] = self.ctx_bi.get(toks[-1], 0.0) + 1.0

    def logp(self, hist: Tuple[Optional[str], Optional[str], Optional[str]], tok: str) -> float:
        """log P(tok | a, b) dengan interpolasi trigram → bigram → unigram."""
        a, b, c = hist
        p_uni = (self.uni.get(tok, 0.0) + _ALPHA) / (self.total + _ALPHA * max(self._n, 1))
        score = p_uni
        if c is not None:
            den = self.ctx_bi.get(c, 0.0) + _ALPHA * max(self._n, 1)
            p_bi = (self.bi.get((c, tok), 0.0) + _ALPHA) / den
            score = 0.55 * p_bi + 0.45 * score
        if b is not None and c is not None:
            den = self.ctx_tri.get((b, c), 0.0) + _ALPHA * max(self._n, 1)
            p_tri = (self.tri.get((b, c, tok), 0.0) + _ALPHA) / den
            score = 0.5 * p_tri + 0.5 * score
        return math.log(max(score, 1e-9))

    def word_bonus(self, word: str) -> float:
        if not word:
            return 0.0
        c = self.words.get(word, 0)
        if c <= 0:
            return 0.0
        return _WORD_BONUS * (1.0 + 0.25 * math.log(1.0 + c))


_LM_CACHE: Dict[str, NgramLM] = {}


def _latin_corpus() -> List[str]:
    texts: List[str] = []
    for name in ("dictionary.json", "aksara_master.json", "lessons.json", "quiz.json", "docs.json",
                 "engagement.json", "lexicon_extra.json"):
        data = _load_json(DATA_DIR / name)
        for s in _iter_strings(data):
            clean = "".join(ch for ch in s.lower() if ch.isalpha() or ch.isspace())
            for word in clean.split():
                if 1 < len(word) <= 24 and word.isascii():
                    texts.append(word)
    return texts


def _balinese_corpus(code_to_label: Dict[int, str]) -> List[List[str]]:
    out: List[List[str]] = []
    for name in ("dictionary.json", "aksara_master.json", "lessons.json", "quiz.json"):
        data = _load_json(DATA_DIR / name)
        for s in _iter_strings(data):
            b = _balinese_only(s)
            if not b:
                continue
            seq = [code_to_label.get(ord(ch)) for ch in b]
            seq = [x for x in seq if x]
            if len(seq) >= 2:
                out.append(seq)
    return out


def build_latin_lm() -> NgramLM:
    words = _latin_corpus()
    lm = NgramLM(vocab=list("abcdefghijklmnopqrstuvwxyz0123456789 </w>"))
    lm.fit([list(w) for w in words])
    counts: Dict[str, int] = {}
    for w in words:
        # Kata 1–2 huruf di korpus repo kebanyakan romanisasi aksara ("ma", "na",
        # "am") — bukan kata Latin. Memasukkannya membuat bonus kamus menyulut
        # pada hasil OCR yang salah ("mm am ma" dianggap kata dikenal) dan
        # merusak pilihan skrip pada mode Otomatis.
        if len(w) < 3:
            continue
        counts[w] = counts.get(w, 0) + 1
    lm.words = counts
    return lm


def _latin_to_aksara_seqs(code_to_label: Dict[int, str], max_words: int = 900) -> List[List[str]]:
    """Terjemahkan kata Latin korpus repo ke aksara → urutan label.

    Menambah data LM secara signifikan (ratusan → ribuan urutan) sehingga urutan
    aksara yang tidak mungkin terjadi (mis. "sa sa sa sa") tertekan saat decoding.
    """
    from collections import Counter

    from ..services.transliterator import transliterate

    out: List[List[str]] = []
    for word, _cnt in Counter(_latin_corpus()).most_common(max_words):
        try:
            bali, _br, warns = transliterate(word, "latin-to-bali", True)
        except Exception:  # pragma: no cover - kamus/transliterasi rusak
            break
        if warns and not bali:
            continue
        seq = [code_to_label.get(ord(ch)) for ch in _balinese_only(bali)]
        seq = [x for x in seq if x]
        if 2 <= len(seq) <= 24:
            out.append(seq)
    return out


LM_CACHE_PATH = DATA_DIR / "ocr_lm_aksara.json"


def _corpus_stamp() -> float:
    names = ("dictionary.json", "aksara_master.json", "lessons.json", "quiz.json", "docs.json", "engagement.json")
    best = 0.0
    for name in names:
        f = DATA_DIR / name
        if f.is_file():
            best = max(best, f.stat().st_mtime)
    return best


def build_aksara_lm(labels: Sequence[str]) -> NgramLM:
    """LM atas urutan label kelas (bukan codepoint) — ruang simbol model klasifikasi."""
    # Relatif terhadap paket (bukan `app.ml` absolut) agar jalan baik saat proses
    # dijalankan sebagai `uvicorn app.main:app` (cwd=backend) MAUPUN
    # `uvicorn backend.app.main:app` (cwd=root repo). Import lokal supaya tidak
    # ada siklus saat pemuatan modul.
    from ..ml import store

    lookup = store.class_lookup("aksara")
    code_to_label = {ord(c["glyph"][0]): c["label"] for c in lookup.values() if c.get("glyph")}

    want = list(labels) + ["</w>"]
    if LM_CACHE_PATH.is_file():
        try:
            cached = json.loads(LM_CACHE_PATH.read_text(encoding="utf-8"))
            if (cached.get("labels") == want
                    and float(cached.get("stamp") or 0) >= _corpus_stamp() - 1e-9):
                return NgramLM.from_dict(cached["lm"])
        except (OSError, ValueError, KeyError):
            pass

    seqs = _balinese_corpus(code_to_label) + _latin_to_aksara_seqs(code_to_label)
    lm = NgramLM(vocab=want)
    lm.fit(seqs)
    # "kata" dalam ruang label, untuk bonus leksikon
    words: Dict[str, int] = {}
    for seq in seqs:
        key = "".join(seq)
        words[key] = words.get(key, 0) + 1
    lm.words = words
    try:
        LM_CACHE_PATH.write_text(json.dumps({"labels": want, "stamp": _corpus_stamp(), "lm": lm.to_dict()},
                                           ensure_ascii=False), encoding="utf-8")
    except OSError:  # pragma: no cover - cache bersifat opsional
        pass
    return lm


def get_lm(task: str, labels: Sequence[str]) -> NgramLM:
    key = f"{task}:{len(labels)}:{hash(tuple(labels)) & 0xffffffff}"
    lm = _LM_CACHE.get(key)
    if lm is None:
        lm = build_aksara_lm(labels) if task == "aksara" else build_latin_lm()
        _LM_CACHE[key] = lm
    return lm


def beam_decode(cands: Sequence[Sequence[Tuple[str, float]]], lm: NgramLM, *, width: int = 6,
                allow_space: bool = False, word_gap: float = 0.62,
                gaps: Optional[Sequence[float]] = None,
                breaks: Optional[Sequence[bool]] = None) -> Tuple[List[str], float]:
    """Beam search atas kandidat per posisi.

    ``cands[i]`` = daftar ``(label, prob)`` terurut menurun untuk posisi ``i``.
    Skor = jumlah log-prob model + log-prob LM (backoff) + bonus kamus per kata.

    Pemisah kata diambil dari ``breaks`` (keputusan segmentasi per baris, yang
    memakai ambang celah adaptif) bila diberikan; jika tidak, dihitung dari
    ``gaps`` terhadap ``word_gap`` — agar pemanggil lama tetap berjalan.
    """
    n = len(cands)
    if n == 0:
        return [], 0.0
    beams: List[Tuple[float, List[str]]] = [(0.0, [])]
    for i in range(n):
        if breaks is not None and i < len(breaks):
            space_here = bool(breaks[i])
        else:
            gap = float(gaps[i]) if gaps is not None and i < len(gaps) else 0.0
            space_here = gap >= word_gap
        space_before = allow_space and i > 0 and space_here
        nxt: List[Tuple[float, List[str]]] = []
        for score, seq in beams:
            starts = [seq + [" "]] if space_before else [seq]
            for base_seq in starts:
                for tok, prob in cands[i][:8]:
                    hist = (base_seq[-3] if len(base_seq) >= 3 else None,
                            base_seq[-2] if len(base_seq) >= 2 else None,
                            base_seq[-1] if base_seq else None)
                    if space_before:
                        hist = (None, None, None)
                    s = score + 0.55 * math.log(max(prob, 1e-6)) + 0.45 * lm.logp(hist, tok)
                    nxt.append((s, base_seq + [tok]))
        if not nxt:
            break
        nxt.sort(key=lambda x: x[0], reverse=True)
        beams = nxt[: width]
    # Bonus kamus dinilai ulang untuk SEMUA balok (bukan hanya yang terbaik),
    # karena rangkaian yang membentuk kata dikenal sering sedikit di belakang
    # secara akustik namun jauh lebih mungkin sebagai teks.
    ranked: List[Tuple[float, List[str]]] = []
    for score, seq in beams:
        total = score
        if lm.words:
            text = "".join(seq)
            words = [w for w in text.split() if w] if allow_space else [text]
            total += 0.12 * sum(lm.word_bonus(w) for w in words)
        ranked.append((total, seq))
    ranked.sort(key=lambda x: x[0], reverse=True)
    best_score, best_seq = ranked[0]
    return best_seq, round(best_score, 4)
