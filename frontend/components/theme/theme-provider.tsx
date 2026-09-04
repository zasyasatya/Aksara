"use client"

import { useEffect } from "react"
import { api } from "@/lib/api"
import { applyTheme, DEFAULT_THEME_ID, THEME_STORAGE_KEY } from "@/lib/themes"

/**
 * Menyinkronkan palet warna global:
 * 1. Skrip inline di <head> sudah menerapkan palet dari localStorage (anti-flash).
 * 2. Komponen ini mengambil palet resmi dari backend (dipilih Admin) lalu
 *    menerapkannya + menyimpan ke localStorage untuk kunjungan berikutnya.
 */
export function ThemeProvider() {
  useEffect(() => {
    let cancelled = false
    api.settings
      .getTheme()
      .then((r) => {
        if (cancelled) return
        const id = r.theme || DEFAULT_THEME_ID
        applyTheme(id)
        try { localStorage.setItem(THEME_STORAGE_KEY, id) } catch {}
      })
      .catch(() => {
        // backend tak tersedia → tetap pakai palet dari localStorage / native
      })
    return () => { cancelled = true }
  }, [])
  return null
}
