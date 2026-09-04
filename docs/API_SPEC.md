# API Specification - Aksara Platform

Base URL: `http://localhost:8000/api` (dev), `https://api.aksara.bali/api` (prod)

## Authentication

Endpoint publik bebas akses. Panel Guru & Admin memakai **login username + password**
yang menerbitkan session token opak, dikirim ulang sebagai header
`Authorization: Bearer <session_token>`.

- **POST /auth/login** — body `{ "role": "admin"|"guru", "username", "password" }`.
  Mode `dev` login otomatis; mode `prod` mencocokkan username/password dengan env
  (`AKSARA_ADMIN_USERNAME`/`AKSARA_ADMIN_PASSWORD`, `AKSARA_GURU_USERNAME`/`AKSARA_GURU_PASSWORD`).
  Response: `{ "ok", "message", "mode", "role", "session_token" }`.
- **GET /auth/info** — `{ "mode": "dev"|"prod" }`.
- **GET /auth/session** — memeriksa sesi aktif → `{ "role", "is_admin", "is_guru", "mode" }`.
- **POST /auth/logout** — menghapus sesi aktif.

## Endpoints

### Health
**GET /health**
- Response 200:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "service": "aksara-backend",
  "timestamp": "2026-08-29T00:00:00Z"
}
```

### Translate

**POST /translate**
Translate between Latin and Balinese script.

Request:
```json
{
  "text": "bali",
  "direction": "latin-to-bali", // or "bali-to-latin"
  "options": {
    "use_dictionary": true,
    "strict": false
  }
}
```

Response 200:
```json
{
  "original": "bali",
  "result": "ᬩᬮᬶ",
  "direction": "latin-to-bali",
  "breakdown": [
    {
      "latin": "ba",
      "bali": "ᬩ",
      "type": "wresastra",
      "description": "Ba"
    },
    {
      "latin": "li",
      "bali": "ᬮᬶ",
      "type": "wresastra+pangangge",
      "base": "ᬮ",
      "pangangge": "ᬶ",
      "pangangge_name": "ulu",
      "description": "La + Ulu = Li"
    }
  ],
  "confidence": 0.98,
  "warnings": []
}
```

Error 400: text too long (>5000), invalid direction
Error 422: validation error

**POST /translate/batch**
Batch translate (max 50 items)

Request:
```json
{
  "items": [
    {"text": "bali", "direction": "latin-to-bali"},
    {"text": "ᬩᬮᬶ", "direction": "bali-to-latin"}
  ]
}
```

### Classify

**POST /classify**
Classify a Balinese character or string.

Request:
```json
{
  "text": "ᬩ"
}
```

Response:
```json
{
  "input": "ᬩ",
  "classifications": [
    {
      "char": "ᬩ",
      "unicode": "U+1B29",
      "latin": "ba",
      "name": "Ba",
      "type": "wresastra",
      "category": "wianjana",
      "subtype": "ostia",
      "description": "Aksara Wresastra Ba, warga Ostia (bibir)",
      "gantungan_form": "◌᭄ᬩ",
      "examples": ["bali - ᬩᬮᬶ", "bapa - ᬩᬧ"],
      "is_gantungan": false,
      "is_pangangge": false
    }
  ],
  "overall_type": "wresastra",
  "syllable_count": 1
}
```

**GET /classify/types**
List all classification types.

Response:
```json
{
  "types": [
    {"id": "wresastra", "name": "Wresastra", "count": 18, "description": "..."},
    {"id": "swalalita", "name": "Swalalita", "count": 33},
    {"id": "suara", "name": "Aksara Suara", "count": 14},
    {"id": "pangangge_suara", "name": "Pangangge Suara", "count": 11},
    {"id": "pangangge_tengenan", "name": "Pangangge Tengenan", "count": 4},
    {"id": "pangangge_aksara", "name": "Pangangge Aksara", "count": 4}
  ]
}
```

### Lessons

**GET /lessons**
Query params: level, search, limit, offset

Response:
```json
{
  "lessons": [
    {
      "id": "wresastra-01",
      "title": "Ha Na Ca Ra Ka",
      "description": "5 aksara pertama dalam Hanacaraka",
      "level": 1,
      "order": 1,
      "aksara": ["ᬳ", "ᬦ", "ᬘ", "ᬭ", "ᬓ"],
      "estimated_minutes": 10,
      "xp_reward": 50,
      "is_locked": false,
      "thumbnail": "/illustrations/ha-na-ca.png"
    }
  ],
  "total": 12,
  "level_info": {
    "1": {"name": "Pemula", "description": "Wresastra dasar"}
  }
}
```

**GET /lessons/{id}**

Response:
```json
{
  "id": "wresastra-01",
  "title": "Ha Na Ca Ra Ka",
  "content": {
    "intro": "Ha Na Ca Ra Ka adalah...",
    "aksara_details": [
      {
        "char": "ᬳ",
        "latin": "ha",
        "name": "Ha",
        "how_to_write": ["step1", "step2"],
        "pronunciation": "ha",
        "examples": [
          {"bali": "ᬳᬦ", "latin": "hana", "meaning": "ada"},
          {"bali": "ᬳᬸᬚᬦ᭄", "latin": "hujan", "meaning": "hujan (dibaca ujan)"}
        ],
        "common_mistakes": ["Ha sering tidak dibaca di awal"],
        "audio_url": "/audio/ha.mp3"
      }
    ],
    "pangangge_in_this_lesson": [],
    "rules": ["..."]
  },
  "quiz_ids": ["quiz-wres-01-1", "quiz-wres-01-2"],
  "next_lesson": "wresastra-02"
}
```

### Quiz

**GET /quiz**
Query: lesson_id, type, difficulty, limit (default 10)

Response:
```json
{
  "quizzes": [
    {
      "id": "quiz-wres-01-1",
      "type": "multiple_choice",
      "difficulty": "easy",
      "question": {
        "text": "Pilih aksara yang berbunyi 'Ha'",
        "latin": "ha",
        "bali": null,
        "image": null
      },
      "options": [
        {"id": "a", "bali": "ᬳ", "latin": "ha"},
        {"id": "b", "bali": "ᬦ", "latin": "na"},
        {"id": "c", "bali": "ᬘ", "latin": "ca"},
        {"id": "d", "bali": "ᬭ", "latin": "ra"}
      ],
      "correct_answer": "a",
      "explanation": "ᬳ adalah Ha...",
      "xp": 10,
      "lesson_id": "wresastra-01"
    }
  ]
}
```

Quiz Types:
- multiple_choice
- true_false
- gantungan_choice
- arrangement
- translate

**POST /quiz/check**
Validate answer.

Request:
```json
{
  "quiz_id": "quiz-wres-01-1",
  "answer": "a",
  "user_input": null,
  "time_spent_seconds": 5
}
```

For arrangement type:
```json
{
  "quiz_id": "quiz-arr-01",
  "answer": ["ᬩ", "ᬮ", "ᬶ"],
  "user_input": "ᬩᬮᬶ"
}
```

Response:
```json
{
  "quiz_id": "quiz-wres-01-1",
  "correct": true,
  "correct_answer": "a",
  "user_answer": "a",
  "explanation": "Benar! ᬳ adalah Ha...",
  "xp_earned": 10,
  "feedback": {
    "type": "success",
    "message": "Mantap! Kamu benar",
    "details": "Ha termasuk Wresastra..."
  },
  "next_quiz": "quiz-wres-01-2"
}
```

For incorrect:
```json
{
  "correct": false,
  "explanation": "Hampir benar! Seharusnya pakai gantungan...",
  "feedback": {
    "type": "error",
    "message": "Ups, kurang tepat",
    "details": "Kamu pakai adeg-adeg, seharusnya gantungan karena...",
    "correct_bali": "ᬓᬭᬗ᭄ᬓᬸᬂ",
    "correct_latin": "karangkung"
  }
}
```

**POST /quiz/validate-pair**
Custom validation for "apakah aksara yang ditulis sudah benar sesuai soal"

Request:
```json
{
  "question_latin": "bali",
  "question_bali": "ᬩᬮᬶ",
  "user_bali": "ᬩᬮᬶ",
  "mode": "exact" // or "tolerant"
}
```

Response:
```json
{
  "is_correct": true,
  "similarity": 1.0,
  "differences": [],
  "suggestions": []
}
```

If incorrect:
```json
{
  "is_correct": false,
  "similarity": 0.7,
  "differences": [
    {
      "position": 1,
      "expected": "ᬮᬶ",
      "got": "ᬮ",
      "reason": "Kehilangan ulu (pangangge suara i)"
    }
  ],
  "suggestions": ["Tambahkan ulu untuk bunyi i"]
}
```

### Gantungan

**GET /gantungan/rules**
Get all gantungan rules.

Response:
```json
{
  "rules": [
    {
      "id": "tumpuk-telu",
      "name": "Tumpuk Telu",
      "description": "Tidak boleh ada 2 gantungan pada 1 aksara dasar",
      "example_wrong": "ka + gantungan ra + gantungan ya (forbidden)",
      "example_correct": "ka + gantungan ra, ya di suku kata baru"
    },
    {
      "id": "pepet-cakra",
      "name": "Pepet + Cakra Forbidden",
      "description": "Kombinasi pepet dan cakra tidak diperbolehkan"
    }
  ]
}
```

**POST /gantungan/analyze**
Analyze word for gantungan usage.

Request:
```json
{
  "text": "dharma",
  "direction": "latin-to-bali"
}
```

Response:
```json
{
  "original": "dharma",
  "bali": "ᬤᬃᬫ",
  "clusters": [
    {
      "position": 1,
      "latin": "rma",
      "bali": "ᬃᬫ",
      "type": "surang+gantungan",
      "explanation": "Ra tengenan surang + Ma gantungan"
    }
  ],
  "has_gantungan": true,
  "gantungan_count": 1
}
```

### ML — Retraining classifier aksara (Panel Admin)

Prefix `/ml`. Semua endpoint **admin-only** (Bearer token admin; mode `dev`
otomatis admin) kecuali `GET /ml/status`, `POST /ml/predict`, dan
`GET /ml/dataset/samples/{id}/image`. Dokumentasi lengkap: `docs/ML_RETRAINING.md`;
panduan langkah demi langkah dengan screenshot: `docs/PANDUAN_RETRAINING.md`.

**GET /ml/status** — ringkasan untuk dashboard admin.
```json
{
  "mode": "dev",
  "is_admin": true,
  "production_model": { "id": "cnn-20260904-1422-ab12", "name": "CNN v1", "arch": "cnn",
                        "metrics": { "accuracy": 0.9815, "macro_precision": 0.9838,
                                     "macro_recall": 0.9815, "macro_f1": 0.9816 } },
  "dataset": { "total": 1080, "labeled": 1080, "unlabeled": 0, "review": 0,
               "per_split": { "train": 756, "val": 162, "test": 162 }, "n_classes": 18, "version": 3 },
  "models_total": 4,
  "active_job": null,
  "font_available": true
}
```

**Dataset & labeling**

| Method | Path | Body / query | Keterangan |
| --- | --- | --- | --- |
| GET | `/ml/architectures` | — | daftar arsitektur + spesifikasi hyperparameter (dipakai form UI) |
| GET / PUT | `/ml/classes` | `{ "labels": ["ha", …] }` | kelas tersedia & aktif / ganti kelas aktif |
| GET | `/ml/dataset/stats` | — | jumlah per label × split, kelas kosong, versi dataset |
| GET | `/ml/dataset/samples` | `label, split, source, status, q, limit (≤500), offset` | daftar sampel (paging) |
| POST | `/ml/dataset/samples` | `{ "image": "<data URL>", "label"?: "ha", "source": "canvas\|upload\|import", "split"?, "note"? }` | tambah 1 sampel (tanpa label → antrean labeling) |
| POST | `/ml/dataset/samples/bulk` | `{ "items": [SampleIn, …] }` | tambah banyak sampel |
| GET / PATCH / DELETE | `/ml/dataset/samples/{id}` | PATCH: `{ "label"?, "clear_label"?, "split"?, "status"?, "note"? }` | detail / labeling / hapus |
| GET | `/ml/dataset/samples/{id}/image` | — | PNG 64×64 sampel (publik, untuk thumbnail) |
| POST | `/ml/dataset/bulk-label` | `{ "ids": [...], "label"?, "split"?, "status"? }` | aksi massal |
| POST | `/ml/dataset/bulk-delete` | `{ "ids": [...] }` | hapus massal |
| GET | `/ml/dataset/bundled` | — | paket dataset yang ikut repo (`dataset/*/manifest.json`): nama, versi, jumlah gambar, kelas, split, lisensi |
| POST | `/ml/dataset/import-bundled` | `{ "name": "aksara-bali-handwriting-v1", "activate_classes": true, "replace_existing": true, "keep_split": true }` | impor paket ke dataset (idempoten; 404 bila nama tidak ada) → `{ added, removed, skipped, classes, seconds, stats }` |
| POST | `/ml/dataset/generate-synthetic` | `{ "per_class": 60, "seed": 20260904, "strength": 1.0 }` | bangkitkan sampel sintetis dari font Noto Sans Balinese |
| POST | `/ml/dataset/rebalance` | `{ "val_ratio": 0.15, "test_ratio": 0.15, "seed": 0 }` | acak ulang split stratified |
| POST | `/ml/dataset/clear` | query `source?` (`synthetic\|upload\|canvas\|import`), `label?` | kosongkan dataset (opsional per sumber/label) |

**Training & model**

| Method | Path | Body | Keterangan |
| --- | --- | --- | --- |
| POST | `/ml/train` → **202** | `{ "arch": "cnn", "hyperparams": { "epochs": 15 }, "name": "CNN v1", "notes": "", "auto_promote": false }` | mulai job retraining (400 bila dataset belum siap / job lain berjalan) |
| GET | `/ml/train/jobs` | — | `{ "jobs": [...], "active": Job\|null }` |
| GET | `/ml/train/jobs/{id}` | — | status job: `status`, `progress`, `epoch`, `history[]`, `message`, `model_id`, `metrics` |
| DELETE | `/ml/train/jobs/{id}` | — | batalkan job |
| GET | `/ml/models` | — | registry `{ "models": [...], "production_model_id" }` |
| GET | `/ml/models/{id}` | — | `{ "model": entry, "report": laporan evaluasi lengkap }` |
| PATCH / DELETE | `/ml/models/{id}` | `{ "name"?, "notes"? }` | ubah / hapus (model produksi tidak bisa dihapus) |
| PUT | `/ml/models/production` | `{ "model_id": "…" \| null }` | pilih / nonaktifkan model produksi |

Laporan evaluasi (`report`) berisi `accuracy`, `macro_precision`, `macro_recall`,
`macro_f1`, `weighted_*`, `top3_accuracy`, `log_loss`, `mean_confidence`,
`confident_rate`, `confident_accuracy`, `train_accuracy`, `per_class[]`
(precision/recall/f1/support/tp/fp/fn), `confusion_matrix`, `top_confusions[]`,
`history[]` (loss & akurasi per epoch), `misclassified[]`.

**Prediksi**

**POST /ml/predict** (publik)
```json
{ "image": "data:image/png;base64,…", "model_id": null, "top_k": 5 }
```
Response 200 (409 bila belum ada model produksi, 422 bila gambar tidak berisi tinta):
```json
{
  "model_id": "cnn-20260904-1422-ab12", "model_name": "CNN v1", "arch": "cnn", "is_production": true,
  "label": "ha", "glyph": "ᬳ", "name": "Ha", "latin": "ha",
  "confidence": 0.93, "margin": 0.88, "confident": true,
  "top": [ { "label": "ha", "glyph": "ᬳ", "probability": 0.93 }, { "label": "nga", "glyph": "ᬗ", "probability": 0.05 } ],
  "preview": "data:image/png;base64,…"
}
```

**POST /ml/predict/compare** (admin) — `{ "image", "model_ids": ["…", "…"] }` →
`{ "results": [prediksi per model] }`.

### Dictionary (Future)

**GET /dictionary?search=bali**

## Error Format

All errors follow:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Text too long",
    "details": {"max": 5000, "got": 6000},
    "timestamp": "2026-08-29T00:00:00Z"
  }
}
```

Codes:
- VALIDATION_ERROR (400, 422)
- NOT_FOUND (404)
- RATE_LIMITED (429)
- INTERNAL_ERROR (500)

## Rate Limiting

- 60 requests/min per IP for translate
- 100 requests/min for lessons/quiz
- Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

## CORS

Allowed origins: 
- http://localhost:3000
- https://aksara.bali
- https://*.vercel.app

## OpenAPI Docs

Available at `/docs` (Swagger) and `/redoc`
