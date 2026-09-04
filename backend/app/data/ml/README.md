# Direktori artefak ML (runtime)

Dibuat otomatis oleh Panel Admin → tab **Model ML**. Isinya **tidak** dikomit
ke git (lihat `.gitignore`) dan ikut persist lewat volume `backend/app/data`.

```
ml/
├── classes.json            kelas aktif (label → glyph, nama, latin, grup)
├── dataset/
│   ├── index.json          metadata sampel (label, split, sumber, status)
│   └── images/<id>.png     PNG kanonik 64×64 per sampel
└── models/
    ├── registry.json       daftar model terlatih + metrik + model produksi
    └── <model_id>/         model.npz · model.json · report.json
```

Reproduksi percobaan: `python eval/ml_experiments.py` (lihat `docs/ML_RETRAINING.md`).
