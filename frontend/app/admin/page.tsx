"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import {
  api,
  DocsPagesResponse,
  getAdminToken,
  setAdminToken,
} from "@/lib/api"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { docRoleMeta, IconByName } from "@/components/docs/meta"
import {
  ShieldCheck,
  Globe,
  Loader2,
  KeyRound,
  LogOut,
  BookOpen,
  ExternalLink,
  CheckCircle2,
  RefreshCw,
} from "lucide-react"

export default function AdminPage() {
  const [data, setData] = useState<DocsPagesResponse | null>(null)
  const [version, setVersion] = useState<string>("")
  const [error, setError] = useState<string | null>(null)
  const [tokenInput, setTokenInput] = useState("")
  const [savingSlug, setSavingSlug] = useState<string | null>(null)
  const [flash, setFlash] = useState<string | null>(null)

  const load = useCallback(async (token: string | null) => {
    setError(null)
    try {
      const d = await api.getDocsPages(token)
      setData(d)
      return d
    } catch (e) {
      setError((e as Error).message)
      return null
    }
  }, [])

  useEffect(() => {
    load(getAdminToken())
    api.health().then((h) => setVersion(h.version ?? "")).catch(() => {})
  }, [load])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = tokenInput.trim()
    if (!token) return
    setAdminToken(token)
    const d = await load(token)
    if (!d?.is_admin) {
      setAdminToken(null)
      setError("Token admin tidak valid. Periksa AKSARA_ADMIN_TOKEN pada backend.")
      setData(null)
    } else {
      setTokenInput("")
    }
  }

  const handleLogout = () => {
    setAdminToken(null)
    load(null)
  }

  const toggleVisibility = async (slug: string, isPublic: boolean) => {
    setSavingSlug(slug)
    try {
      const res = await api.setDocVisibility(slug, isPublic, getAdminToken())
      setFlash(res.message)
      setTimeout(() => setFlash(null), 2500)
      await load(getAdminToken())
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSavingSlug(null)
    }
  }

  const isDev = data?.mode === "dev"
  const isAdmin = data?.is_admin ?? false

  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />

      <div className="container mx-auto px-4 lg:px-8 py-8 max-w-4xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-deep-brown text-cream shadow-soft">
              <ShieldCheck className="h-7 w-7" />
            </div>
            <div>
              <h1 className="font-display text-2xl lg:text-3xl font-bold text-deep-brown">
                Panel Admin
              </h1>
              <p className="text-sm text-charcoal/60">
                Pengaturan platform & publikasi dokumentasi
              </p>
            </div>
          </div>
          {data && (
            <div className="flex items-center gap-2">
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-bold uppercase tracking-wide ${
                  isDev ? "bg-sage/20 text-sage border border-sage/40" : "bg-saffron/15 text-saffron-dark border border-saffron/40"
                }`}
              >
                <Globe className="h-3.5 w-3.5" />
                Mode {data.mode}
              </span>
              {version && (
                <span className="text-xs text-charcoal/50">v{version}</span>
              )}
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 flex items-start gap-3 rounded-2xl border border-terracotta/40 bg-terracotta/10 px-4 py-3 text-sm text-terracotta">
            <KeyRound className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              {error}
              {isDev && (
                <span className="ml-2 text-charcoal/60">
                  (Catatan: di mode dev backend menganggap semua pengakses sebagai admin.)
                </span>
              )}
            </div>
          </div>
        )}

        {flash && (
          <div className="mt-4 flex items-center gap-2 rounded-2xl border border-sage/50 bg-sage/10 px-4 py-3 text-sm text-deep-brown">
            <CheckCircle2 className="h-4 w-4 text-sage" />
            {flash}
          </div>
        )}

        {/* Login (hanya dibutuhkan di mode prod) */}
        {!isAdmin && (
          <div className="mt-6 rounded-3xl border border-sand bg-white p-6 lg:p-8 shadow-soft">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sand">
                <KeyRound className="h-5 w-5 text-deep-brown" />
              </div>
              <div>
                <h2 className="font-display text-lg font-bold text-deep-brown">
                  Masuk sebagai admin
                </h2>
                <p className="text-sm text-charcoal/60">
                  Mode prod aktif — masukkan token admin (env <code className="rounded bg-sand px-1">AKSARA_ADMIN_TOKEN</code>) untuk melanjutkan.
                </p>
              </div>
            </div>
            <form onSubmit={handleLogin} className="mt-5 flex flex-col sm:flex-row gap-3">
              <input
                type="password"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="Token admin…"
                className="flex-1 rounded-xl border border-sand bg-cream px-4 py-2.5 text-sm outline-none focus:border-saffron"
              />
              <button
                type="submit"
                className="rounded-xl bg-saffron px-6 py-2.5 text-sm font-semibold text-cream shadow-soft transition-colors hover:bg-saffron-dark"
              >
                Masuk
              </button>
            </form>
          </div>
        )}

        {/* Konten admin */}
        {isAdmin && data && (
          <>
            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <StatCard label="Mode berjalan" value={data.mode.toUpperCase()} hint={isDev ? "semua halaman terlihat" : "hanya halaman publik terlihat"} />
              <StatCard label="Total halaman docs" value={String(data.pages.length)} hint="terdaftar di docs.json" />
              <StatCard
                label="Halaman publik"
                value={String(data.pages.filter((p) => p.is_public).length)}
                hint={`dari ${data.pages.length} halaman`}
              />
            </div>

            {/* Publikasi dokumentasi */}
            <div className="mt-6 rounded-3xl border border-sand bg-white shadow-soft overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-sand px-6 py-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-saffron/15 text-saffron-dark">
                    <BookOpen className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="font-display text-lg font-bold text-deep-brown">
                      Publikasi Dokumentasi
                    </h2>
                    <p className="text-xs text-charcoal/55">
                      Atur halaman mana yang go public — terlihat di menu Dokumentasi oleh semua pengunjung.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => load(getAdminToken())}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-charcoal/50 hover:text-saffron-dark"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Muat ulang
                </button>
              </div>

              {isDev && (
                <div className="mx-6 mt-4 rounded-xl border border-sage/40 bg-sage/10 px-4 py-2.5 text-xs text-deep-brown/80">
                  Mode <strong>dev</strong>: semua halaman selalu tampil di publik. Sakelar di
                  bawah menyiapkan status yang berlaku saat backend berjalan dalam mode <strong>prod</strong>.
                </div>
              )}

              <ul className="divide-y divide-sand">
                {data.pages.map((p) => {
                  const Icon = IconByName[p.icon] ?? IconByName.BookOpen
                  const role = docRoleMeta[p.role] ?? docRoleMeta.murid
                  const saving = savingSlug === p.slug
                  return (
                    <li key={p.slug} className="flex items-center gap-4 px-6 py-4">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sand/70 text-deep-brown">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-semibold text-deep-brown text-sm">{p.title}</span>
                          <span className="rounded-full bg-sand/80 px-2 py-0.5 text-[10px] font-semibold text-deep-brown/70">
                            {role.label}
                          </span>
                        </div>
                        <div className="mt-0.5 truncate text-xs text-charcoal/50">
                          /docs/{p.slug} · diperbarui {p.updated_at || "-"}
                        </div>
                      </div>
                      <Link
                        href={`/docs/${p.slug}`}
                        target="_blank"
                        className="hidden sm:inline-flex items-center gap-1 text-xs font-semibold text-charcoal/50 hover:text-saffron-dark"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                        Lihat
                      </Link>
                      <Toggle
                        checked={p.is_public}
                        disabled={saving}
                        label={p.is_public ? "Public" : "Privat"}
                        onChange={() => toggleVisibility(p.slug, !p.is_public)}
                      />
                    </li>
                  )
                })}
              </ul>

              <div className="border-t border-sand bg-cream/60 px-6 py-3 text-xs text-charcoal/50">
                Perubahan tersimpan ke <code className="rounded bg-white px-1">backend/app/data/docs.json</code>{" "}
                via <code className="rounded bg-white px-1">PATCH /api/docs/pages/:slug/visibility</code>.
              </div>
            </div>

            {/* Aksi */}
            <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
              <div className="text-xs text-charcoal/50">
                Token tersimpan di peramban ini (localStorage).
              </div>
              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-2 rounded-full border border-sand bg-white px-4 py-2 text-sm font-semibold text-charcoal/70 shadow-soft transition-colors hover:border-terracotta/50 hover:text-terracotta"
              >
                <LogOut className="h-4 w-4" />
                Keluar dari mode admin
              </button>
            </div>
          </>
        )}

        {!data && !error && (
          <div className="flex items-center justify-center gap-3 py-16 text-charcoal/50">
            <Loader2 className="h-5 w-5 animate-spin" />
            Memuat…
          </div>
        )}
      </div>

      <BottomNav />
    </div>
  )
}

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-2xl border border-sand bg-white p-4 shadow-soft">
      <div className="text-xs font-medium text-charcoal/50">{label}</div>
      <div className="mt-1 font-display text-2xl font-bold text-deep-brown">{value}</div>
      {hint && <div className="mt-0.5 text-[11px] text-charcoal/45">{hint}</div>}
    </div>
  )
}

function Toggle({
  checked,
  onChange,
  disabled,
  label,
}: {
  checked: boolean
  onChange: () => void
  disabled?: boolean
  label: string
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={onChange}
      className="inline-flex shrink-0 items-center gap-2 disabled:opacity-60"
    >
      <span
        className={`w-12 text-right text-[10px] font-bold tracking-wide ${
          checked ? "text-sage" : "text-charcoal/45"
        }`}
      >
        {disabled ? "…" : label.toUpperCase()}
      </span>
      <span
        className={`relative inline-flex h-6 w-11 items-center rounded-full border transition-colors ${
          checked ? "bg-sage/30 border-sage/60" : "bg-sand/80 border-sand"
        }`}
      >
        <span
          className={`absolute h-4 w-4 rounded-full bg-white shadow-soft transition-all ${
            checked ? "left-[24px]" : "left-1"
          }`}
        />
      </span>
    </button>
  )
}
