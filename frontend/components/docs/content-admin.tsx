"use client"

import Link from "next/link"
import { Screenshot } from "./screenshot"
import { Callout, Code, CodeBlock, DocSection, DocTable, Steps } from "./primitives"

export function ContentAdmin() {
  return (
    <>
      <p className="text-lg leading-relaxed">
        Halaman ini untuk <strong>admin</strong> platform: cara mengakses panel admin, memahami
        mode <em>dev</em> &amp; <em>prod</em>, dan mengatur halaman dokumentasi mana saja yang
        <em> go public</em>.
      </p>

      <DocSection id="akses" number="1." title="Akses panel admin">
        <p>
          Panel admin berada di{" "}
          <Link href="/admin" className="text-saffron-dark font-semibold hover:underline">
            /admin
          </Link>{" "}
          — bisa dibuka dari ikon gerbang (🛡) di pojok kanan atas header, atau ketik langsung
          URL-nya.
        </p>
        <Steps
          items={[
            {
              title: "Mode dev → tanpa login",
              body: (
                <>
                  Saat backend berjalan dalam mode <Code>dev</Code>, semua pengunjung dianggap
                  admin: panel langsung terbuka dan badge “DEV” tampil. Ini disengaja agar
                  pengembangan &amp; demo mudah.
                </>
              ),
            },
            {
              title: "Mode prod → halaman login",
              body: (
                <>
                  Saat backend dalam mode <Code>prod</Code> dan belum login, Anda
                  diarahkan ke halaman <Link href="/login" className="text-saffron-dark font-semibold hover:underline">/login</Link>.
                  Pilih peran <strong>Admin</strong>, masukkan <strong>username &amp; password</strong> yang
                  diset operator (env <Code>AKSARA_ADMIN_USERNAME</Code> / <Code>AKSARA_ADMIN_PASSWORD</Code>),
                  lalu klik “Masuk”. Sesi tersimpan di peramban — klik “Keluar” untuk menghapusnya.
                </>
              ),
            },
          ]}
        />
        <Screenshot
          src="/screenshots/login.png"
          alt="Halaman login AKSA dengan pilihan peran Guru dan Admin"
          caption="Halaman login: pilih peran (Guru/Admin) lalu masukkan username & password sesuai env backend."
          url="aksara.local/login"
        />
        <Screenshot
          src="/screenshots/admin.png"
          alt="Panel admin AKSA dengan pengaturan publikasi dokumentasi"
          caption="Panel admin: status mode, pengatur publikasi halaman dokumentasi, dan informasi sistem."
          url="aksara.local/admin"
        />
      </DocSection>

      <DocSection id="mode" number="2." title="Memahami mode dev & prod">
        <DocTable
          head={["Aspek", "Mode DEV", "Mode PROD"]}
          rows={[
            ["Halaman dokumentasi", "Semua halaman tampil (termasuk yang privat, dengan badge “Privat”)", "Hanya halaman yang dipublikasikan admin"],
            ["Akses panel admin", "Otomatik, tanpa login", "Wajib login username & password admin"],
            ["Ubah status publikasi", "Boleh (untuk persiapan konten)", "Boleh — langsung berdampak pada apa yang terlihat pengunjung"],
            ["Pengguna biasa", "Melihat semua halaman dokumentasi", "Melihat halaman publik saja; halaman privat tidak bisa dibuka"],
          ]}
        />
        <Callout title="Cara menyetel mode">
          Mode dibaca dari backend: env <Code>AKSARA_MODE</Code> (nilai <Code>dev</Code> atau{" "}
          <Code>prod</Code>, default <Code>dev</Code>). Frontend mengikuti apa yang dijawab API
          <Code> /api/docs/pages</Code> — tidak ada setting terpisah di sisi frontend.
        </Callout>
      </DocSection>

      <DocSection id="publikasi" number="3." title="Atur halaman mana yang go public">
        <p>
          Di panel admin, bagian <strong>“Publikasi Dokumentasi”</strong> menampilkan seluruh
          halaman dokumentasi dengan sakelar (toggle) <em>Public / Privat</em>:
        </p>
        <Steps
          items={[
            {
              title: "Buka panel admin",
              body: "Pastikan mode backend prod (atau dev untuk mencoba).",
            },
            {
              title: "Temukan halaman yang ingin diubah",
              body: "Setiap baris: ikon, judul, role (murid/guru/admin/metodologi), status saat ini.",
            },
            {
              title: "Geser sakelar",
              body: (
                <>
                  <em>Public</em> = halaman muncul di menu <Link href="/docs" className="text-saffron-dark font-semibold hover:underline">Dokumentasi</Link>{" "}
                  dan bisa dibuka semua pengunjung. <em>Privat</em> = disembunyikan dari pengunjung
                  biasa (tetap bisa dibuka admin &amp; mode dev).
                </>
              ),
            },
            {
              title: "Perubahan tersimpan otomatis",
              body: (
                <>
                  Setiap penggeseran langsung disimpan ke <Code>backend/app/data/docs.json</Code>{" "}
                  melalui API <Code>PATCH /api/docs/pages/:slug/visibility</Code>.
                </>
              ),
            },
          ]}
        />
        <Screenshot
          src="/screenshots/docs.png"
          alt="Halaman hub dokumentasi yang menampilkan halaman publik"
          caption="Halaman Dokumentasi yang dilihat pengunjung: hanya halaman publik yang muncul (mode prod)."
          url="aksara.local/docs"
        />
        <Callout variant="warning" title="Catatan operasional">
          Status publikasi disimpan di file <Code>docs.json</Code> pada backend. Untuk
          deployment multi-instance, sinkronkan file ini (atau migrasikan ke database) agar
          semua instance konsisten.
        </Callout>
      </DocSection>

      <DocSection id="model-ml" number="4." title="Model ML — retraining classifier aksara">
        <p>
          Bagian <strong>“Model ML — Klasifikasi Aksara Bali”</strong> di panel admin (tombol{" "}
          <em>Buka panel ML</em>, route{" "}
          <Link href="/admin/ml" className="text-saffron-dark font-semibold hover:underline">/admin/ml</Link>)
          adalah tempat mengelola <strong>dataset tulisan tangan</strong>, <strong>labeling</strong>,{" "}
          <strong>retraining</strong> classifier, membaca <strong>laporan evaluasi</strong>, dan
          memilih <strong>model produksi</strong>. Semua model berjalan murni NumPy di CPU server —
          tidak butuh GPU atau dependensi berat.
        </p>
        <Steps
          items={[
            {
              title: "Tab Dataset & Labeling — kumpulkan dan beri label",
              body: (
                <>
                  Tambah sampel lewat <em>Generate sintetis</em> (glyph font Noto Sans Balinese +
                  augmentasi), <em>Unggah gambar</em> (PNG/JPG, boleh tanpa label), atau{" "}
                  <em>Tulis di kanvas</em>. Sampel tanpa label masuk <strong>antrean labeling</strong>;
                  beri label satu-satu atau massal (pilih banyak → label / pindah split / hapus).
                  Atur <em>kelas aktif</em> (default 18 Wresastra; bisa tambah Swalalita, Suara,
                  Angka) dan <em>acak ulang split 70/15/15</em> (stratified) sebelum melatih.
                </>
              ),
            },
            {
              title: "Tab Training — pilih arsitektur & jalankan retraining",
              body: (
                <>
                  Pilih salah satu dari 6 arsitektur: <Code>template</Code> (chamfer, baseline),{" "}
                  <Code>centroid</Code>, <Code>knn</Code>, <Code>logreg</Code>, <Code>mlp</Code>,{" "}
                  <Code>cnn</Code>. Form hyperparameter (epoch, learning rate, batch, hidden units,
                  dropout, …) menyesuaikan arsitektur. Klik <strong>Mulai Retraining</strong>: job
                  berjalan di server, progress + kurva loss/akurasi tampil langsung, bisa dibatalkan.
                  Centang <em>langsung jadikan model produksi</em> bila ingin otomatis dipromosikan.
                </>
              ),
            },
            {
              title: "Tab Model & Evaluasi — baca metrik, pilih produksi",
              body: (
                <>
                  Registry semua model dengan <strong>accuracy, precision, recall, F1 (makro)</strong>,
                  train acc, durasi, ukuran. Klik baris untuk laporan lengkap: metrik makro &amp;
                  berbobot, top-3, log-loss, tabel <strong>per kelas</strong>,{" "}
                  <strong>confusion matrix</strong>, kurva pelatihan, dan galeri contoh salah
                  klasifikasi. Tombol <strong>Jadikan produksi</strong> menetapkan model yang dipakai{" "}
                  <Code>POST /api/ml/predict</Code>; tombol daya menonaktifkannya.
                </>
              ),
            },
            {
              title: "Tab Percobaan — uji dan koreksi",
              body: (
                <>
                  Tulis aksara di kanvas atau unggah gambar → prediksi dengan model pilihan, lihat
                  top-k probabilitas dan fitur 28×28 yang “dilihat” model. <em>Bandingkan semua
                  model</em> menjalankan input yang sama ke seluruh registry. Prediksi yang salah
                  bisa langsung <strong>disimpan ke dataset</strong> dengan label benar, lalu
                  retraining ulang (human-in-the-loop).
                </>
              ),
            },
          ]}
        />
        <DocTable
          head={["Arsitektur", "Accuracy", "Precision", "Recall", "F1 (makro)", "Latih"]}
          rows={[
            ["Template matching (chamfer)", "74.7%", "81.2%", "74.7%", "75.1%", "0.5 s"],
            ["Nearest centroid", "84.6%", "87.1%", "84.6%", "84.7%", "< 0.1 s"],
            ["k-NN (k=5)", "84.6%", "85.6%", "84.6%", "84.4%", "< 0.1 s"],
            ["Regresi logistik", "91.4%", "92.2%", "91.4%", "91.3%", "0.1 s"],
            ["MLP (128 hidden)", "93.2%", "93.6%", "93.2%", "93.2%", "0.5 s"],
            [<strong key="cnn">CNN</strong>, <strong key="a">98.2%</strong>, <strong key="p">98.4%</strong>, <strong key="r">98.2%</strong>, <strong key="f">98.2%</strong>, "5.7 s"],
          ]}
        />
        <Callout variant="success" title="Hasil percobaan (eval/ml_experiments.py)">
          Dataset sintetis 18 kelas Wresastra, 60 sampel/kelas (1080), split stratified
          756/162/162, hyperparameter default, evaluasi pada split test, CPU 2 core. Angka ini
          adalah metrik pada data sintetis — validasi akhir memakai tulisan tangan nyata yang
          dikumpulkan lewat tab Dataset. Rincian, uji pergeseran distribusi, dan ablasi ukuran
          data ada di <Code>docs/ML_RETRAINING.md</Code>.
        </Callout>
        <Callout variant="warning" title="Catatan operasional">
          Artefak ML (PNG sampel, <Code>model.npz</Code>, registry) tersimpan di{" "}
          <Code>backend/app/data/ml/</Code> — ikut volume data, tidak dikomit ke git. Hanya satu
          job training berjalan pada satu waktu; model produksi tidak bisa dihapus sebelum
          dinonaktifkan.
        </Callout>
      </DocSection>

      <DocSection id="api" number="5." title="API & variabel lingkungan (ringkasan)">
        <CodeBlock>{`# Variabel lingkungan backend
AKSARA_MODE=prod                          # dev | prod
AKSARA_ADMIN_USERNAME=admin               # username admin
AKSARA_ADMIN_PASSWORD=ganti-password      # password admin (wajib diganti di prod)

# Contoh API
POST /auth/login                           # body: {"role":"admin","username":"...","password":"..."}
GET  /api/docs/pages                       # daftar halaman + mode + is_admin
PATCH /api/docs/pages/:slug/visibility     # body: {"is_public": true|false}
       Header: Authorization: Bearer <session>   # sesi dari /auth/login

# Model ML (admin, kecuali status & predict)
GET  /api/ml/status                        # dataset, model produksi, job aktif
POST /api/ml/dataset/generate-synthetic    # {"per_class":60,"seed":20260904,"strength":1.0}
POST /api/ml/dataset/samples               # {"image":"data:image/png;base64,...","label":"ha"|null}
POST /api/ml/train  → 202                  # {"arch":"cnn","hyperparams":{"epochs":15},"auto_promote":false}
GET  /api/ml/train/jobs                    # progress + kurva per epoch
GET  /api/ml/models/:id                    # {model, report}: precision/recall/F1 per kelas, confusion matrix
PUT  /api/ml/models/production             # {"model_id": "..."} | {"model_id": null}
POST /api/ml/predict                       # publik: {"image": "...", "top_k": 5}`}</CodeBlock>
        <p>
          Endpoint <Code>GET /api/docs/pages</Code> membalas field <Code>mode</Code> (
          <Code>dev|prod</Code>) dan <Code>is_admin</Code> — frontend memakai keduanya untuk
          memutuskan halaman mana yang ditampilkan.
        </p>
      </DocSection>
    </>
  )
}
