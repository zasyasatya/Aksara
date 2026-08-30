"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import {
  api,
  ManageStatus,
  getGuruToken,
  setGuruToken,
} from "@/lib/api"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { TabsMateri } from "./tabs-materi"
import { TabsKuis } from "./tabs-kuis"
import { TabsKamus } from "./tabs-kamus"
import { BookOpen, Gamepad2, KeyRound, Loader2, LogOut, PenSquare, Sparkles, Globe } from "lucide-react"

type TabKey = "materi" | "kuis" | "kamus"

const TABS: { key: TabKey; label: string; icon: any; desc: string }[] = [
  { key: "materi", label: "Materi", icon: BookOpen, desc: "pelajaran & urutan" },
  { key: "kuis", label: "Kuis", icon: Gamepad2, desc: "soal & kunci jawaban" },
  { key: "kamus", label: "Kamus", icon: Sparkles, desc: "kata khusus transliterasi" },
]

export default function GuruPage() {
  const [status, setStatus] = useState<ManageStatus | null>(null)
  const [tab, setTab] = useState<TabKey>("materi")
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const load = useCallback(async (token: string | null) => {
    setError(null)
    try {
      const s = await api.manage.status(token)
      setStatus(s)
      return s
    } catch (e) {
      setError((e as Error).message)
      return null
    }
  }, [])

  useEffect(() => {
    // Belum login (token tersimpan kosong / ditolak backend) → halaman /login.
    load(getGuruToken()).then((s) => {
      if (!s?.is_guru) router.replace("/login?next=/guru")
    })
  }, [load, router])

  const handleLogout = () => {
    setGuruToken(null)
    router.replace("/login?next=/guru")
  }

  const isGuru = status?.is_guru ?? false

  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />

      <div className="container mx-auto px-4 lg:px-8 py-8 max-w-5xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-sage to-ocean text-cream shadow-soft">
              <PenSquare className="h-7 w-7" />
            </div>
            <div>
              <h1 className="font-display text-2xl lg:text-3xl font-bold text-deep-brown">Panel Guru</h1>
              <p className="text-sm text-charcoal/60">
                Perbarui materi, kuis, dan kamus — langsung terlihat murid tanpa restart
              </p>
            </div>
          </div>
          {status && (
            <span
              className={`inline-flex w-fit items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-bold uppercase tracking-wide border ${
                status.mode === "dev"
                  ? "bg-sage/20 text-sage border-sage/40"
                  : "bg-saffron/15 text-saffron-dark border-saffron/40"
              }`}
            >
              <Globe className="h-3.5 w-3.5" />
              Mode {status.mode}
            </span>
          )}
        </div>

        {error && (
          <div className="mt-4 flex items-start gap-3 rounded-2xl border border-terracotta/40 bg-terracotta/10 px-4 py-3 text-sm text-terracotta">
            <KeyRound className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!status && !error && (
          <div className="flex items-center justify-center gap-3 py-16 text-charcoal/50">
            <Loader2 className="h-5 w-5 animate-spin" />
            Memuat…
          </div>
        )}

        {/* Konten guru */}
        {isGuru && status && (
          <>
            {/* Tab bar */}
            <div className="mt-6 flex flex-wrap items-center gap-2">
              {TABS.map((t) => {
                const Icon = t.icon
                return (
                  <button
                    key={t.key}
                    onClick={() => setTab(t.key)}
                    className={`flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-sm font-semibold transition-all ${
                      tab === t.key
                        ? "border-deep-brown bg-deep-brown text-cream shadow-soft"
                        : "border-sand bg-white text-charcoal/70 hover:border-deep-brown/40"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {t.label}
                    <span className={`text-[10px] font-normal ${tab === t.key ? "text-cream/60" : "text-charcoal/40"}`}>
                      {t.desc}
                    </span>
                  </button>
                )
              })}
              <div className="ml-auto flex items-center gap-3">
                <Link
                  href="/docs/penggunaan-guru"
                  className="text-xs font-semibold text-charcoal/50 hover:text-saffron-dark"
                >
                  Panduan Guru →
                </Link>
                <button
                  onClick={handleLogout}
                  className="inline-flex items-center gap-2 rounded-full border border-sand bg-white px-4 py-2 text-sm font-semibold text-charcoal/70 shadow-soft transition-colors hover:border-terracotta/50 hover:text-terracotta"
                >
                  <LogOut className="h-4 w-4" />
                  Keluar
                </button>
              </div>
            </div>

            <div className="mt-5">
              {tab === "materi" && <TabsMateri token={getGuruToken()} />}
              {tab === "kuis" && <TabsKuis token={getGuruToken()} />}
              {tab === "kamus" && <TabsKamus token={getGuruToken()} />}
            </div>
          </>
        )}
      </div>

      <BottomNav />
    </div>
  )
}
