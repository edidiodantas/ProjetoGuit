import { activateProfile, type ProfileActivation } from "../../../../core/config/furyu/profiles.ts";

export type SplashChoice = "local" | "online";

export interface SplashOption {
  id: SplashChoice;
  label: string;
}

type Translate = (key: string, options?: Record<string, unknown>) => string;

export interface IdeMessenger {
  post: (message: "pearaiLogin", data: undefined) => void;
}

/**
 * O splash antigo tinha um único "Next" e o onboarding pedia login.
 * As duas escolhas aparecem antes de `pearaiLogin`.
 */
export function splashChoices(translate: Translate): SplashOption[] {
  return [
    { id: "local", label: translate("onboarding:splash.useOnThisComputer") },
    { id: "online", label: translate("onboarding:splash.useOnlineModel") },
  ];
}

/**
 * `Onboarding.tsx` mandava o overlay direto para `/`. O splash vale
 * nesse caminho também.
 */
export function onboardingEntry(_isPearOverlay: boolean): { screen: "splash" } {
  return { screen: "splash" };
}

export async function chooseSplash(
  choice: SplashChoice,
  deps: ProfileActivation & { messenger: IdeMessenger },
): Promise<{ next: "local-onboarding" | "pear-login"; pearaiLogin: boolean }> {
  if (choice === "local") {
    await activateProfile("local", deps);
    return { next: "local-onboarding", pearaiLogin: false };
  }

  await activateProfile("online", deps);
  deps.messenger.post("pearaiLogin", undefined);
  return { next: "pear-login", pearaiLogin: true };
}
