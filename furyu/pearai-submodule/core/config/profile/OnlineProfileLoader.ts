import { ControlPlaneClient } from "../../control-plane/client.js";
import { ContinueConfig, IDE, IdeSettings } from "../../index.js";
import { FURYU_ONLINE_PROFILE_ID } from "../furyu/localMode.js";
import doLoadConfig from "./doLoadConfig.js";
import { IProfileLoader } from "./IProfileLoader.js";

/** Same on-disk config as the local profile, without the offline overlay. */
export default class OnlineProfileLoader implements IProfileLoader {
  profileId = FURYU_ONLINE_PROFILE_ID;
  profileTitle = "Modelo online";

  constructor(
    private ide: IDE,
    private ideSettingsPromise: Promise<IdeSettings>,
    private controlPlaneClient: ControlPlaneClient,
    private writeLog: (message: string) => Promise<void>,
  ) {}

  async doLoadConfig(): Promise<ContinueConfig> {
    return doLoadConfig(
      this.ide,
      this.ideSettingsPromise,
      this.controlPlaneClient,
      this.writeLog,
      undefined,
      "online",
    );
  }

  setIsActive(isActive: boolean): void {}
}
