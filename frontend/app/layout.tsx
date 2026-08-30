import type { Metadata, Viewport } from "next";
import "./globals.css";

/** URL kanonik situs — dipakai Next untuk me-resolve canonical/OG relatif. */
const SITE_URL = "https://aksara.id";

const TITLE_DEFAULT = "Aksara Bali — Belajar, Translate & Tulis Aksara Bali Online";
const DESCRIPTION =
  "Platform interaktif belajar Aksara Bali: transliterasi Latin ↔ Aksara akurat, kuis menulis aksara, dan twibbon budaya. Melestarikan warisan, menulis masa depan.";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#2E1F12",
};

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: TITLE_DEFAULT,
    template: "%s | Aksara Bali",
  },
  description: DESCRIPTION,
  keywords: [
    "aksara",
    "aksara bali",
    "belajar aksara bali",
    "translate aksara bali",
    "transliterasi aksara bali",
    "konversi aksara bali",
    "hanacaraka",
    "wresastra",
    "swalalita",
    "tulisan bali",
    "aksara bali online",
  ],
  authors: [{ name: "Zasya Satya", url: "https://zasya.id" }],
  creator: "Zasya Satya",
  publisher: "Aksara",
  category: "education",
  alternates: {
    canonical: "/",
    languages: { id: "/", "x-default": "/" },
  },
  openGraph: {
    type: "website",
    locale: "id_ID",
    url: SITE_URL,
    siteName: "Aksara Bali",
    title: TITLE_DEFAULT,
    description: DESCRIPTION,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Aksara Bali — platform belajar, translate, dan tulis aksara Bali",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE_DEFAULT,
    description: DESCRIPTION,
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-image-preview": "large" },
  },
};

/**
 * Data terstruktur global (JSON-LD):
 * - WebSite + Organization: mengikat merek "Aksara" ke aksara.id
 * - Person: pengembang Zasya Satya (zasya.id) — membantu kaitan
 *   pencarian "zasya" → zasya.id.
 */
const JSONLD_GLOBAL = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}/#website`,
      url: SITE_URL,
      name: "Aksara Bali",
      description: DESCRIPTION,
      inLanguage: "id",
      publisher: { "@id": `${SITE_URL}/#org` },
      potentialAction: {
        "@type": "SearchAction",
        target: `${SITE_URL}/learn?q={search_term_string}`,
        "query-input": "required name=search_term_string",
      },
    },
    {
      "@type": "Organization",
      "@id": `${SITE_URL}/#org`,
      name: "Aksara",
      url: SITE_URL,
      logo: `${SITE_URL}/og-image.png`,
      sameAs: ["https://github.com/zasyasatya/Aksara"],
      founder: { "@id": `${SITE_URL}/#person` },
    },
    {
      "@type": "Person",
      "@id": `${SITE_URL}/#person`,
      name: "Zasya Satya",
      url: "https://zasya.id",
      sameAs: [
        "https://zasya.id",
        "https://github.com/zasyasatya",
        "https://github.com/zasyasatya/Aksara",
      ],
      jobTitle: "Developer & Pengembang Platform Aksara",
      knowsAbout: ["Aksara Bali", "Hanacaraka", "Pelestarian Budaya Bali", "Web Development"],
    },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(JSONLD_GLOBAL) }}
        />
      </head>
      <body className="min-h-screen overflow-x-hidden bg-cream text-deep-brown antialiased">
        {children}
      </body>
    </html>
  );
}
