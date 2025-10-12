import Datagram from "../Datagram.js";
import {
    ChargeStartErrorReason,
    ChargeStartReservationResult
} from "util/types.js"
import { dateToEmTimestamp } from "../../util/util.js";

export class ChargeStart extends Datagram {
    public static readonly COMMAND = 32775;

    private lineId?: number = 1;
    private userId?: string;
    private chargeId?: string;
    private reservationDate: Date;
    private startType: number = 1;
    private chargeType: number = 1;
    private maxDurationMinutes?: number;  // param 1
    private maxEnergyKWh?: number;        // param 2
    private readonly param3: number = 65535;
    private maxElectricity: number;

    protected unpackPayload(buffer: Buffer): void {
        // Not used; this is an app->EVSE command.
    }

    protected packPayload(): Buffer {
        if (!this.maxElectricity || this.maxElectricity < 6 || this.maxElectricity > 32) {
            throw new Error("Invalid maxElectricity (amps), must be between 6 and 32");
        }
        const now = Date.now();
        // Length: 47 bytes
        // Bytes 	Variable 	Type 	Notes from app analysis
        // 00       lineId        u8    app uses hardcoded 1 most times, except strangely one callsite that passes 2 (for repeated schedule; maybe to avoid immediate start by specifying nonexistent lineId?)
        // 01 - 16 	userId    String    16 chars
        // 17 - 32 	chargeId  String    16 chars: current time (even if reservation in future) formatted as yyyyMMddHHmm, plus 4 random trailing numbers
        // 33       isReservation u8    1 if reservation date is set in future, 0 if not (reservation date is then always set to current time)
        // 34 - 37  reservationDate u32 timestamp to start; if isReservation is 0, this is set to current time
        // 38       startType     u8    always 1
        // 39       chargeType    u8    looks to be always 1, except strangely one callsite that passes 11 for single scheduled charge
        // 40 - 41  chargeParam1 u16    max duration, in minutes
        // 42 - 43 	chargeParam2 u16    max energy amount in hundredths of kWh
        // 44 - 45 	chargeParam3 u16    always 65535
        // 46       maxElectricity u8   in amps

        const buffer = Buffer.alloc(47);
        buffer.writeUInt8(this.lineId || 1, 0);
        buffer.write(this.userId || "emmgr", 1, 16, "ascii");
        const chargeId = this.chargeId || new Date().toISOString().replace(/\D/g, "").slice(0, 12) + Math.floor(Math.random() * 10000).toString().padStart(4, "0");
        buffer.write(chargeId, 17, 16, "ascii");
        buffer.writeUInt8(this.reservationDate?.getTime() > now ? 1 : 0, 33);
        buffer.writeUInt32BE(dateToEmTimestamp(this.reservationDate || new Date()), 34);
        buffer.writeUInt8(this.startType, 38);
        buffer.writeUInt8(this.chargeType, 39);
        buffer.writeUInt16BE(this.maxDurationMinutes || 65535, 40);
        buffer.writeUInt16BE((this.maxEnergyKWh ? Math.floor(this.maxEnergyKWh * 100) : undefined) || 65535, 42);
        buffer.writeUInt16BE(this.param3, 44);
        buffer.writeUInt8(this.maxElectricity, 46);

        return buffer;
    }

    public getLineId(): number {
        return this.lineId;
    }

    public setLineId(lineId?: number): this {
        if (!lineId) {
            return this;
        }
        if (lineId < 1) {
            throw new Error(`Invalid lineId: ${lineId}`);
        }
        this.lineId = lineId;
        return this;
    }

    public setUserId(userId?: string): this {
        if (userId) {
            this.userId = userId;
        }
        return this;
    }

    public setChargeId(chargeId?: string): this {
        this.chargeId = chargeId;
        return this;
    }

    public setReservationDate(reservationDate?: Date): this {
        this.reservationDate = reservationDate;
        return this;
    }

    public setStartType(startType: number): this {
        this.startType = startType;
        return this;
    }

    public setChargeType(chargeType: number): this {
        this.chargeType = chargeType;
        return this;
    }

    public setMaxDurationMinutes(maxDurationMinutes?: number): this {
        this.maxDurationMinutes = maxDurationMinutes;
        return this;
    }

    public setMaxEnergyKWh(maxEnergyKWh?: number): this {
        this.maxEnergyKWh = maxEnergyKWh;
        return this;
    }

    public setMaxElectricity(maxElectricity?: number): this {
        this.maxElectricity = maxElectricity;
        return this;
    }

}

export class ChargeStartResponse extends Datagram {
    public static readonly COMMAND = 7;

    private lineId: number;
    private reservationResult: ChargeStartReservationResult;
    private startResult: number;
    private errorReason: ChargeStartErrorReason;
    private maxElectricity: number;

    protected unpackPayload(buffer: Buffer): void {
        if (buffer.length < 5) {
            throw new Error(`Invalid ChargeStartResponse buffer length; expected 5, got ${buffer.length}`);
        }

        this.lineId = buffer.readUInt8(0);
        this.reservationResult = buffer.readUInt8(1) as ChargeStartReservationResult;
        this.startResult = buffer.readUInt8(2);
        this.errorReason = buffer.readUInt8(3) as ChargeStartErrorReason;
        this.maxElectricity = buffer.readUInt8(4);
    }

    protected packPayload(): Buffer {
        // Not used; this is an EVSE response.
        return Buffer.alloc(0);
    }

    public getLineId(): number {
        return this.lineId;
    }

    public getReservationResult(): ChargeStartReservationResult {
        return this.reservationResult;
    }

    public getStartResult(): number {
        return this.startResult;
    }

    public getErrorReason(): ChargeStartErrorReason {
        return this.errorReason;
    }

    public getMaxElectricity(): number {
        return this.maxElectricity;
    }

}
