import {
  LOCAL_AUTOCOMPLETE_MODEL,
  LOCAL_CHAT_MODEL,
  LOCAL_EMBEDDINGS_MODEL,
} from "../../../../core/config/furyu/localMode.ts";

type Translate = (key: string, options?: Record<string, unknown>) => string;

export function splashCopy(translate: Translate) {
  return {
    title: translate("onboarding:splash.title"),
    subtitle: translate("onboarding:splash.subtitle"),
  };
}

export function loginCopy(translate: Translate) {
  return {
    title: translate("onboarding:login.title"),
    subtitle: translate("onboarding:login.subtitle"),
    submit: translate("onboarding:login.submit"),
    afterLogin: translate("onboarding:login.afterLogin"),
    trouble: translate("onboarding:login.trouble"),
    skip: translate("onboarding:login.skip"),
    skipConfirm: translate("onboarding:login.skipConfirm"),
  };
}

export function localOnboardingCopy(translate: Translate) {
  return {
    title: translate("onboarding:local.title"),
    downloadOllama: translate("onboarding:local.downloadOllama"),
    downloadLink: translate("onboarding:local.downloadLink"),
    afterDownload: translate("onboarding:local.afterDownload"),
    checking: translate("onboarding:local.checking"),
    downloadChat: translate("onboarding:local.downloadChat"),
    chatRecommendation: translate("onboarding:local.chatRecommendation", {
      model: LOCAL_CHAT_MODEL,
    }),
    downloadAutocomplete: translate("onboarding:local.downloadAutocomplete"),
    autocompleteRecommendation: translate(
      "onboarding:local.autocompleteRecommendation",
      { model: LOCAL_AUTOCOMPLETE_MODEL },
    ),
    downloadEmbeddings: translate("onboarding:local.downloadEmbeddings"),
    embeddingsRecommendation: translate(
      "onboarding:local.embeddingsRecommendation",
      { model: LOCAL_EMBEDDINGS_MODEL },
    ),
    complete: translate("onboarding:local.complete"),
  };
}
