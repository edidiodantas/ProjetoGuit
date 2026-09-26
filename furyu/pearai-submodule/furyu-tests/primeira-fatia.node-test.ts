import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { describeFuryuWebviewError } from "../core/config/furyu/errors.ts";
import {
  FURYU_LOCAL_SYSTEM_MESSAGE,
  applyFuryuLocalMode,
  hasEmbeddingModel,
  ollamaHasEmbeddingModel,
  resolveAllowAnonymousTelemetry,
} from "../core/config/furyu/localMode.ts";
import {
  maybeLogStreamChatTelemetry,
  shouldInitializePostHog,
} from "../core/config/furyu/telemetryGate.ts";

const here = dirname(fileURLToPath(import.meta.url));

test("perfil local desliga telemetria, pede português e escolhe embeddings locais", () => {
  const next = applyFuryuLocalMode(
    {
      allowAnonymousTelemetry: true,
      models: [
        { title: "Pear", provider: "pearai_server", model: "pearai_model" },
        { title: "Trial", provider: "free-trial", model: "gpt-4o" },
        { title: "Studio", provider: "lmstudio", model: "local-model" },
      ],
      embeddingsProvider: { provider: "free-trial" },
    },
    { embeddingModelAvailable: true },
  );

  assert.equal(next.allowAnonymousTelemetry, false);
  assert.equal(
    (next as { sendAnonymousTelemetry?: boolean }).sendAnonymousTelemetry,
    false,
  );
  assert.equal(resolveAllowAnonymousTelemetry(next), false);
  assert.equal(next.systemMessage, FURYU_LOCAL_SYSTEM_MESSAGE);
  assert.match(next.models[0].systemMessage ?? "", /português do Brasil/);
  assert.equal(
    next.models.some((model) => model.provider === "pearai_server"),
    false,
  );
  assert.deepEqual(next.embeddingsProvider, {
    provider: "ollama",
    model: "nomic-embed-text",
  });

  const fallback = applyFuryuLocalMode(
    { models: [] },
    { embeddingModelAvailable: false },
  );
  assert.deepEqual(fallback.embeddingsProvider, {
    provider: "transformers.js",
    model: "all-MiniLM-L6-v2",
  });
  assert.equal(hasEmbeddingModel(["nomic-embed-text:latest"]), true);
});

test("sendAnonymousTelemetry false também desliga o opt-in", () => {
  assert.equal(resolveAllowAnonymousTelemetry({}), true);
  assert.equal(
    resolveAllowAnonymousTelemetry({ sendAnonymousTelemetry: false }),
    false,
  );
});

test("streamChat não chama o servidor Pear quando a telemetria está desligada", async () => {
  let calls = 0;
  const logged = await maybeLogStreamChatTelemetry(
    false,
    async () => {
      calls += 1;
      return {};
    },
    { model: "llama3", provider: "ollama" },
  );
  assert.equal(logged, false);
  assert.equal(calls, 0);

  const online = await maybeLogStreamChatTelemetry(
    true,
    async () => {
      calls += 1;
      return {};
    },
    { model: "gpt-4o", provider: "openai" },
  );
  assert.equal(online, true);
  assert.equal(calls, 1);
});

test("PostHog não inicializa com a flag falsa ou ausente", () => {
  assert.equal(shouldInitializePostHog(false), false);
  assert.equal(shouldInitializePostHog(undefined), false);
  assert.equal(shouldInitializePostHog(true), true);
});

test("erro do Ollama em português oferece a troca para online e bate com o catálogo", async () => {
  const catalog = JSON.parse(
    readFileSync(
      join(here, "../gui/src/i18n/locales/pt-BR/errors.json"),
      "utf8",
    ),
  ) as { ollamaMissing: string; switchToOnline: string; connectionRefused: string; timeout: string };

  const missing = describeFuryuWebviewError({
    listModelsFailed: true,
    message: "fetch failed",
  });
  assert.equal(missing?.message, catalog.ollamaMissing);
  assert.equal(missing?.message, "Modelo local não encontrado. Verifique se o Ollama está rodando ou mude para o modo Online.");
  assert.equal(missing?.switchToOnline, true);
  assert.equal(missing?.switchLabel, catalog.switchToOnline);

  const refused = describeFuryuWebviewError({
    provider: "ollama",
    apiBase: "http://127.0.0.1:11434/",
    cause: { code: "ECONNREFUSED", message: "connect ECONNREFUSED 127.0.0.1:11434" },
  });
  assert.equal(refused?.message, catalog.ollamaMissing);

  const otherHost = describeFuryuWebviewError({
    provider: "openai",
    apiBase: "http://localhost:8000/v1/",
    cause: { code: "ECONNREFUSED", message: "refused" },
  });
  assert.equal(otherHost?.message, catalog.connectionRefused);
  assert.equal(otherHost?.switchToOnline, false);

  const timeout = describeFuryuWebviewError({
    cause: { name: "ConnectTimeoutError", message: "timed out" },
  });
  assert.equal(timeout?.message, catalog.timeout);

  const tags = await ollamaHasEmbeddingModel(async () => {
    throw new Error("offline");
  });
  assert.equal(tags, false);

  const present = await ollamaHasEmbeddingModel(async () => ({
    ok: true,
    json: async () => ({ models: [{ name: "nomic-embed-text:latest" }] }),
  }) as Response);
  assert.equal(present, true);
});

test("catálogos en e pt-BR têm as mesmas chaves", () => {
  function keysOf(value: unknown, prefix = ""): string[] {
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
      return [prefix];
    }
    return Object.entries(value as Record<string, unknown>).flatMap(([key, child]) =>
      keysOf(child, prefix ? `${prefix}.${key}` : key),
    );
  }

  for (const namespace of ["onboarding", "errors"]) {
    const english = JSON.parse(
      readFileSync(join(here, `../gui/src/i18n/locales/en/${namespace}.json`), "utf8"),
    );
    const portuguese = JSON.parse(
      readFileSync(join(here, `../gui/src/i18n/locales/pt-BR/${namespace}.json`), "utf8"),
    );
    assert.deepEqual(keysOf(portuguese).sort(), keysOf(english).sort());
  }

  const splash = JSON.parse(
    readFileSync(join(here, "../gui/src/i18n/locales/pt-BR/onboarding.json"), "utf8"),
  ) as { splash: { useOnThisComputer: string; useOnlineModel: string } };
  assert.equal(splash.splash.useOnThisComputer, "Usar neste computador");
  assert.equal(splash.splash.useOnlineModel, "Usar um modelo online");
});
