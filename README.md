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
│   │   └── playground/ - Keyboard virtual
│   ├── components/ui/ - Button, Card, Badge
│   ├── components/layout/ - Header, BottomNav
│   ├── components/aksara/ - AksaraCard, etc
│   ├── lib/api.ts - Typed fetch
│   └── lib/store.ts - Zustand
├── branding/ - Logo, colors, etc
└── docker-compose.yml
```

## 🚀 Quick Start (tanpa Docker)

Cara paling mudah untuk menjalankan Aksara adalah launcher satu-perintah. Ia
membuat virtual environment lokal (`.venv`), memasang dependensi backend, lalu
membangun UI dan menjalankan aplikasi pada satu alamat.

**Syarat wajib:** Python 3.10 atau lebih baru. Tidak ada dependensi Python yang
akan dipasang secara global.

```bash
# Linux / macOS
./run.sh

# Windows (double-click atau dari Command Prompt / PowerShell)
run.bat

# Alternatif di semua platform
python run.py
# Windows jika perintah `python` tidak ada di PATH:
py -3 run.py
```

Pada first run, buka **http://localhost:8000** setelah launcher selesai.
Dokumentasi API tersedia di **http://localhost:8000/docs**.

> **Catatan Windows:** `run.bat` mencoba `py -3`, `python3`, `python`, lalu
> interpreter `.venv` secara otomatis. Jadi Python yang sudah terpasang lewat
> Python Launcher tidak akan keliru dilaporkan sebagai “Python tidak ditemukan”.

Node.js 18+ diperlukan hanya untuk membangun UI dari source. Jika Node.js belum
ada, API tetap berjalan dan launcher dapat melayani UI yang telah dibuild
sebelumnya. Instal Node.js dari https://nodejs.org jika ingin menjalankan UI
pada clone baru atau mengubah frontend.

### Perintah launcher

```bash
python run.py --check          # periksa Python, Node, .venv, dan UI
python run.py --build          # paksa build ulang UI statis, lalu jalankan
python run.py --backend-only   # hanya FastAPI / API (Node tidak dibutuhkan)
python run.py --dev            # FastAPI + Next.js dev server dengan hot reload
python run.py --port 9000      # jalankan aplikasi pada port lain
python run.py --reinstall      # pasang ulang dependensi Python di .venv
./install.sh                   # siapkan semuanya tanpa menjalankan server
# Windows: install.bat
```

Mode biasa menyajikan UI dan API dari port yang sama (`8000`), sehingga browser
selalu memanggil API melalui `/api` pada origin yang sama. Pada mode `--dev`,
UI Next.js berada di `http://localhost:3000` dan API berada di
`http://localhost:8000`; proxy Next.js tetap meneruskan `/api` ke backend.

### Menjalankan manual (opsional)

```bash
# Backend
cd backend
python -m venv ../.venv
../.venv/bin/python -m pip install -r requirements.txt
../.venv/bin/python -m uvicorn app.main:app --reload --port 8000

# Frontend (terminal lain)
cd frontend
npm install
npm run dev
```

### Docker (opsional)

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
