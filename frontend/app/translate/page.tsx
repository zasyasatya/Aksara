"use client"

import { useState, useEffect } from "react"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import { useTranslateStore } from "@/lib/store"
import { AksaraKeyboard } from "@/components/aksara/aksara-keyboard"
import { ArrowLeftRight, Copy, Check, Sparkles, Info, BookOpen, AlertTriangle, Keyboard } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

export default function TranslatePage() {
  const { input, output, direction, breakdown, setInput, setOutput, setDirection, setBreakdown } = useTranslateStore()
  const [isLoading, setIsLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [warnings, setWarnings] = useState<string[]>([])
  const [confidence, setConfidence] = useState(1)
  const [showKeyboard, setShowKeyboard] = useState(false)

  const isBaliInput = direction === "bali-to-latin"

  /** Sisipkan aksara ke input (memilih aksara dari keyboard virtual). */
  const insertAksara = (char: string) => setInput(input + char)
  const backspaceAksara = () => setInput(input.slice(0, -1))

  /** Pilih arah dua-arah: Latin → Bali atau Bali → Latin. */
  const pickDirection = (dir: "latin-to-bali" | "bali-to-latin") => {
    if (dir === direction) return
    setDirection(dir)
    // pindah input ke sisi yang sesuai dengan isi hasil sebelumnya
    if (output) {
      setInput(output)
      setOutput(input)
    }
  }
  
  const handleTranslate = async (text: string, dir: typeof direction) => {
    if (!text.trim()) {
      setOutput("")
      setBreakdown([])
      return
    }
    
    setIsLoading(true)
    try {
      const res = await api.translate(text, dir)
      setOutput(res.result)
      setBreakdown(res.breakdown)
      setWarnings(res.warnings)
      setConfidence(res.confidence)
    } catch (e) {
      console.error(e)
      setOutput("Error: " + (e as Error).message)
    } finally {
      setIsLoading(false)
    }
  }
  
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (input) handleTranslate(input, direction)
    }, 300)
    return () => clearTimeout(timeout)
  }, [input, direction])
  
  const swapDirection = () => {
    const newDir = direction === "latin-to-bali" ? "bali-to-latin" : "latin-to-bali"
    setDirection(newDir)
    setInput(output)
    setOutput(input)
  }
  
  const copyOutput = () => {
    navigator.clipboard.writeText(output)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  
  const examples = [
    { latin: "bali", bali: "ᬩᬮᬶ" },
    { latin: "om swastyastu", bali: "ᬑᬁ ᬲ᭄ᬯᬲ᭄ᬢ᭄ᬬᬲ᭄ᬢᬸ" },
    { latin: "matur suksma", bali: "ᬫᬢᬸᬃ ᬲᬸᬓ᭄ᬱ᭄ᬫ" },
    { latin: "rahajeng", bali: "ᬭᬳᬚᭂᬂ" },
  ]
  
  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />
      
      <div className="container mx-auto px-4 lg:px-8 py-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="font-display text-3xl font-bold">Translate Aksara</h1>
            <p className="text-charcoal/60 mt-2">Latin ↔ Aksara Bali dengan akurasi tinggi + penjelasan gantungan</p>
            <div className="flex justify-center gap-2 mt-4">
              <Badge variant="saffron">95% akurasi</Badge>
              <Badge variant="default">Gantungan cerdas</Badge>
              <Badge variant="success">Tumpuk telu check</Badge>
            </div>
          </div>
          
          <Card className="overflow-hidden bg-white shadow-large">
            {/* Direction toggle */}
            <div className="flex items-center justify-between p-4 border-b border-sand bg-sand/20">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => pickDirection("latin-to-bali")}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${direction === "latin-to-bali" ? "bg-deep-brown text-cream shadow-soft" : "bg-white text-charcoal/60 hover:text-deep-brown"}`}
                >
                  Latin
                </button>
                <ArrowLeftRight className="h-4 w-4 text-charcoal/40" />
                <button
                  type="button"
                  onClick={() => pickDirection("bali-to-latin")}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${direction === "bali-to-latin" ? "bg-deep-brown text-cream shadow-soft" : "bg-white text-charcoal/60 hover:text-deep-brown"}`}
                >
                  <span className="font-bali">ᬩᬮᬶ</span> Bali
                </button>
              </div>
              <Button variant="ghost" size="sm" onClick={swapDirection} className="rounded-full">
                <ArrowLeftRight className="h-4 w-4 mr-2" />
                Tukar
              </Button>
            </div>
            
            <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-sand">
              {/* Input */}
              <div className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <label className="text-sm font-medium">
                    {direction === "latin-to-bali" ? "Teks Latin" : "Aksara Bali"}
                  </label>
                  <span className="text-xs text-charcoal/60">{input.length}/5000</span>
                </div>
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={direction === "latin-to-bali" ? "Ketik teks latin, misal: bali, om swastyastu..." : "Paste aksara Bali, misal: ᬩᬮᬶ"}
                  className={`w-full h-40 p-4 rounded-2xl bg-sand/30 border border-sand focus:border-saffron focus:ring-2 focus:ring-saffron/20 outline-none resize-none transition-all ${direction === "bali-to-latin" ? "font-bali text-xl" : "text-base"}`}
                />
                {isBaliInput && (
                <button
                  type="button"
                  onClick={() => setShowKeyboard(v => !v)}
                  className={`mt-3 inline-flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold transition-colors ${showKeyboard ? "border-saffron bg-saffron/10 text-saffron-dark" : "border-sand bg-cream text-charcoal/60 hover:border-saffron/50"}`}
                >
                  <Keyboard className="h-3.5 w-3.5" />
                  {showKeyboard ? "Tutup Keyboard Aksara" : "Buka Keyboard Aksara"}
                </button>
                )}
                {showKeyboard && isBaliInput && (
                  <div className="mt-3 rounded-2xl border border-sand bg-cream/60 p-3">
                    <AksaraKeyboard onInsert={insertAksara} onBackspace={backspaceAksara} compact />
                  </div>
                )}
                <div className="flex gap-2 mt-3 flex-wrap">
                  {examples.map((ex) => (
                    <button
                      key={ex.latin}
                      onClick={() => setInput(direction === "latin-to-bali" ? ex.latin : ex.bali)}
                      className="text-xs px-3 py-1.5 rounded-full bg-cream border border-sand hover:border-saffron hover:text-saffron transition-colors"
                    >
                      {direction === "latin-to-bali" ? ex.latin : ex.bali}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Output */}
              <div className="p-6 bg-deep-brown/5">
                <div className="flex items-center justify-between mb-3">
                  <label className="text-sm font-medium flex items-center gap-2">
                    {direction === "latin-to-bali" ? "Aksara Bali" : "Teks Latin"}
                    {isLoading && <div className="h-3 w-3 rounded-full bg-saffron animate-pulse" />}
                  </label>
                  <div className="flex items-center gap-2">
                    {confidence < 0.9 && (
                      <Badge variant="warning" className="text-[10px]">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        {Math.round(confidence * 100)}%
                      </Badge>
                    )}
                    <Button variant="ghost" size="sm" onClick={copyOutput} className="h-8 rounded-full">
                      {copied ? <Check className="h-4 w-4 text-sage" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
                
                <div className={`w-full min-h-40 p-4 rounded-2xl bg-white border border-sand shadow-soft ${direction === "latin-to-bali" ? "font-bali text-2xl leading-relaxed" : "text-base"}`}>
                  {output ? (
                    <div className="break-words">{output}</div>
                  ) : (
                    <div className="text-charcoal/30 italic">
                      {direction === "latin-to-bali" ? "Hasil aksara akan muncul di sini..." : "Hasil latin akan muncul di sini..."}
                    </div>
                  )}
                </div>
                
                {warnings.length > 0 && (
                  <div className="mt-3 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800">
                    <div className="font-medium flex items-center gap-1 mb-1">
                      <Info className="h-3 w-3" /> Perhatian:
                    </div>
                    {warnings.map((w, i) => <div key={i}>• {w}</div>)}
                  </div>
                )}
              </div>
            </div>
          </Card>
          
          {/* Breakdown */}
          <AnimatePresence>
            {breakdown.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-6"
              >
                <Card className="p-6 bg-white">
                  <h3 className="font-semibold flex items-center gap-2 mb-4">
                    <Sparkles className="h-5 w-5 text-saffron" />
                    Breakdown & Penjelasan Gantungan
                  </h3>
                  <div className="grid gap-3">
                    {breakdown.map((item, i) => (
                      <div key={i} className="flex items-center gap-4 p-3 rounded-xl bg-sand/30 border border-sand/50">
                        <div className="font-bali text-xl bg-white rounded-xl h-12 w-12 flex items-center justify-center border border-sand shadow-soft">
                          {item.bali}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-sm">{item.latin} → {item.bali}</div>
                          <div className="text-xs text-charcoal/60">{item.description || item.type}</div>
                        </div>
                        {item.type && (
                          <Badge variant="default" className="text-[10px]">
                            {item.type}
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-6 p-4 rounded-xl bg-ocean/5 border border-ocean/10">
                    <h4 className="text-sm font-semibold flex items-center gap-2 mb-2">
                      <BookOpen className="h-4 w-4 text-ocean" />
                      Aturan yang dipakai
                    </h4>
                    <ul className="text-xs text-charcoal/70 space-y-1 list-disc list-inside">
                      <li>Gantungan untuk cluster konsonan (tumpuk telu dilarang)</li>
                      <li>Pangangge suara: ulu (i), suku (u), taleng (e), pepet (ě)</li>
                      <li>Pangangge tengenan: bisah (h), surang (r), cecek (ng), adeg-adeg</li>
                      <li>Kombinasi La gantungan + pepet diperbolehkan (bleganjur), tapi Cakra + pepet dilarang</li>
                    </ul>
                  </div>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Info */}
          <Card className="mt-6 p-6 bg-gradient-to-br from-sand/50 to-cream border-sand">
            <h3 className="font-semibold mb-3">Kenapa translate Aksara Bali sulit?</h3>
            <div className="grid md:grid-cols-3 gap-4 text-sm text-charcoal/70">
              <div>
                <div className="font-medium text-deep-brown mb-1">Gantungan & Gempelan</div>
                <p className="text-xs">Konsonan rangkap ditulis dengan gantungan di bawah, bukan bersebelahan. 4 huruf punya gempelan (menempel).</p>
              </div>
              <div>
                <div className="font-medium text-deep-brown mb-1">Tumpuk Telu</div>
                <p className="text-xs">Tidak boleh 2 gantungan pada 1 aksara dasar. Maksimal 3 lapis total dilarang.</p>
              </div>
              <div>
                <div className="font-medium text-deep-brown mb-1">Pangangge Kompleks</div>
                <p className="text-xs">11 pangangge suara, 4 tengenan, 4 aksara. Posisi di atas, bawah, depan, belakang, bahkan mengapit.</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
      
      <BottomNav />
    </div>
  )
}
