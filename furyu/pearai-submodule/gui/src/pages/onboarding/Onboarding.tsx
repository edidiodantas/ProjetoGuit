import { useContext } from "react";
import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import { lightGray } from "../../components";
import ConfirmationDialog from "../../components/dialogs/ConfirmationDialog";
import { IdeMessengerContext } from "../../context/IdeMessenger";
import {
  setDialogMessage,
  setShowDialog,
} from "../../redux/slices/uiStateSlice";
import { StyledButton } from "./components";
import { useOnboarding } from "./utils";
import styled from "styled-components";
import _ from "lodash";
import { useWebviewListener } from "../../hooks/useWebviewListener";
import { Button } from "@/components/ui/button";
import "@/continue-styles.css";

function Onboarding() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const ideMessenger = useContext(IdeMessengerContext);
  const { completeOnboarding } = useOnboarding();
  const { t } = useTranslation("onboarding");

  return (
    <div className="max-w-96 mx-auto flex flex-col items-center justify-between pt-8">
      <div className="flex flex-col items-center justify-center">
      <img
          src={`${window.vscMediaUrl}/logos/pearai-green.svg`}
          height="24px"
          style={{ marginRight: "5px" }}
        />
      <h1 className="text-center">{t("login.title")}</h1>
      <Button
        variant="animated"
        size="lg"
        className="m-5 flex flex-col justify-center items-center bg-button text-button-foreground"
        onClick={() => {
          void ideMessenger.request("didChangeSelectedProfile", { id: "local" });
          navigate("/localOnboarding");
        }}
      >
        <h3 className="font-medium">{t("splash.useOnThisComputer")}</h3>
      </Button>
      <h3 className="mx-3 text-center flex">{t("login.subtitle")}</h3>
      <Button 
        variant="animated"
        size="lg"
        className="m-5 flex flex-col justify-center items-center bg-button text-button-foreground"
        onClick={() => {
          void ideMessenger.request("didChangeSelectedProfile", { id: "online" });
          ideMessenger.post("pearaiLogin", undefined);
        }}
      >
        <h3 className="font-medium">{t("splash.useOnlineModel")}</h3>

      </Button>

      <p className="mx-3">
        {t("login.afterLogin")}
      </p>
      <small
        style={{
          color: lightGray,
          fontSize: "0.85em",
          display: "block",
        }}
        className="mx-3"
      >
        {t("login.trouble")}{" "}
        <a
          href="https://trypear.ai/dashboard"
          target="_blank"
          rel="noopener noreferrer"
        >
          trypear.ai
        </a>
        .
      </small>
      <div className="absolute bottom-4 right-4">
        <StyledButton
          onClick={(e) => {
            dispatch(setShowDialog(true));
            dispatch(
              setDialogMessage(
                <ConfirmationDialog
                  text={t("login.skipConfirm")}
                  onConfirm={() => {
                    completeOnboarding();
                  }}
                />,
              ),
            );
          }}
        >
          {t("login.skip")}
        </StyledButton>
      </div>
      </div>
      <div></div>
    </div>
  );
}

export default Onboarding;
