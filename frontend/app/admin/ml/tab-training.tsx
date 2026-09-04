"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { api, MlArchitecture, MlDatasetStats, MlJob } from "@/lib/api"
import { Field, TextInput, Flash } from "@/components/guru/ui"
import { Bar, MetricsRow, Pill, TrainingCurve, btnGhost, btnPrimary, fmtDate, pct } from "@/components/admin/ml-ui"
import { Brain, Cpu, Loader2, Play, Square, CheckCircle2, XCircle, Clock, ChevronDown, ChevronUp, Rocket, Info } from "lucide-react"

type FlashT = { kind: "ok" | "err"; text: string } | null

export function TabTraining({ onTrained }: { onTrained?: () => void }) {
  const [archs, setArchs] = useState<MlArchitecture[]>([])
  const [stats, setStats] = useState<MlDatasetStats | null>(null)
  const [arch, setArch] = useState("mlp")
  const [hp, setHp] = useState<Record<string, number>>({})
  const [name, setName] = useState("")
  const [notes, setNotes] = useState("")
  const [autoPromote, setAutoPromote] = useState(false)
  const [jobs, setJobs] = useState<MlJob[]>([])
  const [active, setActive] = useState<MlJob | null>(null)
  const [flash, setFlash] = useState<FlashT>(null)
  const [starting, setStarting] = useState(false)
  const [expanded, setExpanded] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const notifiedRef = useRef<Set<string>>(new Set())

  const spec = useMemo(() => archs.find((a) => a.id === arch), [archs, arch])

  const loadJobs = useCallback(async () => {
    const r = await api.ml.jobs()
    setJobs(r.jobs)
    setActive(r.active)
    // notifikasi saat job selesai
    r.jobs.forEach((j) => {
      if ((j.status === "done" || j.status === "failed") && !notifiedRef.current.has(j.id)) {
        notifiedRef.current.add(j.id)
        if (j.finished_at && Date.now() / 1000 - j.finished_at < 30) {
          setFlash({ kind: j.status === "done" ? "ok" : "err", text: j.message })
          if (j.status === "done") { onTrained?.(); api.ml.datasetStats().then(setStats).catch(() => {}) }
        }
      }
    })
    return r
  }, [onTrained])

  useEffect(() => {
    Promise.all([api.ml.architectures(), api.ml.datasetStats(), loadJobs()])
      .then(([a, s]) => { setArchs(a.architectures); setStats(s) })
      .catch((e) => setFlash({ kind: "err", text: (e as Error).message }))
  }, [loadJobs])

  // reset hyperparams saat arsitektur berubah
  useEffect(() => {
    if (!spec) return
    const d: Record<string, number> = {}
    spec.hyperparams.forEach((h) => { d[h.key] = h.default })
    setHp(d)
  }, [spec])

  // polling saat ada job aktif
  useEffect(() => {
    const running = active && (active.status === "running" || active.status === "queued")
    if (running && !pollRef.current) {
      pollRef.current = setInterval(() => { loadJobs().catch(() => {}) }, 1000)
    }
    if (!running && pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
    return () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null } }
  }, [active, loadJobs])

  const start = async () => {
    setStarting(true)
    try {
      const j = await api.ml.train({ arch, hyperparams: hp, name, notes, auto_promote: autoPromote })
      setFlash({ kind: "ok", text: `Job ${j.id} dimulai: ${j.arch_name}.` })
      await loadJobs()
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    } finally {
      setStarting(false)
    }
  }

  const cancel = async (id: string) => {
    try { await api.ml.cancelJob(id); await loadJobs() } catch (e) { setFlash({ kind: "err", text: (e as Error).message }) }
  }

  const ready = stats && stats.labeled >= 2 * Math.max(2, stats.n_classes) && stats.classes_without_data.length === 0
  const isRunning = !!active && (active.status === "running" || active.status === "queued")
  const estSeconds = useMemo(() => {
    if (!stats) return 0
    const n = stats.per_split.train || stats.labeled * 0.7
    const ep = hp.epochs ?? 1
    const perSample: Record<string, number> = { template: 0.002, centroid: 0.00002, knn: 0.00002, logreg: 0.00002, mlp: 0.00006, cnn: 0.0011 }
    return Math.max(1, n * ep * (perSample[arch] ?? 0.0001) + 1)
  }, [stats, hp, arch])

  return (
    <div className="space-y-4">
      {flash && <Flash kind={flash.kind} text={flash.text} onDone={() => setFlash(null)} />}

      {/* Prasyarat dataset */}
      {stats && (
        <div className={`flex flex-wrap items-center gap-x-6 gap-y-2 rounded-2xl border px-5 py-3 text-sm ${ready ? "border-sage/40 bg-sage/10 text-deep-brown" : "border-saffron/40 bg-saffron/10 text-deep-brown"}`}>
          <span className="flex items-center gap-2 font-semibold">{ready ? <CheckCircle2 className="h-4 w-4 text-sage" /> : <Info className="h-4 w-4 text-saffron-dark" />}{ready ? "Dataset siap dilatih" : "Dataset belum siap"}</span>
          <span className="text-xs text-charcoal/60">{stats.labeled} berlabel · {stats.n_classes} kelas · train {stats.per_split.train} / val {stats.per_split.val} / test {stats.per_split.test}</span>
          {stats.classes_without_data.length > 0 && <span className="text-xs text-terracotta">Kelas tanpa data: {stats.classes_without_data.join(", ")}</span>}
          {!ready && stats.classes_without_data.length === 0 && <span className="text-xs text-charcoal/60">Butuh minimal {2 * Math.max(2, stats.n_classes)} sampel berlabel.</span>}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        {/* Pilih arsitektur */}
        <div className="rounded-3xl border border-sand bg-white shadow-soft">
          <div className="flex items-center gap-3 border-b border-sand px-6 py-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-ocean/10 text-ocean"><Brain className="h-5 w-5" /></div>
            <div>
              <h2 className="font-display text-lg font-bold text-deep-brown">Pilih Arsitektur</h2>
              <p className="text-xs text-charcoal/55">Semua model berjalan di CPU (NumPy) — tanpa GPU, tanpa dependensi berat.</p>
            </div>
          </div>
          <div className="grid gap-2 p-4 sm:grid-cols-2">
            {archs.map((a) => (
              <button key={a.id} onClick={() => setArch(a.id)} className={`rounded-2xl border p-4 text-left transition-all ${arch === a.id ? "border-deep-brown bg-deep-brown text-cream shadow-soft" : "border-sand bg-white hover:border-deep-brown/40"}`}>
                <div className="flex items-center justify-between">
                  <span className="font-display text-sm font-bold">{a.name}</span>
                  <span className={`text-[10px] font-semibold uppercase ${arch === a.id ? "text-cream/60" : "text-charcoal/40"}`}>{a.family}</span>
                </div>
                <p className={`mt-1 text-xs leading-relaxed ${arch === a.id ? "text-cream/80" : "text-charcoal/60"}`}>{a.description}</p>
                <div className={`mt-2 flex flex-wrap gap-1 text-[10px] ${arch === a.id ? "text-cream/70" : "text-charcoal/50"}`}>
                  {a.pros.map((p) => <span key={p} className={`rounded-full px-2 py-0.5 ${arch === a.id ? "bg-cream/10" : "bg-sage/10 text-sage"}`}>+ {p}</span>)}
                  {a.cons.map((p) => <span key={p} className={`rounded-full px-2 py-0.5 ${arch === a.id ? "bg-cream/10" : "bg-terracotta/10 text-terracotta"}`}>− {p}</span>)}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Hyperparameter + mulai */}
        <div className="space-y-4">
          <div className="rounded-3xl border border-sand bg-white shadow-soft">
            <div className="flex items-center gap-3 border-b border-sand px-6 py-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-saffron/15 text-saffron-dark"><Cpu className="h-5 w-5" /></div>
              <div>
                <h2 className="font-display text-lg font-bold text-deep-brown">Konfigurasi</h2>
                <p className="text-xs text-charcoal/55">{spec?.name ?? "—"}</p>
              </div>
            </div>
            <div className="space-y-3 p-5">
              <Field label="Nama model (opsional)"><TextInput value={name} onChange={(e) => setName(e.target.value)} placeholder={spec ? `${spec.name}` : ""} /></Field>
              {spec?.hyperparams.length ? (
                <div className="grid grid-cols-2 gap-3">
                  {spec.hyperparams.map((h) => (
                    <Field key={h.key} label={h.label} hint={`${h.min}–${h.max}`}>
                      <TextInput type="number" step={h.type === "float" ? "any" : 1} min={h.min} max={h.max} value={hp[h.key] ?? h.default} onChange={(e) => setHp({ ...hp, [h.key]: Number(e.target.value) })} />
                    </Field>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl bg-cream/60 px-3 py-2 text-xs text-charcoal/60">Arsitektur ini tidak memiliki hyperparameter yang perlu diatur.</div>
              )}
              <Field label="Catatan (opsional)"><TextInput value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="mis. percobaan lr lebih kecil" /></Field>
              <label className="flex items-center gap-2 text-sm text-charcoal/70"><input type="checkbox" checked={autoPromote} onChange={(e) => setAutoPromote(e.target.checked)} className="accent-saffron" /><Rocket className="h-4 w-4 text-saffron-dark" /> langsung jadikan model produksi bila selesai</label>
              <div className="text-[11px] text-charcoal/45">Perkiraan durasi ≈ {estSeconds < 60 ? `${Math.ceil(estSeconds)} dtk` : `${(estSeconds / 60).toFixed(1)} mnt`} (tergantung CPU server).</div>
              <button disabled={!ready || isRunning || starting} onClick={start} className={`${btnPrimary} w-full justify-center`}>
                {starting || isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                {isRunning ? "Job sedang berjalan…" : "Mulai Retraining"}
              </button>
            </div>
          </div>

          {/* Job aktif */}
          {active && (active.status === "running" || active.status === "queued") && (
            <div className="rounded-3xl border border-saffron/40 bg-saffron/5 p-5 shadow-soft">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm font-bold text-deep-brown"><Loader2 className="h-4 w-4 animate-spin text-saffron-dark" /> {active.arch_name}</span>
                <button onClick={() => cancel(active.id)} className={btnGhost}><Square className="h-3.5 w-3.5" /> Batalkan</button>
              </div>
              <Bar value={active.progress} tone="bg-saffron" className="mt-3" />
              <div className="mt-2 text-xs text-charcoal/60">{active.message}</div>
              {active.history.length >= 2 && <div className="mt-3"><TrainingCurve history={active.history} height={120} /></div>}
            </div>
          )}
        </div>
      </div>

      {/* Riwayat job */}
      <div className="rounded-3xl border border-sand bg-white shadow-soft">
        <div className="flex items-center gap-3 border-b border-sand px-6 py-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sand/70 text-deep-brown"><Clock className="h-5 w-5" /></div>
          <div>
            <h2 className="font-display text-lg font-bold text-deep-brown">Riwayat Pelatihan</h2>
            <p className="text-xs text-charcoal/55">Job pada sesi server ini (model yang selesai tersimpan permanen di tab Model).</p>
          </div>
        </div>
        {jobs.length === 0 ? (
          <div className="px-6 py-10 text-center text-sm text-charcoal/50">Belum ada job pelatihan.</div>
        ) : (
          <ul className="divide-y divide-sand">
            {jobs.map((j) => (
              <li key={j.id} className="px-6 py-3">
                <div className="flex flex-wrap items-center gap-3">
                  <StatusIcon status={j.status} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-deep-brown">
                      {j.name} <Pill>{j.arch}</Pill> {j.auto_promote && <Pill tone="saffron">auto-produksi</Pill>}
                    </div>
                    <div className="truncate text-xs text-charcoal/55">{j.message} · {fmtDate(j.created_at)}</div>
                  </div>
                  {j.metrics && <div className="hidden w-64 sm:block"><MetricsRow m={j.metrics} compact /></div>}
                  {(j.status === "running" || j.status === "queued") && <button onClick={() => cancel(j.id)} className={btnGhost}><Square className="h-3.5 w-3.5" /></button>}
                  <button onClick={() => setExpanded(expanded === j.id ? null : j.id)} className="text-charcoal/40 hover:text-deep-brown">{expanded === j.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}</button>
                </div>
                {expanded === j.id && (
                  <div className="mt-3 grid gap-4 rounded-2xl bg-cream/50 p-4 lg:grid-cols-2">
                    <div>
                      <div className="mb-2 text-xs font-bold uppercase tracking-wide text-charcoal/50">Kurva pelatihan</div>
                      <TrainingCurve history={j.history} />
                    </div>
                    <div className="space-y-2 text-xs text-charcoal/70">
                      <div><span className="font-semibold">Hyperparameter:</span> {Object.entries(j.hyperparams).map(([k, v]) => `${k}=${v}`).join(" · ") || "—"}</div>
                      <div><span className="font-semibold">Dataset:</span> {j.dataset.labeled} berlabel · {j.dataset.n_classes} kelas · train {j.dataset.per_split.train} / val {j.dataset.per_split.val} / test {j.dataset.per_split.test}</div>
                      {j.model_id && <div><span className="font-semibold">Model:</span> <code className="rounded bg-white px-1">{j.model_id}</code></div>}
                      {j.error && <div className="text-terracotta"><span className="font-semibold">Error:</span> {j.error}</div>}
                      {j.history.length > 0 && (
                        <div className="max-h-40 overflow-auto rounded-xl border border-sand bg-white">
                          <table className="w-full text-[11px]">
                            <thead><tr className="border-b border-sand text-left text-charcoal/50"><th className="px-2 py-1">Epoch</th><th className="px-2 py-1">Loss</th><th className="px-2 py-1">Train acc</th><th className="px-2 py-1">Val acc</th><th className="px-2 py-1">Detik</th></tr></thead>
                            <tbody>{j.history.map((h) => <tr key={h.epoch} className="border-b border-sand/50"><td className="px-2 py-1">{h.epoch}</td><td className="px-2 py-1">{h.loss?.toFixed(4) ?? "—"}</td><td className="px-2 py-1">{pct(h.train_acc)}</td><td className="px-2 py-1">{pct(h.val_acc)}</td><td className="px-2 py-1">{h.seconds ?? "—"}</td></tr>)}</tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function StatusIcon({ status }: { status: MlJob["status"] }) {
  if (status === "done") return <CheckCircle2 className="h-5 w-5 text-sage" />
  if (status === "failed") return <XCircle className="h-5 w-5 text-terracotta" />
  if (status === "cancelled") return <Square className="h-5 w-5 text-charcoal/40" />
  return <Loader2 className="h-5 w-5 animate-spin text-saffron-dark" />
}
