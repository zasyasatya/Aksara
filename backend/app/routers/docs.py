"""Router dokumentasi.

Menyediakan:
- GET   /api/docs/pages            → daftar halaman dokumentasi + mode + status admin
- PATCH /api/docs/pages/{slug}/visibility → ubah status publik/privat (admin only)

Aturan visibilitas:
- Mode DEV : semua halaman selalu dikembalikan, is_admin selalu True.
- Mode PROD: hanya halaman `is_public: true` yang dikembalikan untuk pengguna
  biasa. Admin (header X-Admin-Token valid) tetap melihat semua halaman agar
  bisa mengatur mana yang "go public".
"""

import json
import os
import threading
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException

from ..core.config import settings
from ..schemas.docs import DocsPage, DocsPagesResponse, VisibilityResponse, VisibilityUpdate

router = APIRouter(prefix="/docs", tags=["docs"])

DOCS_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "docs.json"
# RLock: endpoint visibilitas memegang lock saat memuat, lalu memanggil
# _save_pages yang mengunci lagi — Lock biasa akan deadlock.
_file_lock = threading.RLock()


def _load_pages() -> List[dict]:
    if not DOCS_DATA_PATH.is_file():
        return []
    with open(DOCS_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("pages", [])


def _save_pages(pages: List[dict]) -> None:
    payload = {"pages": pages}
    with _file_lock:
        tmp = DOCS_DATA_PATH.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DOCS_DATA_PATH)


def is_admin(token: Optional[str]) -> bool:
    """Mode dev: admin otomatis. Mode prod: cocokkan token."""
    if not settings.is_prod:
        return True
    return bool(settings.admin_token) and token == settings.admin_token


@router.get("/pages", response_model=DocsPagesResponse)
async def list_docs_pages(x_admin_token: Optional[str] = Header(default=None)):
    """Daftar halaman dokumentasi.

    Di mode prod, non-admin hanya menerima halaman publik.
    """
    pages_raw = _load_pages()
    admin = is_admin(x_admin_token)
    if settings.is_prod and not admin:
        pages_raw = [p for p in pages_raw if p.get("is_public", True)]
    pages = sorted(
        (DocsPage(**p) for p in pages_raw),
        key=lambda p: (p.order, p.slug),
    )
    return DocsPagesResponse(mode="prod" if settings.is_prod else "dev", is_admin=admin, pages=pages)


@router.patch("/pages/{slug}/visibility", response_model=VisibilityResponse)
async def set_docs_visibility(
    slug: str,
    body: VisibilityUpdate,
    x_admin_token: Optional[str] = Header(default=None),
):
    """Ubah status publik/privat sebuah halaman dokumentasi (admin only)."""
    if not is_admin(x_admin_token):
        raise HTTPException(status_code=403, detail="Akses ditolak. Token admin diperlukan pada mode prod.")

    with _file_lock:
        pages = _load_pages()
        target = next((p for p in pages if p.get("slug") == slug), None)
        if target is None:
            raise HTTPException(status_code=404, detail=f"Halaman dokumentasi '{slug}' tidak ditemukan.")
        target["is_public"] = bool(body.is_public)
        _save_pages(pages)

    state = "publik" if body.is_public else "privat"
    return VisibilityResponse(slug=slug, is_public=bool(body.is_public), message=f"Halaman '{slug}' kini {state}.")
