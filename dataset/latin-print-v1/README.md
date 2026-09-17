# latin-print-v1

Teks tercetak Latin (a–z, 0–9) dari lima font DejaVu dengan degradasi ala foto — bahan latihan pengenal huruf untuk OCR Lens pada papan nama, buku, dan lontar tercetak.

- 2016 PNG kanonik 64×64 · 36 kelas · split
  1568 train / 112 val / 336 test.
- Font: DejaVuSans.ttf, DejaVuSans-Bold.ttf, DejaVuSerif.ttf, DejaVuSerif-Bold.ttf, DejaVuSansMono.ttf — DejaVu Fonts — Bitstream Vera license (bebas digunakan & didistribusikan)
- **Bukan** pengganti data nyata: paket ini melengkapi dataset tulisan tangan
  aktual (`caraka-aksara-bali-v1`, `omniglot-latin-handwriting-v1`) supaya pengenal
  tetap kuat pada teks **tercetak / terukir** yang justru paling sering difoto.
- Regenerasi: `.venv/bin/python eval/build_real_datasets.py --only print --print-per-class 56`
