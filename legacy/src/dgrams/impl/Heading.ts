import Datagram from "../Datagram.js";
import { Buffer } from "node:buffer";

export class Heading extends Datagram {
    public static readonly COMMAND = 0x0003;

    protected packPayload() {
        return Buffer.of();
    }

    protected unpackPayload(buffer): void {
        // Has no payload.
    }
}

export class HeadingResponse extends Datagram {
    public static readonly COMMAND = 32771;

    protected packPayload(): Buffer {
        return Buffer.of(0x00);
    }

    protected unpackPayload(buffer: Buffer) {
        // Unused; this is a response to the EVSE's Heading datagram.
    }
}
