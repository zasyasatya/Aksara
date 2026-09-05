"""Pengaturan tampilan aplikasi (palet warna) yang dikelola Admin.

- GET /api/settings/theme  → publik: palet aktif (dibaca setiap pengunjung).
- PUT /api/settings/theme  → admin: ganti palet (tersimpan di data/settings.json).

Palet "native" (Saffron Nusantara) adalah default dan selalu tersedia.
"""

from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from ..core.config import settings
from ..core import security
from ..services import data_store
from ..schemas.settings import DEFAULT_THEME, THEME_IDS, ThemeOut, ThemeUpdate, ThemeUpdateOut

router = APIRouter(prefix="/settings", tags=["settings"])


def _is_admin(authorization: Optional[str]) -> bool:
    if not settings.is_prod:
        return True
    return security.get_session_role(security.bearer_token(authorization)) == "admin"


@router.get("/theme", response_model=ThemeOut)
async def get_theme():
    data = data_store.get_app_settings()
    theme = data.get("theme", DEFAULT_THEME)
    if theme not in THEME_IDS:
        theme = DEFAULT_THEME
    return ThemeOut(theme=theme)


@router.put("/theme", response_model=ThemeUpdateOut)
async def set_theme(body: ThemeUpdate, authorization: Optional[str] = Header(default=None)):
    if not _is_admin(authorization):
        raise HTTPException(status_code=403, detail="Akses ditolak. Login sebagai Admin diperlukan pada mode prod.")
    if body.theme not in THEME_IDS:
        raise HTTPException(status_code=422, detail=f"Palet '{body.theme}' tidak dikenal. Pilihan: {', '.join(THEME_IDS)}")
    data = data_store.get_app_settings()
    data["theme"] = body.theme
    data_store.save_app_settings(data)
    label = "default (native)" if body.theme == DEFAULT_THEME else body.theme
    return ThemeUpdateOut(theme=body.theme, message=f"Palet warna aplikasi kini: {label}.")
