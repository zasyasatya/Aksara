import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Translate Aksara Bali ↔ Latin Online — Transliterasi Akurat",
  description:
    "Terjemahkan teks Latin ke Aksara Bali dan sebaliknya secara online dengan mesin transliterasi akurat: gantungan, gempelan, tumpuk telu, dan pangangge lengkap. Bisa juga tulis aksara dengan tangan.",
  alternates: { canonical: "/translate" },
  openGraph: {
    title: "Translate Aksara Bali ↔ Latin Online — Transliterasi Akurat",
    description:
      "Konversi Latin ke Aksara Bali dan sebaliknya, plus pengenal tulisan tangan aksara. Gratis, akurat, langsung di peramban.",
    url: "/translate",
    type: "website",
  },
};

const JSONLD = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "SoftwareApplication",
      name: "Aksara Translate",
      url: "https://aksara.id/translate",
      applicationCategory: "EducationalApplication",
      operatingSystem: "Web",
      description:
        "Mesin transliterasi dua arah Latin ↔ Aksara Bali dengan penjelasan gantungan, gempelan, tumpuk telu, dan pangangge. Mendukung tulisan tangan aksara (on-device).",
      offers: { "@type": "Offer", price: "0", priceCurrency: "IDR" },
      featureList: [
        "Transliterasi Latin ke Aksara Bali",
        "Transliterasi Aksara Bali ke Latin",
        "Analisis gantungan, gempelan & tumpuk telu",
        "Pengenalan tulisan tangan aksara (offline/on-device)",
      ],
      provider: { "@type": "Organization", name: "Aksara", url: "https://aksara.id" },
    },
    {
      "@type": "FAQPage",
      mainEntity: [
        {
          "@type": "Question",
          name: "Mengapa menerjemahkan aksara Bali itu sulit?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Karena aksara Bali memakai sistem suku kata dengan aturan khusus: konsonan rangkap ditulis dengan gantungan (huruf kecil di bawah) atau gempelan (menempel), bukan bersebelahan; maksimal tiga lapis tumpuk (tumpuk telu); dan ada 11 jenis pangangge suara dengan posisi atas, bawah, depan, atau belakang.",
          },
        },
        {
          "@type": "Question",
          name: "Apakah translate aksara Bali ini gratis?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Ya, sepenuhnya gratis dan langsung berjalan di peramban tanpa perlu mendaftar atau menyimpan data.",
          },
        },
        {
          "@type": "Question",
          name: "Bagaimana cara menulis aksara Bali di translate?",
          acceptedAnswer: {
            "@type": "Answer",
            text: "Gunakan papan keyboard aksara virtual, ketik, atau tulis langsung dengan jari/mouse/pena di kanvas — sistem mengenali aksara Anda secara on-device tanpa internet.",
          },
        },
      ],
    },
  ],
};

export default function TranslateLayout({ children }: { children: ReactNode }) {
  return (
    <>
      {children}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(JSONLD) }}
      />
    </>
  );
}
