import type {
  ModelDescription,
  SerializedContinueConfig,
} from "../../index.js";

/** Same id as `LocalProfileLoader`. Selecting it applies this overlay in memory. */
export const FURYU_LOCAL_PROFILE_ID = "local";
/** Shown beside the local profile in the existing ProfileSwitcher. */
export const FURYU_ONLINE_PROFILE_ID = "online";

export const FURYU_LOCAL_SYSTEM_MESSAGE =
  "Você é um assistente de programação. Responda em português do Brasil, a menos que a pessoa peça outro idioma.";

export const FURYU_LOCAL_CHAT_MODEL = "llama3";
export const FURYU_LOCAL_EMBEDDINGS_MODEL = "nomic-embed-text";
export const FURYU_TRANSFORMERS_JS_MODEL = "all-MiniLM-L6-v2";
export const OLLAMA_API_BASE = "http://127.0.0.1:11434/";

const REMOTE_PROVIDERS = new Set(["free-trial", "pearai_server"]);

export interface LocalModeOptions {
  /** True when Ollama's /api/tags lists nomic-embed-text (tag optional). */
  embeddingModelAvailable: boolean;
}

export function hasEmbeddingModel(models: readonly string[]): boolean {
  return models.some((name) => name.startsWith(FURYU_LOCAL_EMBEDDINGS_MODEL));
}

/**
 * The Pear comment says `sendAnonymousTelemetry`. The code reads
 * `allowAnonymousTelemetry` and then `Telemetry.allow`. Either flag
 * set to false opts out.
 */
export function resolveAllowAnonymousTelemetry(config: {
  allowAnonymousTelemetry?: boolean;
  sendAnonymousTelemetry?: boolean;
}): boolean {
  if (
    config.allowAnonymousTelemetry === false ||
    config.sendAnonymousTelemetry === false
  ) {
    return false;
  }
  return true;
}

function withLocalPrompt(model: ModelDescription): ModelDescription {
  if (model.provider !== "ollama") {
    return model;
  }
  return { ...model, systemMessage: FURYU_LOCAL_SYSTEM_MESSAGE };
}

/**
 * In-memory overlay for the local profile. Does not write config.json,
 * so the online profile can still load the previous providers.
 */
export function applyFuryuLocalMode(
  config: SerializedContinueConfig,
  options: LocalModeOptions,
): SerializedContinueConfig {
  const kept = (config.models ?? []).filter(
    (model) => !REMOTE_PROVIDERS.has(model.provider),
  );

  const next: SerializedContinueConfig & { sendAnonymousTelemetry?: boolean } =
    {
      ...config,
      allowAnonymousTelemetry: false,
      sendAnonymousTelemetry: false,
      systemMessage: FURYU_LOCAL_SYSTEM_MESSAGE,
      models: [
        withLocalPrompt({
          title: "Llama 3",
          provider: "ollama",
          model: FURYU_LOCAL_CHAT_MODEL,
        }),
        withLocalPrompt({
          title: "Ollama",
          provider: "ollama",
          model: "AUTODETECT",
        }),
        ...kept.map(withLocalPrompt),
      ],
      tabAutocompleteModel: {
        title: "Starcoder 3b",
        provider: "ollama",
        model: "starcoder2:3b",
      },
      embeddingsProvider: options.embeddingModelAvailable
        ? { provider: "ollama", model: FURYU_LOCAL_EMBEDDINGS_MODEL }
        : { provider: "transformers.js", model: FURYU_TRANSFORMERS_JS_MODEL },
      reranker: undefined,
    };

  return next;
}

export async function ollamaHasEmbeddingModel(
  fetchImpl: typeof fetch = fetch,
  apiBase: string = OLLAMA_API_BASE,
): Promise<boolean> {
  try {
    const response = await fetchImpl(new URL("api/tags", apiBase).toString());
    if (!response.ok) {
      return false;
    }
    const data = (await response.json()) as {
      models?: { name?: string }[];
    };
    const names = (data.models ?? []).map((model) => model.name ?? "");
    return hasEmbeddingModel(names);
  } catch {
    return false;
  }
}
