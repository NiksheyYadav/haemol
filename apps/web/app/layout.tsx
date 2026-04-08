import type { Metadata } from "next";
import { IBM_Plex_Mono, Plus_Jakarta_Sans, Space_Grotesk } from "next/font/google";

import "./globals.css";
import { AppShell } from "@/components/app-shell";
import { Providers } from "@/components/providers";

const display = Space_Grotesk({ subsets: ["latin"], variable: "--font-display" });
const body = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-body" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], variable: "--font-mono", weight: ["400", "500"] });

export const metadata: Metadata = {
  title: "Biomarkly",
  description: "Biomarker-first blood report analysis with safer AI, multilingual audio, and patient-friendly review."
};

export default function RootLayout({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <html lang="en">
      <body className={`${display.variable} ${body.variable} ${mono.variable}`} data-theme="light">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
