/**
 * Mesmo contrato de `Telemetry` em pearai-submodule
 * `core/util/posthog.ts` (51eceef). O cliente posthog-node continua
 * desligado; `allow` é o que `streamChat` consulta antes do GET ao
 * servidor Pear.
 */
export class Telemetry {
  static client: undefined = undefined;
  static uniqueId = "NOT_UNIQUE";
  static extensionVersion: string | undefined = undefined;
  static allow = true;

  static async setup(
    allow: boolean,
    uniqueId: string,
    extensionVersion: string,
  ): Promise<void> {
    Telemetry.uniqueId = uniqueId;
    Telemetry.extensionVersion = extensionVersion;
    Telemetry.allow = allow;
    if (!allow) {
      Telemetry.client = undefined;
    }
  }
}
