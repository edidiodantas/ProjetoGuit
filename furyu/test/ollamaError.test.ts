import assert from "node:assert/strict";
import { test } from "node:test";
import { Telemetry } from "../core/util/telemetry.ts";
import { setupI18n } from "../gui/src/i18n/setup.ts";
import { observeOllamaModels } from "../gui/src/pages/onboarding/localModels.ts";
import {
  describeRequestError,
  runErrorAction,
} from "../extensions/vscode/src/webviewErrors.ts";
import type { ContinueConfigSlice } from "../core/config/furyu/localMode.ts";
import {
  profilesForSwitcher,
  shouldShowProfileSwitcher,
} from "../core/config/furyu/profiles.ts";

const config = (): ContinueConfigSlice => ({
  models: [{ title: "Llama 3", provider: "ollama", model: "llama3" }],
});

test("listModels com falha e ECONNREFUSED do Ollama oferecem o modo online em português", async () => {
  const i18n = await setupI18n("pt-BR");
  const t = i18n.t.bind(i18n);

  assert.deepEqual(await observeOllamaModels(async () => {
    throw new Error("connect ECONNREFUSED 127.0.0.1:11434");
  }), { ok: false, failure: "ollama-missing" });

  assert.deepEqual(await observeOllamaModels(async () => null), {
    ok: false,
    failure: "ollama-missing",
  });

  const refused = describeRequestError(
    {
      provider: "ollama",
      apiBase: "http://localhost:11434/",
      cause: { code: "ECONNREFUSED", message: "connect refused" },
    },
    t,
  );
  assert.equal(
    refused.message,
    "Modelo local não encontrado. Verifique se o Ollama está rodando ou mude para o modo Online.",
  );
  assert.equal(refused.actions[0]?.id, "switch-online");
  assert.equal(refused.actions[0]?.label, "Mudar para o modo Online");

  const fromList = describeRequestError({ listModelsFailed: true, message: "fetch failed" }, t);
  assert.equal(fromList.message, refused.message);

  const selected = await runErrorAction(refused.actions[0]!, {
    config: config(),
    embeddingModelAvailable: false,
    ideTelemetryEnabled: true,
    uniqueId: "machine",
    extensionVersion: "2.0.0",
  });
  assert.equal(selected.selectedProfileId, "online");
  assert.equal("selectedModel" in selected, false);
  assert.equal(Telemetry.allow, true);
});

test("timeout e conexão recusada de outro servidor saem do catálogo, sem troca de modelo", async () => {
  const i18n = await setupI18n("pt-BR");
  const t = i18n.t.bind(i18n);

  const timeout = describeRequestError(
    { provider: "openai", cause: { name: "ConnectTimeoutError", message: "timed out" } },
    t,
  );
  assert.match(timeout.message, /A conexão expirou/);
  assert.deepEqual(timeout.actions, []);

  const refused = describeRequestError(
    {
      provider: "openai",
      apiBase: "http://localhost:8000/v1/",
      cause: { code: "ECONNREFUSED", message: "refused" },
    },
    t,
  );
  assert.match(refused.message, /A conexão foi recusada/);
  assert.deepEqual(refused.actions, []);

  const generic = describeRequestError(
    { cause: { name: "AbortError", message: "cancelled" } },
    t,
  );
  assert.match(generic.message, /AbortError/);
  assert.match(generic.message, /cancelled/);
});

test("a troca reusa o ProfileSwitcher e não cria um seletor de modelo", async () => {
  const i18n = await setupI18n("pt-BR");
  const profiles = profilesForSwitcher(i18n.t.bind(i18n));
  assert.deepEqual(profiles, [
    { id: "local", title: "Neste computador" },
    { id: "online", title: "Modelo online" },
  ]);
  assert.equal(shouldShowProfileSwitcher(profiles), true);
  assert.equal(shouldShowProfileSwitcher([{ id: "local", title: "Local Config" }]), false);
});
