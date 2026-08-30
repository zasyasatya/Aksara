import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .routers import health, translate, classify, lessons, quiz, docs, manage

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=settings.description + "\n\nAdvanced transliteration handling gantungan, gempelan, pangangge, tumpuk telu rules.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP allow all, in prod restrict to settings.cors_origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes live under /api. Keeping the public UI and API same-origin lets
# the no-Docker launcher serve a prebuilt interface from this FastAPI process.
app.include_router(health.router)
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(translate.router, prefix=settings.api_prefix)
app.include_router(classify.router, prefix=settings.api_prefix)
app.include_router(lessons.router, prefix=settings.api_prefix)
app.include_router(quiz.router, prefix=settings.api_prefix)
app.include_router(docs.router, prefix=settings.api_prefix)
app.include_router(manage.router, prefix=settings.api_prefix)

@app.get("/api")
async def api_root():
    return {
        "message": "Aksara API v1",
        "version": settings.version,
        "mode": "prod" if settings.is_prod else "dev",
        "docs": "/docs",
        "endpoints": [
            "/api/health",
            "/api/translate",
            "/api/classify",
            "/api/lessons",
            "/api/quiz",
            "/api/docs/pages",
            "/api/manage/lessons",
            "/api/manage/quizzes",
            "/api/manage/dictionary",
        ]
    }


STATIC_DIR = Path(__file__).resolve().parent / "static"


def static_ui_available() -> bool:
    """Whether a launcher-built UI should be exposed by this process."""
    return (
        os.environ.get("AKSARA_SERVE_UI", "1") != "0"
        and (STATIC_DIR / "index.html").is_file()
    )


@app.get("/", include_in_schema=False)
async def root():
    """Serve the exported UI when available; otherwise retain the API landing page."""
    if static_ui_available():
        return FileResponse(STATIC_DIR / "index.html")
    return await health.root()


# Mount last so documented API endpoints and /docs win over static paths.
# The launcher builds the directory before starting Uvicorn, therefore this is
# evaluated once per server process and does not expose a partial build.
if static_ui_available():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="web")
