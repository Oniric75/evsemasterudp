import {clearTimeout} from "node:timers";
import {Communicator} from "./Communicator.js";
import Datagram from "./dgrams/Datagram.js";
import {
    ChargeStartParams,
    ChargeStartResult,
    ChargeStopParams,
    ChargeStopResult,
    type DispatchEvent,
    EmEvse,
    type EmEvseConfig,
    EmEvseCurrentCharge,
    type EmEvseEvent,
    EmEvseEvents,
    EmEvseGunStates,
    type EmEvseInfo,
    type EmEvseMetaState,
    EmEvseMetaStates,
    EmEvseOutputStates,
    type EmEvseState,
    isEmEvseInfo,
    type Language,
    OffLineChargeActions,
    OffLineChargeStatus,
    Phases,
    SetAndGetLanguageActions,
    SetAndGetNickNameActions,
    SetAndGetOutputElectricityActions,
    SetAndGetTemperatureUnitActions,
    SystemTimeActions,
    TemperatureUnit
} from "./util/types.js";
import {decodePassword, encodePassword, logError, logInfo, logWarning, toDate, update} from "./util/util.js";
import {LoginAbstract, LoginConfirm, LoginResponse, RequestLogin} from "./dgrams/impl/Login.js";
import {SingleACStatus} from "./dgrams/impl/SingleACStatus.js";
import {SetAndGetNickName, SetAndGetNickNameResponse} from "./dgrams/impl/SetAndGetNickName.js";
import {SetAndGetTemperatureUnit, SetAndGetTemperatureUnitResponse} from "./dgrams/impl/SetAndGetTemperatureUnit.js";
import {
    SetAndGetOutputElectricity,
    SetAndGetOutputElectricityResponse
} from "./dgrams/impl/SetAndGetOutputElectricity.js";
import {SetAndGetOffLineCharge, SetAndGetOffLineChargeResponse} from "./dgrams/impl/SetAndGetOffLineCharge.js";
import {SetAndGetLanguage, SetAndGetLanguageResponse} from "./dgrams/impl/SetAndGetLanguage.js";
import {GetVersion, GetVersionResponse} from "./dgrams/impl/GetVersion.js";
import {HeadingResponse} from "./dgrams/impl/Heading.js";
import {PasswordErrorResponse} from "./dgrams/impl/PasswordErrorResponse.js";
import {ChargeStart, ChargeStartResponse} from "./dgrams/impl/ChargeStart.js";
import {ChargeStop, ChargeStopResponse} from "./dgrams/impl/ChargeStop.js";
import {ChargeStartError, successReservationResults} from "./errors/ChargeStartError.js";
import {SingleACChargingStatus} from "./dgrams/impl/SingleACChargingStatus.js";
import {SetAndGetSystemTime, SetAndGetSystemTimeResponse} from "./dgrams/impl/SetAndGetSystemTime.js";

export default class Evse implements EmEvse {

    private readonly communicator: Communicator;
    private readonly dispatchEvent: (event: EmEvseEvent, datagram?: Datagram) => void;

    private readonly info: EmEvseInfo;
    private config: EmEvseConfig;
    private lastSeen: Date;
    private lastActiveLogin: Date|undefined = undefined;
    private lastConfigUpdate: Date|undefined;
    private online: boolean;
    private password: string|undefined;
    private state: EmEvseState;
    private currentCharge?: EmEvseCurrentCharge;
    private configUpdatePromise?: Promise<any>;

    constructor(communicator: Communicator,
                dispatchEvent: DispatchEvent,
                info: EmEvseInfo | {info: object, config?: object, lastSeen?: Date|number|string, lastConfigUpdate?: Date|number|string}) {
        this.communicator = communicator;
        this.dispatchEvent = (event: EmEvseEvent, datagram?: Datagram) => dispatchEvent(event, this, datagram);

        if (isEmEvseInfo(info)) {
            // Creating new discovered EVSE.
            this.info = { ... info };
            this.config = {};
            this.lastSeen = new Date();
            this.online = true;
        } else {
            // Loading EVSE from persistent storage.
            if (!isEmEvseInfo(info.info)) {
                throw new Error("Invalid EmEvseInfo in EmEvse constructor: " + JSON.stringify(info.info));
            }
            this.info = { ... info.info };
            this.config = info.config ? { ... info.config } : {};
            this.online = false;
            this.lastSeen = toDate(info.lastSeen);
            this.lastConfigUpdate = toDate(info.lastConfigUpdate);
            this.updateOnlineStatus();
        }
    }

    public getInfo(): EmEvseInfo {
        return this.info;
    }

    public getConfig(): EmEvseConfig {
        return this.config;
    }

    public getLabel() {
        const name = this.getConfig()?.name;
        if (name) return name;
        const brandAndModel = [ this.getInfo().brand, this.getInfo().model ].filter(Boolean).join(" ");
        if (brandAndModel !== "") return brandAndModel;
        return this.getInfo().serial;
    }

    public getLastSeen(): Date {
        return this.lastSeen;
    }

    public getLastConfigUpdate(): Date|undefined {
        return this.lastConfigUpdate;
    }

    public isOnline(): boolean {
        return this.online;
    }

    public isLoggedIn(): boolean {
        return this.isOnline()
            && this.lastActiveLogin !== undefined
            && this.lastActiveLogin.getTime() > (Date.now() - (1000 * 15));
    }

    public hasPassword(): boolean {
        return this.password !== undefined;
    }

    public checkPassword(password: string) {
        return this.password && this.password === password;
    }

    public getState(): EmEvseState|undefined {
        if (!this.isLoggedIn()) return undefined;
        return this.state;
    }

    public getMetaState(): EmEvseMetaState {
        if (!this.isOnline()) return EmEvseMetaStates.OFFLINE;
        if (!this.isLoggedIn()) return EmEvseMetaStates.NOT_LOGGED_IN;
        if (!this.state) return EmEvseMetaStates.IDLE;
        if (this.state.errors?.length > 0) return EmEvseMetaStates.ERROR;
        if (this.state.outputState === EmEvseOutputStates.CHARGING) return EmEvseMetaStates.CHARGING;
        if (this.state.gunState !== EmEvseGunStates.DISCONNECTED) return EmEvseMetaStates.PLUGGED_IN;
        return EmEvseMetaStates.IDLE;
    }

    public getCurrentCharge(): EmEvseCurrentCharge | undefined {
        return this.currentCharge;
    }

    public sendDatagram(datagram: Datagram): Promise<number> {
        if (datagram instanceof HeadingResponse) {
            this.lastActiveLogin = new Date();
            // lastActiveLogin is transient, so no changed event necessary. We need to re-login
            // anyway after an app restart.
        }
        return this.communicator.send(datagram, this);
    }

    public updateIp(ip: string, port: number): boolean {
        this.lastSeen = new Date();
        let changed = false;

        if (this.updateOnlineStatus()) {
            changed = true;
        }

        if (ip !== this.info.ip) {
            this.info.ip = ip;
            changed = true;
        }

        if (port !== this.info.port) {
            this.info.port = port;
            changed = true;
        }

        return changed;
    }

    public updateOnlineStatus(): boolean {
        const now = Math.floor(new Date().getTime() / 1000);
        const lastSeen = this.lastSeen ? Math.floor(this.lastSeen.getTime() / 1000) : 0;
        const onlineNow = lastSeen > now - this.communicator.config.offlineAfterLastDatagram;

        if (onlineNow !== this.online) {
            this.online = onlineNow;
            return true;
        }

        return false;
    }

    public update(datagram: Datagram): boolean {
        if (datagram instanceof LoginAbstract) {
            return this.updateLogin(datagram);
        }
        if (datagram instanceof SingleACStatus) {
            return this.updateSingleAcStatus(datagram);
        }
        if (datagram instanceof SingleACChargingStatus) {
            return this.updateChargingStatus(datagram)
        }
        if (datagram instanceof SetAndGetOffLineChargeResponse) {
            return this.updateOfflineCharging(datagram);
        }
        if (datagram instanceof SetAndGetOutputElectricityResponse) {
            return this.updateOutputElectricity(datagram);
        }
        if (datagram instanceof SetAndGetNickNameResponse) {
            return this.updateNickName(datagram);
        }
        if (datagram instanceof SetAndGetTemperatureUnitResponse) {
            return this.updateTemperatureUnit(datagram);
        }
        if (datagram instanceof SetAndGetLanguageResponse) {
            return this.updateLanguage(datagram);
        }
        if (datagram instanceof GetVersionResponse) {
            return this.updateVersion(datagram);
        }
        if (datagram instanceof PasswordErrorResponse) {
            return this.updatePasswordError(datagram);
        }
        return false;
    }

    private updateLogin(login: LoginAbstract): boolean {
        // Guard against accidental processing of datagrams from other devices.
        if (this.info.serial !== login.getDeviceSerial()) {
            return false;
        }

        this.lastSeen = new Date();
        let changed = this.updateOnlineStatus();

        if (this.info.brand !== login.getBrand()) {
            this.info.brand = login.getBrand();
            changed = true;
        }

        if (this.info.model !== login.getModel()) {
            this.info.model = login.getModel();
            changed = true;
        }

        if (this.info.hardwareVersion !== login.getHardwareVersion()) {
            this.info.hardwareVersion = login.getHardwareVersion();
            changed = true;
        }

        if (this.info.maxPower !== login.getMaxPower()) {
            this.info.maxPower = login.getMaxPower();
            changed = true;
        }

        if (this.info.maxElectricity !== login.getMaxElectricity()) {
            this.info.maxElectricity = login.getMaxElectricity();
            changed = true;
        }

        if (this.info.hotLine !== login.getHotLine()) {
            this.info.hotLine = login.getHotLine();
            changed = true;
        }

        if (this.info.type !== login.getType()) {
            this.info.type = login.getType();
            changed = true;
        }

        const phases = [10, 11, 12, 13, 14, 15, 22, 23, 24, 25].includes(this.info.type) ? Phases.THREE_PHASE : Phases.SINGLE_PHASE;
        if (this.info.phases !== phases) {
            this.info.phases = phases;
            changed = true;
        }

        if (this.info.p51 !== login.getP51()) {
            this.info.p51 = login.getP51();
            changed = true;
        }

        const canForceSinglePhase = [22, 23, 24, 25].includes(this.info.type) && this.info.p51 < 11;
        if (this.info.canForceSinglePhase !== canForceSinglePhase) {
            this.info.canForceSinglePhase = canForceSinglePhase;
            changed = true;
        }

        return changed;
    }

    private updateSingleAcStatus(datagram: SingleACStatus): boolean {
        let changed = this.state === undefined;
        if (!this.state) this.state = {} as EmEvseState;
        const currentPower = Math.floor(Math.max(
            datagram.currentPower,
            (datagram.l1Voltage * datagram.l1Electricity) + (datagram.l2Voltage * datagram.l2Electricity) + (datagram.l3Voltage * datagram.l3Electricity)
        ));
        if (update(this.state, "currentPower", currentPower)) changed = true;
        if (update(this.state, "currentAmount", datagram.totalKWhCounter)) changed = true;
        if (update(this.state, "l1Voltage", datagram.l1Voltage)) changed = true;
        if (update(this.state, "l1Electricity", datagram.l1Electricity)) changed = true;
        if (update(this.state, "l2Voltage", datagram.l2Voltage)) changed = true;
        if (update(this.state, "l2Electricity", datagram.l2Electricity)) changed = true;
        if (update(this.state, "l3Voltage", datagram.l3Voltage)) changed = true;
        if (update(this.state, "l3Electricity", datagram.l3Electricity)) changed = true;
        if (update(this.state, "innerTemp", datagram.innerTemp)) changed = true;
        if (update(this.state, "outerTemp", datagram.outerTemp)) changed = true;
        if (update(this.state, "currentState", datagram.currentState)) changed = true;
        if (update(this.state, "gunState", datagram.gunState)) changed = true;
        if (update(this.state, "outputState", datagram.outputState)) changed = true;
        if (update(this.state, "errors", datagram.errors)) changed = true;
        return changed;
    }

    private updateChargingStatus(datagram: SingleACChargingStatus) {
        let changed = this.currentCharge === undefined;
        if (!this.currentCharge) this.currentCharge = {} as EmEvseCurrentCharge;
        if (update(this.currentCharge, "port", datagram.port)) changed = true;
        if (update(this.currentCharge, "currentState", datagram.currentState)) changed = true;
        if (update(this.currentCharge, "chargeId", datagram.chargeId)) changed = true;
        if (update(this.currentCharge, "startType", datagram.startType)) changed = true;
        if (update(this.currentCharge, "chargeType", datagram.chargeType)) changed = true;
        if (update(this.currentCharge, "maxDurationMinutes", datagram.maxDurationMinutes)) changed = true;
        if (update(this.currentCharge, "maxEnergyKWh", datagram.maxEnergyKWh)) changed = true;
        if (update(this.currentCharge, "reservationDate", datagram.reservationDate)) changed = true;
        if (update(this.currentCharge, "userId", datagram.userId)) changed = true;
        if (update(this.currentCharge, "maxElectricity", datagram.maxElectricity)) changed = true;
        if (update(this.currentCharge, "startDate", datagram.startDate)) changed = true;
        if (update(this.currentCharge, "durationSeconds", datagram.durationSeconds)) changed = true;
        if (update(this.currentCharge, "startKWhCounter", datagram.startKWhCounter)) changed = true;
        if (update(this.currentCharge, "currentKWhCounter", datagram.currentKWhCounter)) changed = true;
        if (update(this.currentCharge, "chargeKWh", datagram.chargeKWh)) changed = true;
        if (update(this.currentCharge, "chargePrice", datagram.chargePrice)) changed = true;
        if (update(this.currentCharge, "feeType", datagram.feeType)) changed = true;
        if (update(this.currentCharge, "chargeFee", datagram.chargeFee)) changed = true;
        return changed;
    }

    /**
     * Serialize this EmEvse to a plain object.
     * @returns Plain object representing this EmEvse.
     */
    public serialize(): object {
        return {
            info: this.info,
            config: this.config,
            lastConfigUpdate: this.lastConfigUpdate ? Math.floor(this.lastConfigUpdate.getTime() / 1000) : undefined,
            lastSeen: this.lastSeen ? Math.floor(this.lastSeen.getTime() / 1000) : undefined,
            password: encodePassword(this.password)
        };
    }

    /**
     * Deserialize an EmEvse from a plain object.
     * @param communicator EmCommunicator instance to associate with the deserialized EmEvse.
     * @param dispatchEvent Function to dispatch events via the communicator.
     * @param data Plain object to deserialize.
     * @returns Deserialized EmEvse instance, or undefined if the plain object cannot be deserialized to a valid EmEvse.
     */
    public static deserialize(communicator: Communicator, dispatchEvent: DispatchEvent, data: any): Evse|undefined {
        if (typeof data === "string") {
            data = JSON.parse(data);
        }
        if (typeof data !== "object") {
            logWarning(`Evse.deserialize: data is not an object but a ${typeof data}: ${JSON.stringify(data)}`);
            return undefined;
        }

        if (!isEmEvseInfo(data.info)) {
            logWarning('Evse.deserialize: data.info is not an EmEvseInfo: ${JSON.stringify(data)}')
            return undefined;
        }

        const evse = new Evse(
            communicator,
            dispatchEvent,
            data
        );

        if (typeof data.password === "string") evse.password = decodePassword(data.password);

        return evse;
    }

    /**
     * Merge fields of other EmEvse into this instance.
     * @param other Other EmEvse whose fields to merge into this instance.
     * @returns True if any fields on this instance were changed, false if no fields were changed.
     */
    public merge(other: Evse): boolean {
        if (this.info.serial !== other.info.serial) {
            return false;
        }

        let changed = false;

        if (other.password && (!this.password || other.password !== this.password)) {
            this.password = other.password;
            changed = true;
        }

        if (other.lastSeen && (!this.lastSeen || other.lastSeen > this.lastSeen)) {
            this.lastSeen = other.lastSeen;
            changed = true;
        }

        if (this.updateOnlineStatus()) {
            changed = true;
        }

        if (other.info.ip && (!this.info.ip || other.info.ip !== this.info.ip)) {
            this.info.ip = other.info.ip;
            changed = true;
        }

        if (other.info.port && (!this.info.port || other.info.port !== this.info.port)) {
            this.info.port = other.info.port;
            changed = true;
        }

        if (other.info.brand && (!this.info.brand || other.info.brand !== this.info.brand)) {
            this.info.brand = other.info.brand;
            changed = true;
        }

        if (other.info.model && (!this.info.model || other.info.model !== this.info.model)) {
            this.info.model = other.info.model;
            changed = true;
        }

        if (other.info.hardwareVersion && (!this.info.hardwareVersion || other.info.hardwareVersion !== this.info.hardwareVersion)) {
            this.info.hardwareVersion = other.info.hardwareVersion;
            changed = true;
        }

        if (other.info.softwareVersion && (!this.info.softwareVersion || other.info.softwareVersion !== this.info.softwareVersion)) {
            this.info.softwareVersion = other.info.softwareVersion;
            changed = true;
        }

        if (other.info.hotLine && (!this.info.hotLine || other.info.hotLine !== this.info.hotLine)) {
            this.info.hotLine = other.info.hotLine;
            changed = true;
        }

        if (other.info.maxPower && (!this.info.maxPower || other.info.maxPower !== this.info.maxPower)) {
            this.info.maxPower = other.info.maxPower;
            changed = true;
        }

        if (other.info.maxElectricity && (!this.info.maxElectricity || other.info.maxElectricity !== this.info.maxElectricity)) {
            this.info.maxElectricity = other.info.maxElectricity;
            changed = true;
        }

        if (other.info.feature !== undefined && other.info.feature !== this.info.feature) {
            this.info.feature = other.info.feature;
            changed = true;
        }

        if (other.info.supportNew !== undefined && other.info.supportNew !== this.info.supportNew) {
            this.info.supportNew = other.info.supportNew;
            changed = true;
        }

        if (other.info.phases !== undefined && other.info.phases !== this.info.phases) {
            this.info.phases = other.info.phases;
            changed = true;
        }

        if (other.info.type !== undefined && other.info.type !== this.info.type) {
            this.info.type = other.info.type;
            changed = true;
        }

        if (other.info.p51 !== undefined && other.info.p51 !== this.info.p51) {
            this.info.p51 = other.info.p51;
            changed = true;
        }

        if (other.info.canForceSinglePhase !== undefined && other.info.canForceSinglePhase !== this.info.canForceSinglePhase) {
            this.info.canForceSinglePhase = other.info.canForceSinglePhase;
            changed = true;
        }

        if (other.config.name && (!this.config.name || other.config.name !== this.config.name)) {
            this.config.name = other.config.name;
            changed = true;
        }

        this.config = { ... this.config, ... other.config };

        return changed;
    }

    public async waitForResponse(command: number|number[], timeoutMillis: number): Promise<Datagram> {
        if (typeof command === "number") command = [ command ];
        return new Promise((resolve, reject) => {
            let timeout: NodeJS.Timeout;
            const listener = (evse: Evse, event: EmEvseEvent, datagram?: Datagram) => {
                if (datagram && evse.info.serial === this.info.serial && command.includes(datagram.getCommand())) {
                    clearTimeout(timeout);
                    this.communicator.removeEventListener(EmEvseEvents.DATAGRAM, listener);
                    resolve(datagram);
                }
            };
            this.communicator.addEventListener(EmEvseEvents.DATAGRAM, listener);
            timeout = setTimeout(() => {
                this.communicator.removeEventListener(EmEvseEvents.DATAGRAM, listener);
                reject(new Error(`Timeout (${timeoutMillis} ms) waiting for response with command ${command}`));
            }, timeoutMillis);
        });
    }

    public async login(password?: string) {
        if (password === undefined && !this.hasPassword()) {
            throw new Error("No saved password to use for login");
        }
        // 1. Send the RequestLogin datagram, explicitly using the specified password. Without an
        // explicit password on the datagram, sendDatagram will fill the existing EVSE password (which
        // will also happen if no password is passed here).
        await this.sendDatagram(new RequestLogin().setDevicePassword(password));
        // 2. Wait for the EVSE to reply with a LoginResponse (correct password)
        // or a PasswordErrorResponse (invalid password).
        const response = await this.waitForResponse([LoginResponse.COMMAND, PasswordErrorResponse.COMMAND], 3000);
        if (response instanceof PasswordErrorResponse) {
            throw new Error("Invalid password");
        }
        // 3. If we get the LoginResponse then the password was correct, so set it on this instance.
        if (password !== undefined && this.password !== password) {
            this.password = password;
            this.dispatchEvent(EmEvseEvents.CHANGED, response);
        }
        // 4. Send the LoginConfirm, completing the login flow. After this the EVSE can take commands.
        await this.sendDatagram(new LoginConfirm().setDevicePassword(password));
        // 5. Mark this evse as having an active session.
        this.lastActiveLogin = new Date();
        // 6. Request EVSE's configuration. We don't need to wait for this; the login is complete.
        this.fetchConfig().catch(error => {
            logError(`Failed to get configuration for ${this.info.serial} after login: ${error.message}`);
        });
    }

    /**
     * Fetch current configuration from EVSE. The EVSE needs to be online and logged in for this.
     * Optionally, if the configuration was fetched recently (within orCachedUntilSeconds), the currently known
     * configuration is returned without fetching it again.
     * @param orCachedUntilSeconds If the configuration was recently fetched (within the last specified
     *                             number of seconds), then return the current config without fetching
     *                             from the EVSE again.
     */
    public async fetchConfig(orCachedUntilSeconds: number = 5): Promise<EmEvseConfig> {
        // If we're already busy getting the configuration, then recycle that promise.
        if (this.configUpdatePromise === undefined) {
            if (this.lastConfigUpdate && this.lastConfigUpdate.getTime() > (Date.now() - (orCachedUntilSeconds * 1000))) {
                return this.config;
            }
            // Set up the receivers for the configuration datagrams. We do this before sending out the
            // requests to avoid missing any responses for earlier requests while we're still busy
            // sending out the later requests.
            this.configUpdatePromise = Promise.all([
                this.waitForResponse(SetAndGetNickNameResponse.COMMAND, 6000),
                this.waitForResponse(SetAndGetLanguageResponse.COMMAND, 6000),
                this.waitForResponse(SetAndGetOffLineChargeResponse.COMMAND, 6000),
                this.waitForResponse(SetAndGetTemperatureUnitResponse.COMMAND, 6000),
                this.waitForResponse(SetAndGetOutputElectricityResponse.COMMAND, 6000),
                this.waitForResponse(GetVersionResponse.COMMAND, 6000)
            ]);

            // Send the datagrams. We don't wait for each one to be flushed to the network.
            this.sendDatagram(new SetAndGetNickName().setAction(SetAndGetNickNameActions.GET)).then();
            this.sendDatagram(new SetAndGetLanguage().setAction(SetAndGetLanguageActions.GET)).then();
            this.sendDatagram(new SetAndGetOffLineCharge().setAction(OffLineChargeActions.GET)).then();
            this.sendDatagram(new SetAndGetOutputElectricity().setAction(SetAndGetOutputElectricityActions.GET)).then();
            this.sendDatagram(new SetAndGetTemperatureUnit().setAction(SetAndGetTemperatureUnitActions.GET)).then();
            this.sendDatagram(new GetVersion()).then();
            logInfo(`Fetching config for ${this.toString()}`);
        }

        // Wait until all responses are in. If some responses are lost, this composite promise will fail
        // due to one of the underlying promises timing out.
        try {
            await this.configUpdatePromise;
        } finally {
            this.configUpdatePromise = undefined;
        }

        // If we get here then all configuration was received (and EVSE changed events were sent). We
        // only mark the time that configuration was last updated, so we can know later on if we need
        // to refresh. Note: we don't send out any CHANGED event here, because the incoming response
        // datagrams will already have gone through the update() method, and sent out events if there
        // actually were changes in config.
        this.lastConfigUpdate = new Date();
        return this.config;
    }

    public setDatagramPassword(datagram: Datagram) {
        if (this.password !== undefined) {
            datagram.setDevicePassword(this.password);
            return true;
        }
        return false;
    }

    public toString(): string {
        const model = [ this.info.brand, this.info.model ].filter(Boolean).join(" ");
        return `[${this.info.serial}${model ? " " + model : ""} @ ${this.info.ip} ${EmEvseMetaStates[this.getMetaState()]}]`;
    }

    private updateOfflineCharging(datagram: SetAndGetOffLineChargeResponse) {
        if (this.config.offLineCharge !== datagram.getStatus()) {
            this.config.offLineCharge = datagram.getStatus();
            return true;
        }
        return false;
    }

    private updateNickName(datagram: SetAndGetNickNameResponse) {
        if (!datagram.getNickName()) return false;
        if (datagram.getNickName() !== this.config.name) {
            this.config.name = datagram.getNickName();
            return true;
        }
        return false;
    }

    private updateTemperatureUnit(datagram: SetAndGetTemperatureUnitResponse) {
        if (!datagram.getTemperatureUnit()) return false;
        if (datagram.getTemperatureUnit() !== this.config.temperatureUnit) {
            this.config.temperatureUnit = datagram.getTemperatureUnit();
            return true;
        }
        return false;
    }

    private updateLanguage(datagram: SetAndGetLanguageResponse): boolean {
        if (!datagram.getLanguage()) return false;
        if (datagram.getLanguage() !== this.config.language) {
            this.config.language = datagram.getLanguage();
            return true;
        }
        return false;
    }

    private updateVersion(datagram: GetVersionResponse) {
        let changed = false;

        if (datagram.getHardwareVersion() && datagram.getHardwareVersion() !== this.info.hardwareVersion) {
            this.info.hardwareVersion = datagram.getHardwareVersion();
            changed = true;
        }

        if (datagram.getSoftwareVersion() && datagram.getSoftwareVersion() !== this.info.softwareVersion) {
            this.info.softwareVersion = datagram.getSoftwareVersion();
            changed = true;
        }

        if (datagram.getFeature() !== undefined && datagram.getFeature() !== this.info.feature) {
            this.info.feature = datagram.getFeature();
            changed = true;
        }

        if (datagram.getSupportNew() !== undefined && datagram.getSupportNew() !== this.info.supportNew) {
            this.info.supportNew = datagram.getSupportNew();
            changed = true;
        }

        return changed;
    }

    private updateOutputElectricity(datagram: SetAndGetOutputElectricityResponse) {
        if (datagram.getElectricity() !== this.config.maxElectricity) {
            this.config.maxElectricity = datagram.getElectricity();
            return true;
        }
        return false;
    }


    private updatePasswordError(datagram: PasswordErrorResponse) {
        const wasLoggedIn = this.isLoggedIn();
        this.lastActiveLogin = undefined;
        if (wasLoggedIn && !this.isLoggedIn()) {
            this.dispatchEvent(EmEvseEvents.CHANGED, datagram);
            return true;
        }
        return false;
    }

    public async setName(name: string): Promise<void> {
        await this.sendDatagram(new SetAndGetNickName().setAction(SetAndGetNickNameActions.SET).setNickName("ACP#" + name));
        const response = await this.waitForResponse(SetAndGetNickNameResponse.COMMAND, 5000) as SetAndGetNickNameResponse;
        if (response.getNickName() !== name) {
            throw new Error(`Failed to set name '${name}': EVSE reported back name '${response.getNickName()}'`);
        }
        this.config.name = name;
        this.dispatchEvent(EmEvseEvents.CHANGED, response);
    }

    public async setOffLineCharge(status: OffLineChargeStatus): Promise<void> {
        await this.sendDatagram(new SetAndGetOffLineCharge().setAction(OffLineChargeActions.SET).setStatus(status));
        const response = await this.waitForResponse(SetAndGetOffLineChargeResponse.COMMAND, 5000) as SetAndGetOffLineChargeResponse;
        if (response.getStatus() != status) {
            throw new Error(`Failed to set offlineCharge to ${status}: EVSE reported back status ${response.getStatus()}`);
        }
        this.config.offLineCharge = status;
        this.dispatchEvent(EmEvseEvents.CHANGED, response);
    }

    public async setTemperatureUnit(unit: TemperatureUnit): Promise<void> {
        await this.sendDatagram(new SetAndGetTemperatureUnit().setAction(SetAndGetTemperatureUnitActions.SET).setTemperatureUnit(unit));
        const response = await this.waitForResponse(SetAndGetTemperatureUnitResponse.COMMAND, 5000) as SetAndGetTemperatureUnitResponse;
        if (response.getTemperatureUnit() !== unit) {
            throw new Error(`Failed to set temperature unit to ${unit}: EVSE reported back unit ${response.getTemperatureUnit()}`);
        }
        this.config.temperatureUnit = unit;
        this.dispatchEvent(EmEvseEvents.CHANGED, response);
    }

    public async setLanguage(language: Language): Promise<void> {
        await this.sendDatagram(new SetAndGetLanguage().setAction(SetAndGetLanguageActions.SET).setLanguage(language));
        const response = await this.waitForResponse(SetAndGetLanguageResponse.COMMAND, 5000) as SetAndGetLanguageResponse;
        if (response.getLanguage() !== language) {
            throw new Error(`Failed to set language to ${language}: EVSE reported back language ${response.getLanguage()}`);
        }
        this.config.language = language;
        this.dispatchEvent(EmEvseEvents.CHANGED, response);
    }

    public async setMaxElectricity(amps: number): Promise<void> {
        await this.sendDatagram(new SetAndGetOutputElectricity().setAction(SetAndGetOutputElectricityActions.SET).setElectricity(amps));
        const response = await this.waitForResponse(SetAndGetOutputElectricityResponse.COMMAND, 5000) as SetAndGetOutputElectricityResponse;
        if (response.getElectricity() !== amps) {
            throw new Error(`Failed to set output electricity to ${amps}: EVSE reported back ${response.getElectricity()}`);
        }
        this.dispatchEvent(EmEvseEvents.CHANGED, response);
    }

    public async fetchSystemTime(): Promise<Date> {
        await this.sendDatagram(new SetAndGetSystemTime().setAction(SystemTimeActions.GET));
        const response = await this.waitForResponse(SetAndGetSystemTimeResponse.COMMAND, 5000) as SetAndGetSystemTimeResponse;
        return response.getTime();
    }

    public async setSystemTime(time?: Date): Promise<void> {
        const datagram = new SetAndGetSystemTime().setAction(SystemTimeActions.SET);
        if (time) datagram.setTime(time);
        await this.sendDatagram(datagram);
        const response = await this.waitForResponse(SetAndGetSystemTimeResponse.COMMAND, 5000) as SetAndGetSystemTimeResponse;
        // Require the set date and the returned date to be within 2 seconds of each other.
        if (Math.abs(response.getTime().getTime() - datagram.getTime().getTime()) > 2000) {
            throw new Error(`Failed to set system time to ${datagram.getTime()}: EVSE reported back ${response.getTime()}`);
        }
    }

    public async chargeStart(params: ChargeStartParams = {}): Promise<ChargeStartResult> {
        const maxAmps = params.maxAmps || this.config.maxElectricity;
        if (!maxAmps) {
            throw new Error("No maxAmps value specified for chargeStart, and none available from configuration.");
        } else {
            const evseMaxAmps = this.getInfo().maxElectricity || 16;
            if (maxAmps < 6 || maxAmps > evseMaxAmps) {
                throw new Error(`Invalid maxAmps value ${maxAmps} specified for chargeStart; valid range is 6-${evseMaxAmps}A`);
            }
        }

        const singlePhase = params.singlePhase || this.info.phases !== Phases.THREE_PHASE;

        const chargeStart = new ChargeStart()
            .setLineId(singlePhase ? 1 : 2)
            .setChargeType(singlePhase ? 11 : 1)
            .setMaxElectricity(maxAmps)
            .setUserId(params.userId)
            .setChargeId(params.chargeId)
            .setReservationDate(params.startAt)
            .setMaxDurationMinutes(params.maxDurationMinutes)
            .setMaxEnergyKWh(params.maxEnergyKWh);
        await this.sendDatagram(chargeStart);
        const response = await this.waitForResponse(ChargeStartResponse.COMMAND, 5000) as ChargeStartResponse;

        if (response.getErrorReason() || !successReservationResults.includes(response.getReservationResult())) {
            throw new ChargeStartError(response);
        }

        // If a different maxAmps was requested than the currently configured value, then update the configuration.
        // Don't fail the chargeStart if this config write fails because charging has started; just log any error.
        if (maxAmps !== this.config.maxElectricity) {
            this.setMaxElectricity(maxAmps).catch(error => {
                logError(`Failed to change maxElectricity config to ${maxAmps}A after successful chargeStart for EVSE ${this.info.serial}: ${error.message}. The EVSE will still have the old configured value for subsequent charges that don't explicitly set maxAmps, and for other apps.`);
            });
        }

        return {
            reservationResult: response.getReservationResult(),
            startResult: response.getStartResult(),
            errorReason: response.getErrorReason(),
            maxElectricity: response.getMaxElectricity()
        };
    }

    public async chargeStop(params: ChargeStopParams = {}): Promise<ChargeStopResult> {
        const chargeStop = new ChargeStop().setUserId(params.userId);
        await this.sendDatagram(chargeStop);
        const response = await this.waitForResponse(ChargeStopResponse.COMMAND, 5000) as ChargeStopResponse;

        if (response.getFailReason()) {
            throw new Error(`chargeStop failed with reason ${response.getFailReason()}`);
        }

        return {
            stopResult: response.getStopResult(),
            failReason: response.getFailReason()
        };
    }
}
