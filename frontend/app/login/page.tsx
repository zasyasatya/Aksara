"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import {
  api,
  getAdminToken,
  getGuruToken,
  setAdminToken,
  setGuruToken,
} from "@/lib/api"
import { Header } from "@/components/layout/header"
import { ArrowLeft, GraduationCap, Loader2, ShieldCheck } from "lucide-react"

type Role = "guru" | "admin"

const ROLES: { key: Role; label: string; desc: string; icon: any }[] = [
  { key: "guru", label: "Guru", desc: "kelola materi, kuis & kamus", icon: GraduationCap },
  { key: "admin", label: "Admin", desc: "kelola dokumen & mode prod", icon: ShieldCheck },
]

export default function LoginPage() {
  const router = useRouter()
  const [role, setRole] = useState<Role>("guru")
  const [token, setToken] = useState("")
  const [mode, setMode] = useState<"dev" | "prod">("dev")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [next, setNext] = useState<string>("/guru")

  useEffect(() => {
    api.auth.info().then((r) => setMode(r.mode)).catch(() => setMode("dev"))
    // ?next=… (dibaca manual agar aman untuk export statis)
    try {
      const n = new URLSearchParams(window.location.search).get("next")
      if (n && n.startsWith("/")) setNext(n)
    } catch {
      /* non-browser */
    }
  }, [])

  const targetPath = (r: Role) => (r === "admin" ? "/admin" : "/guru")
  const storedToken = role === "admin" ? getAdminToken() : getGuruToken()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const res = await api.auth.login(role, token.trim())
      if (res.ok) {
        if (role === "admin") setAdminToken(token.trim() || null)
        else setGuruToken(token.trim() || null)
        router.push(next.startsWith("/guru") || next.startsWith("/admin") ? next : targetPath(role))
      } else {
        setError(res.message)
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />

      <div className="container mx-auto px-4 lg:px-8 py-10 max-w-md">
        <Link
          href={role === "admin" ? "/admin" : "/guru"}
          className="inline-flex items-center gap-1.5 text-sm text-charcoal/60 hover:text-deep-brown"
        >
          <ArrowLeft className="h-4 w-4" />
          Kembali
        </Link>

        <div className="mt-4 rounded-3xl border border-sand bg-white p-6 lg:p-8 shadow-soft">
          <h1 className="font-display text-2xl font-bold text-deep-brown">Masuk</h1>
          <p className="mt-1 text-sm text-charcoal/60">
            Pilih peran lalu masukkan token. Halaman murid tetap bisa diakses tanpa login.
          </p>

          {/* Pilihan role */}
          <div className="mt-5 grid grid-cols-2 gap-2">
            {ROLES.map((r) => {
              const Icon = r.icon
              const active = role === r.key
              return (
                <button
                  key={r.key}
                  type="button"
                  onClick={() => setRole(r.key)}
                  className={`rounded-2xl border p-3 text-left transition-all ${
                    active
                      ? "border-deep-brown bg-deep-brown text-cream shadow-soft"
                      : "border-sand bg-cream text-charcoal/70 hover:border-deep-brown/40"
                  }`}
                >
                  <Icon className={`h-5 w-5 ${active ? "text-cream" : "text-deep-brown"}`} />
                  <div className="mt-1.5 text-sm font-bold">{r.label}</div>
                  <div className={`text-[11px] ${active ? "text-cream/70" : "text-charcoal/50"}`}>
                    {r.desc}
                  </div>
                </button>
              )
            })}
          </div>

          {/* Token */}
          <form onSubmit={handleSubmit} className="mt-5 flex flex-col gap-3">
            <label className="text-xs font-semibold uppercase tracking-wide text-charcoal/50">
              {role === "admin" ? (
                <>Token Admin <code className="rounded bg-sand px-1">AKSARA_ADMIN_TOKEN</code></>
              ) : (
                <>Token Guru <code className="rounded bg-sand px-1">AKSARA_GURU_TOKEN</code></>
              )}
            </label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder={mode === "dev" ? "kosongkan saja (mode dev)" : "Masukkan token…"}
              className="rounded-xl border border-sand bg-cream px-4 py-2.5 text-sm outline-none focus:border-saffron"
            />
            {storedToken && (
              <p className="text-xs text-charcoal/50">
                Token tersimpan di perangkat ini — klik <b>Simpan & Lanjut</b> untuk masuk kembali.
              </p>
            )}
            {error && (
              <div className="rounded-xl border border-terracotta/40 bg-terracotta/10 px-4 py-2.5 text-sm text-terracotta">
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={busy || (mode === "prod" && !token.trim())}
              className="flex items-center justify-center gap-2 rounded-xl bg-sage px-6 py-2.5 text-sm font-semibold text-white shadow-soft transition-colors hover:bg-ocean disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy && <Loader2 className="h-4 w-4 animate-spin" />}
              {busy ? "Memeriksa…" : "Simpan & Lanjut"}
            </button>
          </form>

          {mode === "dev" && (
            <p className="mt-4 rounded-xl bg-sage/10 px-4 py-2.5 text-xs text-sage">
              Mode <b>dev</b> aktif — akses otomatis tanpa token. Pada mode <b>prod</b>,
              token dibaca dari env backend.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
