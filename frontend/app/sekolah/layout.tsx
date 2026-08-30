import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Sekolah Mitra — Ajak Sekolasmu Belajar Aksara Bali",
  description:
    "Daftarkan sekolahmu sebagai mitra program Aksara Bali. Gratis untuk sekolah: platform belajar aksara Bali siap pakai, selaras kebijakan aksara wajib di Bali.",
  alternates: { canonical: "/sekolah" },
  openGraph: {
    title: "Sekolah Mitra — Ajak Sekolasmu Belajar Aksara Bali",
    description: "Program kemitraan sekolah gratis untuk pembelajaran aksara Bali.",
    url: "/sekolah",
    type: "website",
  },
};

export default function SekolahLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
