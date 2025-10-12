import Datagram from "../Datagram.js";
import { SetAndGetNickNameAction, SetAndGetNickNameActions } from "../../util/types.js";
import { readString } from "../../util/util.js";

abstract class SetAndGetNickNameAbstract extends Datagram {
    private action: SetAndGetNickNameAction = SetAndGetNickNameActions.GET;    // u8
    private nickName: string; // 32 bytes

    public getAction(): SetAndGetNickNameAction {
        return this.action;
    }

    public setAction(action: SetAndGetNickNameAction): this {
        this.action = action;
        return this;
    }

    public getNickName(): string {
        return this.nickName;
    }

    public setNickName(nickname: string): this {
        this.nickName = nickname;
        return this;
    }

    protected packPayload(): Buffer {
        if (this.action !== SetAndGetNickNameActions.GET && this.action !== SetAndGetNickNameActions.SET) {
            throw new Error("Invalid action, must be GET or SET");
        }

        if (this.action === SetAndGetNickNameActions.SET && !this.nickName) {
            throw new Error("Nickname is required for SET action");
        }

        const buffer = Buffer.alloc(33);
        buffer.writeUInt8(this.action, 0);
        if (this.action === SetAndGetNickNameActions.SET) {
            buffer.write(this.nickName, 1, 32, "binary");
        }
        return buffer;
    }

    protected unpackPayload(buffer: Buffer) {
        if (buffer.length < 17) {
            throw new Error("Invalid payload; too short");
        }

        this.action = buffer.readUInt8(0) as SetAndGetNickNameAction;
        this.nickName = readString(buffer, 1, buffer.length >= 33 ? 33 : 17);
    }
}

export class SetAndGetNickName extends SetAndGetNickNameAbstract {
    public static readonly COMMAND = 33032;
}

export class SetAndGetNickNameResponse extends SetAndGetNickNameAbstract {
    public static readonly COMMAND = 264;
}
