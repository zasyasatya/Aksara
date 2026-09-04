"""Paket machine-learning Aksara: dataset, pelatihan ulang, evaluasi, registry.

Semua model diimplementasikan murni dengan NumPy (tanpa PyTorch/TensorFlow)
agar ringan dijalankan di container kecil dan mudah diaudit. Struktur:

- ``features``   : decode & normalisasi gambar → vektor fitur 28×28.
- ``synthetic``  : generator dataset sintetis dari font Noto Sans Balinese.
- ``models``     : arsitektur (centroid, knn, logreg, mlp, cnn, template).
- ``metrics``    : accuracy, precision, recall, F1, confusion matrix, dll.
- ``store``      : penyimpanan dataset (PNG + index.json) & registry model.
- ``training``   : job pelatihan di background thread + evaluasi otomatis.
"""
