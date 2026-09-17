"""Router machine-learning: dataset, labeling, retraining, evaluasi, registry.

Semua endpoint *mutasi* dan data admin membutuhkan role **admin**
(mode dev → otomatis admin, mode prod → sesi login admin). Endpoint publik:

- ``task`` (query) memilih tugas ML: ``aksara`` (baku) atau ``latin`` — dipakai seluruh
  endpoint dataset/latihan/registry sehingga retraining OCR Lens bisa dikelola per skrip.

- ``GET  /api/ml/status``      : ringkasan (model produksi + ukuran dataset)
- ``POST /api/ml/predict``     : prediksi dengan model produksi (atau model_id)

Struktur endpoint:

    /ml/status                          GET
    /ml/architectures                   GET
    /ml/classes                         GET | PUT
    /ml/dataset/stats                   GET
    /ml/dataset/samples                 GET (filter) | POST (1 sampel)
    /ml/dataset/samples/bulk            POST
    /ml/dataset/samples/{id}            GET | PATCH | DELETE
    /ml/dataset/samples/{id}/image      GET (PNG)
    /ml/dataset/bulk-label              POST
    /ml/dataset/bulk-delete             POST
    /ml/dataset/generate-synthetic      POST
    /ml/dataset/bundled                 GET   (paket dataset di repo)
    /ml/dataset/import-bundled          POST
    /ml/dataset/rebalance               POST
    /ml/dataset/clear                   POST  (?source=)
    /ml/train                           POST  → job
    /ml/train/jobs                      GET
    /ml/train/jobs/{id}                 GET | DELETE (batal)
    /ml/models                          GET
    /ml/models/{id}                     GET (report lengkap) | PATCH | DELETE
    /ml/models/production               PUT
    /ml/predict                         POST
    /ml/predict/compare                 POST
"""

from __future__ import annotations

import io
import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query, Response

from ..core import security
from ..core.config import settings
from ..ml import bundled, features, inference, models as ml_models, store, synthetic, training
from ..ml import pretrain, tasks as ml_tasks
from ..schemas.ml import (
    BulkDeleteIn, BulkLabelIn, ClassesUpdate, CompareIn, GenerateSyntheticIn, ImportBundledIn,
    MessageResponse, ModelUpdate, PredictIn, PromoteIn, RebalanceIn, SampleBulkIn, SampleIn,
    SampleUpdate, TrainIn,
)

router = APIRouter(prefix="/ml", tags=["ml"])


# ── otorisasi ──────────────────────────────────────────────────────────────

def _role(authorization: Optional[str]) -> Optional[str]:
    if not settings.is_prod:
        return "admin"
    return security.get_session_role(security.bearer_token(authorization))


def _require_admin(authorization: Optional[str]) -> None:
    if _role(authorization) != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak. Login sebagai Admin diperlukan pada mode prod.")


def _decode(image: str):
    try:
        data = features.decode_base64_image(image)
        ink = features.ink_from_bytes(data)
    except features.ImageDecodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not features.has_ink(ink):
        raise HTTPException(status_code=400, detail="Gambar kosong / tidak ada tinta yang terdeteksi.")
    return ink


# ── status & referensi ─────────────────────────────────────────────────────

@router.get("/status")
async def ml_status(task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    stats = store.dataset_stats(task)
    prod_id = store.production_model_id(task)
    prod = store.get_model_entry(prod_id, task) if prod_id else None
    job = training.active_job(task)
    return {
        "mode": "prod" if settings.is_prod else "dev",
        "is_admin": _role(authorization) == "admin",
        "task": store.paths(task).task,
        "tasks": [
            {"id": t["id"], "name": t["name"], "short": t["short"], "description": t["description"],
             "default_arch": t["default_arch"], "n_default_classes": t["n_default_classes"]}
            for t in ml_tasks.list_tasks()
        ],
        "production_model": prod,
        "dataset": {k: stats[k] for k in ("total", "labeled", "unlabeled", "review", "per_split", "n_classes", "version")},
        "models_total": len(store.list_models(task)),
        "active_job": {k: job[k] for k in ("id", "status", "arch", "progress", "message")} if job else None,
        "font_available": synthetic.FONT_PATH.is_file(),
    }


@router.get("/architectures")
async def architectures():
    return {"architectures": ml_models.ARCHITECTURES}


@router.get("/classes")
async def get_classes(task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin")):
    active = store.get_classes(task)
    active_labels = {c["label"] for c in active}
    available = [c.__dict__ | {"active": c.label in active_labels} for c in store.all_available_classes(task)]
    return {"active": active, "available": available}


@router.put("/classes")
async def put_classes(body: ClassesUpdate, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    try:
        classes = store.set_classes(body.labels, task)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"active": classes, "message": f"{len(classes)} kelas aktif."}


# ── dataset ────────────────────────────────────────────────────────────────

@router.get("/dataset/stats")
async def dataset_stats(task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    return store.dataset_stats(task)


@router.get("/dataset/samples")
async def list_samples(
    label: Optional[str] = None,
    split: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(60, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order: str = Query("newest", pattern="^(newest|oldest)$"),
    task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None),
):
    _require_admin(authorization)
    samples = store.list_samples(task)
    if label == "__none__":
        samples = [s for s in samples if not s.get("label")]
    elif label:
        samples = [s for s in samples if s.get("label") == label]
    if split:
        samples = [s for s in samples if s.get("split") == split]
    if source:
        samples = [s for s in samples if s.get("source") == source]
    if status:
        samples = [s for s in samples if s.get("status") == status]
    if q:
        ql = q.lower()
        samples = [s for s in samples if ql in (s.get("note") or "").lower() or ql in s["id"] or ql in (s.get("label") or "")]
    samples.sort(key=lambda s: s.get("created_at", ""), reverse=(order == "newest"))
    total = len(samples)
    page = samples[offset:offset + limit]
    return {"samples": page, "total": total, "offset": offset, "limit": limit}


@router.post("/dataset/samples", status_code=201)
async def add_sample(body: SampleIn, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    ink = _decode(body.image)
    try:
        entry = store.add_sample(ink, body.label, body.source, body.split, body.note, task=task)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return entry


@router.post("/dataset/samples/bulk", status_code=201)
async def add_samples_bulk(body: SampleBulkIn, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    items = []
    skipped = 0
    for it in body.items:
        try:
            data = features.decode_base64_image(it.image)
            ink = features.ink_from_bytes(data)
        except features.ImageDecodeError:
            skipped += 1
            continue
        if not features.has_ink(ink):
            skipped += 1
            continue
        items.append((ink, it.label, it.source, it.split, it.note, {}))
    entries = store.add_samples_bulk(items, task)
    return {"added": len(entries), "skipped": skipped + (len(items) - len(entries)), "samples": entries}


@router.get("/dataset/samples/{sample_id}")
async def get_sample(sample_id: str, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    s = store.get_sample(sample_id, task)
    if not s:
        raise HTTPException(status_code=404, detail="Sampel tidak ditemukan.")
    ink = store.load_ink(sample_id, task)
    preview = features.png_data_url(features.normalize_ink(ink, 28, 20), scale=4) if ink is not None else None
    return s | {"feature_preview": preview}


@router.get("/dataset/samples/{sample_id}/image")
async def sample_image(sample_id: str, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin")):
    p = store.image_path(sample_id, task)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="Gambar tidak ditemukan.")
    return Response(content=p.read_bytes(), media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"})


@router.patch("/dataset/samples/{sample_id}")
async def update_sample(sample_id: str, body: SampleUpdate, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    changes = {}
    if body.clear_label:
        changes["label"] = None
    elif body.label is not None:
        changes["label"] = body.label
    if body.split is not None:
        changes["split"] = body.split
    if body.status is not None:
        changes["status"] = body.status
    if body.note is not None:
        changes["note"] = body.note
    try:
        return store.update_sample(sample_id, task, **changes)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sampel tidak ditemukan.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/dataset/samples/{sample_id}", response_model=MessageResponse)
async def delete_sample(sample_id: str, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    removed = store.delete_samples([sample_id], task)
    if not removed:
        raise HTTPException(status_code=404, detail="Sampel tidak ditemukan.")
    return MessageResponse(message="Sampel dihapus.")


@router.post("/dataset/bulk-label")
async def bulk_label(body: BulkLabelIn, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    updated = 0
    for sid in body.ids:
        changes = {}
        if body.label is not None:
            changes["label"] = body.label
        if body.split is not None:
            changes["split"] = body.split
        if body.status is not None:
            changes["status"] = body.status
        try:
            store.update_sample(sid, task, **changes)
            updated += 1
        except KeyError:
            continue
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    return {"updated": updated, "message": f"{updated} sampel diperbarui."}


@router.post("/dataset/bulk-delete")
async def bulk_delete(body: BulkDeleteIn, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    removed = store.delete_samples(body.ids, task)
    return {"removed": removed, "message": f"{removed} sampel dihapus."}


@router.post("/dataset/generate-synthetic")
async def generate_synthetic(body: GenerateSyntheticIn, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    if not synthetic.FONT_PATH.is_file():
        raise HTTPException(status_code=503, detail="Font Noto Sans Balinese tidak tersedia di server.")
    classes = store.get_classes(task)
    if not classes:
        raise HTTPException(status_code=400, detail="Belum ada kelas aktif.")
    removed = store.delete_where(source="synthetic", task=task) if body.replace_existing else 0
    glyph_classes = [synthetic.GlyphClass(**c) for c in classes]
    t0 = time.time()
    items = []
    for cls, ink, meta in synthetic.generate_samples(glyph_classes, body.per_class, body.seed, body.strength):
        items.append((ink, cls.label, "synthetic", None, f"sintetis seed={body.seed}", meta))
    entries = store.add_samples_bulk(items, task)
    stats = store.dataset_stats(task)
    return {
        "added": len(entries),
        "removed": removed,
        "seconds": round(time.time() - t0, 2),
        "stats": stats,
        "message": f"{len(entries)} sampel sintetis ditambahkan ({len(classes)} kelas × {body.per_class}).",
    }


@router.get("/dataset/bundled")
async def list_bundled_datasets(task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    """Paket dataset gambar yang dikomit ke repo (``dataset/<name>/manifest.json``)."""
    _require_admin(authorization)
    root = bundled.datasets_root()
    return {"root": str(root) if root else None, "datasets": bundled.list_bundled(task)}


@router.post("/dataset/import-bundled")
async def import_bundled_dataset(body: ImportBundledIn, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    t0 = time.time()
    try:
        result = bundled.import_bundled(body.name, body.activate_classes, body.replace_existing, body.keep_split, task)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    inference.invalidate()
    result["seconds"] = round(time.time() - t0, 2)
    result["message"] = (
        f"{result['added']} gambar diimpor dari dataset '{body.name}'"
        + (f" ({result['removed']} impor lama diganti)" if result["removed"] else "")
        + (f", {result['skipped']} dilewati" if result["skipped"] else "")
        + "."
    )
    return result


@router.post("/dataset/rebalance")
async def rebalance(body: RebalanceIn, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    if body.val_ratio + body.test_ratio >= 0.9:
        raise HTTPException(status_code=400, detail="Rasio val + test terlalu besar.")
    counts = store.rebalance_splits(body.val_ratio, body.test_ratio, body.seed, task)
    return {"per_split": counts, "message": f"Split diacak ulang: train {counts['train']} · val {counts['val']} · test {counts['test']}."}


@router.post("/dataset/clear")
async def clear_dataset(
    source: Optional[str] = Query(None, pattern="^(synthetic|upload|canvas|import)$"),
    label: Optional[str] = None,
    task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None),
):
    _require_admin(authorization)
    removed = store.delete_where(source=source, label=label, task=task)
    return {"removed": removed, "message": f"{removed} sampel dihapus."}


# ── training ───────────────────────────────────────────────────────────────

@router.post("/train", status_code=202)
async def train(body: TrainIn, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    try:
        job = training.start_training(body.arch, body.hyperparams, body.name, body.notes, body.auto_promote, task)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return job


@router.get("/train/jobs")
async def train_jobs(task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    return {"jobs": training.list_jobs(task), "active": training.active_job(task)}


@router.get("/train/jobs/{job_id}")
async def train_job(job_id: str, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    job = training.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    return job


@router.delete("/train/jobs/{job_id}", response_model=MessageResponse)
async def cancel_job(job_id: str, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    if not training.cancel_job(job_id):
        raise HTTPException(status_code=409, detail="Job tidak sedang berjalan.")
    return MessageResponse(message="Pembatalan diminta.")


# ── registry model ─────────────────────────────────────────────────────────

@router.get("/models")
async def list_models(task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    return {"models": store.list_models(task), "production_model_id": store.production_model_id(task)}


@router.put("/models/production")
async def set_production(body: PromoteIn, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    try:
        store.set_production(body.model_id, task)
    except KeyError:
        raise HTTPException(status_code=404, detail="Model tidak ditemukan.")
    inference.invalidate()
    if body.model_id:
        return {"production_model_id": body.model_id, "message": f"Model '{body.model_id}' kini dipakai di produksi."}
    return {"production_model_id": None, "message": "Model produksi dinonaktifkan."}


@router.get("/models/{model_id}")
async def get_model(model_id: str, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    entry = store.get_model_entry(model_id, task)
    if not entry:
        raise HTTPException(status_code=404, detail="Model tidak ditemukan.")
    report = store.read_report(model_id, task)
    return {"model": entry, "report": report}


@router.patch("/models/{model_id}")
async def update_model(model_id: str, body: ModelUpdate, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    try:
        return store.update_model_entry(model_id, task, name=body.name, notes=body.notes)
    except KeyError:
        raise HTTPException(status_code=404, detail="Model tidak ditemukan.")


@router.delete("/models/{model_id}", response_model=MessageResponse)
async def delete_model(model_id: str, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    try:
        ok = store.delete_model(model_id, task)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not ok:
        raise HTTPException(status_code=404, detail="Model tidak ditemukan.")
    inference.invalidate(model_id)
    return MessageResponse(message=f"Model '{model_id}' dihapus.")


# ── prediksi ───────────────────────────────────────────────────────────────

@router.post("/predict")
async def predict(body: PredictIn, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin")):
    ink = _decode(body.image)
    try:
        return inference.predict_ink(ink, body.model_id, body.top_k, task)
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model tidak ditemukan.")


@router.post("/predict/compare")
async def predict_compare(body: CompareIn, task: Optional[str] = Query(None, pattern="^(aksara|latin)$", description="Tugas ML: aksara | latin"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    ink = _decode(body.image)
    results = []
    for mid in body.model_ids:
        try:
            results.append(inference.predict_ink(ink, mid, 3, task))
        except FileNotFoundError:
            results.append({"model_id": mid, "error": "Model tidak ditemukan."})
    return {"results": results}
