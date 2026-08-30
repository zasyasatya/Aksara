from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Routers
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
