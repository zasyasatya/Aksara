"use client"

import { useState } from "react"
import { AksaraKeyboard } from "@/components/aksara/aksara-keyboard"
import { Keyboard } from "lucide-react"

/**
 * Input teks Aksara Bali + keyboard virtual inline — untuk mengisi glyph
 * di form Guru (thumbnail materi, kunci bali kuis, entri kamus).
 */
export function BaliInput({
  value,
  onChange,
  placeholder,
  rows = 1,
}: {
  value: string
  onChange: (v: string) => void
  placeholder?: string
  rows?: number
}) {
  const [open, setOpen] = useState(false)

  return (
    <div>
      <div className="flex gap-2">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder ?? "Ketik/paste aksara, atau buka keyboard…"}
          rows={rows}
          className="w-full rounded-xl border border-sand bg-cream/50 px-3 py-2 font-bali text-lg outline-none transition-colors focus:border-saffron focus:bg-white resize-none"
        />
        <button
          type="button"
          onClick={() => setOpen(v => !v)}
          title="Keyboard aksara"
          className={`h-10 w-10 shrink-0 rounded-xl border flex items-center justify-center transition-colors ${
            open ? "border-saffron bg-saffron/10 text-saffron-dark" : "border-sand bg-cream text-charcoal/60 hover:border-saffron/50"
          }`}
        >
          <Keyboard className="h-4 w-4" />
        </button>
      </div>
      {open && (
        <div className="mt-2 rounded-2xl border border-sand bg-cream/60 p-3">
          <AksaraKeyboard onInsert={(c) => onChange(value + c)} onBackspace={() => onChange(value.slice(0, -1))} compact />
        </div>
      )}
    </div>
  )
}
