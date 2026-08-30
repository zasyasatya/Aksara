"""Endpoint engagement & sekolah mitra (publik, tanpa token).

Mendukung narasi "market potential" & proof of concept:
- Counter kunjungan + twibbon yang dibuat (dengan rate-limit per IP
  agar angka tetap jujur dan bisa dikutip di paper).
- Pendaftaran sekolah/sanggar (form publik, status "pending" sampai
  diverifikasi manual oleh tim Aksara).
"""

import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request

from ..services import data_store
from ..schemas.engagement import EngagementStats, MessageResponse, SchoolIn

router = APIRouter(prefix="/stats", tags=["engagement"])

# Rate-limit sederhana: maks 1 increment per IP per N detik.
_BUMP_COOLDOWN = 20  # detik
_last_bump = {}  # (ip, key) -> timestamp


def _rate_ok(request: Request, key: str) -> bool:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    prev = _last_bump.get((ip, key))
    if prev is not None and now - prev < _BUMP_COOLDOWN:
        return False
    _last_bump[(ip, key)] = now
    # jaga agar dict tidak membengkak
    if len(_last_bump) > 10000:
        _last_bump.clear()
        _last_bump[(ip, key)] = now
    return True


@router.get("", response_model=EngagementStats)
async def get_stats():
    """Counter & daftar sekolah untuk landing page / paper."""
    data = data_store.get_engagement()
    return EngagementStats(
        visits=data["visits"],
        twibbons=data["twibbons"],
        schools=data["schools"],
    )


@router.post("/visit", response_model=MessageResponse)
async def track_visit(request: Request):
    if not _rate_ok(request, "visits"):
        return MessageResponse(message="ok (throttled)")
    data_store.bump_engagement("visits")
    return MessageResponse(message="ok")


@router.post("/twibbon", response_model=MessageResponse)
async def track_twibbon(request: Request):
    if not _rate_ok(request, "twibbons"):
        return MessageResponse(message="ok (throttled)")
    data_store.bump_engagement("twibbons")
    return MessageResponse(message="ok")


@router.get("/schools")
async def list_schools():
    data = data_store.get_engagement()
    schools: List[dict] = data["schools"]
    return {"schools": schools, "total": len(schools)}


@router.post("/schools", status_code=201)
async def apply_school(body: SchoolIn):
    """Form publik: sekolah/sanggar/pasraman mendaftar menjadi mitra."""
    data = data_store.get_engagement()
    for s in data["schools"]:
        if s.get("school", "").strip().lower() == body.school.strip().lower():
            raise HTTPException(status_code=409, detail=f"'{body.school}' sudah terdaftar.")
    entry = {
        "id": f"school-{len(data['schools']) + 1:03d}",
        "school": body.school.strip(),
        "region": (body.region or "").strip(),
        "students": body.students,
        "contact": body.contact.strip(),
        "note": (body.note or "").strip(),
        "is_verified": False,
        "joined_at": time.strftime("%Y-%m-%d"),
    }
    data["schools"].append(entry)
    data_store.save_engagement(data)
    return entry
