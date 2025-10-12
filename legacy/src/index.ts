import { Communicator } from "./Communicator.js";
import { EmCommunicator, EmCommunicatorConfig } from "./util/types.js";

/**
 * Create a new communicator instance.
 * @param config Configuration (optional).
 */
export function createCommunicator(config: Partial<EmCommunicatorConfig> = {}): EmCommunicator {
    return new Communicator(config);
}
