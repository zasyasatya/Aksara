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
- Tipe: pilihan ganda, benar/salah, gantungan choice, **menulis aksara** (murid menulis kata dari soal, divalidasi otomatis + skor kemiripan), susun kalimat
- Filter tipe soal di halaman kuis + **keyboard virtual** untuk menulis aksara
- Feedback detail: jelaskan kesalahan (misal: "Seharusnya pakai gantungan, bukan adeg-adeg")
- Endpoint `/api/quiz/validate-pair` untuk validasi custom

### ✍️ Panel Guru (`/guru`)
- Guru **menambah / mengubah / menghapus** materi, kuis, dan kamus langsung dari peramban — **tanpa edit file**
- Tab **Materi** (judul, level, urutan, aksara, kuis terkait), **Kuis** (semua tipe termasuk *menulis aksara*), **Kamus** (kata khusus transliterasi)
- Perubahan **langsung efektif** untuk murid (store JSON + reload per-request, tanpa restart)
- Mode DEV: langsung terbuka. Mode PROD: login dengan username & password (`AKSARA_GURU_USERNAME`/`AKSARA_GURU_PASSWORD`, akun admin juga diterima)

### 🖼️ Studio Twibbon
- **Foto + tulisan Aksara Bali** dalam satu gambar: tulis Latin → otomatis jadi aksara (engine translate), atau paste aksara langsung
- **10 bingkai twibbon** (margin krem, garis ganda, garis titik, gradasi saffron, gradasi cokelat, sudut klasik, strip aksara “warisan”, polaroid, sudut bulat, polos)
- 3 rasio (4:5 post IG, 1:1, 9:16 story/reels); kontrol ukuran, posisi, warna, bayangan, dan teks Latin
- Ekspor **PNG 1080px** + **share langsung ke medsos** (Web Share API) + salin ke clipboard
- **Branding organik**: watermark `aksara.id` (bisa dimatikan) + teks share otomatis berisi link & hashtag
- Setiap twibbon yang dibuat tercatat di penghitung publik (`POST /api/stats/twibbon`)

### 🏫 Program Sekolah & Sanggar (`/sekolah`)
- Halaman kemitraan sekolah/sanggar/pasraman: penjelasan **Pergub Bali 7/2026** (Bahasa & Aksara Bali wajib, min. 2 JP/minggu), daftar sekolah mitra, dan **formulir pendaftaran** publik
- Pendaftaran terekam di backend dan tampil langsung di daftar mitra (status “Verifikasi berjalan” → “Terverifikasi”)
- **Penghitung jujur** (`GET /api/stats`): kunjungan + twibbon dibuat, rate-limited per IP (20 dtk) agar angka kredibel

### 📚 Dokumentasi, Panel Guru & Panel Admin
- **`/docs`** — pusat dokumentasi: tata cara penggunaan untuk **murid, guru, admin**, plus halaman khusus **Metode Scientific & Referensi** (metodologi transliterasi + sumber akademik) — lengkap dengan screenshot halaman
- **`/guru`** — panel guru: kelola konten (materi/kuis/kamus) secara real-time
- **`/admin`** — panel admin: atur halaman dokumentasi mana yang **go public**
- **Mode DEV** (`AKSARA_MODE=dev`): semua halaman dokumentasi selalu tampil, akses admin & guru otomatis
- **Mode PROD** (`AKSARA_MODE=prod`): hanya halaman publik yang tampil; admin & guru login via username + password (`AKSARA_ADMIN_USERNAME`/`AKSARA_ADMIN_PASSWORD` dan `AKSARA_GURU_USERNAME`/`AKSARA_GURU_PASSWORD`)

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
- **Deployment:** Satu container (Docker) — UI statis disajikan FastAPI; siap untuk Coolify, Fly, Render, atau VPS

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
│   ├── TEST_PLAN.md - Testing strategy
│   ├── PAPER.md - Draft paper .id DeveloperDay 2026 (8 bagian wajib, Inggris)
│   ├── DEMO_SCRIPT.md - Skrip video demo 5 menit
│   └── slides/ - Deck slide (HTML 16:9, navigasi keyboard + speaker notes)
├── backend/
│   ├── app/
│   │   ├── main.py - FastAPI app
│   │   ├── core/config.py
│   │   ├── data/ - aksara_master.json, lessons, quiz, dictionary, engagement.json
│   │   ├── services/
│   │   │   ├── transliterator.py - CORE advanced engine (800+ lines)
│   │   │   ├── classifier.py
│   │   │   ├── quiz_engine.py - check_answer + validate_pair (termasuk tipe write_aksara)
│   │   │   └── data_store.py - store JSON terpusat (mampu ditulis ulang, reload per-request)
│   │   ├── routers/ - translate, classify, lessons, quiz, docs, manage, engagement
│   │   ├── schemas/ - Pydantic models (termasuk manage.py)
│   │   └── tests/ - pytest
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx - Landing (+ penghitung kunjungan live & CTA sekolah)
│   │   ├── sekolah/ - Program kemitraan sekolah & sanggar (form + daftar mitra)
│   │   ├── dashboard/ - Dashboard progress
│   │   ├── learn/ - Belajar bertahap
│   │   ├── translate/ - Translate dua arah + keyboard aksara
│   │   ├── quiz/ - Kuis validasi (filter tipe + menulis aksara)
│   │   ├── playground/ - Keyboard virtual
│   │   ├── docs/ - Pusat dokumentasi (hub + [slug])
│   │   ├── guru/ - Panel guru (Materi/Kuis/Kamus)
│   │   ├── twibbon/ - Studio Twibbon (canvas + share medsos)
│   │   └── admin/ - Panel admin (publikasi dokumentasi)
│   ├── components/docs/ - Shell, konten per-role, screenshot
│   ├── components/guru/ - Form & helper panel guru (BaliInput, dll)
│   ├── components/ui/ - Button, Card, Badge
│   ├── components/layout/ - Header, BottomNav
│   ├── components/aksara/ - AksaraCard, AksaraKeyboard (keyboard virtual bersama)
│   ├── lib/api.ts - Typed fetch (termasuk manage.* + sesi login guru/admin)
│   ├── lib/store.ts - Zustand
│   ├── public/screenshots/ - Screenshot halaman (untuk dokumentasi)
│   └── public/sample/ - Foto contoh untuk Studio Twibbon
├── branding/ - Logo, colors, etc
├── Dockerfile - Multi-stage (build UI statis → runtime FastAPI menyajikan UI+API di :8000)
├── .dockerignore
└── docker-compose.yml - single-service + volume persistensi
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

### Docker (satu container, satu origin)

UI statis (hasil build Next.js) disajikan **oleh FastAPI** di port yang sama, jadi
browser selalu memanggil `/api` pada origin yang sama — tanpa CORS, tanpa host yang
terkunci. Ini juga bentuk yang paling mudah di-deploy (Coolify, Fly, Render, VPS).

```bash
docker compose up --build
# Buka http://localhost:8000  (UI + API di satu port)
```

Variabel lingkungan:

| Var | Default | Keterangan |
| --- | --- | --- |
| `AKSARA_MODE` | `prod` | `prod` = hanya docs publik + admin/guru butuh login; `dev` = semua terbuka |
| `AKSARA_ADMIN_USERNAME` | `admin` | Username login admin (panel `/admin`) |
| `AKSARA_ADMIN_PASSWORD` | `aksara-admin` | **Wajib diganti** di produksi (panel `/admin`) |
| `AKSARA_GURU_USERNAME` | `guru` | Username login guru (panel `/guru`) |
| `AKSARA_GURU_PASSWORD` | `aksara-guru` | **Wajib diganti** di produksi (panel `/guru`) |

Persistensi: mount volume di `/app/backend/app/data` agar perubahan Panel Guru dan
engagement (kunjungan/twibbon/sekolah) tidak hilang saat redeploy.

#### Deploy ke Coolify

1. Buat **Project** → **Add Resource** → pilih **Dockerfile** (bukan Docker Compose,
   karena sudah single-service).
2. Sumber: repo ini; Coolify otomatis memakai `Dockerfile` di root dan `.dockerignore`.
3. **Port / domain**: set port internal **`8000`** (bukan 3000). Tautkan domain
   (mis. `aksara.id`) — Coolify menangani reverse-proxy & TLS.
4. **Environment**: set `AKSARA_ADMIN_USERNAME`/`AKSARA_ADMIN_PASSWORD` dan
   `AKSARA_GURU_USERNAME`/`AKSARA_GURU_PASSWORD` (password kuat).
   `AKSARA_MODE` default sudah `prod`.
5. **Persistence** (opsional, disarankan): tambah volume/bind-mount ke
   `/app/backend/app/data`.
6. **Deploy**. Cek health di `https://aksara.id/api/health` (healthcheck terpasang
   di image).

> Catatan: build image mengambil beberapa menit (stage Node membangun static export,
> lalu stage Python). Hasil akhirnya satu image kecil (python:3.11-slim + UI statis).

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

### Engagement & Statistik (penghitung jujur)

```bash
# Statistik publik: kunjungan, twibbon, daftar sekolah mitra
curl http://localhost:8000/api/stats

# Catat kunjungan (dipanggil otomatis landing; rate-limit 20 dtk/IP)
curl -X POST http://localhost:8000/api/stats/visit

# Catat twibbon dibuat (dipanggil studio saat unduh/share)
curl -X POST http://localhost:8000/api/stats/twibbon

# Daftar & daftarkan sekolah
curl http://localhost:8000/api/stats/schools
curl -X POST http://localhost:8000/api/stats/schools \
  -H "Content-Type: application/json" \
  -d '{"school":"SMP Negeri 1 Gianyar","region":"Gianyar","students":600,"contact":"guru@sekolah.sch.id"}'
```

## 📚 Dokumentasi, Admin & Mode Dev/Prod

Buka **`/docs`** (menu Dokumentasi) untuk panduan penggunaan per peran
(murid/guru/admin) dan halaman **Metode Scientific & Referensi**,
**`/guru`** untuk mengelola konten (materi, kuis, kamus), serta **`/admin`**
untuk mengatur publikasi halaman dokumentasi.

```bash
# Login (mode prod): dapatkan session token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"role":"admin","username":"admin","password":"aksara-admin"}'
# → {"ok":true,"session_token":"..."} — simpan ke $SESSION

# Daftar halaman dokumentasi (field mode + is_admin menentukan tampilan)
curl http://localhost:8000/api/docs/pages

# Ubah status publik/privat (admin only)
curl -X PATCH http://localhost:8000/api/docs/pages/metode-scientific/visibility \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION" \
  -d '{"is_public": false}'
```

### Variabel lingkungan

| Var | Default | Keterangan |
| --- | --- | --- |
| `AKSARA_MODE` | `dev` | `dev` = semua halaman docs tampil + admin & guru otomatis; `prod` = hanya halaman publik, admin & guru butuh login |
| `AKSARA_ADMIN_USERNAME` | `admin` | Username login admin untuk mode prod. |
| `AKSARA_ADMIN_PASSWORD` | `aksara-admin` | Password admin. **Wajib diganti di produksi.** |
| `AKSARA_GURU_USERNAME` | `guru` | Username login guru untuk mode prod. |
| `AKSARA_GURU_PASSWORD` | `aksara-guru` | Password guru (akun admin juga diterima di panel guru). **Wajib diganti di produksi.** |

Status publikasi disimpan di `backend/app/data/docs.json`. Konten dinamis
(materi, kuis, kamus) dikelola lewat panel guru dan disimpan di
`backend/app/data/lessons.json`, `quiz.json`, dan `dictionary.json`.

### Manage API (Panel Guru)

```bash
# Status akses (mode + is_guru + is_admin)
curl http://localhost:8000/api/manage/status

# Tambah materi (mode prod: butuh header sesi login)
curl -X POST http://localhost:8000/api/manage/lessons \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION" \
  -d '{"title":"Ha Na Ca Ra Ka","level":1,"order":1,"category":"wresastra","aksara_ids":[],"pangangge_ids":[],"estimated_minutes":10,"xp_reward":50,"prerequisites":[],"quiz_ids":[],"is_published":true}'

# Tambah kuis tipe "menulis aksara"
curl -X POST http://localhost:8000/api/manage/quizzes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION" \
  -d '{"lesson_id":"wresastra-01","type":"write_aksara","difficulty":"easy","question":{"text":"Tuliskan kata \"ha\" dalam Aksara Bali","latin":"ha","bali":"ᬳ"},"options":[],"correct_answer":"","explanation":"ha = aksara pertama Wresastra 18","xp":10}'

# Upsert entri kamus
curl -X POST http://localhost:8000/api/manage/dictionary \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION" \
  -d '{"latin":"angklung","bali":"ᬅᬋ᭄ᬓᬮᬸ","note":"A independent"}'
```

Endpoint lengkap: `GET/POST /api/manage/lessons`, `GET/PUT/DELETE /api/manage/lessons/{id}`,
`GET/POST /api/manage/quizzes`, `GET/PUT/DELETE /api/manage/quizzes/{id}`,
`GET/POST /api/manage/dictionary`, `DELETE /api/manage/dictionary/{latin}`,
`GET /api/manage/aksara`.

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
- **PAPER.md** — draft paper .id DeveloperDay 2026 (8 bagian wajib; bahasa Inggris; data background pelestarian budaya)
- **DEMO_SCRIPT.md** + **slides/** — skrip & deck video demo 5 menit (buka `docs/slides/index.html` di browser)

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
