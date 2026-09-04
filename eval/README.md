# Evaluasi classifier tulisan tangan Aksara Bali

`evaluate_handwriting.py` adalah harness evaluasi **reproducible** untuk
classifier template-matching di `frontend/lib/aksara-recognition.ts`.

Harness meniru 1:1 normalisasi & penskoran classifier (normalize → chamfer
distance dua arah → threshold), lalu mengukur dua tugas:

1. **Verifikasi / telusur** (`classifyTracing`) — tugas utama produk.
2. **Pengenalan terbuka** (`recognizeAksara`) — dilaporkan jujur.

Hasil lengkap beserta metodologi terdokumentasi di `docs/DATASET_MODEL.md`
dan halaman dokumentasi `/docs/dataset-dan-model`.

## Menjalankan

```bash
cd eval
python -m venv .venv
.venv/bin/pip install Pillow numpy
.venv/bin/python evaluate_handwriting.py            # unduh font + jalankan
.venv/bin/python evaluate_handwriting.py --font /path/NotoSansBalinese.ttf
```

Font `NotoSansBalinese.ttf` diunduh otomatis dari google/fonts (lisensi
SIL OFL 1.1) bila belum ada, dan di-*ignore* oleh git.

## Percobaan retraining (`ml_experiments.py`)

`ml_experiments.py` menjalankan **percobaan retraining** classifier dengan kode
pipeline yang sama persis dengan Panel Admin → Model ML (`backend/app/ml`):
dataset sintetis → training 6 arsitektur (template, centroid, k-NN, regresi
logistik, MLP, CNN) → laporan metrik (accuracy, precision, recall, F1, top-3,
log-loss, per kelas) → uji pergeseran distribusi → ablasi ukuran data.
Semua artefak ditulis ke direktori sementara, tidak menyentuh
`backend/app/data/ml`.

```bash
# dari root repo, memakai venv backend (numpy, Pillow, fastapi)
.venv/bin/python eval/ml_experiments.py
.venv/bin/python eval/ml_experiments.py --ablation \
    --out-md eval/results/ml_experiments.md --out-json eval/results/ml_experiments.json
.venv/bin/python eval/ml_experiments.py --help   # opsi: --archs, --groups, --per-class, --seed, …
```

Hasil terakhir tersimpan di `results/ml_experiments.md` (+ JSON) dan dirangkum
di `docs/ML_RETRAINING.md` §5.

## Paket dataset yang dikomit (`build_dataset.py`)

`build_dataset.py` membangun **paket dataset gambar** yang dikomit di
`dataset/<nama>/` — `manifest.json` (kelas, label, split, sha256, seed,
lisensi) + `images/<label>/<label>_NNN.png` (64×64) — dengan generator sintetis
yang sama dengan Panel Admin. Paket ini yang muncul di tombol **Impor dataset
repo** (`GET/POST /api/ml/dataset/bundled|import-bundled`) dan dipakai di
panduan bergambar `docs/PANDUAN_RETRAINING.md`.

```bash
# identik dengan dataset/aksara-bali-handwriting-v1 (seed sama → berkas sama)
.venv/bin/python eval/build_dataset.py --name aksara-bali-handwriting-v1 --per-class 60 --seed 20260904
# varian: kelas lain / lebih banyak sampel / split berbeda
.venv/bin/python eval/build_dataset.py --name aksara-bali-angka-v1 --groups angka --per-class 80 --seed 7 --out dataset
.venv/bin/python eval/build_dataset.py --help
```
