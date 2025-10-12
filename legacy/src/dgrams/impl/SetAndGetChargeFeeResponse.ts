import Datagram from "../Datagram.js";
import { Buffer } from "node:buffer";

export class SetAndGetChargeFeeResponse extends Datagram {

    public static readonly COMMAND = 0x0104;

    protected packPayload() {
        return Buffer.of();
    }

    protected unpackPayload(buffer: Buffer): void {
        // console.log("260/SetAndGetChargeFeeResponse payload: " + buffer.toString("hex"));
    }
}
