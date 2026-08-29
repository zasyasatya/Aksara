# Architecture - Aksara Platform

## High Level Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Next.js 15    │      │   FastAPI       │      │   Data Layer    │
│   Frontend      │─────▶│   Backend       │─────▶│   JSON + SQLite │
│                 │◀─────│                 │◀─────│                 │
│ - App Router    │      │ - Transliterator│      │ - aksara.json   │
│ - Tailwind      │      │ - Classifier    │      │ - lessons.json  │
│ - Zustand       │      │ - Quiz Engine   │      │ - quiz.json     │
│ - Framer Motion │      │ - Lessons API   │      │ - dictionary    │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                        │
         │                        │
         ▼                        ▼
   Vercel / CDN            Render / Fly / Docker
   Noto Sans Balinese      Uvicorn + Gunicorn
```

## Frontend Architecture

### Tech Stack
- Next.js 15.0+ (App Router, RSC, Server Actions)
- TypeScript 5.5+
- Tailwind CSS 3.4+ with custom design tokens
- Framer Motion 11 for animations
- Zustand 4 for state (lightweight, no boilerplate)
- Lucide React for icons
- next/font for Plus Jakarta Sans & Noto Sans Balinese

### Folder Structure
```
frontend/
├── app/
│   ├── layout.tsx (root layout, fonts, providers)
│   ├── page.tsx (landing)
│   ├── globals.css (tailwind + tokens)
│   ├── dashboard/page.tsx
│   ├── learn/
│   │   ├── page.tsx (list lessons)
│   │   └── [id]/page.tsx (detail)
│   ├── translate/page.tsx
│   ├── quiz/page.tsx
│   ├── playground/page.tsx
│   └── api/ (proxy to backend if needed)
├── components/
│   ├── ui/ (Button, Card, Badge, Input, etc)
│   ├── layout/ (Header, Sidebar, BottomNav, Footer)
│   ├── aksara/ (AksaraCard, AksaraKeyboard, AksaraDisplay, GantunganVisualizer)
│   ├── quiz/ (QuizCard, QuizOptions, Feedback)
│   └── dashboard/ (Progress, Streak, Leaderboard)
├── lib/
│   ├── api.ts (typed fetch wrapper)
│   ├── transliterate.ts (client-side fast transliterate for UX)
│   ├── store.ts (zustand stores)
│   ├── utils.ts (cn, etc)
│   └── constants.ts (aksara data for offline)
├── public/
│   ├── fonts/ (fallback)
│   ├── icons/
│   └── illustrations/
├── tests/
│   ├── unit/
│   └── e2e/
├── tailwind.config.ts
├── next.config.js
└── package.json
```

### State Management (Zustand)

```ts
// store.ts
interface ProgressStore {
  xp: number
  streak: number
  completedLessons: string[]
  currentLesson: string | null
  addXP: (n) => void
  completeLesson: (id) => void
}

interface QuizStore {
  currentQuiz: Quiz | null
  answers: Record<string, string>
  score: number
  checkAnswer: (qId, answer) => {correct, explanation}
}
```

### Key Frontend Logic: Client Transliteration Mirror

Untuk instant feedback (tanpa tunggu API), frontend punya simplified transliterator JS yang mirror backend logic untuk 80% kasus umum. Untuk kasus kompleks, fallback ke API.

## Backend Architecture

### Tech Stack
- FastAPI 0.115+ (latest)
- Python 3.11+
- Pydantic v2 for validation
- Uvicorn
- Pytest
- No DB for MVP (JSON files), SQLAlchemy ready for future

### Folder Structure
```
backend/
├── app/
│   ├── main.py (FastAPI app, CORS, routers)
│   ├── core/
│   │   ├── config.py (settings)
│   │   └── exceptions.py
│   ├── data/
│   │   ├── aksara_master.json (full classification)
│   │   ├── pangangge.json
│   │   ├── lessons.json
│   │   ├── quiz.json
│   │   └── dictionary.json (special words)
│   ├── models/ (Pydantic models for future DB)
│   ├── schemas/ (request/response)
│   │   ├── translate.py
│   │   ├── quiz.py
│   │   ├── lessons.py
│   │   └── classify.py
│   ├── services/
│   │   ├── transliterator.py (CORE - 800+ lines)
│   │   ├── classifier.py
│   │   ├── quiz_engine.py
│   │   └── lessons_service.py
│   ├── routers/
│   │   ├── translate.py
│   │   ├── classify.py
│   │   ├── lessons.py
│   │   ├── quiz.py
│   │   └── health.py
│   └── tests/
│       ├── test_transliterator.py
│       ├── test_classifier.py
│       ├── test_api.py
│       └── test_quiz.py
├── requirements.txt
├── Dockerfile
└── README.md
```

### Core Service: Transliterator

#### Latin → Bali Algorithm (Advanced)

```
Input: "bali" (latin)

Steps:
1. Normalize: lowercase, trim, remove non-Bali latin chars? Keep spaces.
2. Split words: ["bali"]
3. For each word:
   a. Initialize result = ""
   b. i = 0
   c. While i < len(word):
      - Detect special clusters: "ng", "ny", "kh", "gh", etc? Actually Balinese "nga" is single.
      - Get current consonant mapping:
        Mapping table:
        ha -> ᬳ U+1B33
        na -> ᬦ U+1B26
        ca -> ᬘ U+1B18
        ra -> ᬭ U+1B2D
        ka -> ᬓ U+1B13
        da -> ᬤ U+1B24 (actually da is different from dha)
        ta -> ᬢ U+1B22
        sa -> ᬲ U+1B32
        wa -> ᬯ U+1B2F
        la -> ᬮ U+1B2E
        ma -> ᬫ U+1B2B
        ga -> ᬕ U+1B15
        ba -> ᬩ U+1B29
        nga -> ᬗ U+1B17
        pa -> ᬧ U+1B27
        ja -> ᬚ U+1B1A
        ya -> ᬬ U+1B2C
        nya -> ᬜ U+1B1C
        etc for Swalalita...
      - Lookahead for vowel:
        If i+1 is vowel (a,i,u,e,o, etc):
          - If vowel == 'a': no pangangge (inherent)
          - If 'i': add ulu ◌ᬶ U+1B36
          - If 'u': suku ◌ᬸ U+1B38
          - If 'e' (pepet): ◌ᬾ? Actually pepet is ◌ᭂ U+1B42? Need accurate mapping
          - etc
          - Advance i by 2 (consonant+vowel)
        Else if next char is consonant:
          - If at word end? Use adeg-adeg ◌᭄ U+1B44 to kill vowel
          - Else: next consonant should be gantungan form
            - For gantungan, we use adeg-adeg + base OR special gantungan form?
            - In Unicode, gantungan is adeg-adeg + base letter
            - Example: "nda": na + adeg-adeg + da => ᬦ᭄ᬤ
          - Advance i by 1, but next iteration will handle gantungan? Actually we need to emit base + adeg-adeg, then next consonant base will be rendered as gantungan automatically by font? In Unicode Balinese, gantungan is rendered via adeg-adeg.
          - So: emit base, emit adeg-adeg, then continue loop will emit next base which will be visually gantungan.
        Else (end of word):
          - If consonant at end, need adeg-adeg
      - Special handling for pangangge tengenan:
        - If word ends with 'h' after vowel: use bisah ◌ᬄ U+1B04? Actually check
        - If 'r' after vowel: surang ◌ᬃ U+1B03
        - If 'ng' at end: cecek ◌ᬂ U+1B02
      - Handle independent vowels at start: "a" -> ᬅ U+1B05, etc
   d. Concatenate
4. Return composed string

Edge Cases:
- "aksara": a (independent) + ksa? Actually "ak-sa-ra": a + sa with gantungan ka? No, "aksara" = a + k + sa + ra? In Balinese, "aksara" is often ᬅᬓ᭄ᬱᬭ (a + ka + adeg-adeg + sa sapa + ra). Sa sapa is Swalalita for "sha".
- Need dictionary for words like "Angklung" where "A" independent not Ha.
- Tumpuk telu: ensure we don't have more than 1 gantungan per base. If we detect 2 consecutive gantungan needed, we must use adeg-adeg + base + adeg-adeg + base but that's forbidden visually. Solution: break with adeg-adeg explicit? Actually rule: max 1 gantungan. So if we have 3 consonants cluster, second is gantungan, third must be...? In practice, use adeg-adeg for second cluster? We implement checker that if we already have gantungan on current base, next consonant must start new syllable with adeg-adeg.

#### Bali → Latin Algorithm

```
Input: "ᬩᬮᬶ"

Steps:
1. Iterate codepoints
2. Maintain state: current base, pending vowel
3. For each codepoint:
   - If U+1B13-U+1B33 etc is base aksara: 
     - If previous base had adeg-adeg pending, then this base is gantungan, so no new syllable vowel, just consonant cluster
     - Else, previous syllable complete, start new: map base to latin (ka, etc)
     - Set inherent vowel /a/ pending
   - If pangangge suara (U+1B35-U+1B3A etc): change vowel
   - If pangangge tengenan (U+1B02-U+1B04): add final consonant (ng, r, h)
   - If adeg-adeg U+1B44: kill inherent vowel, mark next base as gantungan
   - If pangangge aksara (gantungan forms like cakra U+1B2D with adeg-adeg? Actually cakra is ◌᭄ᬭ = adeg-adeg + ra)
     - Need to detect special: ◌᭄ᬭ = ra gantungan (cakra) => add "ra" cluster? Actually "kra" = ka + ra gantungan = "kra"
   - If independent vowel U+1B05-U+1B12: map to a, i, u, etc
4. Compose latin string
```

#### Accuracy Improvements

- Use dictionary for common words (1000+ entries) to override rule-based
- Use longest-match for clusters
- Normalize input (lowercase, remove punctuation except space)
- For Bali→Latin, handle zero-width joiner etc

### Classifier Service

Input: single Bali char or string
Output:
- Type: Wresastra, Swalalita, Suara, Pangangge, Angka, Tanda Baca
- Subtype: for pangangge: Suara/Tengenan/Aksara
- Name: e.g., "Ka", "Ulu", "Bisah"
- Latin: "ka", "i", "h"
- Unicode: "U+1B13"
- Description
- Example usage

Data source: aksara_master.json with 200+ entries

### Quiz Engine

- Generates quiz from lessons.json
- Types:
  - multiple_choice: given latin, choose correct Bali
  - true_false: given pair, is it correct?
  - gantungan: given word, choose correct gantungan form
  - arrangement: arrange Bali chars to form word
- Validation:
  - Normalize both expected and answer (NFC, trim)
  - For multiple_choice: direct equality
  - For arrangement: compare Unicode sequence
  - For true_false: check if pair exists in dictionary or transliterator output matches
  - Return feedback: if wrong, explain why (e.g., "Seharusnya pakai cecek untuk akhiran ng, bukan nga + adeg-adeg")

## API Contract (Summary)

See API_SPEC.md for full

- GET /api/health
- POST /api/translate {text, direction: "latin-to-bali" | "bali-to-latin"} → {result, breakdown}
- POST /api/classify {char} → {classifications}
- GET /api/lessons → list
- GET /api/lessons/{id}
- GET /api/quiz?lesson_id=&type=&limit=
- POST /api/quiz/check {quiz_id, answer} → {correct, explanation, xp}

## Security & Performance

- CORS: allow frontend origin
- Rate limiting: 60 req/min per IP for translate (in-memory)
- Input max length: 5000 chars
- Caching: LRU cache for transliteration results (1000 entries)
- Font: serve Noto Sans Balinese via CDN, preload

## Deployment

### Docker Compose
```
version: "3.8"
services:
  backend:
    build: ./backend
    ports: 8000:8000
    env_file: .env
  frontend:
    build: ./frontend
    ports: 3000:3000
    depends_on: backend
```

### Environment
- Backend: PORT=8000, CORS_ORIGINS, etc
- Frontend: NEXT_PUBLIC_API_URL

## Future Considerations

- Postgres for user progress
- Redis for cache & rate limit
- ML model for handwriting OCR (TensorFlow Lite)
- WebSocket for collaborative learning
- PWA with offline dictionary
