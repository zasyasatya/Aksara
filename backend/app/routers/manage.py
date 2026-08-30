"""Router manajemen konten oleh Guru.

Guru dapat memperbarui materi (lessons), kuis, dan kamus kata khusus
tanpa menyentuh kode — semua editan langsung tersimpan ke file JSON data
dan langsung terlihat oleh murid (baca per-request).

Otentikasi memakai sesi login (username + password, lihat routers/auth.py):
- Mode DEV  → semua pengakses dianggap guru (mudah untuk development/demo).
- Mode PROD → wajib login Guru/Admin; session token dikirim sebagai header
  ``Authorization: Bearer <token>`` (akun admin juga dapat mengelola konten).
"""

import re
import unicodedata
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from ..core.config import settings
from ..core import security
from ..services import data_store
from ..schemas.manage import (
    DictIn, LessonIn, ManageStatus, MessageResponse, QuizIn
)

router = APIRouter(prefix="/manage", tags=["manage"])


def _role(authorization: Optional[str]) -> Optional[str]:
    """Role sesi aktif: 'admin'/'guru', atau None bila tidak login.

    Mode dev tidak mensyaratkan sesi — dianggap guru.
    """
    if not settings.is_prod:
        return "guru"
    return security.get_session_role(security.bearer_token(authorization))


def is_guru(authorization: Optional[str]) -> bool:
    return _role(authorization) in ("admin", "guru")


def _require_guru(authorization: Optional[str]) -> None:
    if not is_guru(authorization):
        raise HTTPException(
            status_code=403,
            detail="Akses ditolak. Login sebagai Guru diperlukan pada mode prod.",
        )


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "item"


def _unique_id(lessons, base: str) -> str:
    existing = {l.get("id") for l in lessons}
    if base not in existing:
        return base
    i = 2
    while f"{base}-{i}" in existing:
        i += 1
    return f"{base}-{i}"


# ── Status ──────────────────────────────────────────────────────────────

@router.get("/status", response_model=ManageStatus)
async def manage_status(authorization: Optional[str] = Header(default=None)):
    role = _role(authorization)
    return ManageStatus(
        mode="prod" if settings.is_prod else "dev",
        is_guru=role in ("admin", "guru"),
        is_admin=(role == "admin"),
    )


# ── Materi (lessons) ────────────────────────────────────────────────────

@router.get("/lessons")
async def list_manage_lessons():
    lessons = sorted(data_store.get_lessons(), key=lambda l: (l.get("order", 0), l.get("id", "")))
    return {"lessons": lessons, "total": len(lessons)}


@router.post("/lessons", status_code=201)
async def create_lesson(body: LessonIn, authorization: Optional[str] = Header(default=None)):
    _require_guru(authorization)
    lessons = data_store.get_lessons()

    if body.id:
        if any(l.get("id") == body.id for l in lessons):
            raise HTTPException(status_code=409, detail=f"Materi dengan id '{body.id}' sudah ada.")
        lesson_id = body.id
    else:
        lesson_id = _unique_id(lessons, _slugify(body.title)[:40] or "materi")

    data = body.model_dump(exclude_none=True)
    data["id"] = lesson_id
    data.setdefault("slug", _slugify(body.title))
    data.setdefault("title", body.title)
    data.setdefault("level", 1)
    data.setdefault("order", len(lessons) + 1)
    data.setdefault("category", "wresastra")
    data.setdefault("aksara_ids", [])
    data.setdefault("pangangge_ids", [])
    data.setdefault("estimated_minutes", 10)
    data.setdefault("xp_reward", 50)
    data.setdefault("prerequisites", [])
    data.setdefault("quiz_ids", [])
    data.setdefault("is_published", True)

    lessons.append(data)
    data_store.save_lessons(lessons)
    return data


@router.put("/lessons/{lesson_id}")
async def update_lesson(lesson_id: str, body: LessonIn, authorization: Optional[str] = Header(default=None)):
    _require_guru(authorization)
    lessons = data_store.get_lessons()
    idx = next((i for i, l in enumerate(lessons) if l.get("id") == lesson_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Materi '{lesson_id}' tidak ditemukan.")

    data = lessons[idx]
    updates = body.model_dump(exclude_none=True)
    updates.pop("id", None)  # id tidak boleh berubah
    data.update(updates)
    data["id"] = lesson_id
    data_store.save_lessons(lessons)
    return data


@router.delete("/lessons/{lesson_id}", response_model=MessageResponse)
async def delete_lesson(lesson_id: str, authorization: Optional[str] = Header(default=None)):
    _require_guru(authorization)
    lessons = data_store.get_lessons()
    remaining = [l for l in lessons if l.get("id") != lesson_id]
    if len(remaining) == len(lessons):
        raise HTTPException(status_code=404, detail=f"Materi '{lesson_id}' tidak ditemukan.")
    # bersihkan referensi dari materi lain (prerequisites & quiz_ids tetap aman)
    for l in remaining:
        l["prerequisites"] = [p for p in l.get("prerequisites", []) if p != lesson_id]
    data_store.save_lessons(remaining)
    return MessageResponse(message=f"Materi '{lesson_id}' dihapus.")


# ── Kuis ────────────────────────────────────────────────────────────────

@router.get("/quizzes")
async def list_manage_quizzes():
    quizzes = data_store.get_quizzes()
    return {"quizzes": quizzes, "total": len(quizzes)}


@router.post("/quizzes", status_code=201)
async def create_quiz(body: QuizIn, authorization: Optional[str] = Header(default=None)):
    _require_guru(authorization)
    quizzes = data_store.get_quizzes()

    if body.id:
        if any(q.get("id") == body.id for q in quizzes):
            raise HTTPException(status_code=409, detail=f"Kuis dengan id '{body.id}' sudah ada.")
        quiz_id = body.id
    else:
        base = f"quiz-custom-{_slugify((body.question.text or 'soal'))[:20]}"
        quiz_id = _unique_id(quizzes, base)

    data = body.model_dump()
    data["id"] = quiz_id
    data.setdefault("type", "multiple_choice")
    data.setdefault("difficulty", "easy")
    data.setdefault("xp", 10)
    quizzes.append(data)
    data_store.save_quizzes(quizzes)
    return data


@router.put("/quizzes/{quiz_id}")
async def update_quiz(quiz_id: str, body: QuizIn, authorization: Optional[str] = Header(default=None)):
    _require_guru(authorization)
    quizzes = data_store.get_quizzes()
    idx = next((i for i, q in enumerate(quizzes) if q.get("id") == quiz_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Kuis '{quiz_id}' tidak ditemukan.")

    data = quizzes[idx]
    updates = body.model_dump()
    updates.pop("id", None)
    data.update(updates)
    data["id"] = quiz_id
    data_store.save_quizzes(quizzes)
    return data


@router.delete("/quizzes/{quiz_id}", response_model=MessageResponse)
async def delete_quiz(quiz_id: str, authorization: Optional[str] = Header(default=None)):
    _require_guru(authorization)
    quizzes = data_store.get_quizzes()
    remaining = [q for q in quizzes if q.get("id") != quiz_id]
    if len(remaining) == len(quizzes):
        raise HTTPException(status_code=404, detail=f"Kuis '{quiz_id}' tidak ditemukan.")
    data_store.save_quizzes(remaining)
    # rapikan referensi di materi
    lessons = data_store.get_lessons()
    changed = False
    for l in lessons:
        if quiz_id in l.get("quiz_ids", []):
            l["quiz_ids"] = [q for q in l["quiz_ids"] if q != quiz_id]
            changed = True
    if changed:
        data_store.save_lessons(lessons)
    return MessageResponse(message=f"Kuis '{quiz_id}' dihapus.")


# ── Kamus (dictionary) ──────────────────────────────────────────────────

@router.get("/dictionary")
async def list_manage_dictionary():
    data = data_store.get_dictionary()
    entries = [{"latin": k, **v} for k, v in data.items()]
    return {"entries": sorted(entries, key=lambda e: e["latin"]), "total": len(entries)}


@router.post("/dictionary", status_code=201)
async def upsert_dictionary(body: DictIn, authorization: Optional[str] = Header(default=None)):
    _require_guru(authorization)
    data = data_store.get_dictionary()
    key = body.latin.strip().lower()
    data[key] = {
        "latin": body.latin.strip(),
        "bali": body.bali,
        "meaning": body.meaning or "",
        "note": body.note or "",
    }
    data_store.save_dictionary(data)
    return data[key]


@router.delete("/dictionary/{latin}", response_model=MessageResponse)
async def delete_dictionary_entry(latin: str, authorization: Optional[str] = Header(default=None)):
    _require_guru(authorization)
    data = data_store.get_dictionary()
    key = latin.strip().lower()
    if key not in data:
        raise HTTPException(status_code=404, detail=f"Kata '{latin}' tidak ada di kamus.")
    del data[key]
    data_store.save_dictionary(data)
    return MessageResponse(message=f"Kata '{latin}' dihapus dari kamus.")


# ── Referensi untuk form (read-only) ────────────────────────────────────

@router.get("/aksara")
async def get_aksara_reference():
    """Daftar aksara & pangangge untuk picker di form guru."""
    master = data_store.get_aksara_master()
    groups = []
    for cat in ["wresastra", "swalalita_extra", "suara", "pangangge_suara", "pangangge_tengenan", "pangangge_aksara"]:
        items = master.get(cat, [])
        if items:
            groups.append({
                "category": cat,
                "items": [
                    {"id": it.get("id"), "bali": it.get("bali"), "latin": it.get("latin"), "name": it.get("name")}
                    for it in items
                ],
            })
    return {"groups": groups}
