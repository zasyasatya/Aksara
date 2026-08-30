"use client"

import Image from "next/image"

interface ScreenshotProps {
  src: string
  alt: string
  caption: string
  url?: string
  height?: number
}

/**
 * Gambar screenshot berbingkai browser dengan caption — dipakai di semua
 * halaman dokumentasi agar konsisten.
 */
export function Screenshot({ src, alt, caption, url = "aksara.local", height = 420 }: ScreenshotProps) {
  return (
    <figure className="my-8">
      <div className="overflow-hidden rounded-2xl border border-sand bg-white shadow-medium">
        {/* Bar browser */}
        <div className="flex items-center gap-2 border-b border-sand bg-cream px-4 py-2.5">
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-terracotta/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-sage/80" />
          </div>
          <div className="ml-2 flex-1 truncate rounded-full bg-white border border-sand px-3 py-1 text-[11px] text-charcoal/50">
            {url}
          </div>
        </div>
        {/* Gambar */}
        <div className="relative w-full" style={{ height }}>
          <Image
            src={src}
            alt={alt}
            fill
            sizes="(max-width: 1024px) 100vw, 768px"
            style={{ objectFit: "cover", objectPosition: "top" }}
          />
        </div>
      </div>
      <figcaption className="mt-3 flex items-start gap-2 text-sm text-charcoal/60">
        <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-saffron/15 text-[10px] font-bold text-saffron-dark">
          i
        </span>
        {caption}
      </figcaption>
    </figure>
  )
}
