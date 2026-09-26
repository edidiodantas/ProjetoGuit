import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { setupI18n } from "../gui/src/i18n/setup.ts";
import {
  localOnboardingCopy,
  loginCopy,
  splashCopy,
} from "../gui/src/pages/onboarding/screens.ts";

const root = join(dirname(fileURLToPath(import.meta.url)), "../gui/src/i18n/locales");

function keysOf(value: unknown, prefix = ""): string[] {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return [prefix];
  }
  return Object.entries(value as Record<string, unknown>).flatMap(([key, child]) =>
    keysOf(child, prefix ? `${prefix}.${key}` : key),
  );
}

test("en e pt-BR têm as mesmas chaves de onboarding e errors", () => {
  for (const namespace of ["onboarding", "errors"]) {
    const english = JSON.parse(readFileSync(join(root, "en", `${namespace}.json`), "utf8"));
    const portuguese = JSON.parse(
      readFileSync(join(root, "pt-BR", `${namespace}.json`), "utf8"),
    );
    assert.deepEqual(keysOf(portuguese).sort(), keysOf(english).sort());
  }
});

test("o catálogo pt-BR cobre splash, onboarding e o erro do Ollama", async () => {
  const i18n = await setupI18n("pt-BR");
  const t = i18n.t.bind(i18n);

  assert.equal(t("onboarding:splash.useOnThisComputer"), "Usar neste computador");
  assert.equal(t("onboarding:splash.useOnlineModel"), "Usar um modelo online");
  assert.equal(
    t("errors:ollamaMissing"),
    "Modelo local não encontrado. Verifique se o Ollama está rodando ou mude para o modo Online.",
  );
  assert.equal(t("errors:switchToOnline"), "Mudar para o modo Online");

  const splash = splashCopy(t);
  const login = loginCopy(t);
  const local = localOnboardingCopy(t);
  assert.match(splash.title, /PearAI/);
  assert.match(login.submit, /Entrar/);
  assert.match(local.chatRecommendation, /llama3/);
  assert.match(local.autocompleteRecommendation, /starcoder2:3b/);
  assert.match(local.embeddingsRecommendation, /nomic-embed-text/);
});

test("inglês permanece disponível no mesmo catálogo", async () => {
  const i18n = await setupI18n("en");
  assert.equal(i18n.t("onboarding:splash.useOnThisComputer"), "Use on this computer");
  assert.match(i18n.t("errors:connectionRefused"), /Connection was refused/);
  assert.match(i18n.t("errors:timeout"), /Connection timed out/);
});
