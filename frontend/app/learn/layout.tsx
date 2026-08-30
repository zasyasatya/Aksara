import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Belajar Aksara Bali — Pelajaran Interaktif Hanacaraka",
  description:
    "Belajar Aksara Bali langkah demi langkah: 11 pelajaran interaktif wresastra, swalalita, pangangge, dan gantungan dengan cerita Hanacaraka, kuis, dan sistem poin (XP).",
  alternates: { canonical: "/learn" },
  openGraph: {
    title: "Belajar Aksara Bali — Pelajaran Interaktif Hanacaraka",
    description:
      "Pelajaran interaktif bertingkat dengan cerita, kuis, dan gamifikasi — dari Ha Na Ca Ra Ka hingga gantungan.",
    url: "/learn",
    type: "website",
  },
};

export default function LearnLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
