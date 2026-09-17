# omniglot-latin-handwriting-v1

Tulisan tangan Latin **aktual** (manusia), 26 kelas a–z, 520 gambar.

- **Sumber**: Omniglot (Lake et al., *Science* 2015) —
  [brendenlake/omniglot](https://github.com/brendanpeterson/omniglot) / MIT.
  Tiap karakter digambar **20 penulis berbeda** (Mechanical Turk).
- **Split per penulis** (penting untuk evaluasi yang jujur):
  penulis 01–14 → train, 15–17 → val, **18–20 → test**. Model diuji pada
  tangan yang belum pernah dilihatnya.
- **Label a–z**: urutan folder `character01…character26` Omniglot mengikuti
  abjad Latin; pemetaan ini diverifikasi dengan pencocokan bentuk ke render
  DejaVu Sans (`eval/verify_ocr_model.py`).
- Konvensi warna dibalik dari sumber (Omniglot: tinta putih di latar hitam)
  menjadi PNG kanonik repo: tinta hitam di atas putih, 64×64.

## Cara pakai

```bash
curl -sSL -o /tmp/omniglot.tgz https://github.com/brendenlake/omniglot/archive/refs/heads/master.tar.gz
mkdir -p /tmp/omni && tar xzf /tmp/omniglot.tgz -C /tmp/omni
cd /tmp/omni/omniglot-master/python && unzip -q -o images_background.zip -d /tmp/omni/x
.venv/bin/python eval/build_real_datasets.py --only omniglot
```
