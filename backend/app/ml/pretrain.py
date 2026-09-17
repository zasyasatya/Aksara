"""Pemasangan **model bawaan** (hasil training pada dataset aktual) ke store ML.

``backend/app/data/ml_bundled/<task>/<model_id>/`` berisi artefak yang dikomit ke
repo (``model.npz``, ``model.json``, ``report.json``, ``entry.json``). Saat aplikasi
dijalankan pertama kali — atau saat halaman Lens membutuhkan model tapi registry
masih kosong — model tersebut disalin ke ``data/ml/<task>/models/`` dan ditetapkan
sebagai produksi, sehingga OCR langsung berfungsi tanpa training ulang.

Admin tetap bebas melatih model baru; model bawaan ditandai ``bundled: true`` dan
tidak menimpa model yang sudah ada kecuali ``force=True``.
"""

from __future__ import annotations

import json
import shutil
import threading
from pathlib import Path
from typing import Dict, List, Optional

from . import store

_lock = threading.Lock()
_attempted: set[str] = set()

BUNDLED_ROOT = store.DATA_DIR / "ml_bundled"


def bundled_models() -> List[Dict]:
    """Daftar model bawaan di repo (per tugas)."""
    out: List[Dict] = []
    if not BUNDLED_ROOT.is_dir():
        return out
    for task_dir in sorted(p for p in BUNDLED_ROOT.iterdir() if p.is_dir()):
        for model_dir in sorted(p for p in task_dir.iterdir() if p.is_dir()):
            entry_file = model_dir / "entry.json"
            if not entry_file.is_file():
                continue
            try:
                entry = json.loads(entry_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            size = sum(p.stat().st_size for p in model_dir.glob("*") if p.is_file())
            out.append({**entry, "folder": str(model_dir.relative_to(BUNDLED_ROOT)), "size_bytes": size})
    return out


def _install_task(task: str, force: bool = False) -> Dict:
    """Salin model bawaan terbaik (terbaru) untuk satu tugas → registry store."""
    installed, skipped = [], []
    candidates = [m for m in bundled_models() if m.get("task") == task]
    if not candidates:
        return {"task": task, "installed": installed, "skipped": skipped, "available": False}
    candidates.sort(key=lambda m: str(m.get("created_at") or ""), reverse=True)
    for cand in candidates[:1] if not force else candidates:
        mid = cand["id"]
        folder = store.model_dir(mid, task)
        already = store.get_model_entry(mid, task) is not None
        if already and not force:
            skipped.append(mid)
            continue
        src = BUNDLED_ROOT / task / mid
        if not (src / "model.json").is_file():
            continue
        folder.mkdir(parents=True, exist_ok=True)
        for f in src.glob("*"):
            if f.name == "entry.json":
                continue
            shutil.copy2(f, folder / f.name)
        entry = {k: v for k, v in cand.items() if k not in ("folder", "size_bytes")}
        entry["bundled"] = True
        # Kelas model bawaan harus menjadi kelas aktif dataset, kalau tidak label
        # hasil prediksi dan komposisi Unicode di Lens akan bergeser.
        try:
            if entry.get("classes"):
                store.set_classes(entry["classes"], task)
        except ValueError:
            pass
        store.register_model(entry, task)
        if not store.production_model_id(task):
            store.set_production(mid, task)
        installed.append(mid)
    return {"task": task, "installed": installed, "skipped": skipped, "available": True}


def ensure_installed(force: bool = False, tasks: Optional[List[str]] = None) -> Dict:
    """Pasang model bawaan yang belum ada. Idempoten & aman dipanggil berkali-kali."""
    tasks = tasks or ["aksara", "latin"]
    results = {}
    with _lock:
        for task in tasks:
            if not force and task in _attempted and store.production_model_id(task):
                results[task] = {"task": task, "installed": [], "skipped": [], "available": True,
                                 "production_model_id": store.production_model_id(task)}
                continue
            res = _install_task(task, force=force)
            res["production_model_id"] = store.production_model_id(task)
            _attempted.add(task)
            results[task] = res
    return results


def status() -> Dict:
    prod = {t: store.production_model_id(t) for t in ("aksara", "latin")}
    return {
        "bundled_root": str(BUNDLED_ROOT),
        "bundled_available": BUNDLED_ROOT.is_dir(),
        "bundled": [{"id": m["id"], "task": m.get("task"), "name": m.get("name"),
                     "metrics": (m.get("metrics") or {}), "size_bytes": m.get("size_bytes"),
                     "created_at": m.get("created_at")} for m in bundled_models()],
        "production": prod,
    }
