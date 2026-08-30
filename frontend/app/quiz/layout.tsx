import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Kuis Aksara Bali — Latihan Menulis & Menguji Hafalan",
  description:
    "Latih hafalan aksara Bali dengan kuis interaktif: pilihan ganda, benar/salah, gantungan, dan menulis aksara yang dinilai otomatis. Kumpulkan XP!",
  alternates: { canonical: "/quiz" },
  openGraph: {
    title: "Kuis Aksara Bali — Latihan Menulis & Menguji Hafalan",
    description: "Kuis interaktif aksara Bali dengan penilaian otomatis dan sistem XP.",
    url: "/quiz",
    type: "website",
  },
};

export default function QuizLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
