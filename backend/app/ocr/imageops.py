"""Operasi citra untuk OCR kamera — NumPy + Pillow saja (tanpa OpenCV/Tesseract).

Semua fungsi menerima/mengembalikan ``float32`` 0..255 (laris) atau ``uint8``
biner (1 = tinta). Tidak ada dependensi berat supaya muat di container kecil dan
berjalan di CPU mana pun.

Pipeline standar::

    bytes → dekode → grayscale (thumbnail) → rentang kontras → ambang Sauvola
          → bersihkan noise → koreksi kemiringan → (segmentasi)
"""

from __future__ import annotations

import io
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageFilter, ImageOps

MAX_SIDE = 1400


# ── dekode & normalisasi dasar ─────────────────────────────────────────────

def decode_gray(data: bytes, max_side: int = MAX_SIDE) -> np.ndarray:
    """Bytes gambar → grayscale float32; sisi terpanjang dibatasi ``max_side``.

    Orientasi EXIF dihormati — penting untuk foto vertikal dari ponsel.
    """
    img = Image.open(io.BytesIO(data))
    img.load()
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:  # pragma: no cover - EXIF opsional
        pass
    if img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        bg.alpha_composite(rgba)
        img = bg.convert("L")
    else:
        img = img.convert("L")
    if max(img.size) > max_side:
        ratio = max_side / float(max(img.size))
        img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.LANCZOS)
    return np.asarray(img, dtype=np.float32)


def stretch_contrast(gray: np.ndarray, lo: float = 1.0, hi: float = 99.0) -> np.ndarray:
    """Regangkan histogram ke 0..255 (kompensasi eksposur rendah / foto gelap)."""
    if gray.size == 0:
        return gray
    a = float(np.percentile(gray, lo))
    b = float(np.percentile(gray, hi))
    if b - a < 12:
        return gray
    return np.clip((gray - a) * (255.0 / (b - a)), 0.0, 255.0).astype(np.float32)


def otsu_threshold(gray: np.ndarray) -> float:
    hist, _ = np.histogram(gray, bins=256, range=(0, 256))
    hist = hist.astype(np.float64)
    total = hist.sum()
    if total == 0:
        return 128.0
    sum_all = float((np.arange(256) * hist).sum())
    sum_b = 0.0
    w_b = 0.0
    best_t, best_var = 128.0, -1.0
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_all - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > best_var:
            best_var, best_t = var, t
    return float(best_t)


def _integral(arr: np.ndarray) -> np.ndarray:
    out = np.zeros((arr.shape[0] + 1, arr.shape[1] + 1), dtype=np.float64)
    out[1:, 1:] = np.cumsum(np.cumsum(arr.astype(np.float64), axis=0), axis=1)
    return out


def sauvola_threshold(gray: np.ndarray, window: int = 25, k: float = 0.12,
                      R: float = 128.0) -> Tuple[np.ndarray, np.ndarray]:
    """Ambang Sauvola per piksel + rerata lokal (dipakai juga jalur noise-aware)."""
    h, w = gray.shape
    half = max(3, int(window) // 2)
    pad = np.pad(gray, half, mode="reflect")
    ii, jj = _integral(pad), _integral(pad * pad)
    size = float((2 * half + 1) ** 2)
    y0 = np.arange(h)[:, None]
    x0 = np.arange(w)[None, :]
    y1, x1 = y0 + 2 * half + 1, x0 + 2 * half + 1

    def box(integ):
        return integ[y1, x1] - integ[y0, x1] - integ[y1, x0] + integ[y0, x0]

    mean = box(ii) / size
    var = np.maximum(box(jj) / size - mean * mean, 0.0)
    thr = mean * (1.0 + k * (np.sqrt(var) / R - 1.0))
    return thr, mean


def sauvola(gray: np.ndarray, window: int = 25, k: float = 0.12, R: float = 128.0) -> np.ndarray:
    """Binerisasi adaptif Sauvola — O(N) lewat integral image, tahan cahaya miring.

    Ambang lokal ``t = mean · (1 + k · (std/R − 1))``: di daerah bertekstur (std besar)
    ambang turun sehingga goresan tipis pada daun lontar tetap terjaga.
    """
    thr, _mean = sauvola_threshold(gray, window=window, k=k, R=R)
    return (gray < thr).astype(np.uint8)


def smooth(gray: np.ndarray, sigma: float = 0.8) -> np.ndarray:
    """Gaussian ringan (PIL) — menekan derau sensor/JPEG tanpa menghapus goresan."""
    im = Image.fromarray(np.clip(gray, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(float(sigma))), dtype=np.float32)


def estimate_noise(gray: np.ndarray) -> float:
    """Estimasi σ derau kamera — median residual terhadap blur 3×3 (robust).

    Area latar (mayoritas piksel) menentukan estimasi, sehingga tepi goresan yang
    kontras tinggi tidak ikut menaikkan angkanya.
    """
    if gray.size < 64:
        return 0.0
    res = np.abs(gray - smooth(gray, 0.8))
    return float(np.median(res)) / 0.693


def _dilate1(mask: np.ndarray) -> np.ndarray:
    """Dilatasi 8-tetangga satu iterasi (NumPy murni)."""
    p = np.pad(mask.astype(bool), 1)
    return (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
            | p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:])


def binarize(gray: np.ndarray, mode: str = "sauvola", window: int = 25, k: float = 0.12,
             invert: str = "auto", denoise: str = "auto", sigma: Optional[float] = None) -> np.ndarray:
    """Citra biner ``uint8`` dengan 1 = tinta.

    ``invert``: ``auto`` (deteksi dari pinggir), ``dark-ink`` (tinta gelap di latar
    terang), ``light-ink`` (kebalikannya — mis. aksara putih pada batu gelap).

    ``denoise``: ``auto`` menambahkan peredam derau adaptif pada mode Sauvola bila
    σ derau estimasi ≥ 2,4 (foto kamera gelap/noisy). Caranya: citra dilembutkan
    ringan, lalu tinta *kuat* dibatasi pada piksel yang berada ``margin ≈ 2,6σ`` di
    bawah rerata lokal — bintik derau di latar rata tidak lagi ikut menjadi tinta —
    sementara piksel tepi goresan yang lolos ambang Sauvola dan menempel pada tinta
    kuat tetap dipulihkan. Citra bersih (render/tangkapan layar) tidak berubah
    perilakunya sama sekali.

    ``sigma``: σ derau yang sudah diestimasi pemanggil (dalam skala abu pasca-stretch).
    Penting saat citra diperbesar: interpolasi menurunkan σ terukur sehingga estimasi
    ulang bisa salah mematikan peredam derau; pemanggil meneruskan σ dari skala asli.
    """
    g = stretch_contrast(gray)
    if mode == "otsu":
        binary = (g < otsu_threshold(g)).astype(np.uint8)
    elif mode == "fixed":
        binary = (g < 128).astype(np.uint8)
    else:
        if denoise == "off":
            sigma = 0.0
        elif sigma is None:
            sigma = estimate_noise(g)
        if sigma >= 2.4:
            # Benih tinta kuat dinilai pada citra yang dilembutkan ringan (0,75px — cukup
            # menekan derau, TIDAK melebur huruf yang berjarak sempit seperti blur besar);
            # pertumbuhan memakai ambang Sauvola pada citra ASLI sehingga tepi goresan
            # tetap tajam dan huruf tetangga tidak menyatu. (Blur adaptif-σ sudah dicoba:
            # justru melelehkan huruf kecil → CER naik; 0,75 tetap terukur paling baik.)
            soft = smooth(g, sigma=0.75)
            _thr_soft, mean_soft = sauvola_threshold(soft, window=window, k=k)
            margin = float(np.clip(2.6 * sigma, 3.0, 30.0))
            strong = soft < (mean_soft - margin)
            thr_grow, _mean_grow = sauvola_threshold(g, window=window, k=k)
            binary = (strong | ((g < thr_grow) & _dilate1(strong))).astype(np.uint8)
        else:
            binary = sauvola(g, window=window, k=k)
    if invert == "auto":
        border = np.concatenate([binary[0, :], binary[-1, :], binary[:, 0], binary[:, -1]])
        if border.mean() > 0.5:
            binary = 1 - binary
    elif invert == "light-ink":
        binary = 1 - binary
    return binary.astype(np.uint8)


# ── morfologi & komponen terhubung ────────────────────────────────────────

def dilate(binary: np.ndarray, iters: int = 1) -> np.ndarray:
    out = binary.astype(np.uint8)
    for _ in range(max(0, int(iters))):
        p = np.pad(out, 1, mode="constant", constant_values=0)
        s = p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
        out = (s > 0).astype(np.uint8)
    return out


def erode(binary: np.ndarray, iters: int = 1) -> np.ndarray:
    out = binary.astype(np.uint8)
    for _ in range(max(0, int(iters))):
        p = np.pad(out, 1, mode="constant", constant_values=1)
        s = p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] + p[1:-1, 1:-1]
        out = (s >= 5).astype(np.uint8)
    return out


def close(binary: np.ndarray, iters: int = 1) -> np.ndarray:
    return erode(dilate(binary, iters), iters)


class _Union:
    def __init__(self) -> None:
        self.parent = [0]

    def add(self) -> int:
        self.parent.append(len(self.parent))
        return len(self.parent) - 1

    def find(self, a: int) -> int:
        p = self.parent
        while p[a] != a:
            p[a] = p[p[a]]
            a = p[a]
        return a

    def union(self, a: int, b: int) -> int:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return ra
        if ra < rb:
            self.parent[rb] = ra
            return ra
        self.parent[ra] = rb
        return rb


def components(binary: np.ndarray) -> Tuple[np.ndarray, List[dict]]:
    """Komponen terhubung 8-konektivitas berbasis *run-length* + Union-Find.

    Jauh lebih ringan dari BFS per-piksel dan tidak butuh SciPy. Mengembalikan
    ``(label_map, stats)`` dengan ``label_map`` bernilai 1..N (0 = latar) dan
    ``stats[i]`` = ``{label, x, y, w, h, area}`` untuk komponen ke-``i``.
    """
    h, w = binary.shape
    labels = np.zeros((h, w), dtype=np.int32)
    uf = _Union()
    boxes: dict[int, List[int]] = {}      # label sementara → [minx, miny, maxx, maxy, area]
    b = binary.astype(np.uint8)
    prev: List[Tuple[int, int, int]] = []  # run baris sebelumnya, terurut x0
    for y in range(h):
        edges = np.flatnonzero(np.diff(np.concatenate(([0], b[y], [0]))))
        starts, ends = edges[0::2], edges[1::2] - 1
        cur: List[Tuple[int, int, int]] = []
        pi = 0
        for x0, x1 in zip(starts.tolist(), ends.tolist()):
            while pi < len(prev) and prev[pi][1] < x0 - 1:
                pi += 1
            lbl = 0
            j = pi
            while j < len(prev) and prev[j][0] <= x1 + 1:
                lbl = prev[j][2] if lbl == 0 else uf.union(lbl, prev[j][2])
                j += 1
            if lbl == 0:
                lbl = uf.add()
            cur.append((x0, x1, lbl))
            labels[y, x0:x1 + 1] = lbl + 1
            bx = boxes.get(lbl)
            if bx is None:
                boxes[lbl] = [x0, y, x1, y, x1 - x0 + 1]
            else:
                bx[0] = min(bx[0], x0); bx[2] = max(bx[2], x1)
                bx[3] = y; bx[4] += x1 - x0 + 1
        prev = cur
    if not boxes:
        return labels, []
    # rapikan: setiap label → indeks akar, lalu padatkan ke 1..N
    root_idx: dict[int, int] = {}
    lut = np.zeros(len(uf.parent) + 1, dtype=np.int32)
    merged: dict[int, List[int]] = {}
    for lbl, bx in boxes.items():
        r = uf.find(lbl)
        if r not in root_idx:
            root_idx[r] = len(root_idx) + 1
        i = root_idx[r]
        cur_box = merged.get(i)
        if cur_box is None:
            merged[i] = list(bx)
        else:
            cur_box[0] = min(cur_box[0], bx[0]); cur_box[1] = min(cur_box[1], bx[1])
            cur_box[2] = max(cur_box[2], bx[2]); cur_box[3] = max(cur_box[3], bx[3])
            cur_box[4] += bx[4]
        lut[lbl + 1] = i
    labels = lut[labels]
    stats: List[dict] = []
    for i in range(1, len(root_idx) + 1):
        mnx, mny, mxx, mxy, area = merged[i]
        stats.append({"label": i - 1, "x": int(mnx), "y": int(mny), "w": int(mxx - mnx + 1),
                      "h": int(mxy - mny + 1), "area": int(area)})
    return labels, stats


def remove_small(binary: np.ndarray, min_area: int = 8, min_side: int = 2) -> np.ndarray:
    labels, stats = components(binary)
    if not stats:
        return binary
    keep = np.zeros(len(stats) + 1, dtype=bool)
    for s in stats:
        if s["area"] >= min_area and min(s["w"], s["h"]) >= min_side:
            keep[s["label"] + 1] = True
    return keep[labels].astype(np.uint8)


def mask_components(binary: np.ndarray, idx: List[int]) -> np.ndarray:
    """Biner yang hanya berisi komponen dengan indeks ``idx`` (0-based, urutan ``stats``)."""
    labels, stats = components(binary)
    if not idx or not stats:
        return np.zeros_like(binary)
    wanted = np.array(sorted({i + 1 for i in idx if 0 <= i < len(stats)}), dtype=np.int32)
    m = np.zeros(int(labels.max()) + 2, dtype=bool)
    m[wanted] = True
    return m[labels].astype(np.uint8)


# ── koreksi kemiringan ─────────────────────────────────────────────────────

def estimate_skew(binary: np.ndarray, max_angle: float = 7.0, step: float = 0.5) -> float:
    """Sudut yang memaksimalkan varians profil proyeksi horizontal (standal Prokikina)."""
    if int(binary.sum()) < 40:
        return 0.0
    img = Image.fromarray((binary * 255).astype(np.uint8), "L")
    best, best_score = 0.0, -1.0
    for a in np.arange(-max_angle, max_angle + 1e-9, step):
        rot = np.asarray(img.rotate(float(a), resample=Image.BILINEAR, fillcolor=0), dtype=np.float32)
        prof = rot.sum(axis=1)
        score = float(((prof - prof.mean()) ** 2).mean())
        if score > best_score:
            best_score, best = score, float(a)
    return best


def rotate(arr: np.ndarray, angle: float, fill: float = 0.0, binary: bool = False) -> np.ndarray:
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")
    out = img.rotate(angle, resample=Image.BILINEAR, fillcolor=int(fill))
    res = np.asarray(out, dtype=np.float32)
    return (res > 110).astype(np.uint8) if binary else res


# ── util ───────────────────────────────────────────────────────────────────

def scale(arr: np.ndarray, factor: float) -> np.ndarray:
    """Perbesar citra dengan LANCZOS — dipakai untuk teks kecil agar goresan
    punya ketebalan yang wajar sebelum dinormalisasi ke kanvas 28×28."""
    h, w = arr.shape
    nw, nh = max(1, int(round(w * factor))), max(1, int(round(h * factor)))
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")
    img = img.resize((nw, nh), Image.LANCZOS)
    return np.asarray(img, dtype=np.float32)


def profile(binary: np.ndarray, axis: int) -> np.ndarray:
    return binary.sum(axis=axis).astype(np.float32)


def group_indices(active: np.ndarray, max_gap: int = 0, min_len: int = 1) -> List[Tuple[int, int]]:
    """Blok indeks ``True`` yang berurutan → daftar ``(awal, akhir)`` (eksklusif).

    ``max_gap`` mengizinkan celah kecil (mis. pemisah antar goresan pada satu aksara).
    """
    idx = np.flatnonzero(active)
    if idx.size == 0:
        return []
    out: List[Tuple[int, int]] = []
    start = prev = int(idx[0])
    for v in idx[1:].tolist():
        if v - prev > max_gap + 1:
            if prev - start + 1 >= min_len:
                out.append((start, prev + 1))
            start = v
        prev = v
    if prev - start + 1 >= min_len:
        out.append((start, prev + 1))
    return out


def bbox_of(binary: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    ys = np.flatnonzero(binary.any(axis=1))
    xs = np.flatnonzero(binary.any(axis=0))
    if ys.size == 0 or xs.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def to_ink(binary: np.ndarray, y0: int, x0: int, y1: int, x1: int) -> np.ndarray:
    """Crop biner → maska tinta float32 [0,1] (1 = tinta) siap ``features.normalize_ink``."""
    return np.clip(binary[max(0, y0):y1, max(0, x0):x1].astype(np.float32), 0.0, 1.0)
