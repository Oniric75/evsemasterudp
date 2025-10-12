import Datagram from "../Datagram.js";
import {
    type Language,
    Languages,
    type SetAndGetLanguageAction,
    SetAndGetLanguageActions
} from "../../util/types.js";

abstract class SetAndGetLanguageAbstract extends Datagram {

    private action: SetAndGetLanguageAction = SetAndGetLanguageActions.GET;

    private language: Language;

    public getAction(): SetAndGetLanguageAction {
        return this.action;
    }

    public setAction(action: SetAndGetLanguageAction): this {
        this.action = action;
        return this;
    }

    public getLanguage(): Language {
        return this.language;
    }

    public setLanguage(language: Language): this {
        this.language = language;
        return this;
    }

    protected packPayload(): Buffer {
        if (this.action === SetAndGetLanguageActions.SET && !this.language) {
            throw new Error('Language is required when setting');
        }

        return Buffer.of(this.action, this.language);
    }

    protected unpackPayload(buffer: Buffer): void {
        this.action = buffer.readUInt8(0) as SetAndGetLanguageAction;
        this.language = buffer.readUInt8(1) as Language || Languages.UNKNOWN;
    }

}

export class SetAndGetLanguage extends SetAndGetLanguageAbstract {
    public static readonly COMMAND = 33039;
}

export class SetAndGetLanguageResponse extends SetAndGetLanguageAbstract {
    public static readonly COMMAND = 271;
}
