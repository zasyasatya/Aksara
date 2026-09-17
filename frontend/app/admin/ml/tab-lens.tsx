"use client"

/**
 * Tab **Lens & OCR** pada Panel Admin — mengurus halaman Lens (kamera):
 *
 * 1. kesiapan model per tugas (Aksara Bali / Latin) + pasang model bawaan repo;
 * 2. antrean **koreksi pengguna** (crop yang salah baca) → terima / tolak / ganti label,
 *    lalu latih ulang model dari data terkoreksi;
 * 3. parameter pipeline (praproses, segmentasi, decoding) yang jadi bawaan semua pengguna;
 * 4. uji mandiri pipeline (render teks known → OCR → CER) untuk memastikan perubahan
 *    konfigurasi tidak merusak pembacaan.
 */

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import {
  api, type MlTaskId, type OcrCorrection, type OcrScanOptions, type OcrSelftest, type OcrStatus,
} from "@/lib/api"
import { Pill, btnGhost, btnPrimary, fmtDate, pct } from "@/components/admin/ml-ui"
import {
  AlertTriangle, Boxes, Camera, Check, Cpu, Download, FlaskConical, Loader2, RefreshCw, ScanText,
  Send, Settings2, Trash2, X,
} from "lucide-react"

const TASK_LABEL: Record<MlTaskId, string> = { aksara: "Aksara Bali", latin: "Latin" }

type NumberField = { key: keyof OcrScanOptions; label: string; hint: string; step?: number; kind?: "bool" | "text" }

const FIELDS: NumberField[] = [
  { key: "script", label: "Skrip baku", hint: "auto | aksara | latin", kind: "text" },
  { key: "binarize", label: "Ambang batas", hint: "sauvola | otsu | fixed", kind: "text" },
  { key: "sauvola_window", label: "Jendela Sauvola", hint: "8–200 px", step: 1 },
  { key: "sauvola_k", label: "K Sauvola", hint: "0.02–0.4 (kepekaan kontras)", step: 0.01 },
  { key: "tta", label: "TTA", hint: "0 cepat · 2 baku · 4 presisi", step: 1 },
  { key: "top_k", label: "Kandidat per aksara", hint: "1–10", step: 1 },
  { key: "beam_width", label: "Lebar beam", hint: "1–64", step: 1 },
  { key: "max_glyphs", label: "Maksimum aksara", hint: "batas biaya per scan", step: 10 },
  { key: "min_height", label: "Tinggi baris minimum", hint: "px", step: 1 },
  { key: "min_area", label: "Luas komponen minimum", hint: "bercak lebih kecil dibuang", step: 1 },
  { key: "merge_gap_ratio", label: "Gabung komponen (× tinggi)", hint: "0–1 · penanda ↔ badan", step: 0.01 },
  { key: "word_gap_ratio", label: "Celah antar kata (× tinggi)", hint: "0.3–1.2", step: 0.01 },
  { key: "split_width_ratio", label: "Batas lebar aksara (× tinggi)", hint: "> ini dicoba dibelah", step: 0.01 },
  { key: "resplit_below", label: "Ambang belah (keyakinan)", hint: "0–1 · makin tinggi makin sering dibelah", step: 0.01 },
  { key: "target_line_height", label: "Tinggi baris target", hint: "upscale teks kecil ke sini", step: 1 },
  { key: "script_margin", label: "Margin pilih skrip", hint: "0–1 · keunggulan yang dibutuhkan model Latin", step: 0.01 },
  { key: "line_min_ink", label: "Kerapatan tinta baris", hint: "0–0.2 · buang pita kosong", step: 0.002 },
  { key: "use_language_model", label: "Model bahasa (kamus)", hint: "menyaring urutan mustahil", kind: "bool" },
  { key: "split_marks", label: "Pisahkan pangangge", hint: "ulu/suku/pepet dinilai terpisah", kind: "bool" },
  { key: "upscale_small", label: "Perbesar teks kecil", hint: "penting untuk foto jauh", kind: "bool" },
  { key: "deskew", label: "Koreksi kemiringan", hint: "rotasi otomatis", kind: "bool" },
]

export function TabLens({ task, onBumped, jobActive }: { task: MlTaskId; onBumped: () => void; jobActive: boolean }) {
  const [status, setStatus] = useState<OcrStatus | null>(null)
  const [cfg, setCfg] = useState<Record<string, any> | null>(null)
  const [form, setForm] = useState<Record<string, any>>({})
  const [queue, setQueue] = useState<{ samples: OcrCorrection[]; total: number; review: number } | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [msg, setMsg] = useState<{ tone: "ok" | "err"; text: string } | null>(null)
  const [selftest, setSelftest] = useState<OcrSelftest | null>(null)
  const [testSize, setTestSize] = useState(48)

  const load = useCallback(async () => {
    setBusy("load")
    try {
      const [st, cf, q] = await Promise.all([api.ocr.status(), api.ocr.config(), api.ocr.pending(task, 40, 0)])
      setStatus(st)
      setCfg(cf)
      setForm({ ...(cf.default_options || {}) })
      setQueue(q)
    } catch (e) {
      setMsg({ tone: "err", text: (e as Error).message })
    } finally {
      setBusy(null)
    }
  }, [task])

  useEffect(() => { load() }, [load])

  const run = useCallback(async (key: string, fn: () => Promise<unknown>, text?: string) => {
    setBusy(key)
    setMsg(null)
    try {
      const r = await fn()
      setMsg({ tone: "ok", text: text || (typeof r === "object" && r && "message" in r ? String((r as any).message) : "Selesai.") })
      await load()
      onBumped()
      return r
    } catch (e) {
      setMsg({ tone: "err", text: (e as Error).message.replace(/^API Error \d+: /, "") })
      return null
    } finally {
      setBusy(null)
    }
  }, [load, onBumped])

  const saveConfig = () => run("save", () => api.ocr.setConfig({ default_options: form as OcrScanOptions }),
    "Bawaan pipeline Lens tersimpan — langsung dipakai semua scan berikutnya.")

  const decide = (s: OcrCorrection, action: "accept" | "reject" | "relabel", label?: string) =>
    run(`decide-${s.id}`, () => api.ocr.decide(s.id, s.task ?? task, { action, label }),
      action === "reject" ? "Koreksi ditolak dan sampel dihapus." : "Keputusan tersimpan.")

  const taskInfo = status?.tasks?.[task]
  const otherInfo = status?.tasks?.[task === "aksara" ? "latin" : "aksara"]

  return (
    <div className="space-y-5">
      {msg && (
        <div className={`flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-sm ${msg.tone === "ok" ? "border-sage/50 bg-sage/10 text-sage" : "border-terracotta/40 bg-terracotta/10 text-terracotta"}`}>
          {msg.tone === "ok" ? <Check className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
          <span className="flex-1">{msg.text}</span>
          <button onClick={() => setMsg(null)}><X className="h-4 w-4 opacity-60" /></button>
        </div>
      )}

      {/* ── 1. kesiapan model ── */}
      <section className="grid gap-3 lg:grid-cols-2">
        {[task, task === "aksara" ? "latin" : "aksara"].map((t) => {
          const info = (t === task ? taskInfo : otherInfo) ?? null
          const active = t === task
          return (
            <div key={t} className={`rounded-2xl border p-4 shadow-soft ${active ? "border-deep-brown/30 bg-white" : "border-sand bg-white/60"}`}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <ScanText className={`h-4 w-4 ${active ? "text-saffron" : "text-charcoal/40"}`} />
                  <h3 className="font-display text-base font-bold text-deep-brown">Tugas {TASK_LABEL[t as MlTaskId]}</h3>
                  {info?.ready ? <Pill tone="sage">siap</Pill> : <Pill tone="terracotta">belum ada model</Pill>}
                  {!active && <span className="text-[11px] text-charcoal/40">(baca tab ini untuk mengelolanya)</span>}
                </div>
                {info?.model_id && <span className="font-mono text-[11px] text-charcoal/40">{info.model_id}</span>}
              </div>
              <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-4">
                <Metric label="Akurasi test" value={info?.accuracy != null ? pct(info.accuracy) : "—"} />
                <Metric label="Tulisan tangan nyata" value={info?.real_handwriting_accuracy != null ? pct(info.real_handwriting_accuracy) : "—"} />
                <Metric label="Kelas aktif" value={String(info?.n_classes ?? "—")} />
                <Metric label="Sampel dataset" value={String(info?.dataset?.labeled ?? "—")} />
              </dl>
              <p className="mt-2 text-[11px] text-charcoal/45">
                {info?.name ? `${info.name} · ${info.arch ?? "?"} · dibuat ${fmtDate(info.created_at)}` :
                  "Model produksi belum ditetapkan untuk tugas ini."}
              </p>
              {active && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <button onClick={() => run("install", () => api.ocr.installBundled(true), "Model bawaan repo dipasang dan ditetapkan sebagai produksi.")}
                    className={btnGhost} disabled={busy === "install"}>
                    {busy === "install" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />} Pasang model bawaan
                  </button>
                  <button onClick={() => run("retrain", () => api.ocr.train({ task, arch: "deepcnn", auto_approve: true }),
                    "Job training dimulai memakai dataset + koreksi Lens (muncul di tab Training).")}
                    className={btnPrimary} disabled={busy === "retrain" || jobActive}>
                    {busy === "retrain" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Cpu className="h-3.5 w-3.5" />} Latih ulang dari data + koreksi
                  </button>
                  <Link href="/lens" className={btnGhost}><Camera className="h-3.5 w-3.5" /> Buka halaman Lens</Link>
                </div>
              )}
            </div>
          )
        })}
      </section>

      {/* ── 2. antrean koreksi ── */}
      <section className="rounded-2xl border border-sand bg-white p-4 shadow-soft">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <h3 className="flex items-center gap-2 font-display text-base font-bold text-deep-brown"><Send className="h-4 w-4 text-saffron" /> Koreksi dari halaman Lens</h3>
          {queue && <Pill tone={queue.review ? "saffron" : "sage"}>{queue.review} menunggu tinjau · {queue.total} total</Pill>}
          <div className="ml-auto flex items-center gap-2">
            <button onClick={() => run("refresh-q", () => api.ocr.pending(task, 40, 0).then(setQueue), "Antrean disegarkan.")} className={btnGhost} disabled={busy === "refresh-q"}>
              <RefreshCw className={`h-3.5 w-3.5 ${busy === "refresh-q" ? "animate-spin" : ""}`} /> Muat ulang
            </button>
            <Link href="/admin/ml?tab=dataset" className="text-xs font-semibold text-charcoal/50 hover:text-saffron-dark">Labeling penuh →</Link>
          </div>
        </div>
        <p className="mb-3 text-xs text-charcoal/50">
          Crop yang dikirim pengguna otomatis masuk dataset dengan sumber <code className="rounded bg-cream px-1">camera</code> dan status
          <code className="rounded bg-cream px-1">review</code>. “Terima” memindahkannya ke <code className="rounded bg-cream px-1">labeled</code> sehingga ikut training berikutnya.
        </p>
        {!queue?.samples.length ? (
          <p className="py-6 text-center text-sm text-charcoal/45">Belum ada koreksi untuk tugas {TASK_LABEL[task]}.</p>
        ) : (
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {queue.samples.map((s) => (
              <li key={s.id} className="rounded-2xl border border-sand p-3">
                <div className="flex items-start gap-3">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={api.ocr.correctionImageUrl(s.id, s.task ?? task)} alt={s.label ?? "tanpa label"}
                    className="h-16 w-16 shrink-0 rounded-xl border border-sand bg-cream object-contain" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5 text-[11px]">
                      <Pill tone={s.status === "review" ? "saffron" : "sage"}>{s.status}</Pill>
                      <span className="truncate text-charcoal/50">{fmtDate(s.created_at)}</span>
                    </div>
                    <p className="mt-1 truncate text-sm text-charcoal/70">{s.note || "tanpa catatan"}</p>
                    <p className="text-[11px] text-charcoal/45">label: <span className="font-mono">{s.label ?? "—"}</span> · split {s.split}</p>
                  </div>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  <button onClick={() => decide(s, "accept")} className="rounded-full bg-sage px-2.5 py-1 text-[11px] font-semibold text-cream hover:opacity-90"><Check className="mr-1 inline h-3 w-3" />Terima</button>
                  <select
                    value=""
                    onChange={(e) => e.target.value && decide(s, "relabel", e.target.value)}
                    className="rounded-full border border-sand bg-white px-2 py-1 text-[11px] font-semibold text-charcoal/70">
                    <option value="">Ganti label…</option>
                    {(taskInfo?.classes ?? []).map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                  <button onClick={() => decide(s, "reject")} className="rounded-full border border-sand px-2.5 py-1 text-[11px] font-semibold text-terracotta hover:bg-terracotta/10">
                    <Trash2 className="mr-1 inline h-3 w-3" />Tolak
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* ── 3. parameter pipeline ── */}
      <section className="rounded-2xl border border-sand bg-white p-4 shadow-soft">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <h3 className="flex items-center gap-2 font-display text-base font-bold text-deep-brown"><Settings2 className="h-4 w-4 text-saffron" /> Parameter pipeline Lens</h3>
          <span className="text-[11px] text-charcoal/45">berlaku untuk semua pengguna (halaman Lens bisa menimpa per permintaan)</span>
          {busy === "save" && <Loader2 className="h-4 w-4 animate-spin text-charcoal/40" />}
          <button onClick={saveConfig} className={`${btnPrimary} ml-auto`} disabled={busy === "save"}>Simpan bawaan</button>
          <button onClick={() => { setForm({ ...(cfg?.default_options || {}) }); setMsg(null) }} className={btnGhost}>Kembalikan</button>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {FIELDS.map((f) => {
            const v = form[f.key as string]
            if (f.kind === "bool") {
              return (
                <label key={String(f.key)} className="flex items-center justify-between gap-2 rounded-xl border border-sand px-3 py-2 text-xs" title={f.hint}>
                  <span className="font-semibold text-charcoal/70">{f.label}</span>
                  <input type="checkbox" checked={v !== false} onChange={(e) => setForm({ ...form, [f.key as string]: e.target.checked })} className="h-4 w-4 accent-saffron" />
                </label>
              )
            }
            if (f.kind === "text") {
              return (
                <label key={String(f.key)} className="rounded-xl border border-sand px-3 py-2 text-xs" title={f.hint}>
                  <span className="block font-semibold text-charcoal/70">{f.label}</span>
                  <input value={String(v ?? "")} onChange={(e) => setForm({ ...form, [f.key as string]: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-sand bg-cream px-2 py-1 font-mono text-sm outline-none focus:border-saffron" />
                  <span className="text-[10px] text-charcoal/40">{f.hint}</span>
                </label>
              )
            }
            return (
              <label key={String(f.key)} className="rounded-xl border border-sand px-3 py-2 text-xs" title={f.hint}>
                <span className="block font-semibold text-charcoal/70">{f.label}</span>
                <input type="number" step={f.step ?? 1} value={typeof v === "number" ? v : 0}
                  onChange={(e) => setForm({ ...form, [f.key as string]: Number(e.target.value) })}
                  className="mt-1 w-full rounded-lg border border-sand bg-cream px-2 py-1 font-mono text-sm outline-none focus:border-saffron" />
                <span className="text-[10px] text-charcoal/40">{f.hint}</span>
              </label>
            )
          })}
        </div>
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <label className="flex items-center justify-between gap-2 rounded-xl border border-saffron/30 bg-saffron/5 px-3 py-2 text-xs">
            <span className="font-semibold text-charcoal/70">Terima koreksi dari pengunjung</span>
            <input type="checkbox" checked={cfg?.feedback?.enabled !== false}
              onChange={async (e) => { await run("fb", () => api.ocr.setConfig({ feedback: { enabled: e.target.checked } }), "Pengumpulan koreksi diperbarui.") }}
              className="h-4 w-4 accent-saffron" />
          </label>
          {(["scan_per_minute", "feedback_per_minute"] as const).map((k) => (
            <label key={k} className="rounded-xl border border-sand px-3 py-2 text-xs">
              <span className="block font-semibold text-charcoal/70">{k === "scan_per_minute" ? "Scan / menit / IP" : "Koreksi / menit / IP"}</span>
              <input type="number" min={0} value={cfg?.limits?.[k] ?? 0}
                onChange={async (e) => { await run(`lim-${k}`, () => api.ocr.setConfig({ limits: { [k]: Number(e.target.value) } }), "Batas pemakaian diperbarui.") }}
                className="mt-1 w-full rounded-lg border border-sand bg-cream px-2 py-1 font-mono text-sm outline-none focus:border-saffron" />
            </label>
          ))}
        </div>
      </section>

      {/* ── 4. uji mandiri ── */}
      <section className="rounded-2xl border border-sand bg-white p-4 shadow-soft">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <h3 className="flex items-center gap-2 font-display text-base font-bold text-deep-brown"><FlaskConical className="h-4 w-4 text-saffron" /> Uji mandiri pipeline</h3>
          <span className="text-[11px] text-charcoal/45">teks known dirender di server → di-OCR → dibandingkan (tanpa dataset)</span>
          <label className="ml-auto flex items-center gap-2 text-xs font-semibold text-charcoal/60">
            ukuran huruf
            <select value={testSize} onChange={(e) => setTestSize(Number(e.target.value))} className="rounded-lg border border-sand bg-white px-2 py-1">
              {[32, 48, 64, 96].map((n) => <option key={n} value={n}>{n}px</option>)}
            </select>
          </label>
          <button onClick={() => run("test", async () => setSelftest(await api.ocr.selftest(task, testSize)), "Uji mandiri selesai.")}
            className={btnPrimary} disabled={busy === "test"}>
            {busy === "test" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Boxes className="h-3.5 w-3.5" />} Jalankan untuk {TASK_LABEL[task]}
          </button>
        </div>
        {selftest ? (
          <>
            <div className="mb-2 flex flex-wrap gap-2 text-xs">
              <Pill tone="sage">exact baris {pct(selftest.exact_line_rate)}</Pill>
              <Pill tone={selftest.cer < 0.2 ? "sage" : "saffron"}>CER {pct(selftest.cer)}</Pill>
              <Pill tone="sand">{selftest.samples} contoh · {selftest.elapsed_ms} ms</Pill>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-[11px] uppercase tracking-wider text-charcoal/45">
                  <tr><th className="py-1 pr-3">Rujukan</th><th className="py-1 pr-3">Hasil OCR</th><th className="py-1">CER</th></tr>
                </thead>
                <tbody>
                  {selftest.rows.map((r, i) => (
                    <tr key={i} className="border-t border-sand">
                      <td className="py-1.5 pr-3 font-mono text-charcoal/70">{r.reference}</td>
                      <td className={`py-1.5 pr-3 font-mono ${r.exact ? "text-sage" : "text-terracotta"}`}>{r.hypothesis}</td>
                      <td className="py-1.5">{pct(r.cer)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <p className="py-4 text-center text-sm text-charcoal/45">Jalankan untuk melihat apakah segmentasi & decoding masih benar setelah konfigurasi diubah.</p>
        )}
      </section>

      <p className="text-[11px] text-charcoal/45">
        Dataset dan model yang sama dipakai seluruh aplikasi — lihat <Link href="/docs/dataset-dan-model" className="font-semibold text-saffron-dark hover:underline">Dokumentasi → Dataset &amp; Model</Link>{" "}
        untuk sumber data, arsitektur, dan cara training ulang <code className="rounded bg-cream px-1">eval/train_ocr_models.py</code>.
      </p>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[11px] uppercase tracking-wider text-charcoal/45">{label}</dt>
      <dd className="font-display text-lg font-bold text-deep-brown">{value}</dd>
    </div>
  )
}
