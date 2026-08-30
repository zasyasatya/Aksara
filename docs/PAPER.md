# Aksara: An Interactive Digital Platform for Preserving the Balinese Language, Script, and Literacy

**Submitted to: .id DeveloperDay 2026 — Inclusions & Community Services, Education track**
**Team:** (up to 3 members, see Section 5) · **Demo:** https://aksara.id

---

## 1. Title

**Aksara — "Melestarikan Warisan, Menulis Masa Depan" (Preserving Heritage, Writing the Future):** an open-access, gamified learning platform for the Balinese language and script (Hanacaraka), with an accurate Latin↔Aksara transliteration engine, auto-graded script-writing assessment, a real-time teacher content panel, and a social-media twibbon studio.

---

## 2. Background (Latar Belakang)

### 2.1 A living heritage under pressure

Balinese (Bhasa Bali) is spoken by approximately **3.33 million people** in a province of **4.46 million** (BPS, mid-2024). It is one of only four regional languages in Indonesia with more than one million speakers — yet its future is not secure. The Indonesian government's language agency (Badan Pengembangan dan Pembinaan Bahasa, via the Bali Provincial Language Office, 2022) assessed Balinese vitality as **"vulnerable" (rentan)**: usage among the younger generation is declining, driven by:

- intergenerational shift — parents increasingly socializing children in Indonesian or English rather than Balinese;
- urbanization and migration toward cities and tourism areas, where Balinese is no longer the default home language;
- code-mixing and reduced formal register use (the three speech levels of *basa krama/madya/awig* are eroding);
- no standardized, modern, digital writing medium: most Balinese people can speak the language but cannot write its script, and most digital resources are static (fonts, PDFs, scanned primers).

Indonesia's situation is stark: of the country's ~700+ languages, **139 are endangered and 15 have already gone extinct** (Badan Bahasa, 2022). The government responded with a nationwide *Revitalisasi Bahasa Daerah* program, explicitly recommending that **"the transmission of Balinese language, script, and literature must be done in a structured way through school-based learning"** (Kemendikbudristek press release, 2022).

### 2.2 A historic policy window

In 2026 the policy window became a mandate. **Peraturan Gubernur Bali No. 7 Tahun 2026** (replacing Pergub No. 20/2013) establishes, for **all formal education units in Bali**:

- **Bahasa Bali** (language, **script/aksara**, and literature) and **Kearifan Lokal Bali** as **two independent local-curriculum subjects**, each **minimum 2 teaching hours per week**;
- Bahasa Bali as the **language of instruction** for those subjects;
- structured progression by grade (tematic introduction in grades I–II, systematic instruction grades III–VIII, SMA/SMK in grades X–XI);
- professional Balinese-language teachers, with space for *pasraman*, *sekaa*, and *sanggar* (community institutions) to participate.

This means that **every formal school in Bali must now teach aksara writing**, but almost none has a modern digital medium for it. Existing tools are static or outdated: the best prior transliteration study (Jampel, Indrawan & Widiana, IJECE 2018) measured a production transliteration app at **68% accuracy (103/151 cases)** with 13 recurring failure words — a quality level unsuitable for classroom assessment.

### 2.3 The gap

| Need (per Pergub 7/2026 & revitalization program) | Available today | Gap |
| --- | --- | --- |
| Structured aksara curriculum, grades I–XII | Printed primers, scattered PDFs | No interactive, leveled, self-paced curriculum |
| Accurate transliteration for teachers/students | Legacy app ≈ 68% (Jampel et al., 2018) | No 95%+ engine with rule explanations |
| Assessment of students' script writing | Manual grading | No automated, educational validation with feedback |
| Teacher-controlled, curriculum-aligned content | None | No browser-based content management for teachers |
| Student motivation & cultural reach beyond the classroom | None | No shareable, culturally authentic creative output |

**Aksara** was built to close all five gaps with one open-access platform.

---

## 3. Objectives of the Solution (Tujuan Pengembangan Solusi)

1. **Preserve** — provide a free, permanent digital medium for learning the Balinese language, script, and literary conventions, so that intergenerational transmission does not depend on any single teacher's initiative.
2. **Support the 2026 mandate** — give every Balinese school (formal, *pasraman*, *sanggar*) ready-to-use, curriculum-aligned learning media aligned with Pergub 7/2026 (2 JP/week, grade-sequenced content, teacher-controllable).
3. **Assess authentically** — let students *write* aksara and receive immediate, rule-based feedback (not multiple choice only), with an accuracy target of ≥ 95% on the validated test set.
4. **Empower teachers** — enable teachers to create/edit lessons, quizzes (including writing quizzes), and the transliteration dictionary from a browser, with changes live for students without any deployment.
5. **Grow organically** — turn learners into publishers: a twibbon studio (photo + aksara text) so that cultural content spreads through social media, bringing new learners to the platform (zero-cost acquisition).

---

## 4. Description of the Solution (Deskripsi Solusi)

Aksara is a web platform (single origin, mobile-first) with five learning/teaching surfaces and one cultural-creative surface:

### 4.1 Translate (Latin ↔ Aksara, bidirectional)
A rule-based transliteration engine with a special-case dictionary. Handles the phenomena that make Balinese hard: *gantungan* (consonant clusters), *gempelan* (glottalized p/s), *pangangge* (11 vocalic signs + 4 final signs + 4 special signs), and the *tumpuk telu* prohibition (two *gantungan* on one base character). Every output ships with a per-syllable **breakdown + rule explanation** (teaching material in itself) and a confidence score. Accuracy: **≥ 95%** on the maintained test set (vs. 68% for the prior best published system). The page is bidirectional — students can also read aksara into Latin — and aksara can be **typed, pasted, or picked from an on-screen virtual keyboard**.

### 4.2 Learn (Belajar) — 11 lessons, 6 levels
Wresastra 18 → vocalic signs → final signs → clusters → Sanskrit/Kawi loan-script → full sentences. Each character: visual form, stroke order, example words, timed estimate (10–15 min), XP. Progress (XP, streak, level) is gamified and stored client-side (MVP, no account needed).

### 4.3 Quiz with automated *script-writing* assessment
Four question types, filterable in one screen: multiple choice, true/false, cluster-choice, and the novel **write-aksara** type: the student sees a Latin word and *writes the aksara* (keyboard virtual, typing, or paste); the system validates the answer via the transliteration engine's pair-validator (`POST /api/quiz/validate-pair`, exact or tolerant mode) and returns **correct/incorrect + similarity % + per-rule suggestions + the correct form**. 24 quizzes ship out of the box (7 are write-aksara, from single letters to full phrases like *matur suksma*).

### 4.4 Teacher Panel (Panel Guru, `/guru`)
Full CRUD for **lessons, quizzes, and the special dictionary** from the browser — with a mini aksara keyboard in the form fields, pickers for characters/quizzes, and two-step delete confirmation. In production the panel is protected by a teacher token (`AKSARA_GURU_TOKEN`); in development mode it is open. Content is persisted to JSON stores with atomic writes and **re-read per request**, so a teacher's edit is live for students immediately — no restart, no deploy. This directly serves the Pergub requirement that schools control their own local curriculum content.

### 4.5 Studio Twibbon (`/twibbon`) — the viral layer
Upload a photo → type a phrase in Latin (auto-translated to aksara) or paste aksara directly → choose among **10 twibbon frames** (including a signature "strip aksara warisan" band), 3 aspect ratios (4:5 / 1:1 / 9:16), text size/position/color/shadow → export a **1080px PNG** and **share directly to WhatsApp/Instagram/X** via the Web Share API, or copy to clipboard. A subtle `aksara.id` watermark (toggleable) turns every shared image into a back-link to the platform.

### 4.6 School partnership program (`/sekolah`)
A public page documenting the Pergub 7/2026 opportunity, listing partner schools, and hosting a free partnership application form (school, region, student count, contact). The backend records applications and publishes an honest, live counter of visits and generated twibbons (`GET /api/stats`) — metrics that serve as the platform's proof of concept and are cited in this paper.

---

## 5. System Implementation (Implementasi Sistem)

### 5.1 Delivery
- One-command launcher (`run.py` / `run.sh` / `run.bat`): creates an isolated `.venv`, installs backend dependencies, builds the UI as a static export, and serves **UI + API on one origin** (port 8000) using only the Python standard library for orchestration. Node.js is optional at runtime.
- `--dev` mode runs FastAPI + Next.js dev servers with hot reload and a same-origin `/api` proxy.
- Static export + FastAPI `StaticFiles` keeps browser code on the same origin — no hard-coded visitor-localhost calls, no CORS pain for classroom use.
- Deployment target: a **.id domain** (aksara.id) — an explicit requirement of .id DeveloperDay and a statement of national digital identity.

### 5.2 Feature implementation notes
- **Transliteration engine:** rule/state-machine implementation of the Balinese Unicode block (U+1B00–U+1B77 per ISO 15919 / LOC Romanization Table 2025 / Nala 2006), with a curated dictionary for known problem words (e.g., *angklung*, *aksara*, *om swastyastu*).
- **Pair validation:** normalizes both strings (combining-sign awareness), aligns characters, and produces a similarity score plus rule-specific suggestions ("use *gantungan*, not *adeg-adeg*").
- **Live content:** `data_store` module — RLock-protected JSON reads/writes with atomic `os.replace`; routers (lessons, quiz, manage) read through it per request.
- **Anti-spam honesty:** visit/twibbon counters are rate-limited per IP (20 s cooldown) so the published PoC metrics stay credible.
- **Testing culture:** 57 automated backend tests (transliteration cases drawn from academic papers, CRUD, auth dev/prod, validation endpoints); frontend verified with a production type-checked build.

### 5.3 Team (max 3, per competition rules)
1. **Product engineer** — full-stack (FastAPI + Next.js), transliteration engine, CI/launcher.
2. **Design & content** — UI/UX, branding, lesson copy, documentation.
3. **Cultural subject-matter advisor** — active Balinese language teacher / *sanggar* member who validates content, pronunciation conventions, and the school partnership program (collaborating, not counted as core build capacity).

---

## 6. Technology Architecture (Arsitektur Teknologi)

```
┌──────────────────────────── Browser (same origin) ────────────────────────────┐
│  Next.js 15 (App Router, React 19, TypeScript, Tailwind, Zustand)             │
│  • /learn /quiz /translate /twibbon /guru /sekolah /docs /admin               │
│  • Canvas twibbon renderer (1080px PNG export, Web Share API)                 │
│  • Virtual aksara keyboard component (shared across pages)                    │
└───────────────▲───────────────────────────────────────────────────────────────┘
                │ /api/* (same-origin; Next.js rewrites in dev, FastAPI StaticFiles in prod)
┌───────────────▼───────────────────────────────────────────────────────────────┐
│  FastAPI (Python 3.11) — single process                                        │
│  routers: translate · classify · lessons · quiz · docs · manage · engagement  │
│  services: transliterator (rules+dict) · quiz_engine (check+validate_pair)    │
│            data_store (RLock JSON, atomic writes, per-request reads)           │
│  config: AKSARA_MODE dev/prod · AKSARA_ADMIN_TOKEN · AKSARA_GURU_TOKEN        │
└───────────────▲───────────────────────────────────────────────────────────────┘
                │ read/write (atomic)
┌───────────────▼───────────────────────────────────────────────────────────────┐
│  JSON content stores (git-versioned, editable live via /guru)                 │
│  aksara_master.json · lessons.json · quiz.json · dictionary.json · docs.json  │
│  engagement.json (visits, twibbons, school applications)                      │
└───────────────────────────────────────────────────────────────────────────────┘
        run.py launcher: .venv + pip + npm build + serve on one port (stdlib only)
```

Design decisions worth noting for the jury:

- **Same-origin everything** — classroom-friendly: the app works from a school device that cannot reach the public internet's API layer; no key management; no CORS.
- **Content as data, not code** — teachers are first-class authors; the platform's curriculum can differ per school without forking the app.
- **Boring, auditable persistence** — JSON files + atomic writes + git: reproducible, diffable, and zero-ops; the trade-off (single-node) is deliberate for an education MVP and documented in the roadmap (SQLite/Postgres behind the same repository interface).
- **Browser as the rendering engine for cultural media** — the twibbon studio uses Canvas + the real Noto Sans Balinese webfont, so output is a faithful 1080px cultural artifact, not a screenshot.

---

## 7. Impact and Benefits (Dampak dan Manfaat)

### 7.1 Cultural impact
- A free, permanent digital medium for aksara writing — the skill the Pergub 7/2026 mandate now requires in every Balinese classroom.
- Authentic rule explanations (not just answers) build *literacy*, not rote memorization; the breakdown panel doubles as a teacher's whiteboard aid.
- The twibbon studio converts learners into cultural publishers: every shared image carries aksara and a back-link — a self-sustaining preservation loop.

### 7.2 Educational impact
- Grade-sequenced 11-lesson path with timed estimates fits the mandated 2 JP/week slot.
- Automated write-aksara assessment removes the grading bottleneck (a class of 40 × weekly writing quiz is now instantly gradeable with per-rule feedback).
- The teacher panel turns *every* Balinese teacher — not only those who can code — into a content author.

### 7.3 Proof of concept (live, verifiable)
- Public demo on a **.id domain** with live, rate-limited metrics: `GET /api/stats` returns real visits and twibbons generated; `GET /api/stats/schools` lists partnership applications.
- 57 automated backend tests (≥ 95% transliteration accuracy on the maintained set) + production type-checked frontend build.
- (Traction numbers at submission are filled from the live counters — honest, small, and growing; we report them as-is.)

### 7.4 Market potential (the 30% criterion)
| Layer | Size | Rationale |
| --- | --- | --- |
| **TAM** | 4.46 M residents of Bali; 3.33 M Balinese speakers; all formal schools in Bali (Pergub 7/2026 mandate) | Every resident is a potential learner; every school is a mandate-holder |
| **SAM** | Schools + *pasraman* + *sanggar* + diaspora + cultural tourists | Mandate-driven (schools) plus voluntary (community institutions, expat/tourism learning) |
| **SOM (yr 1)** | Pilot partnership schools (target 10–30) + organic growth via twibbon sharing | Free for students lowers adoption friction; twibbon UGC is the acquisition channel (CAC ≈ 0) |
| **Expansion TAM** | Other scripts: Javanese, Lontara (Bugis), Batak | Engine, quiz, and twibbon layers are script-agnostic by design — "Aksara Nusantara" roadmap |

Sustainability: free for students (public-good pricing); the school-license and multi-script white-label opportunities are explicit in the roadmap (Section 8), so the model does not depend on venture funding to survive.

---

## 8. Development Plan (Rencana Pengembangan)

| Horizon | Milestone |
| --- | --- |
| **0–3 months** | Pilot with 5–10 partner schools (onboarding + co-designed quizzes); publish traction dashboard; harden `.id` deployment (HTTPS, backups); add offline-capable PWA for low-bandwidth classrooms |
| **3–9 months** | Teacher reports (per-class quiz analytics, writing-error patterns); account system (opt-in, synced progress); pronunciation audio per character (recorded with native speakers) |
| **9–18 months** | **Aksara Nusantara**: Javanese + Lontara (Bugis) script packs (engine port, curriculum template, twibbon frames); multi-tenant school workspaces |
| **Ongoing** | Content council with *sanggar* and the Bali Provincial Language Office; open dataset of validated transliteration cases for academic reuse |

**Success metrics (yr 1):** ≥ 30 partner schools, ≥ 90% lesson completion in pilot classes, ≥ 50,000 twibbons generated (organic reach), 100% of mandated syllabus topics covered per level.

---

## References

1. Jampel, I. N., Indrawan, G., & Widiana, I. W. (2018). *Accuracy Analysis of Latin-to-Balinese Script Transliteration Method.* IJECE 8(3), 1788–1797. DOI 10.11591/ijece.v8i3.pp1788-1797.
2. Library of Congress (2025). *Balinese Romanization Table.* loc.gov/catdir/cpso/romanization/balinese.pdf (ISO 15919:2001-based).
3. Nala, I. M. (2006). *Pedoman Aksara Bali.*
4. Balai Bahasa Provinsi Bali (2022). *Upaya Pelindungan Bahasa Daerah melalui Revitalisasi* — vitalitas bahasa Bali: **rentan** (vulnerable). balaibahasaprovinsibali.kemdikbud.go.id.
5. Kemendikbudristek (2022). *Siaran Pers: Revitalisasi Bahasa Daerah* — pewarisan bahasa, aksara, dan sastra Bali wajib terstruktur berbasis sekolah. kemendikdasmen.go.id.
6. Peraturan Gubernur Bali Nomor 7 Tahun 2026 — muatan lokal: Bahasa Bali (bahasa, aksara, sastra) & Kearifan Lokal Bali, min. 2 JP/minggu, seluruh satuan pendidikan formal.
7. BPS (2024) — penduduk Bali 4.461.260 (estimasi pertengahan 2024); bahasa Bali 3,33 juta penutur (data revitalisasi bahasa daerah 2022).
8. Sanjani, Indrawan, & Gunadi (2021). *Pengembangan Metode Pemilahan Suku Kata pada Transliterasi Teks Latin ke Aksara Bali Berbasis Finite State Machine.* JIK 6(2).
