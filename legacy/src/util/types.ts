// noinspection JSUnusedGlobalSymbols

import { Enum } from "./util.js";

export interface EmCommunicator {
    start(): Promise<number>;
    stop(): void;
    isRunning(): boolean;

    loadEvses(evses: any): EmEvse[];
    saveEvses(file: string): void;

    getEvses(): EmEvse[];
    getEvse(serial: string|null|undefined): EmEvse|undefined;
    getEvseOrThrow(serial: string|null|undefined): EmEvse;
    getEvseByIp(ip: string|null|undefined): EmEvse|undefined;

    addEventListener(types: EmEvseEvent|EmEvseEvent[], handler: EmEvseEventHandler): this;
    removeEventListener(types: EmEvseEvent|EmEvseEvent[], handler: EmEvseEventHandler | undefined): this;
}

export interface EmEvse {
    /**
     * Get information about the EVSE. EVSE does not need to be online or logged in for this.
     */
    getInfo(): EmEvseInfo;

    /**
     * Get currently known EVSE configuration. EVSE does not need to be online or logged in for this.
     */
    getConfig(): EmEvseConfig;

    /**
     * Get live configuration from the EVSE. The EVSE needs to be online and logged in for this.
     * This method is called automatically immediately after a successful login.
     */
    fetchConfig(orCachedUntilSeconds?: number): Promise<EmEvseConfig>;

    /**
     * Get a label for the EVSE. If the name is known (need to be logged in to get the config with name), then
     * that is returned. If no name is known, the brand and model are returned. If no info is known, serial is
     * returned.
     */
    getLabel(): string;

    /**
     * Get the last time a datagram was received from the EVSE.
     */
    getLastSeen(): Date;

    /**
     * Whether the EVSE is online. This is determined by how recent getLastSeen is.
     */
    isOnline(): boolean;

    /**
     * Whether the EVSE has a password saved. Since a password is only saved for the EVSE upon successful login,
     * this means the password was (at least at the time of that login) correct.
     */
    hasPassword(): boolean;

    /**
     * Checks a password against the saved password, without checking at the EVSE (use the login method for that).
     * @param password Password to test against the saved password.
     */
    checkPassword(password: string): boolean;

    /**
     * Whether the app is logged in, i.e. has an active session on the EVSE.
     */
    isLoggedIn(): boolean;

    /**
     * Attempt to login using given password. The EVSE needs to be online for this.
     * If the password is correct, it is also saved for the EVSE.
     *
     * @param password Password to use for logging in to the EVSE. If none is given, use the last-known password.
     * @returns Promise which resolves when the login is successful, or rejects otherwise (e.g. password incorrect
     *          or EVSE not responding).
     */
    login(password?: string): Promise<void>;

    /**
     * Get the current state (at protocol level) of the EVSE. This is only available when the EVSE is online
     * and logged in; otherwise it will return undefined.
     *
     * @returns The current state, or undefined if the EVSE is not online or not logged in.
     */
    getState(): EmEvseState|undefined;

    /**
     * Get the current meta state of the EVSE. This is a computed normalized state based on various aspects
     * of the EVSE's online and login state and its operational state fields. Offered because most apps won't
     * need to know about the protocol-level details, but just want to show some UI.
     *
     * @returns The current meta state.
     */
    getMetaState(): EmEvseMetaState;

    /**
     * Get info about the current charging session.
     * If currently charging, this will return the current session.
     * If a session is planned (reservation), this will return the planned session.
     * If no session is active or planned, this will return the last finished session.
     */
    getCurrentCharge(): EmEvseCurrentCharge|undefined;

    /**
     * Set the EVSE's name. The EVSE needs to be online for this call to work.
     * If the update is successful, the name is also set in EVSE's config.
     * The current (c.q. last known) name can be accessed via getConfig().name.
     *
     * @param name New name to assign to the EVSE.
     * @returns Promise which resolves when the name is successfully set, or rejects otherwise (e.g. invalid name
     *          or EVSE not responding).
     */
    setName(name: string): Promise<void>;

    /**
     * Set whether the EVSE allows charging offline, i.e. without an app. This is usually done via a button or
     * touchpad on the EVSE, and allowing offline charging normally implies that anyone with physical access can
     * start a session, so only enable if the EVSE is on private ground.
     * The EVSE needs to be online for this call to work. If the update is successful, the new status is also
     * set in EVSE's config.
     * The current (c.q. last known) status can be accessed via getConfig().offLineCharge.
     *
     * @param status New offline charging status.
     * @returns Promise which resolves when the status is successfully set, or rejects otherwise (e.g. invalid status
     *          or EVSE not responding).
     */
    setOffLineCharge(status: OffLineChargeStatus): Promise<void>;

    /**
     * Set the EVSE's temperature unit.
     * The EVSE needs to be online for this call to work. If the update is successful, the new unit is also
     * set in EVSE's config.
     * The current (c.q. last known) temperature unit can be accessed via getConfig().temperatureUnit.
     *
     * @param unit New temperature unit to use for the EVSE.
     * @returns Promise which resolves when the temperature unit is successfully set, or rejects otherwise
     *          (e.g. invalid unit or EVSE not responding).
     */
    setTemperatureUnit(unit: TemperatureUnit): Promise<void>;

    /**
     * Set the EVSE's language.
     * The EVSE needs to be online for this call to work. If the update is successful, the new language is also
     * set in EVSE's config.
     * The current (c.q. last known) language can be accessed via getConfig().language.
     *
     * @param language New language to use for the EVSE.
     * @returns Promise which resolves when the language is successfully set, or rejects otherwise (e.g. invalid
     *          language or EVSE not responding).
     */
    setLanguage(language: Language): Promise<void>;

    /**
     * Set the maximum electricity (in amps) the EVSE will deliver. The effective charging current may be
     * lower depending on other factors, such as: the maximum supported by the car's on-board charging circuit;
     * the car's battery state of charge; the car's charging schedule; the battery or EVSE temperature; etc.
     * The EVSE needs to be online for this call to work. If the update is successful, the new value is also
     * set in EVSE's config.
     * The current (c.q. last known) maximum electricity can be accessed via getConfig().maxElectricity.
     *
     * @param amps Maximum current in amps.
     * @returns Promise which resolves when the maximum electricity is successfully set, or rejects otherwise
     *          (e.g. invalid amps value or EVSE not responding).
     */
    setMaxElectricity(amps: number): Promise<void>;

    /**
     * Fetch the EVSE's current system time. The EVSE needs to be online for this call to work.
     */
    fetchSystemTime(): Promise<Date>;

    /**
     * Set the EVSE's system time. The EVSE needs to be online for this call to work. If the time
     * parameter is omitted, uses the application host's current time (that is the preferred way to
     * sync the time since it sets the timestamp only just before sending the datagram onto the
     * network).
     * @param time Specific time to set, as a local JS Date object. If omitted, use the application
     *             host's current time.
     */
    setSystemTime(time?: Date): Promise<void>;

    /**
     * Start charging on given line (plug). The EVSE needs to be online for this call to work.
     *
     * @param params Parameters for starting the charging session. See ChargeStartParams for details.
     * @returns Promise which resolves when the charging session is successfully started, or rejects otherwise
     *          (e.g. invalid amps value or EVSE not responding or invalid EVSE state, like: already charging).
     */
    chargeStart(params: ChargeStartParams): Promise<ChargeStartResult>;

    /**
     * Stop charging on given line (plug). The EVSE needs to be online for this call to work.
     *
     * @param params Parameters for stopping the charging session. See ChargeStopParams for details.
     * @returns Promise which resolves when the charging session is successfully stopped, or rejects otherwise
     *          (e.g. EVSE not responding or invalid EVSE state, like: no active charging session).
     */
    chargeStop(params?: ChargeStopParams): Promise<ChargeStopResult>;

    /**
     * Debug string representation of the EVSE.
     */
    toString(): string;
}

export const enum Phases {
    SINGLE_PHASE = 1,
    THREE_PHASE = 3
}

/**
 * Charge start parameters.
 */
export type ChargeStartParams = {
    /**
     * Maximum current in amps to charge with. The OEM app uses the value obtained from the getOutputElectricity
     * command to get this value, and persists it on the EVSE using the setOutputElectricity command. That command
     * appears to only be used to persist/sync the value between apps (or sessions) and not influence the actual
     * charging current; the EVSE charges with the amps defined here for the charge start.
     * If omitted, the EVSE will charge with the value obtained from getOutputElectricity.
     */
    maxAmps?: number;
    /**
     * Identifier of the charging session. Maximum 16 ASCII characters (truncated if too long).
     * Default if omitted is: current time (even if startAt is set in future) formatted as: yyyyMMddHHmm, plus 4 random
     * trailing numbers (same format is used by the OEM app).
     */
    chargeId?: string;
    /**
     * Identifier of the user starting the session. Maximum 16 ASCII characters (truncated if too long).
     */
    userId?: string;
    /**
     * Date when to start charging. If omitted or in the past, the EVSE will start charging immediately. If the time
     * is in the future, then the EVSE will show a "charging reservation".
     */
    startAt?: Date;
    /**
     * Maximum duration in minutes to charge for. If omitted or zero, there is no duration limit.
     * Maximum value appears to be 65534 minutes.
     */
    maxDurationMinutes?: number;
    /**
     * Maximum energy in kWh to charge. If omitted or zero, there is no energy limit.
     * This value is communicated at protocol level as hundredths of a kWh, so no point specifying it with
     * more than two decimals precision.
     * Maximum value appears to be 655.35 kWh.
     */
    maxEnergyKWh?: number;
    /**
     * Whether to limit charging to single phase. If omitted or false, the EVSE will charge with 3 phases if available.
     * This is only relevant for 3-phase EVSEs; you don't have to set it to true to charge single-phase EVSEs.
     * This feature of limiting 3-phase EVSEs to single phase is only available on some EVSEs - namely only those
     * that have info.canForceSinglePhase set to true (you can inspect this value before offering some option to a
     * user to limit to single phase).
     */
    singlePhase?: boolean;
};

export type ChargeStartResult = {
    reservationResult: ChargeStartReservationResult;
    startResult: number;
    errorReason: ChargeStartErrorReason;
    maxElectricity: number;
};

export type ChargeStopParams = {
    /**
     * Identifier of the user stopping the session. Maximum 16 ASCII characters (truncated if too long).
     */
    userId?: string;
};

export type ChargeStopResult = {
    stopResult: number;
    failReason: number;
}

export type EmCommunicatorConfig = {

    /**
     * UDP port to listen on for incoming EM EVSE datagrams.
     * Default to 28376.
     */
    port: number;

    /**
     * How many seconds after an EVSE's last datagram before considering it offline.
     * EM EVSEs seem to send a datagram every 5 seconds announcing their presence, or once every 10 seconds to keep
     * a login session alive, so we're using 11 seconds as default.,
     */
    offlineAfterLastDatagram: number;

    /**
     * Whether to dump all sent and received datagrams to stdout.
     * Received datagrams are dumped in 2 ways: all raw incoming UDP packet is dumped as hex data (regardless of
     * whether it was recognized and parsed), and if a protocol datagram is recognized by the protocol handler, the
     * (better readable) normalized datagram object parsed from the packet is also dumped.
     */
    dumpDatagrams: boolean;

    /**
     * How often to get the latest configuration from the EVSE, in seconds.
     * Minimum interval is 5 seconds; default is 120 seconds.
     * This is to detect changes in configuration done out-of-band, by other apps (like the OEM app).
     * The periodic refresh is only done when the EVSE is online and the library is logged in.
     * Set to undefined or a numeric value smaller than 5 seconds to disable automatic refresh.
     * Configuration is fetched:
     * - automatically after any successful login;
     * - periodically automatically if the last time it was fetched is longer ago than this interval;
     * - manually if app calls fetchConfig.
     */
    refreshConfigIntervalSeconds?: number;
}

export const DEFAULT_EM_COMMUNICATOR_CONFIG: EmCommunicatorConfig = {
    port: 28376,
    offlineAfterLastDatagram: 11,
    dumpDatagrams: false,
    refreshConfigIntervalSeconds: 120
};

export interface EmDatagram {
    getCommand(): number;
}

export enum EmEvseEvents {
    ADDED = "ADDED",
    CHANGED = "CHANGED",
    REMOVED = "REMOVED",
    DATAGRAM = "DATAGRAM"
}
export type EmEvseEvent = Enum<EmEvseEvents>;
export type EmEvseEventHandler = (evse: EmEvse, event: EmEvseEvent, datagram?: EmDatagram) => void;

export const EmEvseGunStates = {
    UNKNOWN_0: 0,
    DISCONNECTED: 1,   // Seen live when gun not plugged in.
    CONNECTED_UNLOCKED: 2,  // Seen live when just plugged in but not charging yet (l1Electricity=0, outputState=IDLE, currentState=CHARGING).
    UNKNOWN_3: 3,  // Probably used when connected but not charging, or when plugging in and negotiating...
    CONNECTED_LOCKED: 4,  // Seen live while charging and car locked.
    UNKNOWN_5: 5,
    UNKNOWN_6: 6,
    UNKNOWN_7: 7,
    UNKNOWN_8: 8,
    UNKNOWN_9: 9,
    UNKNOWN_10: 10,
    UNKNOWN_OTHER: 254
} as const;
export type EmEvseGunState = Enum<typeof EmEvseGunStates>;

export const EmEvseOutputStates = {
    UNKNOWN_0: 0,
    CHARGING: 1,   // Seen live while charging (auto full charge, the default charge method).
    IDLE: 2, // Seen live when not charging.
    UNKNOWN_3: 3,
    UNKNOWN_4: 4,
    UNKNOWN_5: 5,
    UNKNOWN_6: 6,
    UNKNOWN_7: 7,
    UNKNOWN_8: 8,
    UNKNOWN_9: 9,
    UNKNOWN_10: 10,
    UNKNOWN_OTHER: 254
} as const;
export type EmEvseOutputState = Enum<typeof EmEvseOutputStates>;

export const EmEvseCurrentStates = {
    EVSE_FAULT: 1,
    CHARGING_FAULT_2: 2,
    CHARGING_FAULT_3: 3,
    UNKNOWN_4: 4,
    UNKNOWN_5: 5,
    UNKNOWN_6: 6,
    UNKNOWN_7: 7,
    UNKNOWN_8: 8,
    UNKNOWN_9: 9,
    WAITING_FOR_SWIPE: 10,
    WAITING_FOR_BUTTON: 11,
    NOT_CONNECTED: 12,    // Seen live when not charging and gun not plugged in.
    READY_TO_CHARGE: 13, // Seen live when plugged in but no charge started yet (l1Electricity=0, gunState=2/Connecting, outputState=IDLE)
    CHARGING: 14,  // Seen live while charging (auto full charge, single-phase).
    COMPLETED: 15,
    UNKNOWN_16: 16,
    COMPLETED_FULL_CHARGE: 17,
    UNKNOWN_18: 18,
    UNKNOWN_19: 19,
    CHARGING_RESERVATION: 20,
    UNKNOWN_21: 21,
    UNKNOWN: 254
} as const;
export type EmEvseCurrentState = Enum<typeof EmEvseCurrentStates>;

export const EmEvseErrors = {
    RELAY_STICK_ERROR_L1: 0,
    RELAY_STICK_ERROR_L2: 1,
    RELAY_STICK_ERROR_L3: 2,
    OFFLINE: 3,
    CC_ERROR: 4,
    CP_ERROR: 5,
    EMERGENCY_STOP: 6,
    OVER_TEMPERATURE_INNER: 7,
    OVER_TEMPERATURE_OUTER: 8,
    UNKNOWN_9: 9,
    LEAKAGE_PROTECTION: 10,
    SHORT_CIRCUIT: 11,
    OVER_CURRENT: 12,
    UNGROUNDED: 13,
    OVER_VOLTAGE: 14,
    LOW_VOLTAGE: 15,
    INPUT_POWER_ERROR: 25,
    MAINS_OVERLOAD: 26,
    DIODE_SHORT_CIRCUIT: 27,
    RTC_FAILURE: 28,
    FLASH_MEMORY_FAILURE: 29,
    EEPROM_FAILURE: 30,
    METERING_MODULE_FAILURE: 31
} as const;
export type EmEvseError = Enum<typeof EmEvseErrors>;

export type EmEvseInfo = {
    ip: string;
    port: number;
    serial: string;
    brand?: string;
    model?: string;
    hardwareVersion?: string;
    softwareVersion?: string;
    hotLine?: string;
    // Type reported by the EVSE. This is some number on which certain features are dependent.
    type?: number;
    // This is a field reported by the EVSE on which some features are dependent.
    p51?: number;
    // The number of phases the EVSE can use (1 or 3).
    phases?: Phases;
    // Whether the EVSE can limit a charge to using a single phase even if it has 3 phases.
    // This is required for the ChargeStartParams.singlePhase parameter to work.
    canForceSinglePhase?: boolean;
    // The physical maximum power (in watts) the EVSE can deliver. This is maxElectricity times phase voltage
    // times the number of phases.
    maxPower?: number;
    // The physical maximum electricity (in amps) the EVSE can deliver.
    maxElectricity?: number;
    // Feature flags reported by the EVSE.
    feature?: number;
    // This seems to be some additional feature flags.
    supportNew?: number;
};

export function isEmEvseInfo(obj: any): obj is EmEvseInfo {
    return obj && typeof obj.ip === "string" && typeof obj.port === "number" && typeof obj.serial === "string";
}

export type EmEvseConfig = {
    // Configured name.
    name?: string;
    // Configured language.
    language?: Language;
    // Configured temperature unit.
    temperatureUnit?: TemperatureUnit;
    // Whether the EVSE can charge offline, i.e. from a button on the EVSE, without an app.
    offLineCharge?: OffLineChargeStatus;
    // The configured maximum electricity (in amps) the EVSE will deliver.
    // The effective maximum will be the lowest of this and EmEvseInfo.maxElectricity (and the actual charging rate
    // may be lower if the car's onboard charging circuit is configured at a lower value or is throttling, or the
    // car can't physically charge faster).
    maxElectricity?: number;
};

export type EmEvseState = {
    lineId: number;
    currentPower: number;
    currentAmount: number;
    l1Voltage: number;      // in volts; zero means phase is not connected
    l1Electricity: number;  // in amps
    l2Voltage: number;      // in volts; zero means phase is not connected
    l2Electricity: number;  // in amps
    l3Voltage: number;      // in volts; zero means phase is not connected
    l3Electricity: number;  // in amps
    innerTemp: number;
    outerTemp: number;
    currentState: EmEvseCurrentState;
    gunState: EmEvseGunState;
    outputState: EmEvseOutputState;
    errors: EmEvseError[];
};

export enum EmEvseMetaStates {
    /**
     * EVSE is offline, i.e. no datagrams have been received from it recently.
     */
    OFFLINE = "OFFLINE",
    /**
     * EVSE is online but the library isn't logged in.
     */
    NOT_LOGGED_IN = "NOT_LOGGED_IN",
    /**
     * EVSE is online and logged in but not charging or connected. This state is also used when initializing,
     * when the library has just logged in but no state is determined yet.
     */
    IDLE = "IDLE",
    /**
     * EVSE is online and plugged in but not charging. If a charging session is planned, the meta state will be
     * PLUGGED_IN. In this state, a chargeStart call can be made to start or plan a charging session.
     */
    PLUGGED_IN = "PLUGGED_IN",
    /**
     * EVSE is currently charging.
     */
    CHARGING = "CHARGING",
    /**
     * EVSE is in an error state. The error(s) can be found in getState().errors.
     */
    ERROR = "ERROR"
}
export type EmEvseMetaState = Enum<EmEvseMetaStates>;

export type EmEvseCurrentCharge = {
    port: number;
    /**
     * The current state of the charging session. Seems to correspond to the EVSE's getState().currentState field.
     */
    currentState: EmEvseCurrentState;
    /**
     * Identifier of the charging session, as specified in the chargeStart call.
     */
    chargeId: string;
    startType: number;
    chargeType: number;
    /**
     * Maximum duration (in minutes) the charging session is allowed to last, as specified in the chargeStart call.
     */
    maxDurationMinutes?: number;
    /**
     * Maximum energy (in kWh) the charging session is allowed to deliver, as specified in the chargeStart call.
     */
    maxEnergyKWh?: number;
    /**
     * When the charging session is planned to be started.
     */
    reservationDate: Date;
    /**
     * Identifier of the user who started or planned the session.
     */
    userId: string;
    /**
     * Maximum electricity (in amps) the EVSE will deliver during the charging session.
     */
    maxElectricity: number;
    /**
     * When the charging session was entered (started immediately or planned to be started later, at reservationDate).
     */
    startDate: Date;
    /**
     * How long (in seconds) the session has taken.
     * - For a planned session (currentState == CHARGING_RESERVATION), this will be 0.
     * - For active sessions (currentState == CHARGING), this will be updated regularly (about once every 10 seconds).
     * - For finished sessions (currentState == neither of the above), this will be the duration of that last session.
     */
    durationSeconds: number;
    /**
     * The (cumulative) kWh counter value at the start of the session. This field is only set for active and planned
     * sessions (currentState == CHARGING or CHARGING_RESERVATION). Once a session finishes, it will be zero.
     */
    startKWhCounter: number;
    /**
     * The current (cumulative) kWh counter value. This field is always set to the current value, which for a finished
     * session (since a fresh (planned) session will be a fresh current charge object) will be the final value of that
     * last session.
     */
    currentKWhCounter: number;
    /**
     * The amount of energy (in kWh) delivered during the session. This will be zero for a planned session, or the
     * actual delivered energy for an active or finished session.
     */
    chargeKWh: number;
    chargePrice: number;
    feeType: number;
    chargeFee: number;
};

export const OffLineChargeStatuses = {
    ENABLED: 0,
    DISABLED: 1,
    UNKNOWN_2: 2, // Seen live when offline charge is disabled (app required to start charging session).
    UNKNOWN_3: 3,
    UNKNOWN_4: 4,
    UNKNOWN_5: 5,
    UNKNOWN: 254
} as const;
export type OffLineChargeStatus = Enum<typeof OffLineChargeStatuses>;

export const OffLineChargeActions = {
    UNKNOWN_0: 0,
    SET: 1,     // Seen in an unsolicited SetAndGetOffLineChargeResponse(269) with a status of 2 when offline charging was disabled.
    GET: 2,
    UNKNOWN_3: 3,
    UNKNOWN_4: 4,
    UNKNOWN_5: 5,
    UNKNOWN: 254
} as const;
export type OffLineChargeAction = Enum<typeof OffLineChargeActions>;

export const SystemTimeActions = {
    GET: 0,    // Seen in an unsolicited SettingSystemTime when the evse is reporting its time. Since other calls have actions SET=1 and GET=2, perhaps this means REPORT=0 for unsolicited reports? Need to test an explicit GET.
    SET: 1,
    UNKNOWN_2: 2,
    UNKNOWN_3: 3,
    UNKNOWN_4: 4,
    UNKNOWN_5: 5,
    UNKNOWN: 254
} as const;
export type SystemTimeAction = Enum<typeof SystemTimeActions>;

export const SetAndGetOutputElectricityActions = {
    UNKNOWN_0: 0,
    SET: 1,    // Note: not yet seen.
    GET: 2,    // Note: not yet seen.
    UNKNOWN_3: 3,
    UNKNOWN_4: 4,
    UNKNOWN_5: 5,
    UNKNOWN: 254
} as const;
export type SetAndGetOutputElectricityAction = Enum<typeof SetAndGetOutputElectricityActions>;

export const SetAndGetNickNameActions = {
    SET: 1,
    GET: 2,
    UNKNOWN: 254
} as const;
export type SetAndGetNickNameAction = Enum<typeof SetAndGetNickNameActions>;

export const SetAndGetTemperatureUnitActions = {
    SET: 1,
    GET: 2,
    UNKNOWN: 254
} as const;
export type SetAndGetTemperatureUnitAction = Enum<typeof SetAndGetTemperatureUnitActions>;

export const TemperatureUnits  = {
    CELSIUS: 1,
    FAHRENHEIT: 2,
    UNKNOWN: 254,
} as const;
export type TemperatureUnit = Enum<typeof TemperatureUnits>;

export const GetAndSetSystemTimeActions = {
    SET: 1,
    GET: 2,
    UNKNOWN: 254
} as const;
export type GetAndSetSystemTimeAction = Enum<typeof GetAndSetSystemTimeActions>;

export const SetAndGetLanguageActions = {
    UNKNOWN_0: 0,
    SET: 1,
    GET: 2,
    UNKNOWN_3: 3,
    UNKNOWN_4: 4,
    UNKNOWN_5: 5,
    UNKNOWN: 254
} as const;
export type SetAndGetLanguageAction = Enum<typeof SetAndGetLanguageActions>;

export const Languages = {
    UNKNOWN_0: 0,
    ENGLISH: 1,
    ITALIAN: 2,
    GERMAN: 3,
    FRENCH: 4,
    SPANISH: 5,
    HEBREW: 6,
    UNKNOWN_7: 7,
    UNKNOWN_8: 8,
    UNKNOWN_9: 9,
    UNKNOWN_10: 10,
    UNKNOWN: 254
} as const;
export type Language = Enum<typeof Languages>;

export type DispatchEvent = (event: EmEvseEvent, evse: EmEvse, datagram?: EmDatagram) => void;

export const ChargeStartErrorReasons = {
    NO_ERROR: 0,
    NOT_PLUGGED_IN: 1,
    SYSTEM_ERROR: 2,
    ALREADY_CHARGING: 3,
    SYSTEM_MAINTENANCE: 4,
    INCORRECT_FEE_SET: 5,
    INCORRECT_POWER_SET: 6,
    INCORRECT_TIME_SET: 7,
    UNKNOWN_ERROR: 8,
    RESERVATION_PENDING: 20
} as const;
export type ChargeStartErrorReason = Enum<typeof ChargeStartErrorReasons>;

export const ChargeStartReservationResults = {
    IMMEDIATE_START: 0,            // No reservation planned; start charging immediately.
    RESERVATION_OK: 1,             // Reservation made successfully.
    RESERVATION_NOT_SUPPORTED: 2,  // This wallbox does not support reservations. `ChargeStartParams.startAt` cannot be used.
    RESERVATION_TOO_DISTANT: 3,    // Reservation failed; the start time is too far in the future (more than 24h).
    RESERVATION_IN_PAST: 4,        // Reservation failed; the start time is in the past. The wallbox has started charging immediately.
    SYSTEM_ERROR: 5,               // Reservation failed; system error.
    RESERVATION_EXISTS: 6,         // Reservation failed; there is already a reservation planned.
    ALREADY_CHARGING: 7,           // Reservation failed; the wallbox is already charging.
    INCORRECT_FEE_SET: 8,          // Reservation failed; an incorrect fee has been set.
    INCORRECT_POWER_SET: 9,        // Reservation failed; an incorrect power level has been set.
    INCORRECT_TIME_SET: 10         // Reservation failed; an incorrect time has been set.
} as const;
export type ChargeStartReservationResult = Enum<typeof ChargeStartReservationResults>;
