import type { Metadata } from "next";
import type { ReactNode } from "react";

// Halaman privat/fungsional: tidak perlu diindeks mesin pencari.
export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default function PrivateLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
