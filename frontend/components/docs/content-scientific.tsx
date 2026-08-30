"use client"

import { Screenshot } from "./screenshot"
import { Callout, Code, CodeBlock, DocSection, DocTable, Steps } from "./primitives"

export function ContentScientific() {
  return (
    <>
      <p className="text-lg leading-relaxed">
        Halaman ini adalah dedikasi khusus untuk menjelaskan <strong>metode ilmiah (scientific
        method)</strong> yang dipakai platform AKSA dalam menyajikan materi dan melakukan
        transliterasi Aksara Bali, serta <strong>referensi akademik</strong> yang mendasarinya.
        Tujuannya: transparansi — siapa pun bisa menelusuri <em>mengapa</em> sebuah hasil
        transliterasi muncul, dan sumber mana yang melandasi setiap aturan.
      </p>

      <DocSection id="pendekatan" number="1." title="Pendekatan: rule-based + dictionary (hybrid)">
        <p>
          Platform menggunakan pendekatan <strong>hybrid</strong>:
        </p>
        <Steps
          items={[
            {
              title: "Rule-based (mesin aturan)",
              body: (
                <>
                  Engine transliterasi (
                  <Code>backend/app/services/transliterator.py</Code>, ~1000 baris) menerapkan
                  aturan linguistik Aksara Bali secara eksplisit: pemilahan suku kata, resolusi
                  gantungan, pemetaan pangangge, hingga komposisi Unicode. Aturan yang eksplisit
                  bisa diverifikasi, dijelaskan ke pengguna, dan diperbaiki satu-satu.
                </>
              ),
            },
            {
              title: "Dictionary (kamus kata khusus)",
              body: (
                <>
                  21 entri di <Code>backend/app/data/dictionary.json</Code> menangani kata yang
                  tidak bisa dihasilkan aturan umum (mis. <em>angklung</em>, <em>aksara</em>,{" "}
                  <em>bleganjur</em>, <em>om swastyastu</em>). Dictionary diprioritaskan sebelum
                  aturan — pola “kamus dulu, aturan kemudian” adalah praktik umum sistem
                  transliterasi berbasis aturan.
                </>
              ),
            },
          ]}
        />
        <Callout title="Mengapa bukan black-box?">
          Untuk konteks edukasi, keterlacakan (traceability) lebih penting daripada sekadar akurasi:
          setiap hasil transliterasi disertai <strong>breakdown</strong> per-suku-kata dan{" "}
          <strong>warning</strong> aturan — sehingga guru/murid bisa belajar dari prosesnya,
          bukan hanya hasilnya.
        </Callout>
      </DocSection>

      <DocSection id="pipeline" number="2." title="Pipeline transliterasi">
        <p>Arah <strong>Latin → Aksara Bali</strong>:</p>
        <Steps
          items={[
            { title: "1. Normalisasi", body: (
              <>
                Unicode NFC, kapitalisasi, pembersihan karakter tidak dikenal —
                karakter tak dikenal dilaporkan via <Code>warnings</Code> (bukan diam-diam dibuang).
              </>
            ) },
            { title: "2. Tokenizer & pemilahan suku kata", body: (
              <>
                Teks dipecah per kata, lalu per suku kata mengikuti pola konsonan-vokal
                (CMVS) — mengikuti pendekatan pemilahan suku kata berbasis finite state machine.
              </>
            ) },
            { title: "3. Cek dictionary", body: "Bila kata ada di kamus → gunakan bentuk kamus langsung." },
            { title: "4. Gantungan resolver", body: (
              <>
                Cluster konsonan tengah dirapikan menjadi gantungan (mis. “ks” dalam aksara);
                aturan <strong>tumpuk telu</strong> memastikan maksimal 1 gantungan per aksara dasar.
              </>
            ) },
            { title: "5. Pangangge mapper", body: (
              <>
                Vokal & penanda dipetakan: ulu (i), suku (u), taleng (e), pepet (ě), bisah (h),
                surang (r), cecek (ng), adeg-adeg (penutup vokal).
              </>
            ) },
            { title: "6. Unicode composer", body: (
              <>
                Aksara dirakit dari blok Unicode Balinese <Code>U+1B00–U+1B7F</Code>.
              </>
            ) },
            { title: "7. Validasi & pelaporan", body: (
              <>
                Output akhir: <Code>result</Code> + <Code>breakdown</Code> + <Code>confidence</Code>{" "}
                + <Code>warnings</Code>.
              </>
            ) },
          ]}
        />
        <p>Arah <strong>Aksara Bali → Latin</strong> memakai pipeline kebalikan:{" "}
          <Code>Bali Parser → Unicode Decomposer → Pangangge Detector → Gantungan Parser → Latin Composer</Code>.</p>
        <Screenshot
          src="/screenshots/translate.png"
          alt="Halaman translate memperlihatkan breakdown aturan hasil transliterasi"
          caption="Panel breakdown di halaman Translate adalah “bukti kerja” pipeline: per suku kata & aturan yang dipakai."
          url="aksara.local/translate"
        />
      </DocSection>

      <DocSection id="aturan" number="3." title="Aturan penting yang diimplementasi">
        <DocTable
          head={["Aturan", "Deskripsi", "Contoh / Dampak"]}
          rows={[
            [
              "Tumpuk telu",
              "Maksimal 1 gantungan per aksara dasar; 3 lapis gantungan dilarang.",
              "Dua gantungan berurutan pada satu aksara → sistem mencegah & memperingatkan.",
            ],
            [
              "Pepet + Cakra",
              "Kombinasi dilarang karena secara fonetik tidak mungkin.",
              "Engine menolak membentuk pasangan ini (warning).",
            ],
            [
              "La gantungan + Pepet",
              "Diizinkan secara khusus (bleganjur).",
              "ᬩᬼᬕᬜ᭄ᬚᬸᬃ — entri dictionary khusus.",
            ],
            [
              "Gantungan vs Adeg-adeg",
              "Gantungan untuk cluster konsonan tengah; adeg-adeg untuk konsonan akhir kata.",
              "“saka” → ᬲᬓ (ka gantungan, bunyi “k” tanpa vokal di tengah).",
            ],
            [
              "Cecek vs Nga gantungan",
              "Akhiran -ng ditulis cecek (◌ᬂ); medial -ng- ditulis nga gantungan (◌᭄ᬗ).",
              "Pembedaan posisi fonetik, bukan satu tanda untuk semua.",
            ],
          ]}
        />
        <Callout variant="info" title="Sumber aturan">
          Aturan-aturan di atas dirumuskan dari rujukan akademik & pedoman penulisan di bagian
          <a href="#referensi" className="font-semibold underline"> Referensi</a>, lalu
          diuji lewat suite pytest (bagian<em> Validasi</em>).
        </Callout>
      </DocSection>

      <DocSection id="validasi" number="4." title="Validasi & evaluasi">
        <p>
          Setiap aturan dibuktikan dengan <strong>uji otomatis</strong> (pytest) di{" "}
          <Code>backend/app/tests/test_transliterator.py</Code>:
        </p>
        <Steps
          items={[
            {
              title: "Kasus uji kurasi",
              body: (
                <>
                  14 kasus Latin → Bali dan 4 kasus Bali → Latin yang dikurasi dari literatur
                  akademik & kata umum (mis. <em>bali → ᬩᬮᬶ</em>, <em>angklung → bentuk kamus</em>),
                  plus kasus edge: teks kosong, teks panjang, dan deteksi tumpuk telu.
                </>
              ),
            },
            {
              title: "Uji deteksi tumpuk telu",
              body: (
                <>
                  <Code>has_tumpuk_telu()</Code> wajib mendeteksi 2 gantungan berurutan
                  (dilarang) dan membebaskan 1 gantungan (boleh).
                </>
              ),
            },
            {
              title: "Uji override dictionary",
              body: "Kata kamus harus menghasilkan bentuk eksak (mis. angklung) ketika dictionary aktif.",
            },
            {
              title: "Uji analisis gantungan",
              body: (
                <>
                  <Code>analyze_gantungan()</Code> membalas struktur analisis yang konsisten
                  (jumlah gantungan, dsb.) untuk input berbeda.
                </>
              ),
            },
            {
              title: "Validasi tulisan murid",
              body: (
                <>
                  Endpoint <Code>POST /api/quiz/validate-pair</Code> membandingkan tulisan murid
                  dengan kunci: mode <Code>exact</Code> (identik) atau <Code>tolerant</Code>{" "}
                  (toleransi variasi) — dasar asesmen objektif.
                </>
              ),
            },
          ]}
        />
        <CodeBlock>{`# Menjalankan seluruh uji backend
cd backend
pytest -v --cov=app

# Contoh validasi tulisan murid
curl -X POST http://localhost:8000/api/quiz/validate-pair \\
  -H "Content-Type: application/json" \\
  -d '{"question_latin": "bali", "question_bali": "ᬩᬮᬶ",
       "user_bali": "ᬩᬮᬶ", "mode": "exact"}'
# => {"is_correct": true, "similarity": 1.0, "suggestions": []}`}</CodeBlock>
        <Callout variant="warning" title="Kejujuran limitasi">
          Mesin rule-based tidak sempurna: karakter/kombinasi di luar aturan tetap menghasilkan
          output dengan <em>warning</em> eksplisit (bukan hasil yang “dipaksakan”). Target
          akurasi platform ≥95% pada kosakata umum; kata-kata khusus diatasi lewat dictionary.
          Setiap bug transliterasi yang ditemukan sebaiknya dilaporkan beserta kasusnya —
          itu bahan perbaikan aturan berikutnya.
        </Callout>
      </DocSection>

      <DocSection id="referensi" number="5." title="Referensi">
        <p>
          Sumber-sumber yang mendasari material pembelajaran, aturan transliterasi, dan desain
          sistem ini:
        </p>
        <ol className="list-decimal space-y-3 pl-5">
          <li>
            <strong>Jampel, I. N., Indrawan, G., &amp; Widiana, I. W. (2018).</strong>{" "}
            <em>Accuracy Analysis of Latin-to-Balinese Script Transliteration Method.</em>{" "}
            International Journal of Electrical and Computer Engineering (IJECE), 8(3), 1788–1797.
          </li>
          <li>
            <strong>Library of Congress (2025).</strong>{" "}
            <em>Balinese Romanization Table</em> (2025 version) — pedoman romanisasi resmi,
            berbasis prinsip ISO 15919:2001 dengan modifikasi.
          </li>
          <li>
            <strong>The Unicode Consortium.</strong>{" "}
            <em>The Unicode Standard</em> — blok Balinese <Code>U+1B00–U+1B7F</Code>
            (Unicode Charts: Balinese).
          </li>
          <li>
            <strong>Nala, I. B. K. (2006).</strong>{" "}
            <em>Pedoman Aksara Bali.</em> Pedoman penulisan & istilah aksara Bali.
          </li>
          <li>
            <strong>Sanjani, D. A. P. P., Indrawan, G., &amp; Gunadi, I. G. A. (2021).</strong>{" "}
            <em>Pengembangan Metode Pemilahan Suku Kata Pada Transliterasi Teks Latin Ke Aksara
            Bali Berbasis Finite State Machine Dengan Font Noto Serif Balinese.</em> Jurnal Ilmu
            Komputer Indonesia (JIK), 6(2).
          </li>
          <li>
            <strong>AksaraDinusantara.com</strong> — sumber font & katalog aksara nusantara
            (termasuk Bali) yang dipakai sebagai rujukan bentuk glyph.
          </li>
          <li>
            <strong>Google Fonts (SIL Open Font License 1.1).</strong>{" "}
            <em>Noto Sans Balinese</em> — font rendering Unicode Balinese yang dipakai UI.
          </li>
        </ol>
        <Callout title="Cara mengutip">
          Platform ini adalah perangkat edukasi. Untuk kutipan ilmiah, rujuk sumber primer di
          atas (terutama [1] untuk analisis akurasi transliterasi dan [2] untuk romanisasi).
        </Callout>
      </DocSection>

      <DocSection id="perluasan" number="6." title="Cara memperluas basis pengetahuan">
        <Steps
          items={[
            {
              title: "Tambah entri dictionary",
              body: (
                <>
                  Tambahkan kata khusus ke <Code>backend/app/data/dictionary.json</Code> dengan
                  struktur: <Code>latin, bali, meaning, note</Code> — lalu pastikan ada kasus
                  uji yang memastikannya.
                </>
              ),
            },
            {
              title: "Tambah aturan engine",
              body: (
                <>
                  Ubah <Code>transliterator.py</Code> dengan pola: satu aturan = satu fungsi
                  kecil + satu set kasus uji. Jangan gabungkan banyak aturan dalam satu blok.
                </>
              ),
            },
            {
              title: "Tambah kasus uji",
              body: (
                <>
                  Setiap aturan baru wajib disertai kasus di{" "}
                  <Code>test_transliterator.py</Code> — “no rule without a test”.
                </>
              ),
            },
            {
              title: "Dokumentasikan",
              body: (
                <>
                  Catat aturan & sumbernya di halaman ini dan <Code>docs/</Code> (PRD /
                  ARCHITECTURE) agar pelacakan tetap utuh.
                </>
              ),
            },
          ]}
        />
      </DocSection>
    </>
  )
}
