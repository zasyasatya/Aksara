"""Decode & normalisasi gambar tulisan tangan → vektor fitur.

Pipeline (sama untuk sampel sintetis, unggahan, dan kanvas):

    bytes/dataURL → PIL → komposit putih → luminansi → maska tinta [0,1]
        → crop bounding-box → skala (jaga aspek) ke kotak ``inner``
        → letakkan di kanvas ``size``×``size`` dengan pusat massa di tengah

Representasi kanonik yang disimpan di dataset adalah PNG 64×64 (tinta hitam di
atas putih). Vektor fitur untuk model adalah 28×28 (inner 20) — konvensi MNIST,
sehingga arsitektur klasik maupun CNN kecil bekerja dengan baik.
"""

from __future__ import annotations

import base64
import io
import re
from typing import Optional

import numpy as np
from PIL import Image

INK_THRESHOLD = 200      # luminansi < 200 dianggap tinta (sama dengan classifier on-device)
BBOX_THRESHOLD = 0.2     # nilai maska minimal untuk dihitung sebagai tinta pada bbox
STORAGE_SIZE = 64        # PNG kanonik di dataset
STORAGE_INNER = 52
FEATURE_SIZE = 28        # ukuran fitur model
FEATURE_INNER = 20
N_FEATURES = FEATURE_SIZE * FEATURE_SIZE


class ImageDecodeError(ValueError):
    """Gambar tidak valid / tidak dapat didekode."""


_DATA_URL_RE = re.compile(r"^data:[^;,]+(?:;[^;,]+)*;base64,(.*)$", re.S)


def decode_base64_image(payload: str) -> bytes:
    """Terima data URL (``data:image/png;base64,...``) atau base64 polos."""
    if not isinstance(payload, str) or not payload.strip():
        raise ImageDecodeError("Gambar kosong.")
    s = payload.strip()
    m = _DATA_URL_RE.match(s)
    if m:
        s = m.group(1)
    s = re.sub(r"\s+", "", s)
    try:
        data = base64.b64decode(s, validate=False)
    except Exception as exc:  # pragma: no cover - defensif
        raise ImageDecodeError("Base64 gambar tidak valid.") from exc
    if len(data) < 16:
        raise ImageDecodeError("Data gambar terlalu kecil.")
    return data


def ink_from_bytes(data: bytes) -> np.ndarray:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as exc:
        raise ImageDecodeError("Gambar tidak dapat dibaca (format tidak didukung?).") from exc
    return ink_from_image(img)


def ink_from_image(img: Image.Image) -> np.ndarray:
    """PIL image → maska tinta float32 H×W di [0,1] (1 = tinta pekat).

    Transparansi dikomposit ke putih (kanvas tinta di browser transparan).
    Gambar dengan latar gelap & tinta terang (mis. MNIST-style) dibalik otomatis.
    """
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        bg.alpha_composite(rgba)
        gray = bg.convert("L")
    else:
        gray = img.convert("L")
    if max(gray.size) > 1024:
        gray.thumbnail((1024, 1024), Image.LANCZOS)
    lum = np.asarray(gray, dtype=np.float32)
    if lum.size == 0:
        raise ImageDecodeError("Gambar kosong.")
    # Heuristik latar gelap: pinggiran gambar rata-rata gelap → balik.
    border = np.concatenate([lum[0, :], lum[-1, :], lum[:, 0], lum[:, -1]])
    if border.mean() < 100 and lum.mean() < 128:
        lum = 255.0 - lum
    ink = np.clip((INK_THRESHOLD - lum) / INK_THRESHOLD, 0.0, 1.0)
    return ink.astype(np.float32)


def ink_bbox(ink: np.ndarray, threshold: float = BBOX_THRESHOLD) -> Optional[tuple[int, int, int, int]]:
    ys, xs = np.where(ink > threshold)
    if ys.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def has_ink(ink: np.ndarray, min_pixels: int = 6) -> bool:
    return int((ink > BBOX_THRESHOLD).sum()) >= min_pixels


def normalize_ink(ink: np.ndarray, size: int = FEATURE_SIZE, inner: int = FEATURE_INNER) -> np.ndarray:
    """Crop bbox → skala jaga-aspek ke ``inner`` → pusatkan berdasarkan pusat massa.

    Mengembalikan float32 ``size``×``size`` di [0,1]. Kosong bila tidak ada tinta.
    """
    out = np.zeros((size, size), dtype=np.float32)
    box = ink_bbox(ink)
    if box is None:
        return out
    x0, y0, x1, y1 = box
    crop = ink[y0:y1, x0:x1]
    h, w = crop.shape
    scale = inner / float(max(h, w))
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    im = Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8), mode="L")
    resample = Image.LANCZOS if scale < 1 else Image.BILINEAR
    im = im.resize((nw, nh), resample)
    arr = np.asarray(im, dtype=np.float32) / 255.0
    arr = np.clip(arr, 0.0, 1.0)

    # Pusat massa → tengah kanvas (konvensi MNIST) agar translasi tidak memengaruhi fitur.
    total = float(arr.sum())
    if total > 0:
        ys, xs = np.mgrid[0:nh, 0:nw]
        cy = float((arr * ys).sum() / total)
        cx = float((arr * xs).sum() / total)
    else:
        cy, cx = (nh - 1) / 2.0, (nw - 1) / 2.0
    top = int(round((size - 1) / 2.0 - cy))
    left = int(round((size - 1) / 2.0 - cx))
    top = min(max(top, 0), size - nh)
    left = min(max(left, 0), size - nw)
    out[top:top + nh, left:left + nw] = arr
    return out


def features_from_ink(ink: np.ndarray) -> np.ndarray:
    """Vektor fitur 784-d (28×28) float32."""
    return normalize_ink(ink, FEATURE_SIZE, FEATURE_INNER).reshape(-1)


def to_storage_png(ink: np.ndarray) -> bytes:
    """Maska tinta → PNG kanonik 64×64 (tinta hitam di atas putih)."""
    norm = normalize_ink(ink, STORAGE_SIZE, STORAGE_INNER)
    img = Image.fromarray((255 - norm * 255).astype(np.uint8), mode="L")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def ink_from_storage_png(data: bytes) -> np.ndarray:
    """Kebalikan ``to_storage_png`` — tanpa ambang luminansi (sudah kanonik)."""
    img = Image.open(io.BytesIO(data)).convert("L")
    lum = np.asarray(img, dtype=np.float32)
    return (1.0 - lum / 255.0).astype(np.float32)


def png_data_url(arr01: np.ndarray, scale: int = 1) -> str:
    """Array [0,1] (1 = tinta) → data URL PNG hitam-di-atas-putih (untuk preview UI)."""
    img = Image.fromarray((255 - np.clip(arr01, 0, 1) * 255).astype(np.uint8), mode="L")
    if scale > 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
