# Hasil percobaan retraining classifier Aksara Bali

Dibangkitkan `2026-09-04 14:22 UTC` oleh `eval/ml_experiments.py` (Python 3.11.2, NumPy 2.4.6, CPU x86_64). Semua model murni NumPy di CPU — angka durasi tergantung mesin.

> Metrik pada **dataset sintetis** (glyph Noto Sans Balinese + augmentasi), bukan tulisan tangan manusia.

## 1. Benchmark arsitektur

Dataset sintetis: **1080 sampel**, 18 kelas (wresastra), 60/kelas, augmentasi strength 1.0, seed 20260904. Split train/val/test = 756/162/162 (stratified). Evaluasi pada split **test**.

Uji pergeseran (shift): 360 sampel baru dengan augmentasi lebih kuat (strength 1.6, seed berbeda) — tidak pernah dilihat saat training.

| Arsitektur | Accuracy | Precision | Recall | F1 (makro) | Top-3 | Log-loss | Train acc | Acc (shift) | F1 (shift) | Latih | Param | Ukuran |
| :-- | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| **Template Matching (Chamfer)** (`template`) | 74.7% | 81.2% | 74.7% | 75.1% | 85.2% | 2.098 | 70.4% | 40.0% | 40.4% | 0.5 s | 14.112 | 19 KB |
| **Nearest Centroid** (`centroid`) | 84.6% | 87.1% | 84.6% | 84.7% | 92.0% | 1.769 | 85.2% | 45.0% | 48.2% | 0.0 s | 14.112 | 36 KB |
| **k-Nearest Neighbours** (`knn`) | 84.6% | 85.6% | 84.6% | 84.4% | 97.5% | 1.040 | 100.0% | 51.4% | 53.8% | 0.0 s | 592.704 | 288 KB |
| **Regresi Logistik (Softmax)** (`logreg`) | 91.4% | 92.2% | 91.4% | 91.3% | 98.2% | 0.305 | 100.0% | 56.7% | 57.2% | 0.1 s | 14.130 | 73 KB |
| **Multi-Layer Perceptron** (`mlp`) | 93.2% | 93.6% | 93.2% | 93.2% | 98.2% | 0.256 | 100.0% | 58.6% | 59.7% | 0.5 s | 102.802 | 405 KB |
| **Convolutional Neural Network** (`cnn`) | 98.2% | 98.4% | 98.2% | 98.2% | 98.2% | 0.094 | 100.0% | 63.6% | 65.8% | 5.7 s | 52.658 | 209 KB |

Model terbaik (F1 makro test): **Convolutional Neural Network** — F1 98.2%, akurasi 98.2%.

### Per kelas — Convolutional Neural Network

| Kelas | Precision | Recall | F1 | Support |
| :-- | --: | --: | --: | --: |
| ha | 100.0% | 100.0% | 100.0% | 9 |
| na | 100.0% | 100.0% | 100.0% | 9 |
| ca | 100.0% | 100.0% | 100.0% | 9 |
| ra | 100.0% | 100.0% | 100.0% | 9 |
| ka | 81.8% | 100.0% | 90.0% | 9 |
| da | 100.0% | 100.0% | 100.0% | 9 |
| ta | 100.0% | 88.9% | 94.1% | 9 |
| sa | 100.0% | 100.0% | 100.0% | 9 |
| wa | 100.0% | 100.0% | 100.0% | 9 |
| la | 100.0% | 100.0% | 100.0% | 9 |
| ma | 100.0% | 88.9% | 94.1% | 9 |
| ga | 100.0% | 100.0% | 100.0% | 9 |
| ba | 100.0% | 100.0% | 100.0% | 9 |
| nga | 100.0% | 88.9% | 94.1% | 9 |
| pa | 90.0% | 100.0% | 94.7% | 9 |
| ja | 100.0% | 100.0% | 100.0% | 9 |
| ya | 100.0% | 100.0% | 100.0% | 9 |
| nya | 100.0% | 100.0% | 100.0% | 9 |

Paling sering tertukar: nga→ka ×1, ma→pa ×1, ta→ka ×1.

### Hyperparameter (default panel admin)

| Arsitektur | Hyperparameter |
| :-- | :-- |
| `template` | `{}` |
| `centroid` | `{}` |
| `knn` | `{"k": 5}` |
| `logreg` | `{"epochs": 30, "learning_rate": 0.005, "batch_size": 64, "weight_decay": 0.0005}` |
| `mlp` | `{"epochs": 40, "learning_rate": 0.002, "batch_size": 64, "hidden_units": 128, "dropout": 0.2, "weight_decay": 0.0005}` |
| `cnn` | `{"epochs": 15, "learning_rate": 0.004, "batch_size": 64, "conv1_filters": 8, "conv2_filters": 16, "hidden_units": 64, "dropout": 0.25}` |

## 2. Ablasi ukuran data (sampel per kelas)

Akurasi test / F1 makro saat jumlah sampel per kelas bertambah (hyperparameter default, dataset dibangkitkan ulang per ukuran, seed sama).

| Arsitektur | 10/kelas | 20/kelas | 40/kelas | 80/kelas |
| :-- | --: | --: | --: | --: |
| `logreg` | 69.4% / 65.4% | 87.0% / 86.6% | 91.7% / 91.6% | 96.3% / 96.3% |
| `mlp` | 66.7% / 62.4% | 81.5% / 81.1% | 89.8% / 89.6% | 96.3% / 96.3% |
| `cnn` | 61.1% / 60.0% | 75.9% / 75.5% | 87.0% / 86.6% | 94.4% / 94.5% |

Format sel: akurasi / F1 makro.

Total waktu percobaan: 38 detik.

