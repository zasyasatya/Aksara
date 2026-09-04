"use client"

import {
  GraduationCap,
  Presentation,
  ShieldCheck,
  Microscope,
  Database,
  BookOpen,
  Brain,
  type LucideIcon,
} from "lucide-react"
import { DocsRole } from "@/lib/api"

export const IconByName: Record<string, LucideIcon> = {
  GraduationCap,
  Presentation,
  ShieldCheck,
  Microscope,
  Database,
  BookOpen,
  Brain,
}

export const docRoleMeta: Record<DocsRole, { label: string; badge: "saffron" | "outline" | "default" }> = {
  murid: { label: "Untuk Murid", badge: "saffron" },
  guru: { label: "Untuk Guru", badge: "saffron" },
  admin: { label: "Untuk Admin", badge: "saffron" },
  metodologi: { label: "Metodologi & Riset", badge: "saffron" },
}
