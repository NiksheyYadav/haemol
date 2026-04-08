"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { I18nextProvider } from "react-i18next";

import i18n from "@/lib/i18n";
import { useAppStore } from "@/lib/store";

export function Providers({ children }: { children: React.ReactNode }): JSX.Element {
  const [client] = useState(() => new QueryClient());
  const theme = useAppStore((state) => state.theme);
  const locale = useAppStore((state) => state.locale);

  useEffect(() => {
    document.body.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    void i18n.changeLanguage(locale);
  }, [locale]);

  return (
    <I18nextProvider i18n={i18n}>
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    </I18nextProvider>
  );
}
