import Datagram from "../Datagram.js";
import { readString } from "../../util/util.js";

class GetVersionAbstract extends Datagram {
    private hardwareVersion: string;
    private softwareVersion: string;
    private feature: number;
    private supportNew: number;

    protected unpackPayload(buffer: Buffer): void {
        if (buffer.length < 37) throw new Error('Buffer too short');
        this.hardwareVersion = readString(buffer, 0, 16);
        this.softwareVersion = readString(buffer, 16, 32);
        this.feature = buffer.readUInt32BE(32);
        this.supportNew = buffer.readUInt8(36);
    }

    protected packPayload(): Buffer {
        return Buffer.of();
    }

    public getHardwareVersion(): string {
        return this.hardwareVersion;
    }

    public getSoftwareVersion(): string {
        return this.softwareVersion;
    }

    public getFeature(): number {
        return this.feature;
    }

    public getSupportNew(): number {
        return this.supportNew;
    }
}

export class GetVersion extends GetVersionAbstract {
    public static readonly COMMAND = 33030;
}

export class GetVersionResponse extends GetVersionAbstract {
    public static readonly COMMAND = 262;
}
