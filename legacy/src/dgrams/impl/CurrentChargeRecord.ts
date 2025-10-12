import Datagram from "../Datagram.js";

export class CurrentChargeRecord extends Datagram {
    public static readonly COMMAND = 9;

    public lineId: number = 1;
    public startUserId: string|undefined = undefined;
    public endUserId: string|undefined = undefined;
    public chargeId: string|undefined = undefined;
    public hasReservation: number; // u8
    public startType: number;  // u8
    public chargeType: number;  // u8
    public chargeParam1: number;   // u16
    public chargeParam2: number;   // float - Multiply by 0.001; 255.0 if value = 255
    public chargeParam3: number;   // float - Multiply by 0.01; 255.0 if value = 255
    public stopReason: number; // u8
    public hasStopCharge: number; // u8
    public reservationData: number; // u32
    public startDate: number; // u32
    public stopDate: number; // u32
    public chargedTime: number; // u32
    public chargeStartPower: number; // float - Multiply by 0.01
    public chargeStopPower: number; // float - Multiply by 0.01
    public chargePower: number; // float - Multiply by 0.01
    public chargePrice: number; // float - Multiply by 0.01
    public feeType: number; // u8
    public chargeFee: number; // float - Multiply by 0.01
    public logKWLength: number; // u16
    public logKW: number[]; // u16 - optional, only included if length >= 157
    public logChargeDataKWh: number[]; // u16 - optional, only included if length >= 253
    public logChargeDataChargeFee: number[]; // u16 - optional, only included if length >= 253
    public logChargeDataServiceFee: number[]; // u16 - optional, only included if length >= 253

    protected packPayload() {
        return Buffer.of();
    }

    protected unpackPayload(buffer: Buffer): void {
        if (buffer.length < 97) {
            throw new Error("Invalid EmDatagram CurrentChargeRecord: too short payload")
        }

        this.lineId = buffer.readUInt8(0);
        this.startUserId = this.readString(buffer, 1, 16);
        this.endUserId = this.readString(buffer, 17, 16);
        this.chargeId = this.readString(buffer, 33, 16);
        this.hasReservation = buffer.readUInt8(49);
        this.startType = buffer.readUInt8(50);
        this.chargeType = buffer.readUInt8(51);
        this.chargeParam1 = buffer.readUInt16BE(52);
        this.chargeParam2 = buffer.readUInt16BE(54) * 0.001;
        this.chargeParam3 = buffer.readUInt16BE(56) * 0.01;
        this.stopReason = buffer.readUInt8(58);
        this.hasStopCharge = buffer.readUInt8(59);
        this.reservationData = buffer.readUInt32BE(60);
        this.startDate = buffer.readUInt32BE(64);
        this.stopDate = buffer.readUInt32BE(68);
        this.chargedTime = buffer.readUInt32BE(72);
        this.chargeStartPower = buffer.readUInt32BE(76) * 0.01;
        this.chargeStopPower = buffer.readUInt32BE(80) * 0.01;
        this.chargePower = buffer.readUInt32BE(84) * 0.01;
        this.chargePrice = buffer.readUInt32BE(88) * 0.01;
        this.feeType = buffer.readUInt8(92);
        this.chargeFee = buffer.readUInt16BE(93) * 0.01;
        this.logKWLength = buffer.readUInt16BE(95);
        if (buffer.length >= 156) {
            this.logKW = [];
            for (let i = 0; i < 60; i++) {
                this.logKW.push(buffer.readUInt16BE(96 + i*2));
            }
        }
        if (buffer.length >= 252) {
            this.logChargeDataKWh = [];
            for (let i = 0; i < 96; i += 2) {
                this.logChargeDataKWh.push(buffer.readUInt16BE(156 + i));
            }
        }
        if (buffer.length >= 348) {
            this.logChargeDataChargeFee = [];
            for (let i = 0; i < 96; i += 2) {
                this.logChargeDataChargeFee.push(buffer.readUInt16BE(252 + i));
            }
        }
        if (buffer.length >= 446) {
            this.logChargeDataServiceFee = [];
            for (let i = 0; i < 96; i += 2) {
                this.logChargeDataServiceFee.push(buffer.readUInt16BE(348 + i));
            }
        }
    }

}

export class RequestChargeStatusRecord extends Datagram {
    public static readonly COMMAND = 32781;

    protected packPayload() {
        return Buffer.of();
    }

    protected unpackPayload(buffer: Buffer): void {
        // Not used.
    }

}


export class CurrentChargeRecordResponse extends Datagram {
    public static readonly COMMAND = 32777;

    private lineId: number = 1;  // u8
    private chargeId: string|undefined;  // string (16 char)
    private status: number|undefined;  // u8

    protected packPayload() {
        if (this.status === undefined) {
            throw new Error("Invalid CurrentChargeRecordResponse: status is required")
        }
        const buffer = Buffer.alloc(18);
        buffer.writeUInt8(this.lineId, 0);
        if (this.chargeId !== undefined) {
            buffer.write(this.chargeId, 1, 16, "ascii");
        }
        buffer.writeUInt8(this.status || 0, 17);
        return buffer;
    }

    protected unpackPayload(buffer): void {
        // Not used.
    }

    public setLineId(lineId: number): this {
        if (lineId < 1) {
            throw new Error(`Invalid lineId: ${lineId}`);
        }
        this.lineId = lineId;
        return this;
    }

    public setChargeId(chargeId: string): this {
        this.chargeId = chargeId;
        return this;
    }

    public setStatus(status: number): this {
        this.status = status;
        return this;
    }

}
