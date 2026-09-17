"""Perender teks → citra halaman (untuk **uji mandiri** pipeline tanpa dataset).

Dipakai admin lewat ``GET /api/ocr/selftest``: kalimat_known dirender dengan font
yang sama dengan dataset cetak, di-OCR, lalu dibandingkan dengan ground truth.
Ini bukan pengganti evaluasi di split test (itu ``/api/ml``), tapi tombol cepat
"apakah segmentasi + decoding masih benar?" setelah mengubah konfigurasi.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

FONT_DIRS = [
    Path(__file__).resolve().parent.parent / "assets" / "fonts",
    Path(__file__).resolve().parent.parent / "data" / "assets" / "fonts",
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/truetype"),
]


def has_balinese_font() -> bool:
    """Apakah font Aksara Bali tersedia (dipakai untuk uji mandiri)."""
    return any((base / "NotoSansBalinese.ttf").is_file() or (base / "NotoSansBalinese-Regular.ttf").is_file()
               for base in FONT_DIRS)


def find_font(preferred: str) -> Optional[Path]:
    from PIL import ImageFont

    for base in FONT_DIRS:
        if not base.is_dir():
            continue
        exact = base / preferred
        if exact.is_file():
            return exact
        hits = [h for h in sorted(base.glob("*.ttf")) + sorted(base.glob("*.otf"))]
        for h in hits:  # nama cocok → file terbaik
            if preferred.lower().split(".")[0] in h.name.lower():
                return h
        plain = [h for h in hits if not any(k in h.name for k in ("Bold", "Oblique", "Italic"))]
        if plain:
            return plain[0]
        if hits:
            return hits[0]
    return None


def render_page(text: str, *, font_file: Optional[str] = None, font_size: int = 34,
                width: int = 900, margin: int = 34, leading: float = 1.9,
                rotate: float = 0.4, noise: int = 0, seed: int = 7) -> bytes:
    """Render teks multi-baris ke PNG (halaman gelap di atas kertas terang)."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    path = Path(font_file) if font_file else find_font(
        "NotoSansBalinese-Regular.ttf" if text and any(ord(c) >= 0x1B00 for c in text)
        else "DejaVuSans.ttf"
    )
    if path is None:
        raise RuntimeError("Font TTF tidak tersedia untuk uji mandiri.")
    from PIL import ImageFont

    font = ImageFont.truetype(str(path), font_size)
    lines = text.split("\n")
    line_h = int(font_size * leading)
    img = Image.new("L", (width, line_h * len(lines) + margin * 2), 232)
    draw = ImageDraw.Draw(img)
    y = margin
    for ln in lines:
        draw.text((margin, y), ln, font=font, fill=32)
        y += line_h
    if rotate:
        img = img.rotate(random.Random(seed).uniform(-rotate, rotate), expand=True, fillcolor=232)
    if noise:
        rng = random.Random(seed)
        px = img.load()
        for _ in range(width * img.height // 400 * noise // 10):
            px[rng.randrange(img.width), rng.randrange(img.height)] = rng.randint(120, 200)
        img = img.filter(ImageFilter.GaussianBlur(0.7))
    else:
        img = img.filter(ImageFilter.GaussianBlur(0.6))
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


CER_PHRASES: Dict[str, List[str]] = {
    "aksara": [
        "ᬩᬮ",
        "ᬩᬮᬶ",
        "ᬅᬓ᭄ᬱᬭᬩᬮ",
        "ᬓᬭ",
        "ᬦᬫᬲ᭄ᬢ᭄ᬬᬲ᭄ᬢᬸ",
    ],
    "latin": [
        "Balinese script",
        " aksara bali ",
        "hello world",
        "Ok",
        "Oo",
    ],
}


def _levenshtein(a: List[str], b: List[str]) -> int:
    n, m = len(a), len(b)
    if n == 0:
        return m
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return prev[m]


def selftest(task: str, options: dict, phrases: Optional[List[str]] = None,
             font_size: int = 34) -> Dict:
    """OCR citra render dan bandingkan dengan ground truth (label space)."""
    from ..ml import store
    from . import pipeline

    lookup = store.class_lookup(task)
    char_to_label = {(c.get("glyph") or ""): c["label"] for c in store.get_classes(task) if c.get("glyph")}
    labels = {c["label"]: (c.get("unicode") or c.get("glyph") or c["label"])
              for c in store.get_classes(task) if c.get("label")}
    phrases = phrases or CER_PHRASES.get(task, [])
    # uji mandiri tahu skrip apa yang dirender → paksa, supaya yang diukur
    # kualitas segmentasi/klasifikasinya, bukan tebak-tebakan skrip
    options = {**(options or {}), "script": task}
    rows: List[Dict] = []
    total_edit = total_len = 0
    exact = 0
    for text in phrases:
        if task == "aksara":
            truth = [v for v in (char_to_label.get(ch) for ch in text if ch.strip()) if v]
        else:
            truth = [ch.lower() for ch in text if ch.strip()]
        png = render_page(text, font_size=font_size)
        res = pipeline.scan_bytes(png, options=options)
        hypo: List[str] = []
        for line in res["lines"]:
            hypo += [g["label"] for g in line["glyphs"] if g.get("label")]
        edit = _levenshtein(truth, hypo)
        total_edit += edit
        total_len += max(1, len(truth))
        exact += int(hypo == truth)
        rows.append({
            "reference": "".join(labels.get(l, "?") for l in truth),
            "hypothesis": "".join(labels.get(l, "?") for l in hypo),
            "truth_labels": truth,
            "hypo_labels": hypo,
            "cer": round(edit / max(1, len(truth)), 3),
            "exact": hypo == truth,
            "lines": len(res["lines"]), "scripts": sorted({ln["script"] for ln in res["lines"]}),
        })
    n = max(1, len(rows))
    return {
        "task": task,
        "samples": len(rows),
        "exact_line_rate": round(exact / n, 3),
        "cer": round(total_edit / total_len, 3),
        "rows": rows,
    }
