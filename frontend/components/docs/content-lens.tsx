"use client"

import Link from "next/link"
import { Callout, Code, CodeBlock, DocSection, DocTable, Steps } from "./primitives"

const A = ({ href, children }: { href: string; children: React.ReactNode }) => (
  <Link href={href} className="text-saffron-dark font-semibold hover:underline">{children}</Link>
)

/**
 * Dokumentasi fitur Lens — OCR kamera Aksara Bali + Latin dengan terjemahan otomatis.
 * Angka akurasi diambil dari `eval/results/OCR_LENS_MODELS.md` dan `OCR_LENS_PAGES.md`.
 */
export function ContentLens() {
  return (
    <>
      <p className="text-lg leading-relaxed">
        <strong>Lens Aksara</strong> membaca tulisan dari kamera ponsel maupun laptop: sorot kamera
        dibuka, tiap ± 1 detik satu frame dikirim ke server, dan hasilnya ditumpuk di atas gambar —
        kotak per aksara, bacaan Latin, dan arti kata. Tidak ada model awan pihak ketiga: seluruh
        proses memakai model yang sama dengan yang dikelola di <A href="/admin/ml">Panel Admin → Model ML</A>.
      </p>

      <DocSection id="cara-kerja" number="1." title="Cara kerja (enam tahap)">
        <Steps
          items={[
            { title: "Praproses", body: <>Dekode (EXIF dihormati) → grayscale → rentang kontras → ambang <em>Sauvola</em> adaptif → buang bercak → koreksi kemiringan. Teks kecil diperbesar dulu agar tebal goresan setara dengan data latih.</> },
            { title: "Segmentasi", body: <>Profil proyeksi horizontal memotong baris; komponen terhubung pada satu baris digabung menjadi gugus bila tumpang tindih horizontal (penanda di atas/bawah badannya). Gugus yang terlalu tinggi dipecah menjadi <em>badan + pangangge</em> (ulu, suku, pepet, gantungan).</> },
            { title: "Klasifikasi", body: <>Tiap potongan dinormalisasi ke kanvas 28×28 dan dinilai oleh CNN tugas <Code>aksara</Code> (26 kelas) dan/atau <Code>latin</Code> (36 kelas). <em>Test-time augmentation</em> rata-ratakan beberapa versi teraugmentasi untuk foto kamera.</> },
            { title: "Pilihan skrip", body: <>Per baris: baris mana yang lebih diyakini model Bali atau model Latin. Model Bali diberi keistimewaan bila ada bukti geometris (banyak gugus berpotongan ganda), karena model Latin sering “melihat” tulisan Bali sebagai lengkungan Latin.</> },
            { title: "Decoding", body: <>Beam search dengan model n-gram karakter yang dibangun dari kamus & materi repo (dalam ruang label kelas) — menekan urutan yang tidak mungkin, misalnya <Code>sa sa sa sa</Code>.</> },
            { title: "Rakitan & terjemahan", body: <>Label → Unicode Bali (basis + pangangge), lalu transliterasi dua arah memakai mesin proyek yang sama dengan halaman Translate, plus pencarian arti di kamus.</> },
          ]}
        />
        <Callout title="Mengapa tidak memakai cloud OCR?">
          Aplikasi ini dipakai sekolah dengan koneksi terbatas dan berisi data siswa. Semua inferensi
          berjalan di CPU server sendiri (NumPy murni, tanpa dependensi berat), bisa <Code>Dockerfile</Code>
          atau <Code>run.py</Code> saja, dan tetap jalan luring di jaringan sekolah.
        </Callout>
      </DocSection>

      <DocSection id="data" number="2." title="Dataset & asal data model">
        <DocTable
          head={["Paket", "Isi", "Jumlah", "Sumber"]}
          rows={[
            [<Code key="1">caraka-aksara-bali-v1</Code>, "Tulisan tangan aksara Bali per kelas (26 kelas)", "2.704 citra", "Dataset proyek Caraka (Bangkit) — <aksara-datasets>, diunduh lalu diperkecil/dedinaskan ulang oleh eval/build_real_datasets.py"],
            [<Code key="2">aksara-bali-print-v1</Code>, "Aksara Bali tercetak (Noto Sans Balinese) + degradasi ala foto", "1.456 citra", "Render prosedural repo (CC0), font OFL"],
            [<Code key="3">omniglot-latin-handwriting-v1</Code>, "Huruf Latin tulisan tangan", "520 citra", "Omniglot (brendenlake/omniglot, MIT)"],
            [<Code key="4">latin-print-v1</Code>, "Latin tercetak a–z 0–9, lima font DejaVu + degradasi", "2.016 citra", "Render prosedural repo (CC0)"],
          ]}
        />
        <p>
          augmentation dilakukan <em>saat training</em> (rotasi, geser, skala, coretan) sehingga dataset
          tersimpan tidak pernah tercemar. Dua kelas duplikat pada master file (<Code>tedong</Code>,{" "}
          <Code>adeg_adeg_tengenan</Code>) tidak dipakai agar satu bentuk tidak punya dua label; oleh
          karena itu tugas aksara berisi 26 kelas, bukan 28.
        </p>
        <Callout title="Kelas mana yang tidak ada?">
          Dataset Caraka memuat aksara tunggal, bukan bentuk <em>pasangan</em> (aksara + virama yang
          dirangkai menjadi satu ligatura, mis. <Code>ᬓ᭄ᬭ</Code> “kra”). Rangkaian seperti itu dibaca
          sebagai bentuk terdekat, sehingga teks lontar penuh bisa salah pada suku kata rangkai —
          inilah alasan fitur koreksi disediakan (§4).
        </Callout>
      </DocSection>

      <DocSection id="akurasi" number="3." title="Akurasi terukur">
        <p>Angka dijalankan pada split <em>test</em> yang tidak pernah dilihat model saat training.</p>
        <DocTable
          head={["Uji", "Tugas aksara", "Tugas latin"]}
          rows={[
            ["Akurasi per-aksara (semua test)", "94,29%", "98,07%"],
            ["Akurasi tulisan tangan nyata saja", "90,96% (n=387)", "89,74% (n=78)"],
            ["Top-3 (jawaban benar ada di 3 kandidat)", "99,7%", "100%"],
            ["F1 makro", "90,82%", "89,12%"],
            ["Halaman render terkontrol: exact baris / CER", "30% / 22%", "30% / 33–40%"],
            ["Kata tulisan tangan nyata (23 citra Caraka): mendekati (CER≤25%)", "69,6%", "—"],
          ]}
        />
        <p className="text-sm text-charcoal/60">
          Tabel lengkap dapat direproduksi dengan{" "}
          <Code>.venv/bin/python eval/train_ocr_models.py</Code> dan{" "}
          <Code>.venv/bin/python eval/evaluate_ocr.py</Code>; hasilnya ditulis ke{" "}
          <Code>eval/results/OCR_LENS_MODELS.md</Code> dan <Code>OCR_LENS_PAGES.md</Code>.
        </p>
        <Callout title="Kenapa akurasi halaman lebih rendah daripada akurasi per-aksara?">
          Pada foto, mesin harus menemukan sendiri batas aksara. Kesalahan segmentasi menular ke
          klasifikasi. Karena itu UI menyediakan kotak per aksara + kandidat: koreksi manusia tetap
          berharga dan langsung menjadi data latih.
        </Callout>
      </DocSection>

      <DocSection id="koreksi" number="4." title="Koreksi pengguna → retraining">
        <Steps
          items={[
            { title: "Ketuk kotak salah", body: <>Pada hasil baca, pilih aksara yang keliru (bisa dari overlay pada video atau dari daftar “Per baris”).</> },
            { title: "Pilih kandidat benar", body: <>Panel menampilkan 5 kandidat model beserta keyakinannya. Klik yang benar.</> },
            { title: "Kirim", body: <>Potongan gambarnya dikirim sebagai sampel <Code>source=camera, status=review</Code> — tidak langsung ikut training.</> },
            { title: "Admin meninjau", body: <>Tab <A href="/admin/ml?tab=lens">Lens &amp; OCR</A> di Panel Admin: <em>Terima</em> (masuk <Code>labeled</Code>), <em>Ganti label</em>, atau <em>Tolak</em>.</> },
            { title: "Latih ulang", body: <>Tombol <strong>Latih ulang dari data + koreksi</strong> menjalankan job training pada tugas tersebut; setelah selesai, tetapkan sebagai model produksi di tab Model &amp; Evaluasi.</> },
          ]}
        />
        <Callout title="Privasi">
          Frame kamera tidak disimpan. Yang disimpan hanya potongan yang <em>Anda koreksi</em>, dan
          itu pun masuk ke dataset sekolah sendiri. Nonaktifkan lewat{" "}
          <Code>POST/PUT /api/ocr/config</Code> → <Code>feedback.enabled=false</Code>.
        </Callout>
      </DocSection>

      <DocSection id="api" number="5." title="API">
        <CodeBlock>{`GET  /api/ocr/status            kesiapan model per tugas + bawaan pipeline + batas
POST /api/ocr/scan            { image: "data:image/jpeg;base64,…", options: {…} }
POST /api/ocr/scan/file       multipart (fallback / curl -F file=@foto.jpg)
POST /api/ocr/scan/annotate   JPEG berbingkai hasil baca (untuk dibagikan)
POST /api/ocr/feedback        kirim koreksi (crop + label)
GET  /api/ocr/feedback        [admin] antrean koreksi
POST /api/ocr/feedback/{id}/decide?task=aksara   [admin] accept|reject|relabel
POST /api/ocr/feedback/train  [admin] setujui semua + mulai training
GET  /api/ocr/config · PUT    [admin] opsi pipeline, batas, saklar koreksi
POST /api/ocr/models/install  [admin] pasang model bawaan repo ke store ML
GET  /api/ocr/selftest?task=aksara&font_size=48  [admin] uji pipeline tanpa dataset`}</CodeBlock>
        <p className="text-sm text-charcoal/60">
          Opsi yang dapat dioverride: <Code>script</Code>, <Code>tta</Code>, <Code>binarize</Code>,{" "}
          <Code>sauvola_window</Code>, <Code>sauvola_k</Code>, <Code>deskew</Code>,{" "}
          <Code>use_language_model</Code>, <Code>beam_width</Code>, <Code>top_k</Code>,{" "}
          <Code>merge_gap_ratio</Code>, <Code>word_gap_ratio</Code>, <Code>split_marks</Code>,{" "}
          <Code>split_width_ratio</Code>, <Code>resplit_below</Code>, <Code>upscale_small</Code>,{" "}
          <Code>target_line_height</Code>, <Code>script_margin</Code>, <Code>line_min_ink</Code>,{" "}
          <Code>max_glyphs</Code>, <Code>max_side</Code>. Nilai di luar rentang aman dijepit otomatis.
        </p>
      </DocSection>

      <DocSection id="masalah" number="6." title="Pemecahan masalah">
        <DocTable
          head={[" gejala", "Penyebab", "Solusi"]}
          rows={[
            ["Layar hitam / kamera tidak muncul", "Izin kamera ditolak atau situs bukan HTTPS (selain localhost)", "Izinkan kamera; akses lewat HTTPS. Gunakan tombol “Unggah foto”."],
            ["“Model OCR belum siap”", "Store ML kosong di server ini", "Panel Admin → Lens & OCR → Pasang model bawaan, atau latih dari tab Training"],
            ["Tidak ada teks terdeteksi", "Kontras rendah, bayangan, kamera miring", "Tambah cahaya, dekatkan kamera, aktifkan mode Presisi, atau ubah <Code>binarize</Code> ke <Code>otsu</Code>"],
            ["Aksara terpotong/pecah", "Goresan putus-putus (tinta/lontar)", "Pastikan close_iters ≥ 1 (bawaan 1), turunkan resplit_below, atau pakai mode Presisi"],
            ["Teks Latin terbaca sebagai Bali (atau sebaliknya)", "Skrip campur", "Pilih mode Aksara Bali / Latin alih-alih Otomatis"],
            ["Lambat pada foto resolusi besar", "Banyak kandidat × TTA", "Turunkan max_side; jangan naikkan max_glyphs; turunkan tta ke 0"],
          ]}
        />
        <p className="text-sm text-charcoal/60">
          Rincian teknis: <Code>docs/OCR_LENS.md</Code> di repo (arsitektur modul, keputusan desain,
          batas yang diketahui).
        </p>
      </DocSection>
    </>
  )
}
