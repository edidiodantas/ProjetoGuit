import assert from "node:assert/strict";
import { test } from "node:test";
import {
  LOCAL_SYSTEM_MESSAGE,
  applyLocalMode,
  hasEmbeddingModel,
  unifiedAllowAnonymousTelemetry,
  type ContinueConfigSlice,
} from "../core/config/furyu/localMode.ts";

const baseConfig = (): ContinueConfigSlice => ({
  allowAnonymousTelemetry: true,
  sendAnonymousTelemetry: true,
  models: [
    { title: "Free", provider: "free-trial", model: "pear-trial" },
    { title: "Kept", provider: "openai", model: "gpt-4o" },
  ],
  embeddingsProvider: { provider: "free-trial" },
  reranker: { name: "free-trial" },
});

test("perfil local desliga os dois nomes de telemetria e pede português do Brasil", () => {
  const input = baseConfig();
  const next = applyLocalMode(input, { embeddingModelAvailable: true });

  assert.equal(next.allowAnonymousTelemetry, false);
  assert.equal(next.sendAnonymousTelemetry, false);
  assert.equal(input.allowAnonymousTelemetry, true);
  assert.equal(unifiedAllowAnonymousTelemetry(next), false);

  const llama = next.models.find((model) => model.model === "llama3");
  assert.ok(llama);
  assert.equal(llama.systemMessage, LOCAL_SYSTEM_MESSAGE);
  assert.match(llama.systemMessage, /português do Brasil/);
  assert.equal(
    next.models.find((model) => model.model === "AUTODETECT")?.systemMessage,
    LOCAL_SYSTEM_MESSAGE,
  );
  assert.equal(next.models.some((model) => model.provider === "free-trial"), false);
  assert.equal(next.tabAutocompleteModel?.model, "starcoder2:3b");
  assert.equal(next.reranker, undefined);
});

test("embeddings ficam no Ollama e caem para transformers.js sem o modelo", () => {
  const withModel = applyLocalMode(baseConfig(), { embeddingModelAvailable: true });
  assert.deepEqual(withModel.embeddingsProvider, {
    provider: "ollama",
    model: "nomic-embed-text",
  });

  const withoutModel = applyLocalMode(baseConfig(), { embeddingModelAvailable: false });
  assert.deepEqual(withoutModel.embeddingsProvider, {
    provider: "transformers.js",
    model: "all-MiniLM-L6-v2",
  });

  assert.equal(hasEmbeddingModel(["llama3:latest", "nomic-embed-text:latest"]), true);
  assert.equal(hasEmbeddingModel(["llama3:latest"]), false);
});

test("sendAnonymousTelemetry false desliga o opt-in mesmo com a outra chave omitida", () => {
  assert.equal(unifiedAllowAnonymousTelemetry({}), true);
  assert.equal(unifiedAllowAnonymousTelemetry({ sendAnonymousTelemetry: false }), false);
  assert.equal(unifiedAllowAnonymousTelemetry({ allowAnonymousTelemetry: false }), false);
});
