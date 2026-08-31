"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { api, DocsPagesResponse } from "@/lib/api"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { DocsShell } from "@/components/docs/docs-shell"
import { ContentMurid } from "@/components/docs/content-murid"
import { ContentGuru } from "@/components/docs/content-guru"
import { ContentAdmin } from "@/components/docs/content-admin"
import { ContentScientific } from "@/components/docs/content-scientific"
import { ContentDatasetModel } from "@/components/docs/content-dataset-model"
import { Lock, Loader2, FileQuestion } from "lucide-react"

const CONTENTS: Record<string, () => React.JSX.Element> = {
  "penggunaan-murid": ContentMurid,
  "penggunaan-guru": ContentGuru,
  "penggunaan-admin": ContentAdmin,
  "metode-scientific": ContentScientific,
  "dataset-dan-model": ContentDatasetModel,
}

export function DocsArticleClient() {
  const params = useParams<{ slug: string }>()
  const slug = params?.slug ?? ""
  const [data, setData] = useState<DocsPagesResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getDocsPages().then(setData).catch((e) => setError((e as Error).message))
  }, [])

  const shell = (children: React.ReactNode) => (
    <>
      <Header />
      {children}
      <BottomNav />
    </>
  )

  if (error) {
    return shell(
      <div className="container mx-auto px-4 py-20 max-w-3xl">
        <div className="rounded-2xl border border-terracotta/40 bg-terracotta/10 p-8 text-center">
          <div className="text-3xl"></div>
          <div className="mt-3 font-semibold text-deep-brown">Gagal memuat dokumentasi</div>
          <p className="mt-1 text-sm text-charcoal/60">{error}</p>
          <Link href="/docs" className="mt-4 inline-block text-sm font-semibold text-saffron-dark hover:underline">
            ← Kembali ke Dokumentasi
          </Link>
        </div>
      </div>
    )
  }

  if (!data) {
    return shell(
      <div className="flex items-center justify-center gap-3 py-24 text-charcoal/50">
        <Loader2 className="h-5 w-5 animate-spin" />
        Memuat halaman…
      </div>
    )
  }

  // Ambil daftar sesuai hak akses (dev: semua; prod admin: semua; prod user: publik)
  const page = data.pages.find((p) => p.slug === slug)

  if (!page) {
    return shell(
      <div className="container mx-auto px-4 py-20 max-w-3xl">
        <div className="rounded-2xl border border-sand bg-white p-10 text-center shadow-soft">
          <FileQuestion className="mx-auto h-10 w-10 text-charcoal/30" />
          <h1 className="mt-4 font-display text-2xl font-bold text-deep-brown">
            Halaman tidak ditemukan
          </h1>
          <p className="mt-2 text-sm text-charcoal/60">
            Tidak ada halaman dokumentasi dengan slug “{slug}” yang dapat Anda akses.
          </p>
          <Link
            href="/docs"
            className="mt-5 inline-flex items-center rounded-full bg-saffron px-5 py-2.5 text-sm font-semibold text-cream shadow-soft hover:bg-saffron-dark transition-colors"
          >
            ← Kembali ke Dokumentasi
          </Link>
        </div>
      </div>
    )
  }

  const isPrivate = !page.is_public
  const canView =
    data.mode === "dev" || data.is_admin || !isPrivate

  if (!canView) {
    return shell(
      <div className="container mx-auto px-4 py-20 max-w-3xl">
        <div className="rounded-2xl border border-sand bg-white p-10 text-center shadow-soft">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-sand">
            <Lock className="h-7 w-7 text-deep-brown/60" />
          </div>
          <h1 className="mt-4 font-display text-2xl font-bold text-deep-brown">
            Halaman belum dipublikasikan
          </h1>
          <p className="mt-2 text-sm text-charcoal/60">
            “{page.title}” masih berstatus privat dan hanya dapat dilihat oleh admin atau pada
            mode dev.
          </p>
          <Link
            href="/docs"
            className="mt-5 inline-flex items-center rounded-full bg-saffron px-5 py-2.5 text-sm font-semibold text-cream shadow-soft hover:bg-saffron-dark transition-colors"
          >
            ← Kembali ke Dokumentasi
          </Link>
        </div>
      </div>
    )
  }

  const Content = CONTENTS[page.slug]
  const privateNotice =
    isPrivate && data.mode === "prod" && data.is_admin
      ? "Halaman ini sedang PRIVAT: hanya Anda (admin) dan mode dev yang bisa melihatnya. Aktifkan sakelar Public di panel Admin agar pengunjung biasa dapat membacanya."
      : isPrivate
        ? "Anda melihat halaman ini karena sedang dalam mode DEV — semua halaman tampil, termasuk yang belum dipublikasikan."
        : undefined

  return shell(
    <DocsShell meta={page} privateNotice={privateNotice} pages={data.pages}>
      {Content ? (
        <Content />
      ) : (
        <div className="py-10 text-center text-charcoal/50">
          Konten untuk “{page.slug}” belum dibuat.
        </div>
      )}
    </DocsShell>
  )
}
