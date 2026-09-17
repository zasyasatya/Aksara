# caraka-aksara-bali-v1

Dataset gambar tulisan tangan **aktual** (digambar manusia, bukan render font) untuk
OCR Aksara Bali.

- **Sumber**: [caraka-id/aksara-bali](https://github.com/caraka-id/aksara-datasets) — korpus
  tulisan tangan Aksara Bali yang dikumpulkan tim **Caraka** (Program Bangkit 2023,
  Universitas Kristen Petra / UPN Veteran Jatim). Setiap kelas adalah folder berisi
  goresan tangan yang dipindai, dibersihkan (grayscale → ambang → resize 125×125).
- **Isi paket**: 2704 PNG kanonik 64×64 (tinta hitam di atas putih),
  26 kelas — 18 Wresastra + 10 Pangangge (suara & tengenan).
- **Split**: `2085 train · 232 val · 387 test`
  (deterministik, modulo indeks; sampel dengan hash PNG identik selalu berada di split yang sama
  supaya tidak ada kebocoran train→test).
- **Label**: nama folder sumber dipetakan ke id kelas di `aksara_master.json`
  (`Pengangge suara - Ulu` → `ulu`, dst.). Lihat tabel di bawah.
- **Augmentasi**: augmentasi rotasi/shear/noise dari sumber **dibuang** — augmentasi dilakukan
  saat training (`backend/app/ml/augment.py`) agar variasi dapat diatur ulang kapan pun.

| Kelas | Glyph | Nama | Folder sumber |
| --- | --- | --- | --- |
| `ha` | ᬳ | Ha | `Ha` |
| `na` | ᬦ | Na | `Na` |
| `ca` | ᬘ | Ca | `Ca` |
| `ra` | ᬭ | Ra | `Ra` |
| `ka` | ᬓ | Ka | `Ka` |
| `da` | ᬤ | Da | `Da` |
| `ta` | ᬣ | Ta | `Ta` |
| `sa` | ᬲ | Sa | `Sa` |
| `wa` | ᬯ | Wa | `Wa` |
| `la` | ᬮ | La | `La` |
| `ma` | ᬫ | Ma | `Ma` |
| `ga` | ᬕ | Ga | `Ga` |
| `ba` | ᬩ | Ba | `Ba` |
| `nga` | ᬗ | Nga | `Nga` |
| `pa` | ᬧ | Pa | `Pa` |
| `ja` | ᬚ | Ja | `Ja` |
| `ya` | ᬬ | Ya | `Ya` |
| `nya` | ᬜ | Nya | `Nya` |
| `ulu` | ᬶ | Ulu (i) | `Pengangge suara - Ulu` |
| `suku` | ᬸ | Suku (u) | `Pengangge suara - Suku` |
| `pepet` | ᭂ | Pepet (ě) | `Pengangge suara - Pepet` |
| `taleng` | ᬾ | Taleng (é) | `Pengangge suara - Taleng` |
| `bisah` | ᬄ | Bisah (h) | `Pengangge tengenan - Bisah (h)` |
| `cecek` | ᬂ | Cecek (ng) | `Pengangge tengenan - Cecek (ng)` |
| `surang` | ᬃ | Surang (r) | `Pengangge tengenan - Surang (r)` |
| `adeg_adeg` | ᭄ | Adeg-adeg (pangkon) | `Pengangge tengenan - Adeg Adeg` |

## Cara pakai

- **Panel Admin** → `/admin/ml` → pilih tugas **Aksara Bali** → tab *Dataset & Labeling* →
  **Impor dataset repo** → `caraka-aksara-bali-v1`.
- **API**: `POST /api/ml/dataset/import-bundled` body `{"name": "caraka-aksara-bali-v1", "task": "aksara"}`.

## Regenerasi

Unduh sumber lalu kemas ulang (butuh ± 6 menit, paket lengkap 220 MB):

```bash
curl -sSL -o /tmp/caraka.tgz https://github.com/caraka-id/aksara-datasets/archive/refs/heads/main.tar.gz
mkdir -p /tmp/caraka && tar xzf /tmp/caraka.tgz -C /tmp/caraka
.venv/bin/python eval/build_real_datasets.py --only caraka --caraka-per-class 140
```
