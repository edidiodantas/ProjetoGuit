import assert from "node:assert/strict";
import { test } from "node:test";
import { Telemetry } from "../core/util/telemetry.ts";
import { setupI18n } from "../gui/src/i18n/setup.ts";
import { chooseSplash, onboardingEntry, splashChoices } from "../gui/src/pages/welcome/splash.ts";
import type { ContinueConfigSlice } from "../core/config/furyu/localMode.ts";

const config = (): ContinueConfigSlice => ({
  models: [],
  allowAnonymousTelemetry: true,
});

test("splash oferece este computador antes do login, inclusive no overlay", async () => {
  const i18n = await setupI18n("pt-BR");
  const choices = splashChoices(i18n.t.bind(i18n));
  assert.deepEqual(
    choices.map((choice) => choice.label),
    ["Usar neste computador", "Usar um modelo online"],
  );
  assert.deepEqual(choices.map((choice) => choice.id), ["local", "online"]);
  assert.deepEqual(onboardingEntry(true), { screen: "splash" });
  assert.deepEqual(onboardingEntry(false), { screen: "splash" });
});

test("usar neste computador aplica o perfil local e não chama pearaiLogin", async () => {
  const posts: string[] = [];
  const result = await chooseSplash("local", {
    config: config(),
    embeddingModelAvailable: true,
    ideTelemetryEnabled: true,
    uniqueId: "machine",
    extensionVersion: "2.0.0",
    messenger: {
      post: (message) => posts.push(message),
    },
  });

  assert.equal(result.pearaiLogin, false);
  assert.equal(result.next, "local-onboarding");
  assert.deepEqual(posts, []);
  assert.equal(Telemetry.allow, false);
});

test("modelo online mantém o fluxo de login Pear", async () => {
  const posts: string[] = [];
  const result = await chooseSplash("online", {
    config: config(),
    embeddingModelAvailable: false,
    ideTelemetryEnabled: true,
    uniqueId: "machine",
    extensionVersion: "2.0.0",
    messenger: {
      post: (message) => posts.push(message),
    },
  });

  assert.equal(result.pearaiLogin, true);
  assert.equal(result.next, "pear-login");
  assert.deepEqual(posts, ["pearaiLogin"]);
});
