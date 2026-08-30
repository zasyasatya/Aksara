"use client"

import Link from "next/link"
import { Screenshot } from "./screenshot"
import { Callout, Code, DocSection, DocTable, Steps } from "./primitives"

export function ContentGuru() {
  return (
    <>
      <p className="text-lg leading-relaxed">
        Panduan ini untuk <strong>guru Bahasa Bali</strong> (atau fasilitator) yang ingin
        memanfaatkan platform Aksara di kelas. Platform tidak menuntut daftar akun guru di MVP —
        semua fitur bisa langsung dipakai sebagai alat bantu mengajar, menyiapkan materi,
        dan menilai.
      </p>

      <DocSection id="peta-materi" number="1." title="Petakan silabus dari halaman Belajar">
        <p>
          Buka <Link href="/learn" className="text-saffron-dark font-semibold hover:underline">menu Belajar</Link>.
          Keseluruhan materi tersusun <strong>11 pelajaran dalam 6 level</strong> — gunakan ini
          sebagai peta silabus semester:
        </p>
        <DocTable
          head={["Level", "Tema", "Pelajaran", "Fokus"]}
          rows={[
            ["1 — Pemula", "Wresastra 18", "4", "18 aksara dasar (Ha Na Ca Ra Ka …)"],
            ["2 — Pangangge Suara", "Vokal", "2", "ulu, suku, taleng, pepet"],
            ["3 — Tengenan", "Akhiran", "1", "bisah (h), surang (r), cecek (ng)"],
            ["4 — Gantungan", "Cluster konsonan", "2", "gantungan, cakra, nania"],
            ["5 — Swalalita", "Serapan Sanskerta/Kawi", "1", "aksara serapan Sanskerta/Kawi"],
            ["6 — Kalimat", "Rangkai kalimat", "1", "menulis kalimat utuh"],
          ]}
        />
        <p>
          Estimasi waktu tiap pelajaran tampil di kartu pelajaran — cukup untuk menyusun
          jadwal pertemuan per minggu.
        </p>
        <Screenshot
          src="/screenshots/learn.png"
          alt="Halaman daftar pelajaran yang bisa dipakai guru memetakan silabus"
          caption="Gunakan halaman Belajar sebagai peta silabus: 11 pelajaran, 6 level, dengan estimasi waktu."
          url="aksara.local/learn"
        />
      </DocSection>

      <DocSection id="materi" number="2." title="Siapkan materi dengan Translate">
        <p>
          Menu <Link href="/translate" className="text-saffron-dark font-semibold hover:underline">Translate</Link> adalah
          alat cepat menyiapkan <strong>lembar kerja</strong>:
        </p>
        <Steps
          items={[
            {
              title: "Tulis frasa Latin → Aksara",
              body: (
                <>
                  Contoh: “aksara bali” menjadi{" "}
                  <span className="font-bali text-deep-brown">ᬅᬓ᭄ᬱᬭ ᬩᬮᬶ</span> — langsung bisa
                  dicetak ke LKS.
                </>
              ),
            },
            {
              title: "Bolak-balik arah",
              body: "Mode Bali → Latin untuk membuat soal “bacalah aksara berikut ke Latin”.",
            },
            {
              title: "Jelaskan aturan lewat breakdown",
              body: (
                <>
                  Panel breakdown menjabarkan suku kata dan aturan (gantungan, pangangge) —
                  jadikan ini bahan penjelasan di papan tulis.
                </>
              ),
            },
            {
              title: "Perhatikan warning sebagai momen belajar",
              body: "Bila muncul peringatan (mis. larangan tumpuk telu), jelaskan alasannya ke kelas.",
            },
          ]}
        />
        <Screenshot
          src="/screenshots/translate.png"
          alt="Halaman translate untuk menyiapkan materi pembelajaran"
          caption="Translate dua arah dengan breakdown aturan — cocok untuk membuat soal & menjelaskan di kelas."
          url="aksara.local/translate"
        />
      </DocSection>

      <DocSection id="menilai" number="3." title="Nilai kemampuan menulis dengan Kuis">
        <p>
          Menu <Link href="/quiz" className="text-saffron-dark font-semibold hover:underline">Kuis</Link> menyediakan
          soal interaktif yang dinilai sistem secara otomatis. Untuk asesmen tulisan tangan
          murid, platform menyediakan <strong>validasi pasangan</strong> (endpoint{" "}
          <Code>POST /api/quiz/validate-pair</Code>):
        </p>
        <Steps
          items={[
            { title: "Tampilkan soal", body: "Soal: tuliskan kata “bali” dalam Aksara Bali." },
            { title: "Murid menulis", body: "Murid menuliskan aksara di aplikasi (Playground) atau papan tulis." },
            { title: "Sistem memvalidasi", body: (
              <>
                Hasil membandingkan tulisan murid dengan jawaban kunci — mode{" "}
                <Code>exact</Code> (harus identik) atau <Code>tolerant</Code> (toleransi
                variasi penulisan).
              </>
            ) },
            { title: "Feedback edukatif", body: (
              <>
                Bila salah, sistem menjelaskan <em>mengapa</em> — misalnya “seharusnya pakai
                gantungan, bukan adeg-adeg” — bukan sekadar nilai.
              </>
            ) },
          ]}
        />
        <Screenshot
          src="/screenshots/quiz.png"
          alt="Halaman kuis untuk asesmen murid"
          caption="Kuis dengan penilaian otomatis dan penjelasan kesalahan — dasar asesmen formatif."
          url="aksara.local/quiz"
        />
      </DocSection>

      <DocSection id="demonstrasi" number="4." title="Demonstrasikan di kelas dengan Playground">
        <p>
          <Link href="/playground" className="text-saffron-dark font-semibold hover:underline">Playground</Link> menampilkan
          keyboard virtual — ideal untuk <strong>demonstrasi di proyektor</strong>: ketik
          aksara satu per satu sambil menjelaskan bentuknya, murid mengikuti di perangkat
          masing-masing.
        </p>
        <Screenshot
          src="/screenshots/playground.png"
          alt="Playground keyboard virtual untuk demonstrasi kelas"
          caption="Playground: keyboard virtual untuk demo interaktif di kelas."
          url="aksara.local/playground"
        />
      </DocSection>

      <DocSection id="alur" number="5." title="Contoh alur pertemuan 45 menit">
        <Steps
          items={[
            { title: "10 menit — Apersepsi", body: (
              <>
                Buka detail pelajaran (mis. Level 1) di proyektor; jelaskan bentuk aksara hari ini
                dengan <em>cara menulis</em> di layar.
              </>
            ) },
            { title: "20 menit — Praktik mandiri", body: (
              <>
                Murid membuka pelajaran yang sama di perangkat, mencoba Playground, lalu
                menyelesaikan pelajaran.
              </>
            ) },
            { title: "10 menit — Kuis formatif", body: "Kerjakan 3–5 soal kuis; bahas bersama yang banyak keliru." },
            { title: "5 menit — Refleksi", body: "Ingatkan menjaga streak harian & tugas: 1 kata Aksara di buku tulis." },
          ]}
        />
        <Callout title="Catatan jujur (MVP)">
          Fitur penugasan massal, laporan per-murid, dan portal guru belum tersedia di versi
          ini. MVP berfokus pada materi, kuis, dan validasi. Fitur guru lanjutan masuk roadmap.
        </Callout>
      </DocSection>
    </>
  )
}
