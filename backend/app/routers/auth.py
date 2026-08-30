"""Otentikasi role Guru & Admin (format login: username + password).

- Mode DEV  → login otomatis (praktis untuk development/demo): username &
  password boleh dikosongkan.
- Mode PROD → username + password wajib cocok dengan konfigurasi:
  * Guru  : AKSARA_GURU_USERNAME / AKSARA_GURU_PASSWORD
  * Admin : AKSARA_ADMIN_USERNAME / AKSARA_ADMIN_PASSWORD
  (akun admin juga dapat login sebagai guru)

Login berhasil menerbitkan *session token* opak yang disimpan client dan
dikirim ulang sebagai header ``Authorization: Bearer <token>`` pada endpoint
manage/docs. Sesi dihapus saat logout.
"""

import secrets
from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel

from ..core.config import settings
from ..core import security

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    role: str
    username: str = ""
    password: str = ""


class LoginOut(BaseModel):
    ok: bool
    message: str
    mode: str
    role: Optional[str] = None
    session_token: Optional[str] = None


class AuthInfo(BaseModel):
    mode: str


class SessionOut(BaseModel):
    role: Optional[str] = None
    is_admin: bool = False
    is_guru: bool = False
    mode: str


def _mode() -> str:
    return "prod" if settings.is_prod else "dev"


def _safe_eq(a: str, b: str) -> bool:
    return bool(a) and secrets.compare_digest(a, b)


def _credentials_ok(role: str, username: str, password: str) -> bool:
    """Cocokkan username + password dengan konfigurasi role."""
    if role == "admin":
        return _safe_eq(username, settings.admin_username) and _safe_eq(
            password, settings.admin_password
        )
    # Guru: akun guru, atau akun admin (admin juga dapat mengelola konten).
    if _safe_eq(username, settings.guru_username) and _safe_eq(password, settings.guru_password):
        return True
    return _safe_eq(username, settings.admin_username) and _safe_eq(password, settings.admin_password)


@router.get("/info", response_model=AuthInfo)
def auth_info():
    """Info mode aplikasi (dev/prod) untuk menampilkan petunjuk login."""
    return {"mode": _mode()}


@router.post("/login", response_model=LoginOut)
def auth_login(body: LoginIn):
    """Login dengan username + password; mengembalikan session token."""
    role = (body.role or "").strip().lower()
    if role not in ("guru", "admin"):
        return LoginOut(ok=False, message="Role tidak dikenal.", mode=_mode())

    if not settings.is_prod:
        token = security.create_session(role)
        return LoginOut(
            ok=True,
            message="Mode dev — login otomatis, username/password tidak diperlukan.",
            mode="dev",
            role=role,
            session_token=token,
        )

    username = (body.username or "").strip()
    password = (body.password or "").strip()
    if not username or not password:
        return LoginOut(
            ok=False, message="Username dan password wajib diisi pada mode prod.", mode="prod"
        )

    if _credentials_ok(role, username, password):
        token = security.create_session(role)
        label = "Admin" if role == "admin" else "Guru"
        return LoginOut(
            ok=True,
            message=f"Login berhasil. Selamat datang, {label}!",
            mode="prod",
            role=role,
            session_token=token,
        )

    hint = "Username atau password salah."
    if role == "guru":
        hint = "Username atau password guru salah (akun admin juga dapat diterima)."
    return LoginOut(ok=False, message=hint, mode="prod")


@router.post("/logout", response_model=LoginOut)
def auth_logout(authorization: Optional[str] = Header(default=None)):
    """Hapus sesi aktif."""
    security.destroy_session(security.bearer_token(authorization))
    return LoginOut(ok=True, message="Anda telah keluar.", mode=_mode())


@router.get("/session", response_model=SessionOut)
def auth_session(authorization: Optional[str] = Header(default=None)):
    """Periksa sesi aktif dari header Authorization."""
    role = security.get_session_role(security.bearer_token(authorization))
    return SessionOut(
        role=role,
        is_admin=(role == "admin"),
        is_guru=(role in ("admin", "guru")),
        mode=_mode(),
    )
