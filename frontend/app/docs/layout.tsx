import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Dokumentasi — Panduan Murid, Guru, Admin & Metode",
  description:
    "Panduan lengkap platform AKSA: cara penggunaan untuk murid, guru, dan admin, serta metode ilmiah di balik mesin transliterasi aksara Bali.",
  alternates: { canonical: "/docs" },
  openGraph: {
    title: "Dokumentasi Platform AKSA",
    description:
      "Panduan penggunaan (murid/guru/admin) dan dokumentasi metode ilmiah transliterasi.",
    url: "/docs",
    type: "website",
  },
};

export default function DocsLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
