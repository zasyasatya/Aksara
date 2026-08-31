"use client"

import { useState } from "react"
import { WRESATRA } from "./aksara-keyboard"

export interface PanganggeItem {
  id: string
  bali: string
  name: string
  latin_effect?: string
  /** Template tampilan: ◌ (dotted circle) = posisi aksara dasar yang bisa diisi. */
  mark?: string
  position?: string | null
  description?: string | null
}

/** Isi placeholder ◌ pada template pangangge dengan aksara dasar `base`.
 *  Mirip "rumus": ulu "◌ᬶ" + "ᬓ" → "ᬓᬶ"; taleng "ᬾ◌" + "ᬓ" → "ᬾᬓ". */
export function fillMark(mark: string, base: string): string {
  return mark.replace(/◌/g, base)
}

const POSITION_LABEL: Record<string, string> = {
  above: "di atas",
  below: "di bawah",
  front: "di depan",
  behind: "di belakang",
  after: "di belakang",
  surrounding: "mengapit",
}

interface PanganggeFormulaProps {
  items: PanganggeItem[]
  onInsert?: (text: string) => void
  compact?: boolean
}

/**
 * Simulator pangangge: pengguna memilih aksara dasar, lalu setiap pangangge
 * ditampilkan dengan titik bulat (◌) yang SUDAH TERISI aksara terpilih —
 * seperti formula pangkat/kurung yang bisa diisi angka.
 */
export function PanganggeFormula({ items, onInsert, compact = false }: PanganggeFormulaProps) {
  const [base, setBase] = useState(WRESATRA[4]) // default: ka

  return (
    <div className="space-y-5">
      {/* Pemilih aksara dasar (yang akan mengisi titik bulat ◌) */}
      <div>
        <div className="mb-2 text-xs font-semibold text-charcoal/50">
          Pilih aksara dasar untuk mengisi titik bulat (◌)
        </div>
        <div className="flex flex-wrap gap-1.5">
          {WRESATRA.map((item) => {
            const active = item.bali === base.bali
            return (
              <button
                key={item.latin}
                type="button"
                onClick={() => setBase(item)}
                title={item.latin}
                className={`h-10 min-w-10 px-2 rounded-xl border transition-all flex flex-col items-center justify-center ${
                  active
                    ? "bg-saffron/15 border-saffron text-saffron ring-1 ring-saffron"
                    : "bg-cream border-sand text-charcoal hover:border-saffron"
                }`}
              >
                <span className="font-bali text-lg leading-none">{item.bali}</span>
                <span className="text-[9px] leading-none mt-0.5">{item.latin}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Pangangge dengan titik bulat terisi aksara terpilih */}
      <div>
        <div className="mb-2 text-xs font-semibold text-charcoal/50">
          Pangangge — titik bulat ◌ sudah terisi{" "}
          <span className="font-bali text-sm">{base.bali}</span> ({base.latin})
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {items.map((item) => {
            const filled = fillMark(item.mark || item.bali, base.bali)
            const pos = item.position ? POSITION_LABEL[item.position] : null
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onInsert?.(filled)}
                disabled={!onInsert}
                title={item.description || item.name}
                className={`rounded-2xl border bg-white p-3 text-left transition-all ${
                  onInsert
                    ? "hover:border-saffron hover:bg-saffron/5 hover:shadow-soft cursor-pointer"
                    : "cursor-default"
                }`}
              >
                <div className="flex items-center justify-center h-12 rounded-xl bg-sand/20 border border-sand/50">
                  <span className={`font-bali ${compact ? "text-2xl" : "text-3xl"} leading-none`}>
                    {filled}
                  </span>
                </div>
                <div className="mt-2 text-sm font-semibold text-deep-brown">{item.name}</div>
                <div className="text-[11px] text-charcoal/50">
                  {item.latin_effect && <span>{item.latin_effect}</span>}
                  {pos && <span> · {pos}</span>}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {onInsert && (
        <p className="text-[11px] text-charcoal/45 leading-relaxed">
          Klik sebuah pangangge untuk menyisipkan bentuk terisi ke teks aksara — sama seperti
          mengisi angka ke dalam formula pangkat/kurung.
        </p>
      )}
    </div>
  )
}
