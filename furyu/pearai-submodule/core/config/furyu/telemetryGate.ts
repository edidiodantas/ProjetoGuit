/** PostHog init and opt-in run only when the flag is explicitly true. */
export function shouldInitializePostHog(
  allowAnonymousTelemetry: boolean | undefined,
): boolean {
  return allowAnonymousTelemetry === true;
}

/**
 * `BaseLLM.streamChat` calls this before the model stream.
 * `allow` is `Telemetry.allow`, which the local profile sets to false
 * in `doLoadConfig` before any chat request.
 */
export async function maybeLogStreamChatTelemetry(
  allow: boolean,
  log: (event: string, options: unknown) => Promise<unknown>,
  options: unknown,
): Promise<boolean> {
  if (!allow) {
    return false;
  }
  await log("streamChat", options);
  return true;
}
