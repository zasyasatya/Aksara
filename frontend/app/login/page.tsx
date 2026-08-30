"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { api, AuthRole, getSession, setSession } from "@/lib/api"
import { Header } from "@/components/layout/header"
import { ArrowLeft, GraduationCap, Loader2, Lock, ShieldCheck, User } from "lucide-react"

const ROLES: { key: AuthRole; label: string; desc: string; icon: any }[] = [
  { key: "guru", label: "Guru", desc: "kelola materi, kuis & kamus", icon: GraduationCap },
  { key: "admin", label: "Admin", desc: "kelola dokumen & mode prod", icon: ShieldCheck },
]

export default function LoginPage() {
  const router = useRouter()
  const [role, setRole] = useState<AuthRole>("guru")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
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

  const targetPath = (r: AuthRole) => (r === "admin" ? "/admin" : "/guru")
  const stored = getSession()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const res = await api.auth.login(role, username.trim(), password)
      if (res.ok && res.session_token) {
        setSession(res.session_token, res.role ?? role)
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
            Pilih peran lalu masukkan username & password. Halaman murid tetap bisa diakses tanpa login.
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

          {/* Username & password */}
          <form onSubmit={handleSubmit} className="mt-5 flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="username" className="text-xs font-semibold uppercase tracking-wide text-charcoal/50">
                Username
              </label>
              <div className="relative">
                <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-charcoal/40" />
                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder={mode === "dev" ? "username (boleh kosong)" : "Masukkan username…"}
                  className="w-full rounded-xl border border-sand bg-cream py-2.5 pl-9 pr-4 text-sm outline-none focus:border-saffron"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="password" className="text-xs font-semibold uppercase tracking-wide text-charcoal/50">
                Password
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-charcoal/40" />
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === "dev" ? "password (boleh kosong)" : "Masukkan password…"}
                  className="w-full rounded-xl border border-sand bg-cream py-2.5 pl-9 pr-4 text-sm outline-none focus:border-saffron"
                />
              </div>
            </div>

            {stored && (
              <p className="text-xs text-charcoal/50">
                Anda masih masuk sebagai <b>{stored.role === "admin" ? "Admin" : "Guru"}</b> — klik{" "}
                <b>Masuk</b> untuk memperbarui sesi.
              </p>
            )}
            {error && (
              <div className="rounded-xl border border-terracotta/40 bg-terracotta/10 px-4 py-2.5 text-sm text-terracotta">
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={busy || (mode === "prod" && (!username.trim() || !password))}
              className="flex items-center justify-center gap-2 rounded-xl bg-sage px-6 py-2.5 text-sm font-semibold text-white shadow-soft transition-colors hover:bg-ocean disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy && <Loader2 className="h-4 w-4 animate-spin" />}
              {busy ? "Memeriksa…" : "Masuk"}
            </button>
          </form>

          {mode === "dev" && (
            <p className="mt-4 rounded-xl bg-sage/10 px-4 py-2.5 text-xs text-sage">
              Mode <b>dev</b> aktif — login otomatis tanpa username/password. Pada mode{" "}
              <b>prod</b>, akun dibaca dari env backend (lihat dokumentasi admin).
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
