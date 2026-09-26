/** Mesmo host de `core/util/parameters.ts` no commit 51eceef. */
export const SERVER_URL = "https://server.trypear.ai/pearai-server-api2";

export interface AnonymousTelemetryOptions {
  model?: string;
  provider?: string;
}

export type FetchLike = (
  input: string,
  init?: { method?: string; headers?: Record<string, string> },
) => Promise<unknown>;

/**
 * GET `${SERVER_URL}/anonymousTelemetry`. O corpo do prompt não entra
 * nos cabeçalhos; o perfil local nem chega a chamar esta função.
 */
export async function anonymousTelemetryLog(
  event: string,
  options: AnonymousTelemetryOptions,
  fetchImpl: FetchLike,
): Promise<unknown> {
  return fetchImpl(`${SERVER_URL}/anonymousTelemetry`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      model: options.model || "unknown",
      provider: options.provider || "unknown",
      event,
    },
  });
}
