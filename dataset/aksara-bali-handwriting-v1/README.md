# aksara-bali-handwriting-v1

Dataset gambar tulisan tangan **sintetis** Aksara Bali — 18 kelas
(wresastra), 60 sampel/kelas, total **1080** PNG 64×64
(train 756 · val 162 · test 162, stratified per kelas).

| Kelas | Glyph | Nama |
| --- | --- | --- |
| `ha` | ᬳ | Ha |
| `na` | ᬦ | Na |
| `ca` | ᬘ | Ca |
| `ra` | ᬭ | Ra |
| `ka` | ᬓ | Ka |
| `da` | ᬤ | Da |
| `ta` | ᬢ | Ta |
| `sa` | ᬲ | Sa |
| `wa` | ᬯ | Wa |
| `la` | ᬮ | La |
| `ma` | ᬫ | Ma |
| `ga` | ᬕ | Ga |
| `ba` | ᬩ | Ba |
| `nga` | ᬗ | Nga |
| `pa` | ᬧ | Pa |
| `ja` | ᬚ | Ja |
| `ya` | ᬬ | Ya |
| `nya` | ᬜ | Nya |

## Cara pakai

- **Panel Admin** → `/admin/ml` → tab *Dataset & Labeling* → **Impor dataset repo** →
  pilih `aksara-bali-handwriting-v1` → *Impor*. Label dan split mengikuti `manifest.json`.
- **API**: `POST /api/ml/dataset/import-bundled` body `{"name": "aksara-bali-handwriting-v1"}`.
- **Python**: baca `manifest.json` (`samples[].file`, `label`, `split`).

## Regenerasi

```bash
.venv/bin/python eval/build_dataset.py --name aksara-bali-handwriting-v1 --per-class 60 --seed 20260904
```

Gambar dibangkitkan prosedural dari font Noto Sans Balinese (SIL OFL 1.1) dengan
augmentasi yang sama seperti tombol *Generate sintetis* di panel admin
(`backend/app/ml/synthetic.py`), seed `20260904`. Dataset ini adalah artefak
yang dipakai percobaan `eval/ml_experiments.py` (lihat `docs/ML_RETRAINING.md`).
