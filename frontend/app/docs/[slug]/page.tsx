import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Metadata } from "next";
import { DocsArticleClient } from "./client";

export function generateStaticParams() {
  return [
    "penggunaan-murid",
    "penggunaan-guru",
    "penggunaan-admin",
    "metode-scientific",
    "dataset-dan-model",
    "panduan-retraining",
  ].map((slug) => ({ slug }))
}

/** Metadata SEO per artikel dari katalog dokumen backend (dibaca saat build). */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const slug = (await params).slug
  const fallback: Metadata = {
    title: `Dokumentasi: ${slug}`,
    description: "Dokumentasi platform AKSA.",
    alternates: { canonical: `/docs/${slug}` },
  }
  try {
    const catalogue = join(
      process.cwd(),
      "..",
      "backend",
      "app",
      "data",
      "docs.json"
    )
    const raw: unknown = JSON.parse(readFileSync(catalogue, "utf-8"))
    const pages: { slug: string; title: string; subtitle: string }[] = Array.isArray(raw)
      ? (raw as any[])
      : ((raw as any)?.pages ?? [])
    const page = pages.find((p) => p?.slug === slug)
    if (!page) return fallback
    const description = `${page.subtitle} — dokumentasi resmi platform AKSA.`
    return {
      title: page.title,
      description,
      alternates: { canonical: `/docs/${slug}` },
      openGraph: {
        title: `${page.title} | AKSA`,
        description,
        url: `/docs/${slug}`,
        type: "article",
      },
    }
  } catch {
    return fallback
  }
}

export default function DocsArticlePage() {
  return <DocsArticleClient />
}
