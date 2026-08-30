from fastapi import APIRouter
from datetime import datetime
from ..core.config import settings

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.version,
        "service": settings.app_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "features": {
            "transliteration": True,
            "classification": True,
            "quiz": True,
            "lessons": True,
            "gantungan_analysis": True
        }
    }

# NOTE: bare "/" is intentionally NOT registered here. main.py owns "/" so it
# can serve the exported UI when available and fall back to this payload.
async def root():
    return {
        "message": "Aksara API - Platform Belajar Aksara Bali",
        "version": settings.version,
        "docs": "/docs",
        "health": "/api/health",
        "tagline": "Melestarikan Warisan, Menulis Masa Depan - Ngajegang Warisan, Nyurat Masa Depan",
        "endpoints": {
            "translate": "/api/translate",
            "classify": "/api/classify",
            "lessons": "/api/lessons",
            "quiz": "/api/quiz"
        }
    }
