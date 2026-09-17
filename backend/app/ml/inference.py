"""Inferensi: memuat model (produksi atau tertentu) dengan cache + prediksi.

Model produksi dipakai endpoint publik ``POST /api/ml/predict`` (tanpa
model_id) — misalnya oleh halaman Translate/Playground bila ingin memakai
classifier sisi server. Admin dapat mencoba model mana pun dengan
``model_id`` eksplisit (halaman "Percobaan").
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

import numpy as np

from . import features, models, store

_cache: Dict[str, models.BaseModel] = {}
_cache_lock = threading.Lock()


def invalidate(model_id: Optional[str] = None) -> None:
    with _cache_lock:
        if model_id is None:
            _cache.clear()
        else:
            _cache.pop(model_id, None)


def load_model(model_id: str, task: Optional[str] = None) -> models.BaseModel:
    with _cache_lock:
        if model_id in _cache:
            return _cache[model_id]
    folder = store.model_dir(model_id, task)
    if not (folder / "model.json").is_file():
        raise FileNotFoundError(model_id)
    model = models.BaseModel.load(folder)
    with _cache_lock:
        if len(_cache) > 8:
            _cache.clear()
        _cache[model_id] = model
    return model


def resolve_model_id(model_id: Optional[str], task: Optional[str] = None) -> str:
    if model_id:
        return model_id
    prod = store.production_model_id(task)
    if not prod:
        raise LookupError("Belum ada model produksi. Latih model lalu tetapkan sebagai produksi di Panel Admin.")
    return prod


def predict_ink(ink: np.ndarray, model_id: Optional[str] = None, top_k: int = 5,
                task: Optional[str] = None, tta: int = 0) -> Dict:
    """Klasifikasi satu maska tinta.

    ``tta`` > 0 menjalankan test-time augmentation pada model yang mendukungnya
    (rata-rata probabilitas beberapa versi teraugmentasi) — dipakai OCR Lens untuk
    menaikkan akurasi pada foto kamera yang kurang tajam.
    """
    mid = resolve_model_id(model_id, task)
    entry = store.get_model_entry(mid, task)
    if entry is None:
        entry = store.get_model_entry(mid, None)
    if entry is None:
        raise FileNotFoundError(mid)
    entry_task = entry.get("task") or task or "aksara"
    model = load_model(mid, entry_task)
    labels: List[str] = entry["classes"]
    lookup = {c.label: c.__dict__ for c in store.all_available_classes(entry_task)}
    x = features.features_from_ink(ink)[None, :]
    try:
        proba = (model.predict_proba(x, tta=int(tta)) if tta else model.predict_proba(x))[0]
    except TypeError:  # model lama tanpa dukung TTA
        proba = model.predict_proba(x)[0]
    order = np.argsort(-proba)[:max(1, min(top_k, len(labels)))]
    top = []
    for i in order:
        lbl = labels[int(i)]
        info = lookup.get(lbl, {})
        top.append({
            "label": lbl,
            "glyph": info.get("glyph", ""),
            "name": info.get("name", lbl),
            "latin": info.get("latin", ""),
            "probability": round(float(proba[int(i)]), 4),
        })
    best = top[0]
    margin = best["probability"] - (top[1]["probability"] if len(top) > 1 else 0.0)
    return {
        "task": entry_task or task or "aksara",
        "model_id": mid,
        "model_name": entry.get("name"),
        "arch": entry.get("arch"),
        "is_production": entry.get("is_production", False),
        "label": best["label"],
        "glyph": best["glyph"],
        "name": best["name"],
        "latin": best["latin"],
        "confidence": best["probability"],
        "margin": round(float(margin), 4),
        "confident": best["probability"] >= 0.6 and margin >= 0.15,
        "top": top,
        "preview": features.png_data_url(x.reshape(features.FEATURE_SIZE, features.FEATURE_SIZE), scale=4),
    }
