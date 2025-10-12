import Datagram from "../Datagram.js";
import { Buffer } from "node:buffer";

export class RequestStatusRecord extends Datagram {

    public static readonly COMMAND = 13;

    protected packPayload() {
        return Buffer.of();
    }

    protected unpackPayload(buffer: Buffer): void {
        // console.log("13/RequestStatusRecord payload: " + buffer.toString("hex"));
    }
}
