"use client";

import { create } from "zustand";

type Theme = "light" | "dark";
type Locale = "en" | "hi";

interface AppState {
  theme: Theme;
  locale: Locale;
  pediatricAcknowledged: boolean;
  setTheme: (theme: Theme) => void;
  setLocale: (locale: Locale) => void;
  acknowledgePediatric: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  theme: "light",
  locale: "en",
  pediatricAcknowledged: false,
  setTheme: (theme) => set({ theme }),
  setLocale: (locale) => set({ locale }),
  acknowledgePediatric: () => set({ pediatricAcknowledged: true })
}));
