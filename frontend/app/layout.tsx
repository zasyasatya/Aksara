import type { Metadata, Viewport } from "next";
import "./globals.css";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export const metadata: Metadata = {
  title: "Aksara - Platform Belajar Aksara Bali",
  description: "Melestarikan Warisan, Menulis Masa Depan. Platform interaktif belajar Aksara Bali dengan transliterasi canggih, quiz validasi, dan gamifikasi.",
  keywords: ["aksara bali", "hanacaraka", "belajar aksara", "bali", "transliterasi", "wresastra", "swalalita"],
  authors: [{ name: "Aksara Team" }],
  openGraph: {
    title: "Aksara - Platform Belajar Aksara Bali",
    description: "Platform interaktif belajar Aksara Bali",
    type: "website",
    locale: "id_ID",
  },
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
      </head>
      <body className="bg-cream text-deep-brown antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
