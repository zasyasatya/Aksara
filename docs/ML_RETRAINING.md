# Retraining Model ML — Klasifikasi Aksara Bali (Panel Admin)

> Dokumen ini menjelaskan fitur **Model ML** di Panel Admin (`/admin` → *Buka
> panel ML*, route `/admin/ml`): manajemen dataset tulisan tangan, labeling,
> retraining classifier, laporan evaluasi lengkap (accuracy, precision, recall,
> F1, dst.), pemilihan arsitektur, pemilihan model produksi, serta hasil
> **percobaan (eksperimen)** yang sudah dijalankan.
>
> Fitur ini melengkapi classifier template-matching on-device yang dijelaskan di
> [`DATASET_MODEL.md`](DATASET_MODEL.md): model hasil retraining dilayani server
> lewat `POST /api/ml/predict` dan bisa dipakai untuk **pengenalan terbuka**
> (menebak 1 dari N aksara) — tugas yang tidak bisa diselesaikan template
> matching karena aksara mirip (na/da/ta/ca).

---

## 1. Ringkasan

| Aspek | Nilai |
| --- | --- |
| Lokasi UI | `/admin/ml` — tab **Dataset & Labeling**, **Training**, **Model & Evaluasi**, **Percobaan** |
| API | prefix `/api/ml` (lihat §7 dan `docs/API_SPEC.md`) — admin-only kecuali `status`, `predict`, gambar sampel |
| Runtime model | **Murni NumPy di CPU** (tanpa PyTorch/TensorFlow/scikit-learn) — cocok untuk container kecil |
| Fitur input | Tinta dinormalisasi (crop bbox → skala ke 20 px → pusat massa di 28×28) → vektor 784-d |
| Penyimpanan | `backend/app/data/ml/` (file JSON + PNG 64×64 + `model.npz`), ikut volume `backend/app/data` |
| Arsitektur | `template`, `centroid`, `knn`, `logreg`, `mlp`, `cnn` (6 pilihan) |
| Kelas default | 18 aksara Wresastra; bisa ditambah Swalalita, Suara, Angka (58 kelas tersedia) |
| Split | train/val/test 70/15/15, deterministik per sampel; "acak ulang split" = stratified per label |
| Evaluasi | Otomatis pada split **test** setelah setiap training (fallback val → train) |
| Model produksi | Satu model aktif dipilih admin → dipakai `POST /api/ml/predict` |

---

## 2. Alur kerja admin

```
Dataset & Labeling ──► Training ──► Model & Evaluasi ──► Percobaan
 (kumpulkan, label,     (pilih arsitektur,   (bandingkan metrik,    (uji tulisan nyata,
  atur split)            hyperparameter,      laporan per kelas,     bandingkan model,
                          jalankan job)        pilih produksi)        koreksi → dataset)
```

### 2.1 Dataset & Labeling

- **Sumber sampel**
  - *Generate sintetis*: glyph dirender dari font **Noto Sans Balinese**
    (`backend/app/assets/fonts/`, SIL OFL 1.1) dengan bobot font 400–700 lalu
    diaugmentasi (afinitas: rotasi/skala/shear/translasi, distorsi elastis,
    variasi tebal goresan, noise, putus goresan). Parameter: jumlah/kelas,
    seed, kekuatan augmentasi.
  - *Unggah gambar* (PNG/JPG, satu atau banyak, dengan/ tanpa label).
  - *Tulis di kanvas* langsung di panel admin (dengan siluet pemandu).
  - *Koreksi dari tab Percobaan* (prediksi salah → simpan dengan label benar).
- **Labeling**: sampel tanpa label masuk *antrean labeling*; admin memberi
  label satu per satu (dengan pratinjau) atau massal (pilih banyak → beri label
  / pindah split / tandai *review* / hapus).
- **Kelas aktif**: pilih kelas mana yang dilatih (mis. hanya Wresastra, atau
  tambah Angka). Statistik per kelas (train/val/test) dan peringatan kelas
  kosong ditampilkan sebelum training.
- **Split**: setiap sampel punya split tetap; tombol *Acak ulang split
  70/15/15* melakukan stratifikasi per label agar tiap kelas terwakili di test.

### 2.2 Training (retraining)

1. Pilih arsitektur (kartu berisi deskripsi, kelebihan/kekurangan).
2. Atur hyperparameter (form dibangkitkan dari spesifikasi arsitektur —
   epoch, learning rate, batch size, hidden units, dropout, weight decay, k, …).
3. Beri nama/catatan, centang *langsung jadikan model produksi* bila perlu.
4. **Mulai Retraining** → job berjalan di background thread server; UI polling
   tiap 1 detik: progress bar, kurva loss/akurasi train-val per epoch, tombol
   batal. Hanya satu job berjalan pada satu waktu (CPU-bound).
5. Setelah selesai model otomatis dievaluasi dan tersimpan ke registry.

### 2.3 Model & Evaluasi

Registry semua model terlatih (tabel bisa diurutkan) dengan metrik ringkas:
**accuracy, precision (makro), recall (makro), F1 (makro), train accuracy,
durasi latih, ukuran, tanggal**. Label *F1 terbaik* dan *overfit?* (train acc
− test acc > 15 pt) membantu memilih.

Klik baris → **laporan evaluasi lengkap**:

- Tile metrik: accuracy, precision/recall/F1 makro **dan** berbobot, top-3
  accuracy, log-loss, rata-rata confidence, *confident-rate* & akurasi pada
  prediksi confident, ukuran train/val/test, hyperparameter.
- Tabel **per kelas**: precision, recall, F1, support, TP/FP/FN.
- **Confusion matrix** interaktif (18×18) + daftar pasangan paling sering tertukar.
- **Kurva pelatihan** (loss, akurasi train vs val per epoch).
- Galeri **contoh salah klasifikasi** (gambar sampel test, label benar vs prediksi).

Aksi: *Jadikan produksi* / nonaktifkan, ubah nama & catatan, hapus model.

### 2.4 Percobaan

Tulis aksara di kanvas (atau unggah gambar) → prediksi dengan model pilihan
(default produksi), lihat top-k probabilitas, pratinjau fitur 28×28 yang
"dilihat" model, pilih *target aksara* untuk menghitung akurasi sesi. Tombol
**Bandingkan semua model** menjalankan input yang sama pada seluruh registry.
Prediksi salah bisa langsung **disimpan ke dataset** dengan label benar
(*human-in-the-loop*), lalu retraining ulang.

---

## 3. Arsitektur yang tersedia

| id | Nama | Keluarga | Catatan |
| --- | --- | --- | --- |
| `template` | Template Matching (Chamfer) | baseline non-parametrik | Sama dengan classifier on-device (`aksara-recognition.ts`), template = render font bersih; tidak belajar dari dataset → pembanding |
| `centroid` | Nearest Centroid | statistik klasik | Rata-rata piksel per kelas; instan |
| `knn` | k-Nearest Neighbours | instance-based | Voting k tetangga berbobot 1/jarak; model = seluruh data latih |
| `logreg` | Regresi Logistik (Softmax) | linear | 784→C, Adam + L2, mini-batch |
| `mlp` | Multi-Layer Perceptron | jaringan saraf | 784→hidden (ReLU, dropout)→C, Adam + L2 |
| `cnn` | Convolutional Neural Network | jaringan saraf konvolusi | conv3×3×8 → maxpool → conv3×3×16 → maxpool → FC-64 → softmax (im2col NumPy) |

Semua model punya antarmuka yang sama (`fit`, `predict_proba`, `save/load`)
di `backend/app/ml/models.py`; menambah arsitektur baru = satu kelas + satu
entri spesifikasi hyperparameter (form UI ikut otomatis).

---

## 4. Metrik evaluasi

Dihitung `backend/app/ml/metrics.py` dari confusion matrix pada split test:

- **Accuracy** = benar / total.
- **Precision_c** = TP_c / (TP_c + FP_c); **Recall_c** = TP_c / (TP_c + FN_c);
  **F1_c** = harmonik keduanya. Rata-rata **makro** (tiap kelas bobot sama;
  hanya kelas yang hadir di test) dan **berbobot** (bobot = support).
- **Top-3 accuracy**, **log-loss** (dari probabilitas), **mean confidence**,
  **confident-rate** (maks-prob ≥ 0.8) dan akurasi pada subset confident.
- **Train accuracy** dilaporkan untuk deteksi overfit.

---

## 5. Hasil percobaan (eksperimen nyata)

Percobaan dijalankan dengan `eval/ml_experiments.py`, yang memakai **kode
pipeline yang sama** dengan panel admin (dataset sintetis → `training` →
`metrics`) pada store sementara. Laporan lengkap (termasuk per-kelas & JSON
mentah) ada di [`eval/results/ml_experiments.md`](../eval/results/ml_experiments.md)
dan [`eval/results/ml_experiments.json`](../eval/results/ml_experiments.json).

**Setup**: 18 kelas Wresastra, 60 sampel sintetis/kelas = 1080 sampel, split
stratified 756/162/162, hyperparameter default panel admin, seed 20260904,
CPU 2 core (NumPy 2.4, Python 3.11). Uji **shift**: 360 sampel baru dengan
augmentasi 1.6× lebih kuat dan seed berbeda (mensimulasikan tulisan yang lebih
"liar" daripada data latih).

### 5.1 Benchmark arsitektur (split test)

| Arsitektur | Accuracy | Precision | Recall | F1 (makro) | Top-3 | Log-loss | Train acc | Acc (shift) | F1 (shift) | Latih | Param | Ukuran |
| :-- | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| Template Matching (`template`) | 74.7% | 81.2% | 74.7% | 75.1% | 85.2% | 2.098 | 70.4% | 40.0% | 40.4% | 0.5 s | 14.112 | 19 KB |
| Nearest Centroid (`centroid`) | 84.6% | 87.1% | 84.6% | 84.7% | 92.0% | 1.769 | 85.2% | 45.0% | 48.2% | 0.0 s | 14.112 | 36 KB |
| k-NN (`knn`, k=5) | 84.6% | 85.6% | 84.6% | 84.4% | 97.5% | 1.040 | 100.0% | 51.4% | 53.8% | 0.0 s | 592.704 | 288 KB |
| Regresi Logistik (`logreg`) | 91.4% | 92.2% | 91.4% | 91.3% | 98.2% | 0.305 | 100.0% | 56.7% | 57.2% | 0.1 s | 14.130 | 73 KB |
| MLP (`mlp`, 128 hidden) | 93.2% | 93.6% | 93.2% | 93.2% | 98.2% | 0.256 | 100.0% | 58.6% | 59.7% | 0.5 s | 102.802 | 405 KB |
| **CNN (`cnn`)** | **98.2%** | **98.4%** | **98.2%** | **98.2%** | 98.2% | **0.094** | 100.0% | **63.6%** | **65.8%** | 5.7 s | 52.658 | 209 KB |

Kesalahan CNN (3 dari 162): nga→ka, ma→pa, ta→ka. Kesalahan dominan model
linear: **ca→sa** (bentuk mirip), sesuai temuan di `DATASET_MODEL.md` bahwa
sejumlah aksara nyaris identik.

### 5.2 Ablasi ukuran data (akurasi / F1 makro pada test)

| Arsitektur | 10/kelas | 20/kelas | 40/kelas | 80/kelas |
| :-- | --: | --: | --: | --: |
| `logreg` | 69.4% / 65.4% | 87.0% / 86.6% | 91.7% / 91.6% | 96.3% / 96.3% |
| `mlp` | 66.7% / 62.4% | 81.5% / 81.1% | 89.8% / 89.6% | 96.3% / 96.3% |
| `cnn` | 61.1% / 60.0% | 75.9% / 75.5% | 87.0% / 86.6% | 94.4% / 94.5% |

### 5.3 Kesimpulan percobaan

1. **Model yang belajar dari data jauh mengungguli template matching** pada
   pengenalan terbuka 18 kelas (74.7% → 98.2%), sekaligus membenarkan keputusan
   memakai template matching hanya untuk *verifikasi* di sisi klien.
2. **CNN** paling akurat dan paling tahan pergeseran distribusi (63.6% pada
   set shift vs 56–59% model non-konvolusi), dengan biaya latih ≈ 6 detik pada
   1080 sampel di 2 core — masih sangat layak dijalankan dari panel admin.
3. **Data sedikit (≤ 20/kelas)**: `logreg` lebih aman (lebih sedikit parameter,
   lebih cepat konvergen); CNN/MLP butuh ≥ 40–80 sampel/kelas untuk unggul.
   Ablasi ini memberi target pengumpulan data nyata: **≥ 80 tulisan
   berlabel per aksara**.
4. Semua model mencapai train acc 100% dengan test < 100% → dataset nyata
   yang lebih beragam (tulisan siswa) lebih penting daripada model yang lebih
   besar; itulah gunanya alur *koreksi → dataset → retraining* di panel.
5. Akurasi pada set shift (≤ 64%) menegaskan bahwa **angka test sintetis
   bukan klaim performa pada tulisan tangan manusia**; model produksi harus
   divalidasi ulang dengan sampel nyata yang dikumpulkan lewat tab Dataset.

---

## 6. Reproduksi

```bash
# dari root repo, memakai venv backend (numpy, Pillow, fastapi)
.venv/bin/python eval/ml_experiments.py                       # benchmark 6 arsitektur
.venv/bin/python eval/ml_experiments.py --ablation \
    --out-md eval/results/ml_experiments.md \
    --out-json eval/results/ml_experiments.json               # + ablasi, simpan laporan
.venv/bin/python eval/ml_experiments.py --groups wresastra,angka --per-class 80 --archs logreg,cnn
```

Unit test fitur (16 test, store sementara): `cd backend && ../.venv/bin/python -m pytest app/tests/test_ml.py -q`.

---

## 7. Endpoint API (`/api/ml`)

| Method & path | Akses | Fungsi |
| --- | --- | --- |
| `GET /ml/status` | publik | mode, `is_admin`, statistik dataset, model produksi, job aktif |
| `GET /ml/architectures` | admin | daftar arsitektur + spesifikasi hyperparameter |
| `GET/PUT /ml/classes` | admin | kelas tersedia/aktif; ganti kelas aktif |
| `GET /ml/dataset/stats`, `GET /ml/dataset/samples` | admin | statistik & daftar sampel (filter label/split/sumber/status, paging) |
| `POST /ml/dataset/samples`, `POST /ml/dataset/samples/bulk` | admin | tambah sampel (base64 PNG/JPG), berlabel atau tidak |
| `GET /ml/dataset/samples/{id}`, `PATCH /ml/dataset/samples/{id}`, `DELETE /ml/dataset/samples/{id}` | admin | detail / labeling, pindah split, status / hapus |
| `POST /ml/dataset/bulk-label`, `POST /ml/dataset/bulk-delete` | admin | aksi massal pada banyak sampel |
| `GET /ml/dataset/samples/{id}/image` | publik | PNG sampel (untuk thumbnail) |
| `POST /ml/dataset/generate-synthetic` | admin | bangkitkan sampel sintetis `{per_class, seed, strength}` |
| `POST /ml/dataset/rebalance`, `POST /ml/dataset/clear?source=` | admin | acak ulang split stratified / kosongkan (per sumber/label) |
| `POST /ml/train` → 202 | admin | mulai job retraining `{arch, hyperparams, name, notes, auto_promote}` |
| `GET /ml/train/jobs`, `GET /ml/train/jobs/{id}`, `DELETE /ml/train/jobs/{id}` | admin | pantau / batalkan job |
| `GET /ml/models`, `GET /ml/models/{id}` | admin | registry; detail = `{model, report}` (laporan evaluasi lengkap) |
| `PATCH /ml/models/{id}`, `DELETE /ml/models/{id}` | admin | ubah nama/catatan, hapus |
| `PUT /ml/models/production` | admin | `{model_id}` pilih model produksi (`null` = nonaktifkan) |
| `POST /ml/predict` | publik | `{image, model_id?, top_k?}` → prediksi (409 bila belum ada model produksi) |
| `POST /ml/predict/compare` | admin | input sama pada banyak model |

---

## 8. Batasan & rencana

- Job training berjalan di proses server (thread); untuk dataset sangat besar
  atau banyak admin sebaiknya dipindah ke worker terpisah.
- Semua percobaan di atas memakai **dataset sintetis**; dataset tulisan tangan
  nyata dari sekolah mitra menjadi prioritas berikutnya — alurnya (unggah,
  label, split, retraining, evaluasi) sudah tersedia di panel.
- Model produksi belum otomatis dipakai halaman belajar/kuis (yang masih
  memakai verifikasi template on-device); integrasi `POST /api/ml/predict` ke
  mode *pengenalan terbuka* di Playground adalah langkah lanjut.
