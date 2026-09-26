import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import enErrors from "./locales/en/errors.json";
import enOnboarding from "./locales/en/onboarding.json";
import ptErrors from "./locales/pt-BR/errors.json";
import ptOnboarding from "./locales/pt-BR/onboarding.json";

export const FURYU_NAMESPACES = ["onboarding", "errors"] as const;

void i18n.use(initReactI18next).init({
  lng: "pt-BR",
  fallbackLng: "en",
  supportedLngs: ["pt-BR", "en"],
  ns: [...FURYU_NAMESPACES],
  defaultNS: "onboarding",
  resources: {
    en: { onboarding: enOnboarding, errors: enErrors },
    "pt-BR": { onboarding: ptOnboarding, errors: ptErrors },
  },
  interpolation: { escapeValue: false },
  returnNull: false,
});

export default i18n;
