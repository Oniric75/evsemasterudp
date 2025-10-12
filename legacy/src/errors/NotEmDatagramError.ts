export default class NotEmDatagramError extends Error {
    constructor(msg: string) {
        super("Invalid EmDatagram: " + msg);
    }
}
