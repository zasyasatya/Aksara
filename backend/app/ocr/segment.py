"""Segmentasi baris teks & aksara/huruf pada citra biner (OCR Lens).

Strategi (klasik, transparan, bisa dibetulkan manusia — bukan kotak hitam):

1. **Baris** — profil proyeksi horizontal: kelompokkan baris ber-tinta, gabarkan
   pita yang terbelah oleh ascender/descender, lalu belah pita yang terlalu tinggi
   pada lembah paling tipis.
2. **Gugus (cluster)** — komponen terhubung pada satu baris digabung bila
   tumpang tindih/berdekatan secara horizontal; ini menyatukan aksara dasar dengan
   pangangge-nya (ulu di atas, pepet di bawah, gantungan di bawah).
3. **Aksara** — tiap gugus menjadi satu kandidat. Bila gugus jauh lebih tinggi dari
   median baris, bagian atas/bawah yang terpisah oleh baris "tipis" dilepas sebagai
   *pangangge* sehingga bentuk dasar tetap dikenali model (model dilatih pada
   bentuk tunggal, bukan gabungan).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from . import imageops


@dataclass
class Part:
    """Satu potongan tinta dalam sebuah gugus (basis atau pangangge)."""

    ink: np.ndarray            # maska float32 [0,1] siap kelasifikasi
    box: Tuple[int, int, int, int]  # x0, y0, x1, y1 pada koordinat citra
    role: str = "body"         # body | above | below


@dataclass
class Glyph:
    """Satu satuan baca (gugus komponen) pada suatu baris."""

    parts: List[Part]
    box: Tuple[int, int, int, int]
    pieces: List[List[Part]] = field(default_factory=list)  # alternatif belah horizontal
    whole: Optional[Part] = None               # tinta gugus utuh (belum dipecah badan/tanda)
    piece_wholes: List[Part] = field(default_factory=list)  # tinta utuh tiap belahan
    index: int = 0
    gap_before: float = 0.0    # celah horizontal ke gugus sebelumnya / tinggi baris
    word_break: bool = False
    char: str = ""
    label: str = ""
    confidence: float = 0.0
    alternatives: List[dict] = field(default_factory=list)
    script: str = ""
    mark_char: str = ""
    mark_label: str = ""

    @property
    def body(self) -> Part:
        for p in self.parts:
            if p.role == "body":
                return p
        return self.parts[0]


@dataclass
class Line:
    index: int
    y0: int
    y1: int
    height: float
    glyphs: List[Glyph] = field(default_factory=list)
    word_gap: float = 0.62         # ambang celah (× tinggi baris) yang dipakai baris ini

    @property
    def text(self) -> str:
        return "".join(((" " if g.word_break else "") + (g.char or "")) for g in self.glyphs)


def word_gap_threshold(glyphs: List[Glyph], word_gap_ratio: float) -> float:
    """Ambang celah antar kata untuk SATU baris (dalam satuan tinggi baris).

    Rasio baku (``word_gap_ratio``) dikalibrasi pada teks ber-spasi lebar. Pada
    font/ukuran tertentu spasi hanya ~0,5× tinggi baris sehingga tidak pernah
    terdeteksi dan seluruh baris dibaca sebagai satu kata ("heloworlk"). Karena
    itu, bila pada baris ini ada lompatan jelas antara celah "dalam kata" dan
    celah "antar kata" (≥ 1,55× dan ≥ 0,34× tinggi baris), ambang diturunkan ke
    titik tengah lompatan tersebut — pemisah alami milik baris itu sendiri.
    """
    thr = float(word_gap_ratio)
    inner = sorted(g.gap_before for g in glyphs[1:])
    if len(inner) < 3:
        return thr
    # Cari lompatan terbesar pada deret celah terurut: di bawahnya celah "dalam
    # kata", di atasnya celah "antar kata". Ambang ditaruh di tengah lompatan.
    best_i, best_ratio = -1, 0.0
    for i in range(len(inner) - 1):
        lo, hi = inner[i], inner[i + 1]
        if hi < 0.30:
            continue                      # keduanya masih celah dalam kata
        ratio = hi / max(lo, 0.06)
        if ratio > best_ratio:
            best_ratio, best_i = ratio, i
    if best_i >= 0 and best_ratio >= 1.55 and inner[best_i + 1] >= 0.34:
        thr = min(thr, max(0.32, 0.5 * (inner[best_i] + inner[best_i + 1])))
    return thr


def find_lines(binary: np.ndarray, min_height: int = 6, merge_ratio: float = 0.55,
               split_ratio: float = 2.3, min_ink: float = 0.012) -> List[Tuple[int, int]]:
    """Pita baris ``(y0, y1)`` dari profil horizontal (eksklusif di y1)."""
    h = binary.shape[0]
    rows = binary.sum(axis=1)
    bands = imageops.group_indices(rows > 0, max_gap=1, min_len=min_height)
    if not bands:
        return []
    heights = [b - a for a, b in bands]
    med = float(np.median(heights))
    # gabungkan pita yang berjarak dekat (ascender/descender memotong baris)
    gap = max(1, int(med * merge_ratio))
    spans = [imageops.bbox_of(binary[a:b]) for a, b in bands]

    def x_overlap(i: int, j: int) -> float:
        a, b = spans[i], spans[j]
        if a is None or b is None:
            return 0.0
        wa, wb = max(1.0, a[2] - a[0]), max(1.0, b[2] - b[0])
        return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) / min(wa, wb)

    merged: List[Tuple[int, int]] = []
    src: List[List[int]] = []          # indeks pita sumber tiap baris hasil
    for k, (a, b) in enumerate(bands):
        if merged and a - merged[-1][1] <= gap:
            merged[-1] = (merged[-1][0], b)
            src[-1].append(k)
            continue
        # pita KURANG TINGGI (ulu/suku/pepet, titik i, garis bawah) yang tumpang
        # tindih horizontal dengan baris di atasnya adalah tanda, bukan baris baru
        if merged and src[-1]:
            prev_k = src[-1][-1]
            h_prev = merged[-1][1] - merged[-1][0]
            h_cur = b - a
            thin, tall = min(h_prev, h_cur), max(h_prev, h_cur)
            if (thin <= 0.45 * tall and a - merged[-1][1] <= max(gap, thin * 1.6)
                    and x_overlap(prev_k, k) >= 0.5):
                merged[-1] = (min(merged[-1][0], a), max(merged[-1][1], b))
                src[-1].append(k)
                continue
        merged.append((a, b))
        src.append([k])
    # belah pita yang tingginya jauh di atas median (dua baris menempel)
    out: List[Tuple[int, int]] = []
    W = binary.shape[1]
    for a, b in merged:
        if W and (b - a) and float(rows[a:b].sum()) / float(W * (b - a)) < min_ink:
            continue
        stack = [(a, b)]
        while stack:
            y0, y1 = stack.pop()
            hh = y1 - y0
            if hh <= max(min_height * 2, med * split_ratio) or hh <= min_height:
                if hh >= min_height:
                    out.append((y0, y1))
                continue
            prof = rows[y0:y1]
            inner = prof[1:-1]
            if inner.size < 3:
                out.append((y0, y1))
                continue
            cut = min(int(np.argmin(inner)) + 1, inner.size - 1)
            base = max(int(np.median(inner)), 1)
            if inner[cut] > base * 0.35:  # lembah tidak jelas → jangan dipaksa belah
                out.append((y0, y1))
                continue
            top_h, bot_h = cut + 1, hh - cut - 1
            if min(top_h, bot_h) < 0.6 * max(top_h, bot_h):
                # satu sisi jauh lebih pendek → itu pangangge/titik, bukan baris kedua
                out.append((y0, y1))
                continue
            stack.extend([(y0, y0 + cut), (y0 + cut + 1, y1)])
    out.sort()
    return [(a, b) for a, b in out if b - a >= min_height]


def _split_parts(mask: np.ndarray, y_off: int, x_off: int, body_h: float) -> List[Part]:
    """Lepas bagian atas/bawah yang tersambung longgar dari badan aksara.

    Dua cara, dari yang paling meyakinkan ke yang paling longgar:

    1. **baris hampa nyata** di zona atas/bawah (tinta putus sama sekali) — pemisah
       ulu/suku/pepet/gantungan pada tulisan tangan dan cetak;
    2. **lembah tertipis** (jumlah tinta minimum) — untuk goresan yang nyaris sentuh.

    Potongan terbesar menjadi ``body`` (dinilai sebagai aksara), sisanya ``above`` /
    ``below`` (dinilai sebagai pangangge). Model dilatih pada bentuk tunggal, jadi
    memisahkan tanda menaikkan akurasi secara nyata.
    """
    h, w = mask.shape

    def pack(y0: int, y1: int, role: str) -> Optional[Part]:
        sub = mask[y0:y1]
        bb = imageops.bbox_of(sub)
        if bb is None or (y1 - y0) < 3 or (bb[2] - bb[0]) < 3 or (bb[3] - bb[1]) < 2:
            return None
        return Part(sub[bb[1]:bb[3], bb[0]:bb[2]].astype(np.float32),
                    (x_off + bb[0], y_off + y0 + bb[1], x_off + bb[2], y_off + y0 + bb[3]), role)

    def assemble(cuts: List[int]) -> List[Part]:
        bounds = [0] + sorted(set(c for c in cuts if 1 <= c <= h - 1)) + [h]
        if len(bounds) < 3:
            return []
        segs = [(bounds[i], bounds[i + 1], float(mask[bounds[i]:bounds[i + 1]].sum()))
                for i in range(len(bounds) - 1)]
        body_i = max(range(len(segs)), key=lambda i: segs[i][2])
        parts: List[Part] = []
        for i, (a, b, _area) in enumerate(segs):
            role = "body" if i == body_i else ("above" if b <= segs[body_i][0] else "below")
            part = pack(a, b, role)
            if part is not None:
                parts.append(part)
        if parts and not any(pt.role == "body" for pt in parts):
            parts[0].role = "body"
        # BADAN SELALU DI DEPAN: pipeline memakai ``parts[0]`` sebagai aksara dasar
        # dan ``parts[1:]`` sebagai pangangge. Tanpa urutan ini, huruf "i"/"j"
        # (titik di atas badan) menyerahkan TITIK-nya sebagai glyph dasar.
        parts.sort(key=lambda p: 0 if p.role == "body" else 1)
        return parts

    if h < 8 or w < 3:
        whole = pack(0, h, "body")
        return [whole] if whole else []

    rows = mask.sum(axis=1).astype(np.float32)

    # (1) celah hampa penuh
    cuts: List[int] = []
    i = 1
    while i < h - 1:
        if rows[i] == 0:
            j = i
            while j + 1 < h - 1 and rows[j + 1] == 0:
                j += 1
            top_area, bot_area = float(rows[:i].sum()), float(rows[j + 1:].sum())
            small, big = min(top_area, bot_area), max(top_area, bot_area)
            small_h = min(i, h - j - 1)
            # hanya belah bila sisi kecil itu memang “tanda”: sempit, luasnya minoritas.
            # Kalau tidak, goresan aksara yang putus akan dipecah jadi dua aksara palsu.
            if big > 0 and small > 0 and small <= 0.30 * big and small_h >= 2 and small_h <= 0.45 * h:
                cuts.append((i + j + 1) // 2)
            i = j + 2
        else:
            i += 1
    if cuts:
        parts = assemble(sorted(set(cuts))[:2])
        if len(parts) > 1:
            return parts

    # (2) lembah tertipis — hanya untuk gugus yang memang lebih tinggi dari biasanya
    if h <= max(7.0, body_h * 1.42):
        whole = pack(0, h, "body")
        return [whole] if whole else []

    strong = rows[rows > 0]
    if strong.size == 0:
        return []
    ref = float(np.median(strong))
    cuts = []
    for lo, hi in ((1, max(2, int(h * 0.42))), (min(h - 2, int(h * 0.60)), h - 1)):
        best_i, best_v = -1, 1e18
        for k in range(lo, hi):
            v = float(rows[k] + rows[k + 1])
            if v < best_v:
                best_v, best_i = v, k
        if best_i > 0 and best_v <= max(2.0, ref * 0.34):
            cuts.append(best_i + 1)
    parts = assemble(cuts)
    if len(parts) > 1:
        return parts
    whole = pack(0, h, "body")
    return [whole] if whole else []


def _split_columns(mask: np.ndarray, min_piece: float, max_width: float,
                   max_extra: int = 3, valley_ratio: float = 0.16) -> List[Tuple[int, int, int, int]]:
    """Belah gugus lebar pada lembah kolom tertipis → kandidat per aksara.

    Dipakai bila dua aksara/huruf menempel (atau digabung oleh ``close``). Lembah
    harus nyata (≤ 30% kolom median) supaya tanda adeg-adeg yang memang lebar tidak
    dipotong-potong; pemanggil tetap membandingkan hasil "utuh" vs "belah".
    """
    h, w = mask.shape
    out: List[Tuple[int, int, int, int]] = []

    def finish(x0: int, x1: int) -> None:
        bb = imageops.bbox_of(mask[:, x0:x1])
        if bb is not None and bb[2] - bb[0] >= 2 and bb[3] - bb[1] >= 2:
            # bbox_of relatif terhadap potongan [:, x0:x1] — kembalikan ke koordinat
            # mask (tanpa ini belahan ke-2 dst bergeser ke kiri & saling tumpang).
            out.append((x0 + bb[0], bb[1], x0 + bb[2], bb[3]))

    def rec(x0: int, x1: int, depth: int) -> None:
        ww = x1 - x0
        if depth >= max_extra or ww <= max_width:
            finish(x0, x1)
            return
        cols = mask[:, x0:x1].sum(axis=0).astype(np.float32)
        lo, hi = int(ww * 0.28), int(ww * 0.72)
        best_i, best_v = -1, 1e18
        for i in range(lo, max(lo, hi)):
            v = float(cols[i] + cols[i + 1])
            if v < best_v:
                best_v, best_i = v, i
        ink = cols[cols > 0]
        ref = float(np.median(ink)) if ink.size else 1.0
        if (best_i < 0 or best_v > max(1.0, ref * valley_ratio)
                or (best_i + 1 - x0) < min_piece or (x1 - best_i - 1) < min_piece):
            finish(x0, x1)
            return
        rec(x0, x0 + best_i + 1, depth + 1)
        rec(x0 + best_i + 1, x1, depth + 1)

    rec(0, w, 0)
    return out


def _drop_lonely_specks(cleaned: np.ndarray, min_area: int) -> np.ndarray:
    """Buang titik "kesepian" — kecil, kompak, dan tidak menempel pada huruf.

    Pada foto penuh derau (terutama setelah pembesaran teks kecil) ratusan titik 2–4px
    lolos ambang dan MENJEMBATANI baris teks (profil horizontal tak pernah nol → dua
    baris menyatu) atau menyusup ke celah kata. Titik semacam itu kompak (padat) dan
    jauh dari goresan besar; sebaliknya tanda baca aksara dan titik i/j — yang juga
    kecil — selalu berhimpit dengan hurufnya, sehingga tidak ikut terbuang.
    """
    labels, stats = imageops.components(cleaned)
    if not stats:
        return cleaned
    heights = np.array([s["h"] for s in stats], dtype=np.float32)
    big = heights >= 8
    if not big.any():
        return cleaned
    # tinggi huruf acuan: median komponen yang cukup tinggi (tahan terhadap lautan titik)
    h_ref = float(np.median(heights[big]))
    lim = max(4.0, 0.45 * h_ref)
    kill = np.zeros(len(stats), dtype=bool)
    for i, s in enumerate(stats):
        if big[i]:
            continue
        hh, ww = float(s["h"]), float(s["w"])
        if hh > lim or ww > lim:
            continue                    # pipih/fragmen goresan — bukan titik
        if s["area"] < 0.40 * hh * ww:  # keropos/bintang — biarkan min_area yang menilai
            continue
        x0, y0, x1, y1 = s["x"], s["y"], s["x"] + s["w"], s["y"] + s["h"]
        lonely = True
        for j, t in enumerate(stats):
            if i == j or not big[j]:
                continue
            # bertetangga dengan goresan besar bila rentang-x bersinggungan (±toleransi)
            # dan jarak vertikal dekat — titik i/j & pangangge lolos uji ini.
            tol = 0.25 * h_ref
            ox = min(x1, t["x"] + t["w"]) - max(x0, t["x"]) + tol
            gy = max(0.0, max(y0, t["y"]) - min(y1, t["y"] + t["h"]))
            if ox > 0 and gy <= 1.4 * h_ref:
                lonely = False
                break
        if lonely:
            kill[i] = True
    if not kill.any():
        return cleaned
    drop = {int(stats[i]["label"]) + 1 for i in np.where(kill)[0]}
    lut = np.zeros(int(labels.max()) + 1, dtype=bool)
    for d in drop:
        if d < len(lut):
            lut[d] = True
    out = cleaned.copy()
    out[lut[labels]] = 0
    return out


def _close_is_safe(cleaned: np.ndarray, min_gap: float = 2.5) -> bool:
    """Apakah closing 1–2 iterasi aman (tidak melebur satuan baca bersebelahan)?

    Mengukur celah horizontal tipikal antar komponen yang sebaris. Bila median-nya
    di bawah ``min_gap`` huruf-huruf sudah sempit — dilatasi 1px akan mengelembungkan
    mereka jadi satu komponen — sehingga closing dilewati.
    """
    _labels, stats = imageops.components(cleaned)
    if len(stats) < 6:
        return True
    gaps: List[int] = []
    by_y = sorted(stats, key=lambda s: (s["y"], s["x"]))
    # kelompok kasar per baris (y bertumpang tindih), lalu celah x antar komponen
    line: List[dict] = []
    line_bot = -1
    for s in by_y:
        if s["y"] > line_bot and line:
            _collect_gaps(line, gaps)
            line = []
        if not line or min(s["y"] + s["h"], line_bot) - s["y"] > 0:
            line.append(s)
            line_bot = max(line_bot, s["y"] + s["h"])
    if line:
        _collect_gaps(line, gaps)
    if len(gaps) < 3:
        return True
    return float(np.median(gaps)) >= min_gap


def _collect_gaps(line: List[dict], gaps: List[int]) -> None:
    line.sort(key=lambda s: s["x"])
    for a, b in zip(line, line[1:]):
        # pasangan yang bertumpang tindih vertikal (calon huruf sebaris)
        ov = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
        if ov >= 0.4 * min(a["h"], b["h"]):
            g = b["x"] - (a["x"] + a["w"])
            if 1 <= g <= 30:
                gaps.append(g)


def _drop_border_frames(cleaned: np.ndarray) -> np.ndarray:
    """Buang komponen "bingkai foto": garis/tepi bingkai & bayangan sudut yang
    menyentuh sisi gambar dan mustahil berupa huruf.

    Kandidat dibuang bila menyentuh tepi gambar DAN (a) garis tipis memanjang
    (sliver bingkai: memanjang ≥ 25% sisi namun tebal ≤ 3–5% sisi lainnya),
    atau (b) gumpalan besar (bayangan/vignette: luas bbox ≥ 8% gambar). Huruf asli
    yang kebetulan tergores tepi tidak kena karena ukurannya jauh di bawah ambang.
    """
    labels, stats = imageops.components(cleaned)
    if not stats:
        return cleaned
    H, W = cleaned.shape
    kill = set()
    for i, s in enumerate(stats, start=1):
        touch = s["x"] == 0 or s["y"] == 0 or s["x"] + s["w"] >= W or s["y"] + s["h"] >= H
        if not touch:
            continue
        thin_h = s["h"] >= 0.25 * H and s["w"] <= max(8, 0.03 * W)
        thin_w = s["w"] >= 0.25 * W and s["h"] <= max(10, 0.05 * H)
        big = (s["w"] * s["h"]) >= 0.08 * W * H
        # Gumpalan bayangan/vignette besar: tinta ≥ ~0,7% gambar dengan sisi panjang
        # ≥ ~12% sisi maksimum — tidak mungkin satu huruf; baris teks asli tampak
        # sebagai BANYAK komponen kecil yang masing-masing lolos filter ini.
        shade = s["area"] >= max(160, 0.007 * W * H) and max(s["w"], s["h"]) >= 0.12 * max(W, H)
        if thin_h or thin_w or big or shade:
            kill.add(i)
    if not kill:
        return cleaned
    out = cleaned.copy()
    np.place(out, np.isin(labels, list(kill)), 0)
    return out


def segment(binary: np.ndarray, *, merge_gap_ratio: float = 0.14, word_gap_ratio: float = 0.62,
            min_height: int = 6, min_area: int = 6, close_iters: int = 0,
            split_marks: bool = True, split_width_ratio: float = 1.25,
            min_ink: float = 0.012, split_valley_ratio: float = 0.16) -> List[Line]:
    """Citra biner → daftar :class:`Line` berisi :class:`Glyph` siap diklasifikasi."""
    h, w = binary.shape
    cleaned = imageops.remove_small(binary, min_area=min_area)
    cleaned = _drop_border_frames(cleaned)
    cleaned = _drop_lonely_specks(cleaned, min_area=min_area)
    if close_iters and _close_is_safe(cleaned):
        # Closing isotropik menyambung goresan putus tinta tangan, TETAPI hanya bila
        # celah antar goresan pada citra ini cukup lebar (≥ ~3px): pada teks rapat
        # (huruf Latin kecil berjarak 1–2px) closing justru melebur huruf
        # bersebelahan ("semeng" → "emeng") sehingga dinonaktifkan otomatis.
        cleaned = imageops.close(cleaned, close_iters)
    labels_all, stats_all = imageops.components(cleaned)
    bands = find_lines(cleaned, min_height=min_height, min_ink=min_ink)
    lines: List[Line] = []
    for li, (y0, y1) in enumerate(bands):
        line_bin = cleaned[y0:y1]
        labels, stats = imageops.components(line_bin)
        if not stats:
            continue
        lh = max(6.0, y1 - y0)
        merge = max(1.0, lh * merge_gap_ratio)
        # gabung komponen → gugus
        max_cluster_w = lh * max(1.0, split_width_ratio)
        order = sorted(range(len(stats)), key=lambda i: stats[i]["x"])
        clusters: List[List[int]] = []
        cur: List[int] = []
        cur_end = -10 ** 9
        cur_x0 = 10 ** 9
        cur_w = 10 ** 9
        cur_top, cur_bot = 10 ** 9, -10 ** 9
        for i in order:
            s = stats[i]
            x0, x1 = s["x"], s["x"] + s["w"]
            t0, t1 = s["y"], s["y"] + s["h"]
            join = False
            if cur:
                narrow = max(3.0, min(float(s["w"]), cur_w))
                ov_x = max(0.0, min(x1, cur_end) - max(x0, cur_x0))
                h_cur = max(1.0, float(cur_bot - cur_top))
                tall = max(float(s["h"]), h_cur)
                short = min(float(s["h"]), h_cur)
                ov_y = max(0.0, min(t1, cur_bot) - max(t0, cur_top)) / max(1.0, min(float(s["h"]), h_cur))
                union_w = x1 - min(x0, cur_x0)
                union_h = max(t1, cur_bot) - min(t0, cur_top)
                # "markish": salah satu kotak jauh lebih pendek → tanda (ulu, pepet,
                # titik i, gantungan), bukan huruf sebelah. Huruf Latin yang bersebelahan
                # punya tinggi serupa dan harus tetap terpisah.
                markish = short <= 0.62 * tall
                # Hubungan vertikal menentukan cara tanda menempel:
                # (a) MELAYANG di atas/bawah badan (ada celah vertikal) — titik i/j,
                #     ulu, surang, cecek: pusat horizontal tanda harus berada dalam
                #     rentang badan, sehingga titik "i" tidak jatuh ke huruf sebelah
                #     (dulu "li" terbaca "r" + "i tanpa titik" setelah deskew).
                # (b) BERDAMPINGAN (tumpang tindih vertikal) — goresan putus dari
                #     glyph yang sama: harus benar-benar tumpang tindih horizontal
                #     atau hampir bersinggungan; sekadar "dekat" tidak cukup.
                v_gap = max(0.0, max(t0, cur_top) - min(t1, cur_bot))
                cx = 0.5 * (x0 + x1)
                if v_gap > 0:
                    touching = (x0 - cur_end) <= merge or ov_x >= 0.45 * narrow
                    aligned = (cur_x0 - 1.0) <= cx <= (cur_end + 1.0)
                else:
                    touching = ov_x >= max(1.0, 0.3 * narrow) or (x0 - cur_end) <= 0.5 * merge
                    aligned = ov_x >= 0.45 * narrow or ov_y >= 0.5
                if markish and touching and aligned and union_w <= max_cluster_w and union_h <= lh * 2.2:
                    join = True
            if join:
                cur.append(i)
                cur_end, cur_x0 = max(cur_end, x1), min(cur_x0, x0)
                cur_w = min(cur_w, float(s["w"]))
                cur_top, cur_bot = min(cur_top, t0), max(cur_bot, t1)
            else:
                if cur:
                    clusters.append(cur)
                cur, cur_end, cur_x0, cur_w = [i], x1, x0, float(s["w"])
                cur_top, cur_bot = t0, t1
        if cur:
            clusters.append(cur)

        boxes: List[Tuple[int, int, int, int]] = []
        for cl in clusters:
            xs0 = min(stats[i]["x"] for i in cl)
            xs1 = max(stats[i]["x"] + stats[i]["w"] for i in cl)
            ys0 = min(stats[i]["y"] for i in cl)
            ys1 = max(stats[i]["y"] + stats[i]["h"] for i in cl)
            boxes.append((xs0, ys0, xs1, ys1))
        def _box_of(cl: List[int]) -> Tuple[int, int, int, int]:
            return (min(stats[i]["x"] for i in cl), min(stats[i]["y"] for i in cl),
                    max(stats[i]["x"] + stats[i]["w"] for i in cl),
                    max(stats[i]["y"] + stats[i]["h"] for i in cl))

        prelim = [b[3] - b[1] for b in boxes]
        ref_h = float(np.percentile(prelim, 25)) if prelim else lh

        # ── fragmen kecil diserap tetangga terdekat ───────────────────────
        # Pada tulisan tangan, satu aksara sering pecah jadi beberapa komponen
        # (kait, titik, goresan pemisah). Bila tidak diserap, pecahan itu dibaca
        # sebagai aksara tersendiri — sumber kesalahan tersegmentasi berlebih.
        #
        # Yang boleh diserap HANYA *fragmen*, yaitu komponen yang jelas bukan
        # satuan baca utuh: sangat kecil (debu/tinta lepas) atau pendek-sempit
        # (titik i/j, kait, potongan goresan). Huruf Latin yang sempit tetapi
        # setinggi baris (i, j, l, f, t, 1) dan aksara ramping TIDAK boleh
        # diserap: dulu "ll" menyatu jadi "l" dan "ld" jadi "k" sehingga kata
        # Latin kehilangan huruf. Syarat tambahan: fragmen harus tumpang tindih
        # horizontal dengan tetangganya (goresan putus dari aksara yang sama)
        # atau benar-benar menempel/mengambang di atas-bawahnya (titik).
        absorbed = [False] * len(clusters)
        for ci in range(len(clusters)):
            bx0, by0, bx1, by1 = boxes[ci]
            hh, ww = by1 - by0, bx1 - bx0
            area = sum(stats[i]["area"] for i in clusters[ci])
            tiny = area < min_area * 2
            short_and_narrow = hh <= 0.52 * ref_h and ww <= 0.85 * ref_h
            if not (tiny or short_and_narrow):
                continue                      # satuan baca utuh → jangan diganggu
            cand = []
            for dj in (ci - 1, ci + 1):
                if not (0 <= dj < len(clusters)) or absorbed[dj]:
                    continue
                ox0, oy0, ox1, oy1 = boxes[dj]
                ow, oh = ox1 - ox0, oy1 - oy0
                if max(ox1, bx1) - min(ox0, bx0) > max_cluster_w:
                    continue
                # jarak antar kotak (0 bila bersinggungan/tumpang tindih)
                gx = max(0.0, max(ox0, bx0) - min(ox1, bx1))
                gy = max(0.0, max(oy0, by0) - min(oy1, by1))
                ovx = max(0.0, min(ox1, bx1) - max(ox0, bx0))
                ovy = max(0.0, min(oy1, by1) - max(oy0, by0))
                ov_ratio = max(ovx / max(1.0, min(ww, ow)), ovy / max(1.0, min(hh, oh)))
                if ov_ratio < 0.25 and gx > 0.30 * ref_h:
                    continue           # terlalu jauh untuk jadi bagian aksara ini
                if ov_ratio < 0.25 and gy > 0.85 * ref_h:
                    continue           # beda baris/tinggi → bukan fragmen aksara ini
                # Sejajaran horizontal (covx) adalah bukti terkuat bahwa fragmen
                # milik tetangga ini: titik i/j melayang TEPAT di atas badannya
                # (covx≈1), sedangkan badan tinggi di sebelahnya hanya "menyentuh"
                # fragmen secara vertikal (covx≈0) — tanpa pembeda ini titik "i"
                # bisa jatuh ke huruf di kirinya ("li" terbaca "r"+"i tanpa titik").
                # Jarak vertikal TIDAK menghukum titik yang memang melayang.
                covx = ovx / max(1.0, min(ww, ow))
                score = -2.0 * covx + gx / ref_h + 0.35 * gy / ref_h
                if covx >= 0.6 and gy <= 0.6 * ref_h:
                    score -= 1.0   # fragmen melayang tepat di atas/bawah badannya
                cand.append((score, dj))
            if cand:
                cand.sort()
                dj = cand[0][1]
                clusters[dj] = clusters[dj] + clusters[ci]
                boxes[dj] = _box_of(clusters[dj])
                absorbed[ci] = True
            elif tiny or max(hh, ww) < 0.22 * ref_h:
                absorbed[ci] = True   # terlalu kecil untuk dipercaya → buang
        if any(absorbed):
            pairs = [(c, b) for c, b, keep in zip(clusters, boxes, absorbed) if not keep]
            if not pairs:
                continue
            clusters = [c for c, _b in pairs]
            boxes = [b for _c, b in pairs]

        heights = [b[3] - b[1] for b in boxes]
        # tinggi "normal" = persentil 25 (bukan median) supaya gugus yang lebih tinggi
        # karena ada pangangge/gantungan terdeteksi dan dicoba dipecah
        med_h = float(np.percentile(heights, 25)) if heights else lh
        glyphs: List[Glyph] = []
        for gi, (bx0, by0, bx1, by1) in enumerate(boxes):
            crop = labels[by0:by1, bx0:bx1]
            wanted = np.array(sorted({stats[i]["label"] + 1 for i in clusters[gi]}), dtype=np.int32)
            m = np.zeros(int(labels.max()) + 2, dtype=bool)
            m[wanted] = True
            mask = m[crop].astype(np.uint8)
            # tinta UTUH gugus: untuk huruf Latin satu gugus = satu huruf, termasuk
            # titik i/j dan silang t/f yang oleh pemecah badan/tanda dilepas.
            whole = Part(mask.astype(np.float32), (bx0, y0 + by0, bx1, y0 + by1), "body")
            parts = (_split_parts(mask, by0 + y0, bx0, med_h) if split_marks else [whole])
            pieces: List[List[Part]] = []
            piece_wholes: List[Part] = []
            if split_marks and med_h > 4 and (bx1 - bx0) > split_width_ratio * med_h:
                cuts = _split_columns(mask, max(3.0, med_h * 0.30), split_width_ratio * med_h,
                                      valley_ratio=split_valley_ratio)
                if len(cuts) > 1:
                    for (px0, py0, px1, py1) in cuts:
                        sub = mask[py0:py1, px0:px1]
                        pw = Part(sub.astype(np.float32),
                                  (bx0 + px0, y0 + by0 + py0, bx0 + px1, y0 + by0 + py1), "body")
                        if split_marks:
                            pp = _split_parts(sub, y0 + by0 + py0, bx0 + px0, med_h)
                        else:
                            pp = [pw]
                        if pp:
                            pieces.append(pp)
                            piece_wholes.append(pw)
            gap = (bx0 - boxes[gi - 1][2]) / med_h if gi else 1.0
            glyphs.append(Glyph(parts=parts, box=(bx0, y0 + by0, bx1, y0 + by1), pieces=pieces,
                                whole=whole, piece_wholes=piece_wholes, index=gi, gap_before=gap))
        gap_thr = word_gap_threshold(glyphs, word_gap_ratio)
        for gi, g in enumerate(glyphs):
            g.word_break = gi == 0 or g.gap_before >= gap_thr
        lines.append(Line(index=li, y0=y0, y1=y1, height=med_h, glyphs=glyphs,
                          word_gap=round(gap_thr, 3)))
    return lines
