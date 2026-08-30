import { DocsArticleClient } from "./client"

export function generateStaticParams() {
  return [
    "penggunaan-murid",
    "penggunaan-guru",
    "penggunaan-admin",
    "metode-scientific",
  ].map((slug) => ({ slug }))
}

export default function DocsArticlePage() {
  return <DocsArticleClient />
}
