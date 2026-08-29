# API Specification - Aksara Platform

Base URL: `http://localhost:8000/api` (dev), `https://api.aksara.bali/api` (prod)

## Authentication

MVP: No auth (public). Future: JWT Bearer.

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
