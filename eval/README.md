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
