import {
  anonymousTelemetryLog,
  type AnonymousTelemetryOptions,
  type FetchLike,
} from "../pearaiServer/anonymousTelemetry.ts";
import { Telemetry } from "../util/telemetry.ts";

/**
 * Trecho de `BaseLLM.streamChat` (core/llm/index.ts, 51eceef) que decide
 * o GET ao servidor Pear. O upstream consulta `Telemetry.allow`, não a
 * string `sendAnonymousTelemetry` do comentário.
 */
export async function streamChat<T>(args: {
  telemetryOptions: AnonymousTelemetryOptions;
  completion: AsyncIterable<T>;
  fetchImpl: FetchLike;
}): Promise<T[]> {
  if (Telemetry.allow) {
    await anonymousTelemetryLog(
      "streamChat",
      args.telemetryOptions,
      args.fetchImpl,
    );
  }

  const chunks: T[] = [];
  for await (const chunk of args.completion) {
    chunks.push(chunk);
  }
  return chunks;
}
