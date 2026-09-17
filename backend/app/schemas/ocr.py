"""Skema request/response untuk API OCR Lens (``/api/ocr/*``)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ScanOptionsIn(BaseModel):
    """Override opsional parameter pipeline (nama sama dengan ``ScanOptions``).

    Nilai bertipe salah/di luar rentang dijepit oleh :meth:`ScanOptions.from_dict`,
    jadi klien lama tidak bisa menjatuhkan server lewat opsi aneh.
    """

    model_config = ConfigDict(extra="ignore")

    script: Optional[str] = Field(None, description="auto | aksara | latin")
    tta: Optional[int] = Field(None, ge=0, le=12, description="test-time augmentation (0=cepat, 2=baku, 4=presisi)")
    beam_width: Optional[int] = Field(None, ge=1, le=64)
    use_language_model: Optional[bool] = None
    deskew: Optional[bool] = None
    binarize: Optional[str] = Field(None, description="sauvola | otsu | fixed")
    sauvola_window: Optional[int] = Field(None, ge=8, le=200)
    sauvola_k: Optional[float] = Field(None, ge=0.0, le=1.0)
    invert: Optional[str] = Field(None, description="auto | dark | light")
    min_area: Optional[int] = Field(None, ge=0, le=500)
    min_height: Optional[int] = Field(None, ge=2, le=60)
    close_iters: Optional[int] = Field(None, ge=0, le=4, description="morfologi penutup goresan putus")
    merge_gap_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    word_gap_ratio: Optional[float] = Field(None, ge=0.1, le=2.0)
    max_glyphs: Optional[int] = Field(None, ge=4, le=2000)
    split_marks: Optional[bool] = Field(None, description="pisahkan pangangge dari badan aksara")
    top_k: Optional[int] = Field(None, ge=1, le=10)
    split_width_ratio: Optional[float] = Field(None, ge=0.8, le=4.0)
    resplit_below: Optional[float] = Field(None, ge=0.0, le=1.0)
    with_crops: Optional[bool] = Field(None, description="sertakan PNG kecil tiap aksara (inspector)")
    upscale_small: Optional[bool] = None
    target_line_height: Optional[int] = Field(None, ge=12, le=200)
    script_margin: Optional[float] = Field(None, ge=0.0, le=2.0)
    line_min_ink: Optional[float] = Field(None, ge=0.0, le=0.2)
    max_side: Optional[int] = Field(None, ge=200, le=4000)


class ScanIn(BaseModel):
    image: str = Field(..., description="Data URL atau base64 mentah (JPEG/PNG)")
    options: Optional[ScanOptionsIn] = None
    annotate: bool = Field(False, description="Sertakan JPEG berbingkai kotak sebagai data URL")
    client: Optional[str] = Field(None, max_length=40, description="lens-mobile | lens-desktop (statistik)")


class AnnotateIn(ScanIn):
    background: str = Field("black", pattern="^(black|white)$")


class FeedbackIn(BaseModel):
    image: str = Field(..., description="Crop hasil OCR (data URL/base64) — satu aksara atau satu baris")
    task: str = Field("aksara", description="aksara | latin")
    label: Optional[str] = Field(None, max_length=8, description="Koreksi label; kosong → menunggu tinjau admin")
    kind: str = Field("glyph", pattern="^(glyph|line)$")
    scan_id: Optional[str] = Field(None, max_length=40)
    note: Optional[str] = Field(None, max_length=280)
    device: Optional[str] = Field(None, max_length=60, description="mis. iPhone 13 / Chrome 128")


class DecideIn(BaseModel):
    action: str = Field(..., pattern="^(accept|reject|relabel)$")
    label: Optional[str] = Field(None, max_length=8)
    split: Optional[str] = Field(None, description="train | val | test (untuk accept/relabel)")


class ConfigIn(BaseModel):
    default_options: Dict[str, Any] = Field(default_factory=dict)
    limits: Optional[Dict[str, Any]] = None
    feedback: Optional[Dict[str, Any]] = None
    note: Optional[str] = Field(None, max_length=400)


class TrainFromLensIn(BaseModel):
    task: str = Field("aksara", description="aksara | latin")
    arch: str = Field("deepcnn")
    name: Optional[str] = Field(None, max_length=80)
    auto_approve: bool = Field(True, description="Setujui semua koreksi berlabel sebelum training")
    auto_promote: bool = Field(True, description="Jadikan model terbaik sebagai produksi setelah training")
    hyperparams: Dict[str, Any] = Field(default_factory=dict)


class OcrTaskStatus(BaseModel):
    ready: bool = False
    model_id: Optional[str] = None
    name: Optional[str] = None
    arch: Optional[str] = None
    accuracy: Optional[float] = None
    real_handwriting_accuracy: Optional[float] = None
    n_classes: int = 0
    classes: List[str] = Field(default_factory=list)


class OcrStatusOut(BaseModel):
    mode: str
    is_admin: bool = False
    tasks: Dict[str, OcrTaskStatus]
    limits: Dict[str, Any] = Field(default_factory=dict)
    feedback: Dict[str, Any] = Field(default_factory=dict)
    default_options: ScanOptionsIn = Field(default_factory=ScanOptionsIn)
