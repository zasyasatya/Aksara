"""Definisi *task* pada subsistem ML: satu pipeline dataset→training→model per aksara.

Dulu panel ML hanya mengenal satu tugas (klasifikasi 18 Wresastra). OCR Lens butuh
dua pengenal berbeda — aksara Bali dan huruf Latin — dengan dataset, model, dan
registry masing-masing. ``tasks.py`` adalah satu-satunya tempat yang tahu adanya
tugas-tugas itu; seluruh modul lain (store, training, inference, bundled, router)
hanya meneruskan ``task``.

Struktur data per tugas di ``backend/app/data/ml/<task>/``::

    ml/<task>/
    ├── classes.json              kelas aktif
    ├── dataset/index.json        metadata sampel
    ├── dataset/images/<id>.png   PNG kanonik 64×64
    └── models/registry.json      model terlatih + model produksi
        models/<model_id>/        model.npz · model.json · report.json
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .synthetic import GlyphClass

DEFAULT_TASK = "aksara"


@dataclass(frozen=True)
class MlTask:
    id: str
    name: str                 # nama tampilan (Panel Admin)
    short: str
    description: str
    groups: tuple             # kelompok kelas default dari aksara_master / latin_master
    default_classes: tuple    # label yang aktif bila kelas belum disimpan
    default_arch: str
    script: str               # "bali" | "latin" — dipakai pipeline OCR untuk memilih model


TASKS: Dict[str, MlTask] = {
    "aksara": MlTask(
        id="aksara",
        name="Aksara Bali (Hanacaraka)",
        short="Aksara Bali",
        description="Klasifikasi aksara, pangangge, dan angka Bali — tulisan tangan & tercetak.",
        groups=("wresastra", "pangangge_suara", "pangangge_tengenan", "angka"),
        default_classes=(
            "ha", "na", "ca", "ra", "ka", "da", "ta", "sa", "wa", "la", "ma", "ga", "ba",
            "nga", "pa", "ja", "ya", "nya", "ulu", "suku", "pepet", "taleng", "bisah",
            "cecek", "surang", "adeg_adeg",
        ),
        default_arch="deepcnn",
        script="bali",
    ),
    "latin": MlTask(
        id="latin",
        name="Latin (huruf & angka)",
        short="Latin",
        description="OCR huruf Latin untuk teks terjemahan/label pada foto kamera.",
        groups=("latin",),
        default_classes=tuple("abcdefghijklmnopqrstuvwxyz0123456789"),
        default_arch="deepcnn",
        script="latin",
    ),
}


def resolve(task: Optional[str]) -> str:
    """Normalisasi nama tugas; nilai kosong → tugas aksara (kompatibel lama)."""
    if not task:
        return DEFAULT_TASK
    t = str(task).strip().lower()
    if t in ("bali", "aksara-bali", "aksara_bali"):
        return "aksara"
    if t not in TASKS:
        raise ValueError(f"Tugas tidak dikenal: {task}. Pilihan: {', '.join(TASKS)}")
    return t


def get(task: Optional[str]) -> MlTask:
    return TASKS[resolve(task)]


def list_tasks() -> List[Dict]:
    return [
        {
            "id": t.id,
            "name": t.name,
            "short": t.short,
            "description": t.description,
            "script": t.script,
            "default_arch": t.default_arch,
            "n_default_classes": len(t.default_classes),
        }
        for t in TASKS.values()
    ]


def is_valid(task: Optional[str]) -> bool:
    try:
        resolve(task)
        return True
    except ValueError:
        return False


# ── kelas Latin (tidak diambil dari aksara_master) ──────────────────────────

def latin_classes() -> List[GlyphClass]:
    """26 huruf kecil + 10 angka. OCR Lens membandingkan huruf dalam satu kasus."""
    out = [
        GlyphClass(label=chr(c), glyph=chr(c), name=f"Huruf {chr(c).upper()}", latin=chr(c), group="huruf")
        for c in range(0x61, 0x7B)
    ]
    out += [
        GlyphClass(label=str(d), glyph=str(d), name=f"Angka {d}", latin=str(d), group="angka")
        for d in range(10)
    ]
    return out


def classes_for_task(task: Optional[str], master: dict) -> List[GlyphClass]:
    """Semua kelas yang dapat diaktifkan pada suatu tugas."""
    from .synthetic import build_classes

    spec = get(task)
    groups = [g for g in spec.groups if g != "latin"]
    out: List[GlyphClass] = []
    if groups:
        out = build_classes(master, tuple(groups))
    if "latin" in spec.groups:
        out = latin_classes()
    return out
