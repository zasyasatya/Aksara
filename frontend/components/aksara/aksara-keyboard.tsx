"use client"

import { Delete, Sparkles } from "lucide-react"

export const WRESATRA = [
  { bali: "ᬳ", latin: "ha" }, { bali: "ᬦ", latin: "na" }, { bali: "ᬘ", latin: "ca" }, { bali: "ᬭ", latin: "ra" }, { bali: "ᬓ", latin: "ka" },
  { bali: "ᬤ", latin: "da" }, { bali: "ᬢ", latin: "ta" }, { bali: "ᬲ", latin: "sa" }, { bali: "ᬯ", latin: "wa" }, { bali: "ᬮ", latin: "la" },
  { bali: "ᬫ", latin: "ma" }, { bali: "ᬕ", latin: "ga" }, { bali: "ᬩ", latin: "ba" }, { bali: "ᬗ", latin: "nga" }, { bali: "ᬧ", latin: "pa" },
  { bali: "ᬚ", latin: "ja" }, { bali: "ᬬ", latin: "ya" }, { bali: "ᬜ", latin: "nya" },
]

export const PANGANGGE = [
  { bali: "ᬶ", name: "ulu (i)", mark: "◌ᬶ" },
  { bali: "ᬸ", name: "suku (u)", mark: "◌ᬸ" },
  { bali: "ᬾ", name: "taleng (e)", mark: "◌ᬾ" },
  { bali: "ᭂ", name: "pepet (ě)", mark: "◌ᭂ" },
  { bali: "ᭀ", name: "tedong (ā/o)", mark: "◌ᭀ" },
  { bali: "ᬄ", name: "bisah (h)", mark: "◌ᬄ" },
  { bali: "ᬃ", name: "surang (r)", mark: "◌ᬃ" },
  { bali: "ᬂ", name: "cecek (ng)", mark: "◌ᬂ" },
  { bali: "᭄", name: "adeg (kill)", mark: "◌᭄" },
  { bali: "᭄ᬭ", name: "cakra (ra)", mark: "◌᭄ᬭ" },
  { bali: "᭄ᬬ", name: "nania (ya)", mark: "◌᭄ᬬ" },
]

interface AksaraKeyboardProps {
  onInsert: (char: string) => void
  onBackspace?: () => void
  /** ukuran lebih ringkas untuk panel form */
  compact?: boolean
}

/**
 * Keyboard virtual Aksara Bali — dipakai Playground, kuis menulis aksara,
 * halaman Translate, dan form Guru.
 */
export function AksaraKeyboard({ onInsert, onBackspace, compact = false }: AksaraKeyboardProps) {
  const keySize = compact ? "h-12" : "h-16"
  const pangSize = compact ? "h-14" : "h-20"

  return (
    <div className="space-y-4">
      <div>
        <div className="mb-2 text-xs font-semibold text-charcoal/50">Wresastra 18</div>
        <div className="grid grid-cols-6 gap-1.5 sm:grid-cols-9">
          {WRESATRA.map((item) => (
            <button
              key={item.latin}
              type="button"
              onClick={() => onInsert(item.bali)}
              className={`${keySize} rounded-xl bg-sand/30 border border-sand hover:border-saffron hover:bg-saffron/10 hover:text-saffron transition-all flex flex-col items-center justify-center group`}
            >
              <div className={`font-bali ${compact ? "text-base" : "text-xl"} group-hover:scale-110 transition-transform`}>{item.bali}</div>
              <div className="text-[9px] font-medium">{item.latin}</div>
            </button>
          ))}
          {onBackspace && (
            <button
              type="button"
              onClick={onBackspace}
              title="Hapus satu karakter"
              className={`${keySize} rounded-xl bg-terracotta/10 border border-terracotta/30 text-terracotta hover:bg-terracotta/20 transition-all flex items-center justify-center`}
            >
              <Delete className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>

      <div>
        <div className="mb-2 text-xs font-semibold text-charcoal/50">Pangangge (tanda)</div>
        <div className="grid grid-cols-4 gap-1.5 sm:grid-cols-6">
          {PANGANGGE.map((item) => (
            <button
              key={item.name}
              type="button"
              onClick={() => onInsert(item.bali)}
              className={`${pangSize} rounded-xl bg-cream border border-sand hover:border-saffron hover:bg-saffron/5 transition-all flex flex-col items-center justify-center p-1`}
            >
              <div className="font-bali text-base">{item.bali}</div>
              <div className="text-[9px] text-center leading-tight mt-0.5">{item.name}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="p-2.5 rounded-xl bg-ocean/5 border border-ocean/10 text-xs text-charcoal/70 flex items-start gap-1.5">
        <Sparkles className="h-3.5 w-3.5 text-ocean shrink-0 mt-0.5" />
        <span>
          Klik aksara dasar dulu, lalu panganggenya. Contoh: Ka + Ulu = Ki (ᬓ + ᬶ = ᬓᬶ).
          Untuk konsonan mati/gantungan, klik adeg (◌᭄) + aksara berikutnya.
        </span>
      </div>
    </div>
  )
}
