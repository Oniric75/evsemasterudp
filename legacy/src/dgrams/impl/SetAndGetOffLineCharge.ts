import Datagram from "../Datagram.js";
import {
    type OffLineChargeAction,
    OffLineChargeActions,
    type OffLineChargeStatus
} from "../../util/types.js";

abstract class SetAndGetOffLineChargeAbstract extends Datagram {
    private status: OffLineChargeStatus;
    private action: OffLineChargeAction;

    protected packPayload() {
        return Buffer.of(this.action, this.action === OffLineChargeActions.GET ? 0 : this.status);
    }

    protected unpackPayload(buffer: Buffer) {
        if (buffer.length < 2) {
            throw new Error("269/SetAndGetOffLineChargeResponse payload too small");
        }
        this.action = buffer.readUInt8(0) as OffLineChargeAction;
        this.status = buffer.readUInt8(1) as OffLineChargeStatus;
    }

    public getAction(): OffLineChargeAction {
        return this.action;
    }

    public setAction(action: OffLineChargeAction): this {
        this.action = action;
        return this;
    }

    public getStatus(): OffLineChargeStatus {
        return this.status;
    }

    public setStatus(status: OffLineChargeStatus): this {
        this.status = status;
        return this;
    }
}

export class SetAndGetOffLineCharge extends SetAndGetOffLineChargeAbstract {
    public static readonly COMMAND = 33037;
}

export class SetAndGetOffLineChargeResponse extends SetAndGetOffLineChargeAbstract {
    public static readonly COMMAND = 269;
}
