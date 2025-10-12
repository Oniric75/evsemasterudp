import Datagram from "../Datagram.js";
import { Buffer } from "node:buffer";
import {
    type SetAndGetTemperatureUnitAction,
    SetAndGetTemperatureUnitActions,
    type TemperatureUnit,
    TemperatureUnits
} from "../../util/types.js";

abstract class SetAndGetTemperatureUnitAbstract extends Datagram {
    private action: SetAndGetTemperatureUnitAction;
    private temperatureUnit: TemperatureUnit;

    unpackPayload(buffer: Buffer) {
        this.action = buffer.readUInt8(0) as SetAndGetTemperatureUnitAction;
        this.temperatureUnit = buffer.readUInt8(1) as TemperatureUnit;
    }

    packPayload(): Buffer {
        if (!([SetAndGetTemperatureUnitActions.GET, SetAndGetTemperatureUnitActions.SET] as number[]).includes(this.action)) {
            throw new Error(`Invalid SetAndGetTemperatureUnitAction: ${this.action}`);
        }

        return Buffer.of(this.action, this.action === SetAndGetTemperatureUnitActions.GET ? 0 : this.temperatureUnit);
    }

    public getAction(): SetAndGetTemperatureUnitAction {
        return this.action;
    }

    public setAction(action: SetAndGetTemperatureUnitAction): this {
        this.action = action;
        return this;
    }

    public getTemperatureUnit(): TemperatureUnit {
        return this.temperatureUnit;
    }

    public setTemperatureUnit(temperatureUnit: TemperatureUnit): this {
        this.temperatureUnit = TemperatureUnits[temperatureUnit];
        return this;
    }
}

export class SetAndGetTemperatureUnit extends SetAndGetTemperatureUnitAbstract {
    public static readonly COMMAND = 33042;
}

export class SetAndGetTemperatureUnitResponse extends SetAndGetTemperatureUnitAbstract {
    public static readonly COMMAND = 274;
}
