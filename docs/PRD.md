# PRD - Aksara Platform: Platform Belajar Aksara Bali

**Version:** 1.0.0  
**Date:** 2026-08-29  
**Product:** Aksara - Platform Digital Pelestarian Aksara Bali  
**Tagline:** "Melestarikan Warisan, Menulis Masa Depan" / "Ngajegang Warisan, Nyurat Masa Depan"

---

## 1. Executive Summary

Aksara adalah platform edukasi interaktif untuk mempelajari Aksara Bali (Hanacaraka Bali) dengan pendekatan modern, gamified, dan berbasis teknologi transliterasi canggih. Platform ini menjembatani kesenjangan antara generasi muda dan warisan budaya Bali melalui pengalaman belajar yang intuitif di desktop dan mobile.

### Problem Statement
- Penurunan drastis pengguna Aksara Bali di kalangan generasi muda (<15% bisa membaca)
- Tidak ada platform digital komprehensif dengan validasi penulisan yang akurat
- Sumber belajar tersebar, tidak terstruktur, dan tidak interaktif
- Kompleksitas gantungan, pangangge, dan klasifikasi yang membingungkan tanpa panduan sistematis

### Solution
Platform web all-in-one dengan:
- Transliterasi Latin ↔ Aksara Bali dengan akurasi tinggi (meng-handle gantungan, gempelan, pangangge)
- Sistem quiz validasi penulisan otomatis
- Dashboard progress & gamification
- Design system yang mengangkat estetika Bali modern

---

## 2. Goals & Objectives

### Business Goals
- Menjadi platform #1 belajar Aksara Bali di Indonesia dalam 12 bulan
- 10.000+ MAU dalam 6 bulan
- Partnership dengan 50+ sekolah di Bali

### User Goals
- Mampu membaca Aksara Bali dasar dalam 2 minggu
- Mampu menulis kalimat sederhana dalam 1 bulan
- Memahami aturan gantungan & pangangge secara mendalam

### Success Metrics
- **Learning:** 80% completion rate modul dasar
- **Accuracy:** >95% akurasi transliterasi
- **Engagement:** 30+ menit/session, 3+ session/minggu
- **Retention:** 60% D7, 40% D30

---

## 3. Target Users

### Primary: Siswa (13-25 tahun) - "Putu"
- Pelajar SMP/SMA di Bali & diaspora Bali
- Tech-savvy, mobile-first
- Motivasi: tugas sekolah, identitas budaya, kebanggaan
- Pain: bosan dengan buku, tidak ada feedback instan

### Secondary: Guru & Pengajar Budaya - "Ibu Ayu"
- Guru Bahasa Bali, budayawan
- Butuh alat ajar interaktif
- Motivasi: memudahkan pengajaran, monitoring murid

### Tertiary: General Public & Researcher - "Wayan"
- Pecinta budaya, turis, akademisi
- Motivasi: eksplorasi budaya, penelitian

---

## 4. Features & Requirements

### 4.1 Core Features (MVP)

#### F1: Translate Engine (P0 - Critical)
**Deskripsi:** Translasi dua arah Latin ↔ Aksara Bali dengan handling kompleks.

**Requirements:**
- Latin → Bali: parsing suku kata, deteksi vokal inheren /a/, penanganan gantungan (cluster konsonan), gempelan (pa, sa, sa sapa), pangangge suara (ulu, suku, taleng, pepet, dll), pangangge tengenan (bisah, surang, cecek, adeg-adeg), pangangge aksara (cakra, nania, suku kembung)
- Bali → Latin: parsing Unicode U+1B00-U+1B7F, reverse mapping, deteksi adeg-adeg untuk kill vowel
- Support Wresastra 18 aksara + Swalalita 33 aksara
- Akurasi >95% pada kata umum, >90% pada kalimat kompleks
- API latency <200ms

**Advanced Approach:**
- Rule-based engine + dictionary untuk kata khusus (Angklung, dll)
- State machine untuk syllable segmentation
- Context-aware gantungan vs adeg-adeg (tumpuk telu prohibition)
- Handling special: Ha tidak selalu dibaca, kombinasi Ra+Pepeet forbidden, dll.

**User Story:**
> Sebagai Putu, saya ingin mengetik "Om Swastyastu" dan langsung melihat ᬑᬁ ᬲ᭄ᬯᬲ᭄ᬢ᭄ᬬᬲ᭄ᬢᬸ agar bisa copy untuk bio Instagram.

#### F2: Learn Module / Dashboard (P0)
- Dashboard dengan progress tracking, streak, XP
- Modul bertahap:
  - Level 1: Wresastra 18 (Ha Na Ca Ra Ka...)
  - Level 2: Pangangge Suara (Ulu, Suku, Taleng, Pepet...)
  - Level 3: Pangangge Tengenan (Bisah, Surang, Cecek, Adeg-adeg)
  - Level 4: Gantungan & Gempelan (advanced cluster)
  - Level 5: Swalalita & Modre
  - Level 6: Kalimat & Pupuh
- Setiap aksara: visual, cara tulis (stroke order), audio pelafalan, contoh kata
- Responsive: mobile card swipe, desktop grid

#### F3: Quiz & Validation Engine (P0)
**Deskripsi:** Murid menulis aksara, sistem validasi apakah benar sesuai soal.

**Types:**
- **Pilihan Ganda:** Latin → pilih Aksara yang benar (4 opsi)
- **Tulis Balik:** Diberi Latin, murid susun Aksara dari keyboard virtual Aksara Bali
- **Visual Validation:** Diberi gambar aksara tulisan tangan? MVP: pilih benar/salah untuk pasangan Latin-Bali
- **Gantungan Challenge:** Diberi kata dengan cluster, pilih gantungan yang tepat
- **Sentence Builder:** Susun kalimat dari kata acak

**Validation Logic:**
- Normalisasi Unicode (NFC)
- Perbandingan canonical form
- Toleransi untuk varian (misal: Ha Na Ca Ra Ka order)
- Feedback: jelaskan kesalahan (misal: "Seharusnya pakai gantungan, bukan adeg-adeg")
- Scoring: XP, streak, leaderboard

#### F4: Aksara Keyboard & Playground (P1)
- Virtual keyboard Aksara Bali (Wresastra, pangangge, angka)
- Canvas untuk latihan tulis (freehand dengan panduan)
- Copy & share

### 4.2 Secondary Features (Post-MVP)

- **F5: Community & Dictionary:** Kamus Bali-Indonesia dengan aksara, user submission
- **F6: OCR (Future):** Foto tulisan Aksara Bali → Latin (ML model)
- **F7: Gamification:** Badge (Penjaga Aksara, Puja Sastra), Leaderboard sekolah
- **F8: Guru Dashboard:** Buat soal custom, monitoring kelas
- **F9: Offline PWA & Mobile App**

---

## 5. User Flows

### Flow 1: First Time Learning
1. Landing → CTA "Mulai Belajar"
2. Onboarding: pilih level (pemula/menengah), tujuan
3. Dashboard → Level 1: Ha Na Ca Ra Ka
4. Learn card: lihat aksara ᬳ = Ha, dengar audio, lihat stroke
5. Quiz mini: pilih yang = Ha
6. Progress +10 XP, unlock next aksara
7. Streak notification

### Flow 2: Translate
1. Header → "Translate"
2. Input Latin: "bali"
3. Real-time transliterasi: ᬩᬮᬶ
4. Tampilkan breakdown: ba + la + ulu (i)
5. Copy, share, atau "Pelajari lebih lanjut" → link ke modul terkait (La + Ulu)
6. Toggle Bali→Latin: paste ᬩᬮᬶ → "bali"

### Flow 3: Quiz Validation
1. Dashboard → "Tantangan Harian"
2. Soal: "Apakah ᬓᬭᬗ᭄ᬓᬸᬂ benar untuk 'karangkung'?"
3. Murid: pilih Benar/Salah + alasan
4. Jika salah, sistem tunjukkan yang benar: ᬓᬭᬗ᭄ᬓᬸᬂ dengan penjelasan gantungan Ka
5. XP & feedback

---

## 6. Design System Requirements

### Brand Personality
- **Modern Heritage:** Menghormati tradisi, tapi tidak kuno
- **Warm & Approachable:** Ramah untuk Gen Z
- **Educational but Fun:** Serius belajar, tapi playful
- **Authentic:** Tidak mengada-ada, akurat secara budaya

### Visual Direction (from image reference)
Diasumsikan design system menggunakan:
- Warna earthy: Saffron, Terracotta, Deep Brown, Cream, Sage
- Tipografi: Sans modern untuk UI, Noto Sans Balinese untuk aksara
- Bentuk: Rounded, organik, terinspirasi ukiran Bali
- Iconography: Minimal, dengan aksen tradisional

**Detail ada di BRANDING.md**

### Responsive
- Mobile-first: bottom nav, swipe cards, large tap targets (48px)
- Desktop: sidebar nav, 2-panel layout (learn + playground), keyboard shortcuts

---

## 7. Technical Requirements

### Stack
- **Frontend:** Next.js 15 (App Router), TypeScript, Tailwind CSS, Framer Motion, Zustand
- **Backend:** FastAPI (latest), Python 3.11+, Pydantic v2, SQLAlchemy, SQLite/Postgres
- **Transliteration:** Custom rule engine (Python), dictionary JSON
- **Deployment:** Docker, Vercel (frontend), Fly.io/Render (backend) atau single VPS
- **Testing:** Pytest (backend), Vitest + Playwright (frontend)

### Performance
- LCP <2.5s, TTI <3s
- API p95 <300ms
- Support Noto Sans Balinese font loading optimization (subset)

### Accessibility
- WCAG 2.1 AA
- Keyboard navigable
- Screen reader untuk Latin, aria-label untuk Aksara

### Security
- No auth untuk MVP (local storage progress), JWT untuk future
- Rate limiting translate API
- Sanitization input (prevent XSS via Bali unicode)

---

## 8. Data Model (High Level)

- **Aksara:** id, latin, bali_unicode, bali_char, type (wresastra/swalalita/suara), description, example_words, gantungan_form, unicode_point
- **Pangangge:** id, name, type (suara/tengenan/aksara), latin_effect, bali_mark, position (above/below/front/behind), example
- **Lesson:** id, title, level, order, aksara_ids[], content, quiz_ids[]
- **Quiz:** id, type, question_latin, question_bali, options[], correct_answer, explanation, difficulty
- **UserProgress:** user_id (anon), lesson_id, completed, score, streak, xp

Full schema di DATABASE_DESIGN.md

---

## 9. Open Questions & Assumptions

- Q: Apakah perlu support Sasak extension? A: Post-MVP
- Q: Audio pelafalan dari mana? A: MVP pakai Web Speech API, future rekaman native speaker
- Q: Validasi tulisan tangan? A: MVP hanya validasi pilihan & susun, bukan OCR handwriting
- Assumption: User punya font Noto Sans Balinese installed atau kita serve via CDN

---

## 10. Milestones

- **Week 1:** Docs, Branding, Setup repo, Backend transliterator core, Frontend scaffolding
- **Week 2:** Translate API, Learn module UI, Quiz engine
- **Week 3:** Dashboard, gamification, responsive polish, testing
- **Week 4:** Beta launch, feedback, deployment

---

## 11. Appendix: Sumber Aksara Bali

- https://aksaradinusantara.com/fonta/aksara/bali
- Unicode Balinese U+1B00-U+1B7F
- Nala (2006) - Pedoman Aksara Bali
- LOC Romanization Table Balinese 2025
- Paper: Accuracy Analysis of Latin-to-Balinese Transliteration (IJECE)
- Wiki: Balinese Script - pangangge, gantungan, gempelan rules
  - Tumpuk telu prohibition (max 1 gantungan per base)
  - Cakra vs Guwung Macelek distinction
  - Pepet + Cakra forbidden combination

---

*Dokumen ini adalah living document, akan di-update seiring development.*
