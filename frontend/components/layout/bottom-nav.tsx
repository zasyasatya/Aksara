"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { LayoutDashboard, BookOpen, BookOpenCheck, Languages, Gamepad2, Stamp, User } from "lucide-react"

const navItems = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/learn", label: "Belajar", icon: BookOpen },
  { href: "/translate", label: "Translate", icon: Languages },
  { href: "/quiz", label: "Kuis", icon: Gamepad2 },
  { href: "/twibbon", label: "Twibbon", icon: Stamp },
  { href: "/playground", label: "Play", icon: User },
  { href: "/docs", label: "Dok", icon: BookOpenCheck },
]

export function BottomNav() {
  const pathname = usePathname()
  
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-sand bg-cream/90 backdrop-blur-xl lg:hidden">
      <nav className="flex items-center justify-around px-2 py-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname?.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
          className={cn(
            "flex flex-col items-center gap-1 rounded-2xl px-2 py-2 text-xs font-medium transition-all",
            isActive ? "bg-deep-brown text-cream shadow-soft" : "text-deep-brown/60"
          )}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px]">{item.label}</span>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}
