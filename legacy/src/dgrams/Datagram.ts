import { Buffer } from "node:buffer";
import { EmDatagram } from "../util/types.js";

/**
 * Base class for datagram implementations.
 * Each datagram implementation class must:
 * - Extend this class.
 * - Define the static readonly `COMMAND` property to be the protocol-level command.
 * - Be registered in the `dgrams/index.ts` file (no auto-discovery of datagram classes yet).
 * - Implement the `packPayload` method to pack the payload (datagram fields) into a byte buffer for outgoing datagrams
 *   to be sent to the EVSE. For incoming datagrams (commands) that are only sent from EVSE to manager, this method can
 *   be a no-op, simply returning an empty buffer.
 * - Implement the `unpackPayload` method to unpack the payload from an incoming byte buffer into the datagram fields,
 *   and normalizing the values as needed. For datagrams (commands) that are only sent from manager to EVSE, this method
 *   can be no-op/empty.
 */
export default abstract class Datagram implements EmDatagram {

    /**
     * Implementation datagram classes must define a static `COMMAND` property.
     * They must also register themselves in dgrams/index.ts.
     */
    public static readonly COMMAND = 0 as number;


    public static readonly PACKET_HEADER = 0x0601;
    public static readonly PACKET_TAIL = 0x0f02;

    private keyType: number = 0x00;
    private deviceSerial?: string;
    private devicePassword?: string;

    public getCommand(): number {
        for (let prototype = Object.getPrototypeOf(this); prototype !== Object.prototype && prototype !== Datagram.prototype; prototype = Object.getPrototypeOf(prototype)) {
            if (prototype.constructor.COMMAND) {
                return prototype.constructor.COMMAND;
            }
        }
        throw new Error(`Invalid EmDatagram: missing command for type ${this.constructor.name}`);
    }

    protected abstract unpackPayload(buffer: Buffer): void;

    public unpack(buffer: Buffer) {
        const payloadLength = Datagram.assertValidDatagram(buffer);

        const command = buffer.readUint16BE(19);
        if (command !== this.getCommand()) {
            throw new Error(`Invalid EmDatagram: unexpected command ${command} for type ${this.constructor.name} with command ${this.getCommand()}`);
        }

        this.keyType = buffer.readUInt8(4);
        this.deviceSerial = buffer.toString("hex", 5, 13);
        const password = buffer.subarray(13, 19);
        if (password.every((byte) => byte === 0)) {
            this.devicePassword = undefined;
        } else {
            this.devicePassword = password.toString("ascii");
        }

        const payload = buffer.subarray(21, 21 + payloadLength);
        this.unpackPayload(payload);
        return payloadLength + 25;
    }

    protected readTemperature(buffer: Buffer, offset: number): number {
        const temp = buffer.readUInt16BE(offset);
        return temp === 0xffff ? -1.0 : Number(((temp - 20000) * 0.01).toFixed(2));
    }

    protected readString(buffer: Buffer, offset: number, length: number): string {
        return buffer.toString("ascii", offset, offset + length).replace(/\0+$/, "");
    }

    protected abstract packPayload(): Buffer;

    public pack(): Buffer {
        const command = this.getCommand();
        if (!command) throw new Error(`Invalid EmDatagram: missing command for type ${this.constructor.name}`);

        const payload = this.packPayload();

        const buffer = Buffer.alloc(25 + payload.length);
        buffer.writeUInt16BE(Datagram.PACKET_HEADER, 0);
        buffer.writeUInt16BE(buffer.length, 2);
        buffer.writeUInt8(this.keyType, 4);
        if (this.deviceSerial) {
            buffer.write(this.deviceSerial, 5, 8, "hex");
        }
        if (this.devicePassword !== undefined) {
            buffer.write(this.devicePassword, 13, 6, "ascii");
        }
        buffer.writeUInt16BE(command, 19);
        payload.copy(buffer, 21, 0, payload.length);
        const checksum = buffer.subarray(0, -4).reduce((acc, val) => (acc + val) % 0xffff, 0);
        buffer.writeUInt16BE(checksum, 25 + payload.length - 4);
        buffer.writeUInt16BE(Datagram.PACKET_TAIL, 25 + payload.length - 2);
        return buffer;
    }

    /**
     * Validate the datagram and return the length of the payload.
     * @param buffer Datagram byte buffer.
     * @private
     */
    private static assertValidDatagram(buffer: Buffer): number {
        if (buffer.length < 25) {
            throw new Error("Invalid EmDatagram: too short");
        }
        if (buffer.readUInt16BE(0) !== Datagram.PACKET_HEADER) {
            throw new Error("Invalid EmDatagram: missing magic header");
        }

        const length = buffer.readUInt16BE(2);
        if (length > buffer.length) {
            console.trace("Invalid EmDatagram: invalid length; buffer: " + buffer.toString("hex"));
            throw new Error("Invalid EmDatagram: invalid length");
        }

        const computedChecksum = buffer.subarray(0, length - 4).reduce((acc, val) => (acc + val) % 0xffff, 0);
        const checksum = buffer.readUInt16BE(length - 4);
        if (computedChecksum !== checksum) {
            console.trace("Invalid EmDatagram: invalid checksum (should be " + checksum + ", is " + computedChecksum + ", buffer: " + buffer.toString("hex") + " aka " + buffer.toString("ascii"));
            throw new Error("Invalid EmDatagram: invalid checksum");
        }

        return length - 25;
    }

    public getDevicePassword(): string|undefined {
        return this.devicePassword;
    }

    public setDevicePassword(password: string|undefined): this {
        this.devicePassword = password;
        return this;
    }

    public getDeviceSerial(): string|undefined {
        return this.deviceSerial;
    }

    public setDeviceSerial(serial: string): this {
        this.deviceSerial = serial;
        return this;
    }

    public getKeyType(): number {
        return this.keyType;
    }

    public setKeyType(keyType: number): this {
        this.keyType = keyType;
        return this;
    }

    public toString(): string {
        let str = `${this.constructor.name}/${this.getCommand()} serial=${this.deviceSerial}`;
        Object.entries(this).forEach(([key, value]) => {
            if (key === "deviceSerial" || key === "devicePassword" || key === "keyType" || value === undefined) return;
            if (typeof value === "function") return;
            str += ` ${key}=${value}`;
        });
        return str;
    }
}
