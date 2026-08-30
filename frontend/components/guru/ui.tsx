"use client"

import { useState } from "react"
import { CheckCircle2, Trash2, XCircle } from "lucide-react"

/** Label + wrapper untuk field form. */
export function Field({ label, hint, children, className = "" }: { label: string; hint?: string; children: React.ReactNode; className?: string }) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-1.5 block text-xs font-semibold text-charcoal/70">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-[11px] text-charcoal/45">{hint}</span>}
    </label>
  )
}

const inputCls =
  "w-full rounded-xl border border-sand bg-cream/50 px-3 py-2 text-sm outline-none transition-colors focus:border-saffron focus:bg-white"

export function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`${inputCls} ${props.className ?? ""}`} />
}

export function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`${inputCls} resize-y ${props.className ?? ""}`} />
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`${inputCls} ${props.className ?? ""}`} />
}

/** Sakelar kecil untuk checkbox-like (is_published, is_correct). */
export function MiniToggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label?: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="inline-flex shrink-0 items-center gap-2"
    >
      <span className={`relative inline-flex h-5 w-9 items-center rounded-full border transition-colors ${checked ? "bg-sage/30 border-sage/60" : "bg-sand/80 border-sand"}`}>
        <span className={`absolute h-3.5 w-3.5 rounded-full bg-white shadow-soft transition-all ${checked ? "left-[18px]" : "left-0.5"}`} />
      </span>
      {label && <span className={`text-xs font-semibold ${checked ? "text-sage" : "text-charcoal/45"}`}>{label}</span>}
    </button>
  )
}

/** Tombol hapus dengan konfirmasi inline (2 klik). */
export function ConfirmDelete({ onConfirm, label = "Hapus" }: { onConfirm: () => void; label?: string }) {
  const [armed, setArmed] = useState(false)
  return armed ? (
    <span className="inline-flex items-center gap-1">
      <button
        type="button"
        onClick={onConfirm}
        className="rounded-full bg-terracotta px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-600"
      >
        Yakin?
      </button>
      <button
        type="button"
        onClick={() => setArmed(false)}
        className="rounded-full border border-sand bg-white px-3 py-1.5 text-xs font-semibold text-charcoal/60"
      >
        Batal
      </button>
    </span>
  ) : (
    <button
      type="button"
      onClick={() => setArmed(true)}
      className="inline-flex items-center gap-1 rounded-full border border-sand bg-white px-3 py-1.5 text-xs font-semibold text-terracotta hover:border-terracotta/50 hover:bg-terracotta/5"
    >
      <Trash2 className="h-3 w-3" />
      {label}
    </button>
  )
}

/** Banner notifikasi sukses/gagal di atas konten. */
export function Flash({ kind, text, onDone }: { kind: "ok" | "err"; text: string; onDone: () => void }) {
  return (
    <div
      className={`flex items-start justify-between gap-3 rounded-2xl border px-4 py-3 text-sm ${
        kind === "ok" ? "border-sage/50 bg-sage/10 text-deep-brown" : "border-terracotta/40 bg-terracotta/10 text-terracotta"
      }`}
    >
      <span className="flex items-start gap-2">
        {kind === "ok" ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-sage" /> : <XCircle className="mt-0.5 h-4 w-4 shrink-0" />}
        {text}
      </span>
      <button type="button" onClick={onDone} className="text-xs font-semibold opacity-60 hover:opacity-100">
        Tutup
      </button>
    </div>
  )
}

/** Header kartu tab: judul + tombol tambah. */
export function TabHeader({ title, subtitle, onAdd, addLabel }: { title: string; subtitle: string; onAdd: () => void; addLabel: string }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-sand px-6 py-4">
      <div>
        <h2 className="font-display text-lg font-bold text-deep-brown">{title}</h2>
        <p className="text-xs text-charcoal/55">{subtitle}</p>
      </div>
      <button
        type="button"
        onClick={onAdd}
        className="rounded-full bg-saffron px-5 py-2 text-sm font-semibold text-cream shadow-soft transition-colors hover:bg-saffron-dark"
      >
        {addLabel}
      </button>
    </div>
  )
}
