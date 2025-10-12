import { Communicator } from "../src/Communicator.js";
import {ChargeStartParams, EmEvse} from "../src/util/types.js";
import { logError, logInfo, logSuccess, nowStr } from "../src/util/util.js";

const evsesFile = '~/evses.json';

// Set passwords for EVSEs by serial.
const passwords: {[serial: string]: string} = {};
// The EVSE that we want to test. Can be a (part of) serial or name. First matching EVSE is used.
let evseKeyword: string|undefined = undefined;
// The command.

type Command = "stop" | "start" | "gettime" | "settime";
let command: Command | undefined = undefined;
const isValidCommand = (arg: string): arg is Command => {
    return ["start", "stop", "settime", "gettime"].includes(arg);
};
let startParams: ChargeStartParams = {
    // The amps for the start command.
    maxAmps: undefined,
    // Whether to limit to single phase.
    singlePhase: false
};
// Whether to dump datagrams.
let dumpDatagrams = false;

process.argv.slice(2).forEach(arg => {
    if (arg === "help") {
        process.stdout.write("Usage:\n");
        process.stdout.write("  - Pass without arguments to monitor EVSEs and their state.\n");
        process.stdout.write("  - Pass with arguments to send commands to EVSEs.\n");
        process.stdout.write("  - Pass 'help' to see this message.\n");
        process.stdout.write("\nAvailable arguments:\n");
        process.stdout.write("  <serial|name|model>=<password>\n" +
                             "                 Set the password for the EVSE with the given serial number.\n" +
                             "                 This allows sending commands and watching more detailed oper-\n" +
                             "                 ational state. Passwords are saved in EVSEs file in homedir so\n" +
                             "                 you have to specify them only once per EVSE.\n");
        process.stdout.write("  <serial|name|model>\n" +
                             "                 Only watch matching EVSE(s), and if running a command, send it\n" +
                             "                 to first matching EVSE (otherwise, send to first online one).\n");
        process.stdout.write("  start=<amps>   Send a charge start command using the maximum current in amps.\n");
        process.stdout.write("  start=1x<amps> Send a charge start command using the maximum current, and only\n" +
                             "                 charge using a single phase.\n");
        process.stdout.write("  stop           Send a charge stop command.\n");
        process.stdout.write("  gettime        Show the current time of the EVSE.\n");
        process.stdout.write("  settime        Sync the current app time to the EVSE.\n");
        process.stdout.write("  dump           Dump UDP packets and protocol datagrams to stdout.\n");
        process.stdout.write("\nExamples (run from project root):\n");
        process.stdout.write("  npx tsx clitest 1234567890123456=123456    Watch all EVSEs; set password for\n" + "" +
                             "                 one so more detailed state can be shown.\n");
        process.stdout.write("  npx tsx clitest 1234567890123456           Watch only EVSE with given serial. If password was previously set, more detailed info can be shown.\n");
        process.stdout.write("  npx tsx clitest MyChargerName              Watch only EVSE with given name. If password was previously set, more detailed info can be shown.\n");
        process.stdout.write("  npx tsx clitest 1234567890123456 start=6   Start charging on EVSE with given serial with 6 amps, using previously set password.\n");
        process.stdout.write("  npx tsx clitest start=6                    Start charging on first (/only) online EVSE with 6 amps, using previously set password.\n");
        process.stdout.write("  npx tsx clitest start=1x6                  Start charging on first (/only) online EVSE with 6 amps on a single phase.\n");
        process.stdout.write("  npx tsx clitest stop                       Stop charging on first (/only) online EVSE, using previously set password.\n");
        process.exit();
    }

    if (arg.includes("=")) {
        const parts = arg.split("=", 2);
        if (parts[0] === "start") {
            if (command) throw new Error("Multiple commands")
            command = "start";
            startParams = getStartParams(parts[1]);
        } else {
            passwords[parts[0]] = parts[1];
            if (!evseKeyword) evseKeyword = parts[0].toLowerCase();
        }
    } else if (isValidCommand(arg)) {
        if (command) throw new Error("Multiple commands")
        command = arg; // TypeScript sait maintenant que arg est de type Command
    } else if (arg === "dump") {
        dumpDatagrams = true;
    } else  {
        if (evseKeyword) throw new Error("Multiple filtering keywords passed; only a single one is supported");
        evseKeyword = arg.toLowerCase();
    }
});

function getStartParams(param: string): ChargeStartParams {
    const match = /((?<phases>\d)x)?(?<amps>\d+)$/.exec(param);
    if (!match) throw new Error(`Invalid start parameter: ${param}`);
    const maxAmps = parseInt(match.groups?.amps, 10);
    return {
        maxAmps,
        singlePhase: match.groups?.phases === "1"
    };
}

function evseMatches(evse: EmEvse) {
    if (!evseKeyword) return true;
    return evse.getInfo().serial?.toLowerCase().includes(evseKeyword)
        || evse.getConfig().name?.toLowerCase().includes(evseKeyword)
        || `${evse.getInfo().brand} ${evse.getInfo().model}`.toLowerCase().includes(evseKeyword);
}

(async function() {
    const communicator = new Communicator({ dumpDatagrams });

    await communicator.start();
    communicator.loadEvses(evsesFile);

    logInfo("Press Ctrl+C to exit");

    communicator.addEventListener(["ADDED", "REMOVED", "CHANGED"], async (evse, evt) => {
        if (evseKeyword && !evseMatches(evse)) return;

        process.stdout.write(`[${nowStr()}] ⚡ ${evt} ${evse.toString()}\n`);
        if (evt === 'REMOVED') return;
        const state = evse.getState();
        if (state) {
            process.stdout.write(`    🔌 State: ${JSON.stringify(evse.getState())}\n`);
        }
        const currentCharge = evse.getCurrentCharge();
        if (currentCharge) {
            process.stdout.write(`    🔋 Charge: ${JSON.stringify(currentCharge)}\n`);
        }

        if (evseMatches(evse)) {
            if (passwords[evse.getInfo().serial]) {
                await evse.login(passwords[evse.getInfo().serial]);
                logInfo(`Logged in to ${evse.getInfo().serial}`);
                delete passwords[evse.getInfo().serial];
            }
            if (command === "start") {
                await start(evse, startParams);
            } else if (command === "stop") {
                await stop(evse);
            } else if (command === "gettime") {
                const time = await evse.fetchSystemTime();
                logInfo(`Time on ${evse.getInfo().serial}: ${time}`);
                process.kill(process.pid, 'SIGINT');
            } else if (command === "settime") {
                await evse.setSystemTime();
                logInfo(`Time set on ${evse.getInfo().serial}`);
                process.kill(process.pid, 'SIGINT');
            }
        }
    });

    process.on('SIGINT', () => {
        communicator.stop();
        communicator.saveEvses(evsesFile);
        process.exit();
    });
})();

async function start(evse: EmEvse, startParams: ChargeStartParams) {
    try {
        if (!evse.isLoggedIn()) await evse.login();
        if (!startParams.maxAmps) {
            startParams.maxAmps = evse.getConfig().maxElectricity;
            if (!startParams.maxAmps || startParams.maxAmps < 6 || startParams.maxAmps > 32) {
                throw new Error(`Invalid maxAmps (${startParams.maxAmps}); must be between 6 and 32; configure on EVSE first or specify explicitly.`);
            }
        }
        const result = await evse.chargeStart(startParams);
        logSuccess(`Charge start result: ${JSON.stringify(result)}\n`);
    } catch (error) {
        logError(`Error starting charge: ${error.message}\n`);
    }
    process.kill(process.pid, 'SIGINT');
}

async function stop(evse: EmEvse) {
    try {
        if (!evse.isLoggedIn()) await evse.login();
        const result = await evse.chargeStop();
        logSuccess(`Charge stop result: ${JSON.stringify(result)}\n`);
    } catch (error) {
        logError(`Error stopping charge: ${error.message}\n`);
    }
    process.kill(process.pid, 'SIGINT');
}
