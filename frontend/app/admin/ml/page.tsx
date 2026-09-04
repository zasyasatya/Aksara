"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { Suspense } from "react"
import { api, MlStatus, setSession } from "@/lib/api"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { TabDataset } from "./tab-dataset"
import { TabTraining } from "./tab-training"
import { TabModels } from "./tab-models"
import { TabExperiment } from "./tab-experiment"
import { MetricsRow, Pill } from "@/components/admin/ml-ui"
import { Brain, Database, Boxes, FlaskConical, Globe, KeyRound, Loader2, LogOut, Rocket, ArrowLeft, Cpu } from "lucide-react"

type TabKey = "dataset" | "training" | "models" | "experiment"

const TABS: { key: TabKey; label: string; icon: any; desc: string }[] = [
  { key: "dataset", label: "Dataset & Labeling", icon: Database, desc: "sampel, label, split" },
  { key: "training", label: "Training", icon: Cpu, desc: "arsitektur & retraining" },
  { key: "models", label: "Model & Evaluasi", icon: Boxes, desc: "metrik, produksi" },
  { key: "experiment", label: "Percobaan", icon: FlaskConical, desc: "uji & bandingkan" },
]

export default function AdminMlPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-24 text-charcoal/50"><Loader2 className="h-5 w-5 animate-spin" /></div>}>
      <AdminMlInner />
    </Suspense>
  )
}

function AdminMlInner() {
  const router = useRouter()
  const params = useSearchParams()
  const initial = (params.get("tab") as TabKey) || "dataset"
  const [tab, setTab] = useState<TabKey>(TABS.some((t) => t.key === initial) ? initial : "dataset")
  const [status, setStatus] = useState<MlStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const load = useCallback(async () => {
    setError(null)
    try {
      const s = await api.ml.status()
      setStatus(s)
      return s
    } catch (e) {
      setError((e as Error).message)
      return null
    }
  }, [])

  useEffect(() => {
    load().then((s) => { if (s && !s.is_admin) router.replace("/login?next=/admin/ml") })
  }, [load, router])

  const bump = useCallback(() => { setRefreshKey((k) => k + 1); load() }, [load])

  const switchTab = (k: TabKey) => {
    setTab(k)
    const sp = new URLSearchParams(params.toString())
    sp.set("tab", k)
    router.replace(`/admin/ml?${sp.toString()}`)
  }

  const handleLogout = () => {
    api.auth.logout().catch(() => {})
    setSession(null, null)
    router.replace("/login?next=/admin/ml")
  }

  const isAdmin = status?.is_admin ?? false
  const prod = status?.production_model

  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />
      <div className="container mx-auto max-w-7xl px-4 py-8 lg:px-8">
        <Link href="/admin" className="inline-flex items-center gap-1 text-xs font-semibold text-charcoal/50 hover:text-saffron-dark"><ArrowLeft className="h-3.5 w-3.5" /> Panel Admin</Link>
        <div className="mt-2 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-ocean to-deep-brown text-cream shadow-soft"><Brain className="h-7 w-7" /></div>
            <div>
              <h1 className="font-display text-2xl font-bold text-deep-brown lg:text-3xl">Model ML — Klasifikasi Aksara Bali</h1>
              <p className="text-sm text-charcoal/60">Kelola dataset tulisan tangan, latih ulang classifier, evaluasi, dan pilih model produksi.</p>
            </div>
          </div>
          {status && (
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center gap-1.5 rounded-full border px-4 py-1.5 text-xs font-bold uppercase tracking-wide ${status.mode === "dev" ? "border-sage/40 bg-sage/20 text-sage" : "border-saffron/40 bg-saffron/15 text-saffron-dark"}`}><Globe className="h-3.5 w-3.5" /> Mode {status.mode}</span>
              <button onClick={handleLogout} className="inline-flex items-center gap-2 rounded-full border border-sand bg-white px-4 py-1.5 text-xs font-semibold text-charcoal/70 shadow-soft hover:border-terracotta/50 hover:text-terracotta"><LogOut className="h-3.5 w-3.5" /> Keluar</button>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 flex items-start gap-3 rounded-2xl border border-terracotta/40 bg-terracotta/10 px-4 py-3 text-sm text-terracotta"><KeyRound className="mt-0.5 h-4 w-4 shrink-0" />{error}</div>
        )}

        {!status && !error && <div className="flex items-center justify-center gap-3 py-16 text-charcoal/50"><Loader2 className="h-5 w-5 animate-spin" /> Memuat…</div>}

        {isAdmin && status && (
          <>
            {/* Ringkasan */}
            <div className="mt-6 grid gap-3 md:grid-cols-[1fr_1fr_2fr]">
              <div className="rounded-2xl border border-sand bg-white p-4 shadow-soft">
                <div className="text-xs font-medium text-charcoal/50">Dataset</div>
                <div className="mt-1 font-display text-2xl font-bold text-deep-brown">{status.dataset.labeled.toLocaleString("id-ID")} <span className="text-sm font-normal text-charcoal/50">berlabel</span></div>
                <div className="mt-0.5 text-[11px] text-charcoal/45">{status.dataset.n_classes} kelas · {status.dataset.unlabeled} menunggu label · train {status.dataset.per_split.train} / val {status.dataset.per_split.val} / test {status.dataset.per_split.test}</div>
              </div>
              <div className="rounded-2xl border border-sand bg-white p-4 shadow-soft">
                <div className="text-xs font-medium text-charcoal/50">Model terlatih</div>
                <div className="mt-1 font-display text-2xl font-bold text-deep-brown">{status.models_total}</div>
                <div className="mt-0.5 text-[11px] text-charcoal/45">{status.active_job ? <span className="text-saffron-dark">● job berjalan: {status.active_job.message}</span> : "tidak ada job berjalan"}</div>
              </div>
              <div className={`rounded-2xl border p-4 shadow-soft ${prod ? "border-sage/50 bg-sage/10" : "border-sand bg-white"}`}>
                <div className="flex items-center justify-between">
                  <div className="text-xs font-medium text-charcoal/50">Model produksi</div>
                  {prod && <Pill tone="sage"><Rocket className="h-3 w-3" /> aktif</Pill>}
                </div>
                {prod ? (
                  <div className="mt-1 flex flex-wrap items-center gap-4">
                    <div><div className="font-display text-lg font-bold text-deep-brown">{prod.name}</div><div className="text-[11px] text-charcoal/50">{prod.arch_name} · {prod.n_classes} kelas</div></div>
                    <div className="min-w-[260px] flex-1"><MetricsRow m={prod.metrics} compact /></div>
                  </div>
                ) : (
                  <div className="mt-1 text-sm text-charcoal/60">Belum ada — latih model lalu tetapkan di tab <button onClick={() => switchTab("models")} className="font-semibold text-saffron-dark hover:underline">Model & Evaluasi</button>.</div>
                )}
              </div>
            </div>

            {/* Tab bar */}
            <div className="mt-6 flex flex-wrap items-center gap-2">
              {TABS.map((t) => {
                const Icon = t.icon
                const on = tab === t.key
                return (
                  <button key={t.key} onClick={() => switchTab(t.key)} className={`flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-sm font-semibold transition-all ${on ? "border-deep-brown bg-deep-brown text-cream shadow-soft" : "border-sand bg-white text-charcoal/70 hover:border-deep-brown/40"}`}>
                    <Icon className="h-4 w-4" />{t.label}
                    <span className={`hidden text-[10px] font-normal sm:inline ${on ? "text-cream/60" : "text-charcoal/40"}`}>{t.desc}</span>
                  </button>
                )
              })}
              <Link href="/docs/dataset-dan-model" className="ml-auto text-xs font-semibold text-charcoal/50 hover:text-saffron-dark">Dokumentasi Dataset & Model →</Link>
            </div>

            <div className="mt-5">
              {tab === "dataset" && <TabDataset />}
              {tab === "training" && <TabTraining onTrained={bump} />}
              {tab === "models" && <TabModels refreshKey={refreshKey} onChanged={bump} />}
              {tab === "experiment" && <TabExperiment refreshKey={refreshKey} />}
            </div>
          </>
        )}
      </div>
      <BottomNav />
    </div>
  )
}
