import type { Metadata } from "next";
import type { Viewport } from "next";
import type { ReactNode } from "react";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "AfroLete",
  description: "AI-assisted sports operations and athlete development",
  manifest: "/manifest.webmanifest"
};

export const viewport: Viewport = {
  themeColor: "#111827"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
