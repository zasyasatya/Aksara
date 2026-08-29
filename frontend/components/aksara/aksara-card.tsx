"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface AksaraCardProps {
  bali: string
  latin: string
  name: string
  type?: string
  description?: string
  selected?: boolean
  onClick?: () => void
  size?: "sm" | "md" | "lg"
  showType?: boolean
}

export function AksaraCard({ bali, latin, name, type, description, selected, onClick, size = "md", showType = true }: AksaraCardProps) {
  const sizes = {
    sm: { card: "p-3", bali: "text-2xl", latin: "text-xs" },
    md: { card: "p-4", bali: "text-4xl", latin: "text-sm" },
    lg: { card: "p-6", bali: "text-6xl", latin: "text-base" }
  }
  
  const s = sizes[size]
  
  return (
    <Card
      className={cn(
        "patra-border cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:shadow-large group",
        selected ? "ring-2 ring-saffron border-saffron bg-saffron/5" : "bg-white",
        s.card
      )}
      onClick={onClick}
    >
      <div className="flex flex-col items-center text-center gap-2">
        <div className={cn("font-bali font-bold text-deep-brown group-hover:scale-110 transition-transform duration-300", s.bali)}>
          {bali}
        </div>
        <div className="flex flex-col gap-1">
          <div className={cn("font-semibold text-deep-brown", s.latin)}>
            {latin}
          </div>
          <div className="text-xs text-charcoal/60 font-medium">
            {name}
          </div>
        </div>
        {showType && type && (
          <Badge variant="default" className="mt-1 text-[10px]">
            {type}
          </Badge>
        )}
      </div>
    </Card>
  )
}

export function AksaraGrid({ children, className }: { children: React.ReactNode, className?: string }) {
  return (
    <div className={cn("grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4", className)}>
      {children}
    </div>
  )
}
