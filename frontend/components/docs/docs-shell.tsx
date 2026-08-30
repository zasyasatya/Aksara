"use client"

import Link from "next/link"
import { ArrowLeft, ArrowRight, Lock, CalendarDays } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { DocsPageMeta } from "@/lib/api"
import { docRoleMeta, IconByName } from "./meta"

interface DocsShellProps {
  meta: DocsPageMeta
  /** Halaman privat yang dibuka (mode dev / admin) → tampilkan banner peringatan */
  privateNotice?: string
  /** Halaman dokumentasi lain (untuk navigasi sebelumnya/berikutnya) */
  pages?: DocsPageMeta[]
  children: React.ReactNode
}

export function DocsShell({ meta, privateNotice, pages = [], children }: DocsShellProps) {
  const role = docRoleMeta[meta.role] ?? docRoleMeta.murid
  const index = pages.findIndex((p) => p.slug === meta.slug)
  const prev = index > 0 ? pages[index - 1] : null
  const next = index >= 0 && index < pages.length - 1 ? pages[index + 1] : null
  const Icon = IconByName[meta.icon] ?? IconByName.BookOpen

  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-16">
      <div className="container mx-auto px-4 lg:px-8 py-6 lg:py-10 max-w-4xl">
        {/* Breadcrumb */}
        <Link
          href="/docs"
          className="inline-flex items-center gap-2 text-sm font-medium text-charcoal/60 hover:text-saffron-dark transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Kembali ke Dokumentasi
        </Link>

        {/* Header */}
        <div className="mt-6 rounded-3xl border border-sand bg-white p-6 lg:p-8 shadow-soft">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-saffron to-terracotta text-cream shadow-soft">
              <Icon className="h-7 w-7" />
            </div>
            <div className="min-w-0">
              <h1 className="font-display text-2xl lg:text-3xl font-bold text-deep-brown leading-tight">
                {meta.title}
              </h1>
              <p className="mt-1 text-sm lg:text-base text-charcoal/60">{meta.subtitle}</p>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Badge variant="saffron">{role.label}</Badge>
                {meta.updated_at && (
                  <span className="inline-flex items-center gap-1.5 text-xs text-charcoal/50">
                    <CalendarDays className="h-3.5 w-3.5" />
                    Diperbarui {meta.updated_at}
                  </span>
                )}
                {!meta.is_public && (
                  <Badge variant="outline" className="gap-1.5">
                    <Lock className="h-3 w-3" />
                    Privat — belum go public
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>

        {privateNotice && (
          <div className="mt-4 flex items-start gap-3 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <Lock className="mt-0.5 h-4 w-4 shrink-0" />
            <p>{privateNotice}</p>
          </div>
        )}

        {/* Konten */}
        <div className="mt-6 rounded-3xl border border-sand bg-white p-6 lg:p-10 shadow-soft">
          {children}
        </div>

        {/* Navigasi prev/next */}
        {(prev || next) && (
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {prev ? (
              <Link
                href={`/docs/${prev.slug}`}
                className="group rounded-2xl border border-sand bg-white p-4 shadow-soft transition-all hover:border-saffron hover:shadow-medium"
              >
                <div className="flex items-center gap-1.5 text-xs text-charcoal/50">
                  <ArrowLeft className="h-3.5 w-3.5 group-hover:text-saffron-dark" />
                  Sebelumnya
                </div>
                <div className="mt-1 text-sm font-semibold text-deep-brown group-hover:text-saffron-dark">
                  {prev.title}
                </div>
              </Link>
            ) : (
              <div />
            )}
            {next && (
              <Link
                href={`/docs/${next.slug}`}
                className="group rounded-2xl border border-sand bg-white p-4 text-right shadow-soft transition-all hover:border-saffron hover:shadow-medium"
              >
                <div className="flex items-center justify-end gap-1.5 text-xs text-charcoal/50">
                  Berikutnya
                  <ArrowRight className="h-3.5 w-3.5 group-hover:text-saffron-dark" />
                </div>
                <div className="mt-1 text-sm font-semibold text-deep-brown group-hover:text-saffron-dark">
                  {next.title}
                </div>
              </Link>
            )}
          </div>
        )}

        <div className="mt-8 text-center text-xs text-charcoal/40">
          AKSA — Melestarikan Warisan, Menulis Masa Depan · ᬅᬓᬱ
        </div>
      </div>
    </div>
  )
}
