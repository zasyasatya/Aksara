/**
 * Pengecatan & klasifikasi tulisan tangan Aksara Bali — on-device.
 *
 * Pendekatan: template matching (AI lokal, tanpa API eksternal, bisa offline).
 * 1. Glyph target dirender dengan font "Noto Sans Balinese" ke canvas.
 * 2. Tulisan pengguna (canvas tinta) dan template dinormalisasi:
 *    crop bounding box -> skala ke kotak persegi -> biner (maska tinta).
 * 3. Skor = F1 dari coverage dua arah (berapa bagian bentuk terlengkapi &
 *    seberapa sedikit tinta liar).
 *
 * Dipakai:
 *  - Playground "Tulis Tangan": telusur siluet + klasifikasi benar/salah.
 *  - Translate "Tulis Tangan": kenali satu aksara yang ditulis.
 *
 * CATATAN: semua glyph di file ini dibangun dari codepoint Unicode
 * (String.fromCodePoint) — hindari mengetik glyph Balinese secara manual.
 */

const FONT_STACK = "'Noto Sans Balinese', 'Balinese', sans-serif"
const NORM_SIZE = 128 // ukuran maska normalisasi (px) — lebih besar = detail lebih baik
const INK_THRESHOLD = 200 // luminansi < nilai ini = tinta

/** Codepoint Aksara Bali (subset yang dipakai modul ini). */
export const BALI_CP = {
  ha: 0x1b33, na: 0x1b26, ca: 0x1b18, ra: 0x1b2d, ka: 0x1b13,
  da: 0x1b24, ta: 0x1b23, sa: 0x1b32, wa: 0x1b2f, la: 0x1b2e,
  ma: 0x1b2b, ga: 0x1b15, ba: 0x1b29, nga: 0x1b17, pa: 0x1b27,
  ja: 0x1b1a, ya: 0x1b2c, nya: 0x1b1c,
  ulu: 0x1b36, // i
  suku: 0x1b38, // u
} as const

export const baliGlyph = (name: keyof typeof BALI_CP): string => String.fromCodePoint(BALI_CP[name])

let fontReadyPromise: Promise<void> | null = null

/** Pastikan font Balinese termuat sebelum render glyph ke canvas. */
function ensureFont(px: number): Promise<void> {
  if (!fontReadyPromise) {
    fontReadyPromise = (async () => {
      try {
        await Promise.race([
          document.fonts.load(`600 ${px}px ${FONT_STACK}`),
          new Promise((r) => setTimeout(r, 2000)),
        ])
        await document.fonts.ready.catch(() => {})
      } catch {
        // fallback ke font sistem yang tersedia
      }
    })()
  }
  return fontReadyPromise
}

/** Render teks (1 glyph/segmen) ke canvas putih dengan font Balinese. */
export async function renderGlyphToCanvas(text: string, size = 320): Promise<HTMLCanvasElement> {
  await ensureFont(size * 0.6)
  const c = document.createElement("canvas")
  c.width = size
  c.height = size
  const ctx = c.getContext("2d")!
  ctx.fillStyle = "#ffffff"
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = "#000000"
  ctx.font = `600 ${Math.round(size * 0.58)}px ${FONT_STACK}`
  ctx.textAlign = "center"
  ctx.textBaseline = "middle"
  // geser sedikit ke bawah: glyph Balinese punya ascender tinggi (taleng)
  ctx.fillText(text, size / 2, size / 2 + size * 0.04)
  return c
}

interface Mask {
  data: Uint8Array
  size: number
}

/** Hitung bounding box tinta pada maska (w×h). */
function inkBounds(mask: Uint8Array, w: number, h: number): { x: number; y: number; w: number; h: number } | null {
  let minX = w, minY = h, maxX = -1, maxY = -1
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      if (mask[y * w + x]) {
        if (x < minX) minX = x
        if (x > maxX) maxX = x
        if (y < minY) minY = y
        if (y > maxY) maxY = y
      }
    }
  }
  if (maxX < 0) return null
  return { x: minX, y: minY, w: maxX - minX + 1, h: maxY - minY + 1 }
}

function toBinaryMaskOf(c: HTMLCanvasElement): { data: Uint8Array; w: number; h: number } {
  const w = c.width
  const h = c.height
  // Kanvas tinta pengguna boleh TRANSPARAN (background putih berasal dari
  // CSS container) — komposit ke putih dulu agar piksel transparan tidak
  // dianggap tinta. Ukuran asli, tanpa scaling (menghindari rentang aspect).
  const flat = document.createElement("canvas")
  flat.width = w
  flat.height = h
  const fctx = flat.getContext("2d")!
  fctx.fillStyle = "#ffffff"
  fctx.fillRect(0, 0, w, h)
  fctx.drawImage(c, 0, 0)
  const img = fctx.getImageData(0, 0, w, h)
  const data = new Uint8Array(w * h)
  for (let i = 0; i < w * h; i++) {
    const r = img.data[i * 4]
    const g = img.data[i * 4 + 1]
    const b = img.data[i * 4 + 2]
    const a = img.data[i * 4 + 3]
    const lum = (0.299 * r + 0.587 * g + 0.114 * b) * (a / 255)
    data[i] = lum < INK_THRESHOLD ? 1 : 0
  }
  return { data, w, h }
}

function toBinaryMask(c: HTMLCanvasElement, size: number): Mask {
  const { data } = toBinaryMaskOf(c)
  return { data, size }
}

/**
 * Normalisasi: crop bounding box tinta, skala (maintain aspect) ke dalam
 * kotak size×size terpusat, hasilkan maska biner.
 *
 * PENTING: bbox dihitung di koordinat asli canvas. Canvas sumber TIDAK
 * dibongkar ke probe persegi dulu — drawImage(src, 0, 0, probe, probe)
 * merentangkan kanvas non-persegi dan membuat crop meleset.
 */
export function normalizeToMask(src: HTMLCanvasElement, size = NORM_SIZE): Mask | null {
  const full = toBinaryMaskOf(src)
  const bounds = inkBounds(full.data, full.w, full.h)
  if (!bounds || bounds.w < 4 || bounds.h < 4) return null

  const scale = Math.min(size / bounds.w, size / bounds.h)
  const dw = Math.max(1, Math.round(bounds.w * scale))
  const dh = Math.max(1, Math.round(bounds.h * scale))
  const dx = Math.round((size - dw) / 2)
  const dy = Math.round((size - dh) / 2)

  const out = document.createElement("canvas")
  out.width = size
  out.height = size
  const ctx = out.getContext("2d")!
  ctx.fillStyle = "#ffffff"
  ctx.fillRect(0, 0, size, size)
  ctx.imageSmoothingEnabled = true
  ctx.drawImage(src, bounds.x, bounds.y, bounds.w, bounds.h, dx, dy, dw, dh)
  return toBinaryMask(out, size)
}

/**
 * Skor kemiripan dua maska via chamfer distance dua arah (px → 0..1).
 *
 * Berbeda dengan IoU/F1 (peka terhadap tebal stroke), chamfer mengukur jarak
 * rata-rata tiap piksel tinta ke bentuk terdekat pada maska lawan — sehingga
 * tulisan tangan dengan pena tebal tetap cocok dengan template font tipis,
 * selama bentuknya sama. Ini metrik standar untuk matching siluet/sketsa.
 */
function distanceTransform(mask: Mask): Float32Array {
  const s = mask.size
  const n = s * s
  const dist = new Float32Array(n).fill(1e9)
  const queue = new Int32Array(n)
  let head = 0
  let tail = 0
  for (let i = 0; i < n; i++) {
    if (mask.data[i]) {
      dist[i] = 0
      queue[tail++] = i
    }
  }
  while (head < tail) {
    const i = queue[head++]
    const x = i % s
    const y = (i / s) | 0
    const d = dist[i]
    // 8 tetangga (diagonal ≈ 1.414) — aproksimasi Euclidean
    for (let dy = -1; dy <= 1; dy++) {
      const ny = y + dy
      if (ny < 0 || ny >= s) continue
      for (let dx = -1; dx <= 1; dx++) {
        if (!dx && !dy) continue
        const nx = x + dx
        if (nx < 0 || nx >= s) continue
        const ni = ny * s + nx
        const nd = d + (dx !== 0 && dy !== 0 ? 1.4142 : 1)
        if (nd < dist[ni]) {
          dist[ni] = nd
          queue[tail++] = ni
        }
      }
    }
  }
  return dist
}

export function compareMasks(a: Mask, b: Mask): number {
  if (a.size !== b.size) return 0
  const da = distanceTransform(a)
  const db = distanceTransform(b)
  const n = a.size * a.size
  let sumA = 0
  let cntA = 0
  let sumB = 0
  let cntB = 0
  for (let i = 0; i < n; i++) {
    if (a.data[i]) {
      sumA += db[i]
      cntA++
    }
    if (b.data[i]) {
      sumB += da[i]
      cntB++
    }
  }
  if (!cntA || !cntB) return 0
  const avgPx = (sumA / cntA + sumB / cntB) / 2
  // Kalibrasi: 0px → 1.0; ~14% sisi maska → 0.0
  const scale = a.size * 0.14
  return Math.max(0, Math.min(1, 1 - avgPx / scale))
}

export interface TraceResult {
  score: number
  correct: boolean
  close: boolean
}

/**
 * Klasifikasi telusur siluet: bandingkan tinta pengguna dengan glyph target.
 * `correct` = bentuk terlengkapi dengan baik; `close` = hampir.
 */
export async function classifyTracing(inkCanvas: HTMLCanvasElement, targetGlyph: string): Promise<TraceResult> {
  const templateCanvas = await renderGlyphToCanvas(targetGlyph, 320)
  const a = normalizeToMask(inkCanvas)
  const b = normalizeToMask(templateCanvas)
  if (!a || !b) return { score: 0, correct: false, close: false }
  const score = compareMasks(a, b)
  // Ambang lebih ketat: hanya bentuk yang jelas terlengkapi dianggap benar.
  return { score, correct: score >= 0.55, close: score >= 0.35 }
}

/** Cache maska template per glyph — template konstan per sesi, jangan render ulang. */
const templateMaskCache = new Map<string, Mask | null>()

async function getTemplateMask(ch: string): Promise<Mask | null> {
  if (templateMaskCache.has(ch)) return templateMaskCache.get(ch) ?? null
  const t = await renderGlyphToCanvas(ch, 320)
  const m = normalizeToMask(t)
  templateMaskCache.set(ch, m)
  return m
}

export interface RecognitionResult {
  char: string
  score: number
  second: { char: string; score: number } | null
  confident: boolean
}

/**
 * Kenali glyph yang ditulis bebas dari kandidat.
 * confident = kandidat terbaik skor memadai & unggul jelas dari kandidat kedua.
 */
export async function recognizeAksara(
  inkCanvas: HTMLCanvasElement,
  candidates: string[]
): Promise<RecognitionResult> {
  const a = normalizeToMask(inkCanvas)
  if (!a) return { char: "", score: 0, second: null, confident: false }

  const scored: { char: string; score: number }[] = []
  for (const ch of candidates) {
    const b = await getTemplateMask(ch)
    if (!b) continue
    scored.push({ char: ch, score: compareMasks(a, b) })
  }
  scored.sort((x, y) => y.score - x.score)
  const best = scored[0]
  const second = scored[1] ?? null
  if (!best) return { char: "", score: 0, second: null, confident: false }
  // confident = skor memadai DAN unggul jelas dari kandidat kedua.
  // Chamfer: jejak baik ≈ 0.75-0.95; bukan-aksara ≈ < 0.5.
  const confident = best.score >= 0.55 && (!second || best.score - second.score >= 0.07)
  return { char: best.char, score: best.score, second, confident }
}

/**
 * Kandidat untuk pengenalan satu aksara: 18 Wresastra + vokal i/u tiap basis.
 * Urutan wesa: ha na ca ra ka da ta sa wa la ma ga ba nga pa ja ya nya.
 */
export function buildCandidateSet(): string[] {
  const order = ["ha", "na", "ca", "ra", "ka", "da", "ta", "sa", "wa", "la", "ma", "ga", "ba", "nga", "pa", "ja", "ya", "nya"]
  const bases = order.map((n) => baliGlyph(n as keyof typeof BALI_CP))
  const set = [...bases]
  for (const b of bases) {
    set.push(b + baliGlyph("ulu"))
    set.push(b + baliGlyph("suku"))
  }
  return set
}
