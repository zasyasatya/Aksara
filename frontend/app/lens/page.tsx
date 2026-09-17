"use client"

/**
 * Lens Aksara — OCR kamera gaya Google Lens untuk Aksara Bali & Latin.
 *
 * Alur: kamera (getUserMedia) → bingkai bidik → tangkap frame → `POST /api/ocr/scan`
 * → overlay kotak per aksara + transliterasi + arti → koreksi manusia dikirim ke
 * antrean admin (`/api/ocr/feedback`) untuk retraining berikutnya.
 *
 * Laptop maupun ponsel memakai kode yang sama: bila `facingMode: environment`
 * tersedia (hp) kamera belakang yang dipakai, bila tidak (laptop) webcam standar.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import { api, type OcrLine, type OcrScanOptions, type OcrScanResult, type OcrStatus } from "@/lib/api"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { cn } from "@/lib/utils"
import {
  AlertTriangle, ArrowLeftRight, Camera, CameraOff, Check, Copy, Crop, Flashlight, Lightbulb,
  Loader2, Maximize2, Pause, Play, RotateCw, ScanLine, Send, Settings2, Share2, Sparkles,
  Upload, Wand2, X, Zap,
} from "lucide-react"

type Mode = "auto" | "aksara" | "latin"
type Status = "idle" | "starting" | "scanning" | "live" | "error"
type Region = "frame" | "full"

const MODE_LABEL: Record<Mode, string> = { auto: "Otomatis", aksara: "Aksara Bali", latin: "Latin" }
const REGION_LABEL: Record<Region, string> = { frame: "Dalam bingkai", full: "Seluruh layar" }
const CAPTURE_MS = 950

/**
 * Area baca (bidik) dalam satuan relatif ke kontainer pratinjau (0..1).
 * Bentuk pita lanskap: teks Bali/Latin hampir selalu baris horizontal, jadi
 * pita lebar-perpendek memberi resolusi paling tinggi per aksara dan — yang
 * paling penting — **membuang tulisan di luar bingkai** (meja, papan lain,
 * latar) yang dulu ikut terbaca karena seluruh frame kamera dikirim ke server.
 */
const SCAN_FRAME = { x: 0.035, y: 0.19, w: 0.93, h: 0.62 }
const FULL_FRAME = { x: 0, y: 0, w: 1, h: 1 }

type Rect = { x: number; y: number; w: number; h: number }
/** Geometri object-cover: skala & offset video terhadap kontainer. */
type Cover = { scale: number; ox: number; oy: number; cw: number; ch: number; vw: number; vh: number }
/** Persepsi sumber pada koordinat video (px) yang benar-benar dikirim ke OCR. */
type Source = { sx: number; sy: number; sw: number; sh: number; vw: number; vh: number }

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))

function coverOf(video: HTMLVideoElement, cw: number, ch: number): Cover | null {
  const vw = video.videoWidth
  const vh = video.videoHeight
  if (!vw || !vh || !cw || !ch) return null
  const scale = Math.max(cw / vw, ch / vh)
  return { scale, ox: (cw - vw * scale) / 2, oy: (ch - vh * scale) / 2, cw, ch, vw, vh }
}

/** Rect relatif kontainer → persegi sumber pada piksel video (sudah dipotong cover). */
function sourceOf(m: Cover, roi: Rect): Source {
  const x0 = (roi.x * m.cw - m.ox) / m.scale
  const y0 = (roi.y * m.ch - m.oy) / m.scale
  const x1 = ((roi.x + roi.w) * m.cw - m.ox) / m.scale
  const y1 = ((roi.y + roi.h) * m.ch - m.oy) / m.scale
  const sx = clamp(Math.min(x0, x1), 0, m.vw - 8)
  const sy = clamp(Math.min(y0, y1), 0, m.vh - 8)
  const sw = clamp(Math.abs(x1 - x0), 16, m.vw - sx)
  const sh = clamp(Math.abs(y1 - y0), 16, m.vh - sy)
  return { sx, sy, sw, sh, vw: m.vw, vh: m.vh }
}

/**
 * Tangkap HANYA area yang terlihat/dibingkai → data URL JPEG.
 * Mengembalikan juga `source` agar kotak hasil OCR dapat dipetakan balik ke
 * posisi yang sama persis di pratinjau (overlay tidak bergeser).
 */
function captureFromVideo(
  video: HTMLVideoElement,
  cw: number,
  ch: number,
  roi: Rect,
  maxSide = 1280,
): { url: string; source: Source } | null {
  const cover = coverOf(video, cw, ch)
  if (!cover) return null
  const src = sourceOf(cover, roi)
  const scale = Math.min(1, maxSide / Math.max(src.sw, src.sh))
  const canvas = document.createElement("canvas")
  canvas.width = Math.max(16, Math.round(src.sw * scale))
  canvas.height = Math.max(16, Math.round(src.sh * scale))
  const ctx = canvas.getContext("2d")
  if (!ctx) return null
  ctx.imageSmoothingQuality = "high"
  ctx.drawImage(video, src.sx, src.sy, src.sw, src.sh, 0, 0, canvas.width, canvas.height)
  return { url: canvas.toDataURL("image/jpeg", 0.92), source: src }
}

/** Rect hasil OCR (ternormalisasi pada citra yang dikirim) → persen kontainer. */
function rectToBox(rect: number[], src: Source | null, cover: Cover | null) {
  const [u, v, w, h] = rect
  if (!src || !cover) return { x: u * 100, y: v * 100, w: w * 100, h: h * 100 }
  const px = (sx: number, sy: number) => ({
    x: ((sx * cover.scale + cover.ox) / cover.cw) * 100,
    y: ((sy * cover.scale + cover.oy) / cover.ch) * 100,
  })
  const a = px(src.sx + u * src.sw, src.sy + v * src.sh)
  const b = px(src.sx + (u + w) * src.sw, src.sy + (v + h) * src.sh)
  return { x: a.x, y: a.y, w: Math.max(0.4, b.x - a.x), h: Math.max(0.4, b.y - a.y) }
}

/** Potong satu kotak (rect dinormalkan 0..1) → data URL PNG untuk sampel koreksi. */
function cropFromDataUrl(dataUrl: string, rect: number[], pad = 0.012): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const [x, y, w, h] = rect
      const p = pad
      const sx = Math.max(0, (x - p) * img.width)
      const sy = Math.max(0, (y - p) * img.height)
      const sw = Math.min(img.width - sx, (w + 2 * p) * img.width)
      const sh = Math.min(img.height - sy, (h + 2 * p) * img.height)
      const out = document.createElement("canvas")
      const side = Math.max(28, Math.round(Math.max(sw, sh) * 2))
      out.width = side
      out.height = side
      const ctx = out.getContext("2d")
      if (!ctx) return reject(new Error("canvas tidak tersedia"))
      ctx.fillStyle = "#fff"
      ctx.fillRect(0, 0, side, side)
      const scale = Math.min(side / sw, side / sh)
      ctx.drawImage(img, sx, sy, sw, sh, (side - sw * scale) / 2, (side - sh * scale) / 2, sw * scale, sh * scale)
      resolve(out.toDataURL("image/png"))
    }
    img.onerror = () => reject(new Error("gambar tidak dapat dipotong"))
    img.src = dataUrl
  })
}

function confTone(c: number) {
  if (c >= 0.8) return "text-sage"
  if (c >= 0.55) return "text-saffron"
  return "text-terracotta"
}

export default function LensPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const stageRef = useRef<HTMLDivElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const loopRef = useRef<number | null>(null)
  const busyRef = useRef(false)
  const fileRef = useRef<HTMLInputElement | null>(null)
  /** Sumber (piksel video) dari tangkapan terakhir → pemetaan overlay hasil. */
  const [capSrc, setCapSrc] = useState<Source | null>(null)

  const [status, setStatus] = useState<Status>("idle")
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<Mode>("auto")
  const [region, setRegion] = useState<Region>("frame")
  const [stage, setStage] = useState<{ cw: number; ch: number }>({ cw: 0, ch: 0 })
  const [coverTick, setCoverTick] = useState(0)
  const [portrait, setPortrait] = useState(false)
  const [precision, setPrecision] = useState(false)
  const [live, setLive] = useState(true)
  const [torch, setTorch] = useState(false)
  const [hasCamera, setHasCamera] = useState<boolean>(true)
  const [facing, setFacing] = useState<"environment" | "user">("environment")
  const [result, setResult] = useState<OcrScanResult | null>(null)
  const [frameUrl, setFrameUrl] = useState<string | null>(null)
  const [selected, setSelected] = useState<{ line: number; glyph: number } | null>(null)
  const [picked, setPicked] = useState<string | null>(null)
  const [note, setNote] = useState("")
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [ocrStatus, setOcrStatus] = useState<OcrStatus | null>(null)
  const [manualFrame, setManualFrame] = useState<string | null>(null)

  useEffect(() => {
    api.ocr.status().then(setOcrStatus).catch(() => setOcrStatus(null))
  }, [])

  const ready = !ocrStatus || (ocrStatus.tasks.aksara?.ready && ocrStatus.tasks.latin?.ready)

  const options = useMemo<OcrScanOptions>(() => ({
    script: mode,
    tta: precision ? 4 : 2,
    with_crops: false,
    ...(precision ? { close_iters: 1, max_glyphs: 700 } : {}),
  }), [mode, precision])

  // ── kamera ───────────────────────────────────────────────────────────────
  const stopCamera = useCallback(() => {
    if (loopRef.current) window.clearInterval(loopRef.current)
    loopRef.current = null
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    busyRef.current = false
  }, [])

  const startCamera = useCallback(async () => {
    setError(null)
    if (!navigator.mediaDevices?.getUserMedia) {
      setHasCamera(false)
      setStatus("error")
      setError("Peramban ini tidak mendukung akses kamera. Gunakan tombol Unggah Foto (atau buka lewat HTTPS).")
      return
    }
    setStatus("starting")
    try {
      // Sensor diminta LANSKAP (16:9). Pada ponsel, buffer portrait membuat
      // pratinjau menyempit dan tulisan di atas/bawah objek ikut terkirim ke
      // OCR; dengan rasio lanskap + area baca berbingkai, hanya tulisan yang
      // dibidik yang diproses.
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: facing },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
          aspectRatio: { ideal: 16 / 9 },
        },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => undefined)
      }
      const track = stream.getVideoTracks()[0]
      const caps: any = track?.getCapabilities?.() || {}
      const settings: any = track?.getSettings?.() || {}
      setTorch(Boolean(caps.torch))
      setHasCamera(true)
      setPortrait(
        Number(settings.height || videoRef.current?.videoHeight || 0) >
          Number(settings.width || videoRef.current?.videoWidth || 0),
      )
      setStatus("live")
    } catch (e) {
      setHasCamera(false)
      setStatus("error")
      const msg = (e as Error)?.name === "NotAllowedError"
        ? "Izin kamera ditolak. Aktinkan izin kamera untuk situs ini, lalu coba lagi."
        : `Kamera tidak dapat dibuka: ${(e as Error)?.message || e}. Gunakan Unggah Foto sebagai gantinya.`
      setError(msg)
    }
  }, [facing])

  useEffect(() => () => stopCamera(), [stopCamera])

  // Ukur kontainer pratinjau (dipakai pemetaan area baca & overlay hasil).
  useEffect(() => {
    const el = stageRef.current
    if (!el || typeof ResizeObserver === "undefined") return
    const ro = new ResizeObserver(() => {
      setStage({ cw: el.clientWidth, ch: el.clientHeight })
      setCoverTick((t) => t + 1)
    })
    ro.observe(el)
    setStage({ cw: el.clientWidth, ch: el.clientHeight })
    return () => ro.disconnect()
  }, [status])

  // Buffer video bisa berubah orientasi saat ponsel diputar.
  useEffect(() => {
    const v = videoRef.current
    if (!v) return
    const onResize = () => {
      setPortrait(v.videoHeight > v.videoWidth)
      setCoverTick((t) => t + 1)
    }
    v.addEventListener("resize", onResize)
    return () => v.removeEventListener("resize", onResize)
  }, [status])

  /** Kunci orientasi lanskap (Android Chrome; butuh mode layar penuh). */
  const goLandscape = useCallback(async () => {
    try {
      const el = document.documentElement as HTMLElement & { webkitRequestFullscreen?: () => Promise<void> }
      if (!document.fullscreenElement) {
        const req = el.requestFullscreen?.bind(el) || el.webkitRequestFullscreen?.bind(el)
        if (req) await req()
      }
      const ori = screen.orientation as ScreenOrientation & { lock?: (o: string) => Promise<void> }
      if (ori?.lock) await ori.lock("landscape")
      setPortrait(false)
    } catch {
      setError("Peramban ini tidak mengizinkan kunci orientasi. Putar ponsel Anda ke posisi lanskap (mendatar).")
    }
  }, [])

  // ── pemindaian ───────────────────────────────────────────────────────────
  const scanOnce = useCallback(async (dataUrl: string, source: Source | null) => {
    busyRef.current = true
    setCapSrc(source)
    setStatus((s) => (s === "live" ? "scanning" : s))
    try {
      const res = await api.ocr.scan(dataUrl, options, typeof window !== "undefined" && window.innerWidth < 1024 ? "lens-mobile" : "lens-desktop")
      setResult(res)
      setFrameUrl(dataUrl)
      setSelected(null)
      setPicked(null)
      setSent(null)
    } catch (e) {
      setError((e as Error).message.replace(/^API Error \d+: /, ""))
    } finally {
      busyRef.current = false
      setCoverTick((t) => t + 1)
      setStatus((s) => (s === "scanning" ? "live" : s))
    }
  }, [options])

  /** Tangkap area baca (bingkai / seluruh layar yang terlihat) lalu minta OCR. */
  const grabAndScan = useCallback(async () => {
    const v = videoRef.current
    const el = stageRef.current
    if (!v || v.readyState < 2 || !el) return
    const shot = captureFromVideo(v, el.clientWidth, el.clientHeight,
      region === "frame" ? SCAN_FRAME : FULL_FRAME)
    if (!shot) return
    setManualFrame(null)
    await scanOnce(shot.url, shot.source)
  }, [scanOnce, region])

  useEffect(() => {
    if (loopRef.current) window.clearInterval(loopRef.current)
    loopRef.current = null
    if (status !== "live" || !live) return
    const id = window.setInterval(() => {
      if (busyRef.current || document.hidden) return
      grabAndScan()
    }, CAPTURE_MS)
    loopRef.current = id
    return () => window.clearInterval(id)
  }, [status, live, grabAndScan])

  const toggleTorch = useCallback(async () => {
    const track = streamRef.current?.getVideoTracks()[0]
    if (!track) return
    const next = !torch
    try {
      await track.applyConstraints({ advanced: [{ torch: next } as any] })
      setTorch(next)
    } catch {
      setError("Lampu tidak dapat dikendalikan dari peramban ini.")
    }
  }, [torch])

  const onFile = useCallback(async (file: File | null | undefined) => {
    if (!file) return
    busyRef.current = true
    setError(null)
    try {
      const res = await api.ocr.scanFile(file, options)
      setCapSrc(null)                   // foto unggahan dipakai utuh (tanpa bingkai)
      setResult(res)
      setManualFrame(URL.createObjectURL(file))
      const dataUrl = await new Promise<string>((resolve, reject) => {
        const fr = new FileReader()
        fr.onload = () => resolve(String(fr.result))
        fr.onerror = () => reject(new Error("gagal membaca berkas"))
        fr.readAsDataURL(file)
      })
      setFrameUrl(dataUrl)
      setSelected(null)
      setPicked(null)
      setSent(null)
    } catch (e) {
      setError((e as Error).message.replace(/^API Error \d+: /, ""))
    } finally {
      busyRef.current = false
    }
  }, [options])

  // ── hasil ────────────────────────────────────────────────────────────────
  const lines = result?.lines ?? []
  const current = useMemo(() => {
    if (!selected || !result) return null
    const line = lines[selected.line]
    const glyph = line?.glyphs[selected.glyph]
    return line && glyph ? { line, glyph } : null
  }, [selected, result, lines])

  const pickedChar = picked ? (current?.glyph.alternatives.find((a) => a.label === picked)?.glyph || picked) : null

  /** Teks yang ditampilkan: hasil server, ditimpa lokal bila pengguna memilih kandidat. */
  const finalText = useMemo(() => {
    if (!result) return { aksara: "", latin: "" }
    let aksara = ""
    let latin = ""
    result.lines.forEach((line: OcrLine) => {
      const txt = line.glyphs.map((g) => {
        const isPicked = current?.glyph.index === g.index && current.line.index === line.index
        const base = isPicked && pickedChar ? pickedChar : g.glyph ?? ""
        const marks = line.script === "aksara" ? g.marks.map((m) => m.glyph).join("") : ""
        return (line.script === "latin" && g.word_break ? " " : "") + base + marks
      }).join("")
      if (line.script === "aksara") aksara += (aksara ? "\n" : "") + txt
      else latin += (latin ? " " : "") + txt
    })
    return { aksara: aksara || result.text.aksara, latin: latin || result.text.latin }
  }, [result, current, pickedChar])

  const translit = result?.translation?.bali_to_latin?.result || ""
  const toBali = result?.translation?.latin_to_bali?.result || ""
  const glossary = result?.glossary ?? []
  const displayLatin = translit || finalText.latin

  const sendCorrection = useCallback(async () => {
    if (!current || !frameUrl || !picked) return
    setSending(true)
    setError(null)
    try {
      const crop = await cropFromDataUrl(frameUrl, current.glyph.rect)
      const task = current.line.script === "latin" ? "latin" : "aksara"
      const res = await api.ocr.feedback({
        image: crop,
        task,
        label: picked,
        kind: "glyph",
        scan_id: result?.scan_id,
        note: note || `koreksi Lens: ${current.glyph.label} → ${picked}`,
        device: typeof navigator !== "undefined" ? navigator.userAgent.slice(0, 60) : undefined,
      })
      setSent(res.message || "Terkirim")
      setPicked(null)
      setNote("")
    } catch (e) {
      setError((e as Error).message.replace(/^API Error \d+: /, ""))
    } finally {
      setSending(false)
    }
  }, [current, frameUrl, picked, note, result?.scan_id])

  const copyText = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      const ta = document.createElement("textarea")
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand("copy")
      ta.remove()
    }
  }, [])

  const share = useCallback(async () => {
    const payload = [result?.text.aksara, translit, glossary.map((g) => `${g.word}: ${g.meaning ?? ""}`).filter(Boolean).join(", ")]
      .filter(Boolean)
      .join("\n")
    const nav = navigator as Navigator & { share?: (d: ShareData) => Promise<void> }
    if (nav.share) {
      try {
        await nav.share({ title: "Hasil baca Lens Aksara", text: payload })
        return
      } catch {
        /* dibatalkan pengguna */
      }
    }
    await copyText(payload)
  }, [result, translit, glossary, copyText])

  const running = status === "live" || status === "scanning"

  /** Geometri pratinjau: rect area baca (persen) + pemetaan object-cover. */
  const frame = region === "frame" ? SCAN_FRAME : FULL_FRAME
  const frameStyle = {
    left: `${frame.x * 100}%`, top: `${frame.y * 100}%`,
    width: `${frame.w * 100}%`, height: `${frame.h * 100}%`,
  }
  const cover = useMemo(() => {
    const v = videoRef.current
    if (!v || !stage.cw || !stage.ch) return null
    return coverOf(v, stage.cw, stage.ch)
    // coverTick: dihitung ulang tiap tangkapan/resize/orientasi berubah
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage, coverTick, running])

  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />
      <div className="container mx-auto max-w-7xl px-4 py-6 lg:px-8">
        <div className="mb-5 flex flex-wrap items-center gap-3">
          <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-sm font-medium text-charcoal/60 hover:text-deep-brown">
            <ArrowLeftRight className="h-4 w-4" /> Beranda
          </Link>
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-bold text-charcoal lg:text-3xl">
              <Sparkles className="h-6 w-6 text-saffron" /> Lens Aksara
            </h1>
            <p className="text-sm text-charcoal/60">
              Arahkan kamera ke tulisan Bali atau Latin — dibaca, ditransliterasi, dan diberi arti.
            </p>
          </div>
          {ocrStatus && !ready && (
            <span className="ml-auto inline-flex items-center gap-2 rounded-full bg-terracotta/10 px-3 py-1.5 text-xs font-semibold text-terracotta">
              <AlertTriangle className="h-3.5 w-3.5" /> Model OCR belum terpasang
            </span>
          )}
          {typeof ocrStatus?.corrections_pending === "number" && ocrStatus.corrections_pending > 0 && (
            <span className="ml-auto inline-flex items-center gap-2 rounded-full bg-sand px-3 py-1.5 text-xs font-semibold text-deep-brown/70">
              {ocrStatus.corrections_pending} koreksi menunggu admin
            </span>
          )}
        </div>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
          {/* ── pembidik ── */}
          <section className="overflow-hidden rounded-3xl border border-sand bg-deep-brown shadow-soft">
            {/* Panggung LANSKAP (16:9) — bukan portrait: pratinjau mengisi penuh
                (object-cover) dan hanya area di dalam bingkai yang dikirim ke OCR. */}
            <div ref={stageRef} className="relative aspect-video w-full overflow-hidden bg-charcoal">
              <video
                ref={videoRef}
                playsInline
                muted
                autoPlay
                className={cn("absolute inset-0 h-full w-full object-cover transition-opacity", running ? "opacity-100" : "opacity-0")}
              />
              {!running && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6 text-center">
                  {status === "starting" ? (
                    <Loader2 className="h-7 w-7 animate-spin text-cream/70" />
                  ) : manualFrame ? (
                    <img src={manualFrame} alt="Foto yang diunggah" className="max-h-full w-auto rounded-xl" />
                  ) : (
                    <>
                      {hasCamera ? <Camera className="h-9 w-9 text-cream/60" /> : <CameraOff className="h-9 w-9 text-cream/60" />}
                      <p className="max-w-sm text-sm text-cream/70">
                        {error || "Nyalakan kamera untuk mulai membaca, atau unggah foto tulisan."}
                      </p>
                    </>
                  )}
                </div>
              )}

              {/* ── area baca: HANYA bagian ini yang dikirim ke OCR ── */}
              {running && region === "frame" && (
                <div className="pointer-events-none absolute inset-0">
                  <div className="absolute inset-x-0 top-0 bg-charcoal/60" style={{ height: `${frame.y * 100}%` }} />
                  <div className="absolute inset-x-0 bottom-0 bg-charcoal/60"
                    style={{ height: `${Math.max(0, 1 - frame.y - frame.h) * 100}%` }} />
                  <div className="absolute bg-charcoal/60"
                    style={{ top: `${frame.y * 100}%`, height: `${frame.h * 100}%`, left: 0, width: `${frame.x * 100}%` }} />
                  <div className="absolute bg-charcoal/60"
                    style={{ top: `${frame.y * 100}%`, height: `${frame.h * 100}%`, right: 0,
                             width: `${Math.max(0, 1 - frame.x - frame.w) * 100}%` }} />
                </div>
              )}
              {running && (
                <div className="pointer-events-none absolute" style={frameStyle}>
                  <div className="relative h-full w-full overflow-hidden rounded-2xl border-2 border-cream/60">
                    {/* sudut tegas ala pemindai */}
                    {["left-0 top-0 border-l-2 border-t-2", "right-0 top-0 border-r-2 border-t-2",
                      "left-0 bottom-0 border-l-2 border-b-2", "right-0 bottom-0 border-r-2 border-b-2"].map((c) => (
                      <span key={c} className={cn("absolute h-5 w-5 border-saffron", c)} />
                    ))}
                    {!result && (
                      <div className="absolute inset-x-0 h-14 animate-[scan_2.6s_ease-in-out_infinite] bg-gradient-to-b from-saffron/0 via-saffron/25 to-saffron/0" />
                    )}
                  </div>
                  <span className="absolute -top-6 left-0 inline-flex items-center gap-1 rounded-full bg-charcoal/70 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-cream/80">
                    <ScanLine className="h-3 w-3" /> {REGION_LABEL[region]}
                  </span>
                </div>
              )}

              {/* overlay kotak hasil OCR — dipetakan balik ke posisi aslinya di pratinjau */}
              {running && result && (
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 h-full w-full">
                  {lines.map((ln, li) =>
                    ln.glyphs.map((g, gi) => {
                      const b = rectToBox(g.rect, capSrc, cover)
                      const active = selected?.line === li && selected?.glyph === gi
                      const low = (g.confidence ?? 1) < 0.55
                      return (
                        <g key={`${li}-${gi}`} onClick={() => setSelected({ line: li, glyph: gi })} className="cursor-pointer">
                          <rect
                            x={b.x} y={b.y} width={b.w} height={b.h}
                            fill={active ? "rgba(245,158,11,0.22)" : low ? "rgba(220,38,38,0.14)" : "transparent"}
                            stroke={active ? "#f59e0b" : low ? "#dc2626" : "#ffffff"}
                            strokeWidth={active ? 0.9 : 0.5}
                            vectorEffect="non-scaling-stroke"
                          />
                        </g>
                      )
                    }),
                  )}
                </svg>
              )}
              {status === "scanning" && (
                <div className="absolute inset-x-0 top-0 h-1 animate-pulse bg-saffron" />
              )}
              {running && portrait && (
                <button
                  onClick={goLandscape}
                  className="absolute inset-x-0 bottom-0 flex items-center justify-center gap-2 bg-terracotta/90 px-3 py-2 text-xs font-semibold text-cream"
                >
                  <RotateCw className="h-3.5 w-3.5" /> Kamera mengirim gambar portrait — ketuk untuk kunci lanskap
                </button>
              )}
            </div>

            {/* kontrol */}
            <div className="flex flex-wrap items-center gap-2 border-t border-cream/10 bg-deep-brown p-3">
              <div className="flex overflow-hidden rounded-full bg-charcoal/40 p-1">
                {(["auto", "aksara", "latin"] as Mode[]).map((m) => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    className={cn("rounded-full px-3 py-1.5 text-xs font-semibold transition-colors",
                      mode === m ? "bg-saffron text-cream" : "text-cream/70 hover:text-cream")}
                  >
                    {MODE_LABEL[m]}
                  </button>
                ))}
              </div>
              {/* Area baca: tulisan di luar bingkai tidak dikirim ke OCR */}
              <div className="flex overflow-hidden rounded-full bg-charcoal/40 p-1">
                {(["frame", "full"] as Region[]).map((r) => (
                  <button
                    key={r}
                    onClick={() => setRegion(r)}
                    title={r === "frame"
                      ? "Hanya tulisan di dalam bingkai yang dibaca"
                      : "Baca seluruh layar kamera"}
                    className={cn("inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors",
                      region === r ? "bg-sage text-cream" : "text-cream/70 hover:text-cream")}
                  >
                    {r === "frame" ? <Crop className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
                    {r === "frame" ? "Bingkai" : "Penuh"}
                  </button>
                ))}
              </div>
              {!running ? (
                <button onClick={startCamera} className="inline-flex items-center gap-2 rounded-full bg-saffron px-4 py-2 text-sm font-semibold text-cream hover:bg-saffron-dark">
                  <Play className="h-4 w-4" /> Nyalakan kamera
                </button>
              ) : (
                <>
                  <button
                    onClick={() => setLive((v) => !v)}
                    className="inline-flex items-center gap-2 rounded-full bg-charcoal/50 px-3 py-2 text-sm font-semibold text-cream hover:bg-charcoal"
                    title={live ? "Hentikan pemindaian otomatis" : "Pindai terus"}
                  >
                    {live ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />} {live ? "Jeda" : "Lanjut"}
                  </button>
                  <button onClick={grabAndScan} className="inline-flex items-center gap-2 rounded-full bg-cream px-3 py-2 text-sm font-semibold text-deep-brown hover:bg-white">
                    <Camera className="h-4 w-4" /> Baca sekarang
                  </button>
                </>
              )}
              {torch && running && (
                <button onClick={toggleTorch} className={cn("rounded-full p-2", "bg-charcoal/50 text-cream hover:bg-charcoal")}>
                  <Flashlight className="h-4 w-4" />
                </button>
              )}
              <button
                onClick={() => setPrecision((v) => !v)}
                title="Mode presisi: TTA 4× + penutup goresan (lebih lambat, lebih akurat)"
                className={cn("inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-semibold",
                  precision ? "bg-sage text-cream" : "bg-charcoal/50 text-cream/80 hover:bg-charcoal")}
              >
                <Zap className="h-4 w-4" /> Presisi
              </button>
              <button
                onClick={() => setFacing((f) => (f === "environment" ? "user" : "environment"))}
                className="inline-flex items-center gap-1.5 rounded-full bg-charcoal/50 px-3 py-2 text-sm font-semibold text-cream/80 hover:bg-charcoal"
                title="Ganti kamera (belakang/depan)"
              >
                <ArrowLeftRight className="h-4 w-4" /> {facing === "environment" ? "Belakang" : "Depan"}
              </button>
              <button
                onClick={goLandscape}
                className="inline-flex items-center gap-1.5 rounded-full bg-charcoal/50 px-3 py-2 text-sm font-semibold text-cream/80 hover:bg-charcoal"
                title="Kunci orientasi lanskap (layar penuh)"
              >
                <RotateCw className="h-4 w-4" /> Lanskap
              </button>
              <button onClick={() => fileRef.current?.click()} className="inline-flex items-center gap-1.5 rounded-full bg-charcoal/50 px-3 py-2 text-sm font-semibold text-cream/80 hover:bg-charcoal">
                <Upload className="h-4 w-4" /> Unggah foto
              </button>
              <button onClick={() => setShowSettings((v) => !v)} className="ml-auto rounded-full bg-charcoal/50 p-2 text-cream/80 hover:bg-charcoal" title="Parameter lanjutan">
                <Settings2 className="h-4 w-4" />
              </button>
              <input ref={fileRef} type="file" accept="image/*" capture="environment" className="hidden"
                onChange={(e) => onFile(e.target.files?.[0])} />
            </div>

                {showSettings && <AdvancedPanel status={ocrStatus} />}
          </section>

          {/* ── hasil ── */}
          <section className="flex flex-col gap-4">
            <div className="rounded-3xl border border-sand bg-white p-5 shadow-soft">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-bold uppercase tracking-wider text-charcoal/50">Hasil baca</h2>
                {result && (
                  <span className="text-xs text-charcoal/40">
                    {result.stats.glyphs} aksara · {result.stats.elapsed_ms} ms · keyakinan{" "}
                    {Math.round((result.stats.mean_confidence ?? 0) * 100)}%
                  </span>
                )}
              </div>

              {!result && (
                <div className="py-10 text-center">
                  <Lightbulb className="mx-auto mb-2 h-7 w-7 text-saffron/70" />
                  <p className="mx-auto max-w-sm text-sm text-charcoal/60">
                    Arahkan kamera <b>mendatar (lanskap)</b> dan masukkan tulisan ke dalam bingkai. Tulisan di luar bingkai
                    tidak ikut terbaca.
                  </p>
                  <ul className="mx-auto mt-4 max-w-xs space-y-1 text-left text-xs text-charcoal/50">
                    <li>• Pegang ponsel mendatar — area baca mengikuti bingkai, bukan seluruh sensor.</li>
                    <li>• Satu baris aksara Bali lebih mudah dibaca daripada paragraf panjang.</li>
                    <li>• Untuk prasasti/lontar: potret per baris, lebih dekat.</li>
                    <li>• Salah baca? Ketuk kotaknya lalu kirim koreksi — model dilatih ulang oleh guru/admin.</li>
                  </ul>
                </div>
              )}

              {result && (
                <div className="space-y-4">
                  {finalText.aksara && (
                    <div>
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-charcoal/40">Aksara Bali</p>
                      <p className="whitespace-pre-wrap break-words text-3xl leading-relaxed text-charcoal" lang="ban">
                        {finalText.aksara}
                      </p>
                    </div>
                  )}
                  {(displayLatin || toBali) && (
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-2xl bg-cream p-3">
                        <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-charcoal/40">
                          {result.text.aksara ? "Transliterasi (Latin)" : "Bacaan Latin"}
                        </p>
                        <p className="text-lg font-semibold text-deep-brown">{displayLatin || "—"}</p>
                      </div>
                      <div className="rounded-2xl bg-sage/10 p-3">
                        <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-charcoal/40">Menjadi Aksara</p>
                        <p className="whitespace-pre-wrap break-words text-lg leading-relaxed text-deep-brown" lang="ban">
                          {toBali || result.text.aksara || "—"}
                        </p>
                      </div>
                    </div>
                  )}

                  {glossary.length > 0 && (
                    <div className="rounded-2xl border border-sand p-3">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-charcoal/40">Arti kata</p>
                      <ul className="space-y-1 text-sm">
                        {glossary.slice(0, 8).map((g, i) => (
                          <li key={i} className="flex gap-2">
                            <span className="font-semibold text-deep-brown">{String(g.word)}</span>
                            <span className="text-charcoal/70">{String(g.meaning ?? g.note ?? "")}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {result.warnings.length > 0 && (
                    <div className="flex gap-2 rounded-2xl bg-terracotta/10 p-3 text-sm text-terracotta">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                      <ul className="space-y-0.5">
                        {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
                      </ul>
                    </div>
                  )}

                  {/* baris & keyakinan */}
                  {lines.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-wider text-charcoal/40">Per baris</p>
                      {lines.map((ln, li) => (
                        <div key={li} className="rounded-2xl border border-sand p-2.5">
                          <div className="mb-1.5 flex items-center gap-2 text-xs text-charcoal/50">
                            <span className={cn("rounded-full px-2 py-0.5 font-semibold",
                              ln.script === "aksara" ? "bg-saffron/15 text-saffron-dark" : "bg-ocean/10 text-ocean")}>
                              {ln.script === "aksara" ? "Bali" : "Latin"}
                            </span>
                            <span>{ln.glyphs.length} unit</span>
                            <span className={confTone(ln.confidence)}>{Math.round(ln.confidence * 100)}%</span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {ln.glyphs.map((g, gi) => (
                              <button
                                key={gi}
                                onClick={() => setSelected({ line: li, glyph: gi })}
                                className={cn("rounded-xl border px-2 py-1 text-xl leading-tight transition-colors",
                                  selected?.line === li && selected?.glyph === gi
                                    ? "border-saffron bg-saffron/10" : "border-transparent hover:border-sand hover:bg-cream",
                                  (g.confidence ?? 1) < 0.55 ? "text-terracotta" : "text-charcoal")}
                                title={`${g.name ?? g.label} · ${Math.round((g.confidence ?? 0) * 100)}%`}
                              >
                                {g.glyph || "?"}
                                {g.marks.length > 0 && <span className="ml-0.5 align-super text-[9px] text-charcoal/40">·{g.marks.length}</span>}
                              </button>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2 pt-1">
                    <button onClick={() => copyText([finalText.aksara, displayLatin].filter(Boolean).join("\n"))}
                      className="inline-flex items-center gap-1.5 rounded-full border border-sand bg-white px-3 py-1.5 text-sm font-semibold text-charcoal/70 hover:border-deep-brown/40">
                      <Copy className="h-4 w-4" /> Salin
                    </button>
                    <button onClick={share}
                      className="inline-flex items-center gap-1.5 rounded-full border border-sand bg-white px-3 py-1.5 text-sm font-semibold text-charcoal/70 hover:border-deep-brown/40">
                      <Share2 className="h-4 w-4" /> Bagikan
                    </button>
                    <Link href="/translate" className="inline-flex items-center gap-1.5 rounded-full border border-sand bg-white px-3 py-1.5 text-sm font-semibold text-charcoal/70 hover:border-deep-brown/40">
                      <Wand2 className="h-4 w-4" /> Buka di Translate
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* inspektur glyph / koreksi */}
            {current && (
              <div className="rounded-3xl border border-saffron/40 bg-saffron/5 p-5 shadow-soft">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-charcoal/40">Periksa aksara</p>
                    <p className="text-2xl text-charcoal">
                      {current.glyph.glyph || "?"} <span className="text-base font-semibold text-charcoal/60">{current.glyph.name ?? current.glyph.label}</span>
                    </p>
                    {current.glyph.marks.length > 0 && (
                      <p className="mt-1 text-sm text-charcoal/60">
                        pangangge: {current.glyph.marks.map((m) => `${m.glyph} ${m.name} (${Math.round(m.probability * 100)}%)`).join(", ")}
                      </p>
                    )}
                  </div>
                  <button onClick={() => { setSelected(null); setPicked(null) }} className="rounded-full p-1.5 text-charcoal/40 hover:bg-white hover:text-charcoal">
                    <X className="h-4 w-4" />
                  </button>
                </div>

                {current.glyph.crop && (
                  <img src={current.glyph.crop} alt="Potongan aksara" className="mb-3 h-20 w-20 rounded-xl border border-sand bg-white object-contain p-1" />
                )}

                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-charcoal/40">Kandidat model</p>
                <div className="mb-3 flex flex-wrap gap-2">
                  {current.glyph.alternatives.map((a) => (
                    <button
                      key={a.label}
                      onClick={() => setPicked(a.label === current.glyph.label ? null : a.label)}
                      className={cn("flex items-center gap-2 rounded-2xl border px-3 py-2 text-left transition-colors",
                        picked === a.label ? "border-saffron bg-white" : "border-sand bg-white/60 hover:border-deep-brown/30")}
                    >
                      <span className="text-2xl leading-none text-charcoal">{a.glyph || a.label}</span>
                      <span className="text-xs">
                        <span className="block font-semibold text-charcoal/70">{a.name}</span>
                        <span className="block text-charcoal/50">{Math.round(a.probability * 100)}%</span>
                      </span>
                      {picked === a.label && <Check className="h-4 w-4 text-sage" />}
                    </button>
                  ))}
                </div>

                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  rows={2}
                  placeholder="Catatan untuk admin (opsional), mis. hurufnya tersambung foto."
                  className="mb-2 w-full rounded-2xl border border-sand bg-white p-3 text-sm outline-none focus:border-saffron"
                />
                <div className="flex items-center gap-2">
                  <button
                    onClick={sendCorrection}
                    disabled={!picked || sending}
                    className="inline-flex items-center gap-2 rounded-full bg-deep-brown px-4 py-2 text-sm font-semibold text-cream hover:bg-charcoal disabled:opacity-50"
                  >
                    {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    Kirim koreksi
                  </button>
                  {sent ? (
                    <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-sage"><Check className="h-4 w-4" /> {sent}</span>
                  ) : (
                    <span className="text-xs text-charcoal/50">Pilih kandidat yang benar untuk mengirim koreksi.</span>
                  )}
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-start gap-2 rounded-2xl border border-terracotta/30 bg-terracotta/10 p-3 text-sm text-terracotta">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <div className="flex-1">
                  <p>{error}</p>
                  <button onClick={() => setError(null)} className="mt-1 text-xs font-semibold underline">tutup</button>
                </div>
              </div>
            )}

            {!ready && (
              <div className="rounded-2xl border border-sand bg-white p-4 text-sm text-charcoal/70">
                Model OCR Lens belum dipasang di server ini. Buka{" "}
                <Link href="/admin/ml" className="font-semibold text-deep-brown underline">Panel Admin → Dataset &amp; Model</Link>{" "}
                untuk mengimpor dataset bawaan dan melatih model (atau jalankan{" "}
                <code className="rounded bg-cream px-1">eval/train_ocr_models.py</code>).
              </div>
            )}
          </section>
        </div>
      </div>
      <BottomNav />
    </div>
  )
}

/** Panel kecil pembaca parameter pipeline aktif (diedit admin di Panel Admin → Lens & OCR). */
function AdvancedPanel({ status }: { status: OcrStatus | null }) {
  const opts = status?.default_options ?? {}
  const rows: { key: string; label: string; hint: string; value: string }[] = [
    { key: "binarize", label: "Ambang batas", hint: String(opts.binarize ?? "sauvola"), value: "" },
    { key: "sauvola_window", label: "Jendela Sauvola", hint: String(opts.sauvola_window ?? 25), value: "" },
    { key: "word_gap_ratio", label: "Celah antar kata", hint: String(opts.word_gap_ratio ?? 0.62), value: "" },
    { key: "split_width_ratio", label: "Batas lebar aksara", hint: String(opts.split_width_ratio ?? 1.25), value: "" },
    { key: "max_glyphs", label: "Maksimum aksara", hint: String(opts.max_glyphs ?? 480), value: "" },
    { key: "use_language_model", label: "Model bahasa (kamus)", hint: opts.use_language_model === false ? "mati" : "hidup", value: "" },
  ]
  return (
    <div className="border-t border-cream/10 bg-charcoal/40 p-4 text-cream">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-cream/50">Parameter pipeline (bawaan server)</p>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {rows.map((r) => (
          <div key={r.key} className="rounded-xl bg-cream/10 px-3 py-2">
            <p className="text-[11px] uppercase tracking-wider text-cream/50">{r.label}</p>
            <p className="text-sm font-semibold">{r.hint}</p>
          </div>
        ))}
      </div>
      <p className="mt-2 text-[11px] text-cream/50">
        Ubah lewat Panel Admin → Lens &amp; OCR agar berlaku untuk semua pengguna.
      </p>
    </div>
  )
}
