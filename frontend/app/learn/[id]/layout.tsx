import { readFileSync } from "node:fs"
import { join } from "node:path"
import type { ReactNode } from "react"

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

export const dynamicParams = false

export default function LessonLayout({ children }: { children: ReactNode }) {
  return children
}
