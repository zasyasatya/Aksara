# OCR Lens — evaluasi tingkat halaman

Dihasilkan `eval/evaluate_ocr.py` (diperbarui 2026-09-17 01:21).

Angka di bawah mengukur **seluruh pipeline kamera** (praproses → segmentasi →
klasifikasi → decoding kamus), bukan hanya klasifikasi satu aksara. Oleh karena itu
nilainya di bawah akurasi per-glyph pada `OCR_LENS_MODELS.md`.

## Halaman render (label space)

### Tugas `aksara`

| Ukuran font | Exact line | CER | Rasio jumlah baris | ms/halaman |
| --- | ---: | ---: | ---: | ---: |
| 48 px | 30.0% | 22.0% | 1.00 | 119 |
| 72 px | 30.0% | 22.0% | 1.00 | 135 |
| 96 px | 30.0% | 24.0% | 1.00 | 161 |

### Tugas `latin`

| Ukuran font | Exact line | CER | Rasio jumlah baris | ms/halaman |
| --- | ---: | ---: | ---: | ---: |
| 48 px | 30.0% | 33.3% | 1.00 | 140 |
| 72 px | 30.0% | 38.9% | 1.00 | 151 |
| 96 px | 30.0% | 39.7% | 1.00 | 176 |

## Kata tulisan tangan nyata (Caraka, `test_images/Aksara_Bali`)

n=23 · kata tepat **8.7%** (setara setelah huruf a legya dilepas) · mendekati (CER≤25%) **69.6%** · CER rata-rata 32.6% · 190 ms/kata

| Berkas (nama = teks) | OCR (aksara) | OCR → Latin | target | CER |
| --- | --- | --- | --- | ---: |
| bahasa.png | `ᬩᬧᬲ` | `bapasa` | bahasa | 17% |
| bahasa_bali.png | `ᬩᬧᬲᬩᬮᬶ` | `bapasabali` | bahasabali | 10% |
| bali-pergi_bali.png | `ᬃᬮᬶᬕᬮᬭ` | `ligalara` | balipergibali | 54% |
| belajar.png | `ᬾᬦᬮᬚᬃ` | `nalajar` | belajar | 29% |
| belajar_bahasa_bali.png | `ᬾᬫᬬᬚᬃᬩᬳᬲᬩᬮᬶ` | `mayajarbaasabali` | belajarbahasabali | 24% |
| belajar_bahasa_sunda.png | `ᬾᬢᬮᬚᬃᬩᬧᬲᬩᬮᬶ` | `talajarbapasabali` | belajarbahasasunda | 39% |
| bicara_bahasa_bali.png | `ᬮᬶᬲᬭᬩᬳᬲᬩᬮᬶ` | `lisarabaasabali` | bicarabahasabali | 19% |
| gata.png | `ᬕᬬ` | `gaya` | gata | 25% |
| kalimat_bali.png | `ᬲᬬᬲᬗᬚᬲᬬᬂᬩᬭ ᬾᬤᬬᬩᬗᬾᬭᬦᬦᬗᬓ` | `sayasangajasayangb` | kalimatbali | 254% |
| kasar.png | `ᬓᬲᬃ` | `kasar` | kasar | 0% |
| keberagaman.png | `ᬾᬭᬾᬦᬭᬕᬫ᭄` | `renaragam` | keberagaman | 36% |
| pergi_bersama_kadek.png | `ᬃᬕᬶᬃᬲᬫᬓᬸᬓ᭄` | `girsamakuk` | pergibersamakadek | 41% |
| pergi_ke_bali.png | `ᬃᬕᬭᬾᬲᬩᬮᬶ` | `garesabali` | pergikebali | 55% |
| saya_belajar_bahasa.png | `ᬲᬲᬾᬫᬮᬚᬃᬩᬧᬲ` | `sasemalajarbapasa` | sayabelajarbahasa | 24% |
| saya_bicara_bahasa_bali.png | `ᬲᬧᬩᬶᬲᬦᬩᬧᬲᬩᬮᬶ` | `sapabisanabapasaba` | sayabicarabahasabali | 20% |
| saya_sayang_bahasa.png | `ᬲᬲᬲᬬᬂᬩᬳᬲ` | `sasasayangbaasa` | sayasayangbahasa | 12% |
| saya_sayang_bahasa_bali.png | `ᬲᬬᬲᬬᬂᬩᬳᬲᬩᬮᬶ` | `sayasayangbaasabal` | sayasayangbahasabali | 5% |
| saya_sayang_bali.png | `ᬲᬲᬲᬬᬂᬩᬮᬶ` | `sasasayangbali` | sayasayangbali | 7% |
| saya_sayang_belajar_bahasa.png | `ᬲᬬᬲᬬᬾᬾᬕᬮᬚᬃᬩᬳᬲ` | `sayasayegalajarbaa` | sayasayangbelajarbahasa | 17% |
| saya_sayang_belajar_caraka.png | `ᬲᬧᬲᬬᬂᬾᬬᬮᬓᬃᬘᬭᬓ` | `sapasayangyalakarc` | sayasayangbelajarcaraka | 17% |
| sayang.png | `ᬲᬬᬂ` | `sayang` | sayang | 0% |
| sayang_gata.png | `ᬲᬬᬂᬮᬬ` | `sayanglaya` | sayanggata | 20% |
| seminyak.png | `ᬾᬲᬫᬶᬜ᭄` | `saminy` | seminyak | 25% |

## Catatan

- Huruf Bali yang dirangkai *pasangan* (aksara + virama) dibentuk font menjadi satu ligatura;
  kelas pasangan tidak ada di dataset Caraka, sehingga rangkaian itu dibaca
  sebagai kombinasi terdekat. Koreksi pengguna (halaman Lens → „kirim koreksi”) mengisi
  celah ini lewat retraining admin.
- Uji mandiri di Panel Admin memakai mekanisme yang sama (`app/ocr/render.py`).
