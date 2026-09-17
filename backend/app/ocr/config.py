"""Konfigurasi & antrean umpan balik untuk halaman Lens (OCR kamera).

Dua hal disimpan di ``backend/app/data/ocr.json`` (persist seperti konten Panel
Guru, lewat volume yang sama):

``default_options``
    parameter pipeline yang dipakai ``POST /api/ocr/scan`` bila klien tidak
    mengirim override — bisa disetel admin dari Panel Admin → Lens & OCR
    (ambang binarisasi, TTA, pemisah kata, batas glyph, model bahasa, dsb.).

``feedback``
    saklar pengumpulan koreksi dari halaman Lens: apakah pengunjung boleh
    mengirim crop yang salah baca ke antrean labeling admin, batas ukuran, dan
    status awal sampel (``review`` = menunggu label admin).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, Optional

from ..ml import store

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONFIG_PATH = DATA_DIR / "ocr.json"
_lock = threading.RLock()

DEFAULT_OPTIONS: Dict = {
    "script": "auto",
    "binarize": "sauvola",
    "sauvola_window": 25,
    "sauvola_k": 0.12,
    "invert": "auto",
    "deskew": True,
    "min_area": 6,
    "min_height": 7,
    "close_iters": 1,
    "merge_gap_ratio": 0.14,
    "word_gap_ratio": 0.62,
    "split_marks": True,
    "tta": 2,
    "use_language_model": True,
    "beam_width": 6,
    "top_k": 5,
    "max_glyphs": 480,
    "split_width_ratio": 1.25,
    "resplit_below": 0.62,
    "upscale_small": True,
    "target_line_height": 30,
    "script_margin": 0.85,
    "line_min_ink": 0.012,
}

DEFAULT_FEEDBACK: Dict = {
    "enabled": True,
    "require_review": True,
    "max_images_per_scan": 12,
    "max_bytes": 700_000,
}

DEFAULT_LIMITS: Dict = {
    "scan_per_minute": 30,          # per IP
    "feedback_per_minute": 8,       # per IP
    "max_image_bytes": 8_000_000,   # batas unggah (byte)
    "max_side": 2400,               # sisi terpanjang yang diproses (px)
}

DEFAULTS: Dict = {"default_options": dict(DEFAULT_OPTIONS), "feedback": dict(DEFAULT_FEEDBACK),
                  "limits": dict(DEFAULT_LIMITS)}


def _read() -> Dict:
    if not CONFIG_PATH.is_file():
        return json.loads(json.dumps(DEFAULTS))
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):  # pragma: no cover - file rusak
        return json.loads(json.dumps(DEFAULTS))
    out = json.loads(json.dumps(DEFAULTS))
    for section, values in (data or {}).items():
        if isinstance(values, dict):
            out.setdefault(section, {}).update(values)
        else:
            out[section] = values
    return out


def get_config() -> Dict:
    with _lock:
        return _read()


def merged_options(overrides: Optional[dict] = None) -> Dict:
    """default_options dari config + override pemanggil (None diabaikan)."""
    cfg = get_config().get("default_options", {})
    out = dict(cfg)
    for k, v in (overrides or {}).items():
        if v is not None:
            out[k] = v
    return out


def update_config(patch: Optional[dict]) -> Dict:
    with _lock:
        data = _read()
        patch = patch or {}
        if "default_options" in patch:
            opts = dict(data.get("default_options", {}))
            for k, v in (patch.get("default_options") or {}).items():
                if k in DEFAULT_OPTIONS and v is not None:
                    opts[k] = v
            data["default_options"] = opts
        if "feedback" in patch:
            fb = dict(data.get("feedback", {}))
            for k, v in (patch.get("feedback") or {}).items():
                if k in DEFAULT_FEEDBACK and v is not None:
                    fb[k] = v
            data["feedback"] = fb
        if "limits" in patch:
            lim = dict(data.get("limits", {}))
            for k, v in (patch.get("limits") or {}).items():
                if k in DEFAULT_LIMITS and v is not None:
                    lim[k] = v
            data["limits"] = lim
        if "note" in patch:
            data["note"] = str(patch.get("note") or "")[:400]
        data["updated_at"] = store.now_iso()
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(CONFIG_PATH)
        return data


def feedback_config() -> Dict:
    return dict(DEFAULT_FEEDBACK, **get_config().get("feedback", {}))


def limits() -> Dict:
    return dict(DEFAULT_LIMITS, **get_config().get("limits", {}))


# ── antrean umpan balik (crop yang dikoreksi dari halaman Lens) ─────────────

def submit_feedback(ink, label: Optional[str], task: str, note: str = "", meta: Optional[Dict] = None) -> Dict:
    """Simpan satu crop dari kamera. Tanpa label → status ``review`` (menunggu admin)."""
    fb = feedback_config()
    # Koreksi dari pengunjung TIDAK pernah langsung dipercaya: tanpa saklar ini
    # seseorang bisa menyetujui labelnya sendiri lalu masuk ke model sekolah.
    if fb.get("require_review", True):
        status = "review"
    else:
        status = "labeled" if label else "unlabeled"
    entry = store.add_sample(ink, label, "camera", None, note, {"via": "lens", **(meta or {})}, status=status,
                             task=task)
    return entry


def pending(task: Optional[str] = None, limit: int = 60, offset: int = 0) -> Dict:
    """Koreksi dari kamera yang masuk antrean admin (kedua tugas bila task None)."""
    tasks = [task] if task else ["aksara", "latin"]
    samples: list = []
    for t in tasks:
        for s in store.list_samples(t):
            if s.get("source") == "camera":
                samples.append({**s, "task": t})
    samples.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    total = len(samples)
    review = sum(1 for s in samples if s.get("status") == "review")
    return {"samples": samples[offset: offset + limit], "total": total, "review": review,
            "offset": offset, "limit": limit}


def decide(sample_id: str, task: str, action: str, label: Optional[str] = None,
           split: Optional[str] = None) -> Dict:
    """``accept`` → labeled (siap training) · ``reject`` → hapus · ``relabel`` → ganti label."""
    if action == "reject":
        return {"removed": store.delete_samples([sample_id], task), "sample_id": sample_id}
    changes = {"status": "labeled"} if action == "accept" else {}
    if label:
        changes["label"] = label
    if split:
        changes["split"] = split
    if not changes:
        raise ValueError("Tidak ada perubahan (gunakan accept/relabel/reject).")
    return store.update_sample(sample_id, task, **changes)


def approve_all(task: str) -> int:
    """Setujui seluruh koreksi berlabel valid → siap dipakai training."""
    n = 0
    for s in store.list_samples(task):
        if s.get("source") != "camera" or s.get("status") != "review":
            continue
        if not s.get("label"):
            continue
        store.update_sample(s["id"], task, status="labeled")
        n += 1
    return n
