"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { api, MlClass, MlModelEntry, MlPrediction } from "@/lib/api"
import { Flash, Select } from "@/components/guru/ui"
import { HandwritingCanvas, HandwritingCanvasHandle } from "@/components/aksara/handwriting-canvas"
import { Bar, EmptyState, Pill, btnGhost, btnPrimary, btnSecondary, pct } from "@/components/admin/ml-ui"
import { FlaskConical, Eraser, Undo2, Loader2, Upload, Rocket, Scale, Save, CheckCircle2, XCircle, Sparkles } from "lucide-react"

type FlashT = { kind: "ok" | "err"; text: string } | null

export function TabExperiment({ refreshKey }: { refreshKey?: number }) {
  const ref = useRef<HandwritingCanvasHandle>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const [models, setModels] = useState<MlModelEntry[]>([])
  const [prodId, setProdId] = useState<string | null>(null)
  const [classes, setClasses] = useState<MlClass[]>([])
  const [modelId, setModelId] = useState<string>("")   // "" = produksi
  const [ghost, setGhost] = useState<string>("")
  const [image, setImage] = useState<string | null>(null)
  const [result, setResult] = useState<MlPrediction | null>(null)
  const [compare, setCompare] = useState<MlPrediction[] | null>(null)
  const [busy, setBusy] = useState<"predict" | "compare" | "save" | null>(null)
  const [flash, setFlash] = useState<FlashT>(null)
  const [log, setLog] = useState<{ ts: number; model: string; label: string; conf: number; target?: string; ok?: boolean }[]>([])

  const load = useCallback(async () => {
    try {
      const [m, c] = await Promise.all([api.ml.models(), api.ml.classes()])
      setModels(m.models)
      setProdId(m.production_model_id)
      setClasses(c.active)
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    }
  }, [])

  useEffect(() => { load() }, [load, refreshKey])

  const grabImage = (): string | null => {
    if (image) return image
    const c = ref.current?.getInkCanvas()
    if (!c || ref.current?.isEmpty()) return null
    return c.toDataURL("image/png")
  }

  const predict = async () => {
    const img = grabImage()
    if (!img) { setFlash({ kind: "err", text: "Tulis satu aksara di kanvas atau unggah gambar dulu." }); return }
    setBusy("predict")
    setCompare(null)
    try {
      const r = await api.ml.predict({ image: img, model_id: modelId || null, top_k: 5 })
      setResult(r)
      const target = ghost || undefined
      setLog((l) => [{ ts: Date.now(), model: r.model_name, label: r.label, conf: r.confidence, target, ok: target ? r.label === target : undefined }, ...l].slice(0, 30))
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    } finally {
      setBusy(null)
    }
  }

  const runCompare = async () => {
    const img = grabImage()
    if (!img) { setFlash({ kind: "err", text: "Tulis satu aksara di kanvas atau unggah gambar dulu." }); return }
    setBusy("compare")
    try {
      const r = await api.ml.compare(img, models.slice(0, 10).map((m) => m.id))
      setCompare(r.results)
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    } finally {
      setBusy(null)
    }
  }

  const saveToDataset = async (label: string) => {
    const img = grabImage()
    if (!img) return
    setBusy("save")
    try {
      const s = await api.ml.addSample({ image: img, label, source: image ? "upload" : "canvas", note: "dari halaman percobaan" })
      setFlash({ kind: "ok", text: `Disimpan ke dataset sebagai “${label}” (split ${s.split}). Latih ulang agar model belajar dari koreksi ini.` })
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    } finally {
      setBusy(null)
    }
  }

  const onFile = async (f: File | undefined) => {
    if (!f) return
    const url = await new Promise<string>((res) => { const r = new FileReader(); r.onload = () => res(String(r.result)); r.readAsDataURL(f) })
    setImage(url)
    setResult(null)
    setCompare(null)
  }

  const clearAll = () => { ref.current?.clear(); setImage(null); setResult(null); setCompare(null) }
  const accuracyLog = log.filter((l) => l.ok !== undefined)
  const hits = accuracyLog.filter((l) => l.ok).length

  return (
    <div className="space-y-4">
      {flash && <Flash kind={flash.kind} text={flash.text} onDone={() => setFlash(null)} />}

      {models.length === 0 ? (
        <EmptyState icon={FlaskConical} title="Belum ada model untuk dicoba" body="Latih minimal satu model di tab Training. Setelah itu Anda bisa menulis aksara di sini dan melihat prediksi model — termasuk membandingkan beberapa model sekaligus." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
          {/* Input */}
          <div className="rounded-3xl border border-sand bg-white shadow-soft">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-sand px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-saffron/15 text-saffron-dark"><FlaskConical className="h-5 w-5" /></div>
                <div>
                  <h2 className="font-display text-lg font-bold text-deep-brown">Percobaan Model</h2>
                  <p className="text-xs text-charcoal/55">Tulis aksara (atau unggah gambar) → jalankan pada model pilihan → koreksi & simpan ke dataset bila salah.</p>
                </div>
              </div>
            </div>
            <div className="grid gap-4 p-5 sm:grid-cols-[1fr_220px]">
              <div>
                {image ? (
                  <div className="relative overflow-hidden rounded-2xl border-2 border-dashed border-sand bg-white" style={{ aspectRatio: "480 / 300" }}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={image} alt="unggahan" className="h-full w-full object-contain" />
                    <span className="absolute left-3 top-3 rounded-full bg-deep-brown px-2 py-0.5 text-[10px] font-bold text-cream">GAMBAR UNGGAHAN</span>
                  </div>
                ) : (
                  <HandwritingCanvas ref={ref} ghost={ghost ? classes.find((c) => c.label === ghost)?.glyph ?? null : null} width={480} height={300} />
                )}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  {!image && <><button onClick={() => ref.current?.undo()} className={btnGhost}><Undo2 className="h-4 w-4" /> Undo</button></>}
                  <button onClick={clearAll} className={btnGhost}><Eraser className="h-4 w-4" /> Bersihkan</button>
                  <button onClick={() => fileRef.current?.click()} className={btnGhost}><Upload className="h-4 w-4" /> Unggah gambar</button>
                  <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={(e) => onFile(e.target.files?.[0])} />
                </div>
              </div>
              <div className="space-y-3">
                <label className="block text-xs font-semibold text-charcoal/70">Model yang diuji
                  <Select value={modelId} onChange={(e) => { setModelId(e.target.value); setResult(null) }} className="mt-1">
                    <option value="">{prodId ? "★ Model produksi" : "(belum ada model produksi)"}</option>
                    {models.map((m) => <option key={m.id} value={m.id}>{m.name} · {m.arch} · acc {pct(m.metrics.accuracy)}</option>)}
                  </Select>
                </label>
                <label className="block text-xs font-semibold text-charcoal/70">Target aksara (opsional, untuk menilai)
                  <Select value={ghost} onChange={(e) => setGhost(e.target.value)} className="mt-1">
                    <option value="">— bebas —</option>
                    {classes.map((c) => <option key={c.label} value={c.label}>{c.glyph} {c.name} ({c.label})</option>)}
                  </Select>
                </label>
                <button disabled={busy !== null || (!modelId && !prodId)} onClick={predict} className={`${btnPrimary} w-full justify-center`}>{busy === "predict" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />} Prediksi</button>
                <button disabled={busy !== null || models.length < 2} onClick={runCompare} className={`${btnSecondary} w-full justify-center`}>{busy === "compare" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Scale className="h-4 w-4" />} Bandingkan semua model</button>
                {accuracyLog.length > 0 && <div className="rounded-xl bg-cream/60 px-3 py-2 text-xs text-charcoal/65">Sesi ini: <b>{hits}/{accuracyLog.length}</b> tebakan benar ({pct(hits / accuracyLog.length, 0)}) pada percobaan bertarget.</div>}
              </div>
            </div>
          </div>

          {/* Hasil */}
          <div className="space-y-4">
            <div className="rounded-3xl border border-sand bg-white p-5 shadow-soft">
              <div className="mb-3 text-[11px] font-bold uppercase tracking-wide text-charcoal/50">Hasil prediksi</div>
              {!result ? (
                <div className="py-8 text-center text-sm text-charcoal/45">Belum ada prediksi.</div>
              ) : (
                <div>
                  <div className="flex items-center gap-4">
                    <div className={`flex h-20 w-20 items-center justify-center rounded-2xl font-bali text-5xl ${result.confident ? "bg-sage/15 text-deep-brown" : "bg-saffron/10 text-deep-brown"}`}>{result.glyph}</div>
                    <div className="min-w-0 flex-1">
                      <div className="font-display text-2xl font-bold text-deep-brown">{result.name} <span className="text-base font-normal text-charcoal/50">({result.latin})</span></div>
                      <div className="text-xs text-charcoal/55">label <code className="rounded bg-cream px-1">{result.label}</code> · confidence <b>{pct(result.confidence)}</b> · margin {pct(result.margin)}</div>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {result.confident ? <Pill tone="sage"><CheckCircle2 className="h-3 w-3" /> yakin</Pill> : <Pill tone="saffron">kurang yakin</Pill>}
                        <Pill>{result.arch}</Pill>{result.is_production && <Pill tone="sage"><Rocket className="h-3 w-3" /> produksi</Pill>}
                        {ghost && (result.label === ghost ? <Pill tone="sage">✓ sesuai target</Pill> : <Pill tone="terracotta"><XCircle className="h-3 w-3" /> target: {ghost}</Pill>)}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 space-y-1.5">
                    {result.top.map((t) => (
                      <div key={t.label} className="flex items-center gap-2 text-xs">
                        <span className="w-8 text-center font-bali text-lg text-deep-brown">{t.glyph}</span>
                        <span className="w-14 truncate font-semibold text-deep-brown">{t.label}</span>
                        <Bar value={t.probability} tone={t.label === result.label ? "bg-sage" : "bg-ocean/50"} className="flex-1" />
                        <span className="w-12 text-right text-charcoal/60">{pct(t.probability)}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex items-center gap-3 rounded-2xl bg-cream/60 p-3">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={result.preview} alt="fitur" className="h-16 w-16 rounded-lg border border-sand bg-white [image-rendering:pixelated]" />
                    <div className="text-[11px] text-charcoal/60">Ini yang “dilihat” model: fitur 28×28 setelah normalisasi (crop, skala, pusat massa). Bila potongan aneh, tulis lebih besar/di tengah.</div>
                  </div>
                  <div className="mt-4">
                    <div className="mb-1 text-[11px] font-bold uppercase tracking-wide text-charcoal/50">Koreksi & simpan ke dataset</div>
                    <SaveRow classes={classes} defaultLabel={ghost || result.label} busy={busy === "save"} onSave={saveToDataset} />
                  </div>
                </div>
              )}
            </div>

            {log.length > 0 && (
              <div className="rounded-3xl border border-sand bg-white p-5 shadow-soft">
                <div className="mb-2 text-[11px] font-bold uppercase tracking-wide text-charcoal/50">Log percobaan sesi ini</div>
                <ul className="max-h-48 space-y-1 overflow-auto text-xs">
                  {log.map((l) => (
                    <li key={l.ts} className="flex items-center justify-between gap-2 rounded-lg px-2 py-1 hover:bg-cream/50">
                      <span className="truncate text-charcoal/60">{l.model}</span>
                      <span className="font-semibold text-deep-brown">{l.label} <span className="font-normal text-charcoal/50">{pct(l.conf, 0)}</span></span>
                      {l.ok === undefined ? <span className="text-charcoal/30">—</span> : l.ok ? <CheckCircle2 className="h-3.5 w-3.5 text-sage" /> : <XCircle className="h-3.5 w-3.5 text-terracotta" />}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Perbandingan */}
      {compare && (
        <div className="rounded-3xl border border-sand bg-white shadow-soft">
          <div className="border-b border-sand px-6 py-4">
            <h2 className="font-display text-lg font-bold text-deep-brown">Perbandingan antar model</h2>
            <p className="text-xs text-charcoal/55">Input yang sama dijalankan pada {compare.length} model. {ghost && <>Target: <b>{ghost}</b>.</>}</p>
          </div>
          <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {compare.map((r, i) => {
              const m = models.find((x) => x.id === r.model_id)
              const ok = ghost ? r.label === ghost : undefined
              return (
                <div key={i} className={`rounded-2xl border p-3 ${ok === undefined ? "border-sand" : ok ? "border-sage/50 bg-sage/5" : "border-terracotta/40 bg-terracotta/5"}`}>
                  <div className="flex items-center justify-between">
                    <div className="min-w-0"><div className="truncate text-xs font-bold text-deep-brown">{m?.name ?? r.model_id}</div><div className="text-[10px] text-charcoal/50">{r.arch ?? "—"}{m && ` · acc ${pct(m.metrics.accuracy)}`}</div></div>
                    {r.is_production && <Rocket className="h-4 w-4 text-sage" />}
                  </div>
                  {r.error ? <div className="mt-2 text-xs text-terracotta">{r.error}</div> : (
                    <>
                      <div className="mt-2 flex items-center gap-2"><span className="font-bali text-3xl text-deep-brown">{r.glyph}</span><div><div className="text-sm font-bold text-deep-brown">{r.label}</div><div className="text-[10px] text-charcoal/55">{pct(r.confidence)} {r.confident ? "· yakin" : "· ragu"}</div></div></div>
                      <div className="mt-2 space-y-1">{r.top.slice(0, 3).map((t) => <div key={t.label} className="flex items-center gap-1 text-[10px]"><span className="w-8 truncate">{t.label}</span><Bar value={t.probability} tone="bg-ocean/50" className="flex-1" /><span className="w-8 text-right">{pct(t.probability, 0)}</span></div>)}</div>
                    </>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

function SaveRow({ classes, defaultLabel, busy, onSave }: { classes: MlClass[]; defaultLabel: string; busy: boolean; onSave: (l: string) => void }) {
  const [label, setLabel] = useState(defaultLabel)
  useEffect(() => setLabel(defaultLabel), [defaultLabel])
  return (
    <div className="flex items-center gap-2">
      <Select value={label} onChange={(e) => setLabel(e.target.value)} className="flex-1">
        {classes.map((c) => <option key={c.label} value={c.label}>{c.glyph} {c.name} ({c.label})</option>)}
      </Select>
      <button disabled={busy || !label} onClick={() => onSave(label)} className={btnSecondary}>{busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Simpan</button>
    </div>
  )
}
