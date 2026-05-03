import type { Metadata } from "next";
import { IBM_Plex_Sans, IBM_Plex_Mono, Caveat, Permanent_Marker } from "next/font/google";
import "./globals.css";

const ibmSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-ibm-sans",
});

const ibmMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-ibm-mono",
});

export const metadata: Metadata = {
  title: "Foldables — Pharmacovigilance Signal Triage",
  description: "AI-powered adverse event signal detection and regulatory assessment for FDA FAERS — Metformin, Rofecoxib, Isotretinoin.",
};

const caveat = Caveat({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-caveat",
});

const marker = Permanent_Marker({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-marker",
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${ibmSans.variable} ${ibmMono.variable} ${caveat.variable} ${marker.variable}`}>
      <body className="min-h-full flex flex-col antialiased">
        {children}
      </body>
    </html>
  );
}
