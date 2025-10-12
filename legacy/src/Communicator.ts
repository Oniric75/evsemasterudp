import {createSocket, RemoteInfo, Socket} from "node:dgram";
import * as fs from "node:fs";
import {Buffer} from "node:buffer";
import {homedir} from "node:os";
import {dumpDebug, logError, logInfo, logWarning} from "./util/util.js";
import {parseDatagrams} from "./dgrams/index.js";
import {
    DEFAULT_EM_COMMUNICATOR_CONFIG,
    EmCommunicator,
    EmCommunicatorConfig,
    EmEvseEvent,
    EmEvseEventHandler,
    EmEvseEvents
} from "./util/types.js";
import Evse from "./Evse.js";
import Datagram from "./dgrams/Datagram.js";
import {Heading, HeadingResponse} from "./dgrams/impl/Heading.js";
import {Login} from "./dgrams/impl/Login.js";
import {SingleACStatus, SingleACStatusResponse} from "./dgrams/impl/SingleACStatus.js";

type EmEvseEventListener = {
    types: EmEvseEvent[];
    handler: EmEvseEventHandler;
};

export class Communicator implements EmCommunicator {

    public readonly config: EmCommunicatorConfig;

    private socket: Socket|null = null;

    private periodicChecksInterval: NodeJS.Timeout|null = null;

    private readonly evses: Evse[] = [];

    private listeners: EmEvseEventListener[] = [];

    private supportsBroadcast = false;

    constructor(config: Partial<EmCommunicatorConfig> = {}) {
        this.config = { ... DEFAULT_EM_COMMUNICATOR_CONFIG, ... config };
    }

    public async start(): Promise<number> {
        if (this.socket) return this.socket.address().port;

        return new Promise((resolve, reject) => {
            this.socket = createSocket({type: 'udp4', reuseAddr: true});
            let starting = true;

            if (this.periodicChecksInterval) clearInterval(this.periodicChecksInterval);
            this.periodicChecksInterval = setInterval(this.periodicChecks.bind(this), 5000);

            this.socket.on("error", (err) => {
                logError(`Socket error: ${err.message}\n${err.stack}`)
                if (starting) {
                    reject(err);
                }
            });

            this.socket.on("message", (buffer: Buffer, rinfo: RemoteInfo) => {
                try {
                    if (this.config.dumpDatagrams) {
                        const cmd = buffer.length >= 21 ? buffer.readUInt16BE(19) : 0;
                        dumpDebug(`<- IN: buffer with command ${cmd} [${buffer.toString("hex")}]`);
                    }

                    const datagrams = parseDatagrams(buffer);

                    datagrams.forEach(datagram => {
                        if (this.config.dumpDatagrams) {
                            dumpDebug(`<- IN: ${datagram.toString()}`);
                        }

                        const evse = this.updateEvse(datagram, rinfo);
                        this.dispatchEvent(EmEvseEvents.DATAGRAM, evse, datagram);

                        if (datagram instanceof Login) {
                            // If we are not logged in now (evse's lastHeadingResponse is too long ago), and we have
                            // a password, then we can log in.
                            if (!evse.isLoggedIn() && evse.hasPassword()) {
                                evse.login().then();
                            }
                        }
                        if (datagram instanceof Heading) {
                            // The Heading datagram is sent by the EVSE (explicitly to us - this is not a broadcast)
                            // every 10 seconds when we are logged in, and seems to keep our session alive. If we didn't
                            // get a Heading datagram for a while, we are logged out, and we should log in again by sending
                            // a RequestLogin datagram. We always respond with a HeadingResponse datagram to keep our
                            // session alive, and in the evse instance we keep track of the last time we sent such a
                            // HeadingResponse. We check periodically if that is too long ago, and log in again.
                            evse.sendDatagram(new HeadingResponse()).then();
                        }
                        if (datagram instanceof SingleACStatus) {
                            evse.sendDatagram(new SingleACStatusResponse()).then();
                        }
                    });
                } catch (error) {
                    logError(`${error.message}\n${error.stack}`);
                }
            });

            this.socket.on('error', (error: any) => {
                if (error.code === 'EADDRINUSE') {
                    logError(`Port ${this.config.port} is already in use. Please close any other EVSE monitoring sessions and try again.`);
                    starting = false;
                    reject(error);
                } else {
                    logError(`Socket error: ${error.message}`);
                    starting = false;
                    reject(error);
                }
            });

            this.socket.bind(this.config.port, () => {
                try {
                    this.socket.setBroadcast(true);
                    this.supportsBroadcast = true;
                    // Send a broadcast RequestLogin to all EVSEs on the network. Due to the null password they will respond
                    // with a PasswordErrorResponse, and not give out any info, but at least we'll have discovered the IP,
                    // and we could ask user to provide a password to try with a targeted RequestLogin.
                    // const buffer = new RequestLogin().setDeviceSerial("\x00\x00\x00\x00\x00\x00\x00\x00").pack();
                    // this.socket.send(buffer, 0, buffer.length, 7248, '255.255.255.255', (error: Error|null, bytes: number) => {
                    //     if (error) {
                    //         console.error(error);
                    //     } else {
                    //         console.log(`Sent RequestLogin (${bytes} bytes)`);
                    //     }
                    // });
                } catch (error) {
                    logWarning(`UDP socket does not support broadcasting; busy EVSEs will not be auto-discovered. ${error.message}`);
                }
                const address = this.socket.address();
                logInfo(`UDP socket listening on port ${address.port}`);
                starting = false;
                resolve(address.port);
            });
        });
    }

    public stop() {
        logInfo("Stopping...");
        if (this.periodicChecksInterval) {
            clearInterval(this.periodicChecksInterval);
            this.periodicChecksInterval = null;
        }
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }

    /**
     * Load EVSEs into the communicator. The `evses` can be any of the following:
     * - An array of EVSE objects, or a JSON string of such an array.
     * - A single EVSE object, or a JSON string of such an object.
     * - A string file path from where to load the EVSEs.
     * @param evses EVSEs to load.
     */
    public loadEvses(evses: any): Evse[] {
        evses = this.getEvsesAsArray(evses);
        const loadedEvses: Evse[] = [];
        for (let maybeEvse of evses) {
            let evse = maybeEvse;
            if (typeof evse === "string") {
                evse = JSON.parse(evse);
            }
            evse = Evse.deserialize(this, this.dispatchEvent.bind(this), evse);
            if (!evse) continue;
            loadedEvses.push(evse);
            const existing = this.getEvse(evse.getInfo().serial);
            if (existing) {
                if (existing.merge(evse)) {
                    this.dispatchEvent(EmEvseEvents.CHANGED, evse);
                }
            } else {
                this.evses.push(evse);
                this.dispatchEvent(EmEvseEvents.ADDED, evse);
                this.dispatchEvent(EmEvseEvents.CHANGED, evse);
            }
        }
        if (loadedEvses.length > 0) {
            this.periodicChecks();
        }
        return loadedEvses;
    }

    /**
     * Normalize EVSEs from any type to an array.
     * Each array element is still of type any and will be deserialized in EmEvse.deserialize.
     * @param evses EVSEs to normalize to an array.
     * @private
     */
    private getEvsesAsArray(evses: any) {
        if (typeof evses === "string" && !evses.startsWith("{") && !evses.startsWith("[")) {
            let file = evses;
            if (file.startsWith("~/")) {
                file = homedir() + file.slice(1);
            }
            if (fs.existsSync(file)) {
                logInfo(`Loading EVSEs from file ${evses}`);
                evses = fs.readFileSync(file, "utf-8");
            } else {
                // A non-array / non-object was passed which we treat as a file path, but the file does not exist.
                logInfo(`Attempting to load EVSEs from file ${evses} but it does not exist; zero EVSEs loaded.`);
                return [];
            }
        }
        if (typeof evses === "string") {
            evses = JSON.parse(evses);
        }
        if (typeof evses === "object") {
            if (evses.serial) {
                evses = [evses];
            } else {
                evses = Object.values(evses);
            }
        }
        return Array.isArray(evses) ? evses : [];
    }

    /**
     * Save EVSEs currently in communicator to file.
     * @param file File path to save EVSEs to.
     */
    public saveEvses(file: string) {
        logInfo(`Saving ${this.evses.length} EVSE${this.evses.length === 1 ? '' : 's'} to file ${file}`);
        if (file.startsWith("~/")) {
            file = homedir() + file.slice(1);
        }
        const serializedEvses = this.evses.map(evse => evse.serialize());
        fs.writeFileSync(file, JSON.stringify(serializedEvses, null, 2), { flag: "w" });
    }

    public isRunning(): boolean {
        return Boolean(this.socket);
    }

    public getEvses(): Evse[] {
        return [...this.evses];
    }

    /**
     * Get EVSE by serial from current list.
     * @param serial Serial of EVSE to get.
     * @return EVSE with the specified serial, or undefined if not found.
     */
    public getEvse(serial: string|null|undefined): Evse|undefined {
        if (!serial) return undefined;
        return this.evses.find(evse => evse.getInfo().serial === serial);
    }

    /**
     * Wait for the EVSE with given serial to come online. Or, if no serial is given, for any EVSE.
     * @param serial Serial of online EVSE to get.
     * @param timeoutSeconds Timeout in seconds to wait for the EVSE to come online.
     * @return Promise that resolves with the EVSE, or rejects if requested EVSE is not online within timeout.
     */
    public async waitForEvse(serial?: string, timeoutSeconds: number = 11): Promise<Evse> {
        const known = serial && this.getEvse(serial);
        if (known?.isOnline()) {
            return known;
        }
        return new Promise((resolve, reject) => {
            let listener: (evse: Evse, event: EmEvseEvent) => void;
            const timeout = setTimeout(() => {
                this.removeEventListener(EmEvseEvents.DATAGRAM, listener);
                reject(new Error(`EVSE with serial ${serial ?? '(any)'} not online within ${timeoutSeconds} seconds`));
            }, timeoutSeconds * 1000);
            listener = (evse: Evse, event: EmEvseEvent) => {
                if ((serial && evse.getInfo().serial !== serial) || event === EmEvseEvents.REMOVED) return;
                if (evse.isOnline()) {
                    clearTimeout(timeout);
                    this.removeEventListener(EmEvseEvents.DATAGRAM, listener);
                    resolve(evse);
                }
            };
            this.addEventListener(EmEvseEvents.DATAGRAM, listener);
        });
    }

    public getEvseOrThrow(serial: string|null|undefined): Evse {
        const evse = this.getEvse(serial);
        if (!evse) {
            throw new Error(`EVSE with serial ${serial === null ? '(null)' : serial ?? '(undefined)'} not found`);
        }
        return evse;
    }

    public getEvseByIp(ip: string|null|undefined): Evse|undefined {
        if (!ip) return undefined;
        return this.evses.find(evse => evse.getInfo().ip === ip);
    }

    private updateEvse(datagram: Datagram, rInfo: RemoteInfo): Evse {
        const serial = datagram.getDeviceSerial();
        if (!serial) return;
        let evse = this.getEvse(serial);
        if (evse) {
            const ipUpdated = evse.updateIp(rInfo.address, rInfo.port);
            const evseUpdated = evse.update(datagram);
            if (ipUpdated || evseUpdated) {
                this.dispatchEvent(EmEvseEvents.CHANGED, evse, datagram);
            }
        } else {
            evse = new Evse(this, this.dispatchEvent.bind(this), { serial, ip: rInfo.address, port: rInfo.port });
            evse.update(datagram);
            this.evses.push(evse);
            this.dispatchEvent(EmEvseEvents.ADDED, evse, datagram);
            // Some (most?) apps may not be interested in the difference between an EVSE being added and,
            // changed, and may just want to show the latest info for all EVSEs. So we send a changed
            // event as well when an EVSE is added, allowing such apps to only listen for that event.
            // Small downside is that apps that _do_ differentiate between added and changed will get
            // this spurious changed event.
            this.dispatchEvent(EmEvseEvents.CHANGED, evse, datagram);
        }
        return evse;
    }

    public send(datagram: Datagram, evse: Evse): Promise<number> {
        if (!this.isRunning()) {
            throw new Error("EmCommunicator is not running");
        }

        // If device serial is not set on the datagram, but we have one for the EVSE, then set it before sending.
        if (evse.getInfo().serial && !datagram.getDeviceSerial()) {
            datagram.setDeviceSerial(evse.getInfo().serial);
        }

        // If device password is not yet set on datagram by caller, then have it filled from EVSE before sending.
        if (datagram.getDevicePassword() === undefined) {
            evse.setDatagramPassword(datagram);
        }

        const buffer = datagram.pack();
        const port = evse.getInfo().port;

        return new Promise((resolve, reject) => {
            if (this.config.dumpDatagrams) {
                dumpDebug(`-> OUT: ${datagram.toString()} [${buffer.toString("hex")}] to ${evse.getInfo().ip}:${port}`);
            }
            this.socket.send(buffer, 0, buffer.length, port, evse.getInfo().ip, (error: Error|null, bytes: number) => {
                if (error) {
                    reject(error);
                } else {
                    resolve(bytes);
                }
            });
        });
    }

    /**
     * Add an event listener for one or more event types.
     * @param types   The event type(s) to listen for.
     * @param handler The event handler to call when (one of) the event(s) occurs. The specific event will be passed to the handler.
     */
    public addEventListener(types: EmEvseEvent|EmEvseEvent[], handler: EmEvseEventHandler): this {
        if (typeof types === "string") types = [ types ];
        if (types.length === 0) return this;
        const existing = this.listeners.find(listener => listener.handler === handler);
        if (existing) {
            types.filter(type => !existing.types.includes(type)).forEach(type => existing.types.push(type));
        } else {
            this.listeners.push({ types, handler });
        }
        return this;
    }

    /**
     * Remove an event listener for one or more event types or handler.
     * @param types   Event type(s) to unregister. If empty and a handler is specified, all event listeners
     *                for the handler will be removed.
     * @param handler The event handler to remove. If not specified, all event listeners for the specified types
     *                will be removed.
     */
    public removeEventListener(types: EmEvseEvent|EmEvseEvent[], handler: EmEvseEventHandler | undefined): this {
        if (!Array.isArray(types)) types = [ types ];
        if (!types || types.length === 0) types = Object.values(EmEvseEvents);
        this.listeners = this.listeners.filter(listener => {
            if (handler && listener.handler !== handler) return true;
            types.forEach(type => {
                const index = listener.types.indexOf(type);
                if (index >= 0) {
                    listener.types.splice(index, 1);
                }
            });
            return listener.types.length > 0;
        });
        return this;
    }

    protected dispatchEvent(event: EmEvseEvent, evse: Evse, datagram?: Datagram) {
        this.listeners.forEach(listener => {
            if (listener.types.includes(event)) try {
                listener.handler(evse, event, datagram);
            } catch (error) {
                logError(`Error running event handler [${event} ${evse.toString()}]: ${error.message}\n${error.stack}`);
            }
        });
    }

    private periodicChecks() {
        if (!this.isRunning()) return;
        this.evses.forEach(evse => {
            // Check online state.
            if (evse.updateOnlineStatus()) {
                this.dispatchEvent(EmEvseEvents.CHANGED, evse);
            }
            // Automatic re-login if session was lost.
            if (!evse.isLoggedIn() && evse.hasPassword()) {
                evse.login().then();
            }
            // Automatic refresh of config.
            if (this.config.refreshConfigIntervalSeconds > 5 && evse.isLoggedIn()) {
                const lastConfigUpdate = evse.getLastConfigUpdate()?.getTime();
                if (!lastConfigUpdate || lastConfigUpdate < Date.now() - this.config.refreshConfigIntervalSeconds * 1000) {
                    evse.fetchConfig().then();
                }
            }
        });
    }
}
