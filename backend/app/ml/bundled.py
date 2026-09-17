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


def list_bundled(task: Optional[str] = None) -> List[Dict]:
    """Ringkasan setiap paket dataset yang tersedia (tanpa daftar sampel penuh).

    ``task`` memfilter paket berdasarkan manifest ``task`` (``aksara`` / ``latin``).
    Paket tanpa field ``task`` dianggap tugas aksara (kompatibel paket lama).
    """
    root = datasets_root()
    if root is None:
        return []
    wanted = None
    if task:
        from .tasks import resolve as resolve_task

        wanted = resolve_task(task)
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
        pack_task = m.get("task") or "aksara"
        if wanted and pack_task != wanted:
            continue
        out.append({
            "task": pack_task,
            "real": bool(m.get("source")),
            "source": m.get("source"),
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
    task: Optional[str] = None,
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
    pack_task = m.get("task") or "aksara"
    target_task = task or pack_task
    if task and pack_task != target_task:
        raise ValueError(
            f"Paket '{name}' berisi sampel tugas '{pack_task}', tidak dapat diimpor ke '{target_task}'."
        )
    folder: Path = m["_folder"]
    labels_in_pack = [c["label"] for c in m.get("classes", []) if c.get("label")] or sorted(
        {s["label"] for s in m["samples"] if s.get("label")}
    )
    if activate_classes:
        store.set_classes(labels_in_pack, target_task)
    active = set(store.class_labels(target_task))

    removed = 0
    if replace_existing:
        with store._lock:
            ids = [
                s["id"] for s in store.list_samples(target_task)
                if s.get("source") == "import" and (s.get("meta") or {}).get("dataset") == name
            ]
        removed = store.delete_samples(ids, target_task) if ids else 0

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
        meta = {**(s.get("meta") or {}), "dataset": name, "file": rel, "task": target_task}
        items.append((ink, label, "import", split, f"impor {name}", meta))
    entries = store.add_samples_bulk(items, target_task)
    if not keep_split:
        store.rebalance_splits(task=target_task)
    return {
        "name": name,
        "task": target_task,
        "added": len(entries),
        "removed": removed,
        "skipped": skipped + (len(items) - len(entries)),
        "classes": labels_in_pack,
        "stats": store.dataset_stats(target_task),
    }
