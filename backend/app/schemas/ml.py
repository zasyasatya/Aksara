"""Skema Pydantic untuk API machine-learning (/api/ml)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str


# ── Kelas ──────────────────────────────────────────────────────────────────

class ClassesUpdate(BaseModel):
    labels: List[str] = Field(..., min_length=2, description="Label kelas yang diaktifkan (urut)")


# ── Dataset ────────────────────────────────────────────────────────────────

class GenerateSyntheticIn(BaseModel):
    per_class: int = Field(40, ge=1, le=400, description="Jumlah sampel sintetis per kelas")
    seed: int = Field(20260904, ge=0)
    strength: float = Field(1.0, ge=0.0, le=2.0, description="Kekuatan augmentasi (0 = glyph font bersih)")
    replace_existing: bool = Field(False, description="Hapus sampel sintetis lama sebelum generate")


class SampleIn(BaseModel):
    image: str = Field(..., description="Data URL / base64 PNG|JPEG tinta")
    label: Optional[str] = Field(None, description="Label kelas; kosong → masuk antrean labeling")
    source: str = Field("canvas", pattern="^(upload|canvas|import)$")
    split: Optional[str] = Field(None, pattern="^(train|val|test)$")
    note: str = Field("", max_length=300)


class SampleBulkIn(BaseModel):
    items: List[SampleIn] = Field(..., min_length=1, max_length=200)


class SampleUpdate(BaseModel):
    label: Optional[str] = None
    clear_label: bool = False
    split: Optional[str] = Field(None, pattern="^(train|val|test)$")
    status: Optional[str] = Field(None, pattern="^(labeled|unlabeled|review)$")
    note: Optional[str] = Field(None, max_length=300)


class BulkLabelIn(BaseModel):
    ids: List[str] = Field(..., min_length=1, max_length=500)
    label: Optional[str] = None
    split: Optional[str] = Field(None, pattern="^(train|val|test)$")
    status: Optional[str] = Field(None, pattern="^(labeled|unlabeled|review)$")


class BulkDeleteIn(BaseModel):
    ids: List[str] = Field(..., min_length=1, max_length=2000)


class ImportBundledIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80, description="Nama folder paket di <repo>/dataset/")
    activate_classes: bool = Field(True, description="Jadikan kelas paket sebagai kelas aktif")
    replace_existing: bool = Field(True, description="Hapus impor paket yang sama sebelumnya (idempoten)")
    keep_split: bool = Field(True, description="Pakai split train/val/test dari manifest")


class RebalanceIn(BaseModel):
    val_ratio: float = Field(0.15, ge=0.0, le=0.5)
    test_ratio: float = Field(0.15, ge=0.0, le=0.5)
    seed: int = Field(0, ge=0)


# ── Training ───────────────────────────────────────────────────────────────

class TrainIn(BaseModel):
    arch: str = Field(..., description="template | centroid | knn | logreg | mlp | cnn")
    hyperparams: Dict[str, Any] = Field(default_factory=dict)
    name: str = Field("", max_length=80)
    notes: str = Field("", max_length=500)
    auto_promote: bool = Field(False, description="Langsung jadikan model produksi bila selesai")


class ModelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=80)
    notes: Optional[str] = Field(None, max_length=500)


class PromoteIn(BaseModel):
    model_id: Optional[str] = Field(None, description="null → nonaktifkan model produksi")


# ── Prediksi ───────────────────────────────────────────────────────────────

class PredictIn(BaseModel):
    image: str = Field(..., description="Data URL / base64 gambar tinta")
    model_id: Optional[str] = Field(None, description="Kosong → model produksi")
    top_k: int = Field(5, ge=1, le=20)


class CompareIn(BaseModel):
    image: str
    model_ids: List[str] = Field(..., min_length=1, max_length=10)
