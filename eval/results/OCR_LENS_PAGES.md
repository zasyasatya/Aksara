# OCR Lens — evaluasi tingkat halaman

Dihasilkan `eval/evaluate_ocr.py` (diperbarui 2026-09-17 05:47).

Angka di bawah mengukur **seluruh pipeline kamera** (praproses → segmentasi →
klasifikasi → decoding kamus), bukan hanya klasifikasi satu aksara. Oleh karena itu
nilainya di bawah akurasi per-glyph pada `OCR_LENS_MODELS.md`.

## Halaman render (label space)

### Tugas `aksara`

| Ukuran font | Exact line | CER | Rasio jumlah baris | ms/halaman |
| --- | ---: | ---: | ---: | ---: |
| 48 px | 30.0% | 20.0% | 1.00 | 130 |
| 72 px | 30.0% | 20.0% | 1.00 | 149 |
| 96 px | 30.0% | 22.0% | 1.00 | 178 |

### Tugas `latin`

| Ukuran font | Exact line | CER | Rasio jumlah baris | ms/halaman |
| --- | ---: | ---: | ---: | ---: |
| 48 px | 70.0% | 2.4% | 1.00 | 175 |
| 72 px | 70.0% | 3.2% | 1.00 | 195 |
| 96 px | 60.0% | 5.6% | 1.00 | 215 |

## Kata tulisan tangan nyata (Caraka, `test_images/Aksara_Bali`)

_Tidak diuji — jalankan dengan `--caraka <folder>` (tarball repositori Caraka)._

## Catatan

- Huruf Bali yang dirangkai *pasangan* (aksara + virama) dibentuk font menjadi satu ligatura;
  kelas pasangan tidak ada di dataset Caraka, sehingga rangkaian itu dibaca
  sebagai kombinasi terdekat. Koreksi pengguna (halaman Lens → „kirim koreksi”) mengisi
  celah ini lewat retraining admin.
- Uji mandiri di Panel Admin memakai mekanisme yang sama (`app/ocr/render.py`).
