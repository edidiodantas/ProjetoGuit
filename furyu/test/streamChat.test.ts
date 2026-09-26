import assert from "node:assert/strict";
import { test } from "node:test";
import { runStreamOnProfile } from "../core/config/furyu/profiles.ts";
import { SERVER_URL } from "../core/pearaiServer/anonymousTelemetry.ts";
import { Telemetry } from "../core/util/telemetry.ts";
import type { ContinueConfigSlice } from "../core/config/furyu/localMode.ts";

const config = (): ContinueConfigSlice => ({
  models: [{ title: "GPT", provider: "openai", model: "gpt-4o" }],
  allowAnonymousTelemetry: true,
});

async function* oneChunk() {
  yield { role: "assistant", content: "olá" };
}

test("perfil local chama Telemetry.setup(false) antes do stream e não fala com o servidor Pear", async () => {
  const order: string[] = [];
  const original = Telemetry.setup;
  Telemetry.setup = async (allow, uniqueId, extensionVersion) => {
    order.push(`setup:${String(allow)}`);
    return original.call(Telemetry, allow, uniqueId, extensionVersion);
  };

  const calls: string[] = [];
  try {
    const result = await runStreamOnProfile("local", {
      config: config(),
      embeddingModelAvailable: false,
      ideTelemetryEnabled: true,
      uniqueId: "machine",
      extensionVersion: "2.0.0",
      completion: oneChunk(),
      fetchImpl: (url) => {
        calls.push(url);
        throw new Error("servidor Pear não deveria ser chamado");
      },
    });

    assert.deepEqual(order, ["setup:false"]);
    assert.deepEqual(calls, []);
    assert.equal(Telemetry.allow, false);
    assert.equal(result.config.allowAnonymousTelemetry, false);
    assert.equal(result.chunks[0]?.content, "olá");
    assert.match(result.config.models[0]?.systemMessage ?? "", /português do Brasil/);
  } finally {
    Telemetry.setup = original;
    await Telemetry.setup(true, "NOT_UNIQUE", "test");
  }
});

test("perfil online com telemetria ligada faz o GET anonymousTelemetry no streamChat", async () => {
  const calls: { url: string; event?: string; provider?: string }[] = [];
  await runStreamOnProfile("online", {
    config: config(),
    embeddingModelAvailable: false,
    ideTelemetryEnabled: true,
    uniqueId: "machine",
    extensionVersion: "2.0.0",
    completion: oneChunk(),
    fetchImpl: async (url, init) => {
      calls.push({
        url,
        event: init?.headers?.event,
        provider: init?.headers?.provider,
      });
      return { ok: true };
    },
  });

  assert.equal(Telemetry.allow, true);
  assert.deepEqual(calls, [
    {
      url: `${SERVER_URL}/anonymousTelemetry`,
      event: "streamChat",
      provider: "openai",
    },
  ]);
});

test("opt-out sendAnonymousTelemetry no config online também impede o GET", async () => {
  let called = false;
  await runStreamOnProfile("online", {
    config: { ...config(), sendAnonymousTelemetry: false },
    embeddingModelAvailable: true,
    ideTelemetryEnabled: true,
    uniqueId: "machine",
    extensionVersion: "2.0.0",
    completion: oneChunk(),
    fetchImpl: async () => {
      called = true;
      return {};
    },
  });
  assert.equal(Telemetry.allow, false);
  assert.equal(called, false);
});
