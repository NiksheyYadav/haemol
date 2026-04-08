"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";

import { useAppStore } from "@/lib/store";

export function AppShell({ children }: { children: React.ReactNode }): JSX.Element {
  const { t } = useTranslation();
  const theme = useAppStore((state) => state.theme);
  const locale = useAppStore((state) => state.locale);
  const setTheme = useAppStore((state) => state.setTheme);
  const setLocale = useAppStore((state) => state.setLocale);

  return (
    <>
      <div className="sticky-banner" style={{ borderBottom: "1px solid var(--border)", background: "rgba(255,255,255,0.75)" }}>
        <div className="shell" style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "center", padding: "0.9rem 0" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.8rem", flexWrap: "wrap" }}>
            <Link href="/" style={{ fontWeight: 800, fontSize: "1.1rem" }}>
              Biomarkly
            </Link>
            <span className="badge">{t("disclaimer.banner")}</span>
          </div>
          <nav style={{ display: "flex", alignItems: "center", gap: "0.65rem", flexWrap: "wrap" }} aria-label="Primary navigation">
            <Link href="/upload">{t("nav.upload")}</Link>
            <Link href="/about">{t("nav.about")}</Link>
            <Link href="/privacy">{t("nav.privacy")}</Link>
            <button aria-label="Toggle theme" className="button-ghost" onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
              {theme === "light" ? "Dark" : "Light"}
            </button>
            <button aria-label="Switch language" className="button-ghost" onClick={() => setLocale(locale === "en" ? "hi" : "en")}>
              {locale === "en" ? "हिंदी" : "EN"}
            </button>
          </nav>
        </div>
      </div>
      {children}
      <footer className="shell" style={{ padding: "0 0 3rem", color: "var(--text-muted)" }}>
        {t("disclaimer.emergency")}
      </footer>
    </>
  );
}
