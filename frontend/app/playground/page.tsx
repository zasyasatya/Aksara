"use client"

import { useState } from "react"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import { Copy, Check, Trash2, Keyboard } from "lucide-react"
import { AksaraKeyboard } from "@/components/aksara/aksara-keyboard"

export default function PlaygroundPage() {
  const [baliText, setBaliText] = useState("")
  const [latinResult, setLatinResult] = useState("")
  const [validation, setValidation] = useState<any>(null)
  const [copied, setCopied] = useState(false)
  
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
    // Example validation: check if baliText matches "bali"
    try {
      const res = await api.validatePair("bali", "ᬩᬮᬶ", baliText, "exact")
      setValidation(res)
    } catch (e) {
      console.error(e)
    }
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
          <p className="text-charcoal/60 mt-1">Latihan tulis bebas dengan keyboard virtual Aksara Bali</p>
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
                  {baliText || <span className="text-charcoal/20">Klik keyboard di bawah atau ketik di sini... ᬩᬮᬶ</span>}
                </div>
                <textarea
                  value={baliText}
                  onChange={(e) => setBaliText(e.target.value)}
                  className="w-full mt-4 p-3 rounded-xl bg-white border border-sand text-sm font-bali"
                  placeholder="Atau paste / ketik aksara Bali langsung..."
                  rows={3}
                />
              </div>
              
              <div className="flex gap-2 mt-4">
                <Button onClick={handleTranslate} className="flex-1">
                  Translate ke Latin
                </Button>
                <Button variant="outline" onClick={handleValidate} className="flex-1">
                  Validasi: Apakah ini ᬩᬮᬶ?
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
              <h3 className="font-semibold mb-4">Keyboard Aksara</h3>
              <AksaraKeyboard onInsert={insertChar} onBackspace={backspace} />
            </Card>
          </div>
        </div>
      </div>
      
      <BottomNav />
    </div>
  )
}
