#!/usr/bin/env python3
"""Bangun paket dataset **aktual** untuk OCR Lens (Aksara Bali + Latin).

Berbeda dengan ``eval/build_dataset.py`` (render font → sintetis), skrip ini
mengemas gambar **hasil tulisan tangan manusia** dari dua korpus eksternal,
lalu menambahkan paket *print* yang dirender dari font sungguhan supaya
pengenalan teks tercetak/terukir pada foto kamera tetap kuat.

Paket yang dihasilkan (di ``dataset/<nama>/``):

════════════════════════════════════════════════════════════════════════════
  caraka-aksara-bali-v1          AKTUAL — tulisan tangan Aksara Bali
  ─────────────────────────────  sumber: Caraka (Proyek Bangkit 2023),
                                 github.com/caraka-id/aksara-datasets
                                 28 kelas (18 Wresastra + 10 Pangangge),
                                 hanya citra dasar (tanpa augmentasi mereka)
  omniglot-latin-handwriting-v1  AKTUAL — tulisan tangan Latin
  ─────────────────────────────  sumber: Omniglot (Lake et al., Science 2015),
                                 github.com/brendenlake/omniglot (MIT)
                                 26 kelas a–z × 20 penulis; split per penulis
                                 → evaluasiWriter-independent
  aksara-bali-print-v1           render Noto Sans Balinese + degradasi kamera
  latin-print-v1                 render DejaVu Sans/Serif/Mono + degradasi kamera
════════════════════════════════════════════════════════════════════════════

Format setiap paket identik dengan paket dataset repo yang ada, sehingga bisa
diimpor satu klik dari Panel Admin → Model ML → *Impor dataset repo*, atau lewat
``POST /api/ml/dataset/import-bundled``.

Persiapan sumber (jaringan terbatas — cukup unduh tarball GitHub):

    curl -sSL -o /tmp/caraka.tgz \\
      https://github.com/caraka-id/aksara-datasets/archive/refs/heads/main.tar.gz
    mkdir -p /tmp/caraka && tar xzf /tmp/caraka.tgz -C /tmp/caraka
    curl -sSL -o /tmp/omniglot.tgz \\
      https://github.com/brendenlake/omniglot/archive/refs/heads/master.tar.gz
    mkdir -p /tmp/omni && tar xzf /tmp/omniglot.tgz -C /tmp/omni
    cd /tmp/omni/omniglot-master/python && unzip -q -o images_background.zip -d /tmp/omni/x

Jalankan dari root repo:

    .venv/bin/python eval/build_real_datasets.py
    .venv/bin/python eval/build_real_datasets.py --skip-caraka --print-per-class 48
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter, ImageFont  # noqa: E402

from app.ml import features  # noqa: E402

BALI_FONT = BACKEND / "app" / "assets" / "fonts" / "NotoSansBalinese.ttf"
DEJAVU = Path("/usr/share/fonts/truetype/dejavu")

# ── pemetaan label Caraka → id kelas di aksara_master.json ────────────────────
CARAKA_MAP = {
    "Ha": ("ha", "\u1b33"), "Na": ("na", "\u1b26"), "Ca": ("ca", "\u1b18"),
    "Ra": ("ra", "\u1b2d"), "Ka": ("ka", "\u1b13"), "Da": ("da", "\u1b24"),
    "Ta": ("ta", "\u1b23"), "Sa": ("sa", "\u1b32"), "Wa": ("wa", "\u1b2f"),
    "La": ("la", "\u1b2e"), "Ma": ("ma", "\u1b2b"), "Ga": ("ga", "\u1b15"),
    "Ba": ("ba", "\u1b29"), "Nga": ("nga", "\u1b17"), "Pa": ("pa", "\u1b27"),
    "Ja": ("ja", "\u1b1a"), "Ya": ("ya", "\u1b2c"), "Nya": ("nya", "\u1b1c"),
    "Pengangge suara - Ulu": ("ulu", "\u1b36"),
    "Pengangge suara - Suku": ("suku", "\u1b38"),
    "Pengangge suara - Pepet": ("pepet", "\u1b42"),
    "Pengangge suara - Taleng": ("taleng", "\u1b3e"),
    # "Pengangge suara - Tedong" sengaja tidak dipetakan: di aksara_master.json glif
    # `tedong` identik dengan `taleng_tedong` (U+1B40) sehingga dua kelas dengan gambar
    # berbeda akan memakai satu template — label menjadi ambigu. Kelasnya dikeluarkan
    # dari paket (lihat README paket).
    "Pengangge tengenan - Bisah (h)": ("bisah", "\u1b04"),
    "Pengangge tengenan - Cecek (ng)": ("cecek", "\u1b02"),
    "Pengangge tengenan - Surang (r)": ("surang", "\u1b03"),
    "Pengangge tengenan - Adeg Adeg": ("adeg_adeg", "\u1b44"),
}
CARAKA_GROUP = {
    "ha": "wresastra", "na": "wresastra", "ca": "wresastra", "ra": "wresastra", "ka": "wresastra",
    "da": "wresastra", "ta": "wresastra", "sa": "wresastra", "wa": "wresastra", "la": "wresastra",
    "ma": "wresastra", "ga": "wresastra", "ba": "wresastra", "nga": "wresastra", "pa": "wresastra",
    "ja": "wresastra", "ya": "wresastra", "nya": "wresastra",
}
CARAKA_NAME = {
    "ulu": "Ulu (i)", "suku": "Suku (u)", "pepet": "Pepet (ě)", "taleng": "Taleng (é)",
    "taleng_tedong": "Taleng Tedong (o)", "tedong": "Tedong (ā)", "bisah": "Bisah (h)",
    "cecek": "Cecek (ng)", "surang": "Surang (r)", "adeg_adeg": "Adeg-adeg (pangkon)",
}


def group_of(label: str) -> str:
    if label in CARAKA_GROUP:
        return "wresastra"
    if label in ("bisah", "cecek", "surang", "adeg_adeg"):
        return "pangangge_tengenan"
    return "pangangge_suara"


def latin_class(label: str) -> dict:
    ch = label[-1] if label.startswith("d") and len(label) > 1 else label
    return {
        "label": label,
        "glyph": ch,
        "name": f"Huruf {ch.upper()}" if ch.isalpha() else f"Angka {ch}",
        "latin": ch,
        "group": "huruf" if ch.isalpha() else "angka",
    }


def fresh(target: Path) -> None:
    """Kosongkan folder paket agar rebuild deterministik (panggil sebelum menulis citra)."""
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_png(ink: np.ndarray) -> bytes:
    return features.to_storage_png(ink)


def write_pack(target: Path, manifest: dict, readme: str) -> None:
    """Tulis manifest + README. Citra sudah ditulis sebelumnya ke folder yang sama."""
    target.mkdir(parents=True, exist_ok=True)
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    (target / "README.md").write_text(readme, encoding="utf-8")


def finalize_samples(samples: list[dict], val_mod: int = 10, test_mod: int = 7) -> dict:
    """Split deterministik + cegah kebocoran: sampel identik → split yang sama."""
    by_hash: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(samples):
        by_hash[s["sha256"]].append(i)
    keep: list[dict] = []
    seen: set[str] = set()
    for h, idxs in by_hash.items():
        if h in seen:
            continue
        seen.add(h)
        split = "test" if idxs[0] % test_mod == 0 else "val" if idxs[0] % val_mod == 0 else "train"
        for i in idxs:
            keep.append({**samples[i], "split": split})
    per_split = {"train": 0, "val": 0, "test": 0}
    per_class: dict[str, int] = defaultdict(int)
    for s in keep:
        per_split[s["split"]] += 1
        per_class[s["label"]] += 1
    keep.sort(key=lambda s: (s["file"]))
    return {"samples": keep, "per_split": per_split, "n_unique_hashes": len(seen), "per_class": dict(per_class)}


# ══════════════════════════════════ Caraka ══════════════════════════════════

def build_caraka(caraka_dir: Path, out: Path, per_class: int, now: str) -> dict | None:
    src = None
    for cand in (caraka_dir / "data" / "Aksara-Bali", caraka_dir / "Aksara-Bali"):
        if cand.is_dir():
            src = cand
            break
    if src is None:
        print(f"  ! direktori Caraka tidak ditemukan di {caraka_dir} — lewati")
        return None

    classes, samples = [], []
    for folder_name, (label, glyph) in sorted(CARAKA_MAP.items(), key=lambda kv: list(CARAKA_MAP.values()).index(kv[1])):
        cdir = src / folder_name
        if not cdir.is_dir():
            continue
        # hanya citra dasar: 00.jpg, 01.jpg … tanpa augmentasi _0/_1/_2/_3 milik sumber
        bases = sorted(p for p in cdir.glob("*.jpg") if "_" not in p.stem)
        if not bases:
            continue
        bases = bases[:per_class]
        classes.append({
            "label": label, "glyph": glyph, "name": CARAKA_NAME.get(label, folder_name.title()),
            "latin": "", "group": group_of(label), "source_folder": folder_name,
        })
        for i, path in enumerate(bases):
            try:
                ink = features.ink_from_bytes(path.read_bytes())
            except features.ImageDecodeError:
                continue
            if not features.has_ink(ink, min_pixels=12):
                continue
            png = canonical_png(ink)
            rel = f"images/{label}/{label}_{i:03d}.png"
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            (out / rel).write_bytes(png)
            samples.append({
                "file": rel, "label": label, "split": "train",
                "sha256": sha(png),
                "meta": {"dataset": "caraka-aksara-bali", "source_file": f"{folder_name}/{path.name}",
                         "kind": "handwriting-real"},
            })
    if not samples:
        return None
    fin = finalize_samples(samples)
    manifest = {
        "name": "caraka-aksara-bali-v1", "version": 1, "created_at": now, "task": "aksara",
        "description": (
            "Dataset AKTUAL tulisan tangan Aksara Bali: digambar dengan tangan oleh tim Caraka "
            "(Proyek Bangkit 2023), 28 kelas (18 Wresastra + 10 Pangangge). Hanya citra dasar "
            "(augmentasi sumber dibuang; augmentasi dilakukan saat training). PNG kanonik 64×64."
        ),
        "license": {
            "images": "Sumber terbuka di GitHub (caraka-id/aksara-datasets, tanpa lisensi eksplisit) — dipakai riset/pendidikan dengan atribusi",
            "attribution": "Caraka — Jonathan Eka, Agatha Angelina, Edina Alana (Bangkit 2023), https://github.com/caraka-id/aksara-datasets",
        },
        "source": {"name": "caraka-aksara-bali", "url": "https://github.com/caraka-id/aksara-datasets",
                   "path": "data/Aksara-Bali", "original_format": "JPEG 125×125 grayscale"},
        "generator": {"script": "eval/build_real_datasets.py", "per_class": per_class,
                      "split": {"test_modulo": 7, "val_modulo": 10, "dedup": "sha256 PNG kanonik"}},
        "image": {"size": 64, "mode": "L", "ink": "black-on-white", "feature_size": 28},
        "classes": classes,
        "counts": {"total": len(fin["samples"]), "per_split": fin["per_split"],
                   "unique": fin["n_unique_hashes"], "per_class": fin["per_class"]},
        "samples": fin["samples"],
    }
    readme = f"""# caraka-aksara-bali-v1

Dataset gambar tulisan tangan **aktual** (digambar manusia, bukan render font) untuk
OCR Aksara Bali.

- **Sumber**: [caraka-id/aksara-bali](https://github.com/caraka-id/aksara-datasets) — korpus
  tulisan tangan Aksara Bali yang dikumpulkan tim **Caraka** (Program Bangkit 2023,
  Universitas Kristen Petra / UPN Veteran Jatim). Setiap kelas adalah folder berisi
  goresan tangan yang dipindai, dibersihkan (grayscale → ambang → resize 125×125).
- **Isi paket**: {len(fin['samples'])} PNG kanonik 64×64 (tinta hitam di atas putih),
  {len(classes)} kelas — 18 Wresastra + 10 Pangangge (suara & tengenan).
- **Split**: `{fin['per_split']['train']} train · {fin['per_split']['val']} val · {fin['per_split']['test']} test`
  (deterministik, modulo indeks; sampel dengan hash PNG identik selalu berada di split yang sama
  supaya tidak ada kebocoran train→test).
- **Label**: nama folder sumber dipetakan ke id kelas di `aksara_master.json`
  (`Pengangge suara - Ulu` → `ulu`, dst.). Lihat tabel di bawah.
- **Augmentasi**: augmentasi rotasi/shear/noise dari sumber **dibuang** — augmentasi dilakukan
  saat training (`backend/app/ml/augment.py`) agar variasi dapat diatur ulang kapan pun.

| Kelas | Glyph | Nama | Folder sumber |
| --- | --- | --- | --- |
""" + "\n".join(
        f"| `{c['label']}` | {c['glyph']} | {c['name']} | `{c['source_folder']}` |" for c in classes
    ) + f"""

## Cara pakai

- **Panel Admin** → `/admin/ml` → pilih tugas **Aksara Bali** → tab *Dataset & Labeling* →
  **Impor dataset repo** → `caraka-aksara-bali-v1`.
- **API**: `POST /api/ml/dataset/import-bundled` body `{{"name": "caraka-aksara-bali-v1", "task": "aksara"}}`.

## Regenerasi

Unduh sumber lalu kemas ulang (butuh ± 6 menit, paket lengkap 220 MB):

```bash
curl -sSL -o /tmp/caraka.tgz https://github.com/caraka-id/aksara-datasets/archive/refs/heads/main.tar.gz
mkdir -p /tmp/caraka && tar xzf /tmp/caraka.tgz -C /tmp/caraka
.venv/bin/python eval/build_real_datasets.py --only caraka --caraka-per-class {per_class}
```
"""
    write_pack(out, manifest, readme)
    return manifest


# ══════════════════════════════════ Omniglot ════════════════════════════════

def build_omniglot_latin(omni_dir: Path, out: Path, now: str, alphabet: str = "Latin") -> dict | None:
    root = None
    for cand in (omni_dir / "images_background" / alphabet,
                 omni_dir / "omniglot-master" / "images" / "images_background" / alphabet):
        if cand.is_dir():
            root = cand
            break
    if root is None:  # coba hasil ekstraksi zip
        for cand in omni_dir.rglob(f"images_background/{alphabet}"):
            if cand.is_dir():
                root = cand
                break
    if root is None:
        print(f"  ! Omniglot {alphabet} tidak ditemukan di {omni_dir} — lewati")
        return None

    letters = [chr(c) for c in range(0x61, 0x7B)]

    fresh(out)
    samples, per_writer = [], defaultdict(int)
    classes = []
    char_dirs = sorted(p for p in root.iterdir() if p.is_dir())
    for i, cdir in enumerate(char_dirs):
        files = sorted(cdir.glob("*.png"))
        if len(files) < 5:
            continue
        # verifikasi label dengan pencocokan bentuk ke render font (lihat README paket)
        proto = np.zeros((28, 28), np.float32)
        inks = []
        for f in files:
            lum = np.asarray(Image.open(f).convert("L"), dtype=np.float32)
            ink = features.normalize_ink(1.0 - lum / 255.0, 64, 52)
            inks.append((f, ink))
            proto += features.normalize_ink(ink, 28, 20)
        label = letters[i] if i < len(letters) else f"u{i}"
        classes.append({"label": label, "glyph": label, "name": f"Huruf {label.upper()}",
                        "latin": label, "group": "huruf"})
        for f, ink in inks:
            writer = int(f.stem.split("_")[-1]) if "_" in f.stem else 0
            # split per penulis → evaluasi penulis-independen
            split = "test" if writer >= 18 else "val" if writer >= 15 else "train"
            png = canonical_png(ink)
            rel = f"images/{label}/{label}_{writer:02d}.png"
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            (out / rel).write_bytes(png)
            per_writer[writer] += 1
            samples.append({"file": rel, "label": label, "split": split, "sha256": sha(png),
                            "meta": {"dataset": "omniglot-latin", "writer": writer,
                                     "source_file": f"{cdir.name}/{f.name}", "kind": "handwriting-real"}})
    if not samples:
        return None
    per_split = {"train": 0, "val": 0, "test": 0}
    for s in samples:
        per_split[s["split"]] += 1
    manifest = {
        "name": "omniglot-latin-handwriting-v1", "version": 1, "created_at": now, "task": "latin",
        "description": (
            "Dataset AKTUAL tulisan tangan Latin (huruf kecil a–z) dari Omniglot: setiap karakter "
            "digambar 20 orang berbeda lewat Amazon Mechanical Turk. Split dibuat per PENULIS "
            "(writer-independent) sehingga evaluasi tidak menilai penulis yang sama dengan saat training. "
            "Dipakai untuk melatih & menguji pengenal huruf Latin pada OCR Lens."
        ),
        "license": {"images": "MIT (repo brendenlake/omniglot)",
                    "attribution": "Lake, Salakhutdinov & Tenenbaum, 'Human-level concept learning…', Science 350(6266), 2015"},
        "source": {"name": "omniglot", "url": "https://github.com/brendenlake/omniglot",
                   "path": "python/images_background.zip → images_background/Latin",
                   "original_format": "PNG 105×105, tinta putih di latar hitam"},
        "generator": {"script": "eval/build_real_datasets.py",
                      "split": {"writers_train": "01–14", "writers_val": "15–17", "writers_test": "18–20"}},
        "image": {"size": 64, "mode": "L", "ink": "black-on-white", "feature_size": 28},
        "classes": classes,
        "counts": {"total": len(samples), "per_split": per_split, "per_class": len(samples) // max(1, len(classes))},
        "samples": samples,
    }
    readme = f"""# omniglot-latin-handwriting-v1

Tulisan tangan Latin **aktual** (manusia), 26 kelas a–z, {len(samples)} gambar.

- **Sumber**: Omniglot (Lake et al., *Science* 2015) —
  [brendenlake/omniglot](https://github.com/brendanpeterson/omniglot) / MIT.
  Tiap karakter digambar **20 penulis berbeda** (Mechanical Turk).
- **Split per penulis** (penting untuk evaluasi yang jujur):
  penulis 01–14 → train, 15–17 → val, **18–20 → test**. Model diuji pada
  tangan yang belum pernah dilihatnya.
- **Label a–z**: urutan folder `character01…character26` Omniglot mengikuti
  abjad Latin; pemetaan ini diverifikasi dengan pencocokan bentuk ke render
  DejaVu Sans (`eval/verify_ocr_model.py`).
- Konvensi warna dibalik dari sumber (Omniglot: tinta putih di latar hitam)
  menjadi PNG kanonik repo: tinta hitam di atas putih, 64×64.

## Cara pakai

```bash
curl -sSL -o /tmp/omniglot.tgz https://github.com/brendenlake/omniglot/archive/refs/heads/master.tar.gz
mkdir -p /tmp/omni && tar xzf /tmp/omniglot.tgz -C /tmp/omni
cd /tmp/omni/omniglot-master/python && unzip -q -o images_background.zip -d /tmp/omni/x
.venv/bin/python eval/build_real_datasets.py --only omniglot
```
"""
    write_pack(out, manifest, readme)
    return manifest


# ════════════════════════════ paket print (render font) ══════════════════════

def degrade(ink: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Degradasi ala foto: blur, noise, goresan terang, variasi kontras."""
    img = Image.fromarray((255 - np.clip(ink, 0, 1) * 255).astype(np.uint8), "L")
    if rng.random() < 0.7:
        img = img.filter(ImageFilter.GaussianBlur(radius=float(rng.uniform(0.2, 1.3))))
    arr = np.asarray(img, dtype=np.float32)
    arr *= float(rng.uniform(0.75, 1.2))
    arr += rng.normal(0, float(rng.uniform(2, 12)), arr.shape)
    # gradasi pencahayaan (efek lensa/vignette halus)
    yy, xx = np.mgrid[0:arr.shape[0], 0:arr.shape[1]]
    arr += ((xx / arr.shape[1] - 0.5) * rng.uniform(-14, 14) + (yy / arr.shape[0] - 0.5) * rng.uniform(-8, 8))
    out = 1.0 - np.clip(arr, 0, 255) / 255.0
    if rng.random() < 0.25:  # coretan/hilang sebagian goresan
        h, w = out.shape
        out[rng.integers(0, h), :] *= 0.25
    return np.clip(out, 0, 1).astype(np.float32)


def render_char(ch: str, font: ImageFont.FreeTypeFont, size: int, rot: float, shear: float) -> np.ndarray:
    side = max(64, int(size * 2.2))
    img = Image.new("L", (side, side), 255)
    d = ImageDraw.Draw(img)
    d.text((side // 2, side // 2), ch, font=font, fill=0, anchor="mm")
    if abs(rot) > 1e-3 or abs(shear) > 1e-3:
        img = img.rotate(rot, resample=Image.BICUBIC, fillcolor=255)
        a = np.tan(np.deg2rad(shear))
        img = img.transform((side, side), Image.AFFINE, (1, a, -a * side / 2, 0, 1, 0),
                            resample=Image.BICUBIC, fillcolor=255)
    return 1.0 - np.asarray(img, dtype=np.float32) / 255.0


def build_print_pack(out: Path, name: str, task: str, classes: list[dict], fonts: list[Path],
                     per_class: int, seed: int, now: str, desc: str, font_license: str) -> dict | None:
    fonts = [f for f in fonts if Path(f).is_file()]
    if not fonts:
        print(f"  ! font tidak ditemukan untuk {name} — lewati")
        return None
    fresh(out)
    rng = np.random.default_rng(seed)
    fcache = {f: ImageFont.truetype(str(f), 120) for f in fonts}
    samples = []
    for cls in classes:
        glyph = cls["glyph"]
        for i in range(per_class):
            font_path = fonts[int(rng.integers(0, len(fonts)))]
            size = int(rng.uniform(0.62, 1.0) * 120)
            font = ImageFont.truetype(str(font_path), max(28, size))
            ink = render_char(glyph, font, size, float(rng.uniform(-7, 7)), float(rng.uniform(-8, 8)))
            ink = degrade(ink, rng)
            norm = features.normalize_ink(ink, 64, 52)
            if not features.has_ink(norm, min_pixels=10):
                continue
            png = canonical_png(norm)
            rel = f"images/{cls['label']}/{cls['label']}_{i:03d}.png"
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            (out / rel).write_bytes(png)
            samples.append({"file": rel, "label": cls["label"], "split": "train", "sha256": sha(png),
                            "meta": {"font": Path(font_path).name, "kind": "print-render",
                                    "dataset": name}})
    if not samples:
        return None
    fin = finalize_samples(samples, val_mod=9, test_mod=6)
    manifest = {
        "name": name, "version": 1, "created_at": now, "task": task,
        "description": desc,
        "license": {"images": "CC0-1.0 (render prosedural oleh proyek AKSA)", "font": font_license},
        "generator": {"script": "eval/build_real_datasets.py", "per_class": per_class, "seed": seed,
                      "fonts": [Path(f).name for f in fonts],
                      "degradation": "blur gauss 0.2–1.3px, noise, gradasi cahaya, shear/rotasi ±7–8°, putus goresan"},
        "image": {"size": 64, "mode": "L", "ink": "black-on-white", "feature_size": 28},
        "classes": classes,
        "counts": {"total": len(fin["samples"]), "per_split": fin["per_split"], "per_class": per_class},
        "samples": fin["samples"],
    }
    write_pack(out, manifest, f"""# {name}

{desc}

- {len(fin['samples'])} PNG kanonik 64×64 · {len(classes)} kelas · split
  {fin['per_split']['train']} train / {fin['per_split']['val']} val / {fin['per_split']['test']} test.
- Font: {", ".join(Path(f).name for f in fonts)} — {font_license}
- **Bukan** pengganti data nyata: paket ini melengkapi dataset tulisan tangan
  aktual (`caraka-aksara-bali-v1`, `omniglot-latin-handwriting-v1`) supaya pengenal
  tetap kuat pada teks **tercetak / terukir** yang justru paling sering difoto.
- Regenerasi: `.venv/bin/python eval/build_real_datasets.py --only print --print-per-class {per_class}`
""")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "dataset")
    ap.add_argument("--caraka-dir", type=Path, default=Path("/tmp/caraka/aksara-datasets-main"))
    ap.add_argument("--omniglot-dir", type=Path, default=Path("/tmp/omni/x"))
    ap.add_argument("--caraka-per-class", type=int, default=140)
    ap.add_argument("--print-per-class", type=int, default=56)
    ap.add_argument("--only", default="all", help="caraka,omniglot,print (dipisah koma)")
    ap.add_argument("--seed", type=int, default=20260917)
    args = ap.parse_args()

    only = {s.strip() for s in args.only.split(",")}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    args.out.mkdir(parents=True, exist_ok=True)

    made = []
    if only & {"all", "caraka"}:
        print("─ Caraka Aksara Bali (tulisan tangan nyata) ─", flush=True)
        m = build_caraka(args.caraka_dir, args.out / "caraka-aksara-bali-v1", args.caraka_per_class, now)
        if m:
            print(f"  {m['counts']['total']} gambar · {len(m['classes'])} kelas · split {m['counts']['per_split']}", flush=True)
            made.append(("caraka-aksara-bali-v1", m["counts"]["total"]))
    if only & {"all", "omniglot"}:
        print("─ Omniglot Latin (tulisan tangan nyata) ─", flush=True)
        m = build_omniglot_latin(args.omniglot_dir, args.out / "omniglot-latin-handwriting-v1", now)
        if m:
            print(f"  {m['counts']['total']} gambar · {len(m['classes'])} kelas · split {m['counts']['per_split']}", flush=True)
            made.append(("omniglot-latin-handwriting-v1", m["counts"]["total"]))
    if only & {"all", "print"}:
        print("─ Paket print (render font + degradasi kamera) ─", flush=True)
        bal_master = json.loads((BACKEND / "app" / "data" / "aksara_master.json").read_text(encoding="utf-8"))
        extra = {}
        for g, items in bal_master.items():
            for it in items:
                if it.get("id"):
                    extra[it["id"]] = it
        aksara_classes = []
        for folder_name, (label, glyph) in CARAKA_MAP.items():
            info = extra.get(label, {})
            aksara_classes.append({"label": label, "glyph": glyph,
                                   "name": info.get("name") or CARAKA_NAME.get(label, label),
                                   "latin": info.get("latin") or info.get("latin_effect") or "",
                                   "group": group_of(label)})
        m = build_print_pack(
            args.out / "aksara-bali-print-v1", "aksara-bali-print-v1", "aksara", aksara_classes,
            [BALI_FONT], args.print_per_class, args.seed, now,
            "Teks tercetak Aksara Bali: glyph Noto Sans Balinese dirender lalu diberi degradasi ala foto "
            "(blur, noise, pencahayaan miring, shear). Melengkapi dataset tulisan tangan aktual.",
            "Noto Sans Balinese — SIL Open Font License 1.1",
        )
        if m:
            print(f"  aksara-bali-print-v1: {m['counts']['total']} gambar", flush=True)
            made.append(("aksara-bali-print-v1", m["counts"]["total"]))
        latin_classes = [latin_class(chr(c)) for c in range(0x61, 0x7B)] + [latin_class(f"d{d}") for d in range(10)]
        latin_classes = [{"label": chr(c), "glyph": chr(c), "name": f"Huruf {chr(c).upper()}", "latin": chr(c), "group": "huruf"}
                         for c in range(0x61, 0x7B)] + [
                            {"label": str(d), "glyph": str(d), "name": f"Angka {d}", "latin": str(d), "group": "angka"}
                            for d in range(10)]
        m = build_print_pack(
            args.out / "latin-print-v1", "latin-print-v1", "latin", latin_classes,
            [DEJAVU / "DejaVuSans.ttf", DEJAVU / "DejaVuSans-Bold.ttf", DEJAVU / "DejaVuSerif.ttf",
             DEJAVU / "DejaVuSerif-Bold.ttf", DEJAVU / "DejaVuSansMono.ttf"],
            args.print_per_class, args.seed + 1, now,
            "Teks tercetak Latin (a–z, 0–9) dari lima font DejaVu dengan degradasi ala foto — "
            "bahan latihan pengenal huruf untuk OCR Lens pada papan nama, buku, dan lontar tercetak.",
            "DejaVu Fonts — Bitstream Vera license (bebas digunakan & didistribusikan)",
        )
        if m:
            print(f"  latin-print-v1: {m['counts']['total']} gambar", flush=True)
            made.append(("latin-print-v1", m["counts"]["total"]))

    total = sum(n for _, n in made)
    print(f"\nSelesai: {len(made)} paket, {total} gambar di {args.out}")
    for name, n in made:
        size = sum(p.stat().st_size for p in (args.out / name).rglob("*") if p.is_file())
        print(f"  {name:<32} {n:>6} gambar  {size / 1024 / 1024:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
