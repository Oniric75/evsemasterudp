import Datagram from "../Datagram.js";

export class ChargeStop extends Datagram {
    public static readonly COMMAND = 32776;

    private lineId: number = 1;
    private userId?: string;

    protected packPayload(): Buffer {
        // Length: 47 bytes
        // Bytes 	Variable 	Type 	Notes
        // 00       lineId      u8
        // 01 - 16  userId      String
        // 17 - 46  zeroed
        const buffer = Buffer.alloc(47);
        buffer.writeUInt8(this.lineId, 0);
        buffer.write(this.userId || "emmgr", 1, 16, "ascii");
        return buffer;
    }

    protected unpackPayload(buffer: Buffer) {
        // Not used; this is an app->EVSE command.
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

    public getUserId(): string {
        return this.userId;
    }

    public setUserId(userId?: string): this {
        if (userId) {
            this.userId = userId;
        }
        return this;
    }

}

export class ChargeStopResponse extends Datagram {
    public static readonly COMMAND = 8;

    private lineId?: number;
    private stopResult?: number;
    private failReason?: number;

    protected packPayload(): Buffer {
        // Not used; this is an EVSE response.
        return Buffer.alloc(0);
    }

    protected unpackPayload(buffer: Buffer) {
        // Bytes  Variable   Type  Notes
        // 00     lineId     u8
        // 01     stopResult u8
        // 02     failReason u8
        if (buffer.length < 3) {
            throw new Error(`Invalid ChargeStopResponse buffer length; expected 3, got ${buffer.length}`);
        }
        this.lineId = buffer.readUInt8(0);
        this.stopResult = buffer.readUInt8(1);
        this.failReason = buffer.readUInt8(2);
    }

    public getLineId(): number {
        return this.lineId;
    }

    public getStopResult(): number {
        return this.stopResult;
    }

    public getFailReason(): number {
        return this.failReason;
    }

}
