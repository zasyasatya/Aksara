"""Generator dataset sintetis tulisan tangan Aksara Bali dari font.

Karena korpus tinta manusia berlabel untuk Aksara Bali masih langka, bootstrap
dataset dilakukan dengan merender glyph dari font **Noto Sans Balinese** (OFL)
lalu memberi augmentasi ala tulisan tangan:

- variasi bobot font (400–700) → ketebalan goresan berbeda
- rotasi, skala, *shear*, translasi (affine)
- distorsi elastis ringan (grid warp) → goresan "bergelombang" khas tangan
- dilasi/erosi acak → pena tebal/tipis
- noise garam & goresan pendek liar

Set kelas diambil dari ``aksara_master.json`` (label = id aksara, mis. ``ha``),
sehingga label dataset konsisten dengan sisa aplikasi.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .features import INK_THRESHOLD

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoSansBalinese.ttf"
RENDER_SIZE = 160


@dataclass(frozen=True)
class GlyphClass:
    label: str        # id kelas, mis. "ha", "kha", "akara", "angka_0"
    glyph: str        # string Unicode yang dirender
    name: str         # nama tampilan
    latin: str        # transliterasi
    group: str        # wresastra | swalalita | suara | angka


def build_classes(master: dict, groups: Sequence[str] = ("wresastra",)) -> List[GlyphClass]:
    """Bangun daftar kelas dari aksara_master.json untuk kelompok terpilih."""
    out: List[GlyphClass] = []
    seen = set()
    for group in groups:
        if group == "wresastra":
            items = master.get("wresastra", [])
        elif group == "swalalita":
            items = master.get("swalalita_extra", [])
        elif group == "suara":
            items = master.get("suara", [])
        elif group == "angka":
            items = master.get("angka", [])
        else:
            continue
        for it in items:
            glyph = it.get("bali") or ""
            if not glyph:
                continue
            label = it.get("id") or f"angka_{it.get('latin')}"
            if label in seen:
                continue
            seen.add(label)
            out.append(GlyphClass(
                label=label,
                glyph=glyph,
                name=it.get("name") or label,
                latin=str(it.get("latin") or ""),
                group=group,
            ))
    return out


class GlyphRenderer:
    """Render glyph → maska tinta float32 (RENDER_SIZE²) dengan bobot font variabel."""

    def __init__(self, font_path: Path = FONT_PATH, size: int = RENDER_SIZE):
        if not font_path.is_file():
            raise FileNotFoundError(f"Font tidak ditemukan: {font_path}")
        self.font_path = str(font_path)
        self.size = size
        self._fonts: dict[int, ImageFont.FreeTypeFont] = {}

    def _font(self, weight: int) -> ImageFont.FreeTypeFont:
        weight = int(min(700, max(400, weight)))
        weight = (weight // 50) * 50
        if weight not in self._fonts:
            f = ImageFont.truetype(self.font_path, int(self.size * 0.55))
            try:
                f.set_variation_by_axes([weight])
            except Exception:  # pragma: no cover - font statis
                pass
            self._fonts[weight] = f
        return self._fonts[weight]

    def render(self, glyph: str, weight: int = 500) -> np.ndarray:
        img = Image.new("L", (self.size, self.size), 255)
        d = ImageDraw.Draw(img)
        f = self._font(weight)
        # anchor tengah agar glyph dengan pangangge tinggi/rendah tetap di kanvas
        bbox = d.textbbox((0, 0), glyph, font=f)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (self.size - tw) / 2 - bbox[0]
        y = (self.size - th) / 2 - bbox[1]
        d.text((x, y), glyph, font=f, fill=0)
        lum = np.asarray(img, dtype=np.float32)
        return np.clip((INK_THRESHOLD - lum) / INK_THRESHOLD, 0.0, 1.0)


def _affine(img: Image.Image, rng: random.Random, strength: float) -> Image.Image:
    """Rotasi + skala + shear + translasi di sekitar pusat kanvas."""
    s = img.size[0]
    cx = cy = s / 2.0
    angle = np.deg2rad(rng.uniform(-14, 14) * strength)
    scale_x = rng.uniform(1 - 0.18 * strength, 1 + 0.18 * strength)
    scale_y = rng.uniform(1 - 0.18 * strength, 1 + 0.18 * strength)
    shear = rng.uniform(-0.28, 0.28) * strength
    tx = rng.uniform(-0.08, 0.08) * s * strength
    ty = rng.uniform(-0.08, 0.08) * s * strength
    ca, sa = np.cos(angle), np.sin(angle)
    # matriks output→input (PIL memakai invers): bangun forward lalu invers.
    fwd = np.array([
        [scale_x * ca, -scale_y * sa + shear * scale_x * ca, 0],
        [scale_x * sa, scale_y * ca + shear * scale_x * sa, 0],
        [0, 0, 1],
    ], dtype=np.float64)
    T1 = np.array([[1, 0, -cx], [0, 1, -cy], [0, 0, 1]])
    T2 = np.array([[1, 0, cx + tx], [0, 1, cy + ty], [0, 0, 1]])
    M = T2 @ fwd @ T1
    inv = np.linalg.inv(M)
    a, b, c = inv[0]
    d, e, f = inv[1]
    return img.transform((s, s), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BILINEAR, fillcolor=255)


def _elastic(img: Image.Image, rng: random.Random, strength: float) -> Image.Image:
    """Distorsi elastis ringan via mesh warp 4×4 (goresan tangan bergelombang)."""
    if strength <= 0:
        return img
    s = img.size[0]
    n = 4
    step = s / n
    amp = 0.035 * s * strength
    mesh = []
    jitter = {}
    for gy in range(n + 1):
        for gx in range(n + 1):
            edge = gx in (0, n) or gy in (0, n)
            jitter[(gx, gy)] = (0.0, 0.0) if edge else (rng.uniform(-amp, amp), rng.uniform(-amp, amp))
    for gy in range(n):
        for gx in range(n):
            x0, y0 = gx * step, gy * step
            x1, y1 = (gx + 1) * step, (gy + 1) * step
            box = (int(x0), int(y0), int(x1), int(y1))
            quad = []
            for (px, py) in ((x0, y0), (x0, y1), (x1, y1), (x1, y0)):
                jx, jy = jitter[(int(round(px / step)), int(round(py / step)))]
                quad.extend([px + jx, py + jy])
            mesh.append((box, tuple(quad)))
    return img.transform((s, s), Image.MESH, mesh, resample=Image.BILINEAR, fillcolor=255)


def augment(ink: np.ndarray, rng: random.Random, strength: float = 1.0) -> np.ndarray:
    """Terapkan augmentasi ala tulisan tangan pada maska tinta [0,1]."""
    strength = float(max(0.0, min(2.0, strength)))
    img = Image.fromarray((255 - ink * 255).astype(np.uint8), mode="L")
    if strength > 0:
        img = _affine(img, rng, strength)
        if rng.random() < 0.85:
            img = _elastic(img, rng, strength)
        r = rng.random()
        if r < 0.35:
            img = img.filter(ImageFilter.MinFilter(3))  # dilasi tinta (pena tebal)
        elif r < 0.5:
            img = img.filter(ImageFilter.MaxFilter(3))  # erosi (pena tipis)
        if rng.random() < 0.5:
            img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.2, 0.8) * strength))
    lum = np.asarray(img, dtype=np.float32)
    out = np.clip((INK_THRESHOLD - lum) / INK_THRESHOLD, 0.0, 1.0)
    if strength > 0 and rng.random() < 0.35:
        # goresan pendek liar / titik tinta
        s = out.shape[0]
        canvas = Image.fromarray((255 - out * 255).astype(np.uint8), mode="L")
        d = ImageDraw.Draw(canvas)
        for _ in range(rng.randint(1, 2)):
            x, y = rng.randint(10, s - 10), rng.randint(10, s - 10)
            d.line([(x, y), (x + rng.randint(-8, 8), y + rng.randint(-8, 8))], fill=0, width=rng.randint(1, 3))
        lum = np.asarray(canvas, dtype=np.float32)
        out = np.clip((INK_THRESHOLD - lum) / INK_THRESHOLD, 0.0, 1.0)
    if strength > 0 and rng.random() < 0.3:
        noise = np.random.default_rng(rng.getrandbits(32)).random(out.shape, dtype=np.float32)
        out = np.where(noise > 0.996, 1.0, out)
    return out.astype(np.float32)


def generate_samples(
    classes: Iterable[GlyphClass],
    per_class: int,
    seed: int = 20260904,
    strength: float = 1.0,
    renderer: Optional[GlyphRenderer] = None,
):
    """Yield ``(GlyphClass, ink_mask, meta)`` sejumlah ``per_class`` per kelas."""
    renderer = renderer or GlyphRenderer()
    rng = random.Random(seed)
    for cls in classes:
        for i in range(per_class):
            weight = rng.choice([400, 450, 500, 550, 600, 650, 700])
            base = renderer.render(cls.glyph, weight)
            local_strength = strength * rng.uniform(0.55, 1.15)
            ink = augment(base, rng, local_strength)
            yield cls, ink, {"weight": weight, "strength": round(local_strength, 3), "index": i}
