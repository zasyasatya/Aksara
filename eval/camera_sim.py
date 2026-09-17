"""Simulasi frame kamera → scan OCR (latin/auto) dengan degradasi realistis."""
import base64
import io
import json
import random
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, "."); sys.path.insert(0, "eval")
from backend.app.ocr import render as ocr_render


def to_camera(png_bytes: bytes, *, blur=1.1, shadow=0.55, noise=9.0, jpeg_q=78,
              downscale=1.0, seed=11) -> bytes:
    """PNG bersih → seperti foto kamera: bayangan tidak rata, blur, noise, JPEG."""
    img = Image.open(io.BytesIO(png_bytes)).convert("L")
    if downscale != 1.0:
        img = img.resize((max(8, int(img.width * downscale)), max(8, int(img.height * downscale))),
                         Image.BILINEAR)
    rng = np.random.default_rng(seed)
    arr = np.asarray(img, dtype=np.float32)
    h, w = arr.shape
    # gradien pencahayaan (lampu dari satu sisi)
    gx = np.linspace(1.0, shadow, w, dtype=np.float32)[None, :]
    gy = np.linspace(0.9, 1.05, h, dtype=np.float32)[:, None]
    arr = arr * gx * gy
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    if noise:
        arr = np.asarray(img, dtype=np.float32) + rng.normal(0, noise, (h, w)).astype(np.float32)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=jpeg_q)
    return buf.getvalue()


def scan(data: bytes, options: dict, annotate=False):
    body = json.dumps({
        "image": "data:image/jpeg;base64," + base64.b64encode(data).decode(),
        "options": options,
    }).encode()
    req = urllib.request.Request("http://127.0.0.1:8010/api/ocr/scan", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"HTTP_ERROR": e.code, "detail": e.read().decode()[:600]}


if __name__ == "__main__":
    pass

TEXT = "om swastiastu\nsareng sami"
SCENARIOS = {
    "webcam-hd-ringan   ": dict(blur=0.8, shadow=0.75, noise=6, jpeg_q=82, downscale=0.9),
    "webcam-hd-gelap    ": dict(blur=1.3, shadow=0.45, noise=13, jpeg_q=70, downscale=0.9),
    "kamera-hp-jauh     ": dict(blur=1.6, shadow=0.6, noise=10, jpeg_q=72, downscale=0.45),
    "foto-teks-kecil    ": dict(blur=0.9, shadow=0.7, noise=8, jpeg_q=75, downscale=0.3),
}

def _main():
  for label, kw in SCENARIOS.items():
    page = ocr_render.render_page(TEXT, font_size=44, rotate=1.0, noise=3, seed=5)
    data = to_camera(page, **kw)
    for script in ("latin", "auto"):
        res = scan(data, {"script": script, "tta": 2})
        if "HTTP_ERROR" in res:
            print(f"{label}[{script:5}] HTTP {res['HTTP_ERROR']}: {res['detail'][:200]}")
        else:
            print(f"{label}[{script:5}] det={res.get('detected_script'):7} "
                  f"latin={res.get('text', {}).get('latin')!r} warn={len(res.get('warnings', []))} "
                  f"ms={res.get('stats', {}).get('elapsed_ms')}")
    print("-")

if __name__ == "__main__":
    _main()
