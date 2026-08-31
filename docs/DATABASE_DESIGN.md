# Database Design - Aksara Platform

## Overview

MVP uses JSON files for simplicity and easy versioning. Designed to migrate to PostgreSQL + SQLAlchemy when user system implemented.

## JSON Files Structure

### aksara_master.json

Master data for all Balinese characters.

```json
{
  "wresastra": [
    {
      "id": "ha",
      "bali": "ᬳ",
      "latin": "ha",
      "name": "Ha",
      "unicode": "U+1B33",
      "unicode_char": "ᬳ",
      "type": "wresastra",
      "warga": "kanthya",
      "category": "wianjana",
      "description": "Aksara Wresastra Ha, sering tidak dibaca di awal kata seperti hujan dibaca ujan",
      "gantungan_form": "᭄ᬳ",
      "gantungan_unicode": "U+1B44 U+1B33",
      "is_gempelan": false,
      "examples": [
        {"bali": "ᬳᬦ", "latin": "hana", "meaning": "ada"},
        {"bali": "ᬳᬸᬚᬦ᭄", "latin": "hujan", "meaning": "hujan"}
      ],
      "stroke_order": ["step1", "step2"],
      "audio": "/audio/ha.mp3",
      "level": 1,
      "order": 1
    }
    // ... 17 more
  ],
  "swalalita": [
    {
      "id": "ka_mahaprana",
      "bali": "ᬔ",
      "latin": "kha",
      "name": "Ka Mahaprana",
      "unicode": "U+1B14",
      "type": "swalalita",
      "warga": "kanthya",
      "description": "Kha untuk kata serapan Sanskerta",
      "gantungan_form": "᭄ᬔ",
      "level": 5
    }
    // ... total 33 including wresastra? Actually Swalalita includes 33 distinct, but we list extra beyond 18
  ],
  "suara": [
    {
      "id": "akara",
      "bali": "ᬅ",
      "latin": "a",
      "name": "Akara",
      "unicode": "U+1B05",
      "type": "suara",
      "subtype": "hrasva",
      "description": "A pendek, untuk vokal di awal kata",
      "examples": [{"bali": "ᬅᬓ᭄ᬱᬭ", "latin": "aksara", "meaning": "huruf"}]
    }
    // ... 14 suara
  ],
  "pangangge_suara": [
    {
      "id": "ulu",
      "bali": "ᬶ",
      "mark": "◌ᬶ",
      "unicode": "U+1B36",
      "name": "Ulu",
      "type": "pangangge_suara",
      "latin_effect": "i",
      "position": "above",
      "description": "Memberi vokal i",
      "example": {"base": "ᬓ", "with": "ᬓᬶ", "latin": "ki"},
      "forbidden_combinations": []
    },
    {
      "id": "suku",
      "bali": "ᬸ",
      "mark": "◌ᬸ",
      "unicode": "U+1B38",
      "name": "Suku",
      "type": "pangangge_suara",
      "latin_effect": "u",
      "position": "below",
      "description": "Memberi vokal u"
    },
    {
      "id": "taleng",
      "bali": "ᬾ",
      "mark": "◌ᬾ",
      "unicode": "U+1B3E",
      "name": "Taleng / Taling",
      "type": "pangangge_suara",
      "latin_effect": "e / é",
      "position": "front",
      "description": "Memberi vokal e"
    },
    {
      "id": "pepet",
      "bali": "ᭂ",
      "mark": "◌ᭂ",
      "unicode": "U+1B42",
      "name": "Pepet",
      "type": "pangangge_suara",
      "latin_effect": "ě / e pepet",
      "position": "above",
      "description": "Vokal pepet seperti pada 'bleganjur'",
      "forbidden_combinations": ["cakra"]
    }
    // ... total 11-13
  ],
  "pangangge_tengenan": [
    {
      "id": "bisah",
      "bali": "ᬄ",
      "mark": "◌ᬄ",
      "unicode": "U+1B04",
      "name": "Bisah",
      "type": "pangangge_tengenan",
      "latin_effect": "h",
      "position": "after",
      "description": "Akhiran h, seperti visarga",
      "example": {"base": "ᬩ", "with": "ᬩᬄ", "latin": "bah"}
    },
    {
      "id": "surang",
      "bali": "ᬃ",
      "mark": "◌ᬃ",
      "unicode": "U+1B03",
      "name": "Surang",
      "type": "pangangge_tengenan",
      "latin_effect": "r",
      "description": "Akhiran r"
    },
    {
      "id": "cecek",
      "bali": "ᬂ",
      "mark": "◌ᬂ",
      "unicode": "U+1B02",
      "name": "Cecek",
      "type": "pangangge_tengenan",
      "latin_effect": "ng",
      "description": "Akhiran ng, pengganti nga + adeg-adeg"
    },
    {
      "id": "adeg_adeg",
      "bali": "᭄",
      "mark": "◌᭄",
      "unicode": "U+1B44",
      "name": "Adeg-adeg",
      "type": "pangangge_tengenan",
      "latin_effect": "(kill vowel)",
      "description": "Mematikan vokal inheren /a/, seperti virama",
      "example": {"word": "ᬩᬮᬶ", "with_adeg": "ᬩᬮ᭄"}
    }
  ],
  "pangangge_aksara": [
    {
      "id": "cakra",
      "bali": "᭄ᬭ",
      "mark": "◌᭄ᬭ",
      "unicode": "U+1B44 U+1B2D",
      "name": "Cakra / Guwung",
      "type": "pangangge_aksara",
      "latin_effect": "ra (cluster)",
      "description": "Gantungan Ra, untuk cluster kra, bra, etc",
      "example": {"base": "ᬓ", "with": "ᬓ᭄ᬭ", "latin": "kra"}
    },
    {
      "id": "nania",
      "bali": "᭄ᬬ",
      "mark": "◌᭄ᬬ",
      "name": "Nania",
      "latin_effect": "ya",
      "description": "Gantungan Ya"
    },
    {
      "id": "suku_kembung",
      "bali": "᭄ᬯ",
      "mark": "◌᭄ᬯ",
      "name": "Suku Kembung",
      "latin_effect": "wa",
      "description": "Gantungan Wa"
    },
    {
      "id": "gantungan_la",
      "bali": "᭄ᬮ",
      "mark": "◌᭄ᬮ",
      "name": "Gantungan La",
      "latin_effect": "la",
      "description": "Gantungan La, bisa kombinasi dengan pepet: bleganjur ᬩᬼᬕᬜ᭄ᬚᬸᬃ"
    }
  ],
  "angka": [
    {"bali": "᭐", "latin": "0", "unicode": "U+1B50"},
    {"bali": "᭑", "latin": "1", "unicode": "U+1B51"}
    // ... 0-9
  ],
  "tanda_baca": [
    {"bali": "᭞", "name": "Carik", "latin": ",", "description": "Koma"},
    {"bali": "᭟", "name": "Carik Pareren", "latin": ".", "description": "Titik"}
  ]
}
```

### lessons.json

```json
[
  {
    "id": "wresastra-01",
    "title": "Ha Na Ca Ra Ka",
    "slug": "ha-na-ca-ra-ka",
    "description": "Lima aksara pertama dalam urutan Hanacaraka, mengisahkan dua abdi",
    "level": 1,
    "order": 1,
    "category": "wresastra",
    "aksara_ids": ["ha", "na", "ca", "ra", "ka"],
    "pangangge_ids": [],
    "content": {
      "story": "Ha Na Ca Ra Ka artinya ada dua abdi...",
      "learning_points": ["Mengenal bentuk dasar", "Cara baca Ha yang kadang hilang"],
      "rules": []
    },
    "estimated_minutes": 10,
    "xp_reward": 50,
    "prerequisites": [],
    "quiz_ids": ["quiz-wres-01-1", "quiz-wres-01-2", "quiz-wres-01-3"],
    "thumbnail": "/illustrations/lesson-01.png",
    "is_published": true
  },
  {
    "id": "pangangge-suara-01",
    "title": "Ulu & Suku - Vokal I dan U",
    "level": 2,
    "order": 6,
    "aksara_ids": ["ha", "na"],
    "pangangge_ids": ["ulu", "suku"],
    "content": {...}
  }
  // ... 12 lessons
]
```

### quiz.json

```json
[
  {
    "id": "quiz-wres-01-1",
    "lesson_id": "wresastra-01",
    "type": "multiple_choice",
    "difficulty": "easy",
    "question": {
      "text": "Pilih aksara yang berbunyi 'Ha'",
      "text_bali": null,
      "latin": "ha"
    },
    "options": [
      {"id": "a", "bali": "ᬳ", "latin": "ha", "is_correct": true},
      {"id": "b", "bali": "ᬦ", "latin": "na"},
      {"id": "c", "bali": "ᬘ", "latin": "ca"},
      {"id": "d", "bali": "ᬭ", "latin": "ra"}
    ],
    "correct_answer": "a",
    "explanation": "ᬳ adalah Ha, aksara pertama dalam Hanacaraka...",
    "explanation_bali": "ᬳ ᬳᬶᬂᬕᬶᬄ ᬳ...",
    "xp": 10,
    "tags": ["wresastra", "ha"]
  },
  {
    "id": "quiz-true-false-01",
    "type": "true_false",
    "difficulty": "medium",
    "question": {
      "text": "Apakah ᬩᬮᬶ benar untuk 'bali'?",
      "latin": "bali",
      "bali": "ᬩᬮᬶ",
      "pair": {"latin": "bali", "bali": "ᬩᬮᬶ"}
    },
    "options": [
      {"id": "true", "label": "Benar", "is_correct": true},
      {"id": "false", "label": "Salah"}
    ],
    "correct_answer": "true",
    "explanation": "Benar! Ba + La + Ulu = Bali",
    "xp": 15
  },
  {
    "id": "quiz-gantungan-01",
    "type": "gantungan_choice",
    "difficulty": "hard",
    "question": {
      "text": "Pilih penulisan yang benar untuk 'dharma'",
      "latin": "dharma",
      "hint": "Perhatikan penggunaan surang dan gantungan"
    },
    "options": [
      {"id": "a", "bali": "ᬤᬃᬫ", "is_correct": true, "explanation": "Da + Surang + Ma gantungan"},
      {"id": "b", "bali": "ᬤᬭ᭄ᬫ", "is_correct": false, "explanation": "Salah, seharusnya surang"},
      {"id": "c", "bali": "ᬤᬄᬫ", "is_correct": false}
    ],
    "correct_answer": "a",
    "explanation": "Dharma ditulis ᬤᬃᬫ dengan surang untuk r dan gantungan ma",
    "xp": 20
  }
]
```

### dictionary.json (special words)

For words that fail rule-based transliteration.

```json
{
  "angklung": {
    "latin": "angklung",
    "bali": "ᬅᬗ᭄ᬓ᭄ᬮᬸᬂ",
    "reason": "A independent, not Ha, because Angklung starts with vowel A",
    "source": "common word"
  },
  "aksara": {
    "latin": "aksara",
    "bali": "ᬅᬓ᭄ᬱᬭ",
    "note": "Sa sapa for sha"
  },
  "bleganjur": {
    "latin": "bleganjur",
    "bali": "ᬩᬼᬕᬜ᭄ᬚᬸᬃ",
    "note": "La gantungan + pepet combination allowed, example of special rule"
  }
}
```

## Future SQL Schema (PostgreSQL)

```sql
-- Users (future)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE,
  name VARCHAR(255),
  avatar_url TEXT,
  xp INT DEFAULT 0,
  streak INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Lessons (migrate from JSON)
CREATE TABLE lessons (
  id VARCHAR(50) PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  level INT,
  order_num INT,
  category VARCHAR(50),
  content JSONB,
  xp_reward INT,
  is_published BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Aksara
CREATE TABLE aksara (
  id VARCHAR(50) PRIMARY KEY,
  bali_char VARCHAR(10) NOT NULL,
  latin VARCHAR(20) NOT NULL,
  name VARCHAR(100),
  unicode VARCHAR(20),
  type VARCHAR(50),
  warga VARCHAR(50),
  data JSONB,
  level INT
);

-- User Progress
CREATE TABLE user_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  lesson_id VARCHAR(50) REFERENCES lessons(id),
  completed BOOLEAN DEFAULT false,
  score INT,
  completed_at TIMESTAMP,
  UNIQUE(user_id, lesson_id)
);

-- Quiz Attempts
CREATE TABLE quiz_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  quiz_id VARCHAR(50),
  answer JSONB,
  is_correct BOOLEAN,
  time_spent INT,
  xp_earned INT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Dictionary
CREATE TABLE dictionary (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  latin VARCHAR(255) NOT NULL,
  bali TEXT NOT NULL,
  meaning TEXT,
  source VARCHAR(255),
  is_verified BOOLEAN DEFAULT false
);
```

## Indexes

For JSON MVP, we use in-memory dict with O(1) lookup.
For SQL future:
- INDEX on lessons(level, order_num)
- INDEX on aksara(type, latin)
- INDEX on user_progress(user_id)
- GIN index on dictionary latin for full-text search

## Data Seeding

Seed script `seed.py` loads JSON into memory and optionally into DB.

## Versioning

JSON files versioned in Git. Each change requires PR with cultural verification.

## Backup & Migration

- JSON backup in Git
- For SQL: pg_dump daily, WAL archiving
- Migration tool: Alembic
