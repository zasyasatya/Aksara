"""Manajemen sesi login Guru & Admin.

Setelah login berhasil (username + password benar), server menerbitkan token
sesi opak yang disimpan di client dan dikirim ulang sebagai header
``Authorization: Bearer <token>`` pada endpoint manage/docs. Sesi tersimpan
di memori dengan masa berlaku terbatas — cukup untuk MVP satu proses; bila
butuh multi-proses/restart, ganti dengan penyimpanan eksternal (Redis/DB).
"""

from __future__ import annotations

import secrets
import threading
import time
from typing import Optional

# TTL sesi (detik). 12 jam cukup untuk satu hari kerja.
SESSION_TTL_SECONDS = 12 * 3600

_sessions: dict[str, dict] = {}
_lock = threading.Lock()


def create_session(role: str) -> str:
    """Terbitkan token sesi untuk sebuah role ('admin' atau 'guru')."""
    token = secrets.token_urlsafe(32)
    with _lock:
        _sessions[token] = {
            "role": role,
            "expires_at": time.time() + SESSION_TTL_SECONDS,
        }
        _prune_locked()
    return token


def get_session_role(token: Optional[str]) -> Optional[str]:
    """Kembalikan role sesi bila token valid & belum kedaluwarsa, else None."""
    if not token:
        return None
    with _lock:
        session = _sessions.get(token)
        if session is None:
            return None
        if session["expires_at"] < time.time():
            _sessions.pop(token, None)
            return None
        return session["role"]


def destroy_session(token: Optional[str]) -> None:
    """Hapus sesi (logout)."""
    if not token:
        return
    with _lock:
        _sessions.pop(token, None)


def _prune_locked() -> None:
    """Buang sesi kedaluwarsa (dipanggil sambil memegang _lock)."""
    now = time.time()
    expired = [t for t, s in _sessions.items() if s["expires_at"] < now]
    for t in expired:
        _sessions.pop(t, None)


def bearer_token(authorization: Optional[str]) -> Optional[str]:
    """Ekstrak token dari header ``Authorization: Bearer <token>``."""
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip() or None
    return None
