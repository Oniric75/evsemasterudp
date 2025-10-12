import Datagram from "../Datagram.js";

export class UploadLocalChargeRecord extends Datagram {

    public static readonly COMMAND = 10;

    protected packPayload() {
        return Buffer.of();
    }

    protected unpackPayload(buffer: Buffer): void {
        // TODO
    }
}
