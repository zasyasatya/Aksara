"use client"

import type { MlEpochRecord, MlMetricsSummary } from "@/lib/api"

/** Format persentase 0..1 → "97.3%". */
export const pct = (v: number | null | undefined, digits = 1) =>
  v === null || v === undefined || Number.isNaN(v) ? "—" : `${(v * 100).toFixed(digits)}%`

export const fmtBytes = (b: number) => (b > 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`)

export const fmtDate = (iso: string | number | null | undefined) => {
  if (!iso) return "—"
  const d = typeof iso === "number" ? new Date(iso * 1000) : new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  return d.toLocaleString("id-ID", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })
}

/** Warna sesuai nilai metrik (0..1). */
export function metricTone(v: number | null | undefined) {
  if (v === null || v === undefined) return "text-charcoal/40"
  if (v >= 0.9) return "text-sage"
  if (v >= 0.75) return "text-amber-600"
  return "text-terracotta"
}

export const SPLIT_LABEL: Record<string, string> = { train: "Train", val: "Val", test: "Test" }
export const SOURCE_LABEL: Record<string, string> = { synthetic: "Sintetis", upload: "Unggah", canvas: "Kanvas", import: "Impor" }
export const STATUS_LABEL: Record<string, string> = { labeled: "Berlabel", unlabeled: "Belum berlabel", review: "Perlu tinjauan" }

export function Pill({ children, tone = "sand", className = "" }: { children: React.ReactNode; tone?: "sand" | "sage" | "saffron" | "terracotta" | "ocean" | "brown"; className?: string }) {
  const tones = {
    sand: "bg-sand/80 text-deep-brown/70",
    sage: "bg-sage/15 text-sage border border-sage/40",
    saffron: "bg-saffron/15 text-saffron-dark border border-saffron/40",
    terracotta: "bg-terracotta/10 text-terracotta border border-terracotta/40",
    ocean: "bg-ocean/10 text-ocean border border-ocean/30",
    brown: "bg-deep-brown text-cream",
  }
  return <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${tones[tone]} ${className}`}>{children}</span>
}

/** Kotak metrik besar (accuracy/F1/precision/recall). */
export function MetricTile({ label, value, hint, tone }: { label: string; value: number | null | undefined; hint?: string; tone?: string }) {
  return (
    <div className="rounded-2xl border border-sand bg-white p-4 shadow-soft">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-charcoal/50">{label}</div>
      <div className={`mt-1 font-display text-2xl font-bold ${tone ?? metricTone(value)}`}>{pct(value, 2)}</div>
      {hint && <div className="mt-0.5 text-[11px] text-charcoal/45">{hint}</div>}
    </div>
  )
}

/** Ringkasan 4 metrik utama dalam satu baris. */
export function MetricsRow({ m, compact = false }: { m: MlMetricsSummary; compact?: boolean }) {
  const items: [string, number | undefined][] = [
    ["Accuracy", m.accuracy],
    ["Precision", m.macro_precision],
    ["Recall", m.macro_recall],
    ["F1", m.macro_f1],
  ]
  return (
    <div className={`grid gap-2 ${compact ? "grid-cols-4" : "grid-cols-2 sm:grid-cols-4"}`}>
      {items.map(([k, v]) => (
        <div key={k} className={`rounded-xl border border-sand bg-cream/40 px-3 ${compact ? "py-1.5" : "py-2"}`}>
          <div className="text-[10px] font-semibold uppercase tracking-wide text-charcoal/45">{k}</div>
          <div className={`font-display font-bold ${compact ? "text-sm" : "text-lg"} ${metricTone(v)}`}>{pct(v)}</div>
        </div>
      ))}
    </div>
  )
}

/** Bar horizontal sederhana 0..1. */
export function Bar({ value, tone = "bg-sage", className = "" }: { value: number; tone?: string; className?: string }) {
  return (
    <div className={`h-2 w-full overflow-hidden rounded-full bg-sand/70 ${className}`}>
      <div className={`h-full rounded-full ${tone} transition-all`} style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }} />
    </div>
  )
}

/** Kurva training (loss & akurasi per epoch) tanpa dependensi chart. */
export function TrainingCurve({ history, height = 150 }: { history: MlEpochRecord[]; height?: number }) {
  const pts = history.filter((h) => h.epoch !== undefined)
  if (pts.length < 2) {
    return <div className="flex h-24 items-center justify-center rounded-xl border border-dashed border-sand text-xs text-charcoal/40">Kurva tampil setelah ≥ 2 epoch.</div>
  }
  const W = 600
  const H = height
  const padL = 34, padR = 10, padT = 10, padB = 22
  const xs = (i: number) => padL + (i / (pts.length - 1)) * (W - padL - padR)
  const losses = pts.map((p) => p.loss ?? 0)
  const maxLoss = Math.max(...losses, 1e-6)
  const yLoss = (v: number) => padT + (1 - v / maxLoss) * (H - padT - padB)
  const yAcc = (v: number) => padT + (1 - v) * (H - padT - padB)
  const path = (vals: (number | null)[], y: (v: number) => number) =>
    vals.map((v, i) => (v === null || v === undefined ? null : `${i === 0 || vals[i - 1] === null ? "M" : "L"}${xs(i).toFixed(1)},${y(v).toFixed(1)}`)).filter(Boolean).join(" ")
  const hasLoss = pts.some((p) => p.loss !== null && p.loss !== undefined)
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Kurva pelatihan">
        {[0, 0.25, 0.5, 0.75, 1].map((g) => (
          <g key={g}>
            <line x1={padL} x2={W - padR} y1={yAcc(g)} y2={yAcc(g)} stroke="#F4E4BC" strokeWidth={1} />
            <text x={padL - 6} y={yAcc(g) + 3} fontSize={9} textAnchor="end" fill="#8a8a8a">{Math.round(g * 100)}%</text>
          </g>
        ))}
        {hasLoss && <path d={path(losses, yLoss)} fill="none" stroke="#C45A3C" strokeWidth={2} strokeDasharray="4 3" />}
        <path d={path(pts.map((p) => p.train_acc), yAcc)} fill="none" stroke="#2A6F8E" strokeWidth={2} />
        <path d={path(pts.map((p) => p.val_acc), yAcc)} fill="none" stroke="#7A9E7E" strokeWidth={2.5} />
        {pts.map((p, i) => (
          <text key={i} x={xs(i)} y={H - 6} fontSize={9} textAnchor="middle" fill="#8a8a8a">{pts.length > 20 && i % Math.ceil(pts.length / 15) !== 0 ? "" : p.epoch}</text>
        ))}
      </svg>
      <div className="mt-1 flex flex-wrap gap-4 text-[11px] text-charcoal/60">
        <span className="inline-flex items-center gap-1.5"><span className="h-0.5 w-5 bg-ocean" /> akurasi train</span>
        <span className="inline-flex items-center gap-1.5"><span className="h-0.5 w-5 bg-sage" /> akurasi val</span>
        {hasLoss && <span className="inline-flex items-center gap-1.5"><span className="h-0.5 w-5 border-t-2 border-dashed border-terracotta" /> loss (skala relatif, maks {maxLoss.toFixed(2)})</span>}
      </div>
    </div>
  )
}

/** Confusion matrix heat-map. */
export function ConfusionMatrix({ matrix, labels, glyphs }: { matrix: number[][]; labels: string[]; glyphs?: Record<string, string> }) {
  const n = labels.length
  if (!n) return null
  const rowMax = matrix.map((r) => Math.max(1, ...r))
  const cell = n > 24 ? 18 : n > 12 ? 24 : 32
  return (
    <div className="overflow-auto">
      <table className="border-collapse text-[10px]" style={{ minWidth: cell * (n + 1) }}>
        <thead>
          <tr>
            <th className="sticky left-0 z-10 bg-white p-1 text-left text-[9px] font-semibold text-charcoal/40">asli ↓ / prediksi →</th>
            {labels.map((l) => (
              <th key={l} className="p-0.5 text-center font-semibold text-deep-brown/70" style={{ width: cell }} title={l}>
                <span className="font-bali text-sm">{glyphs?.[l] ?? ""}</span>
                <div className="text-[8px] font-normal text-charcoal/50">{l}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={labels[i]}>
              <th className="sticky left-0 z-10 bg-white p-1 text-left font-semibold text-deep-brown/80">
                <span className="font-bali text-sm">{glyphs?.[labels[i]] ?? ""}</span> <span className="text-[9px] text-charcoal/55">{labels[i]}</span>
              </th>
              {row.map((v, j) => {
                const diag = i === j
                const alpha = v / rowMax[i]
                const bg = v === 0 ? "transparent" : diag ? `rgba(122,158,126,${0.15 + alpha * 0.8})` : `rgba(196,90,60,${0.15 + alpha * 0.8})`
                return (
                  <td key={j} title={`asli ${labels[i]} → prediksi ${labels[j]}: ${v}`} className="border border-sand/60 text-center font-semibold" style={{ width: cell, height: cell, background: bg, color: alpha > 0.55 ? "white" : "#2C1810" }}>
                    {v || ""}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function EmptyState({ icon: Icon, title, body, action }: { icon: any; title: string; body: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-sand bg-cream/40 px-6 py-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-charcoal/40 shadow-soft"><Icon className="h-6 w-6" /></div>
      <div className="mt-3 font-display text-lg font-bold text-deep-brown">{title}</div>
      <p className="mt-1 max-w-md text-sm text-charcoal/55">{body}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export const btnPrimary = "inline-flex items-center gap-2 rounded-full bg-saffron px-5 py-2 text-sm font-semibold text-cream shadow-soft transition-colors hover:bg-saffron-dark disabled:opacity-50 disabled:pointer-events-none"
export const btnSecondary = "inline-flex items-center gap-2 rounded-full bg-deep-brown px-5 py-2 text-sm font-semibold text-cream shadow-soft transition-colors hover:bg-charcoal disabled:opacity-50 disabled:pointer-events-none"
export const btnGhost = "inline-flex items-center gap-1.5 rounded-full border border-sand bg-white px-4 py-2 text-sm font-semibold text-charcoal/70 shadow-soft transition-colors hover:border-deep-brown/40 hover:text-deep-brown disabled:opacity-50 disabled:pointer-events-none"
export const btnDanger = "inline-flex items-center gap-1.5 rounded-full border border-sand bg-white px-4 py-2 text-sm font-semibold text-terracotta shadow-soft transition-colors hover:border-terracotta/50 hover:bg-terracotta/5 disabled:opacity-50 disabled:pointer-events-none"
