# Model OCR Lens — hasil training (diperbarui 2026-09-17)

Dihasilkan oleh `eval/train_ocr_models.py`. Model-model ini dikomit sebagai
**model bawaan** (`backend/app/data/ml_bundled/`) sehingga halaman Lens langsung
berfungsi tanpa training ulang; Panel Admin tetap dapat melatih ulang.

| Tugas | Arsitektur | Kelas | Sampel latih | Akurasi test | **Akurasi tulisan tangan nyata** | F1 makro | Top-3 | CER | Waktu |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| aksara | Deep CNN + Augmentasi (rekomendasi OCR Lens) | 26 | 3217 | 94.29% | 90.96% (n=387) | 90.82% | 99.7% | 9.04% | 397.9 s |
| latin | Deep CNN + Augmentasi (rekomendasi OCR Lens) | 36 | 3282 | 98.58% | 91.03% (n=78) | 89.53% | 97.4% | 8.97% | 935.4 s |

## Konfigurasi

```json
{
  "arch": "deepcnn",
  "epochs": 48,
  "batch_size": 96,
  "lr": 0.007,
  "augment": 1.0,
  "class_balance": 0.6,
  "hidden_units": 112,
  "conv1_filters": 14,
  "conv2_filters": 28,
  "label_smoothing": 0.06,
  "eval_tta": 6,
  "packs": {
    "aksara": [
      "caraka-aksara-bali-v1",
      "aksara-bali-print-v1"
    ],
    "latin": [
      "omniglot-latin-handwriting-v1",
      "latin-print-v1"
    ]
  }
}
```

### Tugas `aksara` — per kelas (tulisan tangan nyata bila tersedia)

| Kelas | Presisi | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| `ha` | 83.3 | 66.7 | 74.1 | 15 |
| `na` | 92.9 | 86.7 | 89.7 | 15 |
| `ca` | 84.6 | 73.3 | 78.6 | 15 |
| `ra` | 83.3 | 100.0 | 90.9 | 15 |
| `ka` | 100.0 | 86.7 | 92.9 | 15 |
| `da` | 93.8 | 100.0 | 96.8 | 15 |
| `ta` | 62.5 | 71.4 | 66.7 | 14 |
| `sa` | 80.0 | 80.0 | 80.0 | 15 |
| `wa` | 100.0 | 60.0 | 75.0 | 15 |
| `la` | 100.0 | 86.7 | 92.9 | 15 |
| `ma` | 100.0 | 100.0 | 100.0 | 15 |
| `ga` | 82.3 | 93.3 | 87.5 | 15 |
| `ba` | 100.0 | 100.0 | 100.0 | 15 |
| `nga` | 100.0 | 100.0 | 100.0 | 14 |
| `pa` | 73.7 | 93.3 | 82.3 | 15 |
| `ja` | 100.0 | 100.0 | 100.0 | 15 |
| `ya` | 88.2 | 100.0 | 93.8 | 15 |
| `nya` | 93.8 | 100.0 | 96.8 | 15 |
| `ulu` | 93.8 | 100.0 | 96.8 | 15 |
| `suku` | 100.0 | 100.0 | 100.0 | 15 |
| `pepet` | 100.0 | 100.0 | 100.0 | 14 |
| `taleng` | 82.3 | 93.3 | 87.5 | 15 |
| `bisah` | 100.0 | 93.3 | 96.5 | 15 |
| `cecek` | 100.0 | 100.0 | 100.0 | 15 |
| `surang` | 100.0 | 100.0 | 100.0 | 15 |
| `adeg_adeg` | 85.7 | 80.0 | 82.8 | 15 |

### Tugas `latin` — per kelas (tulisan tangan nyata bila tersedia)

| Kelas | Presisi | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| `a` | 0.0 | 0.0 | 0.0 | 3 |
| `b` | 100.0 | 100.0 | 100.0 | 3 |
| `c` | 100.0 | 100.0 | 100.0 | 3 |
| `d` | 75.0 | 100.0 | 85.7 | 3 |
| `e` | 100.0 | 100.0 | 100.0 | 3 |
| `f` | 100.0 | 100.0 | 100.0 | 3 |
| `g` | 100.0 | 33.3 | 50.0 | 3 |
| `h` | 100.0 | 100.0 | 100.0 | 3 |
| `i` | 100.0 | 66.7 | 80.0 | 3 |
| `j` | 100.0 | 100.0 | 100.0 | 3 |
| `k` | 100.0 | 100.0 | 100.0 | 3 |
| `l` | 75.0 | 100.0 | 85.7 | 3 |
| `m` | 100.0 | 100.0 | 100.0 | 3 |
| `n` | 100.0 | 100.0 | 100.0 | 3 |
| `o` | 75.0 | 100.0 | 85.7 | 3 |
| `p` | 100.0 | 100.0 | 100.0 | 3 |
| `q` | 60.0 | 100.0 | 75.0 | 3 |
| `r` | 100.0 | 100.0 | 100.0 | 3 |
| `s` | 100.0 | 100.0 | 100.0 | 3 |
| `t` | 100.0 | 100.0 | 100.0 | 3 |
| `u` | 100.0 | 100.0 | 100.0 | 3 |
| `v` | 100.0 | 66.7 | 80.0 | 3 |
| `w` | 100.0 | 100.0 | 100.0 | 3 |
| `x` | 100.0 | 100.0 | 100.0 | 3 |
| `y` | 75.0 | 100.0 | 85.7 | 3 |
| `z` | 100.0 | 100.0 | 100.0 | 3 |
| `0` | 0.0 | 0.0 | 0.0 | 0 |
| `1` | 0.0 | 0.0 | 0.0 | 0 |
| `2` | 0.0 | 0.0 | 0.0 | 0 |
| `3` | 0.0 | 0.0 | 0.0 | 0 |
| `4` | 0.0 | 0.0 | 0.0 | 0 |
| `5` | 0.0 | 0.0 | 0.0 | 0 |
| `6` | 0.0 | 0.0 | 0.0 | 0 |
| `7` | 0.0 | 0.0 | 0.0 | 0 |
| `8` | 0.0 | 0.0 | 0.0 | 0 |
| `9` | 0.0 | 0.0 | 0.0 | 0 |
