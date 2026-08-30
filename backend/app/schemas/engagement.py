"""Skema engagement: counter & pendaftaran sekolah mitra."""

from typing import List, Optional

from pydantic import BaseModel, Field


class EngagementStats(BaseModel):
    visits: int = 0
    twibbons: int = 0
    schools: List[dict] = []


class MessageResponse(BaseModel):
    message: str


class SchoolIn(BaseModel):
    school: str = Field(..., min_length=2, max_length=120, description="Nama sekolah/sanggar/pasraman")
    region: str = Field("", max_length=80, description="Kabupaten/kota")
    students: Optional[int] = Field(None, ge=1, le=100000, description="Perkiraan jumlah siswa")
    contact: str = Field(..., min_length=3, max_length=160, description="Email / WhatsApp yang bisa dihubungi")
    note: Optional[str] = Field(None, max_length=500)
