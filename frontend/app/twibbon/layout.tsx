import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Twibbon Aksara Bali — Studio Stiker Medsos Budaya",
  description:
    "Buat twibbon bertema Aksara Bali untuk Instagram dan media sosial: pilih bingkai budaya, tambahkan foto, dan bagikan untuk melestarikan aksara Bali.",
  alternates: { canonical: "/twibbon" },
  openGraph: {
    title: "Twibbon Aksara Bali — Studio Stiker Medsos Budaya",
    description: "Buat twibbon foto bertema aksara Bali, bagikan ke media sosial.",
    url: "/twibbon",
    type: "website",
  },
};

export default function TwibbonLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
