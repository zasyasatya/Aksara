from typing import List
from pydantic import BaseModel, Field

# Daftar palet yang dikenal backend — harus selaras dengan frontend/lib/themes.ts
THEME_IDS: List[str] = ["native", "lontar", "segara", "pura", "sawah", "candi"]
DEFAULT_THEME = "native"


class ThemeOut(BaseModel):
    """Palet warna aktif untuk seluruh aplikasi."""

    theme: str
    available: List[str] = THEME_IDS
    default: str = DEFAULT_THEME


class ThemeUpdate(BaseModel):
    theme: str = Field(..., description="ID palet, salah satu dari THEME_IDS")


class ThemeUpdateOut(BaseModel):
    theme: str
    message: str
