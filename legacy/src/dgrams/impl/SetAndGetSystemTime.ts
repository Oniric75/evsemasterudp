import Datagram from "../Datagram.js";
import { type SystemTimeAction, SystemTimeActions } from "../../util/types.js";
import { Buffer } from "node:buffer";
import { dateToEmTimestamp, emTimestampToDate } from "../../util/util.js";


abstract class SystemTimeAbstract extends Datagram {
    private action: SystemTimeAction;
    private time: Date;

    unpackPayload(buffer: Buffer) {
        this.action = buffer.readUInt8(0) as SystemTimeAction;
        this.time = emTimestampToDate(buffer.readUInt32BE(1));
    }

    packPayload(): Buffer {
        if (!([SystemTimeActions.GET, SystemTimeActions.SET] as number[]).includes(this.action)) {
            throw new Error(`Invalid GetAndSetSystemTimeAction: ${this.action}`);
        }

        const buffer = Buffer.alloc(5);
        buffer.writeUInt8(this.action, 0);

        if (this.action === SystemTimeActions.SET) {
            if (!this.time || this.time.getTime() === 0) {
                this.time = new Date();
            }
            buffer.writeUInt32BE(dateToEmTimestamp(this.time), 1);
        }

        return buffer;
    }

    public getAction(): SystemTimeAction {
        return this.action;
    }

    public setAction(action: SystemTimeAction): this {
        this.action = action;
        return this;
    }

    public getTime(): Date|undefined {
        return this.time;
    }

    public setTime(time?: Date): this {
        this.time = time;
        return this;
    }

}

export class SetAndGetSystemTime extends SystemTimeAbstract {
    public static readonly COMMAND = 33025;
}

export class SetAndGetSystemTimeResponse extends SystemTimeAbstract {
    public static readonly COMMAND = 257;
}
