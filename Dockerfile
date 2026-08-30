# Aksara — satu container, satu origin: FastAPI menyajikan UI statis + API.
# Multi-stage: build UI (Node) → runtime (Python). Deploy: Coolify, Fly, Render, docker compose.
#
#   docker compose up --build     # http://localhost:8000
#
# Variabel lingkungan (set di Coolify / compose):
#   AKSARA_MODE          prod (default di image) | dev
#   AKSARA_ADMIN_TOKEN   wajib diganti di produksi (header X-Admin-Token, panel /admin)
#   AKSARA_GURU_TOKEN    wajib diganti di produksi (header X-Admin-Token, panel /guru)
#
# Persistensi: mount volume di /app/backend/app/data
# (lessons.json, quiz.json, dictionary.json, docs.json, engagement.json)

# ── Stage 1: build UI — Next.js static export ──────────────────────────────
FROM node:22-slim AS ui
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
# Static export membaca katalog pelajaran saat build (app/learn/[id]/layout.tsx:
# join(process.cwd(), "..", "backend", "app", "data", "lessons.json")).
# WORKDIR = /build, jadi letakkan data backend di lokasi yang dicover path relatif itu.
COPY backend/app/data /backend/app/data
ENV BUILD_EXPORT=1 NEXT_TELEMETRY_DISABLED=1
RUN npm run build
# hasil: /build/out  (UI statis; akan disajikan oleh FastAPI → same origin, tanpa CORS)

# ── Stage 2: runtime — FastAPI (API + UI) ─────────────────────────────────
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AKSARA_MODE=prod \
    AKSARA_SERVE_UI=1
WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=ui /build/out ./app/static

# Store konten — persist via volume agar perubahan Panel Guru & engagement
# tidak hilang saat redeploy.
VOLUME /app/backend/app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/api/health', timeout=4)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
