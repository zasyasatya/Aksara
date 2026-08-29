# SDLC - Software Development Life Cycle - Aksara Platform

## 1. Overview

Metodologi: **Agile Scrum + Lean UX** dengan iterasi 1 minggu, fokus pada validasi transliterasi yang akurat secara budaya.

## 2. Phases

### Phase 1: Requirement & Research (Done)
- **Activities:**
  - Research Aksara Bali dari sumber resmi: aksaradinusantara.com, Unicode, Lontar, jurnal
  - Interview (simulasi) dengan guru Bahasa Bali
  - Competitive analysis: KomangPutra.com, BasaBali Wiki, Noto Balinese
  - Define classification:
    - Wresastra 18
    - Swalalita 33 (Wresastra + mahaprana, etc)
    - Aksara Suara 14 (A, I, U, E, O, etc)
    - Pangangge Suara 11+ (ulu, suku, taleng, pepet...)
    - Pangangge Tengenan 4 (bisah, surang, cecek, adeg-adeg)
    - Pangangge Aksara 4 (cakra, nania, suku kembung, gantungan La)
    - Gantungan & Gempelan forms
    - Angka, tanda baca
  - Create PRD, Branding Guide

- **Deliverables:** PRD.md, BRANDING.md, research notes

### Phase 2: System Design

#### Architecture
```
[Client: Next.js 15] 
   | REST /api
[FastAPI Backend]
   |-- /translate (Transliterator Service)
   |-- /classify (Classifier Service)
   |-- /lessons (Lesson Service)
   |-- /quiz (Quiz Engine + Validation)
   |-- /gantungan (Rule Engine)
   |
[Data Layer: JSON + SQLite (future Postgres)]
   - aksara.json (master data)
   - pangangge.json
   - lessons.json
   - quiz.json
   - dictionary (special words)
```

#### Component Diagram
- **Transliterator Core:**
  - Latin Tokenizer → Syllable Parser → Gantungan Resolver → Pangangge Mapper → Unicode Composer
  - Bali Parser → Unicode Decomposer → Pangangge Detector → Gantungan Parser → Latin Composer
  - Dictionary override for special words (Angklung, etc)
  - Tumpuk Telu checker

- **Classifier:**
  - Input: single char or string
  - Output: type, name, latin, description, unicode, category

- **Quiz Engine:**
  - Question Generator (randomized from lessons)
  - Answer Validator (canonical + normalized comparison)
  - Feedback Generator (explain error type)

#### Database Design
See DATABASE_DESIGN.md

#### API Design
See API_SPEC.md

### Phase 3: Implementation

#### Backend (FastAPI)
- Setup: Python 3.11, FastAPI, Uvicorn, Pydantic v2
- Structure:
```
backend/
  app/
    main.py
    core/config.py
    data/aksara_master.json
    models/
    schemas/
    services/transliterator.py (600+ lines, advanced)
    services/classifier.py
    services/quiz.py
    routers/translate.py, lessons.py, quiz.py, classify.py
    tests/
  requirements.txt
  Dockerfile
```
- Key Algorithms:
  - Latin→Bali: 
    1. Lowercase, normalize
    2. Tokenize per word
    3. For each word, iterate chars, build syllables: detect consonant clusters (ng, ny, etc), vowel signs
    4. Map consonant to base aksara: ha, na, ca, ra, ka, etc.
    5. If next char is vowel, apply pangangge suara, else inherent /a/
    6. If next char is consonant and not at word boundary, use gantungan form for next consonant (not adeg-adeg)
    7. If consonant at end, use adeg-adeg
    8. Handle pangangge tengenan: h→bisah, r→surang, ng→cecek
    9. Compose Unicode string
  - Bali→Latin:
    1. Iterate Unicode codepoints U+1B00-U+1B7F
    2. Detect base aksara
    3. Check for following gantungan (U+1B44 adeg-adeg + base or direct gantungan forms)
    4. Detect pangangge suara marks
    5. Detect pangangge tengenan
    6. Compose latin

#### Frontend (Next.js 15)
- Setup: `npx create-next-app@latest frontend --typescript --tailwind --app`
- Structure:
```
frontend/
  app/
    layout.tsx (font: Plus Jakarta Sans + Noto Sans Balinese)
    page.tsx (landing)
    dashboard/page.tsx
    learn/[id]/page.tsx
    translate/page.tsx
    quiz/page.tsx
    playground/page.tsx
  components/
    ui/ (Button, Card, Badge, etc - custom design system)
    aksara/ (AksaraCard, AksaraKeyboard, AksaraDisplay)
    quiz/ (QuizCard, ValidationFeedback)
    layout/ (Header, Sidebar, BottomNav, MobileMenu)
  lib/
    api.ts (fetch wrapper)
    transliterate.ts (client-side mirror for instant feedback)
    store.ts (zustand)
  public/
    fonts/
  styles/globals.css (design tokens)
```
- Design System: Tailwind with custom tokens (see BRANDING.md)
- State: Zustand for progress, lesson, quiz
- Animations: Framer Motion for card transitions, confetti on correct answer

### Phase 4: Testing

#### Test Strategy (see TEST_PLAN.md)
- **Backend:**
  - Unit: transliterator test cases (100+ cases from research papers)
  - Unit: classifier
  - Integration: API endpoints
  - Accuracy benchmark vs existing tools
- **Frontend:**
  - Unit: Vitest for utils
  - Component: React Testing Library
  - E2E: Playwright for critical flows (translate, quiz)
  - Visual: Chromatic? Manual responsive check
  - Accessibility: axe-core

#### Test Cases Examples
- Latin→Bali: "bali" → ᬩᬮᬶ, "aksara" → ᬅᬓ᭄ᬱᬭ, "Om Swastyastu" → ᬑᬁ ᬲ᭄ᬯᬲ᭄ᬢ᭄ᬬᬲ᭄ᬢᬸ
- Bali→Latin: ᬩᬮᬶ → bali
- Gantungan: "dharma" → ᬤᬃᬫ (with gantungan Ma)
- Tumpuk telu prevention
- Quiz validation: correct vs incorrect detection

### Phase 5: Deployment

- **Docker Compose:** backend + frontend + nginx
- **CI/CD:** GitHub Actions (test → build → push)
- **Hosting:** Vercel for frontend, Render/Fly for backend (or single VPS)
- **Domain:** aksara.bali (future)
- **Monitoring:** Sentry, PostHog analytics

### Phase 6: Maintenance & Iteration

- Feedback loop dari guru Bahasa Bali
- Dictionary expansion (kosa kata Bali)
- ML model untuk OCR tulisan tangan (future)
- PWA offline

## 3. Roles (Solo Dev + AI Agent)

- Product Owner: Define PRD, prioritize
- Designer: Branding, UI/UX, Design System
- Backend Engineer: FastAPI, transliterator engine
- Frontend Engineer: Next.js, responsive
- QA: Test cases, accuracy validation
- DevOps: Docker, deployment

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Transliteration inaccurate for complex sentences | High | Extensive test cases from academic papers, dictionary override, community feedback |
| Font rendering issues on mobile | Medium | Use Noto Sans Balinese via Google Fonts, subset, fallback, test on real devices |
| Tumpuk telu & special rules missed | High | Implement rule engine with explicit forbidden checks, unit tests |
| Performance on low-end devices | Medium | Lazy load, font display swap, API caching |
| Cultural inaccuracy | High | Consult sumber Bali, cite sources, disclaimer |

## 5. Documentation

- PRD.md
- ARCHITECTURE.md
- API_SPEC.md
- BRANDING.md
- DATABASE_DESIGN.md
- TEST_PLAN.md
- README.md (setup instructions)

## 6. Definition of Done

- Feature implemented + tested + documented
- Responsive check (mobile 360px, tablet 768px, desktop 1280px)
- API docs updated (Swagger)
- No console errors, Lighthouse >90
- Transliteration accuracy >95% on test suite
- Committed & pushed to repo
