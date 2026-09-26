/**
 * Perfil local do Furyu, ao lado do `setupLocalMode` de
 * `core/config/onboarding.ts` (51eceef). O upstream não define
 * `systemMessage` nem desliga telemetria; este módulo faz os dois.
 */

export const ONBOARDING_LOCAL_MODEL_TITLE = "Ollama";
export const LOCAL_CHAT_MODEL = "llama3";
export const LOCAL_AUTOCOMPLETE_MODEL = "starcoder2:3b";
export const LOCAL_EMBEDDINGS_MODEL = "nomic-embed-text";
export const TRANSFORMERS_JS_MODEL = "all-MiniLM-L6-v2";

export const LOCAL_SYSTEM_MESSAGE =
  "Você é um assistente de programação. Responda em português do Brasil, a menos que a pessoa peça outro idioma.";

export interface ChatModelConfig {
  title: string;
  provider: string;
  model: string;
  systemMessage?: string;
}

export interface EmbeddingsConfig {
  provider: string;
  model?: string;
}

export interface ContinueConfigSlice {
  models: ChatModelConfig[];
  tabAutocompleteModel?: ChatModelConfig;
  embeddingsProvider?: EmbeddingsConfig;
  reranker?: { name: string };
  allowAnonymousTelemetry?: boolean;
  /** Nome citado no comentário de `anonymousTelemetryLog`; o código lê `allowAnonymousTelemetry`. */
  sendAnonymousTelemetry?: boolean;
}

export interface LocalModeOptions {
  /** Verdadeiro quando `ollama list` contém `nomic-embed-text` (tag opcional, como no onboarding). */
  embeddingModelAvailable: boolean;
}

export function hasEmbeddingModel(models: readonly string[]): boolean {
  return models.some((name) => name.startsWith(LOCAL_EMBEDDINGS_MODEL));
}

export function unifiedAllowAnonymousTelemetry(
  config: Pick<
    ContinueConfigSlice,
    "allowAnonymousTelemetry" | "sendAnonymousTelemetry"
  >,
): boolean {
  if (
    config.allowAnonymousTelemetry === false ||
    config.sendAnonymousTelemetry === false
  ) {
    return false;
  }
  return true;
}

export function applyLocalMode(
  config: ContinueConfigSlice,
  options: LocalModeOptions,
): ContinueConfigSlice {
  const embeddingsProvider: EmbeddingsConfig = options.embeddingModelAvailable
    ? { provider: "ollama", model: LOCAL_EMBEDDINGS_MODEL }
    : { provider: "transformers.js", model: TRANSFORMERS_JS_MODEL };

  const chatModel = (model: ChatModelConfig): ChatModelConfig =>
    model.provider === "ollama"
      ? { ...model, systemMessage: LOCAL_SYSTEM_MESSAGE }
      : model;

  return {
    ...config,
    allowAnonymousTelemetry: false,
    sendAnonymousTelemetry: false,
    models: [
      chatModel({
        title: "Llama 3",
        provider: "ollama",
        model: LOCAL_CHAT_MODEL,
      }),
      chatModel({
        title: ONBOARDING_LOCAL_MODEL_TITLE,
        provider: "ollama",
        model: "AUTODETECT",
      }),
      ...config.models
        .filter((model) => model.provider !== "free-trial")
        .map(chatModel),
    ],
    tabAutocompleteModel: {
      title: "Starcoder 3b",
      provider: "ollama",
      model: LOCAL_AUTOCOMPLETE_MODEL,
    },
    embeddingsProvider,
    reranker: undefined,
  };
}
