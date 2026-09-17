"""Pipeline OCR Lens — kamera → baris → aksara/huruf → teks → terjemahan.

Seluruhnya NumPy/Pillow + model yang sama dengan Panel Admin, jadi hasil
retraining admin langsung dipakai halaman ini. Tahapannya:

1. **Praproses** — dekode (EXIF) → grayscale → rentang kontras → ambang Sauvola →
   bersihkan derau → koreksi kemiringan.
2. **Segmentasi** — ``segment.segment``: baris → gugus komponen → satu kandidat per
   aksara; gugus yang tinggi dipecah menjadi badan + pangangge.
3. **Klasifikasi** — vektor fitur 28×28 tiap potongan → model ``deepcnn`` tugas
   ``aksara`` dan/atau ``latin`` (satu batch per tugas, TTA opsional), top-k disimpan.
4. **Pilihan skrip** — per baris: baris mana yang lebih diyakini model Bali vs model
   Latin; keputusan tetap per gugus sehingga baris campur tetap terbaca.
5. **Decoding** — beam search dengan n-gram + kamus repo (``lexicon``) menyaring
   pasangan mirip (na/da/ta, wa/la …).
6. **Rakitan & translasi** — label → Unicode (basis + pangangge / huruf + spasi),
   lalu transliterasi dua arah oleh mesin proyek + glossarium ``dictionary.json``.

Struktur keluaran dibuat agar frontend bisa menggambar overlay (kotak per aksara,
keyakinan, daftar kandidat untuk koreksi manusia).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..ml import features, inference, store
from . import imageops, lexicon, segment

MARK_GROUPS = {"pangangge_suara", "pangangge_tengenan", "pangangge_aksara"}

#: kunci tinta utuh satu gugus / satu belahan pada matriks klasifikasi
WHOLE_KEY = 50
PIECE_WHOLE_KEY = 150


@dataclass
class ScanOptions:
    script: str = "auto"             # auto | aksara | latin
    tta: int = 2                     # jumlah transformasi test-time augmentation
    beam_width: int = 6
    use_language_model: bool = True
    deskew: bool = True
    binarize: str = "sauvola"        # sauvola | otsu | fixed
    sauvola_window: int = 25
    sauvola_k: float = 0.12
    invert: str = "auto"             # auto | dark-ink | light-ink
    min_area: int = 6
    min_height: int = 7
    close_iters: int = 1        # menjembatani goresan putus (penting untuk tinta nyata)
    merge_gap_ratio: float = 0.34
    word_gap_ratio: float = 0.62
    max_glyphs: int = 480
    split_marks: bool = True
    top_k: int = 5
    split_width_ratio: float = 1.25   # gugus selebar ini × tinggi baris dicoba dibelah
    split_valley_ratio: float = 0.8   # kedalaman lembah kolom (× median) untuk membelah
    resplit_below: float = 0.62       # keyakinan gugus utuh di bawah ini → pakai belahan
    with_crops: bool = False          # sertakan PNG kecil tiap aksara (inspector)
    upscale_small: bool = True        # teks kecil diperbesar dulu (ketebalan goresan)
    target_line_height: int = 30      # tinggi baris target (px) untuk upscale
    script_margin: float = 0.85       # pilih Bali bila skornya ≥ margin × skor Latin
    line_min_ink: float = 0.012       # kepadatan tinta minimum sebuah baris (0..1)
    max_side: int = 2400              # sisi terpanjang yang diproses (foto hp diperkecil dulu)

    #: (nama, minimum, maksimum) — nilai dari API selalu dijepit ke rentang aman
    _RANGE = {
        "tta": (0, 12), "beam_width": (1, 64), "sauvola_window": (8, 200), "sauvola_k": (0.0, 1.0),
        "min_area": (0, 500), "min_height": (2, 60), "close_iters": (0, 4), "merge_gap_ratio": (0.0, 1.0),
        "word_gap_ratio": (0.1, 2.0), "max_glyphs": (4, 2000), "top_k": (1, 10),
        "split_width_ratio": (0.8, 4.0), "split_valley_ratio": (0.05, 0.6),
        "resplit_below": (0.0, 1.0), "target_line_height": (12, 200),
        "script_margin": (0.0, 2.0), "line_min_ink": (0.0, 0.2), "max_side": (200, 4000),
    }
    _CHOICES = {"script": ("auto", "aksara", "latin"), "binarize": ("sauvola", "otsu", "fixed"),
                "invert": ("auto", "dark-ink", "light-ink")}

    @classmethod
    def from_dict(cls, d: Optional[dict]) -> "ScanOptions":
        """Bangun opsi dari dict API (tipe ditebak dari nilai default, angka asing dijepit)."""
        if not d:
            return cls()
        clean: dict = {}
        for k, v in d.items():
            if k not in cls.__dataclass_fields__ or v is None:
                continue
            default = cls.__dataclass_fields__[k].default
            choices = cls._CHOICES.get(k)
            if choices:
                sv = str(v).strip().lower()
                sv = {"dark": "dark-ink", "light": "light-ink"}.get(sv, sv)
                if sv in choices:
                    clean[k] = sv
                continue
            try:
                if isinstance(default, bool):
                    if isinstance(v, str):
                        sv = v.strip().lower()
                        if sv in ("false", "0", "no", "off", "mati"):
                            clean[k] = False
                            continue
                        if sv in ("true", "1", "yes", "on", "hidup"):
                            clean[k] = True
                            continue
                        continue
                    clean[k] = bool(v)
                elif isinstance(default, int):
                    clean[k] = int(float(v))
                elif isinstance(default, float):
                    clean[k] = float(v)
                else:  # pragma: no cover - semua field bertipe dasar
                    clean[k] = v
            except (TypeError, ValueError):
                continue
        opts = cls(**clean)
        for k, (lo, hi) in cls._RANGE.items():
            val = getattr(opts, k)
            cast = int if isinstance(lo, int) else float
            setattr(opts, k, cast(max(lo, min(hi, val))))
        return opts


def mark_labels(task: str = "aksara") -> set:
    return {lab for lab, c in store.class_lookup(task).items() if c.get("group") in MARK_GROUPS}


# ── praproses ──────────────────────────────────────────────────────────────

def preprocess(data: bytes, opts: ScanOptions) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """bytes → (biner 1=tinta, grayscale, info diagnostik)."""
    gray = imageops.decode_gray(data, max_side=int(opts.max_side))
    # σ derau diukur SEKALI pada skala asli: rotasi & terutama pembesaran
    # (``upscale_small``) menghaluskan derau sehingga estimasi ulang secara keliru
    # mematikan peredam derau dan latar kembali penuh tinta palsu.
    sigma = imageops.estimate_noise(imageops.stretch_contrast(gray))
    if sigma >= 2.4:
        info_noise: Dict[str, float] = {"noise_sigma": round(float(sigma), 2)}
    else:
        info_noise = {}
    binary = imageops.binarize(gray, opts.binarize, window=int(opts.sauvola_window),
                              k=float(opts.sauvola_k), invert=opts.invert, sigma=sigma)
    info = {"size": [int(gray.shape[1]), int(gray.shape[0])], "ink_ratio": round(float(binary.mean()), 4),
            **info_noise}
    if opts.deskew and binary.shape[0] > 24:
        angle = imageops.estimate_skew(binary, max_angle=7.0, step=0.5)
        info["deskew_angle"] = round(float(angle), 2)
        # Kecil dari 1° tidak berarti bagi OCR, tetapi rotasinya meninggalkan wedge
        # lancip di sudut — batas tajam itu dilukis Sauvola sebagai pita tinta padat
        # (→ baris "teks" sampah). Wedge diisi abu latar median, bukan putih, supaya
        # tidak ada tepi kontras sama sekali.
        if abs(angle) >= 1.0:
            border = np.concatenate([gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1]])
            gray = imageops.rotate(gray, angle, fill=float(np.median(border)))
            binary = imageops.binarize(gray, opts.binarize, window=int(opts.sauvola_window),
                                      k=float(opts.sauvola_k), invert=opts.invert, sigma=sigma)
            info["ink_ratio_after"] = round(float(binary.mean()), 4)
    # Tulisan kecil → goresan 1-2 px, model (yang dilatih pada glyph ~20 px) kehilangan
    # detail. Bila tinggi baris median di bawah target, perbesar dulu seluruh kanvas.
    if opts.upscale_small:
        bands = segment.find_lines(binary, min_height=int(opts.min_height),
                                   min_ink=float(opts.line_min_ink))
        heights = [b - a for a, b in bands]
        med = float(np.median(heights)) if heights else 0.0
        if 4.0 < med < float(opts.target_line_height):
            factor = min(4.0, float(opts.target_line_height) / med)
            info["upscale"] = round(factor, 2)
            gray = imageops.scale(gray, factor)
            binary = imageops.binarize(gray, opts.binarize, window=max(9, int(opts.sauvola_window * factor)),
                                      k=float(opts.sauvola_k), invert=opts.invert, sigma=sigma)
            info["ink_ratio_up"] = round(float(binary.mean()), 4)
    return binary, gray, info


def _model_row(task: str, model_id: Optional[str]) -> Tuple[Optional[str], Optional[Dict]]:
    try:
        mid = inference.resolve_model_id(model_id, task)
    except LookupError:
        return None, None
    entry = store.get_model_entry(mid, task)
    return (mid, entry) if entry else (None, None)


def _classify(X: np.ndarray, task: str, model_id: Optional[str], tta: int) -> np.ndarray:
    """Semua potongan sekaligus → matriks probabilitas N×C untuk satu tugas."""
    mid = inference.resolve_model_id(model_id, task)
    model = inference.load_model(mid, task)
    if tta:
        try:
            return model.predict_proba(X, tta=int(tta))
        except TypeError:  # arsitektur tanpa dukungan TTA
            return model.predict_proba(X)
    return model.predict_proba(X)


def _model_info(task: str, model_id: Optional[str] = None) -> Optional[Dict]:
    mid, entry = _model_row(task, model_id)
    if not entry:
        return None
    m = entry.get("metrics") or {}
    return {
        "task": task, "model_id": mid, "name": entry.get("name"), "arch": entry.get("arch"),
        "arch_name": entry.get("arch_name"), "n_classes": entry.get("n_classes"),
        "accuracy": m.get("accuracy"), "macro_f1": m.get("macro_f1"),
        "created_at": entry.get("created_at"), "bundled": bool(entry.get("bundled")),
    }


def gloss_latin(text: str) -> List[Dict]:
    """Cocokkan kata hasil OCR Latin dengan kamus proyek (meaning/note)."""
    out: List[Dict] = []
    try:
        from ..services.data_store import get_dictionary

        items = get_dictionary() or {}
    except Exception:  # pragma: no cover - kamus opsional
        return out
    seen = set()
    for word in "".join(ch if ch.isalnum() else " " for ch in (text or "").lower()).split():
        hit = items.get(word) if isinstance(items, dict) else None
        if hit and word not in seen:
            seen.add(word)
            out.append({"word": word, "bali": hit.get("bali", ""), "meaning": hit.get("meaning", ""),
                        "note": hit.get("note", "")})
    return out


# ── utama ─────────────────────────────────────────────────────────────────

def scan_bytes(data: bytes, options: Optional[dict] = None, model_ids: Optional[Dict[str, str]] = None,
               raw_options: Optional[dict] = None) -> Dict:
    t0 = time.time()
    opts = ScanOptions.from_dict(options)
    # Huruf Latin (cetak maupun tulis) tidak punya goresan putus seperti aksara
    # tarikan tangan; morfologi penutup justru melebur huruf yang bersebelahan rapat
    # ("om" → satu gugus) pada teks kamera berukuran kecil. Matikan bawaannya untuk
    # mode latin — override eksplisit dari klien tetap dihormati. Begitu pula ambang
    # pakai-belahan: gugus Latin yang melebur buram jarang meyakinkan, jadi belahan
    # dipakai lebih agresif (0,9); untuk Aksara 0,62 tetap terbaik (belahan sembarang
    # memecah aksara berangkai dan justru menaikkan CER — diuji lewat selftest).
    raw = raw_options if raw_options is not None else (options or {})
    if opts.script == "latin":
        if "close_iters" not in (raw or {}):
            opts.close_iters = 0
        if "resplit_below" not in (raw or {}):
            opts.resplit_below = 0.9
    model_ids = dict(model_ids or {})
    warnings: List[str] = []

    binary, _gray, pinfo = preprocess(data, opts)
    H, W = binary.shape
    lines_seg = segment.segment(
        binary, merge_gap_ratio=float(opts.merge_gap_ratio), word_gap_ratio=float(opts.word_gap_ratio),
        min_height=int(opts.min_height), min_area=int(opts.min_area), close_iters=int(opts.close_iters),
        split_marks=bool(opts.split_marks), split_width_ratio=float(opts.split_width_ratio),
        min_ink=float(opts.line_min_ink), split_valley_ratio=float(opts.split_valley_ratio),
    )
    if not lines_seg:
        return {
            "lines": [], "text": {"aksara": "", "latin": "", "all": ""}, "detected_script": "unknown",
            "warnings": ["Tidak ada teks terdeteksi. Perbesar objek, tambahkan cahaya, dan pegang kamera "
                         "tegak lurus pada bidang tulis."],
            "stats": {"elapsed_ms": int((time.time() - t0) * 1000), "lines": 0, "glyphs": 0, **pinfo},
            "models": [], "options": vars(opts),
        }

    # (baris, gugus, indeks potongan):
    #   0..9        = bagian gugus (0 = badan, sisanya pangangge)
    #   WHOLE       = tinta gugus UTUH (satu huruf Latin: titik i/j & silang t/f ikut)
    #   100+10j+k   = bagian belahan ke-j
    #   PIECE_WHOLE = tinta utuh belahan ke-j
    refs: List[Tuple[int, int, int]] = []
    inks: List[np.ndarray] = []

    def usable(part) -> bool:
        return part is not None and part.ink is not None and part.ink.size >= 9 and float(part.ink.sum()) >= 4

    for li, ln in enumerate(lines_seg):
        for gi, g in enumerate(ln.glyphs):
            if usable(g.whole):
                refs.append((li, gi, WHOLE_KEY))
                inks.append(g.whole.ink)
            for pi, part in enumerate(g.parts[:10]):
                if usable(part):
                    refs.append((li, gi, pi))
                    inks.append(part.ink)
            for j, piece in enumerate(g.pieces):
                pw = g.piece_wholes[j] if j < len(g.piece_wholes) else None
                if usable(pw):
                    refs.append((li, gi, PIECE_WHOLE_KEY + 10 * j))
                    inks.append(pw.ink)
                for k, part in enumerate(piece[:10]):
                    if usable(part):
                        refs.append((li, gi, 100 + 10 * j + k))
                        inks.append(part.ink)
    if len(refs) > opts.max_glyphs:
        warnings.append(f"{len(refs)} potongan terpotong menjadi {opts.max_glyphs} — persempit area bidik.")
        refs, inks = refs[: opts.max_glyphs], inks[: opts.max_glyphs]
    if not refs:
        return {"lines": [], "text": {"aksara": "", "latin": "", "all": ""}, "detected_script": "unknown",
                "warnings": ["Kandidat tinta tidak cukup untuk dikenali."],
                "stats": {"elapsed_ms": int((time.time() - t0) * 1000), "lines": len(lines_seg),
                          "glyphs": 0, **pinfo},
                "models": [], "options": vars(opts)}

    wanted = {"aksara", "latin"} if opts.script == "auto" else {opts.script}
    tasks = [t for t in ("aksara", "latin") if t in wanted and _model_row(t, model_ids.get(t))[1] is not None]
    if not tasks:
        raise LookupError(
            "Model OCR belum siap. Buka Panel Admin → Model ML, impor dataset repo lalu latih model "
            "(tugas Aksara Bali / Latin) dan tetapkan sebagai produksi."
        )

    X = np.stack([features.features_from_ink(ink) for ink in inks]).astype(np.float32)
    rows: Dict[Tuple[int, int, int], Dict[str, np.ndarray]] = {}
    for task in tasks:
        try:
            P = _classify(X, task, model_ids.get(task), opts.tta)
        except Exception as exc:  # pragma: no cover - model rusak
            warnings.append(f"Model tugas '{task}' gagal dipakai: {exc}")
            continue
        for k, key in enumerate(refs):
            rows.setdefault(key, {})[task] = P[k]
    tasks = [t for t in tasks if all(t in rows.get(key, {}) for key in refs)]
    if not tasks:
        raise LookupError("Tidak ada model OCR yang dapat memproses gambar ini.")

    labels = {t: store.class_labels(t) for t in tasks}
    lookup = {t: store.class_lookup(t) for t in tasks}
    marks = {t: mark_labels(t) for t in tasks}

    # ── pilih skrip per baris (badan aksara saja) ─────────────────────────
    line_scores: List[Dict[str, float]] = []
    for li, ln in enumerate(lines_seg):
        sc: Dict[str, List[float]] = {t: [] for t in tasks}
        for gi, _g in enumerate(ln.glyphs):
            for t in tasks:
                # bukti terbaik per gugus: badan saja (cara Aksara dibaca) ATAU
                # gugus utuh (cara huruf Latin dibaca, titik/silang termasuk).
                best = max([float(rows[(li, gi, k)][t].max())
                            for k in (0, WHOLE_KEY)
                            if t in rows.get((li, gi, k), {})] or [0.0])
                if best:
                    sc[t].append(best)
        line_scores.append({t: float(np.mean(v)) if v else 0.0 for t, v in sc.items()})

    def decode_line(li: int, ln, pick: str) -> Tuple[Dict, float, Dict]:
        """Dekode SATU baris sebagai skrip ``pick`` → (hasil, skor bukti, rincian).

        Mode ``auto`` memanggil fungsi ini untuk tiap skrip yang modelnya siap,
        lalu memilih baris dengan skor bukti tertinggi. Skor menggabungkan tiga
        hal yang saling menutupi kelemahannya:

        * keyakinan akustik rata-rata (label terpilih),
        * skor model bahasa per posisi (rangkaian yang tidak mungkin dalam
          bahasa/Bali ditekan), dan
        * bukti geometri/leksikon: gugus badan+pangangge (khas Aksara) dan
          kata yang dikenal kamus (khas Latin).
        """
        lbls, look = labels[pick], lookup[pick]

        g_whole_box: List[Optional[object]] = [None]   # tinta utuh glyph aktif (untuk crop)

        def entry_for(gi: int, parts_list, key_base: int, box, gap, word_break,
                      whole_key: Optional[int] = None):
            """Satu keluaran glyph: kandidat aksara dasar + pangangge pada gugus/belahan.

            ``key_base`` menunjuk BADAN (untuk Aksara: badan + pangangge di
            ``key_base+1..``). Bila skrip baris adalah Latin dan tinta utuh
            tersedia (``whole_key``), huruf dinilai dari gugus UTUH karena titik
            i/j dan silang t/f adalah bagian huruf, bukan tanda terpisah.
            """
            base_key = key_base
            if pick == "latin" and whole_key is not None:
                rw = rows.get((li, gi, whole_key))
                if rw and pick in rw:
                    base_key = whole_key
            r = rows.get((li, gi, base_key))
            if not r or pick not in r:
                return None
            P = r[pick]
            order = np.argsort(-P)[: max(1, int(opts.top_k))]
            cands_g = [(lbls[int(i)], float(P[int(i)])) for i in order]
            out = {
                "index": gi,
                "box": [int(v) for v in box],
                "gap_before": round(float(gap), 3),
                "word_break": bool(word_break),
                "split": key_base >= 100,
                "alternatives": [
                    {"label": l, "probability": round(pr, 4), "glyph": look.get(l, {}).get("glyph", ""),
                     "name": look.get(l, {}).get("name", l), "latin": look.get(l, {}).get("latin", "")}
                    for l, pr in cands_g
                ],
                "marks": [],
            }
            if opts.with_crops and parts_list:
                crop_part = (g_whole_box[0] if (base_key == whole_key and g_whole_box[0] is not None)
                             else parts_list[0])
                out["crop"] = features.png_data_url(crop_part.ink, scale=3)
            if pick == "aksara":
                for pi, part in enumerate(parts_list):
                    if pi == 0:
                        continue
                    rr = rows.get((li, gi, key_base + pi))
                    if not rr or pick not in rr:
                        continue
                    MP = rr[pick]
                    mi = int(np.argmax(MP))
                    lab = lbls[mi]
                    if lab not in marks[pick]:
                        continue
                    out["marks"].append({
                        "role": part.role, "label": lab, "glyph": look[lab]["glyph"],
                        "name": look[lab].get("name", lab), "latin": look[lab].get("latin", ""),
                        "probability": round(float(MP[mi]), 4),
                        "box": [int(part.box[0]), int(part.box[1]), int(part.box[2]), int(part.box[3])],
                    })
            return cands_g, out

        cands: List[List[Tuple[str, float]]] = []
        gaps: List[float] = []
        glyphs_out: List[Dict] = []
        for gi, g in enumerate(ln.glyphs):
            g_whole_box[0] = g.whole
            r = rows.get((li, gi, WHOLE_KEY if pick == "latin" else 0)) \
                or rows.get((li, gi, 0)) or rows.get((li, gi, WHOLE_KEY))
            if r is None:
                continue
            whole_conf = max(float(r[t_].max()) for t_ in r)
            if g.pieces and whole_conf < float(opts.resplit_below):
                for j, piece in enumerate(g.pieces):
                    pxs = [p_.box for p_ in piece]
                    box = (min(b[0] for b in pxs), min(b[1] for b in pxs),
                           max(b[2] for b in pxs), max(b[3] for b in pxs))
                    res = entry_for(gi, piece, 100 + 10 * j, box,
                                    g.gap_before if j == 0 else 0.04, g.word_break and j == 0,
                                    whole_key=PIECE_WHOLE_KEY + 10 * j)
                    if res:
                        cands.append(res[0])
                        gaps.append(float(g.gap_before if j == 0 else 0.04))
                        glyphs_out.append(res[1])
                if any(x["index"] == gi for x in glyphs_out):
                    continue
            res = entry_for(gi, g.parts, 0, g.box, g.gap_before, g.word_break, whole_key=WHOLE_KEY)
            if res:
                cands.append(res[0])
                gaps.append(float(g.gap_before))
                glyphs_out.append(res[1])

        if not cands:
            return ({"index": li, "y": [int(ln.y0), int(ln.y1)], "height": round(ln.height, 1),
                     "script": pick, "text": "", "glyphs": [], "confidence": 0.0,
                     "scores": line_scores[li]}, -1e9, {"empty": True})

        # ── decoding dengan model bahasa ─────────────────────────────────
        lm = lexicon.get_lm(pick, lbls) if opts.use_language_model else None
        if lm is not None:
            # Pemisah kata diserahkan ke segmentasi (ambang adaptif per baris),
            # bukan dihitung ulang dari rasio global yang tidak cocok semua font.
            seq, lm_score = lexicon.beam_decode(cands, lm, width=int(opts.beam_width),
                                                allow_space=(pick == "latin"),
                                                word_gap=float(ln.word_gap or opts.word_gap_ratio),
                                                gaps=gaps, breaks=[g["word_break"] for g in glyphs_out])
        else:
            seq, lm_score = [c[0][0] for c in cands], 0.0

        # Rakit teks. PENTING: `seq` dari beam decode berisi TOKEN SPASI tambahan,
        # jadi indeksnya tidak sejajar dengan `glyphs_out`/`cands`. Dulu posisi
        # glyph diambil dari indeks seq sehingga setiap kata yang diberi spasi
        # menggeser label & keyakinan semua glyph sesudahnya ("read the palm leaf"
        # → "read  th e pa lm leaf", keyakinan 0%). Sekarang penghitung glyph
        # terpisah dan spasi hanya disisipkan sekali.
        text_chars: List[str] = []
        pos = 0
        for lab in seq:
            if lab == " ":
                if text_chars and text_chars[-1] != " ":
                    text_chars.append(" ")
                continue
            g = glyphs_out[pos] if pos < len(glyphs_out) else None
            cand = cands[pos] if pos < len(cands) else []
            pos += 1
            info = look.get(lab, {})
            if pick == "latin":
                if g is not None and g["word_break"] and text_chars and text_chars[-1] != " ":
                    text_chars.append(" ")   # spasi geometri bila LM melewatkannya
                text_chars.append(info.get("glyph", lab))
            else:
                if g is not None and g["word_break"] and text_chars and text_chars[-1] != " ":
                    text_chars.append(" ")   # spasi antar kata Aksara (dari celah geometri)
                mark_glyphs = [m["glyph"] for m in g["marks"]] if g is not None else []
                text_chars.append(info.get("glyph", "") + "".join(mark_glyphs))
            if g is not None:
                g["label"] = lab
                g["glyph"] = info.get("glyph", "")
                g["name"] = info.get("name", lab)
                g["latin"] = info.get("latin", "")
                g["confidence"] = round(float(dict(cand).get(lab, 0.0)), 4)
                g["corrected"] = bool(cand and cand[0][0] != lab)
        text = "".join(text_chars).strip()
        confs = [g["confidence"] for g in glyphs_out if "confidence" in g]
        for g in glyphs_out:
            b = g["box"]
            g["rect"] = [round(b[0] / W, 5), round(b[1] / H, 5), round((b[2] - b[0]) / W, 5),
                         round((b[3] - b[1]) / H, 5)]
            for m in g["marks"]:
                mb = m["box"]
                m["rect"] = [round(mb[0] / W, 5), round(mb[1] / H, 5), round((mb[2] - mb[0]) / W, 5),
                             round((mb[3] - mb[1]) / H, 5)]
        mean_conf = round(float(np.mean(confs)) if confs else 0.0, 4)
        n_pos = max(1, len(cands))
        lm_per = lm_score / n_pos
        score = mean_conf + 0.25 * lm_per
        detail: Dict[str, float] = {"conf": mean_conf, "lm": round(lm_per, 4)}
        if pick == "aksara":
            # Bukti khas tulisan Bali: banyak gugus berisi >1 potongan (badan +
            # pangangge). Huruf Latin hanya sesekali (titik i/j), jadi rasio kecil
            # sudah cukup. Ditambah bonus bila rangkaian labelnya kata dikenal.
            multi = sum(1 for g in ln.glyphs if len(g.parts) > 1)
            ratio = multi / max(1, len(ln.glyphs))
            geo = 0.12 * min(1.0, ratio / 0.22)
            known = 1.0 if (lm is not None and lm.words.get("".join(seq))) else 0.0
            score += geo + 0.10 * known
            detail.update({"geo": round(geo, 4), "known": known})
        else:
            words = [w for w in text.split() if w]
            hit = sum(1 for w in words if lm is not None and lm.words.get(w))
            ratio = hit / max(1, len(words)) if words else 0.0
            lex = 0.20 * ratio - (0.08 if words and hit == 0 else 0.0)
            score += lex
            detail.update({"lex": round(lex, 4), "words": len(words), "hits": hit})
        out = {
            "index": li, "y": [int(ln.y0), int(ln.y1)], "height": round(ln.height, 1),
            "script": pick, "text": text,
            "confidence": mean_conf,
            "lm_score": lm_score, "scores": {t: round(v, 4) for t, v in line_scores[li].items()},
            "script_evidence": detail,
            "glyphs": glyphs_out,
        }
        return out, score, detail

    results: List[Dict] = []
    for li, ln in enumerate(lines_seg):
        picks = [opts.script] if (opts.script != "auto" and opts.script in tasks) else list(tasks)
        best: Optional[Tuple[Dict, float]] = None
        for p in picks:
            out, score, _detail = decode_line(li, ln, p)
            if best is None or score > best[1]:
                best = (out, score)
        if best is not None:
            results.append(best[0])

    results = [r for r in results if r.get("text")]

    # Singkirkan "baris sampah bingkai" — sisa bayangan/bingkai foto di tepi gambar
    # yang lolos ke hasil sebagai 1–6 gugus mungil tanpa kata bermakna. SEMUA syarat
    # harus terpenuhi sekaligus (tepi bingkai + sangat pendek + rendah + tanpa kata
    # kamus + keyakinan rendah) supaya baris teks asli tidak pernah tersapu.
    def _garis_sampah_bingkai(r: Dict) -> bool:
        y0, y1 = r["y"]
        boxes = [g["box"] for g in r["glyphs"]] if r.get("glyphs") else []
        tepi = y0 <= 4 or (binary is not None and y1 >= binary.shape[0] - 4) or \
            any((b[0] <= 3 or (binary is not None and b[2] >= binary.shape[1] - 3)) for b in boxes)
        pendek = r["height"] <= 12 and len(r["glyphs"]) <= 6
        rendah = r["confidence"] <= 0.75
        hits = r.get("script_evidence", {}).get("hits", 0)
        return bool(tepi and pendek and rendah and hits == 0)

    results = [r for r in results if not _garis_sampah_bingkai(r)]
    aksara_text = "\n".join(r["text"] for r in results if r["script"] == "aksara")
    latin_text = "\n".join(r["text"] for r in results if r["script"] == "latin")
    detected = "aksara" if (aksara_text and len(aksara_text) >= len(latin_text)) else (
        "latin" if latin_text else "unknown")

    translation: Dict[str, Dict] = {}
    try:
        from ..services.transliterator import transliterate

        if aksara_text:
            res, breakdown, warns = transliterate(aksara_text.replace("\n", " "), "bali-to-latin", True)
            translation["bali_to_latin"] = {"source": aksara_text.replace("\n", " "), "result": res,
                                            "direction": "bali-to-latin", "warnings": warns,
                                            "breakdown": list(breakdown[:120])}
        if latin_text:
            res, breakdown, warns = transliterate(latin_text.replace("\n", " "), "latin-to-bali", True)
            translation["latin_to_bali"] = {"source": latin_text.replace("\n", " "), "result": res,
                                            "direction": "latin-to-bali", "warnings": warns,
                                            "breakdown": list(breakdown[:120])}
    except Exception as exc:  # pragma: no cover - transliterasi tidak mematahkan OCR
        warnings.append(f"Transliterasi gagal: {exc}")

    # Arti kata: kamus proyek dicocokkan ke teks Latin. Untuk halaman beraksara,
    # yang dipakai adalah hasil transliterasi — jadi "arti kata" tetap muncul meski
    # tidak ada satu pun baris Latin pada citra.
    gloss_src = latin_text or (translation.get("bali_to_latin") or {}).get("result", "")

    total_glyphs = sum(len(r["glyphs"]) for r in results)
    confs_all = [g["confidence"] for r in results for g in r["glyphs"] if "confidence" in g]
    avg_conf = float(np.mean(confs_all)) if confs_all else 0.0
    if total_glyphs and avg_conf < 0.55:
        warnings.append("Keyakinan rata-rata rendah — coba lebih dekat, fokus lebih tajam, cahaya merata.")

    return {
        "lines": results,
        "text": {"aksara": aksara_text, "latin": latin_text, "all": "\n".join(
            r["text"] for r in results if r["text"])},
        "detected_script": detected,
        "translation": translation,
        "glossary": gloss_latin(gloss_src),
        "models": [_model_info(t, model_ids.get(t)) for t in tasks],
        "stats": {
            "elapsed_ms": int((time.time() - t0) * 1000), "lines": len(results),
            "glyphs": total_glyphs, "mean_confidence": round(avg_conf, 4), "tasks": tasks,
            "tta": int(opts.tta), "language_model": bool(opts.use_language_model), **pinfo,
        },
        "warnings": warnings,
        "options": vars(opts),
    }


def crop_glyph(data: bytes, box: Sequence[int], pad: int = 2) -> bytes:
    """Potong wilayah (x0,y0,x1,y1) dari gambar asli → PNG (untuk umpan balik koreksi)."""
    from PIL import Image
    import io

    img = Image.open(io.BytesIO(data)).convert("L")
    W, H = img.size
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(W, x1 + pad), min(H, y1 + pad)
    if x1 <= x0 or y1 <= y0:
        raise ValueError("Kotak koreksi berada di luar gambar.")
    out = io.BytesIO()
    img.crop((x0, y0, x1, y1)).save(out, format="PNG")
    return out.getvalue()
