export type FuryuLanguage = "pt-BR" | "en";

export interface FuryuWebviewError {
  message: string;
  switchToOnline: boolean;
  switchLabel: string;
}

const COPY = {
  "pt-BR": {
    timeout:
      'A conexão expirou. Se a conexão deve demorar, aumente o tempo em config.json com "requestOptions": { "timeout": 10000 }. A referência completa da configuração está em https://trypear.ai/reference/config',
    connectionRefused:
      'A conexão foi recusada. Isso costuma indicar que não há um servidor no endereço informado. Se o servidor é seu, defina o parâmetro "apiBase" em config.json. Um exemplo de servidor compatível com a OpenAI está em https://trypear.ai/reference/Model%20Providers/openai#openai-compatible-servers--apis',
    generic:
      'A requisição falhou com "{{name}}": {{message}}. Se a configuração do PearAI não funcionar, consulte o guia de solução de problemas.',
    ollamaMissing:
      "Modelo local não encontrado. Verifique se o Ollama está rodando ou mude para o modo Online.",
    switchToOnline: "Mudar para o modo Online",
  },
  en: {
    timeout:
      'Connection timed out. If you expect it to take a long time to connect, you can increase the timeout in config.json by setting "requestOptions": { "timeout": 10000 }. You can find the full config reference here: https://trypear.ai/reference/config',
    connectionRefused:
      'Connection was refused. This likely means that there is no server running at the specified URL. If you are running your own server you may need to set the "apiBase" parameter in config.json. For example, you can set up an OpenAI-compatible server like here: https://trypear.ai/reference/Model%20Providers/openai#openai-compatible-servers--apis',
    generic:
      'The request failed with "{{name}}": {{message}}. If you\'re having trouble setting up PearAI, please see the troubleshooting guide for help.',
    ollamaMissing:
      "Local model not found. Check that Ollama is running or switch to Online mode.",
    switchToOnline: "Switch to Online mode",
  },
} as const;

export interface WebviewErrorInput {
  message?: string;
  provider?: string;
  apiBase?: string;
  listModelsFailed?: boolean;
  cause?: {
    name?: string;
    code?: string;
    message?: string;
  };
}

export function isOllamaUnavailable(error: WebviewErrorInput): boolean {
  if (error.listModelsFailed || error.provider === "ollama") {
    return true;
  }
  const base = error.apiBase ?? "";
  if (base.includes("11434")) {
    return true;
  }
  const blob = `${error.message ?? ""} ${error.cause?.message ?? ""}`.toLowerCase();
  return blob.includes("ollama") || blob.includes("11434");
}

function fill(template: string, values: Record<string, string>): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key: string) => values[key] ?? "");
}

/**
 * Portuguese (default) text for the webview error path.
 * Ollama failures include the switch-to-online action.
 */
export function describeFuryuWebviewError(
  error: WebviewErrorInput,
  language: FuryuLanguage = "pt-BR",
): FuryuWebviewError | undefined {
  const copy = COPY[language];
  const cause = error.cause;
  const ollama = isOllamaUnavailable(error);
  const refused = cause?.code === "ECONNREFUSED";
  const timeout = cause?.name === "ConnectTimeoutError";

  if (error.listModelsFailed || (ollama && (refused || timeout || cause?.code === "ENOTFOUND"))) {
    return {
      message: copy.ollamaMissing,
      switchToOnline: true,
      switchLabel: copy.switchToOnline,
    };
  }

  if (!cause && !error.listModelsFailed) {
    return undefined;
  }

  if (timeout) {
    return { message: copy.timeout, switchToOnline: false, switchLabel: copy.switchToOnline };
  }
  if (refused) {
    return {
      message: copy.connectionRefused,
      switchToOnline: false,
      switchLabel: copy.switchToOnline,
    };
  }
  if (cause) {
    return {
      message: fill(copy.generic, {
        name: cause.name ?? "Error",
        message: cause.message ?? error.message ?? "",
      }),
      switchToOnline: false,
      switchLabel: copy.switchToOnline,
    };
  }
  return undefined;
}

export const FURYU_OLLAMA_MISSING_PT = COPY["pt-BR"].ollamaMissing;
