"use client"

import { useRef, useState } from "react"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import { Copy, Check, Trash2, Keyboard, PenLine, Undo2, Shuffle, Sparkles } from "lucide-react"
import { AksaraKeyboard, WRESATRA } from "@/components/aksara/aksara-keyboard"
import { HandwritingCanvas, HandwritingCanvasHandle } from "@/components/aksara/handwriting-canvas"
import { classifyTracing, TraceResult } from "@/lib/aksara-recognition"

type InputMode = "keyboard" | "tulis"

export default function PlaygroundPage() {
  const [baliText, setBaliText] = useState("")
  const [latinResult, setLatinResult] = useState("")
  const [validation, setValidation] = useState<any>(null)
  const [copied, setCopied] = useState(false)

  // --- Mode tulis tangan (telusur siluet) ---
  const [mode, setMode] = useState<InputMode>("keyboard")
  const [target, setTarget] = useState(WRESATRA[4]) // "ka"
  const [traceResult, setTraceResult] = useState<TraceResult | null>(null)
  const [classifying, setClassifying] = useState(false)
  const canvasRef = useRef<HandwritingCanvasHandle>(null)

  const insertChar = (char: string) => {
    setBaliText(prev => prev + char)
  }

  const backspace = () => {
    setBaliText(prev => prev.slice(0, -1))
  }

  const handleTranslate = async () => {
    if (!baliText) return
    try {
      const res = await api.translate(baliText, "bali-to-latin")
      setLatinResult(res.result)
    } catch (e) {
      setLatinResult("Error")
    }
  }

  const handleValidate = async () => {
    // Contoh validasi: cek apakah baliText cocok dengan "bali"
    try {
      const res = await api.validatePair("bali", "ᬩᬮᬶ", baliText, "exact")
      setValidation(res)
    } catch (e) {
      console.error(e)
    }
  }

  const pickTarget = (t: (typeof WRESATRA)[number]) => {
    setTarget(t)
    setTraceResult(null)
  }

  const randomTarget = () => {
    const t = WRESATRA[Math.floor(Math.random() * WRESATRA.length)]
    setTarget(t)
    setTraceResult(null)
  }

  const handleClassify = async () => {
    const canvas = canvasRef.current?.getInkCanvas()
    const isEmpty = canvasRef.current?.isEmpty() ?? true
    if (!canvas || isEmpty) {
      setTraceResult(null)
      return
    }
    setClassifying(true)
    try {
      const r = await classifyTracing(canvas, target.bali)
      setTraceResult(r)
    } finally {
      setClassifying(false)
    }
  }

  const handleCanvasClear = () => {
    canvasRef.current?.clear()
    setTraceResult(null)
  }

  const copy = () => {
    navigator.clipboard.writeText(baliText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />

      <div className="container mx-auto px-4 lg:px-8 py-6 max-w-5xl">
        <div className="text-center mb-8">
          <h1 className="font-display text-3xl font-bold">Playground Aksara</h1>
          <p className="text-charcoal/60 mt-1">
            Latihan tulis bebas — ketik lewat keyboard, atau tulis tangan telusuri siluetnya
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card className="p-6 bg-white">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <Keyboard className="h-5 w-5 text-saffron" />
                  Tulis Aksara Bali
                </h3>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setBaliText("")} className="rounded-full">
                    <Trash2 className="h-4 w-4 mr-1" /> Clear
                  </Button>
                  <Button variant="ghost" size="sm" onClick={copy} className="rounded-full">
                    {copied ? <Check className="h-4 w-4 text-sage" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
              </div>

              <div className="min-h-32 p-4 rounded-2xl bg-sand/20 border-2 border-dashed border-sand focus-within:border-saffron focus-within:bg-white transition-all">
                <div className="font-bali text-3xl leading-relaxed min-h-24 break-words">
                  {baliText || <span className="text-charcoal/20">Klik keyboard di bawah atau tulis tangan... ᬩᬮᬶ</span>}
                </div>
                <textarea
                  value={baliText}
                  onChange={(e) => setBaliText(e.target.value)}
                  className="w-full mt-4 p-3 rounded-xl bg-white border border-sand text-sm font-bali"
                  placeholder="Atau paste / ketik aksara Bali langsung..."
                  rows={3}
                />
              </div>

              <div className="flex flex-col sm:flex-row gap-2 mt-4">
                <Button onClick={handleTranslate} className="sm:flex-1">
                  Translate ke Latin
                </Button>
                {/* Dua baris eksplisit (flex-col): label kecil di atas, aksara
                    di bawah - hindari overlap karena mixed inline dengan
                    line-height glyph Balinese yang besar. */}
                <Button
                  variant="outline"
                  onClick={handleValidate}
                  className="sm:flex-1 flex-col h-auto min-h-12 gap-0.5 py-2 leading-none"
                >
                  <span className="text-[10px] uppercase tracking-wider text-deep-brown/60 font-bold">
                    Validasi
                  </span>
                  <span className="font-bali text-base leading-tight">
                    Apakah ini ᬩᬮᬶ?
                  </span>
                </Button>
              </div>

              {latinResult && (
                <div className="mt-4 p-4 rounded-xl bg-deep-brown text-cream">
                  <div className="text-xs text-cream/60 mb-1">Latin:</div>
                  <div className="font-medium">{latinResult}</div>
                </div>
              )}

              {validation && (
                <div className={`mt-4 p-4 rounded-xl border-2 ${validation.is_correct ? "bg-sage/10 border-sage/20" : "bg-amber-50 border-amber-200"}`}>
                  <div className="flex items-center gap-2 font-semibold">
                    {validation.is_correct ? "✅ Benar!" : "❌ Belum tepat"}
                    <Badge variant={validation.is_correct ? "success" : "warning"}>{Math.round(validation.similarity * 100)}% mirip</Badge>
                  </div>
                  {validation.suggestions.length > 0 && (
                    <ul className="mt-2 text-sm list-disc list-inside">
                      {validation.suggestions.map((s: string, i: number) => <li key={i}>{s}</li>)}
                    </ul>
                  )}
                  {validation.differences.length > 0 && (
                    <div className="mt-2 text-xs">
                      {validation.differences.map((d: any, i: number) => (
                        <div key={i} className="p-2 bg-white rounded-lg border mt-1">
                          {d.reason}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="p-6 bg-white">
              {/* Toggle mode: keyboard vs tulis tangan */}
              <div className="grid grid-cols-2 gap-1 p-1 rounded-xl bg-sand/30 mb-4">
                <button
                  type="button"
                  onClick={() => setMode("keyboard")}
                  className={`flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-semibold transition-all ${
                    mode === "keyboard" ? "bg-white shadow text-charcoal" : "text-charcoal/50 hover:text-charcoal"
                  }`}
                >
                  <Keyboard className="h-3.5 w-3.5" /> Keyboard
                </button>
                <button
                  type="button"
                  onClick={() => setMode("tulis")}
                  className={`flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-semibold transition-all ${
                    mode === "tulis" ? "bg-white shadow text-charcoal" : "text-charcoal/50 hover:text-charcoal"
                  }`}
                >
                  <PenLine className="h-3.5 w-3.5" /> Tulis Tangan
                </button>
              </div>

              {mode === "keyboard" ? (
                <AksaraKeyboard onInsert={insertChar} onBackspace={backspace} compact />
              ) : (
                <div className="space-y-4">
                  <div>
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-semibold text-charcoal/50">Pilih aksara yang akan ditelusuri</span>
                      <button
                        type="button"
                        onClick={randomTarget}
                        className="flex items-center gap-1 text-xs font-semibold text-ocean hover:underline"
                      >
                        <Shuffle className="h-3 w-3" /> Acak
                      </button>
                    </div>
                    <div className="grid grid-cols-6 gap-1.5">
                      {WRESATRA.map((item) => (
                        <button
                          key={item.latin}
                          type="button"
                          onClick={() => pickTarget(item)}
                          title={item.latin}
                          className={`h-12 rounded-xl border flex flex-col items-center justify-center transition-all ${
                            target.bali === item.bali
                              ? "bg-saffron/15 border-saffron text-saffron"
                              : "bg-cream border-sand hover:border-saffron"
                          }`}
                        >
                          <span className="font-bali text-lg leading-none">{item.bali}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="mb-2 text-xs font-semibold text-charcoal/50">
                      Telusuri siluet <span className="font-bali text-sm">{target.bali}</span> ({target.latin})
                    </div>
                    <HandwritingCanvas ref={canvasRef} ghost={target.bali} width={440} height={300} />
                  </div>

                  <div className="flex gap-2">
                    <Button onClick={handleClassify} disabled={classifying} className="flex-1">
                      <Sparkles className="h-4 w-4 mr-1.5" />
                      {classifying ? "Menganalisis..." : "Klasifikasi"}
                    </Button>
                    <Button variant="outline" onClick={() => canvasRef.current?.undo()} title="Undo">
                      <Undo2 className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" onClick={handleCanvasClear} title="Bersihkan">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>

                  {traceResult && (
                    <div
                      className={`p-4 rounded-xl border-2 ${
                        traceResult.correct
                          ? "bg-sage/10 border-sage/30"
                          : traceResult.close
                            ? "bg-amber-50 border-amber-200"
                            : "bg-terracotta/5 border-terracotta/20"
                      }`}
                    >
                      <div className="flex items-center justify-between font-semibold">
                        {traceResult.correct ? (
                          <span className="text-sage">✅ Benar!</span>
                        ) : traceResult.close ? (
                          <span className="text-amber-600">🟡 Hampir tepat</span>
                        ) : (
                          <span className="text-terracotta">🔴 Coba lagi</span>
                        )}
                        <Badge variant={traceResult.correct ? "success" : "warning"}>
                          {Math.round(traceResult.score * 100)}%
                        </Badge>
                      </div>
                      <p className="mt-1.5 text-xs text-charcoal/70">
                        {traceResult.correct
                          ? `Luar biasa — tulisanmu mirip ${target.latin} (${target.bali}). Pilih aksara lain untuk lanjut.`
                          : traceResult.close
                            ? `Kamu sudah ${Math.round(traceResult.score * 100)}% di jalan — lengkapi bagian yang kurang dari siluet.`
                            : `Baru ${Math.round(traceResult.score * 100)}%. Telusuri siluet perlahan dari atas ke bawah.`}
                      </p>
                    </div>
                  )}

                  <p className="text-[10px] text-charcoal/40 leading-relaxed">
                    Klasifikasi AI on-device (template matching) — tulisanmu tidak dikirim ke
                    mana pun, bisa dipakai offline.
                  </p>
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>

      <BottomNav />
    </div>
  )
}
