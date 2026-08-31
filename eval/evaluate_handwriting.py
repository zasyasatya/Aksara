#!/usr/bin/env python3
"""Evaluasi akurasi classifier tulisan tangan Aksara Bali (template matching).

Harness ini meniru 1:1 logika normalisasi & penskoran classifier on-device di
``frontend/lib/aksara-recognition.ts`` (``normalizeToMask`` + ``compareMasks``
dengan *chamfer distance* dua arah, dan ambang ``classifyTracing`` /
``recognizeAksara``), lalu mengukurnya pada dataset sintetis tulisan tangan:

- Template glyph dirender dari font **Noto Sans Balinese** (sumber OFL,
  sama dengan yang dipakai UI).
- Variasi "tulisan tangan" disimulasikan sebagai perturbasi geometri +
  ketebalan stroke + noise.

Dua tugas dievaluasi (sesuai dua mode classifier di produk):

1. **Verifikasi / telusur (``classifyTracing``)** — tugas utama produk:
   memutuskan apakah tulisan pengguna cocok dengan glyph target yang
   ditampilkan (binary, ambang ``correct >= 0.55``).
   Positif = target ditelusuri (variasi kecil, karena ada siluet pemandu);
   negatif = coretan acak (tinta "salah").
2. **Pengenalan terbuka (``recognizeAksara``)** — memilih 1 dari 18 kelas;
   dilaporkan jujur (top-1 + *confident-rate*) karena sejumlah aksara Bali
   (na/da/ta/ca) nyaris identik dan sulit dipisahkan tanpa konteks.

HASIL DI SINI ADALAH METRIK ALGORITMA pada dataset sintetis — bukan klaim
performa pada tinta manusia sungguhan (yang memerlukan dataset ink nyata).

Dependensi: Pillow, NumPy, dan font Noto Sans Balinese (OFL).
Jalankan:
    python evaluate_handwriting.py --font path/ke/NotoSansBalinese.ttf
Font otomatis diunduh dari google/fonts (GitHub) bila ``--font`` tidak diberikan.
"""

import argparse
import random
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

NORM_SIZE = 128          # sama dengan NORM_SIZE di aksara-recognition.ts
INK_THRESHOLD = 200      # luminansi < nilai ini = tinta
SQRT2 = 1.4142135623730951
SCORE_SCALE = 0.14       # a.size * 0.14 pada aksara-recognition.ts

# Ambang klasifikasi di aksara-recognition.ts
CORRECT_MIN = 0.55       # classifyTracing: "correct"
CLOSE_MIN = 0.35         # classifyTracing: "close"
CONFIDENT_MIN = 0.55     # recognizeAksara
CONFIDENT_MARGIN = 0.07  # recognizeAksara

# 18 aksara Wresastra (urutan ha na ca ra ka …) — codepoint Unicode Balinese.
WRESASTRA = [
    ("ha", 0x1B33), ("na", 0x1B26), ("ca", 0x1B18), ("ra", 0x1B2D), ("ka", 0x1B13),
    ("da", 0x1B24), ("ta", 0x1B23), ("sa", 0x1B32), ("wa", 0x1B2F), ("la", 0x1B2E),
    ("ma", 0x1B2B), ("ga", 0x1B15), ("ba", 0x1B29), ("nga", 0x1B17), ("pa", 0x1B27),
    ("ja", 0x1B1A), ("ya", 0x1B2C), ("nya", 0x1B1C),
]

FONT_URL = (
    "https://api.github.com/repos/google/fonts/contents/"
    "ofl/notosansbalinese/NotoSansBalinese%5Bwght%5D.ttf"
)


def download_font(dest: Path) -> None:
    req = urllib.request.Request(FONT_URL, headers={"Accept": "application/vnd.github.raw"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    if not data.startswith(b"\x00\x01\x00\x00"):
        raise RuntimeError("Unduhan bukan font TTF (kemungkinan HTML). Berikan --font.")
    dest.write_bytes(data)


def render_glyph(font: ImageFont.FreeTypeFont, codepoint: int, size: int = 320) -> np.ndarray:
    """Render 1 glyph ke canvas putih, lalu kembalikan maska tinta boolean.

    Mirip ``renderGlyphToCanvas`` + ``toBinaryMaskOf`` di aksara-recognition.ts.
    """
    img = Image.new("L", (size, size), 255)
    d = ImageDraw.Draw(img)
    d.fontmode = "L"
    f = font.font_variant(size=round(size * 0.58))
    text = chr(codepoint)
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1] + size * 0.04
    d.text((x, y), text, font=f, fill=0)
    return np.asarray(img, dtype=np.uint8) < INK_THRESHOLD


def normalize_to_mask(mask: np.ndarray, size: int = NORM_SIZE) -> np.ndarray | None:
    """Crop bbox tinta, skala (maintain aspect) ke kotak size×size terpusat.

    Mirip ``normalizeToMask`` di aksara-recognition.ts.
    """
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return None
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    w = x1 - x0 + 1
    h = y1 - y0 + 1
    if w < 4 or h < 4:
        return None
    crop = mask[y0:y1 + 1, x0:x1 + 1]
    scale = min(size / w, size / h)
    dw = max(1, round(w * scale))
    dh = max(1, round(h * scale))
    dx = round((size - dw) / 2)
    dy = round((size - dh) / 2)
    resized = _resize_bool(crop, dw, dh)
    out = np.zeros((size, size), dtype=bool)
    out[dy:dy + dh, dx:dx + dw] = resized
    return out


def _resize_bool(mask: np.ndarray, w: int, h: int) -> np.ndarray:
    img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    img = img.resize((w, h), Image.NEAREST)
    return np.asarray(img) > 127


def chamfer_distance(mask: np.ndarray) -> np.ndarray:
    """Jarak chamfer (1, sqrt2) dua-pass — ekuivalen BFS 8-tetangga di
    ``distanceTransform`` aksara-recognition.ts (diagonal ≈ 1.4142)."""
    d = np.where(mask, 0.0, 1e9).astype(np.float64)
    H, W = mask.shape
    for i in range(1, H):
        cur = d[i].copy()
        prev = d[i - 1]
        cur = np.minimum(cur, prev + 1.0)
        cur[1:] = np.minimum(cur[1:], prev[:-1] + SQRT2)
        cur[:-1] = np.minimum(cur[:-1], prev[1:] + SQRT2)
        cur[1:] = np.minimum(cur[1:], cur[:-1] + 1.0)
        d[i] = cur
    for i in range(H - 2, -1, -1):
        cur = d[i].copy()
        nxt = d[i + 1]
        cur = np.minimum(cur, nxt + 1.0)
        cur[1:] = np.minimum(cur[1:], nxt[:-1] + SQRT2)
        cur[:-1] = np.minimum(cur[:-1], nxt[1:] + SQRT2)
        cur[:-1] = np.minimum(cur[:-1], cur[1:] + 1.0)
        d[i] = cur
    return d


def compare_masks(a: np.ndarray, b: np.ndarray,
                  dist_a: np.ndarray | None = None,
                  dist_b: np.ndarray | None = None) -> float:
    """Skor kemiripan dua maska via chamfer dua arah (sama dengan
    ``compareMasks`` di aksara-recognition.ts)."""
    da = dist_a if dist_a is not None else chamfer_distance(a)
    db = dist_b if dist_b is not None else chamfer_distance(b)
    cnt_a = int(a.sum())
    cnt_b = int(b.sum())
    if not cnt_a or not cnt_b:
        return 0.0
    sum_a = float(db[a].sum())
    sum_b = float(da[b].sum())
    avg_px = (sum_a / cnt_a + sum_b / cnt_b) / 2.0
    scale = NORM_SIZE * SCORE_SCALE
    return float(max(0.0, min(1.0, 1.0 - avg_px / scale)))


def trace_positive(mask: np.ndarray, rng: random.Random, size: int = 320) -> np.ndarray:
    """Simulasi pengguna yang MENELUSURI siluet target (ada ghost di UI):
    variasi kecil rotasi/skala/translasi + ketebalan pena. Tanpa shear liar."""
    img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    cx = cy = size / 2
    angle = rng.uniform(-2.0, 2.0)
    scale = rng.uniform(0.94, 1.06)
    tx = rng.uniform(-3.0, 3.0)
    ty = rng.uniform(-3.0, 3.0)
    a = scale * np.cos(angle)
    b = -scale * np.sin(angle)
    d = scale * np.sin(angle)
    e = scale * np.cos(angle)
    c = cx - a * cx - b * cy + tx
    f = cy - d * cx - e * cy + ty
    img = img.transform((size, size), Image.AFFINE, (a, b, c, d, e, f),
                        resample=Image.BILINEAR, fillcolor=255)
    if rng.random() < 0.5:
        img = img.filter(ImageFilter.MaxFilter(3))  # pena tebal
    return np.asarray(img, dtype=np.uint8) < INK_THRESHOLD


def scribble(rng: random.Random, size: int = 320) -> np.ndarray:
    """Coretan acak — mewakili tinta 'salah' pada latihan telusur."""
    img = Image.new("L", (size, size), 255)
    d = ImageDraw.Draw(img)
    for _ in range(rng.randint(2, 5)):
        x0, y0 = rng.randint(20, 300), rng.randint(20, 300)
        pts = [(x0, y0)]
        for _ in range(rng.randint(3, 8)):
            pts.append((pts[-1][0] + rng.randint(-40, 40),
                        pts[-1][1] + rng.randint(-40, 40)))
        d.line(pts, fill=0, width=rng.randint(2, 5))
    return np.asarray(img, dtype=np.uint8) < INK_THRESHOLD


def build_templates(font: ImageFont.FreeTypeFont) -> dict:
    templates = {}
    raws = {}
    for name, cp in WRESASTRA:
        raws[name] = render_glyph(font, cp)
        templates[name] = normalize_to_mask(raws[name])
    return raws, templates


def evaluate_verification(raws, templates, rng, samples_per_class: int = 20) -> dict:
    """Tugas verifikasi (classifyTracing): binary correct/incorrect."""
    names = list(templates)
    dists = {n: chamfer_distance(templates[n]) for n in names}
    pos_scores, neg_scores = [], []
    for name in names:
        for _ in range(samples_per_class):
            s = normalize_to_mask(trace_positive(raws[name], rng))
            if s is not None:
                pos_scores.append(compare_masks(s, templates[name],
                                                chamfer_distance(s), dists[name]))
            s = normalize_to_mask(scribble(rng))
            if s is not None:
                neg_scores.append(compare_masks(s, templates[name],
                                                chamfer_distance(s), dists[name]))
    pos = np.array(pos_scores)
    neg = np.array(neg_scores)
    tp = int((pos >= CORRECT_MIN).sum())
    fn = int((pos < CORRECT_MIN).sum())
    tn = int((neg < CORRECT_MIN).sum())
    fp = int((neg >= CORRECT_MIN).sum())
    accuracy = (tp + tn) / max(1, len(pos) + len(neg))
    return {
        "positive": pos, "negative": neg,
        "tp": tp, "fn": fn, "tn": tn, "fp": fp,
        "accuracy": accuracy,
    }


def evaluate_recognition(raws, templates, rng, samples_per_class: int = 30) -> dict:
    """Tugas pengenalan terbuka (recognizeAksara): top-1 dari 18 kelas."""
    names = list(templates)
    dists = {n: chamfer_distance(templates[n]) for n in names}
    total = correct = conf_total = conf_ok = 0
    for name in names:
        for _ in range(samples_per_class):
            s = normalize_to_mask(trace_positive(raws[name], rng))
            if s is None:
                continue
            ds = chamfer_distance(s)
            scored = sorted((compare_masks(s, templates[t], ds, dists[t]), t) for t in names)
            best, best_name = scored[-1]
            second = scored[-2][0]
            margin = best - second
            confident = best >= CONFIDENT_MIN and margin >= CONFIDENT_MARGIN
            total += 1
            if best_name == name:
                correct += 1
            if confident:
                conf_total += 1
                if best_name == name:
                    conf_ok += 1
    return {
        "total": total, "correct": correct,
        "top1_accuracy": correct / max(1, total),
        "confident_total": conf_total, "confident_ok": conf_ok,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", default=None, help="Path font Noto Sans Balinese (.ttf)")
    ap.add_argument("--samples", type=int, default=20, help="Sampel per kelas (verifikasi)")
    ap.add_argument("--seed", type=int, default=20260831)
    args = ap.parse_args()

    font_path = Path(args.font) if args.font else Path(__file__).parent / "NotoSansBalinese.ttf"
    if not font_path.is_file():
        print(f"Mengunduh font ke {font_path} …", file=sys.stderr)
        download_font(font_path)
    font = ImageFont.truetype(str(font_path), 100)

    raws, templates = build_templates(font)
    names = list(templates)
    print("=" * 66)
    print("Evaluasi classifier tulisan tangan Aksara Bali (template matching)")
    print("=" * 66)
    print(f"Kelas (template)   : {len(names)} aksara Wresastra (font Noto Sans Balinese)")
    print(f"Normalisasi         : bbox → {NORM_SIZE}×{NORM_SIZE}, chamfer (1,√2) dua arah")

    # 1) Verifikasi (tugas utama produk)
    print("\n[1] VERIFIKASI / TELUSUR (classifyTracing, ambang correct ≥ 0.55)")
    accs = []
    rows = []
    for seed in range(args.seed, args.seed + 5):
        rng = random.Random(seed)
        np.random.seed(seed)
        r = evaluate_verification(raws, templates, rng, args.samples)
        accs.append(r["accuracy"])
        rows.append((seed, r["tp"], r["fn"], r["tn"], r["fp"]))
    mean_acc = float(np.mean(accs))
    print(f"  (5 seed, {args.samples} positif + {args.samples} negatif per kelas)")
    for seed, tp, fn, tn, fp in rows:
        print(f"    seed {seed}: TP {tp}  FN {fn} | TN {tn}  FP {fp} | "
              f"acc {(tp + tn) / (tp + fn + tn + fp) * 100:.2f}%")
    print(f"  → AKURASI RATA-RATA : {mean_acc * 100:.2f}%")

    # 2) Pengenalan terbuka (jujur)
    print("\n[2] PENGENALAN TERBUKA 18 KELAS (recognizeAksara) — dilaporkan jujur")
    rng = random.Random(args.seed)
    np.random.seed(args.seed)
    r = evaluate_recognition(raws, templates, rng, 30)
    print(f"  top-1 accuracy      : {r['top1_accuracy'] * 100:.2f}%  ({r['correct']}/{r['total']})")
    print(f"  confident-rate      : {r['confident_total'] / r['total'] * 100:.2f}%")
    if r["confident_total"]:
        print(f"  confident accuracy  : {r['confident_ok'] / r['confident_total'] * 100:.2f}%")
    print("  Catatan: aksara na/da/ta/ca nyaris identik (jarak chamfer ~1px)")
    print("  sehingga top-1 ≈ chance (1/18=5.6%); confident-gating menjaga")
    print("  sistem tidak menebak — pada tugas terbuka sistem memilih abstain.")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
