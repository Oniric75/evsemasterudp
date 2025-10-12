import Datagram from "../Datagram.js";
import { Buffer } from "node:buffer";
import { emTimestampToDate } from "../../util/util.js";
import { type EmEvseCurrentState, EmEvseCurrentStates } from "../../util/types.js";

export abstract class SingleACChargingStatus extends Datagram {

    public port: number;
    public currentState: EmEvseCurrentState;    // 13=finished, 14=charging // EmEvseCurrentState
    public chargeId: string;
    public startType: number;
    public chargeType: number;
    public maxDurationMinutes: number;  // param 1
    public maxEnergyKWh: number;        // param 2
    public chargeParam3: number;
    public reservationDate: Date;
    public userId: string;
    public maxElectricity: number;
    public startDate: Date;
    public durationSeconds: number;
    public startKWhCounter: number;   // 0 if session finished.
    public currentKWhCounter: number;   // still filled when session finished.
    public chargeKWh: number;   // currentKWhCounter - startKWhCounter if session is active; filled with last value if session finished (startKWhCounter is set to 0 then)
    public chargePrice: number;
    public feeType: number;
    public chargeFee: number;

    protected packPayload() {
        return Buffer.of();
    }

    protected unpackPayload(buffer: Buffer): void {
        if (buffer.length < 74) {
            throw new Error("Invalid EmDatagram SingleACChargingStatus: too short payload")
        }

        this.port = buffer.readUInt8(0);
        const currentState = buffer.length <= 74 || ![18, 19].includes(buffer.readUInt8(74)) ? buffer.readUInt8(1) : buffer.readUInt8(74);
        this.currentState = currentState as EmEvseCurrentState || EmEvseCurrentStates.UNKNOWN;
        this.chargeId = this.readString(buffer, 2, 16);
        this.startType = buffer.readUInt8(18);
        this.chargeType = buffer.readUInt8(19);
        this.maxDurationMinutes = buffer.readUInt16BE(20) === 65535 ? undefined : buffer.readUInt16BE(20);
        this.maxEnergyKWh = buffer.readUInt16BE(22) === 65535 ? undefined : buffer.readUInt16BE(22) * 0.01;
        this.chargeParam3 = buffer.readUInt16BE(24) === 65535 ? undefined : buffer.readUInt16BE(24) * 0.01;
        this.reservationDate = emTimestampToDate(buffer.readUInt32BE(26));
        this.userId = this.readString(buffer, 30, 16);
        this.maxElectricity = buffer.readUInt8(46);
        this.startDate = emTimestampToDate(buffer.readUInt32BE(47));
        this.durationSeconds = buffer.readUInt32BE(51);
        this.startKWhCounter = buffer.readUInt32BE(55) * 0.01;
        this.currentKWhCounter = buffer.readUInt32BE(59) * 0.01;
        this.chargeKWh = buffer.readUInt32BE(63) * 0.01;
        this.chargePrice = buffer.readUInt32BE(67) * 0.01;
        this.feeType = buffer.readUInt8(71);
        this.chargeFee = buffer.readUInt16BE(72) * 0.01;
    }

}

export class SingleACChargingStatusResponse extends SingleACChargingStatus {

    public static readonly COMMAND = 6;

}

export class SingleACChargingStatusPublicAuto extends SingleACChargingStatus {

    public static readonly COMMAND = 5;

}
