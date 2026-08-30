"use client"

import Link from "next/link"
import { Screenshot } from "./screenshot"
import { Callout, DocSection, Steps } from "./primitives"

export function ContentMurid() {
  return (
    <>
      <p className="text-lg leading-relaxed">
        Halo! <span className="font-bali text-deep-brown">ᬅᬓ᭄ᬱᬭ</span> — selamat datang di Aksara.
        Halaman ini membimbingmu langkah demi langkah memanfaatkan platform: mulai dari
        melihat progres, belajar per level, menulis aksara, hingga menguji kemampuanmu lewat kuis.
      </p>
      <Callout title="Kamu tidak perlu daftar akun (MVP)">
        Progres (XP, streak, level, pelajaran selesai) tersimpan otomatis di peramban kamu.
        Buka halaman yang sama di perangkat/peramban yang sama untuk melanjutkan belajar.
      </Callout>

      <DocSection id="dashboard" number="1." title="Kenali Dashboard — pusat progresmu">
        <p>
          Setiap kali membuka aplikasi, kamu akan mendarat di{" "}
          <Link href="/dashboard" className="text-saffron-dark font-semibold hover:underline">
            Dashboard
          </Link>
          . Di sana kamu melihat tiga angka penting: <strong>streak</strong> (berapi 🔥) —
          berapa hari beruntun kamu belajar, <strong>XP</strong> — poin pengalaman, dan{" "}
          <strong>level</strong> kamu saat ini.
        </p>
        <p>
          Bagian bawah dashboard menampilkan <strong>pelajaran berikutnya</strong> yang
          disarankan beserta persentase keseluruhan progresmu. Klik kartu pelajaran untuk
          langsung mulai belajar.
        </p>
        <Screenshot
          src="/screenshots/dashboard.png"
          alt="Halaman dashboard Aksara menampilkan streak, XP, level, dan rekomendasi pelajaran"
          caption="Dashboard: lihat streak, XP, level, dan pelajaran yang direkomendasikan untuk dilanjutkan."
          url="aksara.local/dashboard"
        />
      </DocSection>

      <DocSection id="belajar" number="2." title="Belajar bertahap lewat menu Belajar">
        <p>
          Buka menu <strong>Belajar</strong> di bar navigasi atas (atau tombol <em>Belajar</em> di
          bawah untuk perangkat ponsel). Seluruh materi tersusun dalam <strong>11 pelajaran</strong>{" "}
          di 6 level, dari yang paling dasar:
        </p>
        <Steps
          items={[
            {
              title: "Level 1 — Pemula (Wresastra 18)",
              body: (
                <>
                  4 pelajaran: <span className="font-bali">ᬳᬦᬘᬭᬓ</span> — 18 aksara dasar
                  (Ha Na Ca Ra Ka, Da Ta Sa Wa La, Pa Dha Ja Ya Nya, Ma Ga Ba Tha Nga).
                </>
              ),
            },
            {
              title: "Level 2 — Pangangge Suara",
              body: (
                <>
                  Vokal: <span className="font-bali">ᬶᬸᬾ</span> — ulu (i), suku (u), taleng (e),
                  dan pepet (ě).
                </>
              ),
            },
            {
              title: "Level 3 — Tengenan",
              body: (
                <>
                  Akhiran: <span className="font-bali">ᬄᬃᬂ</span> — bisah (h), surang (r), cecek (ng).
                </>
              ),
            },
            {
              title: "Level 4 — Gantungan",
              body: "Cluster konsonan seperti -ng-, -ny-, dan cakra (ra gantungan).",
            },
            {
              title: "Level 5 — Swalalita",
              body: "Aksara untuk kata serapan Sanskerta & Kawi.",
            },
            {
              title: "Level 6 — Kalimat",
              body: "Merangkai kata menjadi kalimat utuh dalam Aksara Bali.",
            },
          ]}
        />
        <p>
          Gunakan tombol filter <em>Semua Level</em> / level tertentu untuk memfilter daftar
          pelajaran. Pelajaran yang sudah kamu selesaikan ditandai centang hijau.
        </p>
        <Screenshot
          src="/screenshots/learn.png"
          alt="Halaman daftar pelajaran Aksara dengan filter level"
          caption="Halaman Belajar: 11 pelajaran tersusun per level, dengan filter dan penanda selesainya."
          url="aksara.local/learn"
        />
      </DocSection>

      <DocSection id="pelajaran" number="3." title="Selesaikan satu pelajaran">
        <p>Klik salah satu kartu pelajaran untuk masuk ke detailnya. Di dalam:</p>
        <Steps
          items={[
            {
              title: "Lihat visual setiap aksara",
              body: "Bentuk aksara tampil besar dengan nama Latin di bawahnya.",
            },
            {
              title: "Perhatikan cara menulis",
              body: "Urutan coretan dan bentuk akhir setiap aksara dijelaskan satu per satu.",
            },
            {
              title: "Dengarkan & baca contoh kata",
              body: "Setiap aksara dilengkapi contoh kata agar kamu paham pemakaiannya.",
            },
            {
              title: "Tandai selesai untuk dapat XP",
              body: (
                <>
                  Setelah yakin paham, tekan tombol selesaikan — XP bertambah dan pelajaran
                  ditandai centang di daftar <em>Belajar</em>.
                </>
              ),
            },
          ]}
        />
        <Screenshot
          src="/screenshots/lesson-detail.png"
          alt="Halaman detail pelajaran menampilkan aksara, cara menulis, dan contoh kata"
          caption="Detail pelajaran: visual aksara, cara menulis, dan contoh kata untuk tiap aksara."
          url="aksara.local/learn/wresastra-01"
        />
        <Callout variant="warning" title="Jangan lompat level">
          Level disusun kumulatif — gantungan, misalnya, butuh penguasaan aksara dasar dulu.
          Ikur urutan agar pemahamanmu kuat.
        </Callout>
      </DocSection>

      <DocSection id="kuis" number="4." title="Uji diri dengan Kuis validasi">
        <p>
          Buka menu <strong>Kuis</strong>. Ada beberapa tipe soal, dan kamu bisa memfilternya
          dengan tombol di atas: <strong>pilihan ganda</strong> (tekan aksara yang tepat),{" "}
          <strong>benar/salah</strong>, <strong>gantungan</strong>, dan yang baru —{" "}
          <strong>“Menulis Aksara”</strong>: kamu melihat kata Latin, lalu <strong>menulis
          aksaranya sendiri</strong> (ketik, paste, atau pilih dari keyboard virtual), dan sistem
          memvalidasi tulisanmu.
        </p>
        <p>
          Setiap jawaban langsung dinilai dengan <strong>feedback detail</strong> — bukan cuma
          “benar/salah”, tapi juga penjelasannya, misalnya: <em>“Seharusnya pakai gantungan,
          bukan adeg-adeg”</em>. Kuis menulis juga menampilkan <strong>persen kemiripan</strong>{" "}
          tulisanmu dengan kunci. Jawab benar memberikan XP.
        </p>
        <Screenshot
          src="/screenshots/quiz.png"
          alt="Halaman kuis dengan filter tipe soal"
          caption="Halaman Kuis: filter tipe soal + penilaian langsung dan penjelasan."
          url="aksara.local/quiz"
        />
        <Screenshot
          src="/screenshots/quiz-write.png"
          alt="Kuis menulis aksara dengan keyboard virtual"
          caption="Tipe “Menulis Aksara”: tulis kata dari soal (pakai keyboard virtual bila perlu), lalu cek jawabanmu."
          url="aksara.local/quiz?type=write_aksara"
        />
      </DocSection>

      <DocSection id="translate" number="5." title="Latih penerjemahan Latin ↔ Aksara (dua arah)">
        <p>
          Menu <strong>Translate</strong> mengubah teks Latin ke Aksara Bali <em>dan sebaliknya</em>{" "}
          secara langsung saat kamu mengetik. Klik pill <strong>Latin / Bali</strong> (atau tombol
          Tukar) untuk membalik arah. Saat arahnya <strong>Bali → Latin</strong>, aksara bisa
          <strong> diketik, ditempel, atau dipilih</strong> lewat tombol{" "}
          <em>“Buka Keyboard Aksara”</em>. Gunakan ini untuk:
        </p>
        <Steps
          items={[
            {
              title: "Menulis nama atau kalimat",
              body: (
                <>
                  Ketik “aksara bali” dan lihat hasilnya:{" "}
                  <span className="font-bali text-deep-brown">ᬅᬓ᭄ᬱᬭ ᬩᬮᬶ</span>.
                </>
              ),
            },
            {
              title: "Membaca aksara (Bali → Latin)",
              body: (
                <>
                  Pilih aksara dari keyboard virtual — mis.{" "}
                  <span className="font-bali text-deep-brown">ᬩᬮᬶ</span> — dan lihat padanan Latin
                  “bali”. Latihan membaca yang bagus.
                </>
              ),
            },
            { title: "Pelajari breakdown", body: "Panel di bawah hasil menjabarkan setiap suku kata & aturan yang dipakai engine." },
            { title: "Cek confidence", body: "Skor keyakinan engine (0–1). Dekat 1 artinya hasil sangat terpercaya." },
            { title: "Salin hasilnya", body: "Tombol salin memudahkan kamu menyalin aksara ke aplikasi lain." },
          ]}
        />
        <Screenshot
          src="/screenshots/translate.png"
          alt="Halaman translate dua arah dengan keyboard aksara"
          caption="Translate dua arah: Bali → Latin memakai keyboard virtual, dengan breakdown aturan dan skor confidence."
          url="aksara.local/translate"
        />
      </DocSection>

      <DocSection id="playground" number="6." title="Bermain bebas di Playground">
        <p>
          <strong>Playground</strong> adalah keyboard virtual Aksara Bali: ketuk aksara{" "}
          <span className="font-bali">ᬳᬘᬭ…</span>, pangangge <span className="font-bali">ᬶᬸᬾᭂ</span>,
          atau tanda seperti bisah, surang, cecek — lalu baca hasilnya dalam Latin secara real-time.
          Tempat terbaik untuk bermain sambil belajar sebelum menghadapi kuis.
        </p>
        <Screenshot
          src="/screenshots/playground.png"
          alt="Playground keyboard virtual Aksara Bali"
          caption="Playground: ketik aksara bebas dengan keyboard virtual dan transliterasi langsung."
          url="aksara.local/playground"
        />
      </DocSection>

      <DocSection id="twibbon" number="7." title="Bikin twibbon aksara & bagikan ke medsos">
        <p>
          <strong>Studio Twibbon</strong> (menu <Link href="/twibbon" className="text-saffron-dark font-semibold hover:underline">Twibbon</Link>)
          membuat <strong>foto kamu + tulisan Aksara Bali</strong> dalam satu gambar siap
          dibagikan. Teks ditulis dalam Latin, lalu <strong>otomatis diterjemahkan ke aksara</strong>{" "}
          memakai engine translate yang sama — atau kamu bisa mem-paste aksara langsung.
        </p>
        <Steps
          items={[
            { title: "Unggah foto", body: "Pilih foto dari perangkat, atau pakai foto contoh. Ada 3 rasio: 4:5 (post IG), 1:1 (kotak), 9:16 (story/reels)." },
            { title: "Tulis teks", body: "Ketik kalimat Latin (mis. “matur suksma”) — aksaranya muncul otomatis; atur ukuran, posisi, warna, bayangan, dan teks Latin kecil di bawahnya." },
            { title: "Pilih bingkai", body: "10 gaya twibbon: margin krem, garis ganda, garis titik, dua gradasi, sudut klasik, strip aksara “warisan”, polaroid, sudut bulat, dan polos." },
            { title: "Bagikan", body: "Tombol Bagikan memakai berbagi peramban (WhatsApp/IG/X) — atau Unduh PNG 1080px lalu unggah manual; hasil juga bisa disalin ke clipboard." },
          ]}
        />
        <Screenshot
          src="/screenshots/twibbon.png"
          alt="Studio Twibbon: foto pura dengan tulisan aksara matur suksma dan bingkai strip aksara"
          caption="Studio Twibbon: foto + aksara hasil translate + bingkai pilihan — langsung bisa dishare ke sosial media."
          url="aksara.local/twibbon"
        />
      </DocSection>

      <DocSection id="tips" number="8." title="Tips belajar efektif">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong>Jaga streak harian</strong> — 10 menit setiap hari lebih baik daripada 1 jam seminggu sekali.
          </li>
          <li>
            <strong>Kerjakan kuis setelah tiap pelajaran</strong> — pengulangan langsung menguatkan ingatan.
          </li>
          <li>
            <strong>Baca breakdown Translate</strong> — memahami “mengapa” engine menghasilkan
            ᬩᬮᬶ dari “bali” membantu menulis manual.
          </li>
          <li>
            <strong>Perhatikan warning</strong> — bila engine memberi peringatan (mis. tumpuk telu),
            itu justru pelajaran: baca penjelasannya.
          </li>
        </ul>
        <Callout variant="success" title="Target realistis">
          Kuasai Wresastra 18 dalam 1 minggu (Level 1), lanjut pangangge & tengenan di minggu kedua.
          Konsisten, bukan cepat.
        </Callout>
      </DocSection>
    </>
  )
}
