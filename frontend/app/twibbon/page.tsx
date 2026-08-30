"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api, SITE_URL, SITE_HASHTAGS } from "@/lib/api"
import {
  Stamp, Upload, ImagePlus, Download, Share2, Copy, Check, Trash2,
  Sparkles, Loader2, ImageIcon,
} from "lucide-react"

// ── Konstanta ────────────────────────────────────────────────────────────

type Ratio = "4:5" | "1:1" | "9:16"
const RATIOS: { id: Ratio; label: string; note: string }[] = [
  { id: "4:5", label: "4:5", note: "Post IG" },
  { id: "1:1", label: "1:1", note: "Kotak" },
  { id: "9:16", label: "9:16", note: "Story/Reels" },
]
const SIZES: Record<Ratio, { w: number; h: number }> = {
  "4:5": { w: 1080, h: 1350 },
  "1:1": { w: 1080, h: 1080 },
  "9:16": { w: 1080, h: 1920 },
}

const COLORS = [
  { id: "cream", hex: "#FFF8E7", name: "Krem" },
  { id: "white", hex: "#FFFFFF", name: "Putih" },
  { id: "saffron", hex: "#FF6B35", name: "Saffron" },
  { id: "sage", hex: "#A8C8A0", name: "Sage" },
  { id: "brown", hex: "#2C1810", name: "Cokelat" },
]

type TextPos = "top" | "middle" | "bottom"

/** Style twibbon: id, nama, inset teks (fraksi dari lebar), & preview CSS. */
type TwibbonStyle = {
  id: string
  name: string
  /** [atas, bawah] — fraksi lebar kanvas yang "dimakan" bingkai (untuk posisi teks) */
  inset: [number, number]
  /** preview: kelas/struktur CSS mini */
  preview: "plain" | "margin" | "double" | "dotted" | "saffron" | "batik" | "corners" | "aksara" | "polaroid" | "rounded"
}

const STYLES: TwibbonStyle[] = [
  { id: "plain", name: "Tanpa Bingkai", inset: [0.04, 0.04], preview: "plain" },
  { id: "margin", name: "Margin Krem", inset: [0.055, 0.055], preview: "margin" },
  { id: "double", name: "Garis Ganda", inset: [0.06, 0.06], preview: "double" },
  { id: "dotted", name: "Garis Titik", inset: [0.055, 0.055], preview: "dotted" },
  { id: "saffron", name: "Gradasi Saffron", inset: [0.05, 0.05], preview: "saffron" },
  { id: "batik", name: "Gradasi Cokelat", inset: [0.05, 0.05], preview: "batik" },
  { id: "corners", name: "Sudut Klasik", inset: [0.055, 0.055], preview: "corners" },
  { id: "aksara", name: "Strip Aksara", inset: [0.085, 0.085], preview: "aksara" },
  { id: "polaroid", name: "Polaroid", inset: [0.05, 0.14], preview: "polaroid" },
  { id: "rounded", name: "Sudut Bulat", inset: [0.06, 0.06], preview: "rounded" },
]

const C = {
  cream: "#FFF8E7",
  saffron: "#FF6B35",
  terracotta: "#C45A3C",
  brown: "#2C1810",
  white: "#FFFFFF",
}

// ── Helper gambar kanvas ─────────────────────────────────────────────────

function roundRectPath(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w, y, x + w, y + h, r)
  ctx.arcTo(x + w, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w, y, r)
  ctx.closePath()
}

/** Bingkai: 4 strip (atas/bawah/kiri/kanan) dengan warna atau gradasi. */
function drawBorder(
  ctx: CanvasRenderingContext2D, W: number, H: number,
  inset: number, thick: number, paint: string | CanvasGradient
) {
  ctx.fillStyle = paint as string
  ctx.fillRect(inset, inset, W - 2 * inset, thick)                 // atas
  ctx.fillRect(inset, H - inset - thick, W - 2 * inset, thick)      // bawah
  ctx.fillRect(inset, inset + thick, thick, H - 2 * inset - 2 * thick) // kiri
  ctx.fillRect(W - inset - thick, inset + thick, thick, H - 2 * inset - 2 * thick) // kanan
}

/** Latar bingkai (digambar SEBELUM foto). */
function drawFrameBackground(ctx: CanvasRenderingContext2D, W: number, H: number, id: string) {
  if (id === "polaroid") {
    ctx.fillStyle = C.white
    ctx.fillRect(0, 0, W, H)
  } else if (id === "rounded") {
    ctx.fillStyle = C.cream
    ctx.fillRect(0, 0, W, H)
  }
}

/** Lini depan bingkai (digambar SETELAH foto). */
function drawFrame(ctx: CanvasRenderingContext2D, W: number, H: number, id: string) {
  const m = Math.round(W * 0.035)
  switch (id) {
    case "margin": {
      drawBorder(ctx, W, H, Math.round(m * 0.5), m, C.cream)
      break
    }
    case "double": {
      drawBorder(ctx, W, H, Math.round(m * 0.5), Math.round(m * 0.9), C.cream)
      ctx.strokeStyle = C.brown
      ctx.lineWidth = Math.max(3, m * 0.18)
      ctx.strokeRect(m * 1.15, m * 1.15, W - m * 2.3, H - m * 2.3)
      ctx.lineWidth = Math.max(2, m * 0.1)
      ctx.strokeRect(m * 1.9, m * 1.9, W - m * 3.8, H - m * 3.8)
      break
    }
    case "dotted": {
      drawBorder(ctx, W, H, Math.round(m * 0.5), m * 0.8, C.cream)
      ctx.strokeStyle = C.brown
      ctx.lineWidth = Math.max(3, m * 0.22)
      ctx.setLineDash([m * 0.7, m * 0.55])
      ctx.strokeRect(m * 1.5, m * 1.5, W - m * 3, H - m * 3)
      ctx.setLineDash([])
      break
    }
    case "saffron": {
      const g = ctx.createLinearGradient(0, 0, W, H)
      g.addColorStop(0, C.saffron)
      g.addColorStop(0.5, C.terracotta)
      g.addColorStop(1, C.saffron)
      drawBorder(ctx, W, H, Math.round(m * 0.5), m * 0.95, g)
      break
    }
    case "batik": {
      const g = ctx.createLinearGradient(0, 0, 0, H)
      g.addColorStop(0, C.brown)
      g.addColorStop(1, C.terracotta)
      drawBorder(ctx, W, H, Math.round(m * 0.5), m * 0.95, g)
      ctx.strokeStyle = C.cream
      ctx.lineWidth = Math.max(2, m * 0.12)
      ctx.strokeRect(m * 1.4, m * 1.4, W - m * 2.8, H - m * 2.8)
      break
    }
    case "corners": {
      drawBorder(ctx, W, H, Math.round(m * 0.5), m * 0.85, C.cream)
      const L = Math.round(W * 0.13)
      const t = Math.max(6, Math.round(m * 0.5))
      ctx.strokeStyle = C.saffron
      ctx.lineWidth = t
      const inner = m * 2.6
      const corners: [number, number, number, number][] = [
        [inner, inner, 1, 1],
        [W - inner, inner, -1, 1],
        [W - inner, H - inner, -1, -1],
        [inner, H - inner, 1, -1],
      ]
      for (const [cx, cy, dx, dy] of corners) {
        ctx.beginPath()
        ctx.moveTo(cx, cy + dy * L)
        ctx.lineTo(cx, cy)
        ctx.lineTo(cx + dx * L, cy)
        ctx.stroke()
      }
      break
    }
    case "aksara": {
      const strip = Math.round(W * 0.075)
      ctx.fillStyle = C.brown
      ctx.fillRect(0, 0, W, strip)
      ctx.fillRect(0, H - strip, W, strip)
      ctx.fillStyle = C.saffron
      ctx.fillRect(0, strip, W, Math.max(3, m * 0.25))
      ctx.fillRect(0, H - strip - Math.max(3, m * 0.25), W, Math.max(3, m * 0.25))
      const glyphSize = Math.round(strip * 0.62)
      ctx.fillStyle = C.cream
      ctx.font = `600 ${glyphSize}px "Noto Sans Balinese", sans-serif`
      ctx.textBaseline = "middle"
      const pattern = "ᬧ᭄ᬮᬫ"
      const gap = glyphSize * 2.2
      const yTop = strip / 2
      const yBot = H - strip / 2
      let x = gap * 0.4
      while (x < W) {
        ctx.fillText(pattern, x, yTop)
        ctx.fillText(pattern, x + gap * 0.5, yBot)
        x += gap
      }
      ctx.textBaseline = "alphabetic"
      break
    }
    case "rounded": {
      const b = Math.round(W * 0.035)
      const r = Math.round(W * 0.05)
      ctx.strokeStyle = C.cream
      ctx.lineWidth = b
      roundRectPath(ctx, b / 2, b / 2, W - b, H - b, r)
      ctx.stroke()
      break
    }
    default:
      break
  }
}

/** Potong gambar ke kanvas (cover). */
function drawPhotoCover(
  ctx: CanvasRenderingContext2D, img: HTMLImageElement, W: number, H: number,
  clip?: (ctx: CanvasRenderingContext2D) => void
) {
  const scale = Math.max(W / img.naturalWidth, H / img.naturalHeight)
  const dw = img.naturalWidth * scale
  const dh = img.naturalHeight * scale
  ctx.save()
  if (clip) clip(ctx)
  ctx.drawImage(img, (W - dw) / 2, (H - dh) / 2, dw, dh)
  ctx.restore()
}

// ── Komponen ─────────────────────────────────────────────────────────────

function StylePreview({ kind, active }: { kind: TwibbonStyle["preview"]; active: boolean }) {
  const ring = active ? "ring-2 ring-saffron border-saffron" : "border-sand hover:border-saffron/50"
  const base = "h-14 w-full overflow-hidden transition-all"
  switch (kind) {
    case "plain":
      return <div className={`${base} ${ring} border-2 border-dashed rounded-xl bg-gradient-to-br from-sand to-cream`} />
    case "margin":
      return <div className={`${base} ${ring} border rounded-xl p-1.5 bg-cream`}><div className="h-full w-full rounded-lg bg-gradient-to-br from-sage/40 to-ocean/30" /></div>
    case "double":
      return (
        <div className={`${base} ${ring} border rounded-xl p-1.5 bg-cream`}>
          <div className="h-full w-full rounded-lg border-2 border-deep-brown p-0.5">
            <div className="h-full w-full rounded-md border border-deep-brown/60 bg-gradient-to-br from-sage/40 to-ocean/30" />
          </div>
        </div>
      )
    case "dotted":
      return (
        <div className={`${base} ${ring} border rounded-xl p-1.5 bg-cream`}>
          <div className="h-full w-full rounded-lg border-2 border-dashed border-deep-brown bg-gradient-to-br from-sage/40 to-ocean/30" />
        </div>
      )
    case "saffron":
      return <div className={`${base} ${ring} border rounded-xl p-[6px] bg-gradient-to-br from-saffron via-terracotta to-saffron`}><div className="h-full w-full rounded-lg bg-gradient-to-br from-sage/40 to-ocean/30" /></div>
    case "batik":
      return <div className={`${base} ${ring} border rounded-xl p-[6px] bg-gradient-to-b from-deep-brown to-terracotta`}><div className="h-full w-full rounded-lg border border-cream/60 bg-gradient-to-br from-sage/40 to-ocean/30" /></div>
    case "corners":
      return (
        <div className={`${base} ${ring} border rounded-xl p-1.5 bg-cream relative`}>
          <div className="h-full w-full rounded-lg bg-gradient-to-br from-sage/40 to-ocean/30" />
          <span className="absolute left-2 top-2 h-4 w-4 border-l-2 border-t-2 border-saffron" />
          <span className="absolute right-2 top-2 h-4 w-4 border-r-2 border-t-2 border-saffron" />
          <span className="absolute left-2 bottom-2 h-4 w-4 border-l-2 border-b-2 border-saffron" />
          <span className="absolute right-2 bottom-2 h-4 w-4 border-r-2 border-b-2 border-saffron" />
        </div>
      )
    case "aksara":
      return (
        <div className={`${base} ${ring} border rounded-xl overflow-hidden bg-gradient-to-br from-sage/40 to-ocean/30`}>
          <div className="bg-deep-brown text-cream font-bali text-[10px] leading-4 text-center overflow-hidden whitespace-nowrap">ᬧᬮ᭄ᬫ ᬧ᭄ᬮᬨᬫ ᭄ᬮ᭄ᬨ</div>
          <div className="flex-1" />
          <div className="bg-deep-brown text-cream font-bali text-[10px] leading-4 text-center overflow-hidden whitespace-nowrap">ᬧ᭄ᬮᬨᬫ ᭄ᬮ᭄ᬨ ᬧ᭄᭄ᬨᬫ</div>
        </div>
      )
    case "polaroid":
      return (
        <div className={`${base} ${ring} border rounded-xl p-1 bg-white flex`}>
          <div className="flex-1 flex flex-col">
            <div className="flex-1 bg-gradient-to-br from-sage/40 to-ocean/30" />
            <div className="h-3" />
          </div>
        </div>
      )
    case "rounded":
      return <div className={`${base} ${ring} border rounded-[14px] p-[5px]`}><div className="h-full w-full rounded-[10px] bg-gradient-to-br from-sage/40 to-ocean/30" /></div>
    default:
      return null
  }
}

export default function TwibbonPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const [photo, setPhoto] = useState<HTMLImageElement | null>(null)
  const [photoName, setPhotoName] = useState<string>("")
  const [ratio, setRatio] = useState<Ratio>("4:5")
  const [styleId, setStyleId] = useState("aksara")
  const [latinText, setLatinText] = useState("matur suksma")
  const [aksaraText, setAksaraText] = useState("")
  const [manualMode, setManualMode] = useState(false)
  const [translating, setTranslating] = useState(false)
  const [textSize, setTextSize] = useState(110)
  const [textPos, setTextPos] = useState<TextPos>("bottom")
  const [colorId, setColorId] = useState("cream")
  const [shadow, setShadow] = useState(true)
  const [showLatin, setShowLatin] = useState(true)
  const [darken, setDarken] = useState(true)
  const [watermark, setWatermark] = useState(true)
  const [fontReady, setFontReady] = useState(false)
  const [busy, setBusy] = useState<"" | "download" | "share" | "copy">("")

  const { w: W, h: H } = SIZES[ratio]

  // Muat font aksara sebelum menggambar ke canvas
  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        await (document as any).fonts?.load('600 100px "Noto Sans Balinese"')
        await (document as any).fonts?.ready
      } catch { /* fallback sans-serif */ }
      if (alive) setFontReady(true)
    })()
    return () => { alive = false }
  }, [])

  // Terjemahkan Latin → Aksara (debounce)
  useEffect(() => {
    if (manualMode || !latinText.trim()) { setAksaraText(""); return }
    setTranslating(true)
    const t = setTimeout(() => {
      api.translate(latinText.trim(), "latin-to-bali")
        .then((r) => setAksaraText(r.result))
        .catch((e) => console.error(e))
        .finally(() => setTranslating(false))
    }, 350)
    return () => clearTimeout(t)
  }, [latinText, manualMode])

  // ── Gambar canvas ──────────────────────────────────────────────────
  const render = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas || !fontReady) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return
    const style = STYLES.find((s) => s.id === styleId) ?? STYLES[0]
    const color = COLORS.find((c) => c.id === colorId)?.hex ?? C.cream

    canvas.width = W
    canvas.height = H

    // 0) latar bingkai (polaroid/rounded) — sebelum foto agar tidak menutupi
    drawFrameBackground(ctx, W, H, styleId)

    const clip =
      styleId === "rounded"
        ? (c: CanvasRenderingContext2D) => {
            const r = Math.round(W * 0.05)
            const b = Math.round(W * 0.035)
            roundRectPath(c, b / 2, b / 2, W - b, H - b, r)
            c.clip()
          }
        : styleId === "polaroid"
          ? (c: CanvasRenderingContext2D) => {
              const t = Math.round(W * 0.045)
              const bo = Math.round(W * 0.12)
              c.rect(t, t, W - 2 * t, H - t - bo)
              c.clip()
            }
          : undefined

    // 1) latar: foto atau gradasi
    if (photo) {
      drawPhotoCover(ctx, photo, W, H, clip)
    } else {
      const g = ctx.createLinearGradient(0, 0, W, H)
      g.addColorStop(0, "#3A2417")
      g.addColorStop(0.55, C.brown)
      g.addColorStop(1, "#7A3B24")
      ctx.fillStyle = g
      ctx.fillRect(0, 0, W, H)
      // watermark glyph besar
      ctx.save()
      ctx.globalAlpha = 0.08
      ctx.fillStyle = C.cream
      ctx.font = `600 ${Math.round(W * 0.8)}px "Noto Sans Balinese", sans-serif`
      ctx.textAlign = "center"
      ctx.textBaseline = "middle"
      ctx.fillText("ᬅ", W / 2, H / 2)
      ctx.restore()
      if (clip) {
        // gambar ulang latar ter-clip agar watermark ikut terpotong
        ctx.save()
        clip(ctx)
        ctx.fillStyle = g
        ctx.fillRect(0, 0, W, H)
        ctx.globalAlpha = 0.08
        ctx.fillStyle = C.cream
        ctx.font = `600 ${Math.round(W * 0.8)}px "Noto Sans Balinese", sans-serif`
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillText("ᬅ", W / 2, H / 2)
        ctx.restore()
      }
    }

    // 2) penggelapan foto untuk keterbacaan
    if (darken && photo) {
      const g =
        textPos === "top"
          ? ctx.createLinearGradient(0, 0, 0, H * 0.7)
          : textPos === "middle"
            ? ctx.createLinearGradient(0, 0, 0, H)
            : ctx.createLinearGradient(0, H * 0.3, 0, H)
      g.addColorStop(0, "rgba(20,12,8,0.55)")
      g.addColorStop(1, "rgba(20,12,8,0.05)")
      ctx.fillStyle = g
      ctx.save()
      if (clip) clip(ctx)
      ctx.fillRect(0, 0, W, H)
      ctx.restore()
    }

    // 3) bingkai
    drawFrame(ctx, W, H, styleId)

    // 4) teks
    const topInset = Math.round(W * style.inset[0]) + Math.round(W * 0.03)
    const botInset = Math.round(W * style.inset[1]) + Math.round(W * 0.03)
    const maxW = W - topInset - botInset
    const size = textSize
    const lineH = Math.round(size * 1.45)

    const baliLines: string[] = []
    if (aksaraText.trim()) {
      const words = aksaraText.trim().split(/\s+/)
      let cur = ""
      ctx.font = `600 ${size}px "Noto Sans Balinese", sans-serif`
      for (const wd of words) {
        const trial = cur ? `${cur} ${wd}` : wd
        if (ctx.measureText(trial).width > maxW && cur) {
          baliLines.push(cur)
          cur = wd
        } else cur = trial
      }
      if (cur) baliLines.push(cur)
    }
    const latinLine = showLatin && latinText.trim() ? latinText.trim() : ""
    const latinSize = Math.max(28, Math.round(size * 0.34))

    const blockH =
      baliLines.length * lineH +
      (latinLine ? Math.round(latinSize * 1.7) : 0)

    let yTop: number
    if (textPos === "top") yTop = Math.max(topInset, H * 0.05)
    else if (textPos === "middle") yTop = (H - blockH) / 2
    else yTop = H - Math.max(botInset, H * 0.05) - blockH
    yTop = Math.min(Math.max(yTop, topInset - 20), H - blockH - 20)

    ctx.save()
    if (shadow) {
      ctx.shadowColor = "rgba(0,0,0,0.55)"
      ctx.shadowBlur = size * 0.28
      ctx.shadowOffsetY = size * 0.06
    }
    ctx.fillStyle = color
    ctx.textAlign = "center"
    ctx.textBaseline = "alphabetic"
    ctx.font = `600 ${size}px "Noto Sans Balinese", sans-serif`
    baliLines.forEach((ln, i) => {
      ctx.fillText(ln, W / 2, yTop + lineH * i + size * 0.8)
    })
    if (latinLine) {
      const ly = yTop + baliLines.length * lineH + latinSize * 1.1
      ctx.font = `600 ${latinSize}px Inter, sans-serif`
      ctx.globalAlpha = 0.92
      ctx.fillText(latinLine.toUpperCase(), W / 2, ly)
      ctx.globalAlpha = 1
    }
    ctx.restore()

    // 5) branding kecil (watermark) — di dalam area konten, pojok kanan bawah
    if (watermark) {
      ctx.save()
      ctx.font = `600 ${Math.round(W * 0.021)}px Inter, sans-serif`
      ctx.textAlign = "right"
      ctx.fillStyle = "rgba(255,248,231,0.8)"
      ctx.shadowColor = "rgba(0,0,0,0.5)"
      ctx.shadowBlur = 8
      const wmX = W - Math.round(W * style.inset[0]) - Math.round(W * 0.025)
      const wmY = H - Math.round(W * style.inset[1]) - Math.round(W * 0.022)
      ctx.fillText("aksara.id · aksara bali", wmX, wmY)
      ctx.restore()
    }
  }, [photo, W, H, styleId, darken, watermark, textPos, aksaraText, latinText, showLatin, textSize, colorId, shadow, fontReady])

  useEffect(() => { render() }, [render])

  // ── Foto ──────────────────────────────────────────────────────────
  const loadFile = (f: File) => {
    const reader = new FileReader()
    reader.onload = () => {
      const img = new Image()
      img.onload = () => { setPhoto(img); setPhotoName(f.name) }
      img.src = String(reader.result)
    }
    reader.readAsDataURL(f)
  }

  const loadSample = () => {
    const img = new Image()
    img.onload = () => { setPhoto(img); setPhotoName("contoh: pura") }
    img.src = "/sample/temple.jpg"
  }

  // ── Ekspor & share ─────────────────────────────────────────────────
  const getBlob = () =>
    new Promise<Blob>((res, rej) => {
      canvasRef.current?.toBlob((b) => (b ? res(b) : rej(new Error("gagal export"))), "image/png")
    })

  const download = async () => {
    setBusy("download")
    try {
      const blob = await getBlob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = "twibbon-aksara.png"
      a.click()
      api.trackTwibbon()
      setTimeout(() => URL.revokeObjectURL(url), 4000)
    } catch (e) {
      alert("Gagal mengunduh: " + (e as Error).message)
    } finally {
      setBusy("")
    }
  }

  const share = async () => {
    setBusy("share")
    try {
      const blob = await getBlob()
      const file = new File([blob], "twibbon-aksara.png", { type: "image/png" })
      const shareText = `Twibbon Aksara Bali ✨ Buat sendiri di ${SITE_URL} ${SITE_HASHTAGS}`
      const nav = navigator as any
      if (nav.canShare?.({ files: [file] })) {
        await nav.share({ files: [file], title: "Twibbon Aksara Bali", text: shareText })
      } else if (nav.share) {
        await nav.share({ title: "Twibbon Aksara Bali", text: shareText })
      } else {
        alert("Peramban ini tidak mendukung share langsung — gunakan tombol Unduh lalu unggah ke medsos kamu.")
      }
      api.trackTwibbon()
    } catch (e) {
      if ((e as Error).name !== "AbortError") console.error(e)
    } finally {
      setBusy("")
    }
  }

  const [copied, setCopied] = useState(false)
  const copy = async () => {
    setBusy("copy")
    try {
      const blob = await getBlob()
      await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })])
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (e) {
      alert("Gagal menyalin ke clipboard (peramban tidak mendukung). Gunakan Unduh.")
    } finally {
      setBusy("")
    }
  }

    return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-10">
      <Header />

      <div className="container mx-auto px-4 lg:px-8 py-6 lg:py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-saffron to-terracotta text-cream shadow-soft">
              <Stamp className="h-7 w-7" />
            </div>
            <div>
              <h1 className="font-display text-2xl lg:text-3xl font-bold text-deep-brown">Studio Twibbon</h1>
              <p className="text-sm text-charcoal/60">
                Tulis aksara di fotomu — hasil translate langsung jadi twibbon untuk medsos
              </p>
            </div>
          </div>
          <Badge variant="saffron">PNG 1080px</Badge>
        </div>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,460px)_1fr] lg:items-start">
          {/* ── Preview ── */}
          <div>
            <div className="rounded-3xl border border-sand bg-white p-3 shadow-medium">
              <canvas
                ref={canvasRef}
                className="w-full h-auto rounded-2xl shadow-soft"
                style={{ aspectRatio: `${W} / ${H}` }}
              />
            </div>

            {/* Rasio */}
            <div className="mt-4 flex gap-2">
              {RATIOS.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setRatio(r.id)}
                  className={`flex-1 rounded-2xl border px-3 py-2.5 text-sm font-semibold transition-all ${
                    ratio === r.id ? "border-deep-brown bg-deep-brown text-cream shadow-soft" : "border-sand bg-white text-charcoal/60 hover:border-deep-brown/40"
                  }`}
                >
                  {r.label}
                  <span className={`block text-[10px] font-normal ${ratio === r.id ? "text-cream/60" : "text-charcoal/40"}`}>{r.note}</span>
                </button>
              ))}
            </div>

            {/* Aksi ekspor */}
            <div className="mt-4 grid grid-cols-3 gap-2">
              <Button onClick={download} disabled={busy !== ""} className="rounded-2xl">
                {busy === "download" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                Unduh
              </Button>
              <Button variant="outline" onClick={share} disabled={busy !== ""} className="rounded-2xl border-saffron text-saffron-dark hover:bg-saffron/5 hover:text-saffron-dark">
                {busy === "share" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Share2 className="h-4 w-4" />}
                Bagikan
              </Button>
              <Button variant="outline" onClick={copy} disabled={busy !== ""} className="rounded-2xl">
                {copied ? <Check className="h-4 w-4 text-sage" /> : busy === "copy" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Copy className="h-4 w-4" />}
                Salin
              </Button>
            </div>
            <p className="mt-2 text-center text-[11px] text-charcoal/45">
              “Bagikan” memakai berbagi peramban (WhatsApp, IG, X…) — di desktop gunakan Unduh.
            </p>
          </div>

          {/* ── Kontrol ── */}
          <div className="space-y-4">
            {/* Foto */}
            <Card className="p-5 bg-white shadow-soft">
              <h3 className="flex items-center gap-2 text-sm font-bold text-deep-brown mb-3">
                <ImageIcon className="h-4 w-4 text-saffron" /> 1. Foto
              </h3>
              <div className="flex flex-wrap gap-2">
                <input
                  ref={fileRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) loadFile(f); e.target.value = "" }}
                />
                <button
                  onClick={() => fileRef.current?.click()}
                  className="inline-flex items-center gap-2 rounded-full bg-deep-brown px-4 py-2 text-sm font-semibold text-cream shadow-soft hover:bg-deep-brown/90"
                >
                  <Upload className="h-4 w-4" /> Unggah Foto
                </button>
                <button
                  onClick={loadSample}
                  className="inline-flex items-center gap-2 rounded-full border border-sand bg-cream px-4 py-2 text-sm font-semibold text-charcoal/70 hover:border-saffron/50"
                >
                  <ImagePlus className="h-4 w-4" /> Pakai Contoh
                </button>
                {photo && (
                  <button
                    onClick={() => { setPhoto(null); setPhotoName("") }}
                    className="inline-flex items-center gap-2 rounded-full border border-sand bg-white px-4 py-2 text-sm font-semibold text-terracotta hover:border-terracotta/50"
                  >
                    <Trash2 className="h-4 w-4" /> Hapus Foto
                  </button>
                )}
              </div>
              <p className="mt-2 text-[11px] text-charcoal/45">
                {photo ? `Foto: ${photoName}` : "Belum ada foto — latar gradasi cokelat akan dipakai."}
              </p>
            </Card>

            {/* Teks */}
            <Card className="p-5 bg-white shadow-soft">
              <div className="flex items-center justify-between mb-3">
                <h3 className="flex items-center gap-2 text-sm font-bold text-deep-brown">
                  <Sparkles className="h-4 w-4 text-saffron" /> 2. Teks Aksara
                </h3>
                <div className="flex rounded-full border border-sand bg-cream p-0.5 text-[11px] font-semibold">
                  <button
                    onClick={() => setManualMode(false)}
                    className={`rounded-full px-3 py-1 ${!manualMode ? "bg-deep-brown text-cream" : "text-charcoal/50"}`}
                  >
                    Tulis Latin (otomatis)
                  </button>
                  <button
                    onClick={() => setManualMode(true)}
                    className={`rounded-full px-3 py-1 ${manualMode ? "bg-deep-brown text-cream" : "text-charcoal/50"}`}
                  >
                    Paste Aksara
                  </button>
                </div>
              </div>

              {manualMode ? (
                <textarea
                  value={aksaraText}
                  onChange={(e) => setAksaraText(e.target.value)}
                  rows={2}
                  placeholder="Paste aksara Bali di sini, mis. ᬫᬢᬸᬃ ᬲᬸᬓ᭄ᬱ᭄"
                  className="w-full rounded-xl border border-sand bg-cream/50 px-3 py-2 font-bali text-xl outline-none focus:border-saffron"
                />
              ) : (
                <div className="relative">
                  <input
                    value={latinText}
                    onChange={(e) => setLatinText(e.target.value)}
                    placeholder="mis. matur suksma, rahajeng, om swastyastu…"
                    className="w-full rounded-xl border border-sand bg-cream/50 px-3 py-2.5 pr-10 outline-none focus:border-saffron"
                  />
                  {translating && <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-saffron" />}
                </div>
              )}

              <div className="mt-3 min-h-12 rounded-xl bg-deep-brown/5 border border-sand px-4 py-2 text-center">
                <div className="font-bali text-2xl text-deep-brown">
                  {aksaraText || <span className="text-charcoal/25 text-sm font-sans">Aksara hasil translate tampil di sini…</span>}
                </div>
              </div>

              <div className="mt-4 space-y-3">
                <div>
                  <div className="flex justify-between text-[11px] font-semibold text-charcoal/60 mb-1">
                    <span>Ukuran teks</span><span>{textSize}px</span>
                  </div>
                  <input
                    type="range" min={56} max={170} step={2}
                    value={textSize}
                    onChange={(e) => setTextSize(Number(e.target.value))}
                    className="w-full accent-saffron"
                  />
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-semibold text-charcoal/60">Posisi:</span>
                  {(["top", "middle", "bottom"] as TextPos[]).map((p) => (
                    <button
                      key={p}
                      onClick={() => setTextPos(p)}
                      className={`rounded-full border px-3 py-1 text-xs font-semibold ${textPos === p ? "border-deep-brown bg-deep-brown text-cream" : "border-sand bg-cream text-charcoal/60"}`}
                    >
                      {p === "top" ? "Atas" : p === "middle" ? "Tengah" : "Bawah"}
                    </button>
                  ))}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-semibold text-charcoal/60">Warna:</span>
                  {COLORS.map((c) => (
                    <button
                      key={c.id}
                      title={c.name}
                      onClick={() => setColorId(c.id)}
                      className={`h-7 w-7 rounded-full border-2 transition-transform ${colorId === c.id ? "scale-110 border-saffron" : "border-sand"}`}
                      style={{ background: c.hex }}
                    />
                  ))}
                </div>
                <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs font-semibold text-charcoal/70">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={shadow} onChange={(e) => setShadow(e.target.checked)} className="accent-saffron h-4 w-4" />
                    Bayangan teks
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={showLatin} onChange={(e) => setShowLatin(e.target.checked)} className="accent-saffron h-4 w-4" />
                    Tampilkan teks Latin
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={darken} onChange={(e) => setDarken(e.target.checked)} className="accent-saffron h-4 w-4" />
                    Gelapkan foto
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer" title="Tulisan kecil aksara.id di sudut gambar — bantu menyebarkan platform">
                    <input type="checkbox" checked={watermark} onChange={(e) => setWatermark(e.target.checked)} className="accent-saffron h-4 w-4" />
                    Branding aksara.id
                  </label>
                </div>
              </div>
            </Card>

            {/* Bingkai */}
            <Card className="p-5 bg-white shadow-soft">
              <h3 className="flex items-center gap-2 text-sm font-bold text-deep-brown mb-3">
                <Stamp className="h-4 w-4 text-saffron" /> 3. Bingkai Twibbon
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-3">
                {STYLES.map((s) => (
                  <button key={s.id} onClick={() => setStyleId(s.id)} className="text-left group">
                    <StylePreview kind={s.preview} active={styleId === s.id} />
                    <span className={`mt-1.5 block text-center text-[11px] font-semibold ${styleId === s.id ? "text-saffron-dark" : "text-charcoal/55"}`}>
                      {s.name}
                    </span>
                  </button>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </div>

      <BottomNav />
    </div>
  )
}
