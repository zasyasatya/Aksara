"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { api, MlClass, MlModelEntry, MlReport } from "@/lib/api"
import { Flash, TextInput, ConfirmDelete } from "@/components/guru/ui"
import {
  ConfusionMatrix, EmptyState, MetricTile, MetricsRow, Pill, TrainingCurve, btnGhost, btnPrimary, btnSecondary, fmtBytes, fmtDate, metricTone, pct,
} from "@/components/admin/ml-ui"
import { Boxes, Rocket, Loader2, ChevronDown, ChevronUp, BarChart3, Grid3X3, Pencil, Check, X, Trophy, RefreshCw, Power, ArrowUpDown } from "lucide-react"

type FlashT = { kind: "ok" | "err"; text: string } | null
type SortKey = "created_at" | "accuracy" | "macro_f1" | "macro_precision" | "macro_recall" | "train_seconds" | "size_bytes"

export function TabModels({ refreshKey, onChanged }: { refreshKey?: number; onChanged?: () => void }) {
  const [models, setModels] = useState<MlModelEntry[]>([])
  const [prodId, setProdId] = useState<string | null>(null)
  const [classes, setClasses] = useState<Record<string, MlClass>>({})
  const [loading, setLoading] = useState(true)
  const [flash, setFlash] = useState<FlashT>(null)
  const [open, setOpen] = useState<string | null>(null)
  const [report, setReport] = useState<Record<string, MlReport | null>>({})
  const [busy, setBusy] = useState<string | null>(null)
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: "created_at", dir: -1 })
  const [editing, setEditing] = useState<{ id: string; name: string; notes: string } | null>(null)

  const load = useCallback(async () => {
    try {
      const [m, c] = await Promise.all([api.ml.models(), api.ml.classes()])
      setModels(m.models)
      setProdId(m.production_model_id)
      const map: Record<string, MlClass> = {}
      c.available.forEach((x) => { map[x.label] = x })
      setClasses(map)
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load, refreshKey])

  const openReport = async (id: string) => {
    if (open === id) { setOpen(null); return }
    setOpen(id)
    if (!(id in report)) {
      try {
        const r = await api.ml.model(id)
        setReport((prev) => ({ ...prev, [id]: r.report }))
      } catch (e) {
        setFlash({ kind: "err", text: (e as Error).message })
      }
    }
  }

  const promote = async (id: string | null) => {
    setBusy(id ?? "none")
    try {
      const r = await api.ml.setProduction(id)
      setFlash({ kind: "ok", text: r.message })
      await load()
      onChanged?.()
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    } finally {
      setBusy(null)
    }
  }

  const remove = async (id: string) => {
    try {
      const r = await api.ml.deleteModel(id)
      setFlash({ kind: "ok", text: r.message })
      await load()
      onChanged?.()
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    }
  }

  const saveEdit = async () => {
    if (!editing) return
    try {
      await api.ml.updateModel(editing.id, { name: editing.name, notes: editing.notes })
      setEditing(null)
      await load()
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    }
  }

  const sorted = useMemo(() => {
    const val = (m: MlModelEntry): number | string => {
      if (sort.key === "created_at") return m.created_at
      if (sort.key === "train_seconds") return m.train_seconds
      if (sort.key === "size_bytes") return m.size_bytes
      return (m.metrics as any)[sort.key] ?? 0
    }
    return [...models].sort((a, b) => (val(a) > val(b) ? 1 : val(a) < val(b) ? -1 : 0) * sort.dir)
  }, [models, sort])

  const best = useMemo(() => models.reduce<MlModelEntry | null>((acc, m) => (!acc || m.metrics.macro_f1 > acc.metrics.macro_f1 ? m : acc), null), [models])
  const prod = models.find((m) => m.id === prodId) ?? null
  const glyphs = useMemo(() => Object.fromEntries(Object.values(classes).map((c) => [c.label, c.glyph])), [classes])

  const th = (label: string, key: SortKey) => (
    <th className="cursor-pointer select-none whitespace-nowrap px-3 py-2 font-semibold hover:text-deep-brown" onClick={() => setSort((s) => ({ key, dir: s.key === key ? (s.dir === 1 ? -1 : 1) : -1 }))}>
      <span className="inline-flex items-center gap-1">{label}{sort.key === key && <ArrowUpDown className="h-3 w-3" />}</span>
    </th>
  )

  return (
    <div className="space-y-4">
      {flash && <Flash kind={flash.kind} text={flash.text} onDone={() => setFlash(null)} />}

      {/* Model produksi */}
      <div className={`rounded-3xl border p-5 shadow-soft ${prod ? "border-sage/50 bg-sage/10" : "border-saffron/40 bg-saffron/5"}`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className={`flex h-11 w-11 items-center justify-center rounded-2xl ${prod ? "bg-sage text-white" : "bg-saffron/20 text-saffron-dark"}`}><Rocket className="h-5 w-5" /></div>
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wide text-charcoal/50">Model produksi aktif</div>
              {prod ? (
                <div className="font-display text-lg font-bold text-deep-brown">{prod.name} <span className="text-sm font-normal text-charcoal/50">· {prod.arch_name}</span></div>
              ) : (
                <div className="font-display text-lg font-bold text-deep-brown">Belum ada</div>
              )}
              <div className="text-xs text-charcoal/55">{prod ? `dipakai endpoint POST /api/ml/predict · dipromosikan ${fmtDate(prod.promoted_at)}` : "Pilih model dari daftar di bawah, klik “Jadikan produksi”."}</div>
            </div>
          </div>
          {prod && (
            <div className="flex items-center gap-3">
              <div className="w-72"><MetricsRow m={prod.metrics} compact /></div>
              <button disabled={busy !== null} onClick={() => promote(null)} className={btnGhost} title="Nonaktifkan model produksi"><Power className="h-4 w-4" /></button>
            </div>
          )}
        </div>
      </div>

      {/* Registry */}
      <div className="rounded-3xl border border-sand bg-white shadow-soft">
        <div className="flex items-center justify-between gap-3 border-b border-sand px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-deep-brown text-cream"><Boxes className="h-5 w-5" /></div>
            <div>
              <h2 className="font-display text-lg font-bold text-deep-brown">Registry Model</h2>
              <p className="text-xs text-charcoal/55">{models.length} model terlatih · klik baris untuk laporan evaluasi lengkap (per kelas + confusion matrix).</p>
            </div>
          </div>
          <button onClick={() => load()} className="inline-flex items-center gap-1.5 text-xs font-semibold text-charcoal/50 hover:text-saffron-dark"><RefreshCw className="h-3.5 w-3.5" /> Muat ulang</button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center gap-3 py-16 text-charcoal/50"><Loader2 className="h-5 w-5 animate-spin" /> Memuat…</div>
        ) : models.length === 0 ? (
          <div className="p-6"><EmptyState icon={Boxes} title="Belum ada model terlatih" body="Buka tab Training, pilih arsitektur, lalu jalankan retraining. Setiap model yang selesai muncul di sini beserta metriknya." /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-sand text-[11px] uppercase tracking-wide text-charcoal/45">
                  <th className="px-6 py-2 font-semibold">Model</th>
                  {th("Akurasi", "accuracy")}
                  {th("Precision", "macro_precision")}
                  {th("Recall", "macro_recall")}
                  {th("F1", "macro_f1")}
                  <th className="px-3 py-2 font-semibold">Train acc</th>
                  {th("Durasi", "train_seconds")}
                  {th("Ukuran", "size_bytes")}
                  {th("Dibuat", "created_at")}
                  <th className="px-6 py-2 text-right font-semibold">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-sand">
                {sorted.map((m) => {
                  const isProd = m.id === prodId
                  const isOpen = open === m.id
                  const overfit = m.metrics.train_accuracy !== undefined && m.metrics.train_accuracy - m.metrics.accuracy > 0.15
                  return (
                    <ModelRows key={m.id}>
                      <tr className={`cursor-pointer transition-colors hover:bg-cream/50 ${isProd ? "bg-sage/5" : ""}`} onClick={() => openReport(m.id)}>
                        <td className="px-6 py-3">
                          <div className="flex items-center gap-2">
                            {isOpen ? <ChevronUp className="h-4 w-4 text-charcoal/40" /> : <ChevronDown className="h-4 w-4 text-charcoal/40" />}
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-1.5 font-semibold text-deep-brown">
                                {m.name}
                                <Pill>{m.arch}</Pill>
                                {isProd && <Pill tone="sage"><Rocket className="h-3 w-3" /> produksi</Pill>}
                                {best?.id === m.id && models.length > 1 && <Pill tone="saffron"><Trophy className="h-3 w-3" /> F1 terbaik</Pill>}
                                {overfit && <Pill tone="terracotta">overfit?</Pill>}
                              </div>
                              <div className="text-[11px] text-charcoal/50">{m.id} · {m.n_classes} kelas · {m.n_params.toLocaleString("id-ID")} parameter · eval pada {m.eval_split} ({m.metrics.n_samples})</div>
                            </div>
                          </div>
                        </td>
                        <td className={`px-3 py-3 font-bold ${metricTone(m.metrics.accuracy)}`}>{pct(m.metrics.accuracy)}</td>
                        <td className={`px-3 py-3 ${metricTone(m.metrics.macro_precision)}`}>{pct(m.metrics.macro_precision)}</td>
                        <td className={`px-3 py-3 ${metricTone(m.metrics.macro_recall)}`}>{pct(m.metrics.macro_recall)}</td>
                        <td className={`px-3 py-3 font-bold ${metricTone(m.metrics.macro_f1)}`}>{pct(m.metrics.macro_f1)}</td>
                        <td className="px-3 py-3 text-charcoal/60">{pct(m.metrics.train_accuracy)}</td>
                        <td className="px-3 py-3 text-charcoal/60">{m.train_seconds < 60 ? `${m.train_seconds.toFixed(1)} dtk` : `${(m.train_seconds / 60).toFixed(1)} mnt`}</td>
                        <td className="px-3 py-3 text-charcoal/60">{fmtBytes(m.size_bytes)}</td>
                        <td className="whitespace-nowrap px-3 py-3 text-xs text-charcoal/60">{fmtDate(m.created_at)}</td>
                        <td className="px-6 py-3" onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center justify-end gap-2">
                            {!isProd && (
                              <button disabled={busy !== null} onClick={() => promote(m.id)} className={btnSecondary}>
                                {busy === m.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />} Jadikan produksi
                              </button>
                            )}
                            <button onClick={() => setEditing({ id: m.id, name: m.name, notes: m.notes })} className={btnGhost} title="Ubah nama/catatan"><Pencil className="h-3.5 w-3.5" /></button>
                            {!isProd && <ConfirmDelete onConfirm={() => remove(m.id)} />}
                          </div>
                        </td>
                      </tr>
                      {editing?.id === m.id && (
                        <tr className="bg-cream/40"><td colSpan={10} className="px-6 py-3">
                          <div className="flex flex-wrap items-end gap-3">
                            <label className="flex-1 text-xs font-semibold text-charcoal/60">Nama<TextInput value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} /></label>
                            <label className="flex-[2] text-xs font-semibold text-charcoal/60">Catatan<TextInput value={editing.notes} onChange={(e) => setEditing({ ...editing, notes: e.target.value })} /></label>
                            <button onClick={saveEdit} className={btnPrimary}><Check className="h-4 w-4" /> Simpan</button>
                            <button onClick={() => setEditing(null)} className={btnGhost}><X className="h-4 w-4" /></button>
                          </div>
                        </td></tr>
                      )}
                      {isOpen && (
                        <tr><td colSpan={10} className="bg-cream/30 px-6 py-5">
                          <ReportView model={m} report={report[m.id]} glyphs={glyphs} />
                        </td></tr>
                      )}
                    </ModelRows>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function ModelRows({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

export function ReportView({ model, report, glyphs }: { model: MlModelEntry; report: MlReport | null | undefined; glyphs: Record<string, string> }) {
  const [view, setView] = useState<"perclass" | "matrix" | "curve">("perclass")
  if (report === undefined) return <div className="flex items-center gap-2 text-sm text-charcoal/50"><Loader2 className="h-4 w-4 animate-spin" /> Memuat laporan…</div>
  if (report === null) return <div className="text-sm text-charcoal/50">Laporan evaluasi tidak tersedia untuk model ini.</div>
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Accuracy" value={report.accuracy} hint={`${report.n_samples} sampel ${report.eval_split}`} />
        <MetricTile label="Precision (makro)" value={report.macro_precision} hint={`berbobot ${pct(report.weighted_precision)}`} />
        <MetricTile label="Recall (makro)" value={report.macro_recall} hint={`berbobot ${pct(report.weighted_recall)}`} />
        <MetricTile label="F1-score (makro)" value={report.macro_f1} hint={`berbobot ${pct(report.weighted_f1)}`} />
      </div>
      <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-charcoal/65">
        <span>Top-3 acc: <b>{pct(report.top3_accuracy)}</b></span>
        <span>Log-loss: <b>{report.log_loss?.toFixed(4) ?? "—"}</b></span>
        <span>Train acc: <b>{pct(report.train_accuracy)}</b>{report.train_accuracy !== undefined && report.train_accuracy - report.accuracy > 0.15 && <span className="ml-1 text-terracotta">(gap besar → indikasi overfit)</span>}</span>
        <span>Rata-rata confidence: <b>{pct(report.mean_confidence)}</b></span>
        <span>Confident (≥80%): <b>{pct(report.confident_rate)}</b> dari sampel, akurasinya <b>{pct(report.confident_accuracy)}</b></span>
        <span>Data: train {report.train_samples} · val {report.val_samples} · test {report.test_samples}</span>
        <span>Durasi latih: <b>{report.train_seconds.toFixed(2)} dtk</b></span>
        <span>Hyperparameter: {Object.entries(model.hyperparams).map(([k, v]) => `${k}=${v}`).join(", ") || "—"}</span>
      </div>
      {report.top_confusions.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-semibold text-charcoal/60">Paling sering tertukar:</span>
          {report.top_confusions.slice(0, 6).map((c, i) => (
            <span key={i} className="rounded-full border border-terracotta/30 bg-terracotta/5 px-2 py-0.5 text-terracotta"><span className="font-bali">{glyphs[c.true]}</span> {c.true} → <span className="font-bali">{glyphs[c.pred]}</span> {c.pred} <b>×{c.count}</b></span>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        {([["perclass", "Per kelas", BarChart3], ["matrix", "Confusion matrix", Grid3X3], ["curve", "Kurva pelatihan", BarChart3]] as const).map(([k, label, Icon]) => (
          <button key={k} onClick={() => setView(k)} className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold ${view === k ? "bg-deep-brown text-cream" : "border border-sand bg-white text-charcoal/60"}`}><Icon className="h-3.5 w-3.5" /> {label}</button>
        ))}
      </div>
      {view === "perclass" && (
        <div className="overflow-x-auto rounded-2xl border border-sand bg-white">
          <table className="w-full text-xs">
            <thead><tr className="border-b border-sand text-left text-[10px] uppercase tracking-wide text-charcoal/45"><th className="px-3 py-2">Kelas</th><th className="px-3 py-2">Precision</th><th className="px-3 py-2">Recall</th><th className="px-3 py-2">F1</th><th className="px-3 py-2">Support</th><th className="px-3 py-2">TP / FP / FN</th><th className="w-40 px-3 py-2">F1</th></tr></thead>
            <tbody className="divide-y divide-sand/70">
              {report.per_class.map((p) => (
                <tr key={p.label} className={p.support === 0 ? "opacity-40" : ""}>
                  <td className="px-3 py-1.5 font-semibold text-deep-brown"><span className="font-bali text-base">{glyphs[p.label]}</span> {p.label}</td>
                  <td className={`px-3 py-1.5 ${metricTone(p.precision)}`}>{pct(p.precision)}</td>
                  <td className={`px-3 py-1.5 ${metricTone(p.recall)}`}>{pct(p.recall)}</td>
                  <td className={`px-3 py-1.5 font-bold ${metricTone(p.f1)}`}>{pct(p.f1)}</td>
                  <td className="px-3 py-1.5 text-charcoal/60">{p.support}</td>
                  <td className="px-3 py-1.5 text-charcoal/60">{p.tp} / {p.fp} / {p.fn}</td>
                  <td className="px-3 py-1.5"><div className="h-2 w-full overflow-hidden rounded-full bg-sand/70"><div className={`h-full ${p.f1 >= 0.9 ? "bg-sage" : p.f1 >= 0.75 ? "bg-amber-400" : "bg-terracotta"}`} style={{ width: `${p.f1 * 100}%` }} /></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {view === "matrix" && <div className="rounded-2xl border border-sand bg-white p-3"><ConfusionMatrix matrix={report.confusion_matrix} labels={report.class_names} glyphs={glyphs} /></div>}
      {view === "curve" && <div className="rounded-2xl border border-sand bg-white p-4"><TrainingCurve history={report.history} /></div>}
      {report.misclassified.length > 0 && (
        <div>
          <div className="mb-2 text-xs font-bold uppercase tracking-wide text-charcoal/50">Contoh salah klasifikasi ({report.misclassified.length})</div>
          <div className="flex flex-wrap gap-2">
            {report.misclassified.slice(0, 24).map((m, i) => (
              <div key={i} className="w-20 rounded-xl border border-sand bg-white p-1 text-center">
                {m.sample_id ? /* eslint-disable-next-line @next/next/no-img-element */ <img src={api.ml.sampleImageUrl(m.sample_id)} alt="" className="aspect-square w-full rounded-lg object-contain" loading="lazy" /> : <div className="aspect-square w-full rounded-lg bg-cream" />}
                <div className="mt-0.5 text-[10px] leading-tight"><span className="text-sage">{m.true}</span> → <span className="text-terracotta">{m.pred}</span><div className="text-charcoal/40">{pct(m.confidence, 0)}</div></div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
