"""Otentikasi role Guru & Admin.

- Mode DEV  → akses otomatis (praktis untuk development/demo).
- Mode PROD → token wajib:
  * Guru  : AKSARA_GURU_TOKEN (token admin AKSARA_ADMIN_TOKEN juga diterima)
  * Admin : AKSARA_ADMIN_TOKEN
Token disimpan di sisi client (localStorage) dan dikirim ulang sebagai
header X-Admin-Token pada endpoint manage/docs.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from ..core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    role: str
    token: str = ""


class LoginOut(BaseModel):
    ok: bool
    message: str
    mode: str


class AuthInfo(BaseModel):
    mode: str


def _mode() -> str:
    return "prod" if settings.is_prod else "dev"


@router.get("/info", response_model=AuthInfo)
def auth_info():
    """Info mode aplikasi (dev/prod) untuk menampilkan petunjuk login."""
    return {"mode": _mode()}


@router.post("/login", response_model=LoginOut)
def auth_login(body: LoginIn):
    """Validasi token sesuai role; mengembalikan pesan hasil."""
    role = (body.role or "").strip().lower()
    if role not in ("guru", "admin"):
        return LoginOut(ok=False, message="Role tidak dikenal.", mode=_mode())

    if not settings.is_prod:
        return LoginOut(
            ok=True,
            message="Mode dev — akses otomatis, token tidak diperlukan.",
            mode="dev",
        )

    token = (body.token or "").strip()
    if not token:
        return LoginOut(ok=False, message="Token wajib diisi pada mode prod.", mode="prod")

    if role == "admin":
        ok = bool(settings.admin_token) and token == settings.admin_token
        if ok:
            return LoginOut(ok=True, message="Login berhasil. Selamat datang, Admin!", mode="prod")
        return LoginOut(ok=False, message="Token admin salah.", mode="prod")

    ok = token == settings.guru_token or (
        bool(settings.admin_token) and token == settings.admin_token
    )
    if ok:
        return LoginOut(ok=True, message="Login berhasil. Selamat datang, Guru!", mode="prod")
    return LoginOut(
        ok=False,
        message="Token guru salah (token admin juga dapat diterima).",
        mode="prod",
    )
