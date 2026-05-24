import type { Metadata } from "next";
import { Inter, Newsreader } from "next/font/google";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const newsreader = Newsreader({ subsets: ["latin"], variable: "--font-newsreader" });

export const metadata: Metadata = {
  title: {
    default: "Pulso Fiscal",
    template: "%s | Pulso Fiscal",
  },
  description: "Datos publicos claros para revisar gastos del Estado de Chile.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es" className={`${inter.variable} ${newsreader.variable}`}>
      <body className="font-sans antialiased">
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
