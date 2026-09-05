/**
 * Palet warna aplikasi.
 *
 * Setiap palet memetakan token warna merek (saffron, deep-brown, cream, …)
 * ke nilai hex. Palet "native" adalah warna asli AKSA dan menjadi default.
 * Nilai diterapkan sebagai CSS variable `--c-*` (format "r g b") pada <html>
 * sehingga seluruh kelas Tailwind (bg-saffron, text-deep-brown, …) ikut berubah.
 *
 * Daftar ID harus selaras dengan backend/app/schemas/settings.py (THEME_IDS).
 */

export type ThemeTokens = {
  saffron: string
  "saffron-light": string
  "saffron-dark": string
  "deep-brown": string
  cream: string
  terracotta: string
  sage: string
  ocean: string
  sand: string
  charcoal: string
}

export type ThemeDef = {
  id: string
  name: string
  tagline: string
  tokens: ThemeTokens
}

export const DEFAULT_THEME_ID = "native"

export const THEMES: ThemeDef[] = [
  {
    id: "native",
    name: "Native — Saffron Nusantara",
    tagline: "Warna asli AKSA: jingga saffron, krem lontar, cokelat tua.",
    tokens: {
      saffron: "#FF6B35", "saffron-light": "#FF8C61", "saffron-dark": "#E55A2B",
      "deep-brown": "#2C1810", cream: "#FFF8E7", terracotta: "#C45A3C",
      sage: "#7A9E7E", ocean: "#2A6F8E", sand: "#F4E4BC", charcoal: "#1A1A1A",
    },
  },
  {
    id: "lontar",
    name: "Lontar — Emas Tua",
    tagline: "Krem gading & emas tembaga yang tenang, kesan naskah klasik.",
    tokens: {
      saffron: "#B8862B", "saffron-light": "#D4A84B", "saffron-dark": "#946A1D",
      "deep-brown": "#2B2118", cream: "#FBF7EE", terracotta: "#A5613A",
      sage: "#7C8F6E", ocean: "#3F6B7A", sand: "#EADFC8", charcoal: "#1F1A15",
    },
  },
  {
    id: "segara",
    name: "Segara — Biru Laut",
    tagline: "Biru laut dalam dan pasir pucat; modern, bersih, profesional.",
    tokens: {
      saffron: "#1F6F8B", "saffron-light": "#3A8FAB", "saffron-dark": "#175669",
      "deep-brown": "#14212B", cream: "#F6F9FB", terracotta: "#C2664A",
      sage: "#6E9E8A", ocean: "#2A6F8E", sand: "#DCE6EC", charcoal: "#131B21",
    },
  },
  {
    id: "pura",
    name: "Pura — Merah Bata",
    tagline: "Merah bata pura & abu hangat, elegan dan berwibawa.",
    tokens: {
      saffron: "#A6392F", "saffron-light": "#C4554A", "saffron-dark": "#862B23",
      "deep-brown": "#241514", cream: "#FAF5F1", terracotta: "#B5563E",
      sage: "#7B9377", ocean: "#3B5F7A", sand: "#EBDDD4", charcoal: "#1B1312",
    },
  },
  {
    id: "sawah",
    name: "Sawah — Hijau Subak",
    tagline: "Hijau zaitun & krem daun; segar, natural, menenangkan.",
    tokens: {
      saffron: "#4F7D4A", "saffron-light": "#6B9A66", "saffron-dark": "#3D6339",
      "deep-brown": "#1E2A1C", cream: "#F7F9F2", terracotta: "#B26B3C",
      sage: "#7A9E7E", ocean: "#2F6E7E", sand: "#E1E8D3", charcoal: "#171F16",
    },
  },
  {
    id: "candi",
    name: "Candi — Monokrom Arang",
    tagline: "Arang, batu, dan putih tulang; minimalis dengan aksen tembaga.",
    tokens: {
      saffron: "#8D6B4B", "saffron-light": "#A8896B", "saffron-dark": "#6F5238",
      "deep-brown": "#1C1B1A", cream: "#F8F7F4", terracotta: "#A05A45",
      sage: "#7B8C7A", ocean: "#4A6478", sand: "#E4E0D8", charcoal: "#151414",
    },
  },
]

export const THEME_IDS = THEMES.map((t) => t.id)

export function getTheme(id: string | null | undefined): ThemeDef {
  return THEMES.find((t) => t.id === id) ?? THEMES[0]
}

export function hexToRgbTriplet(hex: string): string {
  const h = hex.replace("#", "")
  const n = parseInt(h.length === 3 ? h.split("").map((c) => c + c).join("") : h, 16)
  return `${(n >> 16) & 255} ${(n >> 8) & 255} ${n & 255}`
}

/** Terapkan palet ke <html> (CSS variables + data-theme). */
export function applyTheme(id: string) {
  if (typeof document === "undefined") return
  const theme = getTheme(id)
  const root = document.documentElement
  root.dataset.theme = theme.id
  for (const [k, v] of Object.entries(theme.tokens)) {
    root.style.setProperty(`--c-${k}`, hexToRgbTriplet(v))
  }
  root.style.setProperty("--c-saffron-hex", theme.tokens.saffron)
  root.style.setProperty("--c-terracotta-hex", theme.tokens.terracotta)
  root.style.setProperty("--c-sage-hex", theme.tokens.sage)
  root.style.setProperty("--c-ocean-hex", theme.tokens.ocean)
  root.style.setProperty("--c-cream-hex", theme.tokens.cream)
  root.style.setProperty("--c-sand-hex", theme.tokens.sand)
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) meta.setAttribute("content", theme.tokens["deep-brown"])
}

export const THEME_STORAGE_KEY = "aksara-theme"

/** Skrip inline (dijalankan sebelum hidrasi) agar tidak terjadi kedipan palet. */
export function themeBootScript(): string {
  const map: Record<string, ThemeTokens> = {}
  for (const t of THEMES) map[t.id] = t.tokens
  return `(function(){try{var id=localStorage.getItem(${JSON.stringify(THEME_STORAGE_KEY)});var T=${JSON.stringify(map)};var t=T[id];if(!t||id===${JSON.stringify(DEFAULT_THEME_ID)})return;var r=document.documentElement;r.dataset.theme=id;function rgb(h){h=h.slice(1);var n=parseInt(h,16);return ((n>>16)&255)+" "+((n>>8)&255)+" "+(n&255)}for(var k in t){r.style.setProperty("--c-"+k,rgb(t[k]))}["saffron","terracotta","sage","ocean","cream","sand"].forEach(function(k){r.style.setProperty("--c-"+k+"-hex",t[k])})}catch(e){}})();`
}
