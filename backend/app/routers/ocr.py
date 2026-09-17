"""Router **OCR Lens** — baca kamera (Aksara Bali + Latin), terjemahkan, kumpulkan koreksi.

Endpoint publik (dipakai halaman ``/lens``):

    GET  /api/ocr/status              kesiapan model per tugas + opsi default + batas pakai
    POST /api/ocr/scan              { image, options? } → hasil OCR satu citra
    POST /api/ocr/scan/file         unggah multipart (fallback browser lama / curl)
    POST /api/ocr/feedback            kirim crop yang salah baca ke antrean admin

Endpoint admin (login admin pada mode prod):

    GET  /api/ocr/feedback            daftar antrean koreksi
    POST /api/ocr/feedback/{id}/decide  accept / reject / relabel
    POST /api/ocr/feedback/train      setujui semua + latih ulang model tugas itu
    GET  /api/ocr/config            · PUT /api/ocr/config (opsi pipeline, batas, feedback)
    POST /api/ocr/models/install    pasang model bawaan repo ke store ML
    GET  /api/ocr/selftest          render teks known → OCR → CER (uji pipeline)

Semua tulisan diarahkan lewat ``app.ocr.pipeline`` yang memakai model dari store ML
Panel Admin, jadi retraining di admin langsung mengubah hasil halaman Lens.
"""

from __future__ import annotations

import io
import threading
import time
import uuid
from typing import Dict, Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, Query, Request, Response, UploadFile

from ..core import security
from ..core.config import settings
from ..ml import features, pretrain, store, training
from ..ocr import config as ocr_config
from ..ocr import pipeline
from ..ocr import render as ocr_render
from ..schemas.ocr import AnnotateIn, ConfigIn, DecideIn, FeedbackIn, ScanIn, TrainFromLensIn

router = APIRouter(prefix="/ocr", tags=["ocr"])


# ── otorisasi & pembatas ───────────────────────────────────────────────────

def _role(authorization: Optional[str]) -> Optional[str]:
    if not settings.is_prod:
        return "admin"
    return security.get_session_role(security.bearer_token(authorization))


def _require_admin(authorization: Optional[str]) -> None:
    if _role(authorization) != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak. Login sebagai Admin diperlukan pada mode prod.")


_lock = threading.Lock()
_buckets: Dict[str, tuple] = {}


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for") or ""
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _throttle(scope: str, request: Request, per_minute: int) -> None:
    """Token bucket kasar per IP (menit berjalan)."""
    if per_minute <= 0:
        return
    # Admin (sesi login) dibebaskan — tapi hanya pada mode prod; di dev semua orang
    # "admin", jadi batasnya tetap berlaku supaya dapat diuji dan tidak mengejutkan.
    if settings.is_prod and _role(request.headers.get("authorization")) == "admin":
        return
    now = time.time()
    key = f"{scope}:{_client_ip(request)}"
    with _lock:
        window, count = _buckets.get(key, (int(now // 60), 0))
        if window != int(now // 60):
            window, count = int(now // 60), 0
        if count >= per_minute:
            raise HTTPException(status_code=429,
                                detail=f"Terlalu banyak permintaan (maks {per_minute}/menit). Tunggu sebentar.")
        _buckets[key] = (window, count + 1)
        if len(_buckets) > 4096:  # jaga memori
            _buckets.clear()


def _read_image(data: bytes, limits: Dict) -> bytes:
    if not data:
        raise HTTPException(status_code=400, detail="Berkas gambar kosong.")
    if len(data) > int(limits.get("max_image_bytes", 8_000_000)):
        raise HTTPException(status_code=413, detail="Gambar terlalu besar untuk diproses.")
    return data


def _scan(body_image: str = "", data: Optional[bytes] = None, options: Optional[dict] = None,
          annotate: bool = False) -> Dict:
    limits = ocr_config.limits()
    if data is None:
        try:
            data = features.decode_base64_image(body_image)
        except features.ImageDecodeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    data = _read_image(data, limits)
    opts = ocr_config.merged_options(options)
    opts.setdefault("max_side", int(limits.get("max_side", 2400)))
    try:
        out = pipeline.scan_bytes(data, options=opts)
    except LookupError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:  # pragma: no cover - citra rusak
        raise HTTPException(status_code=422, detail=f"Gambar tidak dapat dibaca: {exc}")
    out["scan_id"] = uuid.uuid4().hex[:10]
    if annotate:
        out["annotated"] = _annotated_data_url(data, out)
    return out


# ── status ─────────────────────────────────────────────────────────────────

@router.get("/status")
async def ocr_status(authorization: Optional[str] = Header(default=None)):
    """Model produksi per tugas + kesiapan Lens + batas yang berlaku."""
    out: Dict = {"mode": "prod" if settings.is_prod else "dev", "is_admin": _role(authorization) == "admin",
                 "limits": ocr_config.limits(), "feedback": ocr_config.feedback_config(),
                 "default_options": ocr_config.get_config().get("default_options", {}), "tasks": {}}
    for task in ("aksara", "latin"):
        mid = store.production_model_id(task)
        entry = store.get_model_entry(mid, task) if mid else None
        metrics = (entry or {}).get("metrics") or {}
        out["tasks"][task] = {
            "ready": bool(entry),
            "model_id": mid,
            "name": (entry or {}).get("name"),
            "arch": (entry or {}).get("arch"),
            "created_at": (entry or {}).get("created_at"),
            "accuracy": metrics.get("accuracy"),
            "real_handwriting_accuracy": metrics.get("real_handwriting_accuracy"),
            "n_classes": len(store.class_labels(task)),
            "classes": store.class_labels(task),
            "dataset": {k: store.dataset_stats(task).get(k) for k in ("labeled", "review", "unlabeled")},
        }
    out["bundled"] = pretrain.status()
    out["corrections_pending"] = ocr_config.pending(limit=0)["review"]
    return out


# ── scan ───────────────────────────────────────────────────────────────────

@router.post("/scan")
async def scan(body: ScanIn, request: Request):
    """Citra (data URL/base64) → baris, aksara, translasi. Body ``options`` untuk override."""
    _throttle("scan", request, int(ocr_config.limits().get("scan_per_minute", 30)))
    return _scan(body_image=body.image, annotate=body.annotate,
                 options=body.options.model_dump(exclude_none=True) if body.options else None)


@router.post("/scan/file")
async def scan_file(request: Request, file: UploadFile = File(...), options: str = Form(""),
                    annotate: str = Form("")):
    """Versi multipart (kamera hp / ``curl -F``). ``options`` = JSON string opsional."""
    _throttle("scan", request, int(ocr_config.limits().get("scan_per_minute", 30)))
    data = await file.read()
    import json as _json

    parsed = {}
    if options.strip():
        try:
            parsed = _json.loads(options)
        except ValueError:
            raise HTTPException(status_code=400, detail="options harus JSON yang valid.")
    return _scan(data=data, options=parsed, annotate=annotate in ("1", "true", "yes"))


@router.post("/scan/annotate")
async def scan_annotate(body: AnnotateIn, request: Request):
    """Seperti ``/scan`` tetapi mengembalikan JPEG berbingkai (untuk dibagikan)."""
    _throttle("scan", request, int(ocr_config.limits().get("scan_per_minute", 30)))
    res = _scan(body_image=body.image, options=body.options.model_dump(exclude_none=True) if body.options else None)
    try:
        data = features.decode_base64_image(body.image)
    except features.ImageDecodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return Response(content=_annotated_bytes(data, res, background=body.background), media_type="image/jpeg")


# ── umpan balik (koreksi dari pengguna) ────────────────────────────────────

@router.post("/feedback")
async def submit_feedback(body: FeedbackIn, request: Request):
    """Kirim crop hasil OCR yang salah ke antrean admin (``source=camera``).

    Tanpa ``label`` sampel masuk dengan status ``review`` sehingga tidak ikut training
    sebelum admin meninjau.
    """
    limits = ocr_config.limits()
    if not ocr_config.feedback_config().get("enabled", True):
        raise HTTPException(status_code=503, detail="Pengumpulan koreksi sedang ditutup oleh admin.")
    _throttle("feedback", request, int(limits.get("feedback_per_minute", 8)))
    try:
        data = features.decode_base64_image(body.image)
    except features.ImageDecodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    data = _read_image(data, limits)
    if body.task not in ("aksara", "latin"):
        raise HTTPException(status_code=400, detail="Tugas harus 'aksara' atau 'latin'.")
    labels = store.class_labels(body.task)
    if body.label and body.label not in labels:
        raise HTTPException(status_code=400, detail=f"Label '{body.label}' bukan kelas aktif tugas {body.task}.")
    try:
        ink = features.ink_from_bytes(data)
    except features.ImageDecodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    meta = {"via": "lens", "kind": body.kind, "scan_id": body.scan_id, "device": body.device,
            "corrected": bool(body.label)}
    try:
        entry = ocr_config.submit_feedback(ink, body.label, body.task, body.note or "", meta)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"sample_id": entry["id"], "task": body.task, "status": entry.get("status"),
            "message": "Koreksi terkirim. Terima kasih — admin akan meninjau untuk training berikutnya."}


@router.get("/feedback")
async def list_feedback(task: Optional[str] = Query(None, pattern="^(aksara|latin)$"), limit: int = Query(60, ge=1, le=300),
                        offset: int = Query(0, ge=0), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    return ocr_config.pending(task, limit, offset)


@router.get("/feedback/{sample_id}/image")
async def feedback_image(sample_id: str, task: str = Query("aksara"), authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    entry = store.get_sample(sample_id, task)
    if entry is None:
        raise HTTPException(status_code=404, detail="Sampel tidak ditemukan.")
    png = store.image_path(sample_id, task)
    if not png.is_file():
        raise HTTPException(status_code=404, detail="Gambar sampel hilang.")
    return Response(content=png.read_bytes(), media_type="image/png")


@router.post("/feedback/{sample_id}/decide")
async def decide_feedback(sample_id: str, body: DecideIn, task: str = Query("aksara"),
                          authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    try:
        return ocr_config.decide(sample_id, task, body.action, body.label, body.split)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sampel tidak ditemukan.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/feedback/train")
async def train_from_lens(body: TrainFromLensIn, authorization: Optional[str] = Header(default=None)):
    """Setujui koreksi Lens lalu latih ulang model tugas tersebut (job latar belakang)."""
    _require_admin(authorization)
    if body.task not in ("aksara", "latin"):
        raise HTTPException(status_code=400, detail="Tugas harus 'aksara' atau 'latin'.")
    if training.active_job(body.task):
        raise HTTPException(status_code=409, detail="Masih ada job training berjalan untuk tugas ini.")
    approved = ocr_config.approve_all(body.task) if body.auto_approve else 0
    stats = store.dataset_stats(body.task)
    if stats["labeled"] + approved < 8:
        raise HTTPException(status_code=400, detail="Data berlabel terlalu sedikit untuk training (min. 8 sampel).")
    mid = store.production_model_id(body.task)
    hp = dict((store.get_model_entry(mid, body.task) or {}).get("hyperparams") or {})
    hp.update(body.hyperparams or {})
    name = body.name or f"Lens {body.task} · koreksi kamera ({time.strftime('%d/%m %H:%M')})"
    note = f"Dari koreksi Lens — {approved} koreksi disetujui otomatis" if approved else "Dari koreksi Lens"
    try:
        # `task` WAJIB sebagai keyword: urutan posisinya adalah (arch, hp, name, notes,
        # auto_promote, task) — lewat posisi, tugas malah tertulis di catatan.
        job = training.start_training(body.arch, hp, name, notes=note,
                                      auto_promote=body.auto_promote, task=body.task)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"job": {k: job[k] for k in ("id", "status", "arch", "task", "message")},
            "approved": approved, "auto_promote": body.auto_promote,
            "dataset": {k: stats[k] for k in ("labeled", "review", "unlabeled", "total")},
            "message": f"Job pelatihan model tugas {body.task} dijalankan."}


# ── konfigurasi & perawatan ────────────────────────────────────────────────

@router.get("/config")
async def get_ocr_config(authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    cfg = ocr_config.get_config()
    return {**cfg, "defaults": {"default_options": ocr_config.DEFAULT_OPTIONS, "limits": ocr_config.DEFAULT_LIMITS,
                                "feedback": ocr_config.DEFAULT_FEEDBACK},
            "pipeline_fields": sorted(pipeline.ScanOptions.__dataclass_fields__)}


@router.put("/config")
async def put_ocr_config(body: ConfigIn, authorization: Optional[str] = Header(default=None)):
    _require_admin(authorization)
    patch = {k: v for k, v in body.model_dump().items() if v not in (None, {})}
    try:
        data = ocr_config.update_config(patch)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=f"Konfigurasi ditolak: {exc}")
    return {**data, "message": "Konfigurasi Lens tersimpan."}


@router.post("/models/install")
async def install_bundled(force: bool = Query(False), authorization: Optional[str] = Header(default=None)):
    """Salin model bawaan repo (hasil ``eval/train_ocr_models.py``) ke store ML."""
    _require_admin(authorization)
    res = pretrain.ensure_installed(force=force)
    inference_ready = {t: bool(store.production_model_id(t)) for t in ("aksara", "latin")}
    return {"installed": res, "production": inference_ready,
            "message": "Model bawaan terpasang." if any(inference_ready.values()) else "Model bawaan tidak ditemukan."}


@router.get("/selftest")
async def selftest(task: str = Query("aksara", pattern="^(aksara|latin)$"), font_size: int = Query(48, ge=16, le=180),
                   authorization: Optional[str] = Header(default=None)):
    """Uji mandiri pipeline: teks known dirender → OCR → CER/exact (tanpa dataset)."""
    _require_admin(authorization)
    opts = ocr_config.merged_options(None)
    t0 = time.time()
    res = ocr_render.selftest(task, opts, font_size=font_size)
    res["elapsed_ms"] = int((time.time() - t0) * 1000)
    return res


# ── anotasi (gambar berbingkai) ────────────────────────────────────────────

def _annotated_bytes(data: bytes, result: Dict, background: str = "black") -> bytes:
    from PIL import Image, ImageDraw

    img = Image.open(io.BytesIO(data)).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)
    base = (0, 0, 0) if background == "black" else (255, 255, 255)
    ink = (235, 140, 40) if background == "black" else (170, 70, 20)
    mark = (90, 190, 140) if background == "black" else (40, 120, 90)
    for ln in result.get("lines", []):
        for g in ln.get("glyphs", []):
            x, y, w, h = g.get("rect") or (0, 0, 0, 0)
            box = [x * W, y * H, (x + w) * W, (y + h) * H]
            draw.rectangle(box, outline=ink, width=2)
            for m in g.get("marks", []):
                mx, my, mw, mh = m.get("rect") or (0, 0, 0, 0)
                draw.rectangle([mx * W, my * H, (mx + mw) * W, (my + mh) * H], outline=mark, width=1)
            conf = float(g.get("confidence") or 0.0)
            if conf and conf < 0.55:
                draw.rectangle([box[0] - 2, box[1] - 2, box[2] + 2, box[3] + 2], outline=base, width=1)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return buf.getvalue()


def _annotated_data_url(data: bytes, result: Dict) -> str:
    import base64

    return "data:image/jpeg;base64," + base64.b64encode(_annotated_bytes(data, result)).decode("ascii")
