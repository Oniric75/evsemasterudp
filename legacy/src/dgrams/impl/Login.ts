import Datagram from "../Datagram.js";
import { Buffer } from "node:buffer";

export abstract class LoginAbstract extends Datagram {
    private type: number; // u8
    private brand: string; // String
    private model: string; // String
    private hardwareVersion: string; // String
    private maxPower: number; // u32
    private maxElectricity: number; // u8
    private hotLine: string; // String
    private p51: number; // u8

    protected packPayload() {
        return Buffer.of();
    }

    protected unpackPayload(buffer: Buffer): void {
        this.type = buffer.readUInt8(0);
        this.brand = this.readString(buffer, 1, 16);
        this.model = this.readString(buffer, 17, 16);
        this.hardwareVersion = this.readString(buffer, 33, 16);
        this.maxPower = buffer.readUInt32BE(49);
        this.maxElectricity = buffer.readUInt8(53);
        this.hotLine = this.readString(buffer, 54, 16);
        if (buffer.length === 118) {
            this.hotLine += this.readString(buffer, 70, 48);
        } else if (buffer.length === 119 || buffer.length === 151) {
            this.hotLine += this.readString(buffer, 71, 48);
        }
        if (buffer.length === 151) {
            this.brand += this.readString(buffer, 119, 16);
            this.model += this.readString(buffer, 135, 16);
        }
        if (buffer.length >= 71 && this.type === 25 || this.type === 9 || this.type === 10) {
            this.p51 = buffer.readUInt8(70);
        } else {
            this.p51 = 0;
        }
    }

    public getType(): number {
        return this.type;
    }

    public getBrand(): string {
        return this.brand;
    }

    public getModel(): string {
        return this.model;
    }

    public getHardwareVersion(): string {
        return this.hardwareVersion;
    }

    public getMaxPower(): number {
        return this.maxPower;
    }

    public getMaxElectricity(): number {
        return this.maxElectricity;
    }

    public getHotLine(): string {
        return this.hotLine;
    }

    public getP51(): number {
        return this.p51;
    }
}

export class Login extends LoginAbstract {
    public static readonly COMMAND = 0x0001;
}

export class LoginResponse extends LoginAbstract {
    public static readonly COMMAND = 0x0002;
}

export class RequestLogin extends Datagram {
    public static readonly COMMAND = 0x8002;

    protected packPayload() {
        return Buffer.of(0x00);
    }

    protected unpackPayload(buffer: Buffer): void {
        // Unused: this is an app->EVSE datagram.
    }
}

export class LoginConfirm extends Datagram {
    public static readonly COMMAND = 0x8001;

    protected packPayload() {
        return Buffer.of(0x00);
    }

    protected unpackPayload(buffer: Buffer): void {
        // Unused: this is an outgoing command.
    }
}
