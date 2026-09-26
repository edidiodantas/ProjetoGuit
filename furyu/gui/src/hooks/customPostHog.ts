/**
 * O `useEffect` de `CustomPostHogProvider.tsx` (51eceef) chama
 * `posthog.init` e `opt_in_capturing` sempre. `allowAnonymousTelemetry`
 * só decide se o `PostHogProvider` envolve a árvore. No perfil local
 * a inicialização não acontece.
 */
export interface PostHogClient {
  init: (apiKey: string, options: { api_host: string; disable_session_recording: boolean; capture_pageview: boolean }) => void;
  identify: (id: string, properties?: { pearAiId: string }) => void;
  alias: (userId: string, machineId: string) => void;
  opt_in_capturing: () => void;
}

export function syncPostHogClient(args: {
  allowAnonymousTelemetry: boolean | undefined;
  client: PostHogClient;
  apiKey: string;
  apiHost: string;
  userId?: string;
  machineId: string;
}): { initialized: boolean } {
  if (args.allowAnonymousTelemetry !== true) {
    return { initialized: false };
  }

  args.client.init(args.apiKey, {
    api_host: args.apiHost,
    disable_session_recording: true,
    capture_pageview: false,
  });

  if (args.userId) {
    args.client.identify(args.machineId, { pearAiId: args.userId });
    args.client.alias(args.userId, args.machineId);
  } else {
    args.client.identify(args.machineId);
  }

  args.client.opt_in_capturing();
  return { initialized: true };
}
