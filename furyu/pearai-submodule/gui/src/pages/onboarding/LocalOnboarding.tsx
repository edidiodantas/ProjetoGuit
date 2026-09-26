import { ArrowLeftIcon } from "@heroicons/react/24/outline";
import { ONBOARDING_LOCAL_MODEL_TITLE } from "core/config/onboarding";
import { FURYU_ONLINE_PROFILE_ID } from "core/config/furyu/localMode";
import { useContext, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { IdeMessengerContext } from "../../context/IdeMessenger";
import { CheckMarkHeader } from "./CheckMarkHeader";
import { StyledButton } from "./components";
import { CopyToTerminalButton } from "./CopyToTerminalButton";
import { useOnboarding } from "./utils";
import "@/continue-styles.css";

type OllamaConnectionStatuses =
  | "waiting_to_download"
  | "downloading"
  | "verified";

enum DefaultLocalModels {
  Chat = "llama3",
  Autocomplete = "starcoder2:3b",
  Embeddings = "nomic-embed-text",
}

const OLLAMA_DOWNLOAD_URL = "https://ollama.com/download";
const REFETCH_MODELS_INTERVAL_MS = 1000;

function LocalOnboarding() {
  const navigate = useNavigate();
  const ideMessenger = useContext(IdeMessengerContext);

  const [downloadedOllamaModels, setDownloadedOllamaModels] = useState<
    string[] | undefined
  >(undefined);

  const [ollamaConnectionStatus, setOllamaConnectionStatus] =
    useState<OllamaConnectionStatuses>("waiting_to_download");

  const [hasLoadedChatModel, setHasLoadedChatModel] = useState(false);

  const { completeOnboarding } = useOnboarding();
  const { t } = useTranslation(["onboarding", "errors"]);
  const [ollamaMissing, setOllamaMissing] = useState(false);

  const isOllamaConnected = ollamaConnectionStatus === "verified";

  function switchToOnline() {
    void ideMessenger.request("didChangeSelectedProfile", {
      id: FURYU_ONLINE_PROFILE_ID,
    });
    navigate("/onboarding");
  }

  function isModelDownloaded(model: string) {
    if (!downloadedOllamaModels) {
      return false;
    }

    return downloadedOllamaModels.some(
      (ollamaModel) => ollamaModel.startsWith(model), // We use `startsWith` to ignore trailing tags like `:latest`
    );
  }

  function renderOllamaConnectionStatus(status: OllamaConnectionStatuses) {
    switch (status) {
      case "waiting_to_download":
        return (
          <div className="pb-6">
            <a
              href={OLLAMA_DOWNLOAD_URL}
              target="_blank"
              onClick={() => setOllamaConnectionStatus("downloading")}
            >
              {t("onboarding:local.downloadLink")}
            </a>

            <p className="leading-relaxed">
              {t("onboarding:local.afterDownload")}
            </p>
          </div>
        );

      case "downloading":
        return <p className="pb-6">{t("onboarding:local.checking")}</p>;

      case "verified":
        return <></>;

      default:
        return <></>;
    }
  }

  /**
   * The first time we detect that a chat model has been loaded,
   * we send an empty request to load it
   */
  useEffect(() => {
    if (!hasLoadedChatModel && isModelDownloaded(DefaultLocalModels.Chat)) {
      ideMessenger.post("llm/complete", {
        completionOptions: {},
        prompt: "",
        title: ONBOARDING_LOCAL_MODEL_TITLE,
      });

      setHasLoadedChatModel(true);
    }
  }, [downloadedOllamaModels]);

  /**
   * Sets up an interval that runs every `REFETCH_MODELS_INTERVAL_MS`
   * to fetch the list of downloaded models and update state.
   */
  useEffect(() => {
    const fetchDownloadedModels = async () => {
      try {
        const models = await ideMessenger.request("llm/listModels", {
          title: ONBOARDING_LOCAL_MODEL_TITLE,
        });

        if (Array.isArray(models)) {
          // If we got a response, the connection has been verified
          if (!isOllamaConnected) {
            setOllamaConnectionStatus("verified");
          }

          setDownloadedOllamaModels(models);
          setOllamaMissing(false);
        } else {
          // /api/show swallows the error. listModels is what this page observes.
          setOllamaMissing(true);
        }
      } catch {
        setOllamaMissing(true);
      }
    };

    // Immediately invoke to try to minimize jank if a user already has
    // the models installed. A better fix would be to not load the onboarding
    // steps until we've first checked if the user already has the models installed.
    fetchDownloadedModels();

    const interval = setInterval(
      fetchDownloadedModels,
      REFETCH_MODELS_INTERVAL_MS,
    );

    return () => {
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="p-8 overflow-y-scroll">
      <div>
        <ArrowLeftIcon
          width="1.2em"
          height="1.2em"
          onClick={() => navigate(-1)}
          className="inline-block cursor-pointer"
        />
      </div>

      <h1 className="text-center">{t("onboarding:local.title")}</h1>
      {ollamaMissing && (
        <div className="my-4 rounded border border-red-500 p-4">
          <p>{t("errors:ollamaMissing")}</p>
          <StyledButton className="mt-3" onClick={switchToOnline}>
            {t("errors:switchToOnline")}
          </StyledButton>
        </div>
      )}

      <div>
        <CheckMarkHeader isComplete={isOllamaConnected}>
          {t("onboarding:local.downloadOllama")}
        </CheckMarkHeader>

        {renderOllamaConnectionStatus(ollamaConnectionStatus)}
      </div>

      <div>
        <CheckMarkHeader
          isComplete={isModelDownloaded(DefaultLocalModels.Chat)}
        >
          {t("onboarding:local.downloadChat")}
        </CheckMarkHeader>
        {!isModelDownloaded(DefaultLocalModels.Chat) && (
          <div className="pb-6">
            <p className="leading-relaxed">
              {t("onboarding:local.chatRecommendation", {
                model: DefaultLocalModels.Chat,
              })}
            </p>

            <CopyToTerminalButton>
              {` ollama run ${DefaultLocalModels.Chat}`}
            </CopyToTerminalButton>
          </div>
        )}
      </div>

      <div>
        <CheckMarkHeader
          isComplete={isModelDownloaded(DefaultLocalModels.Autocomplete)}
        >
          {t("onboarding:local.downloadAutocomplete")}
        </CheckMarkHeader>

        {!isModelDownloaded(DefaultLocalModels.Autocomplete) && (
          <div className="pb-6">
            <p className="leading-relaxed">
              {t("onboarding:local.autocompleteRecommendation", {
                model: DefaultLocalModels.Autocomplete,
              })}
            </p>

            <CopyToTerminalButton>
              {`ollama run ${DefaultLocalModels.Autocomplete}`}
            </CopyToTerminalButton>
          </div>
        )}
      </div>

      <div>
        <CheckMarkHeader
          isComplete={isModelDownloaded(DefaultLocalModels.Embeddings)}
        >
          {t("onboarding:local.downloadEmbeddings")}
        </CheckMarkHeader>

        {!isModelDownloaded(DefaultLocalModels.Embeddings) && (
          <div className="pb-6">
            <p className="leading-relaxed">
              {t("onboarding:local.embeddingsRecommendation", {
                model: DefaultLocalModels.Embeddings,
              })}
            </p>

            <CopyToTerminalButton>
              {`ollama pull ${DefaultLocalModels.Embeddings}`}
            </CopyToTerminalButton>
          </div>
        )}
      </div>

      <div className="flex flex-col justify-end mt-4">
        <StyledButton onClick={completeOnboarding}>
          {t("onboarding:local.complete")}
        </StyledButton>
      </div>
    </div>
  );
}

export default LocalOnboarding;
