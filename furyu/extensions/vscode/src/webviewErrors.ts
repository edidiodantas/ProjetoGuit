import { didChangeSelectedProfile, type ProfileActivation } from "../../../core/config/furyu/profiles.ts";

type Translate = (key: string, options?: Record<string, unknown>) => string;

export interface RequestError {
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

export interface ErrorAction {
  id: "switch-online";
  label: string;
}

export interface WebviewErrorView {
  message: string;
  actions: ErrorAction[];
}

export type RequestFailure =
  | "timeout"
  | "connection-refused"
  | "ollama-missing"
  | "generic";

function isOllamaTarget(error: RequestError): boolean {
  if (error.provider === "ollama") {
    return true;
  }
  const base = error.apiBase ?? "";
  if (base.includes("11434")) {
    return true;
  }
  const blob = `${error.message ?? ""} ${error.cause?.message ?? ""}`.toLowerCase();
  return blob.includes("ollama") || blob.includes("11434");
}

/** Classifica o `catch` de `webviewProtocol.ts` e a falha de `listModels`. */
export function classifyRequestError(error: RequestError): RequestFailure {
  if (error.listModelsFailed) {
    return "ollama-missing";
  }

  const code = error.cause?.code;
  const name = error.cause?.name;
  const ollama = isOllamaTarget(error);

  if (ollama && (code === "ECONNREFUSED" || code === "ENOTFOUND" || name === "ConnectTimeoutError")) {
    return "ollama-missing";
  }
  if (name === "ConnectTimeoutError") {
    return "timeout";
  }
  if (code === "ECONNREFUSED") {
    return "connection-refused";
  }
  return "generic";
}

export function describeRequestError(error: RequestError, translate: Translate): WebviewErrorView {
  const kind = classifyRequestError(error);

  if (kind === "ollama-missing") {
    return {
      message: translate("errors:ollamaMissing"),
      actions: [{ id: "switch-online", label: translate("errors:switchToOnline") }],
    };
  }
  if (kind === "timeout") {
    return { message: translate("errors:timeout"), actions: [] };
  }
  if (kind === "connection-refused") {
    return { message: translate("errors:connectionRefused"), actions: [] };
  }
  return {
    message: translate("errors:generic", {
      name: error.cause?.name ?? "Error",
      message: error.cause?.message ?? error.message ?? "",
    }),
    actions: [],
  };
}

/** A ação usa o mesmo `didChangeSelectedProfile` do ProfileSwitcher. */
export async function runErrorAction(
  action: ErrorAction,
  deps: ProfileActivation,
): Promise<{ selectedProfileId: string }> {
  if (action.id !== "switch-online") {
    throw new Error(`Ação desconhecida: ${action.id}`);
  }
  const selected = await didChangeSelectedProfile("online", deps);
  return { selectedProfileId: selected.selectedProfileId };
}
