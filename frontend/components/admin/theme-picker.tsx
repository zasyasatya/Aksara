"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { applyTheme, DEFAULT_THEME_ID, THEME_STORAGE_KEY, THEMES, ThemeDef } from "@/lib/themes"
import { Palette, Check, Loader2, RotateCcw, Eye } from "lucide-react"

/** Kartu pratinjau palet: mini mock-up header + tombol + kartu. */
function Swatch({ t, active, previewing, onPreview, onApply, busy }: {
  t: ThemeDef; active: boolean; previewing: boolean; busy: boolean
  onPreview: () => void; onApply: () => void
}) {
  const c = t.tokens
  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border-2 bg-white text-left shadow-soft transition-all ${
        active ? "border-saffron ring-2 ring-saffron/30" : previewing ? "border-deep-brown/50" : "border-sand hover:border-deep-brown/30"
      }`}
    >
      <button type="button" onClick={onPreview} className="block w-full text-left" title="Pratinjau palet ini (belum disimpan)">
        <div className="p-3" style={{ background: c.cream }}>
          <div className="flex items-center justify-between rounded-lg px-2 py-1.5" style={{ background: c.cream, border: `1px solid ${c.sand}` }}>
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-md" style={{ background: c.saffron }} />
              <span className="h-1.5 w-8 rounded-full" style={{ background: c["deep-brown"] }} />
            </div>
            <span className="h-3 w-3 rounded-full" style={{ background: c["deep-brown"] }} />
          </div>
          <div className="mt-2 grid grid-cols-3 gap-1.5">
            <div className="col-span-2 rounded-lg p-2" style={{ background: "#fff", border: `1px solid ${c.sand}` }}>
              <div className="h-1.5 w-10 rounded-full" style={{ background: c["deep-brown"] }} />
              <div className="mt-1 h-1 w-14 rounded-full" style={{ background: c.charcoal, opacity: 0.35 }} />
              <div className="mt-2 inline-block rounded-full px-2 py-0.5 text-[8px] font-bold" style={{ background: c.saffron, color: "#fff" }}>Mulai</div>
            </div>
            <div className="flex flex-col gap-1.5">
              <div className="flex-1 rounded-lg" style={{ background: c.sage, opacity: 0.6 }} />
              <div className="flex-1 rounded-lg" style={{ background: c.ocean, opacity: 0.6 }} />
              <div className="flex-1 rounded-lg" style={{ background: c.terracotta, opacity: 0.7 }} />
            </div>
          </div>
        </div>
        <div className="flex gap-0 h-2">
          {[c.saffron, c["saffron-dark"], c["deep-brown"], c.terracotta, c.sage, c.ocean, c.sand].map((h, i) => (
            <span key={i} className="flex-1" style={{ background: h }} />
          ))}
        </div>
        <div className="px-3 pt-2.5">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-deep-brown">{t.name}</span>
            {t.id === DEFAULT_THEME_ID && (
              <span className="rounded-full bg-sand/80 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-deep-brown/70">Default</span>
            )}
          </div>
          <p className="mt-0.5 text-[11px] leading-snug text-charcoal/55">{t.tagline}</p>
        </div>
      </button>
      <div className="flex items-center justify-between px-3 pb-3 pt-2">
        <span className={`inline-flex items-center gap-1 text-[11px] font-semibold ${active ? "text-sage" : previewing ? "text-saffron-dark" : "text-charcoal/40"}`}>
          {active ? <><Check className="h-3.5 w-3.5" /> Aktif</> : previewing ? <><Eye className="h-3.5 w-3.5" /> Pratinjau</> : "\u00a0"}
        </span>
        {!active && (
          <button
            type="button"
            disabled={busy}
            onClick={onApply}
            className="inline-flex items-center gap-1.5 rounded-full bg-deep-brown px-3 py-1 text-[11px] font-semibold text-cream shadow-soft transition-colors hover:bg-charcoal disabled:opacity-60"
          >
            {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : null} Terapkan
          </button>
        )}
      </div>
    </div>
  )
}

export function ThemePicker({ onMessage, onError }: { onMessage?: (m: string) => void; onError?: (m: string) => void }) {
  const [active, setActive] = useState<string>(DEFAULT_THEME_ID)
  const [preview, setPreview] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    api.settings.getTheme().then((r) => { setActive(r.theme); setLoaded(true) }).catch(() => setLoaded(true))
  }, [])

  // Pratinjau hanya lokal — kembalikan ke palet aktif saat komponen dilepas.
  useEffect(() => () => { applyTheme(active) }, [active])

  const doPreview = (id: string) => { setPreview(id); applyTheme(id) }
  const cancelPreview = () => { setPreview(null); applyTheme(active) }

  const doApply = async (id: string) => {
    setBusy(id)
    try {
      const r = await api.settings.setTheme(id)
      setActive(r.theme)
      setPreview(null)
      applyTheme(r.theme)
      try { localStorage.setItem(THEME_STORAGE_KEY, r.theme) } catch {}
      onMessage?.(r.message)
    } catch (e) {
      applyTheme(active)
      onError?.((e as Error).message)
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="mt-6 overflow-hidden rounded-3xl border border-sand bg-white shadow-soft">
      <div className="flex flex-col gap-3 border-b border-sand px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-saffron to-terracotta text-white">
            <Palette className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-display text-lg font-bold text-deep-brown">Palet Warna Aplikasi</h2>
            <p className="text-xs text-charcoal/55">
              Ganti nuansa warna seluruh platform untuk semua pengunjung. Klik kartu untuk pratinjau, lalu <strong>Terapkan</strong>.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {preview && preview !== active && (
            <button onClick={cancelPreview} className="inline-flex items-center gap-1.5 rounded-full border border-sand bg-white px-3 py-1.5 text-xs font-semibold text-charcoal/60 hover:text-deep-brown">
              <RotateCcw className="h-3.5 w-3.5" /> Batal pratinjau
            </button>
          )}
          {active !== DEFAULT_THEME_ID && (
            <button
              disabled={busy !== null}
              onClick={() => doApply(DEFAULT_THEME_ID)}
              className="inline-flex items-center gap-1.5 rounded-full border border-saffron/40 bg-saffron/10 px-3 py-1.5 text-xs font-semibold text-saffron-dark hover:bg-saffron/20 disabled:opacity-60"
            >
              <RotateCcw className="h-3.5 w-3.5" /> Kembali ke Native
            </button>
          )}
        </div>
      </div>

      <div className="grid gap-4 p-6 sm:grid-cols-2 lg:grid-cols-3">
        {THEMES.map((t) => (
          <Swatch
            key={t.id}
            t={t}
            active={loaded && active === t.id}
            previewing={preview === t.id && active !== t.id}
            busy={busy === t.id}
            onPreview={() => doPreview(t.id)}
            onApply={() => doApply(t.id)}
          />
        ))}
      </div>

      <div className="border-t border-sand bg-cream/60 px-6 py-3 text-xs text-charcoal/50">
        Pilihan tersimpan ke <code className="rounded bg-white px-1">backend/app/data/settings.json</code> via{" "}
        <code className="rounded bg-white px-1">PUT /api/settings/theme</code>. Palet <strong>Native</strong> selalu menjadi default.
      </div>
    </div>
  )
}
