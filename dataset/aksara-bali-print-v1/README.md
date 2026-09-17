# aksara-bali-print-v1

Teks tercetak Aksara Bali: glyph Noto Sans Balinese dirender lalu diberi degradasi ala foto (blur, noise, pencahayaan miring, shear). Melengkapi dataset tulisan tangan aktual.

- 1456 PNG kanonik 64×64 · 26 kelas · split
  1132 train / 81 val / 243 test.
- Font: NotoSansBalinese.ttf — Noto Sans Balinese — SIL Open Font License 1.1
- **Bukan** pengganti data nyata: paket ini melengkapi dataset tulisan tangan
  aktual (`caraka-aksara-bali-v1`, `omniglot-latin-handwriting-v1`) supaya pengenal
  tetap kuat pada teks **tercetak / terukir** yang justru paling sering difoto.
- Regenerasi: `.venv/bin/python eval/build_real_datasets.py --only print --print-per-class 56`
