# OCR Lens — pipeline kamera tingkat halaman

Dokumen teknis fitur **Lens Aksara** (`/lens`): OCR foto/video kamera menjadi teks Aksara Bali
dan/atau Latin, lengkap dengan transliterasi + arti. Ini melengkapi `ML_RETRAINING.md`
(store ML, training, registry) dan `DATASET_MODEL.md` (classifier on-device berupa
template-matcher).

```
frontend/app/lens/page.tsx        pemirsa: kamera (getUserMedia), overlay, inspektur aksara, koreksi
frontend/lib/api.ts               api.ocr.* (status, scan, scanFile, feedback, config, selftest, install)
backend/app/routers/ocr.py        HTTP: /api/ocr/*, rate-limit per IP, otorisasi admin
backend/app/schemas/ocr.py        model Pydantic request
backend/app/ocr/
  imageops.py                     dekode, kontras, Sauvola/Otsu, komponen terhubung, profil, rotasi
  segment.py                      baris → gugus komponen → badan + pangangge; belah gugus lebar
  pipeline.py                     orkestrasi: ScanOptions → praproses → klasifikasi → decode → teks
  lexicon.py                      n-gram karakter (ruang label) + beam search + bonus kamus
  render.py                       render teks → citra halaman (uji mandiri admin, tanpa dataset)
  config.py                       data/ocr.json: default_options · feedback · limits; antrean koreksi
backend/app/ml/pretrain.py        pasang model bawaan (ml_bundled) ke store ML saat startup
backend/app/data/ml_bundled/      model hasil training dataset aktual (dikomit, ±300 KB/tugas)
eval/build_real_datasets.py       bangun paket dataset (Caraka, Omniglot, render cetak)
eval/train_ocr_models.py          latih model OCR Lens per tugas → tulis ml_bundled + laporan
eval/evaluate_ocr.py              evaluasi tingkat halaman (render + kata nyata Caraka)
```

## 1. Alur satu permintaan

`POST /api/ocr/scan` (atau `/scan/file` multipart) →

1. `imageops.decode_gray` (EXIF dihiraukan, sisi terpanjang ≤ `max_side`) → `stretch_contrast`
   → binerisasi `sauvola|otsu|fixed` dengan `invert=auto` (deteksi polaritas dari border).
2. Opsional: `estimate_skew` + `rotate` (expand=False → sistem koordinat tetap, agar `rect`
   yang dinormalkan tetap sejajar dengan gambar asli di klien).
3. `upscale_small`: bila tinggi baris median < `target_line_height`, citra diperbesar
   (×≤4) **sebelum** segmentasi. Model dilatih pada glyph ~20 px; teks 1–2 px tanpa ini hancur.
4. `segment.find_lines`: pita proyeksi horizontal; pita berjarak dekat digabung (ascender/
   descender), pita > 2.3× median dibelah pada lembah tertipis; pita berkepadatan tinta <
   `line_min_ink` dibuang (debu/kotoran kamera).
5. `imageops.components` (scanline 8-konektivitas, O(piksel), 0,07 s untuk 4000 blob pada
   1400²) → gugus: gabung bila tumpang tindih horizontal ≥ 45% **atau** celah ≤ `merge_gap_ratio`
   × tinggi baris; wajib `markish` (salah satu kotak ≤ 62% tinggi yang lain) supaya huruf
   Latin bersebelahan tidak menyatu, dan lebar gabungan ≤ `split_width_ratio` × tinggi baris.
6. `_split_parts`: bila gugus lebih tinggi dari 1,42× tinggi basis (persentil-25), potong pada
   baris tertipis di zona atas/bawah → `body` + `above`/`below` (pangangge). `_split_columns`
   menyiapkan opsi belah horizontal untuk gugus yang kelebaran.
7. Klasifikasi batch: semua potongan (termasuk alternatif belahan) sekali jalan per tugas →
   `predict_proba` (dengan `tta`), label dari `entry["classes"]` model, bukan dari kelas aktif
   store — supaya model lama tetap benar walau admin mengubah kelas.
8. Pilihan skrip per baris: rata-rata top-1 tiap model; Latin harus unggul > `script_margin`
   bila barisnya punya bukti geometri Bali (banyak gugus >1 potongan).
9. `lexicon.beam_decode` (lebar `beam_width`): skor = 0,55·log P(akustik) + 0,45·log P(n-gram)
   + bonus kata; aksara memaksa satu kata per baris, Latin boleh ber-spasi dari `word_gap_ratio`.
10. Rakit Unicode (`glyph` basis + `glyph` pangangge) → `services.transliterator.transliterate`
    dua arah → `glossary` dari `dictionary.json`.

## 2. Model bahasa (lexicon)

* Ruang simbol = **label kelas** (`ha`, `ulu`, `m`…): tidak ada pemetaan Unicode di dalam decoding.
* Sumber korpus: `dictionary.json`, `aksara_master.json`, `lessons.json`, `quiz.json`, `docs.json`,
  `engagement.json`. Untuk Bali, kata Latin korpus **ditransliterasi dulu** ke aksara
  (`_latin_to_aksara_seqs`) → 2 642 token / 406 bentuk (vs 388 token tanpa itu).
* Interpolasi trigram → bigram → unigram (α=0,15), token `</w>` penanda akhir, bonus kata
  `_WORD_BONUS·(1+0,25·log(1+c))`.
* Cache: `backend/app/data/ocr_lm_aksara.json`; invalidated oleh mtime korpus.

## 3. Data & model

| Paket | Isi | Jumlah |
| --- | --- | --- |
| `dataset/caraka-aksara-bali-v1` | tulisan tangan 26 kelas aksara Bali (dari repositori Caraka/Bangkit, di-dedupe & dikecilkan) | 2 704 |
| `dataset/aksara-bali-print-v1` | render Noto Sans Balinese + degradasi foto | 1 456 |
| `dataset/omniglot-latin-handwriting-v1` | huruf Latin tulisan tangan (Omniglot, MIT) | 520 |
| `dataset/latin-print-v1` | render 5 font DejaVu a–z 0–9 + degradasi | 2 016 |

* Augmentasi hanya **on-the-fly** saat training (`ml/augment.py`): rotasi, geser, skala, elastis
  ringan, coretan — dataset tersimpan tidak pernah berubah.
* `deepcnn` (Conv 14 → Conv 24 → 2 FC 112, BN-free, label smoothing 0,06, cosine LR,
  class-balance 0,6) di CPU: 398 s (aksara, 3 217 sampel) / 263 s (latin).
* Hasil 48 epoch (`eval/results/OCR_LENS_MODELS.md`):

  | Tugas | test acc | tulisan tangan nyata | F1 makro | top-3 |
  | --- | ---: | ---: | ---: | ---: |
  | aksara | 94,29% | 90,96% (n=387) | 90,82% | 99,7% |
  | latin | 98,07% | 89,74% (n=78) | 89,12% | 100% |

* Halaman (`eval/results/OCR_LENS_PAGES.md`, bawaan `close_iters=1`, TTA 2): exact-line 30%,
  CER 22% (aksara) / 33–40% (latin) pada render terkontrol; pada 23 citra **kata tulisan tangan
  nyata** Caraka: **69,6%** kata “mendekati” (CER ≤ 25%), CER rata-rata 32,6%, ±200 ms/kata.
  Uji pipeline admin (`/api/ocr/selftest`) berada di rentang yang sama (exact 40%, CER 29–34%).

Lisensi/attribusi: Caraka tidak mencantumkan berkas lisensi di repo → yang dikomit **bukan** salinan
mentah, melainkan paket turunan yang sudah diperkecil (28×28 → 64×64 PNG), dedinamiskan per kelas,
dan diberi atribusi di `dataset/*/README.md`. Font: Noto Sans Balinese & DejaVu (OFL). Omniglot (MIT).

## 4. Batas yang diketahui (jujur di muka)

1. **Pasangan/aksara berangkai** (`ᬓ᭄ᬭ`, `ᬦᬿᬢ`): font merangkainya jadi satu ligatura, kelasnya tidak
   ada di dataset → dibaca sebagai bentuk terdekat. Solusi jangka panjang: kelas pasangan atau
   pemecah ligatura berbasis kamus.
2. Teks **sangat kecil/kontras rendah** tetap bergantung pada kualitas kamera; `upscale_small`
   membantu tapi tidak menciptakan detail.
3. Segmentasi berbasis proyeksi — **baris melengkung** (lontar) atau tulisan tumpang tindih akan
   terpotong salah; tidak ada model segmentasi semantik.
4. Bukan OCR umum: kelas = 26 aksara + 36 Latin. Di luar itu (Angka Bali, jangkep lengkap)
   butuh dataset + training tambahan.

## 5. Konfigurasi & operasional

`backend/app/data/ocr.json` (diedit lewat Panel Admin → Lens & OCR, atau `PUT /api/ocr/config`):

```json
{
  "default_options": { "script": "auto", "tta": 2, "binarize": "sauvola", "max_glyphs": 480 },
  "limits": { "scan_per_minute": 30, "feedback_per_minute": 8, "max_image_bytes": 8000000, "max_side": 2400 },
  "feedback": { "enabled": true, "require_review": true }
}
```

* Rate limit = token bucket per IP (`X-Forwarded-For` dihormati); admin dibebaskan.
* Setiap opsi request dijepit ke rentang aman (`ScanOptions._RANGE`) → klien tidak bisa
  menjatuhkan server dengan `max_glyphs=1e9`.
* `pretrain.ensure_installed()` dijalankan pada startup (`main.py`) dan idempoten: menyalin
  `data/ml_bundled/<task>/<id>/` ke `data/ml/<task>/models/`, mengaktifkan kelas model, dan
  menetapkan produksi bila belum ada.
* Alur koreksi: Lens → `POST /api/ocr/feedback` (crop 64×64, `source=camera`, `status=review`)
  → admin *Terima* → ikut training berikutnya (`POST /api/ocr/feedback/train`).

## 6. Reproduksi

```bash
.venv/bin/python eval/build_real_datasets.py --only caraka,omniglot,print
.venv/bin/python eval/train_ocr_models.py --epochs 48 --tta 6
.venv/bin/python eval/evaluate_ocr.py --caraka /path/aksara-datasets-main
.venv/bin/python -m pytest backend/app/tests -q
```
