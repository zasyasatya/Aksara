"use client"

import Link from "next/link"
import { Screenshot as BaseScreenshot } from "./screenshot"
import { Callout, Code, CodeBlock, DocSection, DocTable, Steps } from "./primitives"

/** Semua tangkapan layar 1440×900 → tinggi 480 pada lebar 768px agar bingkai utuh. */
const Screenshot = (props: React.ComponentProps<typeof BaseScreenshot>) => <BaseScreenshot height={480} {...props} />

const A = ({ href, children }: { href: string; children: React.ReactNode }) => (
  <Link href={href} className="text-saffron-dark font-semibold hover:underline">{children}</Link>
)

/**
 * Panduan langkah demi langkah retraining classifier aksara Bali di Panel Admin.
 * Semua screenshot direkam dari alur nyata (frontend/public/screenshots/ml/).
 */
export function ContentRetraining() {
  return (
    <>
      <p className="text-lg leading-relaxed">
        Panduan ini menuntun <strong>admin</strong> dari nol sampai punya model klasifikasi aksara
        Bali yang aktif di produksi: <em>impor dataset → labeling → pilih arsitektur → latih →
        baca evaluasi → tetapkan model produksi → uji &amp; koreksi</em>. Setiap langkah disertai
        screenshot dari panel yang sebenarnya. Waktu total untuk alur dasar ± 10 menit.
      </p>

      <DocSection id="ringkasan" number="0." title="Ringkasan alur">
        <DocTable
          head={["#", "Tahap", "Tab di /admin/ml", "Hasil"]}
          rows={[
            ["1", "Impor dataset dari repo (1.080 gambar berlabel)", "Dataset & Labeling", "Dataset siap latih, split 756/162/162"],
            ["2", "Tambah & beri label tulisan tangan nyata", "Dataset & Labeling", "Sampel baru berlabel, masuk split"],
            ["3", "Pilih arsitektur + hyperparameter, jalankan job", "Training", "Model terlatih + laporan evaluasi otomatis"],
            ["4", "Bandingkan metrik, baca laporan per kelas", "Model & Evaluasi", "Model terbaik teridentifikasi"],
            ["5", "Jadikan model produksi", "Model & Evaluasi", "Dipakai POST /api/ml/predict"],
            ["6", "Uji tulisan, bandingkan model, koreksi → dataset", "Percobaan", "Data baru untuk retraining berikutnya"],
          ]}
        />
        <Callout title="Prasyarat">
          Backend berjalan (mode <Code>dev</Code> otomatis admin; mode <Code>prod</Code> login
          sebagai Admin di <A href="/login">/login</A>). Tidak butuh GPU: semua model murni NumPy
          di CPU. Dataset gambar tersedia di folder <Code>dataset/</Code> repo (lihat §1).
        </Callout>
      </DocSection>

      <DocSection id="masuk" number="1." title="Masuk ke panel Model ML">
        <p>
          Buka <A href="/admin">/admin</A>. Seksi <strong>“Model ML — Klasifikasi Aksara
          Bali”</strong> menampilkan ringkasan dataset, jumlah model, dan model produksi. Klik{" "}
          <strong>Buka panel ML</strong> (atau salah satu pintasan tab) untuk masuk ke{" "}
          <A href="/admin/ml">/admin/ml</A>.
        </p>
        <Screenshot
          src="/screenshots/ml/01-admin-seksi-ml.png"
          alt="Panel admin dengan seksi Model ML: dataset kosong, belum ada model"
          caption="Panel admin sebelum ada apa-apa: 0 sampel, 0 model, belum ada model produksi."
          url="aksara.local/admin"
        />
        <Screenshot
          src="/screenshots/ml/02-dataset-kosong.png"
          alt="Halaman /admin/ml tab Dataset & Labeling dalam keadaan kosong"
          caption="Tab Dataset & Labeling saat kosong. Empat tab di atas mengikuti urutan alur kerja."
          url="aksara.local/admin/ml?tab=dataset"
        />
      </DocSection>

      <DocSection id="dataset" number="2." title="Siapkan dataset (impor dari repo)">
        <p>
          Repo menyertakan paket dataset gambar <Code>dataset/aksara-bali-handwriting-v1/</Code>:
          <strong> 1.080 PNG 64×64</strong>, 18 kelas Wresastra × 60 sampel, sudah berlabel dan
          punya split train/val/test (756/162/162, stratified). Ini dataset yang sama dengan yang
          dipakai percobaan di dokumen <A href="/docs/dataset-dan-model">Dataset &amp; Model</A>.
        </p>
        <Steps
          items={[
            { title: "Klik “Impor dataset repo”", body: "Panel menampilkan paket yang tersedia beserta jumlah gambar, kelas, split, seed, dan lisensi." },
            {
              title: "Periksa opsi impor",
              body: (
                <>
                  <em>Aktifkan kelas paket</em> (kelas aktif mengikuti manifest), <em>Ganti impor
                  sebelumnya</em> (impor ulang tidak menggandakan data), <em>Pakai split manifest</em>{" "}
                  (hasil bisa dibandingkan langsung dengan angka di dokumentasi).
                </>
              ),
            },
            { title: "Klik “Impor 1.080 gambar”", body: "Impor memakan ± 3–5 detik. Statistik di atas langsung terisi." },
          ]}
        />
        <Screenshot
          src="/screenshots/ml/03-impor-dataset-repo.png"
          alt="Panel Impor dataset dari repo dengan paket aksara-bali-handwriting-v1 dan opsi impor"
          caption="Panel impor: paket aksara-bali-handwriting-v1 (1.080 gambar, 18 kelas, seed 20260904, CC0) + tiga opsi impor."
          url="aksara.local/admin/ml?tab=dataset"
        />
        <Screenshot
          src="/screenshots/ml/04-dataset-terisi.png"
          alt="Statistik dataset setelah impor: 1080 berlabel, split 756/162/162"
          caption="Setelah impor: 1.080 sampel berlabel, 0 antrean, split 756 / 162 / 162, semua 18 kelas terisi 60 sampel."
          url="aksara.local/admin/ml?tab=dataset"
        />
        <Screenshot
          src="/screenshots/ml/05-distribusi-kelas.png"
          alt="Distribusi sampel per kelas, 60 sampel tiap aksara"
          caption="Distribusi per kelas (klik kelas untuk memfilter galeri). Kelas tanpa data ditandai merah — training akan menolak sampai terisi."
          url="aksara.local/admin/ml?tab=dataset"
        />
        <Callout title="Alternatif: Generate sintetis">
          Tombol <strong>Generate sintetis</strong> membuat sampel baru dari font Noto Sans
          Balinese dengan augmentasi (pilih jumlah/kelas, seed, kekuatan). Gunakan untuk menambah
          variasi atau untuk kelas di luar Wresastra (Swalalita, Suara, Angka) yang tidak ada di
          paket repo. Paket dataset sendiri dibangun ulang dengan{" "}
          <Code>.venv/bin/python eval/build_dataset.py</Code>.
        </Callout>
      </DocSection>

      <DocSection id="labeling" number="3." title="Tambah tulisan tangan nyata & labeling">
        <p>
          Dataset sintetis hanya titik awal. Akurasi pada tulisan siswa sungguhan naik bila
          dataset berisi <strong>tinta nyata</strong>. Ada tiga jalur masuk:
        </p>
        <Steps
          items={[
            {
              title: "Unggah gambar (PNG/JPG, bisa banyak sekaligus)",
              body: (
                <>
                  Label ditebak dari nama file (<Code>ha_01.png</Code> → <em>ha</em>) dan bisa diubah
                  per file. Kosongkan label untuk memasukkan gambar ke <em>antrean labeling</em>.
                </>
              ),
            },
            { title: "Tulis di kanvas", body: "Pilih label, (opsional) tampilkan siluet pemandu, tulis, simpan — cocok saat guru mendemonstrasikan bentuk aksara." },
            { title: "Koreksi dari tab Percobaan", body: "Prediksi yang salah bisa disimpan sebagai sampel dengan label benar (lihat §7)." },
          ]}
        />
        <Screenshot
          src="/screenshots/ml/06-unggah-gambar.png"
          alt="Panel unggah gambar dengan label default dan split"
          caption="Panel Unggah gambar: pilih banyak file, tentukan label default & split, atau biarkan tanpa label."
          url="aksara.local/admin/ml?tab=dataset"
        />
        <Screenshot
          src="/screenshots/ml/07-tulis-kanvas.png"
          alt="Panel Tulis di kanvas dengan pilihan label dan siluet pemandu"
          caption="Panel Tulis di kanvas: pilih aksara target, tulis dengan mouse/pena/sentuh, simpan langsung ke dataset."
          url="aksara.local/admin/ml?tab=dataset"
        />
        <p>
          <strong>Kelas aktif</strong> menentukan aksara mana yang ikut dilatih. Default 18
          Wresastra; centang Swalalita/Suara/Angka bila datanya sudah ada.
        </p>
        <Screenshot
          src="/screenshots/ml/08-kelas-aktif.png"
          alt="Panel Kelas aktif dengan daftar aksara per kelompok"
          caption="Panel Kelas aktif: kelas dikelompokkan (Wresastra, Swalalita, Suara, Angka) dengan jumlah sampel masing-masing."
          url="aksara.local/admin/ml?tab=dataset"
        />
        <p>
          Sampel tanpa label muncul di tombol <strong>Antrean labeling</strong> (dengan jumlah).
          Klik kartu untuk membuka detail, pilih label, split, status, lalu <em>Simpan</em>. Untuk
          banyak sampel sekaligus: centang beberapa kartu → bilah aksi massal (beri label, pindah
          split, tandai <em>review</em>, hapus).
        </p>
        <Screenshot
          src="/screenshots/ml/09-antrean-labeling.png"
          alt="Galeri sampel difilter tanpa label, tiga kartu menunggu label"
          caption="Antrean labeling: tiga unggahan tanpa label. Filter label/split/sumber/status ada di atas galeri."
          url="aksara.local/admin/ml?tab=dataset"
        />
        <Screenshot
          src="/screenshots/ml/10-detail-sampel-label.png"
          alt="Dialog detail sampel: gambar, fitur 28×28, form label/split/status/catatan"
          caption="Detail sampel: pratinjau fitur 28×28 yang “dilihat” model, pilih label & split, simpan atau hapus."
          url="aksara.local/admin/ml?tab=dataset"
        />
        <Callout variant="warning" title="Split & kebocoran data">
          Setiap sampel punya split tetap; evaluasi hanya memakai split <strong>test</strong>.
          Setelah menambah banyak data baru, klik <em>Acak ulang split 70/15/15</em> agar tiap
          kelas terwakili di test secara proporsional. Jangan memindahkan sampel test ke train
          hanya untuk menaikkan angka.
        </Callout>
      </DocSection>

      <DocSection id="training" number="4." title="Pilih arsitektur & jalankan retraining">
        <p>
          Tab <strong>Training</strong> menampilkan banner kesiapan dataset, enam kartu
          arsitektur, dan form konfigurasi yang menyesuaikan arsitektur terpilih.
        </p>
        <DocTable
          head={["Arsitektur", "Kapan dipakai", "Perkiraan durasi*"]}
          rows={[
            ["Template Matching (chamfer)", "Baseline pembanding — tidak belajar dari data", "< 1 dtk"],
            ["Nearest Centroid", "Sanity-check dataset", "< 1 dtk"],
            ["k-Nearest Neighbours", "Data sangat sedikit; tanpa asumsi bentuk", "< 1 dtk"],
            ["Regresi Logistik", "Data ≤ 20/kelas; cepat & stabil", "≈ 0.1 dtk"],
            ["Multi-Layer Perceptron", "Data 40+/kelas; akurat & masih cepat", "≈ 0.5–7 dtk"],
            ["CNN", "Akurasi terbaik, paling tahan variasi goresan", "≈ 6–15 dtk"],
          ]}
        />
        <p className="text-sm text-charcoal/60">*1.080 sampel, CPU 2 core, hyperparameter default.</p>
        <Screenshot
          src="/screenshots/ml/11-training-pilih-arsitektur.png"
          alt="Tab Training: banner dataset siap, enam kartu arsitektur, form konfigurasi"
          caption="Tab Training: banner “Dataset siap dilatih”, kartu arsitektur dengan kelebihan/kekurangan, form konfigurasi di kanan."
          url="aksara.local/admin/ml?tab=training"
        />
        <Steps
          items={[
            { title: "Pilih arsitektur", body: "Klik kartu (mis. Convolutional Neural Network). Form hyperparameter berubah mengikuti arsitektur." },
            {
              title: "Atur hyperparameter & nama",
              body: (
                <>
                  Default sudah aman. Untuk CNN: epoch 12–20, learning rate 0.004, batch 64. Beri nama
                  yang deskriptif (mis. <em>CNN v1 — dataset repo</em>) dan catatan supaya registry mudah
                  dibaca. Centang <em>langsung jadikan model produksi</em> hanya bila Anda yakin.
                </>
              ),
            },
            { title: "Klik “Mulai Retraining”", body: "Job berjalan di server; halaman boleh ditinggal — progres tersimpan di server selama proses hidup." },
          ]}
        />
        <Screenshot
          src="/screenshots/ml/12-training-konfigurasi-cnn.png"
          alt="Konfigurasi CNN: epoch 12, learning rate 0.004, nama model, catatan"
          caption="Konfigurasi CNN: epoch, learning rate, batch size, filter conv-1/2, neuron FC, dropout, nama, catatan, opsi auto-promosi."
          url="aksara.local/admin/ml?tab=training"
        />
        <Screenshot
          src="/screenshots/ml/13-training-berjalan.png"
          alt="Kartu job berjalan: progress bar, epoch 14/60, kurva akurasi train/val dan loss, tombol Batalkan"
          caption="Job berjalan: progress bar, epoch saat ini, loss & val acc, kurva train-vs-val live, tombol Batalkan. Riwayat di bawah mencatat semua job sesi ini."
          url="aksara.local/admin/ml?tab=training"
        />
        <Screenshot
          src="/screenshots/ml/14-training-selesai.png"
          alt="Riwayat pelatihan: CNN v1 selesai dengan akurasi 94.4% dan F1 94.4%"
          caption="Selesai: ringkasan accuracy / precision / recall / F1 langsung tampil di riwayat; model tersimpan permanen di registry."
          url="aksara.local/admin/ml?tab=training"
        />
        <Callout title="Tips membaca kurva">
          Akurasi <em>train</em> yang terus naik sementara <em>val</em> stagnan/turun = overfit →
          kurangi epoch, naikkan dropout/weight decay, atau tambah data. Loss yang tidak turun sama
          sekali = learning rate terlalu besar/kecil.
        </Callout>
      </DocSection>

      <DocSection id="evaluasi" number="5." title="Baca laporan evaluasi">
        <p>
          Tab <strong>Model &amp; Evaluasi</strong> memuat registry semua model. Kolom bisa diurutkan;
          label <em>F1 terbaik</em> dan <em>overfit?</em> (train acc − test acc &gt; 15 poin) membantu
          memilih. Klik baris untuk laporan lengkap.
        </p>
        <Screenshot
          src="/screenshots/ml/15-registry-model.png"
          alt="Registry model: empat model dengan accuracy, precision, recall, F1, durasi, ukuran"
          caption="Registry: MLP v2, MLP v1, Regresi logistik v1, CNN v1 — bandingkan accuracy, precision, recall, F1 makro, train acc, durasi, ukuran."
          url="aksara.local/admin/ml?tab=models"
        />
        <Screenshot
          src="/screenshots/ml/16-laporan-evaluasi.png"
          alt="Laporan evaluasi CNN v1: accuracy 94.44%, precision 94.94%, recall 94.44%, F1 94.42%, top-3, log-loss, hyperparameter"
          caption="Laporan CNN v1: tile accuracy / precision / recall / F1 (makro & berbobot), top-3, log-loss, confident-rate, ukuran split, hyperparameter, pasangan paling sering tertukar."
          url="aksara.local/admin/ml?tab=models"
        />
        <DocTable
          head={["Metrik", "Arti praktis"]}
          rows={[
            ["Accuracy", "Proporsi sampel test yang ditebak benar."],
            ["Precision (per kelas)", "Dari semua tebakan “ka”, berapa yang benar-benar ka — rendah = model sering salah menebak kelas itu."],
            ["Recall (per kelas)", "Dari semua ka sebenarnya, berapa yang tertangkap — rendah = kelas sering terlewat."],
            ["F1", "Rata-rata harmonik precision & recall; angka utama untuk membandingkan model."],
            ["Makro vs berbobot", "Makro: tiap kelas bobot sama (adil untuk kelas kecil). Berbobot: proporsional jumlah sampel."],
            ["Top-3 / Log-loss", "Apakah jawaban benar ada di 3 teratas; seberapa terkalibrasi probabilitasnya (kecil = baik)."],
            ["Train acc vs test acc", "Selisih besar = overfit."],
          ]}
        />
        <Screenshot
          src="/screenshots/ml/17-laporan-per-kelas.png"
          alt="Tabel per kelas: precision, recall, F1, support, TP/FP/FN untuk 18 aksara"
          caption="Per kelas: precision / recall / F1 / support / TP-FP-FN dengan bar F1 — cepat terlihat aksara mana yang lemah."
          url="aksara.local/admin/ml?tab=models"
        />
        <Screenshot
          src="/screenshots/ml/18-confusion-matrix.png"
          alt="Confusion matrix 18×18 dengan diagonal hijau dan kesalahan merah, plus galeri contoh salah klasifikasi"
          caption="Confusion matrix (baris = label asli, kolom = prediksi). Sel di luar diagonal menunjukkan pasangan aksara yang tertukar; di bawahnya galeri contoh salah klasifikasi."
          url="aksara.local/admin/ml?tab=models"
        />
        <Screenshot
          src="/screenshots/ml/19-kurva-pelatihan.png"
          alt="Kurva pelatihan: akurasi train dan val serta loss per epoch"
          caption="Kurva pelatihan per epoch (loss, akurasi train vs val) tersimpan bersama model — berguna untuk menyetel epoch pada retraining berikutnya."
          url="aksara.local/admin/ml?tab=models"
        />
      </DocSection>

      <DocSection id="produksi" number="6." title="Tetapkan model produksi">
        <p>
          Klik <strong>Jadikan produksi</strong> pada baris model pilihan. Banner hijau di atas
          registry menandai model aktif; sejak itu <Code>POST /api/ml/predict</Code> (tanpa{" "}
          <Code>model_id</Code>) memakai model tersebut. Tombol daya di banner menonaktifkan
          produksi; model produksi tidak bisa dihapus sebelum dinonaktifkan.
        </p>
        <Screenshot
          src="/screenshots/ml/20-model-produksi.png"
          alt="Banner Model produksi aktif: CNN v1 — dataset repo, accuracy 94.4%, F1 94.4%"
          caption="CNN v1 kini model produksi: banner hijau + ringkasan metrik; kartu status di atas ikut berubah."
          url="aksara.local/admin/ml?tab=models"
        />
        <Callout variant="success" title="Kriteria promosi yang disarankan">
          F1 makro tertinggi <em>dan</em> tidak ada kelas dengan recall &lt; 60% <em>dan</em> selisih
          train–test &lt; 15 poin. Bila dua model setara, pilih yang lebih kecil/cepat (MLP/logreg)
          untuk server terbatas, atau CNN bila tulisan pengguna sangat bervariasi.
        </Callout>
      </DocSection>

      <DocSection id="percobaan" number="7." title="Uji, bandingkan, koreksi">
        <p>
          Tab <strong>Percobaan</strong> menutup siklus: tulis aksara (atau unggah gambar), pilih
          <em> target</em> bila ingin menilai, klik <strong>Prediksi</strong>. Hasil menampilkan
          top-k probabilitas, margin, dan pratinjau fitur 28×28.
        </p>
        <Screenshot
          src="/screenshots/ml/21-percobaan-prediksi.png"
          alt="Tab Percobaan: coretan di kanvas, hasil prediksi ha 23.5% kurang yakin, target ra"
          caption="Contoh prediksi yang RAGU (23.5%, ditandai “kurang yakin”): coretan sederhana tidak mirip aksara mana pun — inilah kandidat koreksi."
          url="aksara.local/admin/ml?tab=experiment"
        />
        <Steps
          items={[
            { title: "Bandingkan semua model", body: "Input yang sama dijalankan ke seluruh registry — cepat terlihat model mana yang paling konsisten pada tulisan nyata." },
            { title: "Koreksi & simpan ke dataset", body: "Pilih label benar → Simpan. Sampel masuk dataset (sumber: kanvas) dengan split otomatis." },
            { title: "Retraining ulang", body: "Setelah terkumpul cukup koreksi (idealnya ≥ 20 per kelas yang lemah), ulangi §4 dan bandingkan F1 sebelum–sesudah di registry." },
          ]}
        />
        <Screenshot
          src="/screenshots/ml/22-percobaan-bandingkan.png"
          alt="Perbandingan antar model pada input yang sama: MLP v2, MLP v1, CNN v1 dengan top-3 masing-masing"
          caption="Perbandingan antar model untuk input yang sama — tiga model ragu dengan jawaban berbeda: sinyal jelas bahwa bentuk ini belum ada di dataset."
          url="aksara.local/admin/ml?tab=experiment"
        />
        <Screenshot
          src="/screenshots/ml/23-admin-selesai.png"
          alt="Panel admin setelah alur selesai: 1.083 berlabel, 4 model, produksi CNN v1"
          caption="Kembali ke /admin: ringkasan kini menampilkan dataset, jumlah model, dan model produksi beserta metriknya."
          url="aksara.local/admin"
        />
      </DocSection>

      <DocSection id="api" number="8." title="Alur yang sama lewat API (otomasi)">
        <CodeBlock>{`# 1. impor dataset repo (admin)
curl -X POST http://localhost:8000/api/ml/dataset/import-bundled \\
  -H "Content-Type: application/json" -H "Authorization: Bearer $SESSION" \\
  -d '{"name":"aksara-bali-handwriting-v1"}'

# 2. tambah sampel berlabel / tanpa label (labeling lewat PATCH)
curl -X POST http://localhost:8000/api/ml/dataset/samples -H "Authorization: Bearer $SESSION" \\
  -H "Content-Type: application/json" -d '{"image":"data:image/png;base64,...","label":"ka","source":"upload"}'
curl -X PATCH http://localhost:8000/api/ml/dataset/samples/<id> -H "Authorization: Bearer $SESSION" \\
  -H "Content-Type: application/json" -d '{"label":"ka","split":"train"}'

# 3. retraining → 202 + job id, lalu pantau
curl -X POST http://localhost:8000/api/ml/train -H "Authorization: Bearer $SESSION" \\
  -H "Content-Type: application/json" -d '{"arch":"cnn","hyperparams":{"epochs":15},"name":"CNN v1"}'
curl -H "Authorization: Bearer $SESSION" http://localhost:8000/api/ml/train/jobs/<job_id>

# 4–5. laporan evaluasi & promosi
curl -H "Authorization: Bearer $SESSION" http://localhost:8000/api/ml/models/<model_id>
curl -X PUT http://localhost:8000/api/ml/models/production -H "Authorization: Bearer $SESSION" \\
  -H "Content-Type: application/json" -d '{"model_id":"<model_id>"}'

# 6. prediksi (publik)
curl -X POST http://localhost:8000/api/ml/predict -H "Content-Type: application/json" \\
  -d '{"image":"data:image/png;base64,...","top_k":5}'`}</CodeBlock>
        <p>
          Spesifikasi lengkap: <Code>docs/API_SPEC.md</Code> (bagian ML). Metodologi & hasil
          percobaan: <Code>docs/ML_RETRAINING.md</Code>; panduan ini dalam bentuk markdown:{" "}
          <Code>docs/PANDUAN_RETRAINING.md</Code>.
        </p>
      </DocSection>

      <DocSection id="masalah" number="9." title="Pemecahan masalah">
        <DocTable
          head={["Gejala", "Penyebab umum", "Solusi"]}
          rows={[
            ["Tombol Mulai Retraining menolak: “kelas tanpa sampel”", "Kelas aktif punya 0 data", "Nonaktifkan kelas itu di Kelas aktif, atau tambah data"],
            ["“Masih ada job yang berjalan”", "Hanya satu job per server", "Tunggu selesai atau Batalkan di kartu job"],
            ["Akurasi bagus di test, jelek di tulisan nyata", "Dataset didominasi sintetis", "Kumpulkan tinta nyata (unggah/kanvas/koreksi), acak ulang split, latih ulang"],
            ["Train acc 100%, test jauh di bawah", "Overfit", "Kurangi epoch, naikkan dropout/weight decay, tambah data"],
            ["Prediksi selalu “kurang yakin”", "Goresan terlalu kecil/terpotong", "Tulis besar di tengah kanvas; cek pratinjau 28×28"],
            ["Impor dataset repo tidak muncul", "Folder dataset/ tidak ada di server", "Set env AKSARA_DATASET_DIR atau bangun ulang dengan eval/build_dataset.py"],
            ["Model produksi tidak bisa dihapus", "Masih aktif", "Nonaktifkan lewat tombol daya di banner, lalu hapus"],
          ]}
        />
      </DocSection>
    </>
  )
}
