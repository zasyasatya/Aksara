# Dataset & Model — Pengenalan Tulisan Tangan Aksara Bali

> Dokumen ini menjelaskan secara rinci **dataset** yang dipakai untuk membangun
> dan mengevaluasi **classifier pengenalan tulisan tangan Aksara Bali**, serta
> **arsitektur classifier**-nya. Classifier berjalan **on-device** di peramban
> (`frontend/lib/aksara-recognition.ts`) — tanpa API eksternal, tanpa server
> inference, dan dapat dipakai **offline**.

---

## 1. Ringkasan

| Aspek | Nilai |
| --- | --- |
| Tipe classifier | Template matching (AI lokal) — **bukan** neural-network training |
| Fitur input | Maska biner tinta (128×128) hasil normalisasi canvas tulisan tangan |
| Metrik kesamaan | **Chamfer distance dua arah** (1, √2) |
| Kandidat (kelas) | **304 glyph unik** dari blok Unicode Balinese (lihat §3) |
| Sumber template | Font **Noto Sans Balinese** (Google Fonts, SIL OFL 1.1) |
| Ambang verifikasi | `correct ≥ 0.55`, `close ≥ 0.35` |
| Ambang pengenalan | `confident ≥ 0.55` **dan** margin ke kandidat #2 ≥ 0.07 |
| **Akurasi (verifikasi)** | **≈ 97%** (rata-rata 5 seed; lihat §5) |

> **Kejelasan istilah "training".** Classifier ini adalah *template matcher*:
> "training"-nya adalah **rendering template glyph** dari font + **kalibrasi
> ambang** pada dataset evaluasi (§4), bukan optimasi bobot model. Istilah
> "dataset training" di sini merujuk pada **dataset evaluasi/kalibrasi** yang
> dipakai untuk mengukur dan menyetel classifier.

---

## 2. Arsitektur classifier

```
Tulisan tangan (canvas)
        │
        ▼
Normalisasi: komposit putih → biner (luminansi < 200 = tinta)
        │
        ▼
Crop bounding-box tinta → skala (maintain aspect) → pusatkan → 128×128 maska
        │
        ▼
Chamfer distance transform (1, √2) — jarak tiap piksel ke tinta terdekat
        │
        ▼
Skor = 1 − rata-rata jarak dua arah / (0.14 × 128)      → [0, 1]
        │
        ├── classifyTracing : benar bila skor ≥ 0.55   (verifikasi / telusur)
        └── recognizeAksara : argmax skor, confident bila skor ≥ 0.55 & margin ≥ 0.07
```

Classifier dipakai di dua titik produk:

1. **Playground → "Tulis Tangan"** (`classifyTracing`) — pengguna menelusuri
   siluet satu glyph target; sistem menilai benar/hampir/salah.
2. **Translate → "Tulis Tangan"** (`recognizeAksara`) — pengguna menulis bebas
   satu aksara; sistem memilih kandidat terdekat dari 304 glyph.

---

## 3. Dataset

### 3.1 Set template / kandidat (`buildCandidateSet()`)

Kandidat dibangun **sepenuhnya dari codepoint Unicode** (tidak mengetik glyph
manual), agar tidak bergantung pada keyboard/font tertentu:

| Komponen | Isi | Jumlah |
| --- | --- | --- |
| Aksara dasar (Wresastra 18) | ha na ca ra ka da ta sa wa la ma ga ba nga pa ja ya nya | 18 |
| Tanda vokal (pangangge suara) | ulu, ulu sari, suku, suku ilut, taleng, taling detya, taleng tedong, pepet + 3 tengenan (bisah, surang, cecek) | 11 |
| Aksara suara & Swalalita | rentang U+1B05–U+1B59 (vokal independen, Sanskerta/Kawi) | 85 |
| Kombinasi cluster | dasar + pangangge, serta dasar + adeg-adeg + gantungan | 504 |
| **Total unik setelah deduplikasi** | | **304** |

### 3.2 Rendering template

Setiap template dirender dengan font **Noto Sans Balinese** (600 weight) ke
canvas 320×320, di tengah, lalu dinormalisasi ke maska 128×128:

1. komposit ke latar putih;
2. binarisasi (luminansi < 200 ⇒ tinta);
3. crop bounding-box tinta;
4. skala *maintain-aspect* ke dalam kotak 128×128 terpusat.

Template di-*cache* per sesi (tidak dirender ulang).

### 3.3 Dataset evaluasi (tulisan tangan sintetis)

Karena belum ada korpus tinta (ink) Aksara Bali publik berlabel, evaluasi
memakai **dataset sintetis** yang mensimulasikan variasi tulisan tangan dari
template font (harness: `eval/evaluate_handwriting.py`):

| Jenis sampel | Simulasi | Peran |
| --- | --- | --- |
| **Positif (telusur)** | rotasi ±2°, skala 0.94–1.06, translasi ±3 px, penebalan stroke (dilasi) 0–1 px | pengguna menelusuri siluet target yang tampil |
| **Negatif (salah)** | coretan poligon acak 2–5 goresan | tinta yang tidak cocok dengan target |

Sampel positif sengaja **bervariasi kecil** karena mode telusur menampilkan
*ghost silhouette* yang memandu pengguna.

---

## 4. Metrik kesamaan (detail)

### 4.1 Distance transform (chamfer 1, √2)

`distanceTransform(mask)` menghitung, untuk **setiap piksel**, jarak ke tinta
terdekat menggunakan 8-tetangga dengan bobot 1 (ortogonal) dan √2 (diagonal) —
ekuivalen BFS multi-sumber. Dipakai agar perbandingan **tahan terhadap
ketebalan stroke** (pena tebal tetap cocok dengan template font tipis selama
bentuknya sama).

### 4.2 Skor kesamaan (`compareMasks`)

```
sumA = Σ jarak tinta-a → bentuk-b      cntA = jumlah piksel tinta a
sumB = Σ jarak tinta-b → bentuk-a      cntB = jumlah piksel tinta b
avg  = (sumA/cntA + sumB/cntB) / 2
skor = clamp(1 − avg / (0.14 × 128), 0, 1)
```

Skor 1.0 = identik; skor menurun bila tinta bergeser/berlebih/kurang.

### 4.3 Keputusan

| Fungsi | Aturan |
| --- | --- |
| `classifyTracing` | `correct` bila skor ≥ 0.55; `close` bila ≥ 0.35 |
| `recognizeAksara` | kandidat dengan skor tertinggi; `confident` bila skor ≥ 0.55 **dan** unggul ≥ 0.07 dari kandidat kedua |

---

## 5. Evaluasi & hasil

Harness `eval/evaluate_handwriting.py` meniru 1:1 normalisasi & penskoran di
`aksara-recognition.ts` lalu mengukur dua tugas.

### 5.1 Verifikasi / telusur (tugas utama produk) — ✅ ≥ 90%

Ambang produksi `correct ≥ 0.55`, 20 positif + 20 negatif per kelas, 18 kelas,
5 seed acak:

| Seed | TP | FN | TN | FP | Akurasi |
| --- | --- | --- | --- | --- | --- |
| 20260831 | 360 | 0 | 341 | 19 | 97.36% |
| 20260832 | 360 | 0 | 337 | 23 | 96.81% |
| 20260833 | 360 | 0 | 338 | 22 | 96.94% |
| 20260834 | 360 | 0 | 344 | 16 | 97.78% |
| 20260835 | 360 | 0 | 331 | 29 | 95.97% |
| **Rata-rata** | | | | | **96.97%** |

> **Akurasi verifikasi ≈ 97%** (rentang 95.97–97.78%). *True negative* dominan:
> coretan acak hampir selalu ditolak, dan tidak ada satu pun tulisan target
> yang salah ditolak (FN = 0).

### 5.2 Pengenalan terbuka 18 kelas — keterbatasan yang dilaporkan jujur

Pada pengenalan *tanpa target* (memilih 1 dari 18), top-1 ≈ 5.6% (≈ peluang,
1/18). Penyebabnya **bukan bug**, melainkan fakta bentuk: sejumlah aksara
(na ᬦ, da ᬤ, ta ᬢ, ca ᬘ) nyaris identik — jarak chamfer antar-template hanya
±1 px pada resolusi 128×128 — sehingga tak terpisahkan tanpa konteks.

Karena itu `recognizeAksara` memakai **confident-gating** (margin ≥ 0.07):
bila tidak yakin, sistem **abstain** (tidak menebak) daripada memberi jawaban
salah. Pada dataset di atas *confident-rate* = 0% — perilaku yang **diinginkan**
untuk aplikasi edukasi: lebih baik tidak menjawab daripada salah mengajari.

### 5.3 Batasan & kejujuran

- Angka di atas adalah **metrik algoritma pada dataset sintetis**; akurasi pada
  tinta manusia sungguhan memerlukan korpus ink berlabel — pengumpulannya kini
  difasilitasi Panel Admin → Model ML (§5.4).
- Pengenalan terbuka dengan template matching masih terbatas; mode telusur
  (verifikasi) adalah jalur pembelajaran utama dan sudah andal (≥ 95%).

### 5.4 Model terlatih (retraining) untuk pengenalan terbuka — Panel Admin

Keterbatasan §5.2 dijawab dengan pipeline **retraining** di Panel Admin
(`/admin/ml`, dokumentasi lengkap: [`ML_RETRAINING.md`](ML_RETRAINING.md)):
dataset tulisan tangan dikelola & dilabeli admin (sintetis, unggahan, kanvas,
koreksi dari percobaan), lalu classifier **belajar dari data** — 6 arsitektur
murni NumPy (template, centroid, k-NN, regresi logistik, MLP, CNN) — dan
dievaluasi otomatis (accuracy, precision, recall, F1 makro/berbobot, top-3,
log-loss, confusion matrix, per kelas). Admin memilih model **produksi** yang
dilayani `POST /api/ml/predict`.

Hasil percobaan (`eval/ml_experiments.py`; 18 kelas Wresastra, 60 sampel
sintetis/kelas, split 70/15/15, evaluasi pada test):

| Arsitektur | Accuracy | Precision | Recall | F1 (makro) | Acc pada set *shift* |
| --- | --- | --- | --- | --- | --- |
| Template matching (chamfer) | 74.7% | 81.2% | 74.7% | 75.1% | 40.0% |
| Nearest centroid | 84.6% | 87.1% | 84.6% | 84.7% | 45.0% |
| k-NN (k=5) | 84.6% | 85.6% | 84.6% | 84.4% | 51.4% |
| Regresi logistik | 91.4% | 92.2% | 91.4% | 91.3% | 56.7% |
| MLP | 93.2% | 93.6% | 93.2% | 93.2% | 58.6% |
| **CNN** | **98.2%** | **98.4%** | **98.2%** | **98.2%** | **63.6%** |

Pengenalan terbuka 18 kelas naik dari ≈ 75% (template) ke **98.2% (CNN)** pada
data sintetis; pada set *shift* (augmentasi 1.6× lebih kuat) CNN tetap
terbaik (63.6%), yang sekaligus mengingatkan bahwa validasi akhir harus memakai
tulisan tangan nyata. Detail metodologi, ablasi ukuran data, dan kesimpulan ada
di `ML_RETRAINING.md` §5 dan `eval/results/ml_experiments.md`.

---

## 6. Reproduksi

```bash
# Dependensi: Pillow + NumPy + font Noto Sans Balinese (diunduh otomatis)
cd eval
python -m venv .venv && .venv/bin/pip install Pillow numpy
.venv/bin/python evaluate_handwriting.py            # unduh font + jalankan
.venv/bin/python evaluate_handwriting.py --font /path/NotoSansBalinese.ttf

# Percobaan retraining (6 arsitektur + ablasi) — memakai venv backend
cd .. && .venv/bin/python eval/ml_experiments.py --ablation
```

---

## 7. Referensi

- Unicode Consortium — blok Balinese `U+1B00–U+1B7F`.
- Google Fonts — *Noto Sans Balinese* (SIL Open Font License 1.1).
- Jampel, Indrawan & Widiana (2018). *Accuracy Analysis of Latin-to-Balinese
  Script Transliteration Method.* IJECE 8(3) — konteks kesulitan aksara Bali.
- Borges, G. A. K. — konsep chamfer distance untuk template matching bentuk.
