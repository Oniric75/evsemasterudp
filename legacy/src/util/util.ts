import { EmEvseError } from "./types.js";

/**
 * Encode a password to a base64 string with some slight obfuscation.
 * To be used in conjunction with decodePassword.
 * @param password Password to encode as an ASCII string.
 * @returns Encoded password as a base64 string.
 */
export function encodePassword(password?: string): string|undefined {
    if (password === undefined) return undefined;
    const inputBuf = Buffer.from(password, "ascii");
    const outputBuf = Buffer.allocUnsafe(inputBuf.length)
    for (let i = 0; i < inputBuf.length; i++) {
        outputBuf.writeUInt8(inputBuf.readUInt8(i) ^ 0xff, i);
    }
    return outputBuf.toString("base64");
}

/**
 * Decode a password from a base64 string with some slight obfuscation.
 * @param encodedPassword Encoded password as a base64 string.
 * @returns Decoded password as an ASCII string.
 */
export function decodePassword(encodedPassword?: string): string|undefined {
    if (encodedPassword === undefined) return undefined;
    const inputBuf = Buffer.from(encodedPassword, "base64");
    const outputBuf = Buffer.allocUnsafe(inputBuf.length)
    for (let i = 0; i < inputBuf.length; i++) {
        outputBuf.writeUInt8(inputBuf.readUInt8(i) ^ 0xff, i);
    }
    return outputBuf.toString("ascii");
}

export function equals(a: any, b: any): boolean {
    if (a === b) return true;
    if (typeof a !== typeof b) return false;

    if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length) return false;
        for (let i = 0; i < a.length; i++) {
            if (!equals(a[i], b[i])) return false;
        }
        return true;
    }

    if (typeof a === 'object') {
        const aKeys = Object.keys(a);
        const bKeys = Object.keys(b);
        if (aKeys.length !== bKeys.length) return false;
        for (const key of aKeys) {
            if (!equals(a[key], b[key])) return false;
        }
        return true;
    }

    if (a instanceof Date && b instanceof Date) {
        return a.getTime() === b.getTime();
    }

    return false;
}

/**
 * Update a property of an object if the new value is different from the old value,
 * and return whether the property was updated.
 * @param obj      Object whose property to change.
 * @param prop     Property (name) to change.
 * @param newValue New value of property.
 * @returns True if the property was updated, false if the new value is the same as the old value.
 */
export function update(obj: object, prop: string, newValue: any): boolean {
    if (equals(obj[prop], newValue)) {
        return false;
    }
    obj[prop] = newValue;
    return true;
}

/**
 * Read a string from a buffer, stopping at the first null character, and stripping any trailing spaces.
 * @param buffer Buffer to read string from.
 * @param start  Byte position to start reading from.
 * @param end    Byte position to stop reading at (exclusive).
 */
export function readString(buffer: Buffer, start: number, end: number): string {
    return buffer.toString("binary", start, end).split(/\s*\x00/)[0];
}

/**
 * Convert a Date object, a number of seconds since the epoch, or a string to a Date object.
 * If the parameter is already a Date instance, returns a new Date instance with the same time.
 * @param dt Date string/number/Date to convert.
 */
export function toDate(dt: Date | number | string | undefined | null): Date {
    if (dt instanceof Date || typeof dt === 'string') {
        return new Date(dt);
    }
    if (typeof dt === 'number') {
        return new Date(dt * 1000);
    }
    return undefined;
}

/**
 * Promised setTimeout.
 * @param ms Milliseconds to wait.
 */
export function sleep(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Generic enum type. Takes either a (const) enum as input type, or an "object as const" type.
 */
export type Enum<E extends string | object> = E extends string ? `${E}` | E : E[keyof E];

export function parseErrorState(errorState: number): EmEvseError[] {
    const errors: EmEvseError[] = [];
    for (let i = 0; i < 32; i++) {
        if (errorState & (1 << i)) {
            errors.push(i as EmEvseError);
        }
    }
    return errors;
}

export function nowStr() {
    const now = new Date();
    return `${now.getFullYear()}-${now.getMonth()+1}-${now.getDate()} ${now.getHours()}:${('0' + now.getMinutes()).slice(-2)}:${('0' + now.getSeconds()).slice(-2)}`;
}

const LOCAL_TIMEZONE = Intl.DateTimeFormat().resolvedOptions().timeZone;
const EM_TIMEZONE = 'Asia/Shanghai';

export function dateToEmTimestamp(date: Date): number {
    const time = date.getTime();
    const dateInLocalTimeZone = new Date(date.toLocaleString('en-US', { timeZone: LOCAL_TIMEZONE }));
    const dateInEmTimeZone = new Date(date.toLocaleString('en-US', { timeZone: EM_TIMEZONE }));
    const offset = dateInEmTimeZone.getTime() - dateInLocalTimeZone.getTime();
    return Math.floor((time - offset) / 1000);
}

export function emTimestampToDate(timestamp: number): Date {
    const date = new Date(timestamp * 1000);
    const dateInLocalTimeZone = new Date(date.toLocaleString('en-US', { timeZone: LOCAL_TIMEZONE }));
    const dateInEmTimeZone = new Date(date.toLocaleString('en-US', { timeZone: EM_TIMEZONE }));
    const offset = dateInEmTimeZone.getTime() - dateInLocalTimeZone.getTime();
    return new Date(date.getTime() + offset);
}

export function logInfo(msg: string) {
    process.stdout.write(`[${nowStr()}] ℹ️ ${msg}\n`);
}

export function logWarning(msg: string) {
    process.stdout.write(`[${nowStr()}] ⚠️ ${msg}\n`);
}

export function logError(msg: string) {
    process.stderr.write(`[${nowStr()}] ⚠️ ${msg}\n`);
}

export function logSuccess(msg: string) {
    process.stdout.write(`[${nowStr()}] 🆗 ${msg}\n`);
}

export function dumpDebug(msg: string) {
    process.stdout.write(`[${nowStr()}] 🐞 ${msg}\n`);
}
