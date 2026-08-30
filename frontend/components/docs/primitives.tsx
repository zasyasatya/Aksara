"use client"

import { Lightbulb, AlertTriangle, CheckCircle2 } from "lucide-react"

/** Judul sub-bab di dalam halaman dokumentasi. */
export function DocSection({ id, number, title, children }: { id: string; number?: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24">
      <h2 className="mt-10 mb-4 flex items-baseline gap-3 font-display text-xl lg:text-2xl font-bold text-deep-brown first:mt-0">
        {number && <span className="text-saffron">{number}</span>}
        {title}
      </h2>
      <div className="space-y-4 text-[15px] leading-relaxed text-charcoal/80">{children}</div>
    </section>
  )
}

/** Langkah bernomor (1. 2. 3. ...). */
export function Steps({ items }: { items: { title: string; body: React.ReactNode }[] }) {
  return (
    <ol className="space-y-4">
      {items.map((item, i) => (
        <li key={i} className="flex gap-3">
          <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-deep-brown text-xs font-bold text-cream">
            {i + 1}
          </span>
          <div className="min-w-0 pt-0.5">
            <div className="font-semibold text-deep-brown">{item.title}</div>
            <div className="text-charcoal/70">{item.body}</div>
          </div>
        </li>
      ))}
    </ol>
  )
}

/** Kotak catatan (tips, peringatan, info). */
export function Callout({
  variant = "info",
  title,
  children,
}: {
  variant?: "info" | "warning" | "success"
  title?: string
  children: React.ReactNode
}) {
  const styles = {
    info: "border-ocean/30 bg-ocean/5 text-ocean",
    warning: "border-amber-300 bg-amber-50 text-amber-900",
    success: "border-sage/40 bg-sage/10 text-deep-brown",
  } as const
  const Icon = variant === "warning" ? AlertTriangle : variant === "success" ? CheckCircle2 : Lightbulb
  const colorIcon = variant === "warning" ? "text-amber-500" : variant === "success" ? "text-sage" : "text-ocean"

  return (
    <div className={`my-4 flex items-start gap-3 rounded-2xl border px-4 py-3 ${styles[variant]}`}>
      <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${colorIcon}`} />
      <div className="text-sm leading-relaxed">
        {title && <div className="font-semibold">{title}</div>}
        <div className={variant === "info" ? "text-charcoal/70" : "inherit"}>{children}</div>
      </div>
    </div>
  )
}

/** Kode / command dengan latar gelap. */
export function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="rounded-md bg-deep-brown px-1.5 py-0.5 font-mono text-[13px] text-saffron-light">
      {children}
    </code>
  )
}

/** Blok kode / contoh API lebih lebar. */
export function CodeBlock({ children }: { children: React.ReactNode }) {
  return (
    <pre className="my-4 overflow-x-auto rounded-2xl bg-deep-brown p-4 font-mono text-[13px] leading-relaxed text-cream/90">
      <code>{children}</code>
    </pre>
  )
}

/** Tabel sederhana. */
export function DocTable({ head, rows }: { head: string[]; rows: (string | React.ReactNode)[][] }) {
  return (
    <div className="my-4 overflow-x-auto rounded-2xl border border-sand">
      <table className="w-full min-w-[560px] text-sm">
        <thead>
          <tr className="bg-sand/60 text-left">
            {head.map((h) => (
              <th key={h} className="px-4 py-2.5 font-semibold text-deep-brown">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 ? "bg-cream/60" : "bg-white"}>
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-2.5 align-top text-charcoal/75">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
