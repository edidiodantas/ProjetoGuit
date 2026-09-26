import React from 'react';
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { getLogoPath } from './setup/ImportExtensions';

const SplashScreen = ({
    onUseLocal,
    onUseOnline,
}: {
    onUseLocal: () => void;
    onUseOnline: () => void;
}) => {
    const { t } = useTranslation("onboarding");
    return (
        <div className="h-full flex-col justify-center items-center gap-10 inline-flex overflow-hidden select-none">
            <div className="max-w-2xl mx-auto text-center flex flex-col gap-7 justify-center">
                <div className="flex-col justify-center items-center gap-7 flex w-64 mx-auto">
                    <img src={getLogoPath("pearai-color.png")} alt="..." />
                </div>
                <div className="flex flex-col gap-2">
                    <div className="text-4xl font-['SF Pro']">{t("splash.title")}</div>
                    <div className="text-xl font-['SF Pro']">{t("splash.subtitle")}</div>
                </div>
                <div className="flex flex-col gap-3 items-center">
                    <Button className="mx-auto w-[300px] rounded-lg justify-center items-center gap-1 inline-flex overflow-hidden" onClick={onUseLocal}>
                        <div className="text-xs font-['SF Pro']">{t("splash.useOnThisComputer")}</div>
                    </Button>
                    <Button variant="outline" className="mx-auto w-[300px] rounded-lg justify-center items-center gap-1 inline-flex overflow-hidden" onClick={onUseOnline}>
                        <div className="text-xs font-['SF Pro']">{t("splash.useOnlineModel")}</div>
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default SplashScreen;
