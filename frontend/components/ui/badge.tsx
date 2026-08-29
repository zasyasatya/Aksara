import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "success" | "warning" | "outline" | "saffron"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "bg-sand text-deep-brown",
    success: "bg-sage text-white",
    warning: "bg-amber-100 text-amber-800",
    outline: "border border-deep-brown text-deep-brown",
    saffron: "bg-saffron text-cream"
  }
  
  return (
    <div className={cn("inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold transition-colors", variants[variant], className)} {...props} />
  )
}

export { Badge }
