from typing import List, Literal
from pydantic import BaseModel, Field

RoleType = Literal["murid", "guru", "admin", "metodologi"]


class DocsPage(BaseModel):
    """Metdata satu halaman dokumentasi (konten lengkap ada di frontend)."""

    slug: str
    title: str
    subtitle: str
    role: RoleType
    icon: str
    is_public: bool = True
    order: int = 0
    updated_at: str = ""


class DocsPagesResponse(BaseModel):
    """Respons daftar halaman dokumentasi.

    - `mode`: "dev" | "prod" — menentukan perilaku visibilitas di frontend.
    - `is_admin`: True bila sesi login admin aktif (atau mode dev).
    """

    mode: str
    is_admin: bool
    pages: List[DocsPage]


class VisibilityUpdate(BaseModel):
    is_public: bool = Field(..., description="True = go public, False = privat")


class VisibilityResponse(BaseModel):
    slug: str
    is_public: bool
    message: str
