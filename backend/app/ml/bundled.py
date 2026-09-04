"""Dataset gambar yang *dikomit ke repo* (``<repo>/dataset/<name>/``).

Setiap paket berisi ``manifest.json`` (kelas, daftar sampel dengan label & split)
dan folder ``images/``. Paket dibuat oleh ``eval/build_dataset.py`` dan dapat
diimpor ke store ML dengan satu klik dari Panel Admin, sehingga admin baru
langsung punya data awal untuk retraining tanpa harus generate/unggah dulu.

Lokasi dicari berurutan (yang pertama ada dipakai):

1. env ``AKSARA_DATASET_DIR``
2. ``<repo>/dataset`` (checkout sumber: backend/app/ml → ../../../dataset)
3. ``backend/app/data/bundled_datasets`` (fallback untuk image Docker)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from . import features, store

_HERE = Path(__file__).resolve().parent
CANDIDATE_DIRS = [
    Path(p) for p in [
        os.environ.get("AKSARA_DATASET_DIR", ""),
        str(_HERE.parent.parent.parent / "dataset"),          # <repo>/dataset
        str(_HERE.parent / "data" / "bundled_datasets"),       # fallback (Docker)
    ] if p
]


def datasets_root() -> Optional[Path]:
    for d in CANDIDATE_DIRS:
        if d.is_dir():
            return d
    return None


def _read_manifest(folder: Path) -> Optional[Dict]:
    mf = folder / "manifest.json"
    if not mf.is_file():
        return None
    try:
        data = json.loads(mf.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("samples"), list):
        return None
    data["_folder"] = folder
    return data


def list_bundled() -> List[Dict]:
    """Ringkasan setiap paket dataset yang tersedia (tanpa daftar sampel penuh)."""
    root = datasets_root()
    if root is None:
        return []
    out = []
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        m = _read_manifest(folder)
        if m is None:
            continue
        labels = sorted({s.get("label") for s in m["samples"] if s.get("label")})
        per_split = {"train": 0, "val": 0, "test": 0}
        for s in m["samples"]:
            sp = s.get("split")
            if sp in per_split:
                per_split[sp] += 1
        out.append({
            "name": m.get("name") or folder.name,
            "folder": folder.name,
            "description": m.get("description", ""),
            "version": m.get("version"),
            "created_at": m.get("created_at"),
            "license": m.get("license"),
            "generator": m.get("generator"),
            "total": len(m["samples"]),
            "per_split": per_split,
            "n_classes": len(labels),
            "labels": labels,
            "classes": m.get("classes", []),
            "readme": (folder / "README.md").is_file(),
        })
    return out


def get_bundled(name: str) -> Optional[Dict]:
    root = datasets_root()
    if root is None:
        return None
    folder = (root / name).resolve()
    if root.resolve() not in folder.parents or not folder.is_dir():
        return None
    return _read_manifest(folder)


def import_bundled(
    name: str,
    activate_classes: bool = True,
    replace_existing: bool = True,
    keep_split: bool = True,
) -> Dict:
    """Salin paket dataset ke store ML.

    - ``activate_classes``: kelas aktif diganti menjadi kelas paket (urutan manifest).
    - ``replace_existing``: hapus sampel bersumber ``import`` dengan nama paket sama
      sebelumnya (idempoten: impor ulang tidak menggandakan data).
    - ``keep_split``: pakai split dari manifest; bila False split diacak 70/15/15.
    """
    m = get_bundled(name)
    if m is None:
        raise LookupError(f"Dataset '{name}' tidak ditemukan di repo.")
    folder: Path = m["_folder"]
    labels_in_pack = [c["label"] for c in m.get("classes", []) if c.get("label")] or sorted(
        {s["label"] for s in m["samples"] if s.get("label")}
    )
    if activate_classes:
        store.set_classes(labels_in_pack)
    active = set(store.class_labels())

    removed = 0
    if replace_existing:
        with store._lock:
            ids = [
                s["id"] for s in store.list_samples()
                if s.get("source") == "import" and (s.get("meta") or {}).get("dataset") == name
            ]
        removed = store.delete_samples(ids) if ids else 0

    items, skipped = [], 0
    for s in m["samples"]:
        rel = s.get("file")
        label = s.get("label")
        if not rel or label not in active:
            skipped += 1
            continue
        path = (folder / rel).resolve()
        if folder.resolve() not in path.parents or not path.is_file():
            skipped += 1
            continue
        try:
            ink = features.ink_from_bytes(path.read_bytes())
        except features.ImageDecodeError:
            skipped += 1
            continue
        split = s.get("split") if keep_split and s.get("split") in store.SPLITS else None
        meta = {"dataset": name, "file": rel, **(s.get("meta") or {})}
        items.append((ink, label, "import", split, f"impor {name}", meta))
    entries = store.add_samples_bulk(items)
    if not keep_split:
        store.rebalance_splits()
    return {
        "name": name,
        "added": len(entries),
        "removed": removed,
        "skipped": skipped + (len(items) - len(entries)),
        "classes": labels_in_pack,
        "stats": store.dataset_stats(),
    }
