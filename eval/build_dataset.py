#!/usr/bin/env python3
"""Bangun paket dataset gambar Aksara Bali yang dikomit ke repo (``dataset/``).

Dataset ini adalah **artefak yang sama** dengan yang dipakai percobaan
``eval/ml_experiments.py`` dan dapat diimpor satu-klik dari Panel Admin →
Model ML → Dataset → *Impor dataset repo* (endpoint
``POST /api/ml/dataset/import-bundled``).

Tata letak paket:

    dataset/<name>/
    ├── manifest.json            metadata: kelas, split per sampel, seed, lisensi
    ├── README.md                deskripsi singkat + cara pakai
    └── images/<label>/<label>_NNN.png   PNG kanonik 64×64 (tinta hitam di atas putih)

Sampel dibangkitkan dengan renderer + augmentasi yang sama persis dengan
``backend/app/ml/synthetic.py`` (font Noto Sans Balinese, SIL OFL 1.1), split
train/val/test 70/15/15 di-stratifikasi per label dengan seed tetap, sehingga
hasil percobaan dapat direproduksi.

Jalankan dari root repo:

    .venv/bin/python eval/build_dataset.py                       # default: 60/kelas, 18 kelas Wresastra
    .venv/bin/python eval/build_dataset.py --per-class 80 --groups wresastra,angka --name aksara-bali-v2
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import numpy as np  # noqa: E402

from app.ml import features, store, synthetic  # noqa: E402


def stratified_splits(n: int, rng: np.random.Generator, val_ratio: float, test_ratio: float):
    idx = rng.permutation(n)
    n_test = int(round(n * test_ratio))
    n_val = int(round(n * val_ratio))
    out = ["train"] * n
    for rank, i in enumerate(idx):
        out[i] = "test" if rank < n_test else "val" if rank < n_test + n_val else "train"
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="aksara-bali-handwriting-v1")
    ap.add_argument("--groups", default="wresastra")
    ap.add_argument("--per-class", type=int, default=60)
    ap.add_argument("--seed", type=int, default=20260904)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--val-ratio", type=float, default=0.15)
    ap.add_argument("--test-ratio", type=float, default=0.15)
    ap.add_argument("--out", type=Path, default=ROOT / "dataset")
    args = ap.parse_args()

    groups = [g.strip() for g in args.groups.split(",") if g.strip()]
    classes = synthetic.build_classes(store._master(), tuple(groups))
    if not classes:
        ap.error("tidak ada kelas untuk kelompok tersebut")

    target = args.out / args.name
    images_dir = target / "images"
    if target.exists():
        shutil.rmtree(target)
    images_dir.mkdir(parents=True)

    rng = np.random.default_rng(args.seed)
    samples = []
    per_split = {"train": 0, "val": 0, "test": 0}
    print(f"Membangun {args.name}: {len(classes)} kelas × {args.per_class} sampel …", flush=True)
    gen = synthetic.generate_samples(classes, args.per_class, args.seed, args.strength)
    buckets: dict[str, list] = {c.label: [] for c in classes}
    for cls, ink, meta in gen:
        buckets[cls.label].append((ink, meta))
    for cls in classes:
        items = buckets[cls.label]
        splits = stratified_splits(len(items), rng, args.val_ratio, args.test_ratio)
        (images_dir / cls.label).mkdir(exist_ok=True)
        for i, ((ink, meta), split) in enumerate(zip(items, splits)):
            png = features.to_storage_png(ink)
            rel = f"images/{cls.label}/{cls.label}_{i:03d}.png"
            (target / rel).write_bytes(png)
            samples.append({
                "file": rel,
                "label": cls.label,
                "split": split,
                "sha256": hashlib.sha256(png).hexdigest()[:16],
                "meta": {"weight": meta["weight"], "strength": meta["strength"]},
            })
            per_split[split] += 1
        print(f"  {cls.label:>6}: {len(items)} sampel", flush=True)

    manifest = {
        "name": args.name,
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "description": (
            "Dataset gambar tulisan tangan sintetis Aksara Bali: glyph dirender dari font Noto Sans Balinese "
            "(bobot 400–700) lalu diaugmentasi (afinitas, distorsi elastis, tebal goresan, noise, putus goresan). "
            "PNG kanonik 64×64, tinta hitam di atas putih."
        ),
        "license": {
            "images": "CC0-1.0 (dibangkitkan secara prosedural oleh proyek AKSA)",
            "font": "Noto Sans Balinese — SIL Open Font License 1.1 (backend/app/assets/fonts/OFL.txt)",
        },
        "generator": {
            "script": "eval/build_dataset.py",
            "module": "backend/app/ml/synthetic.py",
            "seed": args.seed,
            "strength": args.strength,
            "per_class": args.per_class,
            "groups": groups,
            "split": {"val_ratio": args.val_ratio, "test_ratio": args.test_ratio, "stratified": True},
        },
        "image": {"size": 64, "mode": "L", "ink": "black-on-white", "feature_size": 28},
        "classes": [{"label": c.label, "glyph": c.glyph, "name": c.name, "latin": c.latin, "group": c.group} for c in classes],
        "counts": {"total": len(samples), "per_split": per_split, "per_class": args.per_class},
        "samples": samples,
    }
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    readme = f"""# {args.name}

Dataset gambar tulisan tangan **sintetis** Aksara Bali — {len(classes)} kelas
({", ".join(groups)}), {args.per_class} sampel/kelas, total **{len(samples)}** PNG 64×64
(train {per_split['train']} · val {per_split['val']} · test {per_split['test']}, stratified per kelas).

| Kelas | Glyph | Nama |
| --- | --- | --- |
""" + "\n".join(f"| `{c.label}` | {c.glyph} | {c.name} |" for c in classes) + f"""

## Cara pakai

- **Panel Admin** → `/admin/ml` → tab *Dataset & Labeling* → **Impor dataset repo** →
  pilih `{args.name}` → *Impor*. Label dan split mengikuti `manifest.json`.
- **API**: `POST /api/ml/dataset/import-bundled` body `{{"name": "{args.name}"}}`.
- **Python**: baca `manifest.json` (`samples[].file`, `label`, `split`).

## Regenerasi

```bash
.venv/bin/python eval/build_dataset.py --name {args.name} --per-class {args.per_class} --seed {args.seed}
```

Gambar dibangkitkan prosedural dari font Noto Sans Balinese (SIL OFL 1.1) dengan
augmentasi yang sama seperti tombol *Generate sintetis* di panel admin
(`backend/app/ml/synthetic.py`), seed `{args.seed}`. Dataset ini adalah artefak
yang dipakai percobaan `eval/ml_experiments.py` (lihat `docs/ML_RETRAINING.md`).
"""
    (target / "README.md").write_text(readme, encoding="utf-8")
    size = sum(p.stat().st_size for p in target.rglob("*") if p.is_file())
    print(f"Selesai: {len(samples)} gambar → {target} ({size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
