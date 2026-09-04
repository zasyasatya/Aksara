"""Job pelatihan ulang (retraining) di background thread + evaluasi otomatis.

Alur satu job:

    1. muat dataset berlabel (train/val/test) dari store
    2. bangun model sesuai arsitektur + hyperparameter
    3. latih (progress per epoch dipublikasikan ke job state)
    4. evaluasi pada split test (fallback: val → train) → laporan metrik lengkap
    5. simpan model + report ke ``data/ml/models/<id>`` dan daftarkan ke registry

Hanya satu job berjalan pada satu waktu (CPU-bound). Job bisa dibatalkan;
status dapat dipantau lewat ``GET /api/ml/train/jobs/{id}``.
"""

from __future__ import annotations

import json
import threading
import time
import traceback
import uuid
from typing import Dict, List, Optional

import numpy as np

from . import features, metrics, models, store
from .synthetic import GlyphRenderer, build_classes

_jobs: Dict[str, Dict] = {}
_jobs_lock = threading.Lock()
_active_job_id: Optional[str] = None
_cancel_flags: Dict[str, threading.Event] = {}

MAX_JOBS_KEPT = 30


def _now() -> float:
    return time.time()


def list_jobs() -> List[Dict]:
    with _jobs_lock:
        return sorted((dict(j) for j in _jobs.values()), key=lambda j: j["created_at"], reverse=True)


def get_job(job_id: str) -> Optional[Dict]:
    with _jobs_lock:
        j = _jobs.get(job_id)
        return dict(j) if j else None


def active_job() -> Optional[Dict]:
    with _jobs_lock:
        if _active_job_id and _active_job_id in _jobs:
            return dict(_jobs[_active_job_id])
        return None


def cancel_job(job_id: str) -> bool:
    with _jobs_lock:
        flag = _cancel_flags.get(job_id)
        job = _jobs.get(job_id)
        if not flag or not job or job["status"] not in ("queued", "running"):
            return False
        flag.set()
        job["cancel_requested"] = True
        return True


def _update(job_id: str, **changes) -> None:
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(changes)


def _prune_locked() -> None:
    finished = [j for j in _jobs.values() if j["status"] in ("done", "failed", "cancelled")]
    finished.sort(key=lambda j: j["created_at"])
    while len(_jobs) > MAX_JOBS_KEPT and finished:
        old = finished.pop(0)
        _jobs.pop(old["id"], None)
        _cancel_flags.pop(old["id"], None)


def _templates_for(labels: List[str]) -> Optional[np.ndarray]:
    """Template font bersih per kelas (untuk arsitektur 'template')."""
    try:
        renderer = GlyphRenderer()
    except FileNotFoundError:
        return None
    lookup = {c["label"]: c for c in store.get_classes()}
    out = []
    for l in labels:
        c = lookup.get(l)
        if not c:
            return None
        out.append(features.features_from_ink(renderer.render(c["glyph"], 500)))
    return np.stack(out)


def start_training(
    arch: str,
    hyperparams: Optional[Dict] = None,
    name: str = "",
    notes: str = "",
    auto_promote: bool = False,
) -> Dict:
    """Antrikan job pelatihan. Melempar ValueError bila prasyarat tidak terpenuhi."""
    global _active_job_id
    if arch not in models.ARCH_BY_ID:
        raise ValueError(f"Arsitektur tidak dikenal: {arch}")
    stats = store.dataset_stats()
    if stats["labeled"] < 2 * max(2, stats["n_classes"]):
        raise ValueError(
            f"Dataset berlabel terlalu sedikit ({stats['labeled']} sampel untuk {stats['n_classes']} kelas). "
            "Generate dataset sintetis atau tambahkan sampel dulu."
        )
    if stats["classes_without_data"]:
        missing = ", ".join(stats["classes_without_data"][:6])
        raise ValueError(f"Ada kelas tanpa sampel berlabel: {missing}. Tambahkan data atau nonaktifkan kelas tersebut.")
    with _jobs_lock:
        if _active_job_id and _jobs.get(_active_job_id, {}).get("status") in ("queued", "running"):
            raise ValueError("Masih ada job pelatihan yang berjalan. Tunggu selesai atau batalkan dulu.")
        job_id = uuid.uuid4().hex[:10]
        hp = models.coerce_hyperparams(arch, hyperparams)
        job = {
            "id": job_id,
            "status": "queued",
            "arch": arch,
            "arch_name": models.ARCH_BY_ID[arch]["name"],
            "hyperparams": hp,
            "name": name.strip() or f"{models.ARCH_BY_ID[arch]['name']}",
            "notes": notes,
            "auto_promote": bool(auto_promote),
            "created_at": _now(),
            "started_at": None,
            "finished_at": None,
            "progress": 0.0,
            "epoch": 0,
            "total_epochs": int(hp.get("epochs", 1)),
            "history": [],
            "message": "Menunggu giliran…",
            "error": None,
            "model_id": None,
            "metrics": None,
            "cancel_requested": False,
            "dataset": {"labeled": stats["labeled"], "n_classes": stats["n_classes"], "per_split": stats["per_split"]},
        }
        _jobs[job_id] = job
        _cancel_flags[job_id] = threading.Event()
        _active_job_id = job_id
        _prune_locked()
    t = threading.Thread(target=_run_job, args=(job_id,), name=f"aksara-train-{job_id}", daemon=True)
    t.start()
    return get_job(job_id)  # type: ignore[return-value]


def run_training_sync(arch: str, hyperparams: Optional[Dict] = None, name: str = "", notes: str = "",
                      auto_promote: bool = False) -> Dict:
    """Varian sinkron (dipakai test & skrip): jalankan job di thread ini."""
    job = start_training(arch, hyperparams, name, notes, auto_promote)
    # start_training sudah menjalankan thread; tunggu sampai selesai.
    while True:
        j = get_job(job["id"])
        if j and j["status"] in ("done", "failed", "cancelled"):
            return j
        time.sleep(0.05)


def _run_job(job_id: str) -> None:
    global _active_job_id
    flag = _cancel_flags[job_id]
    job = get_job(job_id)
    assert job is not None
    arch, hp = job["arch"], job["hyperparams"]
    _update(job_id, status="running", started_at=_now(), message="Memuat dataset…")
    try:
        labels = store.class_labels()
        X_tr, y_tr, _ = store.load_matrix("train", labels)
        X_va, y_va, _ = store.load_matrix("val", labels)
        X_te, y_te, ids_te = store.load_matrix("test", labels)
        if len(y_tr) == 0:
            raise ValueError("Split train kosong. Jalankan 'acak ulang split' atau tambah data.")
        eval_split = "test"
        if len(y_te) == 0:
            X_te, y_te, ids_te, eval_split = (X_va, y_va, [], "val") if len(y_va) else (X_tr, y_tr, [], "train")
        if len(y_va) == 0:
            X_va, y_va = X_te, y_te

        model = models.create_model(arch, len(labels), hp)
        if arch == "template":
            tpl = _templates_for(labels)
            if tpl is not None:
                model.set_templates(tpl)

        total_epochs = int(hp.get("epochs", 1))
        _update(job_id, message=f"Melatih {models.ARCH_BY_ID[arch]['name']} ({len(y_tr)} sampel latih)…",
                total_epochs=total_epochs)

        def progress(rec: Dict) -> None:
            with _jobs_lock:
                j = _jobs.get(job_id)
                if j is None:
                    return
                j["history"].append(rec)
                j["epoch"] = rec.get("epoch", j["epoch"])
                j["progress"] = min(0.95, 0.05 + 0.9 * (rec.get("epoch", 0) / max(1, total_epochs)))
                va = rec.get("val_acc")
                j["message"] = (
                    f"Epoch {rec.get('epoch')}/{total_epochs}"
                    + (f" · loss {rec['loss']:.4f}" if rec.get("loss") is not None else "")
                    + (f" · val acc {va * 100:.1f}%" if va is not None else "")
                )

        t0 = time.time()
        model.fit(X_tr, y_tr, X_va, y_va, progress=progress, should_stop=flag.is_set)
        train_seconds = time.time() - t0
        if flag.is_set():
            _update(job_id, status="cancelled", finished_at=_now(), message="Dibatalkan oleh admin.", progress=0.0)
            return

        _update(job_id, message="Mengevaluasi model…", progress=0.96)
        proba = model.predict_proba(X_te)
        y_pred = proba.argmax(axis=1)
        report = metrics.classification_report(y_te, y_pred, labels, proba)
        report["eval_split"] = eval_split
        report["train_samples"] = int(len(y_tr))
        report["val_samples"] = int(len(y_va))
        report["test_samples"] = int(len(y_te))
        report["train_seconds"] = round(train_seconds, 3)
        # akurasi train untuk deteksi overfit
        p_tr = model.predict_proba(X_tr[:2000])
        report["train_accuracy"] = round(float((p_tr.argmax(axis=1) == y_tr[:2000]).mean()), 4)
        report["history"] = model.history
        # contoh kesalahan (maks 40) untuk galeri di admin
        wrong = [i for i in range(len(y_te)) if y_pred[i] != y_te[i]][:40]
        report["misclassified"] = [
            {"sample_id": ids_te[i] if i < len(ids_te) else None, "true": labels[int(y_te[i])],
             "pred": labels[int(y_pred[i])], "confidence": round(float(proba[i].max()), 4)}
            for i in wrong
        ]

        model_id = store.new_model_id(arch)
        folder = store.model_dir(model_id)
        model.save(folder)
        (folder / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        size_bytes = sum(p.stat().st_size for p in folder.glob("*") if p.is_file())
        ds_stats = store.dataset_stats()
        entry = {
            "id": model_id,
            "name": job["name"],
            "notes": job["notes"],
            "arch": arch,
            "arch_name": models.ARCH_BY_ID[arch]["name"],
            "hyperparams": hp,
            "classes": labels,
            "n_classes": len(labels),
            "n_params": model.n_params(),
            "size_bytes": int(size_bytes),
            "created_at": store.now_iso(),
            "train_seconds": round(train_seconds, 3),
            "dataset_version": ds_stats.get("version"),
            "dataset_size": {"train": int(len(y_tr)), "val": int(len(y_va)), "test": int(len(y_te))},
            "eval_split": eval_split,
            "metrics": metrics.summarize(report) | {"train_accuracy": report["train_accuracy"]},
            "job_id": job_id,
        }
        store.register_model(entry)
        if job.get("auto_promote"):
            store.set_production(model_id)
            from . import inference
            inference.invalidate()
        _update(job_id, status="done", finished_at=_now(), progress=1.0, model_id=model_id,
                metrics=entry["metrics"],
                message=f"Selesai · akurasi {report['accuracy'] * 100:.2f}% · F1 makro {report['macro_f1'] * 100:.2f}%")
    except Exception as exc:  # pragma: no cover - jalur error
        _update(job_id, status="failed", finished_at=_now(), error=str(exc),
                message=f"Gagal: {exc}", progress=0.0)
        traceback.print_exc()
    finally:
        with _jobs_lock:
            if _active_job_id == job_id:
                _active_job_id = None
