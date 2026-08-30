"use client"

import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react"

export interface HandwritingCanvasHandle {
  clear: () => void
  undo: () => void
  getInkCanvas: () => HTMLCanvasElement | null
  isEmpty: () => boolean
}

interface Point {
  x: number
  y: number
}

export interface HandwritingCanvasProps {
  /** Glyph siluet yang ditelusuri (di-render dengan font Balinese). */
  ghost?: string | null
  /** Resolusi internal canvas (CSS tetap responsif). */
  width?: number
  height?: number
  strokeColor?: string
  strokeWidth?: number
  onInkChange?: (hasInk: boolean) => void
  className?: string
}

/**
 * Kanvas menulis tangan untuk Aksara Bali.
 *
 * - Dua canvas bertumpuk: bawah = siluet ghost, atas = tinta pengguna.
 * - Pointer Events → mouse, sentuhan, dan stylus berjalan semua;
 *   `touch-action: none` agar geser tidak jadi scroll.
 * - Undo per-stroke; `getInkCanvas()` mengekspos tinta untuk klasifikasi.
 */
export const HandwritingCanvas = forwardRef<HandwritingCanvasHandle, HandwritingCanvasProps>(
  function HandwritingCanvas(
    {
      ghost = null,
      width = 480,
      height = 320,
      strokeColor = "#1c1917",
      strokeWidth = 9,
      onInkChange,
      className = "",
    },
    ref
  ) {
    const ghostRef = useRef<HTMLCanvasElement>(null)
    const inkRef = useRef<HTMLCanvasElement>(null)
    const strokesRef = useRef<Point[][]>([])
    const currentRef = useRef<Point[]>([])
    const drawingRef = useRef(false)

    const [hasInk, setHasInk] = useState(false)

    const notifyInk = useCallback(
      (ink: boolean) => {
        setHasInk(ink)
        onInkChange?.(ink)
      },
      [onInkChange]
    )

    /** Gambar ulang seluruh tinta dari daftar stroke (untuk undo). */
    const redraw = useCallback(() => {
      const c = inkRef.current
      if (!c) return
      const ctx = c.getContext("2d")!
      ctx.clearRect(0, 0, c.width, c.height)
      ctx.lineCap = "round"
      ctx.lineJoin = "round"
      ctx.strokeStyle = strokeColor
      ctx.lineWidth = strokeWidth
      for (const stroke of strokesRef.current) {
        if (stroke.length === 0) continue
        if (stroke.length < 3) {
          // titik / goresan sangat pendek
          ctx.beginPath()
          ctx.arc(stroke[0].x, stroke[0].y, strokeWidth / 2, 0, Math.PI * 2)
          ctx.fillStyle = strokeColor
          ctx.fill()
          continue
        }
        ctx.beginPath()
        ctx.moveTo(stroke[0].x, stroke[0].y)
        for (let i = 1; i < stroke.length - 1; i++) {
          const midX = (stroke[i].x + stroke[i + 1].x) / 2
          const midY = (stroke[i].y + stroke[i + 1].y) / 2
          ctx.quadraticCurveTo(stroke[i].x, stroke[i].y, midX, midY)
        }
        const last = stroke[stroke.length - 1]
        ctx.lineTo(last.x, last.y)
        ctx.stroke()
      }
    }, [strokeColor, strokeWidth])

    /** Render siluet ghost (setelah font siap). */
    const renderGhost = useCallback(() => {
      const c = ghostRef.current
      if (!c) return
      const ctx = c.getContext("2d")!
      ctx.clearRect(0, 0, c.width, c.height)
      if (!ghost) return
      const render = () => {
        const g = ctx
        g.fillStyle = "#ffffff"
        g.fillRect(0, 0, c.width, c.height)
        g.font = `600 ${Math.round(c.height * 0.56)}px 'Noto Sans Balinese', 'Balinese', sans-serif`
        g.textAlign = "center"
        g.textBaseline = "middle"
        // isian samar + garis luar tipis agar mudah ditelusur
        g.fillStyle = "rgba(120, 113, 108, 0.10)"
        g.fillText(ghost, c.width / 2, c.height / 2 + c.height * 0.03)
        g.strokeStyle = "rgba(120, 113, 108, 0.28)"
        g.lineWidth = 1.5
        g.strokeText(ghost, c.width / 2, c.height / 2 + c.height * 0.03)
      }
      if (document.fonts?.ready) {
        document.fonts.ready.then(render).catch(render)
      } else {
        render()
      }
    }, [ghost])

    useEffect(() => {
      renderGhost()
    }, [renderGhost, width, height])

    const getPos = (e: React.PointerEvent<HTMLCanvasElement>): Point => {
      const c = inkRef.current!
      const rect = c.getBoundingClientRect()
      return {
        x: ((e.clientX - rect.left) / rect.width) * c.width,
        y: ((e.clientY - rect.top) / rect.height) * c.height,
      }
    }

    const handlePointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
      e.preventDefault()
      const c = inkRef.current
      if (!c) return
      try {
        c.setPointerCapture(e.pointerId)
      } catch {
        // synthetic pointer event (mis. test) — aman dilewati
      }
      drawingRef.current = true
      currentRef.current = [getPos(e)]
    }

    const handlePointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
      if (!drawingRef.current) return
      e.preventDefault()
      const c = inkRef.current
      if (!c) return
      const ctx = c.getContext("2d")!
      const pos = getPos(e)
      const pts = currentRef.current
      const prev = pts[pts.length - 1]
      ctx.lineCap = "round"
      ctx.lineJoin = "round"
      ctx.strokeStyle = strokeColor
      ctx.lineWidth = strokeWidth
      ctx.beginPath()
      ctx.moveTo(prev.x, prev.y)
      ctx.lineTo(pos.x, pos.y)
      ctx.stroke()
      pts.push(pos)
    }

    const endStroke = (e: React.PointerEvent<HTMLCanvasElement>) => {
      if (!drawingRef.current) return
      drawingRef.current = false
      try {
        inkRef.current?.releasePointerCapture(e.pointerId)
      } catch {
        // abaikan
      }
      if (currentRef.current.length > 0) {
        strokesRef.current.push(currentRef.current)
        notifyInk(true)
      }
      currentRef.current = []
    }

    const clear = useCallback(() => {
      strokesRef.current = []
      currentRef.current = []
      const c = inkRef.current
      if (c) c.getContext("2d")?.clearRect(0, 0, c.width, c.height)
      notifyInk(false)
    }, [notifyInk])

    const undo = useCallback(() => {
      strokesRef.current.pop()
      redraw()
      notifyInk(strokesRef.current.length > 0)
    }, [redraw, notifyInk])

    useImperativeHandle(ref, () => ({
      clear,
      undo,
      getInkCanvas: () => inkRef.current,
      isEmpty: () => strokesRef.current.length === 0,
    }))

    return (
      <div
        className={`relative select-none overflow-hidden rounded-2xl border-2 border-dashed border-sand bg-white ${className}`}
        style={{ aspectRatio: `${width} / ${height}` }}
      >
        <canvas ref={ghostRef} width={width} height={height} className="absolute inset-0 h-full w-full" />
        <canvas
          ref={inkRef}
          width={width}
          height={height}
          className="absolute inset-0 h-full w-full cursor-crosshair"
          style={{ touchAction: "none" }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={endStroke}
          onPointerCancel={endStroke}
        />
        {!hasInk && !ghost && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-xs text-charcoal/30">
            Tulis di sini (sentuh, mouse, atau pena)
          </div>
        )}
      </div>
    )
  }
)
