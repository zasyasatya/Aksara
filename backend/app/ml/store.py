"""Penyimpanan dataset & registry model (file-based, thread-safe, multi-tugas).

Satu direktori per *task* (lihat ``tasks.py``) di ``backend/app/data/ml/``::

    ml/
    ├── <task>/                   task = aksara | latin
    │   ├── classes.json          definisi kelas (label → glyph, nama, latin, grup)
    │   ├── dataset/
    │   │   ├── index.json        ← metadata semua sampel (label, split, sumber, …)
    │   │   └── images/<id>.png   ← PNG kanonik 64×64 per sampel
    │   └── models/
    │       ├── registry.json     ← daftar model terlatih + metrik + model produksi aktif
    │       └── <model_id>/       ← model.npz + model.json + report.json
    └── bundled/                  model siap pakai yang dikomit (dipasang saat first run)

Struktur lama (``ml/dataset``, ``ml/models``, ``ml/classes.json`` — satu tugas
saja) dipindahkan otomatis ke ``ml/aksara/`` pada ``ensure_dirs()`` pertama.

Semua operasi tulis dilindungi ``RLock`` dan ditulis atomik (tmp + replace).
"""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

from . import features
from .synthetic import GlyphClass, build_classes
from .tasks import DEFAULT_TASK, classes_for_task, resolve

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ML_DIR = DATA_DIR / "ml"

SPLITS = ("train", "val", "test")
SOURCES = ("synthetic", "upload", "canvas", "import", "camera")
STATUSES = ("labeled", "unlabeled", "review")

_lock = threading.RLock()
_migrated: set[str] = set()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class TaskPaths:
    task: str
    root: Path
    classes: Path
    dataset: Path
    index: Path
    images: Path
    models: Path
    registry: Path
    report_dir: Path

    def model(self, model_id: str) -> Path:
        return self.models / model_id


def paths(task: Optional[str] = None) -> TaskPaths:
    t = resolve(task)
    root = ML_DIR / t
    return TaskPaths(
        task=t,
        root=root,
        classes=root / "classes.json",
        dataset=root / "dataset",
        index=root / "dataset" / "index.json",
        images=root / "dataset" / "images",
        models=root / "models",
        registry=root / "models" / "registry.json",
        report_dir=root / "models",
    )


def _migrate_legacy(task: str) -> None:
    """Pindahkan tata letak lama (satu tugas di akar ``ml/``) ke ``ml/<task>/``."""
    if task in _migrated or task != DEFAULT_TASK:
        return
    _migrated.add(task)
    legacy_index = ML_DIR / "dataset" / "index.json"
    target = ML_DIR / task
    if not legacy_index.is_file() or (target / "dataset" / "index.json").is_file():
        return
    target.mkdir(parents=True, exist_ok=True)
    for name in ("dataset", "models"):
        src = ML_DIR / name
        if src.is_dir():
            shutil.move(str(src), str(target / name))
    for name in ("classes.json",):
        src = ML_DIR / name
        if src.is_file():
            shutil.move(str(src), str(target / name))


def ensure_dirs(task: Optional[str] = None) -> None:
    p = paths(task)
    _migrate_legacy(p.task)
    p.images.mkdir(parents=True, exist_ok=True)
    p.models.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Kelas ─────────────────────────────────────────────────────────────────

def _master() -> dict:
    with open(DATA_DIR / "aksara_master.json", "r", encoding="utf-8") as f:
        return json.load(f)


def all_available_classes(task: Optional[str] = None) -> List[GlyphClass]:
    """Semua kelas yang bisa diaktifkan pada suatu tugas.

    Tugas aksara: wresastra, swalalita, suara, angka, pangangge (suara & tengenan).
    Tugas latin: 26 huruf + 10 angka.
    """
    from .tasks import get as get_task

    spec = get_task(task)
    out = classes_for_task(spec.id, _master())
    if not out:  # pragma: no cover - jaring pengaman
        out = build_classes(_master(), ("wresastra",))
    return out


def get_classes(task: Optional[str] = None) -> List[Dict]:
    """Kelas aktif dataset (default tugas aksara: 18 Wresastra)."""
    p = paths(task)
    with _lock:
        data = _read_json(p.classes, None)
        if data is None:
            from .tasks import get as get_task

            spec = get_task(p.task)
            available = {c.label: c for c in all_available_classes(spec.id)}
            wanted = [l for l in spec.default_classes if l in available] or list(available)[:2]
            data = {"classes": [available[l].__dict__ for l in wanted], "updated_at": now_iso()}
            _write_json(p.classes, data)
        return list(data["classes"])


def set_classes(labels: Iterable[str], task: Optional[str] = None) -> List[Dict]:
    """Aktifkan kelas berdasarkan label (harus ada di daftar tersedia tugas itu)."""
    p = paths(task)
    wanted = list(dict.fromkeys(labels))
    available = {c.label: c for c in all_available_classes(p.task)}
    unknown = [l for l in wanted if l not in available]
    if unknown:
        raise ValueError(f"Label tidak dikenal: {', '.join(unknown)}")
    if len(wanted) < 2:
        raise ValueError("Minimal 2 kelas harus aktif.")
    with _lock:
        classes = [available[l].__dict__ for l in wanted]
        _write_json(p.classes, {"classes": classes, "updated_at": now_iso()})
        return classes


def class_labels(task: Optional[str] = None) -> List[str]:
    return [c["label"] for c in get_classes(task)]


def class_lookup(task: Optional[str] = None) -> Dict[str, Dict]:
    return {c["label"]: c for c in get_classes(task)}


# ── Dataset ────────────────────────────────────────────────────────────────

def _load_index(task: Optional[str] = None) -> Dict:
    p = paths(task)
    data = _read_json(p.index, None)
    if data is None:
        data = {"samples": [], "updated_at": now_iso(), "version": 1}
    data.setdefault("samples", [])
    return data


def _save_index(data: Dict, task: Optional[str] = None) -> None:
    data["updated_at"] = now_iso()
    data["version"] = int(data.get("version", 1)) + 1
    _write_json(paths(task).index, data)


def list_samples(task: Optional[str] = None) -> List[Dict]:
    with _lock:
        return list(_load_index(task)["samples"])


def get_sample(sample_id: str, task: Optional[str] = None) -> Optional[Dict]:
    with _lock:
        return next((s for s in _load_index(task)["samples"] if s["id"] == sample_id), None)


def image_path(sample_id: str, task: Optional[str] = None) -> Path:
    return paths(task).images / f"{sample_id}.png"


def assign_split(rng_value: float, val_ratio: float = 0.15, test_ratio: float = 0.15) -> str:
    if rng_value < test_ratio:
        return "test"
    if rng_value < test_ratio + val_ratio:
        return "val"
    return "train"


def _split_for_sample(sid: str) -> str:
    return assign_split(np.random.default_rng(int.from_bytes(bytes.fromhex(sid[:8]), "big")).random())


def add_sample(
    ink: np.ndarray,
    label: Optional[str],
    source: str,
    split: Optional[str] = None,
    note: str = "",
    meta: Optional[Dict] = None,
    status: Optional[str] = None,
    task: Optional[str] = None,
) -> Dict:
    """Simpan satu sampel (PNG kanonik + entri index). Label None → unlabeled."""
    p = paths(task)
    if source not in SOURCES:
        raise ValueError(f"Sumber tidak dikenal: {source}")
    if not features.has_ink(ink):
        raise ValueError("Gambar tidak mengandung tinta yang cukup.")
    labels = class_labels(p.task)
    if label is not None and label not in labels:
        raise ValueError(f"Label '{label}' tidak termasuk kelas aktif tugas '{p.task}'.")
    ensure_dirs(p.task)
    sid = uuid.uuid4().hex[:12]
    png = features.to_storage_png(ink)
    if split is None:
        split = _split_for_sample(sid)
    if split not in SPLITS:
        raise ValueError(f"Split tidak dikenal: {split}")
    if status is None:
        status = "labeled" if label else "unlabeled"
    entry = {
        "id": sid,
        "label": label,
        "status": status,
        "split": split,
        "source": source,
        "note": note or "",
        "meta": meta or {},
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "bytes": len(png),
        "task": p.task,
    }
    with _lock:
        image_path(sid, p.task).write_bytes(png)
        data = _load_index(p.task)
        data["samples"].append(entry)
        _save_index(data, p.task)
    return entry


def add_samples_bulk(items: Iterable[tuple], task: Optional[str] = None) -> List[Dict]:
    """Tambah banyak sampel sekaligus (satu penulisan index).

    items: ``(ink, label, source, split, note, meta)`` — ``meta`` opsional.
    """
    p = paths(task)
    ensure_dirs(p.task)
    labels = set(class_labels(p.task))
    entries = []
    with _lock:
        data = _load_index(p.task)
        for item in items:
            ink, label, source, split, note = item[0], item[1], item[2], item[3], item[4]
            meta = item[5] if len(item) > 5 else {}
            if source not in SOURCES:
                continue
            if label is not None and label not in labels:
                continue
            if not features.has_ink(ink):
                continue
            sid = uuid.uuid4().hex[:12]
            png = features.to_storage_png(ink)
            if split is None:
                split = _split_for_sample(sid)
            entry = {
                "id": sid, "label": label, "status": "labeled" if label else "unlabeled",
                "split": split, "source": source, "note": note or "", "meta": meta or {},
                "created_at": now_iso(), "updated_at": now_iso(), "bytes": len(png), "task": p.task,
            }
            image_path(sid, p.task).write_bytes(png)
            data["samples"].append(entry)
            entries.append(entry)
        _save_index(data, p.task)
    return entries


def update_sample(sample_id: str, task: Optional[str] = None, **changes) -> Dict:
    allowed = {"label", "split", "note", "status"}
    p = paths(task)
    with _lock:
        data = _load_index(p.task)
        target = next((s for s in data["samples"] if s["id"] == sample_id), None)
        if target is None:
            raise KeyError(sample_id)
        labels = set(class_labels(p.task))
        for k, v in changes.items():
            if k not in allowed or v is None and k != "label":
                continue
            if k == "label":
                if v is not None and v not in labels:
                    raise ValueError(f"Label '{v}' tidak termasuk kelas aktif tugas '{p.task}'.")
                target["label"] = v
                if v and target.get("status") == "unlabeled":
                    target["status"] = "labeled"
                if not v:
                    target["status"] = "unlabeled"
            elif k == "split":
                if v not in SPLITS:
                    raise ValueError(f"Split tidak dikenal: {v}")
                target["split"] = v
            elif k == "status":
                if v not in STATUSES:
                    raise ValueError(f"Status tidak dikenal: {v}")
                target["status"] = v
            else:
                target[k] = v
        target["updated_at"] = now_iso()
        _save_index(data, p.task)
        return dict(target)


def delete_samples(sample_ids: Iterable[str], task: Optional[str] = None) -> int:
    p = paths(task)
    ids = set(sample_ids)
    with _lock:
        data = _load_index(p.task)
        before = len(data["samples"])
        data["samples"] = [s for s in data["samples"] if s["id"] not in ids]
        removed = before - len(data["samples"])
        for sid in ids:
            fp = image_path(sid, p.task)
            if fp.is_file():
                fp.unlink()
        _save_index(data, p.task)
    return removed


def delete_where(
    source: Optional[str] = None, label: Optional[str] = None, split: Optional[str] = None,
    task: Optional[str] = None,
) -> int:
    p = paths(task)
    with _lock:
        ids = [
            s["id"] for s in _load_index(p.task)["samples"]
            if (source is None or s.get("source") == source)
            and (label is None or s.get("label") == label)
            and (split is None or s.get("split") == split)
        ]
    return delete_samples(ids, p.task) if ids else 0


def rebalance_splits(val_ratio: float = 0.15, test_ratio: float = 0.15, seed: int = 0,
                     task: Optional[str] = None) -> Dict[str, int]:
    """Acak ulang split secara terstratifikasi per label (hanya sampel berlabel)."""
    p = paths(task)
    rng = np.random.default_rng(seed)
    counts = {"train": 0, "val": 0, "test": 0}
    with _lock:
        data = _load_index(p.task)
        by_label: Dict[str, List[Dict]] = {}
        for s in data["samples"]:
            if s.get("label") and s.get("status") == "labeled":
                by_label.setdefault(s["label"], []).append(s)
        for label, items in by_label.items():
            idx = rng.permutation(len(items))
            n = len(items)
            n_test = int(round(n * test_ratio))
            n_val = int(round(n * val_ratio))
            for rank, i in enumerate(idx):
                if rank < n_test:
                    sp = "test"
                elif rank < n_test + n_val:
                    sp = "val"
                else:
                    sp = "train"
                items[i]["split"] = sp
                items[i]["updated_at"] = now_iso()
                counts[sp] += 1
        _save_index(data, p.task)
    return counts


def load_ink(sample_id: str, task: Optional[str] = None) -> Optional[np.ndarray]:
    fp = image_path(sample_id, task)
    if not fp.is_file():
        return None
    return features.ink_from_storage_png(fp.read_bytes())


def dataset_stats(task: Optional[str] = None) -> Dict:
    p = paths(task)
    samples = list_samples(p.task)
    labels = class_labels(p.task)
    per_label = {l: {"train": 0, "val": 0, "test": 0, "total": 0} for l in labels}
    per_source: Dict[str, int] = {}
    per_split = {"train": 0, "val": 0, "test": 0}
    unlabeled = review = 0
    for s in samples:
        per_source[s.get("source", "?")] = per_source.get(s.get("source", "?"), 0) + 1
        if s.get("status") == "unlabeled" or not s.get("label"):
            unlabeled += 1
            continue
        if s.get("status") == "review":
            review += 1
        lbl = s["label"]
        if lbl in per_label:
            per_label[lbl][s.get("split", "train")] += 1
            per_label[lbl]["total"] += 1
        per_split[s.get("split", "train")] += 1
    labeled = sum(v["total"] for v in per_label.values())
    totals = [v["total"] for v in per_label.values()]
    index = _load_index(p.task)
    return {
        "task": p.task,
        "total": len(samples),
        "labeled": labeled,
        "unlabeled": unlabeled,
        "review": review,
        "per_split": per_split,
        "per_source": per_source,
        "per_label": per_label,
        "n_classes": len(labels),
        "min_per_class": min(totals) if totals else 0,
        "max_per_class": max(totals) if totals else 0,
        "classes_without_data": [l for l, v in per_label.items() if v["total"] == 0],
        "updated_at": index.get("updated_at"),
        "version": index.get("version", 1),
    }


def load_matrix(split: Optional[str] = None, labels: Optional[List[str]] = None,
                task: Optional[str] = None):
    """Muat (X, y, ids) untuk sampel berlabel pada split tertentu."""
    p = paths(task)
    labels = labels or class_labels(p.task)
    idx = {l: i for i, l in enumerate(labels)}
    X, y, ids = [], [], []
    for s in list_samples(p.task):
        if not s.get("label") or s.get("status") == "unlabeled":
            continue
        if split and s.get("split") != split:
            continue
        if s["label"] not in idx:
            continue
        ink = load_ink(s["id"], p.task)
        if ink is None:
            continue
        X.append(features.features_from_ink(ink))
        y.append(idx[s["label"]])
        ids.append(s["id"])
    if not X:
        return np.zeros((0, features.N_FEATURES), dtype=np.float32), np.zeros((0,), dtype=np.int64), ids
    return np.stack(X).astype(np.float32), np.asarray(y, dtype=np.int64), ids


# ── Registry model ─────────────────────────────────────────────────────────

def _load_registry(task: Optional[str] = None) -> Dict:
    p = paths(task)
    data = _read_json(p.registry, None)
    if data is None:
        data = {"models": [], "production_model_id": None, "updated_at": now_iso()}
    data.setdefault("models", [])
    data.setdefault("production_model_id", None)
    return data


def _save_registry(data: Dict, task: Optional[str] = None) -> None:
    data["updated_at"] = now_iso()
    _write_json(paths(task).registry, data)


def list_models(task: Optional[str] = None) -> List[Dict]:
    p = paths(task)
    with _lock:
        reg = _load_registry(p.task)
        prod = reg.get("production_model_id")
        out = []
        for m in reg["models"]:
            m = dict(m)
            m["is_production"] = (m["id"] == prod)
            out.append(m)
        return sorted(out, key=lambda m: m.get("created_at", ""), reverse=True)


def get_model_entry(model_id: str, task: Optional[str] = None) -> Optional[Dict]:
    return next((m for m in list_models(task) if m["id"] == model_id), None)


def find_model(model_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Cari entri model di semua tugas → ``(entry, task)``."""
    for t in (DEFAULT_TASK, "latin"):
        entry = get_model_entry(model_id, t)
        if entry:
            return entry, t
    return None, None


def model_dir(model_id: str, task: Optional[str] = None) -> Path:
    return paths(task).model(model_id)


def register_model(entry: Dict, task: Optional[str] = None) -> Dict:
    p = paths(task)
    with _lock:
        reg = _load_registry(p.task)
        reg["models"] = [m for m in reg["models"] if m["id"] != entry["id"]]
        reg["models"].append(entry)
        _save_registry(reg, p.task)
    return entry


def update_model_entry(model_id: str, task: Optional[str] = None, **changes) -> Dict:
    p = paths(task)
    with _lock:
        reg = _load_registry(p.task)
        target = next((m for m in reg["models"] if m["id"] == model_id), None)
        if target is None:
            raise KeyError(model_id)
        target.update({k: v for k, v in changes.items() if v is not None})
        target["updated_at"] = now_iso()
        _save_registry(reg, p.task)
        return dict(target)


def delete_model(model_id: str, task: Optional[str] = None) -> bool:
    p = paths(task)
    with _lock:
        reg = _load_registry(p.task)
        if reg.get("production_model_id") == model_id:
            raise ValueError("Model produksi aktif tidak boleh dihapus. Pindahkan produksi ke model lain dulu.")
        before = len(reg["models"])
        reg["models"] = [m for m in reg["models"] if m["id"] != model_id]
        _save_registry(reg, p.task)
        d = model_dir(model_id, p.task)
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)
        return len(reg["models"]) < before


def set_production(model_id: Optional[str], task: Optional[str] = None) -> Optional[str]:
    p = paths(task)
    with _lock:
        reg = _load_registry(p.task)
        if model_id is not None and not any(m["id"] == model_id for m in reg["models"]):
            raise KeyError(model_id)
        reg["production_model_id"] = model_id
        for m in reg["models"]:
            if m["id"] == model_id:
                m["promoted_at"] = now_iso()
        _save_registry(reg, p.task)
        return model_id


def production_model_id(task: Optional[str] = None) -> Optional[str]:
    p = paths(task)
    with _lock:
        return _load_registry(p.task).get("production_model_id")


def read_report(model_id: str, task: Optional[str] = None) -> Optional[Dict]:
    fp = model_dir(model_id, task) / "report.json"
    return _read_json(fp, None)


def new_model_id(arch: str, task: Optional[str] = None) -> str:
    prefix = arch if resolve(task) == DEFAULT_TASK else f"{resolve(task)}-{arch}"
    return f"{prefix}-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
