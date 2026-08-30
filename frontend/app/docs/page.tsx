"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { api, DocsPageMeta, DocsPagesResponse } from "@/lib/api"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { Badge } from "@/components/ui/badge"
import { docRoleMeta, IconByName } from "@/components/docs/meta"
import { BookOpenCheck, Lock, Globe, Loader2, ChevronRight } from "lucide-react"

export default function DocsHubPage() {
  const [data, setData] = useState<DocsPagesResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getDocsPages().then(setData).catch((e) => setError((e as Error).message))
  }, [])

  const visiblePages = useMemo(() => {
    if (!data) return []
    // Dev: semua halaman. Prod: publik untuk semua; admin tetap lihat semua (dengan badge).
    if (data.mode === "dev" || data.is_admin) return data.pages
    return data.pages.filter((p) => p.is_public)
  }, [data])

  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />

      {/* Hero */}
      <section className="border-b border-sand bg-gradient-to-br from-sand/60 via-cream to-cream">
        <div className="container mx-auto px-4 lg:px-8 py-10 lg:py-14">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-saffron to-terracotta text-cream shadow-medium">
              <BookOpenCheck className="h-8 w-8" />
            </div>
            <div>
              <h1 className="font-display text-3xl lg:text-4xl font-bold text-deep-brown">
                Dokumentasi
              </h1>
              <p className="text-charcoal/60 mt-1">
                Tata cara penggunaan & metodologi ilmiah platform Aksara
              </p>
            </div>
          </div>

          {data && (
            <div className="mt-6 flex flex-wrap items-center gap-3">
              {data.mode === "dev" ? (
                <Badge variant="saffron" className="gap-1.5">
                  <Globe className="h-3.5 w-3.5" />
                  Mode DEV — semua halaman terlihat
                </Badge>
              ) : (
                <Badge variant="outline" className="gap-1.5">
                  <Globe className="h-3.5 w-3.5" />
                  Mode PROD — hanya halaman publik yang tampil
                </Badge>
              )}
              {data.is_admin && (
                <Badge variant="outline" className="gap-1.5">
                  <Lock className="h-3.5 w-3.5" />
                  Anda melihat sebagai admin
                </Badge>
              )}
            </div>
          )}
        </div>
      </section>

      <div className="container mx-auto px-4 lg:px-8 py-8 max-w-5xl">
        {error && (
          <div className="rounded-2xl border border-terracotta/40 bg-terracotta/10 p-6 text-center text-sm text-terracotta">
            Gagal memuat dokumentasi: {error}
          </div>
        )}

        {!data && !error && (
          <div className="flex items-center justify-center gap-3 py-20 text-charcoal/50">
            <Loader2 className="h-5 w-5 animate-spin" />
            Memuat dokumentasi…
          </div>
        )}

        {data && visiblePages.length === 0 && (
          <div className="rounded-2xl border border-sand bg-white p-10 text-center shadow-soft">
            <div className="text-4xl">📭</div>
            <div className="mt-3 font-semibold text-deep-brown">Belum ada halaman dokumentasi publik</div>
            <p className="mt-1 text-sm text-charcoal/60">
              Semua halaman masih privat. Admin dapat mempublikasikannya lewat panel Admin.
            </p>
          </div>
        )}

        {data && visiblePages.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2">
            {visiblePages.map((page) => (
              <DocsCard key={page.slug} page={page} mode={data.mode} isAdmin={data.is_admin} />
            ))}
          </div>
        )}

        <div className="mt-8 rounded-2xl border border-sand bg-white p-5 text-sm text-charcoal/60 shadow-soft">
          <div className="font-semibold text-deep-brown">Butuh akses admin?</div>
          Buka <Link href="/admin" className="font-semibold text-saffron-dark hover:underline">/admin</Link>{" "}
          untuk mengatur halaman mana yang go public (efektif di mode prod).
        </div>
      </div>

      <BottomNav />
    </div>
  )
}

function DocsCard({
  page,
  mode,
  isAdmin,
}: {
  page: DocsPageMeta
  mode: "dev" | "prod"
  isAdmin: boolean
}) {
  const role = docRoleMeta[page.role] ?? docRoleMeta.murid
  const Icon = IconByName[page.icon] ?? IconByName.BookOpen
  const showPrivateBadge = !page.is_public && (mode === "dev" || isAdmin)

  return (
    <Link
      href={`/docs/${page.slug}`}
      className="group flex flex-col rounded-3xl border border-sand bg-white p-5 shadow-soft transition-all hover:-translate-y-0.5 hover:border-saffron/50 hover:shadow-medium"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sand/70 text-deep-brown group-hover:bg-saffron group-hover:text-cream transition-colors">
          <Icon className="h-6 w-6" />
        </div>
        {showPrivateBadge ? (
          <Badge variant="outline" className="gap-1 text-[11px]">
            <Lock className="h-3 w-3" />
            Privat
          </Badge>
        ) : (
          <Badge variant="outline" className="gap-1 text-[11px]">
            <Globe className="h-3 w-3" />
            Publik
          </Badge>
        )}
      </div>
      <div className="mt-4 font-display text-lg font-bold text-deep-brown leading-snug group-hover:text-saffron-dark transition-colors">
        {page.title}
      </div>
      <p className="mt-1 flex-1 text-sm text-charcoal/60">{page.subtitle}</p>
      <div className="mt-4 flex items-center justify-between">
        <span className="text-xs font-semibold text-saffron-dark">{role.label}</span>
        <span className="inline-flex items-center gap-1 text-xs text-charcoal/50 group-hover:text-saffron-dark">
          Buka <ChevronRight className="h-3.5 w-3.5" />
        </span>
      </div>
    </Link>
  )
}
