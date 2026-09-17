"""Augmentasi on-the-fly untuk training (NumPy + Pillow, tanpa dependensi berat).

Dataset aktual untuk Aksara Bali & tulisan tangan Latin berukuran kecil (ratusan
hingga ribuan sampel per kelas), jadi penyebab utama overfit adalah variasi
gaya tulis, ketebalan pena, resolusi kamera, blur fokus, dan kemiringan. Semua
itu disimulasikan *saat training* (bukan disimpan sebagai file), sehingga admin
dapat menaikkan/turunkan ``augment`` tanpa menyentuh dataset.

Maska yang dipakai di sini adalah vektor fitur kanonik 28×28 (0..1, 1 = tinta)
— bentuk yang sama dengan yang dikonsumsi model.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

from .features import FEATURE_SIZE


def _to_img(ink01: np.ndarray) -> Image.Image:
    """maska tinta (1=ink) → PIL 'L' (0=ink, 255=putih)."""
    return Image.fromarray((255 - np.clip(ink01, 0, 1) * 255).astype(np.uint8), "L")


def _to_mask(img: Image.Image) -> np.ndarray:
    lum = np.asarray(img, dtype=np.float32)
    return np.clip((200.0 - lum) / 200.0, 0.0, 1.0).astype(np.float32)


def augment_one(ink01: np.ndarray, rng: np.random.Generator, strength: float = 1.0,
                max_side: int = FEATURE_SIZE, task: str = "latin") -> np.ndarray:
    """Satu maska (H×W, 1=tinta) → maska teraugmentasi ukuran sama.

    ``strength`` 0 = identitas, 1 = penuh (dipakai saat training), >1 = agresif.

    ``task`` menata derajat distorsi: aksara Bali berstruktur multi-bagian tipis
    (gantungan/aksara suara) yang rusak oleh blur & derau kuat — diuji empiris model
    aksara jeblok 94→86% bila dipaksa konfigurasi latin — sehingga aksara memakai
    versi lebih ringan, sedangkan latin (huruf tegas beruji pada kamera buram nyata)
    memakai versi kuat.
    """
    heavy = task != "aksara"
    strength = float(max(0.0, min(2.0, strength)))
    if strength <= 0:
        return ink01.astype(np.float32, copy=True)
    side = max_side
    img = _to_img(ink01)
    if img.size[0] != side or img.size[1] != side:
        img = img.resize((side, side), Image.BILINEAR)

    angle = float(rng.uniform(-11, 11)) * strength
    shift_x = float(rng.uniform(-2.6, 2.6)) * strength
    shift_y = float(rng.uniform(-2.6, 2.6)) * strength
    scale = 1.0 + float(rng.uniform(-0.16, 0.16)) * strength
    shear = float(rng.uniform(-9, 9)) * strength
    img = img.rotate(angle, resample=Image.BILINEAR, fillcolor=255, translate=(shift_x, shift_y))
    if abs(shear) > 0.2:
        a = np.tan(np.deg2rad(shear))
        img = img.transform(img.size, Image.AFFINE, (1, a, -a * side / 2, 0, 1, 0),
                            resample=Image.BILINEAR, fillcolor=255)
    if abs(scale - 1.0) > 0.01:
        w = max(4, int(round(side * scale)))
        h = max(4, int(round(side * scale)))
        img = img.resize((w, h), Image.BILINEAR)
        canvas = Image.new("L", (side, side), 255)
        canvas.paste(img, ((side - w) // 2, (side - h) // 2))
        img = canvas

    r = float(rng.random())
    if r < 0.30 * strength:
        img = img.filter(ImageFilter.MinFilter(3))        # pena tebal (dilasi tinta)
    elif r < 0.45 * strength:
        img = img.filter(ImageFilter.MaxFilter(3))        # pena tipis (erosi tinta)
    # Blur fokus kamera. Untuk latin, rentang atas diperlebar (≈1,5px pada kanvas
    # 28×28) karena bidikan Lens nyata sering setara blur page 1,1–1,5px pada huruf
    # 25–40px; tanpa contoh seburam itu model mengacaukan pasangan mirip (e→k, u→m,
    # i→l). Aksara dipertahankan ringan — goresan tipisnya mudah musnah.
    if heavy:
        if rng.random() < 0.60:
            img = img.filter(ImageFilter.GaussianBlur(radius=float(rng.uniform(0.1, 1.25)) * strength))
    elif rng.random() < 0.40 * strength:
        img = img.filter(ImageFilter.GaussianBlur(radius=float(rng.uniform(0.1, 0.9)) * strength))

    out = _to_mask(img)
    if rng.random() < 0.22 * strength:                     # garis fokus hilang / kotoran
        h, w = out.shape
        y = int(rng.integers(0, h))
        out[max(0, y - 1):y + 2, :] *= 0.2
    if rng.random() < 0.30 * strength:                     # bintik noise kamera
        noise = rng.random(out.shape).astype(np.float32)
        out = np.where(noise > 0.994, 1.0, out)
    if heavy and rng.random() < 0.45 * strength:           # derau Gaussian (sensor gelap)
        sigma_g = float(rng.uniform(0.02, 0.10)) * strength
        out = out + rng.normal(0.0, sigma_g, out.shape).astype(np.float32)
    if rng.random() < (0.50 if heavy else 0.35) * strength:  # tinta pudar / kontras rendah
        out = out * float(rng.uniform(0.62, 1.12) if heavy else rng.uniform(0.78, 1.08))
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def augment_batch(X: np.ndarray, y: np.ndarray, rng: np.random.Generator,
                  strength: float = 1.0, task: str = "latin") -> tuple[np.ndarray, np.ndarray]:
    """Augmentasi sekumpulan vektor fitur ``N×784`` (baris = 28×28)."""
    if strength <= 0:
        return X, y
    n = X.shape[0]
    side = int(round(X.shape[1] ** 0.5))
    out = np.empty_like(X)
    for i in range(n):
        m = X[i].reshape(side, side)
        out[i] = augment_one(m, rng, strength, max_side=side, task=task).reshape(-1)
    return out, y


def balanced_indices(y: np.ndarray, rng: np.random.Generator, power: float = 0.5) -> np.ndarray:
    """Indeks sampel dengan bobot kelas ``∝ n_kelas^-power`` (kurangi efek kelas langka).

    - ``0``   → distribusi dataset apa adanya (default aman)
    - ``0.5`` → akar: koreksi ketidakseimbangan ringan
    - ``1``   → setiap kelas sama sering dilihat (oversampling penuh)
    """
    n = len(y)
    power = float(power or 0.0)
    if power <= 0 or n == 0:
        return np.arange(n)
    classes, counts = np.unique(y, return_counts=True)
    if len(classes) < 2:
        return np.arange(n)
    inv = counts.astype(np.float64) ** (-power)
    per_class = dict(zip(classes.tolist(), inv.tolist()))
    w = np.array([per_class[int(c)] for c in y], dtype=np.float64)
    w /= w.sum()
    return rng.choice(n, size=n, replace=True, p=w)
