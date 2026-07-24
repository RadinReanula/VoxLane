import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kubernetica Drive‑Thru",
  description: "Accessible, voice-first drive-thru ordering.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
