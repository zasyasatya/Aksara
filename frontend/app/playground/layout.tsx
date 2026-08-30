import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Playground Aksara Bali — Eksperimen Transliterasi & Gantungan",
  description:
    "Coba langsung transliterasi dan validasi gantungan/gempelan aksara Bali: lihat hasil, penjelasan suku kata, dan aturan yang berlaku secara real-time.",
  alternates: { canonical: "/playground" },
  openGraph: {
    title: "Playground Aksara Bali — Eksperimen Transliterasi & Gantungan",
    description: "Coba transliterasi dan analisis gantungan aksara Bali secara interaktif.",
    url: "/playground",
    type: "website",
  },
};

export default function PlaygroundLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
