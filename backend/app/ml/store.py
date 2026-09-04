"""Penyimpanan dataset & registry model (file-based, thread-safe).

Tata letak di ``backend/app/data/ml/`` (persist via volume yang sama dengan
konten guru):

    ml/
    ├── dataset/
    │   ├── index.json          ← metadata semua sampel (label, split, sumber, …)
    │   └── images/<id>.png     ← PNG kanonik 64×64 per sampel
    ├── models/
    │   ├── registry.json       ← daftar model terlatih + metrik + model produksi aktif
    │   └── <model_id>/         ← model.npz + model.json + report.json
    └── classes.json            ← definisi kelas (label → glyph, nama, latin, grup)

Semua operasi tulis dilindungi ``RLock`` dan ditulis atomik (tmp + replace).
"""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

from . import features
from .synthetic import GlyphClass, build_classes

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ML_DIR = DATA_DIR / "ml"
DATASET_DIR = ML_DIR / "dataset"
IMAGES_DIR = DATASET_DIR / "images"
INDEX_PATH = DATASET_DIR / "index.json"
MODELS_DIR = ML_DIR / "models"
REGISTRY_PATH = MODELS_DIR / "registry.json"
CLASSES_PATH = ML_DIR / "classes.json"

SPLITS = ("train", "val", "test")
SOURCES = ("synthetic", "upload", "canvas", "import")
STATUSES = ("labeled", "unlabeled", "review")

_lock = threading.RLock()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def ensure_dirs() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ── Kelas ──────────────────────────────────────────────────────────────────

def _master() -> dict:
    with open(DATA_DIR / "aksara_master.json", "r", encoding="utf-8") as f:
        return json.load(f)


def all_available_classes() -> List[GlyphClass]:
    """Semua kelas yang bisa diaktifkan (wresastra, swalalita, suara, angka)."""
    return build_classes(_master(), ("wresastra", "swalalita", "suara", "angka"))


def get_classes() -> List[Dict]:
    """Kelas aktif dataset (default: 18 Wresastra)."""
    with _lock:
        data = _read_json(CLASSES_PATH, None)
        if data is None:
            data = {
                "classes": [c.__dict__ for c in build_classes(_master(), ("wresastra",))],
                "updated_at": now_iso(),
            }
            _write_json(CLASSES_PATH, data)
        return list(data["classes"])


def set_classes(labels: Iterable[str]) -> List[Dict]:
    """Aktifkan kelas berdasarkan label (harus ada di daftar tersedia)."""
    wanted = list(dict.fromkeys(labels))
    available = {c.label: c for c in all_available_classes()}
    unknown = [l for l in wanted if l not in available]
    if unknown:
        raise ValueError(f"Label tidak dikenal: {', '.join(unknown)}")
    if len(wanted) < 2:
        raise ValueError("Minimal 2 kelas harus aktif.")
    with _lock:
        classes = [available[l].__dict__ for l in wanted]
        _write_json(CLASSES_PATH, {"classes": classes, "updated_at": now_iso()})
        return classes


def class_labels() -> List[str]:
    return [c["label"] for c in get_classes()]


def class_lookup() -> Dict[str, Dict]:
    return {c["label"]: c for c in get_classes()}


# ── Dataset ────────────────────────────────────────────────────────────────

def _load_index() -> Dict:
    data = _read_json(INDEX_PATH, None)
    if data is None:
        data = {"samples": [], "updated_at": now_iso(), "version": 1}
    data.setdefault("samples", [])
    return data


def _save_index(data: Dict) -> None:
    data["updated_at"] = now_iso()
    data["version"] = int(data.get("version", 1)) + 1
    _write_json(INDEX_PATH, data)


def list_samples() -> List[Dict]:
    with _lock:
        return list(_load_index()["samples"])


def get_sample(sample_id: str) -> Optional[Dict]:
    with _lock:
        return next((s for s in _load_index()["samples"] if s["id"] == sample_id), None)


def image_path(sample_id: str) -> Path:
    return IMAGES_DIR / f"{sample_id}.png"


def assign_split(rng_value: float, val_ratio: float = 0.15, test_ratio: float = 0.15) -> str:
    if rng_value < test_ratio:
        return "test"
    if rng_value < test_ratio + val_ratio:
        return "val"
    return "train"


def add_sample(
    ink: np.ndarray,
    label: Optional[str],
    source: str,
    split: Optional[str] = None,
    note: str = "",
    meta: Optional[Dict] = None,
    status: Optional[str] = None,
) -> Dict:
    """Simpan satu sampel (PNG kanonik + entri index). Label None → unlabeled."""
    if source not in SOURCES:
        raise ValueError(f"Sumber tidak dikenal: {source}")
    if not features.has_ink(ink):
        raise ValueError("Gambar tidak mengandung tinta yang cukup.")
    labels = class_labels()
    if label is not None and label not in labels:
        raise ValueError(f"Label '{label}' tidak termasuk kelas aktif.")
    ensure_dirs()
    sid = uuid.uuid4().hex[:12]
    png = features.to_storage_png(ink)
    if split is None:
        split = assign_split(np.random.default_rng(int.from_bytes(bytes.fromhex(sid[:8]), "big")).random())
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
    }
    with _lock:
        image_path(sid).write_bytes(png)
        data = _load_index()
        data["samples"].append(entry)
        _save_index(data)
    return entry


def add_samples_bulk(items: Iterable[tuple]) -> List[Dict]:
    """Tambah banyak sampel sekaligus (satu penulisan index). items: (ink, label, source, split, note, meta)."""
    ensure_dirs()
    labels = set(class_labels())
    entries = []
    with _lock:
        data = _load_index()
        for ink, label, source, split, note, meta in items:
            if label is not None and label not in labels:
                continue
            if not features.has_ink(ink):
                continue
            sid = uuid.uuid4().hex[:12]
            png = features.to_storage_png(ink)
            if split is None:
                split = assign_split(np.random.default_rng(int.from_bytes(bytes.fromhex(sid[:8]), "big")).random())
            entry = {
                "id": sid, "label": label, "status": "labeled" if label else "unlabeled",
                "split": split, "source": source, "note": note or "", "meta": meta or {},
                "created_at": now_iso(), "updated_at": now_iso(), "bytes": len(png),
            }
            image_path(sid).write_bytes(png)
            data["samples"].append(entry)
            entries.append(entry)
        _save_index(data)
    return entries


def update_sample(sample_id: str, **changes) -> Dict:
    allowed = {"label", "split", "note", "status"}
    with _lock:
        data = _load_index()
        target = next((s for s in data["samples"] if s["id"] == sample_id), None)
        if target is None:
            raise KeyError(sample_id)
        labels = set(class_labels())
        for k, v in changes.items():
            if k not in allowed or v is None and k != "label":
                continue
            if k == "label":
                if v is not None and v not in labels:
                    raise ValueError(f"Label '{v}' tidak termasuk kelas aktif.")
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
        _save_index(data)
        return dict(target)


def delete_samples(sample_ids: Iterable[str]) -> int:
    ids = set(sample_ids)
    with _lock:
        data = _load_index()
        before = len(data["samples"])
        data["samples"] = [s for s in data["samples"] if s["id"] not in ids]
        removed = before - len(data["samples"])
        for sid in ids:
            p = image_path(sid)
            if p.is_file():
                p.unlink()
        _save_index(data)
    return removed


def delete_where(source: Optional[str] = None, label: Optional[str] = None, split: Optional[str] = None) -> int:
    with _lock:
        ids = [
            s["id"] for s in _load_index()["samples"]
            if (source is None or s.get("source") == source)
            and (label is None or s.get("label") == label)
            and (split is None or s.get("split") == split)
        ]
    return delete_samples(ids) if ids else 0


def rebalance_splits(val_ratio: float = 0.15, test_ratio: float = 0.15, seed: int = 0) -> Dict[str, int]:
    """Acak ulang split secara terstratifikasi per label (hanya sampel berlabel)."""
    rng = np.random.default_rng(seed)
    counts = {"train": 0, "val": 0, "test": 0}
    with _lock:
        data = _load_index()
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
        _save_index(data)
    return counts


def load_ink(sample_id: str) -> Optional[np.ndarray]:
    p = image_path(sample_id)
    if not p.is_file():
        return None
    return features.ink_from_storage_png(p.read_bytes())


def dataset_stats() -> Dict:
    samples = list_samples()
    labels = class_labels()
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
    return {
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
        "updated_at": _load_index().get("updated_at"),
        "version": _load_index().get("version", 1),
    }


def load_matrix(split: Optional[str] = None, labels: Optional[List[str]] = None):
    """Muat (X, y, ids) untuk sampel berlabel pada split tertentu."""
    labels = labels or class_labels()
    idx = {l: i for i, l in enumerate(labels)}
    X, y, ids = [], [], []
    for s in list_samples():
        if not s.get("label") or s.get("status") == "unlabeled":
            continue
        if split and s.get("split") != split:
            continue
        if s["label"] not in idx:
            continue
        ink = load_ink(s["id"])
        if ink is None:
            continue
        X.append(features.features_from_ink(ink))
        y.append(idx[s["label"]])
        ids.append(s["id"])
    if not X:
        return np.zeros((0, features.N_FEATURES), dtype=np.float32), np.zeros((0,), dtype=np.int64), ids
    return np.stack(X).astype(np.float32), np.asarray(y, dtype=np.int64), ids


# ── Registry model ─────────────────────────────────────────────────────────

def _load_registry() -> Dict:
    data = _read_json(REGISTRY_PATH, None)
    if data is None:
        data = {"models": [], "production_model_id": None, "updated_at": now_iso()}
    data.setdefault("models", [])
    data.setdefault("production_model_id", None)
    return data


def _save_registry(data: Dict) -> None:
    data["updated_at"] = now_iso()
    _write_json(REGISTRY_PATH, data)


def list_models() -> List[Dict]:
    with _lock:
        reg = _load_registry()
        prod = reg.get("production_model_id")
        out = []
        for m in reg["models"]:
            m = dict(m)
            m["is_production"] = (m["id"] == prod)
            out.append(m)
        return sorted(out, key=lambda m: m.get("created_at", ""), reverse=True)


def get_model_entry(model_id: str) -> Optional[Dict]:
    return next((m for m in list_models() if m["id"] == model_id), None)


def model_dir(model_id: str) -> Path:
    return MODELS_DIR / model_id


def register_model(entry: Dict) -> Dict:
    with _lock:
        reg = _load_registry()
        reg["models"] = [m for m in reg["models"] if m["id"] != entry["id"]]
        reg["models"].append(entry)
        _save_registry(reg)
    return entry


def update_model_entry(model_id: str, **changes) -> Dict:
    with _lock:
        reg = _load_registry()
        target = next((m for m in reg["models"] if m["id"] == model_id), None)
        if target is None:
            raise KeyError(model_id)
        target.update({k: v for k, v in changes.items() if v is not None})
        target["updated_at"] = now_iso()
        _save_registry(reg)
        return dict(target)


def delete_model(model_id: str) -> bool:
    with _lock:
        reg = _load_registry()
        if reg.get("production_model_id") == model_id:
            raise ValueError("Model produksi aktif tidak boleh dihapus. Pindahkan produksi ke model lain dulu.")
        before = len(reg["models"])
        reg["models"] = [m for m in reg["models"] if m["id"] != model_id]
        _save_registry(reg)
        d = model_dir(model_id)
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)
        return len(reg["models"]) < before


def set_production(model_id: Optional[str]) -> Optional[str]:
    with _lock:
        reg = _load_registry()
        if model_id is not None and not any(m["id"] == model_id for m in reg["models"]):
            raise KeyError(model_id)
        reg["production_model_id"] = model_id
        for m in reg["models"]:
            if m["id"] == model_id:
                m["promoted_at"] = now_iso()
        _save_registry(reg)
        return model_id


def production_model_id() -> Optional[str]:
    with _lock:
        return _load_registry().get("production_model_id")


def read_report(model_id: str) -> Optional[Dict]:
    p = model_dir(model_id) / "report.json"
    return _read_json(p, None)


def new_model_id(arch: str) -> str:
    return f"{arch}-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
