"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { useProgressStore } from "@/lib/store"
import { Flame, Trophy, BookOpen, BookOpenCheck, Languages, LayoutDashboard, Gamepad2, PenSquare, Stamp, ShieldCheck, FlaskConical } from "lucide-react"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/learn", label: "Belajar", icon: BookOpen },
  { href: "/translate", label: "Translate", icon: Languages },
  { href: "/playground", label: "Play", icon: FlaskConical },
  { href: "/quiz", label: "Kuis", icon: Gamepad2 },
  { href: "/twibbon", label: "Twibbon", icon: Stamp },
  { href: "/guru", label: "Guru", icon: PenSquare },
  { href: "/docs", label: "Dokumentasi", icon: BookOpenCheck },
]

export function Header() {
  const pathname = usePathname()
  const { xp, streak, level } = useProgressStore()
  
  return (
    <header className="sticky top-0 z-50 w-full border-b border-sand bg-cream/80 backdrop-blur-xl">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 lg:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-saffron to-terracotta text-cream font-bali text-xl font-bold shadow-soft">
              ᬅ
            </div>
            <div className="hidden sm:block">
              <div className="font-display font-bold text-lg leading-none">AKSARA</div>
              <div className="text-[10px] tracking-widest text-deep-brown/60 -mt-1">BALINESE SCRIPT</div>
            </div>
          </Link>
          
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname?.startsWith(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all",
                    isActive ? "bg-deep-brown text-cream shadow-soft" : "text-deep-brown/70 hover:bg-sand hover:text-deep-brown"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 rounded-full bg-white border border-sand px-3 py-1.5 shadow-soft">
            <div className="flex items-center gap-1.5">
              <Flame className="h-4 w-4 text-saffron" />
              <span className="text-sm font-bold">{streak}</span>
            </div>
            <div className="h-4 w-px bg-sand" />
            <div className="flex items-center gap-1.5">
              <Trophy className="h-4 w-4 text-amber-500" />
              <span className="text-sm font-bold">{xp}</span>
            </div>
            <div className="h-4 w-px bg-sand" />
            <div className="text-xs font-medium bg-deep-brown text-cream rounded-full px-2 py-0.5">
              Lv {level}
            </div>
          </div>
          
          <Link
            href="/guru"
            title="Panel Guru"
            aria-label="Panel Guru"
            className="flex sm:hidden h-9 w-9 items-center justify-center rounded-full border border-sand bg-white text-deep-brown/60 shadow-soft transition-colors hover:text-saffron-dark hover:border-saffron/40"
          >
            <PenSquare className="h-5 w-5" />
          </Link>
          <Link
            href="/admin"
            title="Panel Admin"
            aria-label="Panel Admin"
            className="hidden sm:flex h-9 w-9 items-center justify-center rounded-full border border-sand bg-white text-deep-brown/60 shadow-soft transition-colors hover:text-saffron-dark hover:border-saffron/40"
          >
            <ShieldCheck className="h-5 w-5" />
          </Link>
          
          <Button variant="primary" size="sm" className="hidden sm:inline-flex">
            Rahajeng! 👋
          </Button>
        </div>
      </div>
    </header>
  )
}
