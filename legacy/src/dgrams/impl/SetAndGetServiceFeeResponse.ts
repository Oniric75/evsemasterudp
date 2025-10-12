import Datagram from "../Datagram.js";
import { Buffer } from "node:buffer";

export class SetAndGetServiceFeeResponse extends Datagram {

    public static readonly COMMAND = 0x0105;

    protected packPayload() {
        return Buffer.of();
    }

    protected unpackPayload(buffer: Buffer): void {
        // console.log("261/SetAndGetServiceFeeResponse payload: " + buffer.toString("hex"));
    }
}
