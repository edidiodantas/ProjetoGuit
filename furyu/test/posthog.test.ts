import assert from "node:assert/strict";
import { test } from "node:test";
import { syncPostHogClient, type PostHogClient } from "../gui/src/hooks/customPostHog.ts";

function fakeClient() {
  const calls: string[] = [];
  const client: PostHogClient = {
    init: () => calls.push("init"),
    identify: () => calls.push("identify"),
    alias: () => calls.push("alias"),
    opt_in_capturing: () => calls.push("opt_in"),
  };
  return { calls, client };
}

const common = {
  apiKey: "phc_test",
  apiHost: "https://us.i.posthog.com",
  machineId: "machine-1",
};

test("allowAnonymousTelemetry false não inicializa o PostHog nem opta por captura", () => {
  const { calls, client } = fakeClient();
  const result = syncPostHogClient({
    ...common,
    allowAnonymousTelemetry: false,
    client,
    userId: "pear-user",
  });
  assert.equal(result.initialized, false);
  assert.deepEqual(calls, []);
});

test("flag ausente também não inicializa o cliente", () => {
  const { calls, client } = fakeClient();
  syncPostHogClient({
    ...common,
    allowAnonymousTelemetry: undefined,
    client,
  });
  assert.deepEqual(calls, []);
});

test("flag true inicializa, identifica e liga a captura", () => {
  const { calls, client } = fakeClient();
  const result = syncPostHogClient({
    ...common,
    allowAnonymousTelemetry: true,
    client,
    userId: "pear-user",
  });
  assert.equal(result.initialized, true);
  assert.deepEqual(calls, ["init", "identify", "alias", "opt_in"]);
});
