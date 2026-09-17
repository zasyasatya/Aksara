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

    @property
    def text(self) -> str:
        return "".join(((" " if g.word_break else "") + (g.char or "")) for g in self.glyphs)


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
                   max_extra: int = 3) -> List[Tuple[int, int, int, int]]:
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
            out.append(bb)

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
        if (best_i < 0 or best_v > max(1.0, ref * 0.16)
                or (best_i + 1 - x0) < min_piece or (x1 - best_i - 1) < min_piece):
            finish(x0, x1)
            return
        rec(x0, x0 + best_i + 1, depth + 1)
        rec(x0 + best_i + 1, x1, depth + 1)

    rec(0, w, 0)
    return out


def segment(binary: np.ndarray, *, merge_gap_ratio: float = 0.14, word_gap_ratio: float = 0.62,
            min_height: int = 6, min_area: int = 6, close_iters: int = 0,
            split_marks: bool = True, split_width_ratio: float = 1.25,
            min_ink: float = 0.012) -> List[Line]:
    """Citra biner → daftar :class:`Line` berisi :class:`Glyph` siap diklasifikasi."""
    h, w = binary.shape
    cleaned = imageops.remove_small(binary, min_area=min_area)
    if close_iters:
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
                touching = (x0 - cur_end) <= merge or ov_x >= 0.45 * narrow
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

        # ── gugus kecil yang menyendiri diserap tetangga terdekat ──────────
        # Pada tulisan tangan, satu aksara sering pecah jadi beberapa komponen
        # (kait, titik, goresan pemisah). Bila tidak diserap, pecahan itu dibaca
        # sebagai aksara tersendiri — sumber kesalahan tersegmentasi berlebih.
        absorbed = [False] * len(clusters)
        for ci in range(len(clusters)):
            bx0, by0, bx1, by1 = boxes[ci]
            hh, ww = by1 - by0, bx1 - bx0
            area = sum(stats[i]["area"] for i in clusters[ci])
            big_enough = hh >= 0.46 * ref_h and ww >= 0.30 * ref_h
            if big_enough and area >= min_area * 2:
                continue
            cand = []
            for dj in (ci - 1, ci + 1):
                if not (0 <= dj < len(clusters)) or absorbed[dj]:
                    continue
                ox0, oy0, ox1, oy1 = boxes[dj]
                if max(ox1, bx1) - min(ox0, bx0) > max_cluster_w:
                    continue
                dx = min(abs(ox0 - bx1), abs(bx0 - ox1))
                dy = abs((oy0 + oy1) / 2.0 - (by0 + by1) / 2.0)
                ovx = max(0, min(ox1, bx1) - max(ox0, bx0))
                if ovx < 0.4 * min(ww, ox1 - ox0) and dx > 0.4 * ref_h:
                    continue           # terlalu jauh untuk jadi bagian aksara ini
                cand.append((dx + 0.6 * dy, dj))
            if cand:
                cand.sort()
                dj = cand[0][1]
                clusters[dj] = clusters[dj] + clusters[ci]
                boxes[dj] = _box_of(clusters[dj])
                absorbed[ci] = True
            elif area < min_area * 2 or max(hh, ww) < 0.24 * ref_h:
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
            parts = (_split_parts(mask, by0 + y0, bx0, med_h) if split_marks
                     else [Part(mask.astype(np.float32), (bx0, y0 + by0, bx1, y0 + by1), "body")])
            pieces: List[List[Part]] = []
            if split_marks and med_h > 4 and (bx1 - bx0) > split_width_ratio * med_h:
                cuts = _split_columns(mask, max(3.0, med_h * 0.30), split_width_ratio * med_h)
                if len(cuts) > 1:
                    for (px0, py0, px1, py1) in cuts:
                        sub = mask[py0:py1, px0:px1]
                        if split_marks:
                            pp = _split_parts(sub, y0 + by0 + py0, bx0 + px0, med_h)
                        else:
                            pp = [Part(sub.astype(np.float32),
                                       (bx0 + px0, y0 + by0 + py0, bx0 + px1, y0 + by0 + py1), "body")]
                        if pp:
                            pieces.append(pp)
            gap = (bx0 - boxes[gi - 1][2]) / med_h if gi else 1.0
            glyphs.append(Glyph(parts=parts, box=(bx0, y0 + by0, bx1, y0 + by1), pieces=pieces,
                                index=gi, gap_before=gap))
        for gi, g in enumerate(glyphs):
            g.word_break = gi == 0 or g.gap_before >= word_gap_ratio
        lines.append(Line(index=li, y0=y0, y1=y1, height=med_h, glyphs=glyphs))
    return lines
