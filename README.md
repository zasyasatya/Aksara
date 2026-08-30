# Aksara - Platform Belajar Aksara Bali

> **"Melestarikan Warisan, Menulis Masa Depan"**  
> **"Ngajegang Warisan, Nyurat Masa Depan"**  
> ᬅᬓ᭄ᬱᬭ - ᬧ᭄ᬮᬢ᭄ᬨᭀᬃᬫ᭄ ᬩᭂᬮᬚᬃ ᬅᬓ᭄ᬱᬭ ᬩᬮᬶ

Platform edukasi interaktif untuk mempelajari Aksara Bali (Hanacaraka) dengan pendekatan modern, gamified, dan transliterasi canggih yang menangani gantungan, gempelan, pangangge, dan aturan tumpuk telu.

## ✨ Fitur Utama

### 🔤 Translate Canggih
- **Latin ↔ Aksara Bali** dengan akurasi 95%+
- Handling **gantungan** (cluster konsonan), **gempelan** (pa, sa), **pangangge** (ulu, suku, taleng, pepet, bisah, surang, cecek, adeg-adeg)
- Deteksi **tumpuk telu** (larangan 2 gantungan pada 1 aksara)
- Penanganan khusus: La gantungan + pepet boleh (bleganjur), Cakra + pepet dilarang
- Dictionary untuk kata khusus (Angklung, Aksara, Om Swastyastu)

### 📚 Belajar Bertahap
- 11 level: Wresastra 18 → Pangangge Suara → Tengenan → Gantungan → Swalalita → Kalimat
- Setiap aksara: visual, cara tulis, audio, contoh kata
- Progress tracking, XP, streak, leaderboard

### ✅ Quiz Validasi
- Murid menulis aksara, sistem validasi apakah benar sesuai soal
- Tipe: pilihan ganda, benar/salah, gantungan choice, susun kalimat
- Feedback detail: jelaskan kesalahan (misal: "Seharusnya pakai gantungan, bukan adeg-adeg")
- Endpoint `/api/quiz/validate-pair` untuk validasi custom

### 📚 Dokumentasi & Panel Admin
- **`/docs`** — pusat dokumentasi: tata cara penggunaan untuk **murid, guru, admin**, plus halaman khusus **Metode Scientific & Referensi** (metodologi transliterasi + sumber akademik) — lengkap dengan screenshot halaman
- **`/admin`** — panel admin: atur halaman dokumentasi mana yang **go public**
- **Mode DEV** (`AKSARA_MODE=dev`): semua halaman dokumentasi selalu tampil, akses admin otomatis
- **Mode PROD** (`AKSARA_MODE=prod`): hanya halaman publik yang tampil; admin login via token (`AKSARA_ADMIN_TOKEN`)

### 🎨 Design System
- Branding kuat: Saffron (#FF6B35), Deep Brown (#2C1810), Cream (#FFF8E7), Terracotta
- Font: Plus Jakarta Sans + Noto Sans Balinese
- Responsive: mobile bottom nav, desktop sidebar, swipe cards
- Animasi: Framer Motion, confetti on correct

## 🏗️ Tech Stack

- **Backend:** FastAPI 0.115 (latest), Python 3.11, Pydantic v2, Uvicorn
- **Frontend:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Zustand, Framer Motion
- **Transliteration:** Custom rule engine + dictionary, state machine, Unicode U+1B00-U+1B7F
- **Testing:** Pytest, Vitest, Playwright
- **Deployment:** Docker Compose, Vercel (frontend), Render/Fly (backend)

## 📁 Struktur Repo

```
Aksara/
├── docs/
│   ├── PRD.md - Product Requirements
│   ├── SDLC.md - Development lifecycle
│   ├── BRANDING.md - Brand identity & design system
│   ├── ARCHITECTURE.md - System architecture
│   ├── API_SPEC.md - API specification
│   ├── DATABASE_DESIGN.md - Data model
│   └── TEST_PLAN.md - Testing strategy
├── backend/
│   ├── app/
│   │   ├── main.py - FastAPI app
│   │   ├── core/config.py
│   │   ├── data/ - aksara_master.json, lessons, quiz, dictionary
│   │   ├── services/
│   │   │   ├── transliterator.py - CORE advanced engine (800+ lines)
│   │   │   ├── classifier.py
│   │   │   └── quiz_engine.py
│   │   ├── routers/ - translate, classify, lessons, quiz
│   │   ├── schemas/ - Pydantic models
│   │   └── tests/ - pytest
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx - Landing
│   │   ├── dashboard/ - Dashboard progress
│   │   ├── learn/ - Belajar bertahap
│   │   ├── translate/ - Translate live
│   │   ├── quiz/ - Kuis validasi
│   │   ├── playground/ - Keyboard virtual
│   │   ├── docs/ - Pusat dokumentasi (hub + [slug])
│   │   └── admin/ - Panel admin (publikasi dokumentasi)
│   ├── components/docs/ - Shell, konten per-role, screenshot
│   ├── components/ui/ - Button, Card, Badge
│   ├── components/layout/ - Header, BottomNav
│   ├── components/aksara/ - AksaraCard, etc
│   ├── lib/api.ts - Typed fetch
│   ├── lib/store.ts - Zustand
│   └── public/screenshots/ - Screenshot halaman (untuk dokumentasi)
├── branding/ - Logo, colors, etc
└── docker-compose.yml
```

## 🚀 Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Docs: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App: http://localhost:3000
```

### Docker

```bash
docker-compose up --build
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## 🧪 Testing

### Backend

```bash
cd backend
pytest -v --cov=app
# Test cases: 100+ transliteration cases from academic papers
```

### Frontend

```bash
cd frontend
npm run test:unit
npm run build # Check no TS errors
```

## 📖 Sumber Aksara Bali

- https://aksaradinusantara.com/fonta/aksara/bali
- Unicode Balinese U+1B00-U+1B7F
- Paper: Accuracy Analysis of Latin-to-Balinese Transliteration (IJECE)
- LOC Romanization Table Balinese 2025
- Nala (2006) - Pedoman Aksara Bali

### Aturan Penting yang Diimplementasi

1. **Tumpuk Telu:** Max 1 gantungan per aksara dasar, 3 lapis dilarang
2. **Pepet + Cakra:** Forbidden (fonetik tidak mungkin)
3. **La Gantungan + Pepet:** Allowed (bleganjur ᬩᬼᬕᬜ᭄ᬚᬸᬃ)
4. **Gantungan vs Adeg-adeg:** Gantungan untuk cluster tengah, adeg-adeg untuk akhiran konsonan
5. **Cecek vs Nga:** Cecek (◌ᬂ) untuk akhiran ng, Nga gantungan (◌᭄ᬗ) untuk medial

## 🎯 API Examples

### Translate

```bash
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "bali", "direction": "latin-to-bali"}'
# => {"result": "ᬩᬮᬶ", "breakdown": [...], "confidence": 0.95}
```

### Validate Pair (Fitur Utama: cek apakah tulisan murid benar)

```bash
curl -X POST http://localhost:8000/api/quiz/validate-pair \
  -H "Content-Type: application/json" \
  -d '{"question_latin": "bali", "question_bali": "ᬩᬮᬶ", "user_bali": "ᬩᬮᬶ", "mode": "exact"}'
# => {"is_correct": true, "similarity": 1.0, "suggestions": []}
```

### Quiz Check

```bash
curl -X POST http://localhost:8000/api/quiz/check \
  -H "Content-Type: application/json" \
  -d '{"quiz_id": "quiz-wres-01-1", "answer": "a"}'
```

## 📚 Dokumentasi, Admin & Mode Dev/Prod

Buka **`/docs`** (menu Dokumentasi) untuk panduan penggunaan per peran
(murid/guru/admin) dan halaman **Metode Scientific & Referensi**, serta
**`/admin`** untuk mengatur publikasi halaman dokumentasi.

```bash
# Daftar halaman dokumentasi (field mode + is_admin menentukan tampilan)
curl http://localhost:8000/api/docs/pages

# Ubah status publik/privat (admin only)
curl -X PATCH http://localhost:8000/api/docs/pages/metode-scientific/visibility \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: $AKSARA_ADMIN_TOKEN" \
  -d '{"is_public": false}'
```

### Variabel lingkungan

| Var | Default | Keterangan |
| --- | --- | --- |
| `AKSARA_MODE` | `dev` | `dev` = semua halaman docs tampil + admin otomatis; `prod` = hanya halaman publik, admin butuh token |
| `AKSARA_ADMIN_TOKEN` | `aksara-admin` | Token admin untuk mode prod (header `X-Admin-Token`). **Wajib diganti di produksi.** |

Status publikasi disimpan di `backend/app/data/docs.json`.

## 🎨 Branding

- **Name:** Aksara
- **Tagline:** Melestarikan Warisan, Menulis Masa Depan
- **Colors:** Saffron #FF6B35, Deep Brown #2C1810, Cream #FFF8E7, Terracotta #C45A3C, Sage #7A9E7E, Ocean #2A6F8E
- **Fonts:** Plus Jakarta Sans (UI), Noto Sans Balinese (aksara), Fraunces (display)
- **Logo:** ᬅ (Akara) stylized

Full branding di `docs/BRANDING.md`

## 📝 SDLC & Docs

Semua docs SDLC ada di `/docs`:
- PRD.md, ARCHITECTURE.md, API_SPEC.md, DATABASE_DESIGN.md, TEST_PLAN.md, BRANDING.md, SDLC.md

## 🤝 Kontribusi

1. Fork repo
2. Buat branch fitur
3. Pastikan transliterasi accuracy >95%
4. Jalankan pytest
5. PR dengan penjelasan budaya

## 📄 Lisensi

MIT - Untuk pelestarian budaya Bali

## 🙏 Matur Suksma

Terima kasih kepada:
- Komunitas Aksara di Nusantara
- Guru-guru Bahasa Bali
- Noto Sans Balinese team
- Semua penutur dan penjaga Aksara Bali

---

**ᬫᬢᬸᬃ ᬲᬸᬓ᭄ᬱ᭄ᬫ - Matur Suksma**  
Made with ❤️ for Bali
