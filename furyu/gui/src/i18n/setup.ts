import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createInstance, type i18n } from "i18next";

const here = dirname(fileURLToPath(import.meta.url));

export const NAMESPACES = ["onboarding", "errors"] as const;
export type CatalogLanguage = "pt-BR" | "en";

function loadCatalog(language: CatalogLanguage, namespace: string) {
  const file = join(here, "locales", language, `${namespace}.json`);
  return JSON.parse(readFileSync(file, "utf8")) as Record<string, unknown>;
}

function resources() {
  const languages: CatalogLanguage[] = ["en", "pt-BR"];
  return Object.fromEntries(
    languages.map((language) => [
      language,
      Object.fromEntries(
        NAMESPACES.map((namespace) => [namespace, loadCatalog(language, namespace)]),
      ),
    ]),
  );
}

/** i18next com JSON por namespace, no mesmo desenho do Roo. O padrão desta fatia é pt-BR. */
export async function setupI18n(language: CatalogLanguage = "pt-BR"): Promise<i18n> {
  const instance = createInstance();
  await instance.init({
    lng: language,
    fallbackLng: "en",
    supportedLngs: ["pt-BR", "en"],
    ns: [...NAMESPACES],
    defaultNS: "onboarding",
    resources: resources(),
    interpolation: { escapeValue: false },
    returnNull: false,
  });
  return instance;
}
