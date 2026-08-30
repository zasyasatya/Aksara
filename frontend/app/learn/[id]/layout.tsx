import { readFileSync } from "node:fs"
import { join } from "node:path"
import type { ReactNode } from "react"
import type { Metadata } from "next"

/**
 * The production launcher exports the Next app as static files. Generate one
 * HTML page for every lesson ID from the backend catalogue, rather than
 * duplicating IDs in the frontend.
 */
export function generateStaticParams(): { id: string }[] {
  const catalogue = join(
    process.cwd(),
    "..",
    "backend",
    "app",
    "data",
    "lessons.json"
  )
  const lessons: unknown = JSON.parse(readFileSync(catalogue, "utf-8"))

  if (!Array.isArray(lessons)) {
    throw new Error("backend/app/data/lessons.json must contain a lesson array")
  }

  return lessons.flatMap((lesson) => {
    if (
      typeof lesson === "object" &&
      lesson !== null &&
      "id" in lesson &&
      typeof lesson.id === "string"
    ) {
      return [{ id: lesson.id }]
    }
    return []
  })
}

/** Metadata SEO per pelajaran (judul + deskripsi dari katalog backend). */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}): Promise<Metadata> {
  const { id: paramsId } = await params
  const fallback: Metadata = {
    title: `Pelajaran ${paramsId}`,
    description: "Pelajaran interaktif aksara Bali di AKSA.",
    alternates: { canonical: `/learn/${paramsId}` },
  }
  try {
    const catalogue = join(
      process.cwd(),
      "..",
      "backend",
      "app",
      "data",
      "lessons.json"
    )
    const lessons: unknown = JSON.parse(readFileSync(catalogue, "utf-8"))
    const lesson = (lessons as any[]).find((l) => l?.id === paramsId)
    if (!lesson) return fallback
    const title = `${lesson.title} — Belajar Aksara Bali di AKSA`
    const description = `${lesson.description ?? lesson.title} — pelajaran interaktif level ${lesson.level ?? "-"} di AKSA.`
    return {
      title,
      description,
      alternates: { canonical: `/learn/${paramsId}` },
      openGraph: {
        title,
        description,
        url: `/learn/${paramsId}`,
        type: "article",
      },
    }
  } catch {
    return fallback
  }
}

export const dynamicParams = false

export default function LessonLayout({ children }: { children: ReactNode }) {
  return children
}
