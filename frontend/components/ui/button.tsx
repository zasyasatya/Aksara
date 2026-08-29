import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "outline"
  size?: "sm" | "md" | "lg" | "icon"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    const base = "inline-flex items-center justify-center rounded-full font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-saffron disabled:opacity-50 disabled:pointer-events-none"
    
    const variants = {
      primary: "bg-saffron text-cream hover:bg-saffron-dark shadow-soft hover:shadow-medium hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98]",
      secondary: "bg-deep-brown text-cream hover:bg-charcoal shadow-soft",
      ghost: "bg-transparent text-deep-brown hover:bg-sand",
      outline: "border-2 border-deep-brown text-deep-brown hover:bg-deep-brown hover:text-cream"
    }
    
    const sizes = {
      sm: "h-9 px-4 text-sm",
      md: "h-12 px-6 text-base",
      lg: "h-14 px-8 text-lg",
      icon: "h-10 w-10"
    }
    
    return (
      <button
        className={cn(base, variants[variant], sizes[size], className)}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
