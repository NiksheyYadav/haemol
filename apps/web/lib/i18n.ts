"use client";

import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "@biomarkly/locales/en/common.json";
import hi from "@biomarkly/locales/hi/common.json";

if (!i18n.isInitialized) {
  void i18n.use(initReactI18next).init({
    resources: {
      en: { common: en },
      hi: { common: hi }
    },
    fallbackLng: "en",
    lng: "en",
    ns: ["common"],
    defaultNS: "common",
    interpolation: { escapeValue: false }
  });
}

export default i18n;
