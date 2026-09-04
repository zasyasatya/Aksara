"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { api, MlClass, MlDatasetStats, MlSample, MlSource, MlSplit } from "@/lib/api"
import { Field, TextInput, Select, Flash } from "@/components/guru/ui"
import { HandwritingCanvas, HandwritingCanvasHandle } from "@/components/aksara/handwriting-canvas"
import {
  Bar, EmptyState, Pill, SOURCE_LABEL, SPLIT_LABEL, STATUS_LABEL, btnDanger, btnGhost, btnPrimary, btnSecondary, fmtDate,
} from "@/components/admin/ml-ui"
import {
  Database, Sparkles, Upload, PenLine, Tag, Trash2, RefreshCw, Loader2, CheckCircle2, ChevronLeft, ChevronRight,
  Shuffle, Layers, X, Eraser, Undo2, Check, AlertTriangle, ListChecks,
} from "lucide-react"

type Flash = { kind: "ok" | "err"; text: string } | null
type Filters = { label: string; split: string; source: string; status: string; q: string }

const PAGE = 48

export function TabDataset() {
  const [stats, setStats] = useState<MlDatasetStats | null>(null)
  const [classes, setClasses] = useState<{ active: MlClass[]; available: MlClass[] } | null>(null)
  const [samples, setSamples] = useState<MlSample[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [filters, setFilters] = useState<Filters>({ label: "", split: "", source: "", status: "", q: "" })
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [flash, setFlash] = useState<Flash>(null)
  const [panel, setPanel] = useState<"none" | "synthetic" | "upload" | "canvas" | "classes">("none")
  const [detail, setDetail] = useState<MlSample | null>(null)

  const glyphOf = useMemo(() => {
    const m: Record<string, MlClass> = {}
    classes?.available.forEach((c) => { m[c.label] = c })
    return m
  }, [classes])

  const loadStats = useCallback(async () => {
    const [s, c] = await Promise.all([api.ml.datasetStats(), api.ml.classes()])
    setStats(s)
    setClasses(c)
  }, [])

  const loadSamples = useCallback(async (off = offset, f = filters) => {
    const r = await api.ml.listSamples({ ...f, limit: PAGE, offset: off })
    setSamples(r.samples)
    setTotal(r.total)
  }, [offset, filters])

  const refresh = useCallback(async () => {
    try {
      await Promise.all([loadStats(), loadSamples()])
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    } finally {
      setLoading(false)
    }
  }, [loadStats, loadSamples])

  useEffect(() => { refresh() }, [refresh])

  const applyFilters = (f: Partial<Filters>) => {
    const nf = { ...filters, ...f }
    setFilters(nf)
    setOffset(0)
    setSelected(new Set())
    loadSamples(0, nf).catch((e) => setFlash({ kind: "err", text: (e as Error).message }))
  }

  const goto = (off: number) => {
    setOffset(off)
    setSelected(new Set())
    loadSamples(off).catch((e) => setFlash({ kind: "err", text: (e as Error).message }))
  }

  const run = async (key: string, fn: () => Promise<string | void>) => {
    setBusy(key)
    try {
      const msg = await fn()
      if (msg) setFlash({ kind: "ok", text: msg })
      await refresh()
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    } finally {
      setBusy(null)
    }
  }

  const toggleSel = (id: string) => {
    const s = new Set(selected)
    s.has(id) ? s.delete(id) : s.add(id)
    setSelected(s)
  }

  const activeLabels = classes?.active ?? []

  return (
    <div className="space-y-4">
      {flash && <Flash kind={flash.kind} text={flash.text} onDone={() => setFlash(null)} />}

      {/* Statistik */}
      {stats && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Stat label="Total sampel" value={stats.total} hint={`versi dataset v${stats.version}`} />
          <Stat label="Berlabel" value={stats.labeled} hint={`${stats.n_classes} kelas aktif`} tone="text-sage" />
          <Stat label="Antrean labeling" value={stats.unlabeled} hint="belum berlabel" tone={stats.unlabeled ? "text-saffron-dark" : undefined} />
          <Stat label="Train / Val / Test" value={`${stats.per_split.train} / ${stats.per_split.val} / ${stats.per_split.test}`} hint="pembagian split" small />
          <Stat label="Min / maks per kelas" value={`${stats.min_per_class} / ${stats.max_per_class}`} hint={stats.classes_without_data.length ? `${stats.classes_without_data.length} kelas kosong` : "semua kelas terisi"} tone={stats.classes_without_data.length ? "text-terracotta" : undefined} small />
        </div>
      )}

      {/* Aksi utama */}
      <div className="rounded-3xl border border-sand bg-white shadow-soft">
        <div className="flex flex-col gap-3 border-b border-sand px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-ocean/10 text-ocean"><Database className="h-5 w-5" /></div>
            <div>
              <h2 className="font-display text-lg font-bold text-deep-brown">Manajemen Dataset</h2>
              <p className="text-xs text-charcoal/55">Kumpulkan sampel tulisan tangan per aksara: generate sintetis, unggah gambar, atau tulis langsung di kanvas.</p>
            </div>
          </div>
          <button onClick={() => refresh()} className="inline-flex items-center gap-1.5 text-xs font-semibold text-charcoal/50 hover:text-saffron-dark"><RefreshCw className="h-3.5 w-3.5" /> Muat ulang</button>
        </div>
        <div className="flex flex-wrap gap-2 px-6 py-4">
          <ActionBtn active={panel === "synthetic"} onClick={() => setPanel(panel === "synthetic" ? "none" : "synthetic")} icon={Sparkles} label="Generate sintetis" />
          <ActionBtn active={panel === "upload"} onClick={() => setPanel(panel === "upload" ? "none" : "upload")} icon={Upload} label="Unggah gambar" />
          <ActionBtn active={panel === "canvas"} onClick={() => setPanel(panel === "canvas" ? "none" : "canvas")} icon={PenLine} label="Tulis di kanvas" />
          <ActionBtn active={panel === "classes"} onClick={() => setPanel(panel === "classes" ? "none" : "classes")} icon={Layers} label={`Kelas aktif (${activeLabels.length})`} />
          <button
            disabled={busy !== null}
            onClick={() => run("rebalance", async () => (await api.ml.rebalance({ val_ratio: 0.15, test_ratio: 0.15, seed: Date.now() % 100000 })).message)}
            className={btnGhost}
          >
            {busy === "rebalance" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Shuffle className="h-4 w-4" />} Acak ulang split 70/15/15
          </button>
        </div>

        {panel === "synthetic" && <SyntheticPanel busy={busy === "synthetic"} nClasses={activeLabels.length} onRun={(b) => run("synthetic", async () => (await api.ml.generateSynthetic(b)).message)} onClose={() => setPanel("none")} />}
        {panel === "upload" && <UploadPanel classes={activeLabels} busy={busy === "upload"} onRun={(items) => run("upload", async () => { const r = await api.ml.addSamplesBulk(items); return `${r.added} gambar ditambahkan${r.skipped ? `, ${r.skipped} dilewati (kosong/tidak valid)` : ""}.` })} onClose={() => setPanel("none")} />}
        {panel === "canvas" && <CanvasPanel classes={activeLabels} busy={busy === "canvas"} onRun={(b) => run("canvas", async () => { const s = await api.ml.addSample(b); return s.label ? `Sampel “${s.label}” disimpan ke split ${SPLIT_LABEL[s.split]}.` : "Sampel masuk antrean labeling." })} onClose={() => setPanel("none")} />}
        {panel === "classes" && classes && <ClassesPanel classes={classes} stats={stats} busy={busy === "classes"} onSave={(labels) => run("classes", async () => (await api.ml.setClasses(labels)).message)} onClose={() => setPanel("none")} />}
      </div>

      {/* Distribusi per kelas */}
      {stats && classes && stats.labeled > 0 && (
        <div className="rounded-3xl border border-sand bg-white p-6 shadow-soft">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-display text-base font-bold text-deep-brown">Distribusi sampel per kelas</h3>
            <span className="text-xs text-charcoal/50">klik kelas untuk memfilter</span>
          </div>
          <div className="grid gap-x-6 gap-y-2 sm:grid-cols-2 lg:grid-cols-3">
            {activeLabels.map((c) => {
              const d = stats.per_label[c.label] ?? { train: 0, val: 0, test: 0, total: 0 }
              return (
                <button key={c.label} onClick={() => applyFilters({ label: filters.label === c.label ? "" : c.label })} className={`group rounded-xl px-2 py-1.5 text-left transition-colors hover:bg-cream ${filters.label === c.label ? "bg-saffron/10 ring-1 ring-saffron/40" : ""}`}>
                  <div className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-2 font-semibold text-deep-brown"><span className="font-bali text-lg">{c.glyph}</span>{c.name} <span className="text-charcoal/40">({c.label})</span></span>
                    <span className={`font-bold ${d.total === 0 ? "text-terracotta" : "text-charcoal/70"}`}>{d.total}</span>
                  </div>
                  <Bar value={stats.max_per_class ? d.total / stats.max_per_class : 0} tone={d.total === 0 ? "bg-terracotta" : "bg-ocean/70"} className="mt-1" />
                  <div className="mt-0.5 text-[10px] text-charcoal/45">train {d.train} · val {d.val} · test {d.test}</div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Galeri sampel + labeling */}
      <div className="rounded-3xl border border-sand bg-white shadow-soft">
        <div className="flex flex-col gap-3 border-b border-sand px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-saffron/15 text-saffron-dark"><Tag className="h-5 w-5" /></div>
            <div>
              <h2 className="font-display text-lg font-bold text-deep-brown">Sampel & Labeling</h2>
              <p className="text-xs text-charcoal/55">{total} sampel cocok · pilih beberapa lalu beri label / pindah split / hapus sekaligus.</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button onClick={() => applyFilters({ label: "__none__", status: "", split: "", source: "" })} className={`${btnGhost} ${filters.label === "__none__" ? "border-saffron text-saffron-dark" : ""}`}>
              <ListChecks className="h-4 w-4" /> Antrean labeling {stats?.unlabeled ? <span className="rounded-full bg-saffron px-1.5 text-[10px] text-cream">{stats.unlabeled}</span> : null}
            </button>
            <button onClick={() => applyFilters({ label: "", status: "review", split: "", source: "" })} className={`${btnGhost} ${filters.status === "review" ? "border-saffron text-saffron-dark" : ""}`}>
              <AlertTriangle className="h-4 w-4" /> Perlu tinjauan
            </button>
          </div>
        </div>

        {/* Filter */}
        <div className="grid gap-2 border-b border-sand bg-cream/40 px-6 py-3 sm:grid-cols-2 lg:grid-cols-5">
          <Select value={filters.label} onChange={(e) => applyFilters({ label: e.target.value })}>
            <option value="">Semua label</option>
            <option value="__none__">— tanpa label —</option>
            {activeLabels.map((c) => <option key={c.label} value={c.label}>{c.glyph} {c.name} ({c.label})</option>)}
          </Select>
          <Select value={filters.split} onChange={(e) => applyFilters({ split: e.target.value })}>
            <option value="">Semua split</option>
            {Object.entries(SPLIT_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </Select>
          <Select value={filters.source} onChange={(e) => applyFilters({ source: e.target.value })}>
            <option value="">Semua sumber</option>
            {Object.entries(SOURCE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </Select>
          <Select value={filters.status} onChange={(e) => applyFilters({ status: e.target.value })}>
            <option value="">Semua status</option>
            {Object.entries(STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </Select>
          <TextInput value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} onKeyDown={(e) => e.key === "Enter" && applyFilters({})} onBlur={() => applyFilters({})} placeholder="Cari catatan / id…" />
        </div>

        {/* Aksi massal */}
        {selected.size > 0 && (
          <BulkBar
            count={selected.size}
            classes={activeLabels}
            busy={busy === "bulk"}
            onClear={() => setSelected(new Set())}
            onSelectAll={() => setSelected(new Set(samples.map((s) => s.id)))}
            onLabel={(label) => run("bulk", async () => (await api.ml.bulkLabel({ ids: [...selected], label })).message).then(() => setSelected(new Set()))}
            onSplit={(split) => run("bulk", async () => (await api.ml.bulkLabel({ ids: [...selected], split })).message).then(() => setSelected(new Set()))}
            onReview={() => run("bulk", async () => (await api.ml.bulkLabel({ ids: [...selected], status: "review" })).message).then(() => setSelected(new Set()))}
            onDelete={() => run("bulk", async () => (await api.ml.bulkDelete([...selected])).message).then(() => setSelected(new Set()))}
          />
        )}

        {loading ? (
          <div className="flex items-center justify-center gap-3 py-16 text-charcoal/50"><Loader2 className="h-5 w-5 animate-spin" /> Memuat dataset…</div>
        ) : samples.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Database}
              title={total === 0 && stats?.total === 0 ? "Dataset masih kosong" : "Tidak ada sampel yang cocok"}
              body={stats?.total === 0 ? "Mulai dengan “Generate sintetis” untuk membuat ribuan sampel dari font Noto Sans Balinese dalam hitungan detik, lalu tambahkan tulisan tangan asli lewat unggah/kanvas." : "Ubah filter atau kosongkan pencarian."}
              action={stats?.total === 0 ? <button onClick={() => setPanel("synthetic")} className={btnPrimary}><Sparkles className="h-4 w-4" /> Generate sintetis</button> : undefined}
            />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-3 gap-2 p-4 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8">
              {samples.map((s) => (
                <SampleCard key={s.id} s={s} glyph={s.label ? glyphOf[s.label]?.glyph : undefined} selected={selected.has(s.id)} onToggle={() => toggleSel(s.id)} onOpen={() => setDetail(s)} />
              ))}
            </div>
            <div className="flex items-center justify-between border-t border-sand px-6 py-3 text-xs text-charcoal/55">
              <span>Menampilkan {offset + 1}–{Math.min(offset + PAGE, total)} dari {total}</span>
              <div className="flex items-center gap-2">
                <button disabled={offset === 0} onClick={() => goto(Math.max(0, offset - PAGE))} className={btnGhost}><ChevronLeft className="h-4 w-4" /></button>
                <button disabled={offset + PAGE >= total} onClick={() => goto(offset + PAGE)} className={btnGhost}><ChevronRight className="h-4 w-4" /></button>
              </div>
            </div>
          </>
        )}
      </div>

      {detail && (
        <SampleDetail
          sample={detail}
          classes={activeLabels}
          glyphOf={glyphOf}
          onClose={() => setDetail(null)}
          onSaved={(msg) => { setFlash({ kind: "ok", text: msg }); setDetail(null); refresh() }}
          onError={(msg) => setFlash({ kind: "err", text: msg })}
        />
      )}
    </div>
  )
}

// ── sub-komponen ──────────────────────────────────────────────────────────

function Stat({ label, value, hint, tone, small }: { label: string; value: number | string; hint?: string; tone?: string; small?: boolean }) {
  return (
    <div className="rounded-2xl border border-sand bg-white p-4 shadow-soft">
      <div className="text-xs font-medium text-charcoal/50">{label}</div>
      <div className={`mt-1 font-display font-bold text-deep-brown ${small ? "text-lg" : "text-2xl"} ${tone ?? ""}`}>{value}</div>
      {hint && <div className="mt-0.5 text-[11px] text-charcoal/45">{hint}</div>}
    </div>
  )
}

function ActionBtn({ active, onClick, icon: Icon, label }: { active: boolean; onClick: () => void; icon: any; label: string }) {
  return (
    <button onClick={onClick} className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition-all ${active ? "border-deep-brown bg-deep-brown text-cream shadow-soft" : "border-sand bg-white text-charcoal/70 hover:border-deep-brown/40"}`}>
      <Icon className="h-4 w-4" /> {label}
    </button>
  )
}

function PanelShell({ title, desc, onClose, children }: { title: string; desc: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="border-t border-sand bg-cream/40 px-6 py-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-base font-bold text-deep-brown">{title}</h3>
          <p className="text-xs text-charcoal/55">{desc}</p>
        </div>
        <button onClick={onClose} className="text-charcoal/40 hover:text-terracotta"><X className="h-5 w-5" /></button>
      </div>
      {children}
    </div>
  )
}

function SyntheticPanel({ busy, nClasses, onRun, onClose }: { busy: boolean; nClasses: number; onRun: (b: { per_class: number; seed: number; strength: number; replace_existing: boolean }) => void; onClose: () => void }) {
  const [perClass, setPerClass] = useState(60)
  const [seed, setSeed] = useState(20260904)
  const [strength, setStrength] = useState(1.0)
  const [replace, setReplace] = useState(false)
  return (
    <PanelShell title="Generate dataset sintetis" desc="Glyph dirender dari font Noto Sans Balinese (OFL) lalu diberi augmentasi ala tulisan tangan: variasi bobot, rotasi, skala, shear, distorsi elastis, ketebalan pena, dan noise. Split 70/15/15 diberikan otomatis." onClose={onClose}>
      <div className="grid gap-4 sm:grid-cols-4">
        <Field label="Sampel per kelas" hint={`total ≈ ${perClass * nClasses} sampel`}><TextInput type="number" min={1} max={400} value={perClass} onChange={(e) => setPerClass(Math.max(1, Math.min(400, Number(e.target.value) || 1)))} /></Field>
        <Field label="Seed" hint="ubah untuk variasi berbeda"><TextInput type="number" min={0} value={seed} onChange={(e) => setSeed(Math.max(0, Number(e.target.value) || 0))} /></Field>
        <Field label={`Kekuatan augmentasi: ${strength.toFixed(2)}`} hint="0 = glyph bersih · 1 = normal · 2 = ekstrem"><input type="range" min={0} max={2} step={0.05} value={strength} onChange={(e) => setStrength(Number(e.target.value))} className="w-full accent-saffron" /></Field>
        <Field label="Sampel sintetis lama"><label className="flex items-center gap-2 text-sm text-charcoal/70"><input type="checkbox" checked={replace} onChange={(e) => setReplace(e.target.checked)} className="accent-saffron" /> hapus dulu (ganti)</label></Field>
      </div>
      <div className="mt-4 flex justify-end">
        <button disabled={busy} onClick={() => onRun({ per_class: perClass, seed, strength, replace_existing: replace })} className={btnPrimary}>{busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />} Generate</button>
      </div>
    </PanelShell>
  )
}

function readFileAsDataUrl(f: File): Promise<string> {
  return new Promise((res, rej) => {
    const r = new FileReader()
    r.onload = () => res(String(r.result))
    r.onerror = () => rej(r.error)
    r.readAsDataURL(f)
  })
}

/** Tebak label dari nama file: "ha_01.png" → "ha", "na-3.jpg" → "na". */
function guessLabel(name: string, labels: string[]): string | undefined {
  const base = name.toLowerCase().replace(/\.[a-z0-9]+$/, "")
  const tokens = base.split(/[^a-z0-9]+/).filter(Boolean)
  const sorted = [...labels].sort((a, b) => b.length - a.length)
  for (const t of tokens) if (labels.includes(t)) return t
  for (const l of sorted) if (base.startsWith(l)) return l
  return undefined
}

function UploadPanel({ classes, busy, onRun, onClose }: { classes: MlClass[]; busy: boolean; onRun: (items: { image: string; label?: string | null; source: MlSource; split?: MlSplit; note?: string }[]) => void; onClose: () => void }) {
  const [files, setFiles] = useState<{ name: string; url: string; label: string }[]>([])
  const [defaultLabel, setDefaultLabel] = useState("")
  const [split, setSplit] = useState<"" | MlSplit>("")
  const inputRef = useRef<HTMLInputElement>(null)
  const labels = classes.map((c) => c.label)

  const pick = async (list: FileList | null) => {
    if (!list) return
    const arr = await Promise.all(Array.from(list).filter((f) => f.type.startsWith("image/")).slice(0, 200).map(async (f) => ({ name: f.name, url: await readFileAsDataUrl(f), label: guessLabel(f.name, labels) ?? defaultLabel })))
    setFiles((prev) => [...prev, ...arr])
  }

  return (
    <PanelShell title="Unggah gambar tulisan tangan" desc="PNG/JPG (foto atau scan, latar putih, tinta gelap). Label ditebak dari nama file (mis. ha_01.png → ha); sisanya pakai label default atau biarkan kosong → masuk antrean labeling." onClose={onClose}>
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files) }}
        onClick={() => inputRef.current?.click()}
        className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-sand bg-white px-6 py-8 text-center transition-colors hover:border-saffron/60"
      >
        <Upload className="h-6 w-6 text-charcoal/40" />
        <div className="mt-2 text-sm font-semibold text-deep-brown">Seret gambar ke sini atau klik untuk memilih</div>
        <div className="text-xs text-charcoal/50">maks 200 berkas per unggahan</div>
        <input ref={inputRef} type="file" accept="image/*" multiple className="hidden" onChange={(e) => pick(e.target.files)} />
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <Field label="Label default (bila tak tertebak)">
          <Select value={defaultLabel} onChange={(e) => { setDefaultLabel(e.target.value); setFiles((fs) => fs.map((f) => ({ ...f, label: f.label || e.target.value }))) }}>
            <option value="">— tanpa label (antrean) —</option>
            {classes.map((c) => <option key={c.label} value={c.label}>{c.glyph} {c.name} ({c.label})</option>)}
          </Select>
        </Field>
        <Field label="Split"><Select value={split} onChange={(e) => setSplit(e.target.value as any)}><option value="">otomatis (70/15/15)</option>{Object.entries(SPLIT_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</Select></Field>
        <div className="flex items-end justify-end gap-2">
          {files.length > 0 && <button onClick={() => setFiles([])} className={btnGhost}>Kosongkan</button>}
          <button disabled={busy || files.length === 0} onClick={() => onRun(files.map((f) => ({ image: f.url, label: f.label || null, source: "upload" as const, split: split || undefined, note: f.name })))} className={btnPrimary}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />} Unggah {files.length ? `(${files.length})` : ""}
          </button>
        </div>
      </div>
      {files.length > 0 && (
        <div className="mt-4 grid max-h-64 grid-cols-4 gap-2 overflow-auto sm:grid-cols-6 md:grid-cols-8">
          {files.map((f, i) => (
            <div key={i} className="rounded-xl border border-sand bg-white p-1.5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={f.url} alt={f.name} className="aspect-square w-full rounded-lg object-contain" />
              <select value={f.label} onChange={(e) => setFiles((fs) => fs.map((x, j) => (j === i ? { ...x, label: e.target.value } : x)))} className="mt-1 w-full rounded-md border border-sand bg-cream/50 px-1 py-0.5 text-[10px]">
                <option value="">(tanpa label)</option>
                {classes.map((c) => <option key={c.label} value={c.label}>{c.label}</option>)}
              </select>
            </div>
          ))}
        </div>
      )}
    </PanelShell>
  )
}

function CanvasPanel({ classes, busy, onRun, onClose }: { classes: MlClass[]; busy: boolean; onRun: (b: { image: string; label?: string | null; source: MlSource; split?: MlSplit; note?: string }) => void; onClose: () => void }) {
  const ref = useRef<HandwritingCanvasHandle>(null)
  const [label, setLabel] = useState(classes[0]?.label ?? "")
  const [split, setSplit] = useState<"" | MlSplit>("")
  const [ghost, setGhost] = useState(false)
  const [count, setCount] = useState(0)
  const cls = classes.find((c) => c.label === label)

  const save = () => {
    const c = ref.current?.getInkCanvas()
    if (!c || ref.current?.isEmpty()) return
    onRun({ image: c.toDataURL("image/png"), label: label || null, source: "canvas", split: split || undefined, note: "ditulis di panel admin" })
    ref.current?.clear()
    setCount((n) => n + 1)
  }

  return (
    <PanelShell title="Tulis sampel di kanvas" desc="Cara tercepat menambah data tulisan tangan asli: pilih aksara target, tulis, simpan — ulangi. Sampel langsung masuk dataset dengan label yang dipilih." onClose={onClose}>
      <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
        <div>
          <HandwritingCanvas ref={ref} ghost={ghost && cls ? cls.glyph : null} width={480} height={300} className="bg-white" />
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <button onClick={() => ref.current?.undo()} className={btnGhost}><Undo2 className="h-4 w-4" /> Undo</button>
            <button onClick={() => ref.current?.clear()} className={btnGhost}><Eraser className="h-4 w-4" /> Hapus</button>
            <label className="ml-auto flex items-center gap-2 text-xs text-charcoal/60"><input type="checkbox" checked={ghost} onChange={(e) => setGhost(e.target.checked)} className="accent-saffron" /> tampilkan siluet pemandu</label>
          </div>
        </div>
        <div className="space-y-3">
          <Field label="Label aksara">
            <Select value={label} onChange={(e) => setLabel(e.target.value)}>
              <option value="">— tanpa label (antrean) —</option>
              {classes.map((c) => <option key={c.label} value={c.label}>{c.glyph} {c.name} ({c.label})</option>)}
            </Select>
          </Field>
          {cls && <div className="flex items-center gap-3 rounded-2xl border border-sand bg-white p-3"><span className="font-bali text-5xl text-deep-brown">{cls.glyph}</span><div className="text-xs text-charcoal/60"><div className="font-semibold text-deep-brown">{cls.name}</div>latin: {cls.latin} · grup: {cls.group}</div></div>}
          <Field label="Split"><Select value={split} onChange={(e) => setSplit(e.target.value as any)}><option value="">otomatis</option>{Object.entries(SPLIT_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</Select></Field>
          <button disabled={busy} onClick={save} className={`${btnPrimary} w-full justify-center`}>{busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />} Simpan sampel</button>
          {count > 0 && <div className="text-center text-xs text-sage">{count} sampel tersimpan sesi ini</div>}
        </div>
      </div>
    </PanelShell>
  )
}

function ClassesPanel({ classes, stats, busy, onSave, onClose }: { classes: { active: MlClass[]; available: MlClass[] }; stats: MlDatasetStats | null; busy: boolean; onSave: (labels: string[]) => void; onClose: () => void }) {
  const [sel, setSel] = useState<Set<string>>(new Set(classes.active.map((c) => c.label)))
  const groups = useMemo(() => {
    const g: Record<string, MlClass[]> = {}
    classes.available.forEach((c) => { (g[c.group] ||= []).push(c) })
    return g
  }, [classes])
  const groupLabel: Record<string, string> = { wresastra: "Wresastra (18 aksara dasar)", swalalita: "Swalalita (Sanskerta/Kawi)", suara: "Aksara Suara (vokal independen)", angka: "Angka Bali" }
  const toggle = (l: string) => { const s = new Set(sel); s.has(l) ? s.delete(l) : s.add(l); setSel(s) }
  const toggleGroup = (items: MlClass[]) => {
    const all = items.every((c) => sel.has(c.label))
    const s = new Set(sel)
    items.forEach((c) => (all ? s.delete(c.label) : s.add(c.label)))
    setSel(s)
  }
  return (
    <PanelShell title="Kelas yang dilatih" desc="Tentukan aksara mana yang menjadi kelas classifier. Sampel dengan label di luar kelas aktif diabaikan saat training (tidak dihapus)." onClose={onClose}>
      <div className="space-y-4">
        {Object.entries(groups).map(([g, items]) => (
          <div key={g}>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wide text-charcoal/50">{groupLabel[g] ?? g}</span>
              <button onClick={() => toggleGroup(items)} className="text-xs font-semibold text-saffron-dark hover:underline">{items.every((c) => sel.has(c.label)) ? "lepas semua" : "pilih semua"}</button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {items.map((c) => {
                const on = sel.has(c.label)
                const n = stats?.per_label[c.label]?.total
                return (
                  <button key={c.label} onClick={() => toggle(c.label)} title={`${c.name} (${c.latin})`} className={`inline-flex items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-xs font-semibold transition-all ${on ? "border-deep-brown bg-deep-brown text-cream" : "border-sand bg-white text-charcoal/60 hover:border-deep-brown/40"}`}>
                    <span className="font-bali text-base">{c.glyph}</span>{c.label}{n !== undefined && on ? <span className="opacity-60">· {n}</span> : null}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center justify-between">
        <span className="text-xs text-charcoal/55">{sel.size} kelas dipilih (min. 2)</span>
        <button disabled={busy || sel.size < 2} onClick={() => onSave(classes.available.filter((c) => sel.has(c.label)).map((c) => c.label))} className={btnPrimary}>{busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />} Simpan kelas</button>
      </div>
    </PanelShell>
  )
}

function BulkBar({ count, classes, busy, onClear, onSelectAll, onLabel, onSplit, onReview, onDelete }: { count: number; classes: MlClass[]; busy: boolean; onClear: () => void; onSelectAll: () => void; onLabel: (l: string) => void; onSplit: (s: MlSplit) => void; onReview: () => void; onDelete: () => void }) {
  const [label, setLabel] = useState("")
  const [armed, setArmed] = useState(false)
  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-sand bg-deep-brown px-6 py-3 text-cream">
      <span className="text-sm font-semibold">{count} dipilih</span>
      <button onClick={onSelectAll} className="text-xs underline-offset-2 hover:underline">pilih semua di halaman</button>
      <button onClick={onClear} className="text-xs underline-offset-2 hover:underline">batal</button>
      <div className="mx-2 h-5 w-px bg-cream/20" />
      <select value={label} onChange={(e) => setLabel(e.target.value)} className="rounded-lg bg-cream/10 px-2 py-1 text-xs text-cream outline-none">
        <option value="" className="text-deep-brown">— label —</option>
        {classes.map((c) => <option key={c.label} value={c.label} className="text-deep-brown">{c.glyph} {c.name} ({c.label})</option>)}
      </select>
      <button disabled={!label || busy} onClick={() => onLabel(label)} className="rounded-full bg-saffron px-3 py-1 text-xs font-semibold text-cream disabled:opacity-40"><Tag className="mr-1 inline h-3 w-3" />Beri label</button>
      <div className="mx-2 h-5 w-px bg-cream/20" />
      {(["train", "val", "test"] as MlSplit[]).map((s) => <button key={s} disabled={busy} onClick={() => onSplit(s)} className="rounded-full border border-cream/30 px-3 py-1 text-xs font-semibold hover:bg-cream/10">→ {SPLIT_LABEL[s]}</button>)}
      <button disabled={busy} onClick={onReview} className="rounded-full border border-cream/30 px-3 py-1 text-xs font-semibold hover:bg-cream/10">Tandai tinjau</button>
      <div className="ml-auto">
        {armed ? (
          <span className="flex items-center gap-1"><button onClick={() => { setArmed(false); onDelete() }} className="rounded-full bg-terracotta px-3 py-1 text-xs font-semibold">Yakin hapus {count}?</button><button onClick={() => setArmed(false)} className="text-xs">batal</button></span>
        ) : (
          <button disabled={busy} onClick={() => setArmed(true)} className="rounded-full border border-terracotta/60 px-3 py-1 text-xs font-semibold text-terracotta hover:bg-terracotta/20"><Trash2 className="mr-1 inline h-3 w-3" />Hapus</button>
        )}
      </div>
    </div>
  )
}

function SampleCard({ s, glyph, selected, onToggle, onOpen }: { s: MlSample; glyph?: string; selected: boolean; onToggle: () => void; onOpen: () => void }) {
  const unl = !s.label
  return (
    <div className={`group relative rounded-xl border bg-white p-1.5 transition-all ${selected ? "border-saffron ring-2 ring-saffron/40" : unl ? "border-saffron/40" : "border-sand hover:border-deep-brown/40"}`}>
      <button onClick={onToggle} aria-label="pilih" className={`absolute left-2 top-2 z-10 flex h-5 w-5 items-center justify-center rounded-md border bg-white text-[10px] transition-opacity ${selected ? "border-saffron bg-saffron text-cream opacity-100" : "border-sand opacity-0 group-hover:opacity-100"}`}>{selected && <Check className="h-3 w-3" />}</button>
      <button onClick={onOpen} className="block w-full">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`${api.ml.sampleImageUrl(s.id)}?v=${s.updated_at}`} alt={s.label ?? "tanpa label"} className="aspect-square w-full rounded-lg object-contain [image-rendering:auto]" loading="lazy" />
      </button>
      <div className="mt-1 flex items-center justify-between px-0.5">
        <span className="flex items-center gap-1 text-[11px] font-semibold text-deep-brown">{glyph && <span className="font-bali text-sm">{glyph}</span>}{s.label ?? <span className="text-saffron-dark">tanpa label</span>}</span>
        <span className="text-[9px] uppercase text-charcoal/40">{s.split}</span>
      </div>
      {s.status === "review" && <span className="absolute right-1.5 top-1.5 rounded-full bg-amber-100 px-1.5 text-[9px] font-bold text-amber-800">tinjau</span>}
    </div>
  )
}

function SampleDetail({ sample, classes, glyphOf, onClose, onSaved, onError }: { sample: MlSample; classes: MlClass[]; glyphOf: Record<string, MlClass>; onClose: () => void; onSaved: (msg: string) => void; onError: (msg: string) => void }) {
  const [label, setLabel] = useState(sample.label ?? "")
  const [split, setSplit] = useState<MlSplit>(sample.split)
  const [status, setStatus] = useState(sample.status)
  const [note, setNote] = useState(sample.note ?? "")
  const [full, setFull] = useState<MlSample | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => { api.ml.getSample(sample.id).then(setFull).catch(() => {}) }, [sample.id])

  const save = async () => {
    setSaving(true)
    try {
      await api.ml.updateSample(sample.id, { label: label || undefined, clear_label: !label, split, status: label ? status : undefined, note })
      onSaved(label ? `Sampel diberi label “${label}”.` : "Label sampel dihapus (kembali ke antrean).")
    } catch (e) {
      onError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }
  const remove = async () => {
    try { await api.ml.deleteSample(sample.id); onSaved("Sampel dihapus.") } catch (e) { onError((e as Error).message) }
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center bg-deep-brown/40 p-4 backdrop-blur-sm sm:items-center" onClick={onClose}>
      <div className="w-full max-w-2xl rounded-3xl bg-white p-6 shadow-large" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-display text-lg font-bold text-deep-brown">Detail sampel</h3>
            <p className="text-xs text-charcoal/50">id {sample.id} · {SOURCE_LABEL[sample.source]} · dibuat {fmtDate(sample.created_at)}</p>
          </div>
          <button onClick={onClose} className="text-charcoal/40 hover:text-terracotta"><X className="h-5 w-5" /></button>
        </div>
        <div className="mt-4 grid gap-5 sm:grid-cols-[200px_1fr]">
          <div className="space-y-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={`${api.ml.sampleImageUrl(sample.id)}?v=${sample.updated_at}`} alt="sampel" className="aspect-square w-full rounded-2xl border border-sand object-contain" />
            <div className="flex items-center gap-2 text-[11px] text-charcoal/50">
              {full?.feature_preview && /* eslint-disable-next-line @next/next/no-img-element */ <img src={full.feature_preview} alt="fitur 28×28" className="h-14 w-14 rounded-lg border border-sand [image-rendering:pixelated]" />}
              <span>Fitur 28×28 yang dilihat model (crop bbox → skala → pusat massa).</span>
            </div>
            {sample.meta && Object.keys(sample.meta).length > 0 && <div className="rounded-xl bg-cream/60 p-2 text-[10px] text-charcoal/55">meta: {JSON.stringify(sample.meta)}</div>}
          </div>
          <div className="space-y-3">
            <Field label="Label">
              <Select value={label} onChange={(e) => setLabel(e.target.value)}>
                <option value="">— tanpa label —</option>
                {classes.map((c) => <option key={c.label} value={c.label}>{c.glyph} {c.name} ({c.label})</option>)}
              </Select>
            </Field>
            {label && glyphOf[label] && <div className="flex items-center gap-3 rounded-2xl border border-sand bg-cream/40 p-3"><span className="font-bali text-4xl text-deep-brown">{glyphOf[label].glyph}</span><div className="text-xs text-charcoal/60"><div className="font-semibold text-deep-brown">{glyphOf[label].name}</div>latin: {glyphOf[label].latin}</div></div>}
            <div className="grid grid-cols-2 gap-3">
              <Field label="Split"><Select value={split} onChange={(e) => setSplit(e.target.value as MlSplit)}>{Object.entries(SPLIT_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</Select></Field>
              <Field label="Status"><Select value={status} onChange={(e) => setStatus(e.target.value as any)} disabled={!label}><option value="labeled">Berlabel</option><option value="review">Perlu tinjauan</option></Select></Field>
            </div>
            <Field label="Catatan"><TextInput value={note} onChange={(e) => setNote(e.target.value)} placeholder="mis. tulisan murid kelas 4" /></Field>
            <div className="flex items-center justify-between pt-2">
              <button onClick={remove} className={btnDanger}><Trash2 className="h-4 w-4" /> Hapus</button>
              <button disabled={saving} onClick={save} className={btnSecondary}>{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />} Simpan</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
