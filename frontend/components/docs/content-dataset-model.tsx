"use client"

import Link from "next/link"
import { Callout, Code, CodeBlock, DocSection, DocTable, Steps } from "./primitives"

export function ContentDatasetModel() {
  return (
    <>
      <p className="text-lg leading-relaxed">
        Halaman ini mendokumentasikan <strong>dataset</strong> dan <strong>classifier</strong>{" "}
        pengenalan tulisan tangan Aksara Bali secara rinci. Classifier berjalan{" "}
        <strong>on-device</strong> di peramban (<Code>frontend/lib/aksara-recognition.ts</Code>) —
        tanpa API eksternal, tanpa server inference, dan bisa dipakai <strong>offline</strong>.
      </p>

      <DocSection id="ringkasan" number="1." title="Ringkasan">
        <DocTable
          head={["Aspek", "Nilai"]}
          rows={[
            ["Tipe classifier", "Template matching (AI lokal) — bukan neural-network training"],
            ["Fitur input", "Maska biner tinta 128×128 hasil normalisasi canvas"],
            ["Metrik kesamaan", "Chamfer distance dua arah (1, √2)"],
            ["Kandidat (kelas)", "304 glyph unik dari blok Unicode Balinese"],
            ["Sumber template", "Font Noto Sans Balinese (Google Fonts, SIL OFL 1.1)"],
            ["Ambang verifikasi", "correct ≥ 0.55 · close ≥ 0.35"],
            ["Ambang pengenalan", "confident ≥ 0.55 & margin ke kandidat #2 ≥ 0.07"],
            ["Akurasi (verifikasi)", "≈ 97% (rata-rata 5 seed)"],
          ]}
        />
        <Callout title='Kejelasan istilah "training"'>
          Classifier ini adalah <em>template matcher</em>: “training”-nya adalah{" "}
          <strong>rendering template glyph</strong> dari font + <strong>kalibrasi ambang</strong>{" "}
          pada dataset evaluasi — bukan optimasi bobot model. Istilah “dataset training” di sini
          merujuk pada dataset evaluasi/kalibrasi yang dipakai mengukur &amp; menyetel classifier.
        </Callout>
      </DocSection>

      <DocSection id="arsitektur" number="2." title="Arsitektur classifier">
        <CodeBlock>{`Tulisan tangan (canvas)
   │  komposit putih → biner (luminansi < 200 = tinta)
   ▼
Crop bbox tinta → skala (maintain aspect) → pusatkan → 128×128 maska
   │
   ▼
Chamfer distance transform (1, √2) — jarak tiap piksel ke tinta terdekat
   │
   ▼
Skor = 1 − rata-rata jarak dua arah / (0.14 × 128)      → [0, 1]
   │
   ├── classifyTracing : benar bila skor ≥ 0.55   (verifikasi / telusur)
   └── recognizeAksara : argmax skor, confident bila ≥ 0.55 & margin ≥ 0.07`}</CodeBlock>
        <p>Classifier dipakai di dua titik produk:</p>
        <Steps
          items={[
            {
              title: "Playground → Tulis Tangan (classifyTracing)",
              body: "Pengguna menelusuri siluet satu glyph target; sistem menilai benar/hampir/salah.",
            },
            {
              title: "Translate → Tulis Tangan (recognizeAksara)",
              body: "Pengguna menulis bebas satu aksara; sistem memilih kandidat terdekat dari 304 glyph.",
            },
          ]}
        />
      </DocSection>

      <DocSection id="dataset" number="3." title="Dataset">
        <p>
          Kandidat dibangun <strong>sepenuhnya dari codepoint Unicode</strong> (tidak mengetik
          glyph manual) agar tidak bergantung pada keyboard/font tertentu, melalui{" "}
          <Code>buildCandidateSet()</Code>:
        </p>
        <DocTable
          head={["Komponen", "Isi", "Jumlah"]}
          rows={[
            ["Aksara dasar (Wresastra 18)", "ha na ca ra ka da ta sa wa la ma ga ba nga pa ja ya nya", "18"],
            ["Tanda vokal & tengenan", "ulu, ulu sari, suku, suku ilut, taleng, taling detya, taleng tedong, pepet + bisah, surang, cecek", "11"],
            ["Aksara suara & Swalalita", "rentang U+1B05–U+1B59 (vokal independen, Sanskerta/Kawi)", "85"],
            ["Kombinasi cluster", "dasar + pangangge, serta dasar + adeg-adeg + gantungan", "504"],
            ["Total unik setelah deduplikasi", "", "304"],
          ]}
        />
        <p>
          Setiap template dirender dengan font <strong>Noto Sans Balinese</strong> ke canvas
          320×320 → biner → crop bbox → skala ke kotak 128×128 terpusat (template di-cache per
          sesi).
        </p>
        <p>
          Karena belum ada korpus tinta (ink) Aksara Bali publik berlabel, evaluasi memakai{" "}
          <strong>dataset sintetis</strong> yang mensimulasikan variasi tulisan tangan dari
          template font (harness <Code>eval/evaluate_handwriting.py</Code>):
        </p>
        <DocTable
          head={["Jenis sampel", "Simulasi", "Peran"]}
          rows={[
            ["Positif (telusur)", "rotasi ±2°, skala 0.94–1.06, translasi ±3 px, penebalan stroke 0–1 px", "pengguna menelusuri siluet target yang tampil"],
            ["Negatif (salah)", "coretan poligon acak 2–5 goresan", "tinta yang tidak cocok dengan target"],
          ]}
        />
      </DocSection>

      <DocSection id="metrik" number="4." title="Metrik kesamaan (detail)">
        <p>
          <Code>distanceTransform()</Code> menghitung jarak tiap piksel ke tinta terdekat memakai
          8-tetangga berbobot 1 (ortogonal) dan √2 (diagonal) — agar tahan terhadap ketebalan
          stroke.
        </p>
        <CodeBlock>{`sumA = Σ jarak tinta-a → bentuk-b      cntA = jumlah piksel tinta a
sumB = Σ jarak tinta-b → bentuk-a      cntB = jumlah piksel tinta b
avg  = (sumA/cntA + sumB/cntB) / 2
skor = clamp(1 − avg / (0.14 × 128), 0, 1)`}</CodeBlock>
        <DocTable
          head={["Fungsi", "Aturan"]}
          rows={[
            ["classifyTracing", "correct bila skor ≥ 0.55 · close bila ≥ 0.35"],
            ["recognizeAksara", "kandidat skor tertinggi · confident bila skor ≥ 0.55 dan unggul ≥ 0.07"],
          ]}
        />
      </DocSection>

      <DocSection id="evaluasi" number="5." title="Evaluasi & hasil">
        <p>
          Ambang produksi <Code>correct ≥ 0.55</Code>, 20 positif + 20 negatif per kelas, 18
          kelas, 5 seed acak:
        </p>
        <DocTable
          head={["Seed", "TP", "FN", "TN", "FP", "Akurasi"]}
          rows={[
            ["20260831", "360", "0", "341", "19", "97.36%"],
            ["20260832", "360", "0", "337", "23", "96.81%"],
            ["20260833", "360", "0", "338", "22", "96.94%"],
            ["20260834", "360", "0", "344", "16", "97.78%"],
            ["20260835", "360", "0", "331", "29", "95.97%"],
            ["Rata-rata", "", "", "", "", "96.97%"],
          ]}
        />
        <Callout variant="success" title="Akurasi verifikasi ≈ 97% (≥ 90%)">
          Rentang 95.97–97.78%. Tidak ada satu pun tulisan target yang salah ditolak (FN = 0),
          dan coretan acak hampir selalu ditolak (TN dominan).
        </Callout>
        <Callout variant="warning" title="Pengenalan terbuka 18 kelas — dilaporkan jujur">
          Pada pengenalan <em>tanpa target</em>, top-1 ≈ 5.6% (≈ peluang 1/18) karena sejumlah
          aksara (na ᬦ, da ᬤ, ta ᬢ, ca ᬘ) nyaris identik — jarak chamfer antar-template ±1 px pada
          128×128. Karena itu <Code>recognizeAksara</Code> memakai <strong>confident-gating</strong>{" "}
          (margin ≥ 0.07): bila tidak yakin sistem <strong>abstain</strong>, bukan menebak — lebih
          baik tidak menjawab daripada salah mengajari.
        </Callout>
      </DocSection>

      <DocSection id="retraining" number="6." title="Model terlatih (retraining) — Panel Admin">
        <p>
          Keterbatasan pengenalan terbuka di atas dijawab dengan pipeline <strong>retraining</strong>{" "}
          di Panel Admin (<Link href="/admin/ml" className="text-saffron-dark font-semibold hover:underline">/admin/ml</Link>):
          dataset tulisan tangan dikelola &amp; dilabeli admin, lalu classifier{" "}
          <strong>belajar dari data</strong> dan dievaluasi otomatis. Model produksi yang dipilih
          admin dilayani server lewat <Code>POST /api/ml/predict</Code>.
        </p>
        <DocTable
          head={["Aspek", "Nilai"]}
          rows={[
            ["Fitur input", "Tinta dinormalisasi (crop → 20 px → pusat massa) pada 28×28 → vektor 784-d"],
            ["Arsitektur", "template (chamfer) · nearest centroid · k-NN · regresi logistik · MLP · CNN — murni NumPy, CPU"],
            ["Dataset", "Sintetis (font + augmentasi afinitas/elastis/tebal/noise), unggahan, kanvas, koreksi dari percobaan"],
            ["Split", "train/val/test 70/15/15 · stratified per label"],
            ["Evaluasi", "accuracy · precision/recall/F1 makro & berbobot · top-3 · log-loss · confusion matrix · per kelas · kurva pelatihan"],
            ["Reproduksi", <Code key="c">.venv/bin/python eval/ml_experiments.py --ablation</Code>],
          ]}
        />
        <p>
          <strong>Percobaan</strong> (18 kelas Wresastra, 60 sampel sintetis/kelas = 1080, split
          756/162/162, hyperparameter default, evaluasi pada test; kolom <em>shift</em> = 360 sampel
          baru dengan augmentasi 1.6× lebih kuat):
        </p>
        <DocTable
          head={["Arsitektur", "Accuracy", "Precision", "Recall", "F1 (makro)", "Top-3", "Acc (shift)", "Latih"]}
          rows={[
            ["Template matching", "74.7%", "81.2%", "74.7%", "75.1%", "85.2%", "40.0%", "0.5 s"],
            ["Nearest centroid", "84.6%", "87.1%", "84.6%", "84.7%", "92.0%", "45.0%", "< 0.1 s"],
            ["k-NN (k=5)", "84.6%", "85.6%", "84.6%", "84.4%", "97.5%", "51.4%", "< 0.1 s"],
            ["Regresi logistik", "91.4%", "92.2%", "91.4%", "91.3%", "98.2%", "56.7%", "0.1 s"],
            ["MLP (128 hidden)", "93.2%", "93.6%", "93.2%", "93.2%", "98.2%", "58.6%", "0.5 s"],
            [<strong key="n">CNN</strong>, <strong key="a">98.2%</strong>, <strong key="p">98.4%</strong>, <strong key="r">98.2%</strong>, <strong key="f">98.2%</strong>, "98.2%", <strong key="s">63.6%</strong>, "5.7 s"],
          ]}
        />
        <p>Ablasi ukuran data (akurasi test saat sampel per kelas bertambah):</p>
        <DocTable
          head={["Arsitektur", "10/kelas", "20/kelas", "40/kelas", "80/kelas"]}
          rows={[
            ["Regresi logistik", "69.4%", "87.0%", "91.7%", "96.3%"],
            ["MLP", "66.7%", "81.5%", "89.8%", "96.3%"],
            ["CNN", "61.1%", "75.9%", "87.0%", "94.4%"],
          ]}
        />
        <Callout variant="success" title="Kesimpulan percobaan">
          Pengenalan terbuka 18 kelas naik dari ≈ 75% (template) menjadi <strong>98.2% (CNN)</strong>{" "}
          pada data sintetis, dan CNN paling tahan pergeseran distribusi. Untuk data sedikit
          (≤ 20/kelas) regresi logistik lebih aman; CNN/MLP unggul mulai ≥ 40–80 sampel/kelas —
          target pengumpulan tulisan nyata: <strong>≥ 80 per aksara</strong>.
        </Callout>
        <Callout variant="warning" title="Batas klaim">
          Akurasi pada set <em>shift</em> (≤ 64%) menegaskan angka test sintetis bukan klaim performa
          pada tulisan tangan manusia. Model produksi harus divalidasi ulang dengan sampel nyata yang
          dikumpulkan lewat tab Dataset. Detail metodologi: <Code>docs/ML_RETRAINING.md</Code>,
          laporan mentah: <Code>eval/results/ml_experiments.md</Code>.
        </Callout>
      </DocSection>

      <DocSection id="reproduksi" number="7." title="Reproduksi">
        <CodeBlock>{`# Dependensi: Pillow + NumPy + font Noto Sans Balinese (diunduh otomatis)
cd eval
python -m venv .venv && .venv/bin/pip install Pillow numpy
.venv/bin/python evaluate_handwriting.py            # unduh font + jalankan
.venv/bin/python evaluate_handwriting.py --font /path/NotoSansBalinese.ttf

# Percobaan retraining (6 arsitektur + ablasi) — memakai venv backend dari root repo
.venv/bin/python eval/ml_experiments.py --ablation \\
    --out-md eval/results/ml_experiments.md --out-json eval/results/ml_experiments.json`}</CodeBlock>
        <p>
          Detail lengkap (termasuk formula &amp; referensi) tersedia di{" "}
          <Code>docs/DATASET_MODEL.md</Code> dan <Code>docs/ML_RETRAINING.md</Code>.
        </p>
      </DocSection>
    </>
  )
}
