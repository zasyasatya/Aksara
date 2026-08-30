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

      <DocSection id="api" number="4." title="API & variabel lingkungan (ringkasan)">
        <CodeBlock>{`# Variabel lingkungan backend
AKSARA_MODE=prod                          # dev | prod
AKSARA_ADMIN_USERNAME=admin               # username admin
AKSARA_ADMIN_PASSWORD=ganti-password      # password admin (wajib diganti di prod)

# Contoh API
POST /auth/login                           # body: {"role":"admin","username":"...","password":"..."}
GET  /api/docs/pages                       # daftar halaman + mode + is_admin
PATCH /api/docs/pages/:slug/visibility     # body: {"is_public": true|false}
       Header: Authorization: Bearer <session>   # sesi dari /auth/login`}</CodeBlock>
        <p>
          Endpoint <Code>GET /api/docs/pages</Code> membalas field <Code>mode</Code> (
          <Code>dev|prod</Code>) dan <Code>is_admin</Code> — frontend memakai keduanya untuk
          memutuskan halaman mana yang ditampilkan.
        </p>
      </DocSection>
    </>
  )
}
