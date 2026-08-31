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
 *
 * Disusun seperti keyboard sungguhan: dua baris Wresastra rapat + baris
 * pangangge, dengan umpan balik tekan (active) agar terasa interaktif.
 */
export function AksaraKeyboard({ onInsert, onBackspace, compact = false }: AksaraKeyboardProps) {
  const keySize = compact ? "h-11" : "h-14"
  const pangSize = compact ? "h-12" : "h-16"

  const wresastraKey = (item: { bali: string; latin: string }) => (
    <button
      key={item.latin}
      type="button"
      onClick={() => onInsert(item.bali)}
      title={`${item.latin} (${item.bali})`}
      className={`${keySize} select-none touch-manipulation rounded-lg bg-white border border-sand shadow-sm hover:border-saffron hover:bg-saffron/10 hover:text-saffron active:scale-95 active:bg-saffron/20 active:border-saffron transition-all duration-100 flex flex-col items-center justify-center cursor-pointer group`}
    >
      <span className={`font-bali ${compact ? "text-base" : "text-lg"} leading-none group-hover:scale-110 transition-transform`}>{item.bali}</span>
      <span className="text-[9px] font-medium leading-none mt-0.5 opacity-70">{item.latin}</span>
    </button>
  )

  const backspaceKey = (
    <button
      type="button"
      onClick={onBackspace}
      title="Hapus satu karakter"
      className={`${keySize} select-none touch-manipulation rounded-lg bg-terracotta/10 border border-terracotta/30 text-terracotta hover:bg-terracotta/20 active:scale-95 active:bg-terracotta/25 transition-all duration-100 flex items-center justify-center cursor-pointer`}
    >
      <Delete className="h-4 w-4" />
    </button>
  )

  return (
    <div className="space-y-2">
      <div className="rounded-2xl bg-sand/40 border border-sand p-2 space-y-1">
        <div className="mb-0.5 text-[10px] font-semibold uppercase tracking-wide text-charcoal/50 px-1">Wresastra 18</div>
        <div className="grid grid-cols-6 gap-1 sm:grid-cols-9">
          {WRESATRA.slice(0, 9).map(wresastraKey)}
        </div>
        <div className="grid grid-cols-6 gap-1 sm:grid-cols-10">
          {WRESATRA.slice(9).map(wresastraKey)}
          {onBackspace && backspaceKey}
        </div>
      </div>

      <div className="rounded-2xl bg-cream/70 border border-sand p-2 space-y-1">
        <div className="mb-0.5 text-[10px] font-semibold uppercase tracking-wide text-charcoal/50 px-1">Pangangge (tanda)</div>
        <div className="grid grid-cols-4 gap-1 sm:grid-cols-6">
          {PANGANGGE.map((item) => (
            <button
              key={item.name}
              type="button"
              onClick={() => onInsert(item.bali)}
              title={item.name}
              className={`${pangSize} select-none touch-manipulation rounded-lg bg-white border border-sand shadow-sm hover:border-saffron hover:bg-saffron/5 active:scale-95 active:bg-saffron/15 active:border-saffron transition-all duration-100 flex flex-col items-center justify-center p-0.5 cursor-pointer`}
            >
              <span className="font-bali text-base leading-none">{item.mark}</span>
              <span className="text-[8px] text-center leading-tight mt-0.5 opacity-70">{item.name}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="px-1.5 py-2 rounded-xl bg-ocean/5 border border-ocean/10 text-[11px] text-charcoal/70 flex items-start gap-1.5">
        <Sparkles className="h-3.5 w-3.5 text-ocean shrink-0 mt-0.5" />
        <span>
          Klik aksara dasar dulu, lalu panganggenya. Contoh: Ka + Ulu = Ki (ᬓ + ᬶ = ᬓᬶ).
          Untuk konsonan mati/gantungan, klik adeg (◌᭄) + aksara berikutnya.
        </span>
      </div>
    </div>
  )
}
