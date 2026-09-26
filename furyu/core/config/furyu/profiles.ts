import {
  applyLocalMode,
  unifiedAllowAnonymousTelemetry,
  type ContinueConfigSlice,
} from "./localMode.ts";
import { streamChat } from "../../llm/streamChat.ts";
import type { FetchLike } from "../../pearaiServer/anonymousTelemetry.ts";
import { Telemetry } from "../../util/telemetry.ts";

/** Id já usado por `LocalProfileLoader` no submodule. */
export const LOCAL_PROFILE_ID = "local";
/** Perfil online que passa a aparecer ao lado do local no ProfileSwitcher. */
export const ONLINE_PROFILE_ID = "online";

export interface ProfileDescription {
  id: string;
  title: string;
}

export interface ProfileActivation {
  config: ContinueConfigSlice;
  embeddingModelAvailable: boolean;
  ideTelemetryEnabled: boolean;
  uniqueId: string;
  extensionVersion: string;
}

/**
 * Títulos que o `ProfileSwitcher` existente já renderiza em `option.title`.
 * Não há seletor de modelo aqui: a troca continua sendo `didChangeSelectedProfile`.
 */
export function profilesForSwitcher(translate: (key: string) => string): ProfileDescription[] {
  return [
    { id: LOCAL_PROFILE_ID, title: translate("onboarding:profiles.local") },
    { id: ONLINE_PROFILE_ID, title: translate("onboarding:profiles.online") },
  ];
}

/** O listbox atual só aparece com o beta do control plane. Os dois perfis do Furyu precisam aparecer sem isso. */
export function shouldShowProfileSwitcher(profiles: readonly { id: string }[]): boolean {
  const ids = new Set(profiles.map((profile) => profile.id));
  return ids.has(LOCAL_PROFILE_ID) && ids.has(ONLINE_PROFILE_ID);
}

/**
 * `ConfigHandler.setSelectedProfile`: grava o id e recarrega.
 * `Telemetry.setup` roda antes de qualquer `streamChat` deste perfil.
 */
export async function activateProfile(
  profileId: string,
  deps: ProfileActivation,
): Promise<ContinueConfigSlice> {
  if (profileId === LOCAL_PROFILE_ID) {
    const next = applyLocalMode(deps.config, {
      embeddingModelAvailable: deps.embeddingModelAvailable,
    });
    await Telemetry.setup(false, deps.uniqueId, deps.extensionVersion);
    return next;
  }

  if (profileId === ONLINE_PROFILE_ID) {
    const allow =
      unifiedAllowAnonymousTelemetry(deps.config) && deps.ideTelemetryEnabled;
    await Telemetry.setup(allow, deps.uniqueId, deps.extensionVersion);
    return deps.config;
  }

  throw new Error(`Perfil desconhecido: ${profileId}`);
}

export async function didChangeSelectedProfile(
  profileId: string,
  deps: ProfileActivation,
): Promise<{ selectedProfileId: string; config: ContinueConfigSlice }> {
  const config = await activateProfile(profileId, deps);
  return { selectedProfileId: profileId, config };
}

export async function runStreamOnProfile<T>(
  profileId: string,
  deps: ProfileActivation & {
    fetchImpl: FetchLike;
    completion: AsyncIterable<T>;
  },
): Promise<{ config: ContinueConfigSlice; chunks: T[] }> {
  const config = await activateProfile(profileId, deps);
  const model = config.models[0];
  const chunks = await streamChat({
    telemetryOptions: {
      model: model?.model,
      provider: model?.provider,
    },
    completion: deps.completion,
    fetchImpl: deps.fetchImpl,
  });
  return { config, chunks };
}
