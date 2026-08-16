#!/usr/bin/osascript -l JavaScript

ObjC.import("AppKit");
ObjC.import("Foundation");

ObjC.bindFunction("malloc", ["void *", ["unsigned long"]]);
ObjC.bindFunction("free", ["void", ["void *"]]);
ObjC.bindFunction("proc_listallpids", ["int", ["void *", "int"]]);
ObjC.bindFunction("proc_name", ["int", ["int", "void *", "unsigned int"]]);
ObjC.bindFunction("proc_pid_rusage", ["int", ["int", "int", "void *"]]);
ObjC.bindFunction("kill", ["int", ["int", "int"]]);

const CPU_THRESHOLD_DEFAULT_PERCENT = 0.25;
const CPU_THRESHOLD_MIN_PERCENT = 0;
const CPU_THRESHOLD_MAX_PERCENT = 1;
const CPU_TIMEOUT_DEFAULT_SECONDS = 10;
const CPU_TIMEOUT_MIN_SECONDS = 0;
const CPU_TIMEOUT_MAX_SECONDS = 20;
const AVERAGE_WINDOW_DEFAULT_SECONDS = 0.5;
const AVERAGE_WINDOW_MIN_SECONDS = 0.1;
const AVERAGE_WINDOW_MAX_SECONDS = 5;
const WAIT_TIMEOUT_DEFAULT_SECONDS = 600;
const WAIT_TIMEOUT_MIN_SECONDS = 0;
const WAIT_TIMEOUT_MAX_SECONDS = 900;
const PERPLEXITY_RESTART_QUIT_TIMEOUT_MILLISECONDS = 5000;
const PERPLEXITY_RESTART_FORCE_TIMEOUT_MILLISECONDS = 3000;
const PERPLEXITY_RESTART_LAUNCH_TIMEOUT_MILLISECONDS = 10000;
const PERPLEXITY_RESTART_POLL_MILLISECONDS = 100;
const RUNNER_NOTIFY_WAIT_DEFAULT_SECONDS = 2;
const RUNNER_NOTIFY_WAIT_MIN_SECONDS = 0;
const RUNNER_NOTIFY_WAIT_MAX_SECONDS = 20;
const WARNING_SECONDS = 3;
const PULSE_INTERVAL_MILLISECONDS = 300;
const MONITOR_TICK_SECONDS = 0.05;
const CPU_SAMPLE_SECONDS = 0.1;
const PID_REFRESH_SECONDS = 1;
const RUNNER_PRESENCE_POLL_SECONDS = 1;
const ORPHAN_RUNNER_POLL_SECONDS = 1;
const ORPHAN_RUNNER_KILL_FALLBACK_MILLISECONDS = 1200;
const ORPHAN_RUNNER_KILL_VERIFY_MILLISECONDS = 3000;
const ACTIVE_RUN_RECORD_SCHEMA_VERSION = 1;
const EXECUTION_SNAPSHOT_NAME_PATTERN =
    /^\.perplexity-cpu-loop-execution-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.sh$/;
const PROCESS_NAME = "Perplexity";
const PERPLEXITY_BUNDLE_IDENTIFIER = "ai.perplexity.macv3";
const RUSAGE_INFO_V2 = 2;
const RUSAGE_BUFFER_SIZE = 256;
const PROCESS_NAME_BUFFER_SIZE = 1024;
const UINT32_SIZE = 4;
const CONFIG_SCHEMA_VERSION = 1;
const CONFIG_SAVE_DEBOUNCE_SECONDS = 0.4;
const PROMPT_TEXT_TAG_BASE = 1000;
const SIGNAL_EDGE_PULSE_MILLISECONDS = 700;
const PROMPT_ROLL_MILLISECONDS = 3000;
const PROMPT_ROLL_SETTLE_MILLISECONDS = 300;
const PROMPT_ROLL_MIN_DWELL_MILLISECONDS = 55;
const ACTIVE_SENTINEL_PATTERN = /^[A-Za-z0-9+/]{21}[AQgw]==$/;
const PROMPT_SENTINEL_TOOLTIP =
    "Each time this UI injects a prompt, it generates and remembers a fresh cryptographically random " +
    "128-bit Base64 token. Every {sentinel} occurrence expands to that token only at injection time; " +
    "the stored field text is unchanged. Before starting the watched run.sh, this UI checks for the " +
    "remembered token. If found, it disables Auto Mode, leaves run.sh untouched, and skips execution.";
const RUNNER_SUCCESS_TEMPLATE_DEFAULT =
    "run.sh finished with exit code 0. Find output in {output}";
const RUNNER_FAILURE_TEMPLATE_DEFAULT =
    "run.sh finished with exit code {exit}. Find output in {output}";
const DEFAULT_PROMPTS = [
    {
        weight: 55,
        text: "go on with your task until completed. Don't yield except when waiting for a run.sh to finish."
    },
    {
        weight: 20,
        text: "Read AGENTS.md and keep going."
    },
    {
        weight: 15,
        text: "What's the next step?"
    },
    {
        weight: 10,
        text: "If you're stuck or finished, write \"{sentinel}\" into run.sh. Otherwise, keep going."
    }
];

let previousProcessCPUTimes = {};
let previousCPUSampleTime = null;
let matchingProcessPids = [];
let lastPIDRefreshTime = 0;

let monitorState = null;
let monitorController = null;
let monitorTimer = null;
let waitClickRecognizer = null;
let graphClickStart = null;
let graphGestureMode = null;
let promptRows = [];
let signalAnimation = null;
let perplexityRestart = null;
let activePromptSentinel = "";
let promptWeightGestureSnapshot = null;
let configurationSaveTimer = null;
let configurationDirty = false;
let configurationLastError = "";

let runnerTask = null;
let runnerTaskMode = null;
let runnerTaskStartedAt = 0;
let runnerReady = false;
let runnerPathDirectoryAvailable = false;
let runnerSelfTestStatus = "unverified";
let runnerLastExitStatus = null;
let runnerSelectedScriptPath = null;
let runnerKillRequested = false;
let runnerKillDeadline = null;
let runnerStatusDetail = "";
let runnerValidatedConfiguration = null;
let runnerTaskConfiguration = null;
let runnerExecutionSnapshotPath = null;
let runnerExecutionOriginalPath = null;
let runnerOutputLastPollAt = 0;
let runnerOutputLastText = "";
let runnerScriptPreviewLastPollAt = 0;
let runnerScriptPreviewLastText = null;
let runnerOutputPresentationMode = null;
let runnerOutputTextView = null;
let runnerStatusImageMode = null;
let runnerSentinelDetected = false;
let runnerLEDHovering = false;
let lastRunnerSentinelCheckAt = 0;
const RUNNER_SENTINEL_POLL_SECONDS = 1;
let runnerExistingScriptNotice = false;
let runnerAutoTriggeredForPresence = false;
let lastRunnerPresenceCheckAt = 0;
let orphanedRunner = null;
let lastOrphanRunnerPollAt = 0;
let runnerActiveOwnershipToken = null;
let runnerStartupSelfTestPending = false;
let pendingRunnerPrompt = null;

function processArgumentStrings() {
    const argumentsArray = $.NSProcessInfo.processInfo.arguments;
    const result = [];
    for (let index = 0; index < Number(argumentsArray.count); index += 1) {
        result.push(String(ObjC.unwrap(argumentsArray.objectAtIndex(index))));
    }
    return result;
}

function discoverScriptDirectory() {
    const fileManager = $.NSFileManager.defaultManager;
    for (const argument of processArgumentStrings()) {
        if (!argument.endsWith(".js") || !Boolean(fileManager.fileExistsAtPath(argument))) {
            continue;
        }
        const url = $.NSURL.fileURLWithPath(argument);
        return String(ObjC.unwrap(url.URLByDeletingLastPathComponent.path));
    }

    return String(ObjC.unwrap(fileManager.currentDirectoryPath));
}

const SCRIPT_DIRECTORY = discoverScriptDirectory();
const PROCESS_WORKING_DIRECTORY = String(ObjC.unwrap(
    $.NSFileManager.defaultManager.currentDirectoryPath.stringByStandardizingPath
));
const DEFAULT_RUN_SCRIPT_PATH = String(ObjC.unwrap(
    $(PROCESS_WORKING_DIRECTORY).stringByAppendingPathComponent("run.sh")
));
const RUNNER_PATH = SCRIPT_DIRECTORY + "/run-loop.sh";
const temporaryDirectoryValue = $.NSProcessInfo.processInfo.environment.objectForKey("TMPDIR");
const TEMPORARY_DIRECTORY = temporaryDirectoryValue
    ? String(ObjC.unwrap(temporaryDirectoryValue))
    : "/tmp/";
const RUNNER_OUTPUT_PATH = TEMPORARY_DIRECTORY.replace(/\/$/, "") +
    "/perplexity-runner-output-" +
    Number($.NSProcessInfo.processInfo.processIdentifier) + ".log";
const homeDirectoryValue = $.NSProcessInfo.processInfo.environment.objectForKey("HOME");
const HOME_DIRECTORY = homeDirectoryValue
    ? String(ObjC.unwrap(homeDirectoryValue))
    : String(ObjC.unwrap($.NSHomeDirectory()));
const CONFIG_DIRECTORY = HOME_DIRECTORY +
    "/Library/Application Support/Perplexity CPU Loop";
const CONFIG_PATH = CONFIG_DIRECTORY + "/config.json";
const ACTIVE_RUN_RECORD_PATH = CONFIG_DIRECTORY + "/active-run.json";
runnerSelectedScriptPath = DEFAULT_RUN_SCRIPT_PATH;

function stringValue(control) {
    return String(ObjC.unwrap(control.stringValue));
}

function objcObjectIsNil(value) {
    return value === null || value === undefined || String(value) === "[id nil]";
}

function resolveProjectDirectory(argument) {
    const suppliedPath = String(argument);
    if (!suppliedPath) {
        throw new Error("PROJECT_DIRECTORY must not be empty.");
    }

    let path = $(suppliedPath).stringByExpandingTildeInPath;
    if (!Boolean(path.isAbsolutePath)) {
        path = $(PROCESS_WORKING_DIRECTORY).stringByAppendingPathComponent(path);
    }
    const standardizedPath = String(ObjC.unwrap(path.stringByStandardizingPath));
    const isDirectory = Ref();
    const exists = $.NSFileManager.defaultManager.fileExistsAtPathIsDirectory(
        standardizedPath,
        isDirectory
    );
    if (!Boolean(exists)) {
        throw new Error(`PROJECT_DIRECTORY does not exist: ${standardizedPath}`);
    }
    if (!Boolean(isDirectory[0])) {
        throw new Error(`PROJECT_DIRECTORY is not a directory: ${standardizedPath}`);
    }
    return standardizedPath;
}

function defaultConfiguration() {
    return {
        schemaVersion: CONFIG_SCHEMA_VERSION,
        smoothingWindowSeconds: AVERAGE_WINDOW_DEFAULT_SECONDS,
        cpuThresholdPercent: CPU_THRESHOLD_DEFAULT_PERCENT,
        lowCPUCountdownSeconds: CPU_TIMEOUT_DEFAULT_SECONDS,
        waitSignalTimeoutSeconds: WAIT_TIMEOUT_DEFAULT_SECONDS,
        cpuSignalActive: false,
        waitSignalActive: false,
        postExecutionWaitSeconds: RUNNER_NOTIFY_WAIT_DEFAULT_SECONDS,
        activePromptSentinel: "",
        successPrompt: {
            enabled: true,
            template: RUNNER_SUCCESS_TEMPLATE_DEFAULT
        },
        failurePrompt: {
            enabled: true,
            template: RUNNER_FAILURE_TEMPLATE_DEFAULT
        },
        prompts: DEFAULT_PROMPTS.map(prompt => ({
            text: prompt.text,
            weight: prompt.weight
        })),
        runner: {
            selectedScriptPath: DEFAULT_RUN_SCRIPT_PATH,
            sandbox: true,
            autoMode: false
        }
    };
}

function validatedNumber(value, minimum, maximum, fallback) {
    return typeof value === "number" && Number.isFinite(value) &&
        value >= minimum && value <= maximum
        ? value
        : fallback;
}

function validatedBoolean(value, fallback) {
    return typeof value === "boolean" ? value : fallback;
}

function validatedString(value, fallback, maximumLength, allowEmpty) {
    return typeof value === "string" && value.length <= maximumLength &&
        (allowEmpty || value.length > 0)
        ? value
        : fallback;
}

function validatedActivePromptSentinel(value) {
    return typeof value === "string" &&
        (value === "" || ACTIVE_SENTINEL_PATTERN.test(value))
        ? value
        : "";
}

function allocateIntegerUnits(totalUnits, basisUnits) {
    if (basisUnits.length === 0) {
        return [];
    }

    const safeTotalUnits = Math.max(0, Math.round(totalUnits));
    const safeBasis = basisUnits.map(value => Math.max(0, Math.round(Number(value) || 0)));
    const basisTotal = safeBasis.reduce((total, value) => total + value, 0);
    const exactShares = basisTotal > 0
        ? safeBasis.map(value => safeTotalUnits * value / basisTotal)
        : safeBasis.map(() => safeTotalUnits / safeBasis.length);
    const allocations = exactShares.map(value => Math.floor(value));
    let unitsLeft = safeTotalUnits - allocations.reduce((total, value) => total + value, 0);
    const rankedRemainders = exactShares.map((value, index) => ({
        index,
        remainder: value - allocations[index]
    })).sort((left, right) =>
        right.remainder - left.remainder || left.index - right.index
    );

    for (let index = 0; index < unitsLeft; index += 1) {
        allocations[rankedRemainders[index].index] += 1;
    }
    return allocations;
}

function validateConfiguration(rawConfiguration) {
    const configuration = defaultConfiguration();
    if (!rawConfiguration || typeof rawConfiguration !== "object" ||
        Array.isArray(rawConfiguration) ||
        rawConfiguration.schemaVersion !== CONFIG_SCHEMA_VERSION) {
        return configuration;
    }

    configuration.smoothingWindowSeconds = validatedNumber(
        rawConfiguration.smoothingWindowSeconds,
        AVERAGE_WINDOW_MIN_SECONDS,
        AVERAGE_WINDOW_MAX_SECONDS,
        configuration.smoothingWindowSeconds
    );
    configuration.cpuThresholdPercent = validatedNumber(
        rawConfiguration.cpuThresholdPercent,
        CPU_THRESHOLD_MIN_PERCENT,
        CPU_THRESHOLD_MAX_PERCENT,
        configuration.cpuThresholdPercent
    );
    configuration.lowCPUCountdownSeconds = validatedNumber(
        rawConfiguration.lowCPUCountdownSeconds,
        CPU_TIMEOUT_MIN_SECONDS,
        CPU_TIMEOUT_MAX_SECONDS,
        configuration.lowCPUCountdownSeconds
    );
    configuration.waitSignalTimeoutSeconds = validatedNumber(
        rawConfiguration.waitSignalTimeoutSeconds,
        WAIT_TIMEOUT_MIN_SECONDS,
        WAIT_TIMEOUT_MAX_SECONDS,
        configuration.waitSignalTimeoutSeconds
    );
    configuration.postExecutionWaitSeconds = validatedNumber(
        rawConfiguration.postExecutionWaitSeconds,
        RUNNER_NOTIFY_WAIT_MIN_SECONDS,
        RUNNER_NOTIFY_WAIT_MAX_SECONDS,
        configuration.postExecutionWaitSeconds
    );
    configuration.cpuSignalActive = validatedBoolean(
        rawConfiguration.cpuSignalActive,
        configuration.cpuSignalActive
    );
    configuration.waitSignalActive = validatedBoolean(
        rawConfiguration.waitSignalActive,
        configuration.waitSignalActive
    );
    configuration.activePromptSentinel = validatedActivePromptSentinel(
        rawConfiguration.activePromptSentinel
    );

    const successPrompt = rawConfiguration.successPrompt;
    if (successPrompt && typeof successPrompt === "object" && !Array.isArray(successPrompt)) {
        configuration.successPrompt.enabled = validatedBoolean(
            successPrompt.enabled,
            configuration.successPrompt.enabled
        );
        configuration.successPrompt.template = validatedString(
            successPrompt.template,
            configuration.successPrompt.template,
            10000,
            true
        );
    }

    const failurePrompt = rawConfiguration.failurePrompt;
    if (failurePrompt && typeof failurePrompt === "object" && !Array.isArray(failurePrompt)) {
        configuration.failurePrompt.enabled = validatedBoolean(
            failurePrompt.enabled,
            configuration.failurePrompt.enabled
        );
        configuration.failurePrompt.template = validatedString(
            failurePrompt.template,
            configuration.failurePrompt.template,
            10000,
            true
        );
    }

    if (Array.isArray(rawConfiguration.prompts) &&
        rawConfiguration.prompts.length === configuration.prompts.length) {
        configuration.prompts = configuration.prompts.map((defaultPrompt, index) => {
            const prompt = rawConfiguration.prompts[index];
            if (!prompt || typeof prompt !== "object" || Array.isArray(prompt)) {
                return defaultPrompt;
            }
            return {
                text: validatedString(prompt.text, defaultPrompt.text, 100000, true),
                weight: validatedNumber(prompt.weight, 0, 100, defaultPrompt.weight)
            };
        });
    }

    const eligiblePromptIndexes = [];
    const promptBasisUnits = [];
    for (let index = 0; index < configuration.prompts.length; index += 1) {
        const prompt = configuration.prompts[index];
        if (prompt.text.trim()) {
            eligiblePromptIndexes.push(index);
            promptBasisUnits.push(Math.round(prompt.weight * 10));
        } else {
            prompt.weight = 0;
        }
    }
    const normalizedPromptUnits = allocateIntegerUnits(1000, promptBasisUnits);
    for (let index = 0; index < eligiblePromptIndexes.length; index += 1) {
        configuration.prompts[eligiblePromptIndexes[index]].weight =
            normalizedPromptUnits[index] / 10;
    }

    const runner = rawConfiguration.runner;
    if (runner && typeof runner === "object" && !Array.isArray(runner)) {
        configuration.runner.selectedScriptPath = validatedString(
            runner.selectedScriptPath,
            configuration.runner.selectedScriptPath,
            4096,
            false
        );
        configuration.runner.sandbox = validatedBoolean(
            runner.sandbox,
            configuration.runner.sandbox
        );
        configuration.runner.autoMode = validatedBoolean(
            runner.autoMode,
            configuration.runner.autoMode
        );
    }
    return configuration;
}

function loadConfiguration() {
    const text = readTextFile(CONFIG_PATH, true);
    if (text === null) {
        return defaultConfiguration();
    }

    try {
        return validateConfiguration(JSON.parse(text));
    } catch (error) {
        configurationLastError = `Could not load configuration: ${error}`;
        return defaultConfiguration();
    }
}

function promptRowIsEligible(row) {
    return Boolean(stringValue(row.textField).trim());
}

function setPromptRowEligibility(row, eligible) {
    row.eligible = eligible;
    row.slider.setEnabled(eligible);
    row.slider.setAlphaValue(eligible ? 1.0 : 0.4);
    if (!eligible) {
        row.slider.setDoubleValue(0);
    }
}

function updatePromptWeightLabels() {
    for (const row of promptRows) {
        row.valueLabel.setStringValue(`${Number(row.slider.doubleValue).toFixed(1)}%`);
        row.valueLabel.setAlphaValue(row.eligible ? 1.0 : 0.4);
    }
}

function normalizePromptWeights() {
    const eligibleIndexes = [];
    const basisUnits = [];
    for (let index = 0; index < promptRows.length; index += 1) {
        const row = promptRows[index];
        const eligible = promptRowIsEligible(row);
        setPromptRowEligibility(row, eligible);
        if (eligible) {
            eligibleIndexes.push(index);
            basisUnits.push(Math.round(Number(row.slider.doubleValue) * 10));
        }
    }

    const allocations = allocateIntegerUnits(1000, basisUnits);
    for (let index = 0; index < eligibleIndexes.length; index += 1) {
        promptRows[eligibleIndexes[index]].slider.setDoubleValue(allocations[index] / 10);
    }
    updatePromptWeightLabels();
}

function promptTextChanged(changedIndex) {
    if (changedIndex < 0 || changedIndex >= promptRows.length) {
        return;
    }
    promptWeightGestureSnapshot = null;
    normalizePromptWeights();
    scheduleConfigurationSave();
}

function rebalancePromptWeights(changedIndex, requestedValue) {
    if (changedIndex < 0 || changedIndex >= promptRows.length ||
        !promptRows[changedIndex].eligible) {
        return;
    }

    const eligibleIndexes = promptRows
        .map((row, index) => row.eligible ? index : -1)
        .filter(index => index >= 0);
    const eligibilityKey = eligibleIndexes.join(",");
    if (!promptWeightGestureSnapshot ||
        promptWeightGestureSnapshot.changedIndex !== changedIndex ||
        promptWeightGestureSnapshot.eligibilityKey !== eligibilityKey) {
        const basisByIndex = {};
        for (const index of eligibleIndexes) {
            basisByIndex[index] = Math.max(
                0,
                Math.round(Number(promptRows[index].slider.doubleValue) * 10)
            );
        }
        promptWeightGestureSnapshot = {
            changedIndex,
            eligibilityKey,
            basisByIndex
        };
    }

    if (eligibleIndexes.length === 1) {
        promptRows[changedIndex].slider.setDoubleValue(100);
        updatePromptWeightLabels();
        scheduleConfigurationSave();
        return;
    }

    const targetUnits = Math.round(clamp(Number(requestedValue), 0, 100) * 10);
    const otherIndexes = eligibleIndexes.filter(index => index !== changedIndex);
    const otherBasisUnits = otherIndexes.map(
        index => promptWeightGestureSnapshot.basisByIndex[index]
    );
    const otherAllocations = allocateIntegerUnits(1000 - targetUnits, otherBasisUnits);
    promptRows[changedIndex].slider.setDoubleValue(targetUnits / 10);
    for (let index = 0; index < otherIndexes.length; index += 1) {
        promptRows[otherIndexes[index]].slider.setDoubleValue(otherAllocations[index] / 10);
    }
    updatePromptWeightLabels();
    scheduleConfigurationSave();
}

function configurationFromUI() {
    const ui = monitorState.ui;
    return {
        schemaVersion: CONFIG_SCHEMA_VERSION,
        smoothingWindowSeconds: Number(ui.averageWindowSlider.doubleValue),
        cpuThresholdPercent: Number(ui.cpuThresholdSlider.doubleValue),
        lowCPUCountdownSeconds: Number(ui.cpuDurationSlider.doubleValue),
        waitSignalTimeoutSeconds: Number(ui.waitSlider.doubleValue),
        cpuSignalActive: Number(ui.cpuActiveButton.state) === Number($.NSControlStateValueOn),
        waitSignalActive: Number(ui.waitActiveButton.state) === Number($.NSControlStateValueOn),
        postExecutionWaitSeconds: Number(ui.runnerWaitSlider.doubleValue),
        activePromptSentinel,
        successPrompt: {
            enabled: Number(ui.runnerSuccessPromptButton.state) ===
                Number($.NSControlStateValueOn),
            template: stringValue(ui.runnerSuccessPromptField)
        },
        failurePrompt: {
            enabled: Number(ui.runnerFailurePromptButton.state) ===
                Number($.NSControlStateValueOn),
            template: stringValue(ui.runnerFailurePromptField)
        },
        prompts: promptRows.map(row => ({
            text: stringValue(row.textField),
            weight: row.eligible ? Number(row.slider.doubleValue) : 0
        })),
        runner: {
            selectedScriptPath: runnerSelectedScriptPath,
            sandbox: Number(ui.runnerSandboxButton.state) === Number($.NSControlStateValueOn),
            autoMode: Number(ui.runnerAutoButton.state) === Number($.NSControlStateValueOn)
        }
    };
}

function writeConfiguration(configuration) {
    const fileManager = $.NSFileManager.defaultManager;
    const directoryCreated = fileManager.createDirectoryAtPathWithIntermediateDirectoriesAttributesError(
        CONFIG_DIRECTORY,
        true,
        undefined,
        undefined
    );
    if (!Boolean(directoryCreated)) {
        throw new Error(`Could not create configuration directory: ${CONFIG_DIRECTORY}`);
    }

    const json = JSON.stringify(validateConfiguration(configuration), null, 2) + "\n";
    const written = $(json).writeToFileAtomicallyEncodingError(
        CONFIG_PATH,
        true,
        $.NSUTF8StringEncoding,
        undefined
    );
    if (!Boolean(written)) {
        throw new Error(`Could not write configuration: ${CONFIG_PATH}`);
    }
}

function flushConfiguration(force) {
    if (configurationSaveTimer) {
        configurationSaveTimer.invalidate;
        configurationSaveTimer = null;
    }
    if (!monitorState) {
        configurationLastError = "The UI is not initialized, so configuration cannot be saved.";
        return false;
    }
    if (!force && !configurationDirty) {
        return true;
    }

    try {
        writeConfiguration(configurationFromUI());
        configurationDirty = false;
        configurationLastError = "";
        return true;
    } catch (error) {
        configurationDirty = true;
        configurationLastError = String(error);
        return false;
    }
}

function scheduleConfigurationSave() {
    configurationDirty = true;
    if (!monitorController) {
        return;
    }
    if (configurationSaveTimer) {
        configurationSaveTimer.invalidate;
    }
    configurationSaveTimer = $.NSTimer.timerWithTimeIntervalTargetSelectorUserInfoRepeats(
        CONFIG_SAVE_DEBOUNCE_SECONDS,
        monitorController,
        "saveConfiguration:",
        null,
        false
    );
    $.NSRunLoop.mainRunLoop.addTimerForMode(
        configurationSaveTimer,
        $.NSRunLoopCommonModes
    );
}

function applyConfigurationToUI(rawConfiguration) {
    if (!monitorState || runnerOperationInProgress() || signalAnimation || perplexityRestart) {
        return false;
    }

    const previousSelfTestStatus = runnerSelfTestStatus;
    const previousValidatedConfiguration = runnerValidatedConfiguration;
    const configuration = validateConfiguration(rawConfiguration);
    const ui = monitorState.ui;
    ui.averageWindowSlider.setDoubleValue(configuration.smoothingWindowSeconds);
    ui.cpuThresholdSlider.setDoubleValue(configuration.cpuThresholdPercent);
    ui.cpuDurationSlider.setDoubleValue(configuration.lowCPUCountdownSeconds);
    ui.waitSlider.setDoubleValue(configuration.waitSignalTimeoutSeconds);
    ui.cpuActiveButton.setState(
        configuration.cpuSignalActive
            ? $.NSControlStateValueOn
            : $.NSControlStateValueOff
    );
    ui.waitActiveButton.setState(
        configuration.waitSignalActive
            ? $.NSControlStateValueOn
            : $.NSControlStateValueOff
    );
    ui.runnerWaitSlider.setDoubleValue(configuration.postExecutionWaitSeconds);
    ui.runnerSuccessPromptButton.setState(
        configuration.successPrompt.enabled
            ? $.NSControlStateValueOn
            : $.NSControlStateValueOff
    );
    ui.runnerSuccessPromptField.setStringValue(configuration.successPrompt.template);
    ui.runnerFailurePromptButton.setState(
        configuration.failurePrompt.enabled
            ? $.NSControlStateValueOn
            : $.NSControlStateValueOff
    );
    ui.runnerFailurePromptField.setStringValue(configuration.failurePrompt.template);

    for (let index = 0; index < promptRows.length; index += 1) {
        const prompt = configuration.prompts[index];
        promptRows[index].textField.setStringValue(prompt.text);
        promptRows[index].slider.setDoubleValue(prompt.weight);
        setPromptRowEligibility(promptRows[index], Boolean(prompt.text.trim()));
    }
    normalizePromptWeights();

    runnerSelectedScriptPath = configuration.runner.selectedScriptPath;
    ui.runnerSandboxButton.setState(
        configuration.runner.sandbox
            ? $.NSControlStateValueOn
            : $.NSControlStateValueOff
    );
    ui.runnerAutoButton.setState(
        configuration.runner.autoMode
            ? $.NSControlStateValueOn
            : $.NSControlStateValueOff
    );
    activePromptSentinel = configuration.activePromptSentinel;
    runnerPathDirectoryAvailable = runnerPathDirectoryExists();
    runnerReady = runnerPathDirectoryAvailable && runnerFileExists();
    runnerAutoTriggeredForPresence = false;
    const fingerprint = runnerConfigurationFingerprint();
    const validationRemainsCurrent = previousSelfTestStatus === "passed" &&
        previousValidatedConfiguration === fingerprint;
    runnerSelfTestStatus = validationRemainsCurrent ? "passed" : "unverified";
    runnerValidatedConfiguration = validationRemainsCurrent ? fingerprint : null;
    runnerTaskConfiguration = null;
    setRunnerOutputVisible(false);
    resetAllProgress();

    const autoDisabled = disableAutoModeForExistingRunScript(ui, true);
    const signalsDisabled = !runnerAutoModeEnabled() && disableSignalSources(ui);
    if (autoDisabled || signalsDisabled) {
        scheduleConfigurationSave();
    }
    runnerStatusDetail = !runnerPathDirectoryAvailable
        ? `Project directory does not exist: ${runnerRootDirectory()}.`
        : runnerDisplayState() === "uninitialized"
            ? "Environment self-test required."
            : runnerReady
                ? `${runnerScriptName()} is ready.`
                : `Waiting for ${runnerScriptName()} to become available.`;
    updateRunnerUI(Date.now());
    return true;
}

function saveConfigurationNow() {
    configurationDirty = true;
    return flushConfiguration(true);
}

function configurationSaveFailureMessage() {
    return `Could not save configuration to ${CONFIG_PATH}. ${configurationLastError || "Unknown write error."}`;
}

function showConfigurationSaveFailure() {
    const message = configurationSaveFailureMessage();
    runnerStatusDetail = message;
    if (monitorState) {
        updateRunnerUI(Date.now());
    }
    const alert = $.NSAlert.alloc.init;
    alert.setAlertStyle(Number($.NSAlertStyleCritical));
    alert.setMessageText("Configuration save failed");
    alert.setInformativeText(message);
    alert.addButtonWithTitle("OK");
    alert.runModal;
}

function loadSavedConfiguration() {
    if (runnerOperationInProgress() || signalAnimation) {
        return;
    }
    applyConfigurationToUI(loadConfiguration());
}

function resetDefaultConfiguration() {
    if (runnerOperationInProgress() || signalAnimation) {
        return;
    }
    const configuration = defaultConfiguration();
    configuration.activePromptSentinel = activePromptSentinel;
    if (applyConfigurationToUI(configuration) && !saveConfigurationNow()) {
        showConfigurationSaveFailure();
    }
}

function generateRandomPromptSentinel() {
    const handle = $.NSFileHandle.fileHandleForReadingAtPath("/dev/urandom");
    if (objcObjectIsNil(handle)) {
        throw new Error("Could not open /dev/urandom for prompt sentinel generation.");
    }
    const data = handle.readDataOfLength(16);
    handle.closeFile;
    if (objcObjectIsNil(data) || Number(data.length) !== 16) {
        throw new Error("Could not read 16 random bytes for the prompt sentinel.");
    }
    const encoded = String(ObjC.unwrap(data.base64EncodedStringWithOptions(0)));
    if (!ACTIVE_SENTINEL_PATTERN.test(encoded)) {
        throw new Error("Generated prompt sentinel was not valid 128-bit Base64.");
    }
    return encoded;
}

function expandPromptSentinel(text, sentinel) {
    return String(text).replace(/\{sentinel\}/g, sentinel);
}

function weightedPromptText() {
    const eligibleIndexes = eligiblePromptIndexesForAnimation();
    const selectedIndex = weightedPromptRowIndex(eligibleIndexes, Math.random());
    return selectedIndex === null
        ? "Read AGENTS.md and keep going."
        : stringValue(promptRows[selectedIndex].textField);
}

function currentRunScriptOption() {
    return runnerSelectedScriptPath;
}


function runnerRootDirectory() {
    return String(ObjC.unwrap($(runnerSelectedScriptPath).stringByDeletingLastPathComponent));
}

function runnerScriptName() {
    return String(ObjC.unwrap($(runnerSelectedScriptPath).lastPathComponent));
}

function readTextFile(path, preserveWhitespace) {
    const data = $.NSFileManager.defaultManager.contentsAtPath(path);
    if (objcObjectIsNil(data)) {
        return null;
    }
    const text = $.NSString.alloc.initWithDataEncoding(data, $.NSUTF8StringEncoding);
    if (objcObjectIsNil(text)) {
        return null;
    }
    const value = String(ObjC.unwrap(text));
    return preserveWhitespace ? value : value.trim();
}

function runnerTaskIsRunning() {
    return Boolean(runnerTask && runnerTask.isRunning);
}

function runnerOperationInProgress() {
    return runnerTaskIsRunning() || Boolean(orphanedRunner);
}

function isRegularFileAtPath(path) {
    const isDirectory = Ref();
    return Boolean(
        $.NSFileManager.defaultManager.fileExistsAtPathIsDirectory(path, isDirectory)
    ) && !Boolean(isDirectory[0]);
}

function executionSnapshotPathsForSelectedRunner() {
    if (!runnerPathDirectoryExists()) {
        return [];
    }
    const names = $.NSFileManager.defaultManager.contentsOfDirectoryAtPathError(
        runnerRootDirectory(),
        undefined
    );
    if (objcObjectIsNil(names)) {
        return [];
    }
    const result = [];
    for (let index = 0; index < Number(names.count); index += 1) {
        const name = String(ObjC.unwrap(names.objectAtIndex(index)));
        if (!EXECUTION_SNAPSHOT_NAME_PATTERN.test(name)) {
            continue;
        }
        const path = runnerRootDirectory() + "/" + name;
        if (isRegularFileAtPath(path)) {
            result.push(path);
        }
    }
    return result;
}

function commandOutput(launchPath, argumentsList) {
    const task = $.NSTask.alloc.init;
    const pipe = $.NSPipe.pipe;
    task.setLaunchPath(launchPath);
    task.setArguments(argumentsList);
    task.setStandardOutput(pipe);
    task.setStandardError($.NSFileHandle.fileHandleWithNullDevice);
    task.launch;
    const data = pipe.fileHandleForReading.readDataToEndOfFile;
    task.waitUntilExit;
    if (Number(task.terminationStatus) !== 0 || objcObjectIsNil(data)) {
        return null;
    }
    const text = $.NSString.alloc.initWithDataEncoding(data, $.NSUTF8StringEncoding);
    return objcObjectIsNil(text) ? null : String(ObjC.unwrap(text));
}

function runnerProcessRows() {
    const output = commandOutput("/bin/ps", [
        "-ww",
        "-axo",
        "pid=,ppid=,pgid=,command="
    ]);
    if (output === null) {
        return [];
    }
    const result = [];
    for (const line of output.split("\n")) {
        const match = line.match(/^\s*(\d+)\s+(\d+)\s+(\d+)\s+(.*)$/);
        if (!match) {
            continue;
        }
        result.push({
            pid: Number(match[1]),
            ppid: Number(match[2]),
            pgid: Number(match[3]),
            command: match[4]
        });
    }
    return result;
}

function activeRunRecordIsValid(record) {
    if (!record || typeof record !== "object" || Array.isArray(record) ||
        record.schemaVersion !== ACTIVE_RUN_RECORD_SCHEMA_VERSION ||
        typeof record.token !== "string" ||
        !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(record.token) ||
        record.runnerPath !== RUNNER_PATH ||
        record.selectedScriptPath !== runnerSelectedScriptPath ||
        typeof record.snapshotPath !== "string") {
        return false;
    }
    const snapshotDirectory = String(ObjC.unwrap(
        $(record.snapshotPath).stringByDeletingLastPathComponent
    ));
    const snapshotName = String(ObjC.unwrap($(record.snapshotPath).lastPathComponent));
    return snapshotDirectory === runnerRootDirectory() &&
        EXECUTION_SNAPSHOT_NAME_PATTERN.test(snapshotName);
}

function loadActiveRunRecord() {
    const text = readTextFile(ACTIVE_RUN_RECORD_PATH, true);
    if (text === null) {
        return null;
    }
    try {
        return JSON.parse(text);
    } catch (error) {
        return { invalid: true, error: String(error) };
    }
}

function writeActiveRunRecord(record, allowSameToken) {
    const existing = loadActiveRunRecord();
    if (existing && (!allowSameToken || existing.token !== record.token)) {
        throw new Error(`Active-run ownership record already exists at ${ACTIVE_RUN_RECORD_PATH}.`);
    }
    const created = $.NSFileManager.defaultManager
        .createDirectoryAtPathWithIntermediateDirectoriesAttributesError(
            CONFIG_DIRECTORY,
            true,
            undefined,
            undefined
        );
    if (!Boolean(created)) {
        throw new Error(`Could not create ownership-record directory: ${CONFIG_DIRECTORY}`);
    }
    const json = JSON.stringify(record, null, 2) + "\n";
    if (!Boolean($(json).writeToFileAtomicallyEncodingError(
        ACTIVE_RUN_RECORD_PATH,
        true,
        $.NSUTF8StringEncoding,
        undefined
    ))) {
        throw new Error(`Could not write active-run ownership record: ${ACTIVE_RUN_RECORD_PATH}`);
    }
}

function clearActiveRunRecord(expectedToken) {
    const existing = loadActiveRunRecord();
    if (!existing) {
        return true;
    }
    if (!expectedToken || existing.token !== expectedToken) {
        return false;
    }
    return Boolean($.NSFileManager.defaultManager.removeItemAtPathError(
        ACTIVE_RUN_RECORD_PATH,
        undefined
    ));
}

function processMatchesOwnedRunner(process, ownership) {
    if (!process || process.ppid !== 1 ||
        process.command.indexOf(ownership.snapshotPath) < 0) {
        return false;
    }
    if (ownership.descendant) {
        return process.pid === ownership.pid && process.pgid === ownership.pgid;
    }
    if (process.pid !== process.pgid ||
        process.command.indexOf(RUNNER_PATH) < 0 ||
        process.command.indexOf("--once") < 0) {
        return false;
    }
    return ownership.legacy || process.command.indexOf(
        `--ui-owner-token ${ownership.token}`
    ) >= 0;
}

function matchingOwnedRunnerProcesses(ownership, includeAttached) {
    return runnerProcessRows().filter(process => {
        if (!includeAttached && process.ppid !== 1) {
            return false;
        }
        if (process.pid !== process.pgid ||
            process.command.indexOf(RUNNER_PATH) < 0 ||
            process.command.indexOf("--once") < 0 ||
            process.command.indexOf(ownership.snapshotPath) < 0) {
            return false;
        }
        return ownership.legacy || process.command.indexOf(
            `--ui-owner-token ${ownership.token}`
        ) >= 0;
    });
}

function setDetectedOrphanedRunner(orphan) {
    orphanedRunner = orphan;
    runnerExistingScriptNotice = false;
    if (monitorState) {
        disableRunnerAutoMode(monitorState.ui);
        scheduleConfigurationSave();
    }
}

function detectOrphanedRunner() {
    if (runnerTaskIsRunning()) {
        return null;
    }

    const record = loadActiveRunRecord();
    if (record) {
        if (!activeRunRecordIsValid(record)) {
            return {
                phase: "conflict",
                legacy: false,
                detail: `Invalid or mismatched ownership record retained at ${ACTIVE_RUN_RECORD_PATH}.`
            };
        }
        const ownership = {
            token: record.token,
            snapshotPath: record.snapshotPath,
            selectedScriptPath: record.selectedScriptPath,
            legacy: false
        };
        const matches = matchingOwnedRunnerProcesses(ownership, true);
        if (matches.length > 1) {
            return {
                ...ownership,
                phase: "conflict",
                detail: "Multiple processes matched the active-run ownership token; refusing to signal any process."
            };
        }
        if (matches.length === 1) {
            const process = matches[0];
            return {
                ...ownership,
                pid: process.pid,
                pgid: process.pgid,
                phase: process.ppid === 1 ? "running" : "foreign",
                detail: process.ppid === 1
                    ? "Detached runner verified."
                    : "Runner is still owned by another live dashboard."
            };
        }
        if (isRegularFileAtPath(record.snapshotPath)) {
            return {
                ...ownership,
                phase: "recoverable",
                detail: "No live owner remains; click the status icon to recover the exact snapshot."
            };
        }
        clearActiveRunRecord(record.token);
        return null;
    }

    const snapshots = executionSnapshotPathsForSelectedRunner();
    const processes = runnerProcessRows();
    const matches = [];
    const unverifiedReferences = [];
    for (const snapshotPath of snapshots) {
        const ownership = {
            snapshotPath,
            selectedScriptPath: runnerSelectedScriptPath,
            legacy: true,
            token: null
        };
        for (const process of processes) {
            if (process.command.indexOf(snapshotPath) < 0) {
                continue;
            }
            if (process.pid === process.pgid &&
                process.command.indexOf(RUNNER_PATH) >= 0 &&
                process.command.indexOf("--once") >= 0) {
                matches.push({ ownership, process });
            } else {
                unverifiedReferences.push({ ownership, process });
            }
        }
    }
    if (matches.length > 1 || snapshots.length > 1) {
        return {
            phase: "conflict",
            legacy: true,
            detail: "Multiple legacy execution snapshots or owners matched this project; refusing automatic recovery."
        };
    }
    if (matches.length === 1) {
        const match = matches[0];
        return {
            ...match.ownership,
            pid: match.process.pid,
            pgid: match.process.pgid,
            phase: match.process.ppid === 1 ? "running" : "foreign",
            detail: match.process.ppid === 1
                ? "Legacy detached runner verified by exact runner and snapshot paths."
                : "Legacy runner is still owned by another live dashboard."
        };
    }
    if (unverifiedReferences.length === 1 &&
        unverifiedReferences[0].process.ppid === 1) {
        const reference = unverifiedReferences[0];
        return {
            ...reference.ownership,
            pid: reference.process.pid,
            pgid: reference.process.pgid,
            descendant: true,
            phase: "running",
            detail: "Detached snapshot process verified after its original runner leader exited."
        };
    }
    if (unverifiedReferences.length > 0) {
        return {
            ...unverifiedReferences[0].ownership,
            phase: "conflict",
            detail: "Processes still reference the snapshot, but ownership cannot be safely verified."
        };
    }
    if (snapshots.length === 1) {
        return {
            snapshotPath: snapshots[0],
            selectedScriptPath: runnerSelectedScriptPath,
            legacy: true,
            token: null,
            phase: "recoverable",
            detail: "No live owner remains; click the status icon to preserve or restore the exact legacy snapshot."
        };
    }
    return null;
}

function sandboxArgument() {
    if (!monitorState || !monitorState.ui.runnerSandboxButton) {
        return "--sandbox";
    }
    return Number(monitorState.ui.runnerSandboxButton.state) === Number($.NSControlStateValueOn)
        ? "--sandbox"
        : "--no-sandbox";
}

function runnerNotifyWait() {
    if (!monitorState || !monitorState.ui.runnerWaitSlider) {
        return RUNNER_NOTIFY_WAIT_DEFAULT_SECONDS;
    }
    return clamp(
        Number(monitorState.ui.runnerWaitSlider.doubleValue),
        RUNNER_NOTIFY_WAIT_MIN_SECONDS,
        RUNNER_NOTIFY_WAIT_MAX_SECONDS
    );
}

function runnerConfigurationFingerprint() {
    return `${runnerSelectedScriptPath}|${sandboxArgument()}`;
}

function sandboxIsEnabled() {
    return sandboxArgument() === "--sandbox";
}

function runnerExecutionAllowed() {
    return !sandboxIsEnabled() || (
        runnerSelfTestStatus === "passed" &&
        runnerValidatedConfiguration === runnerConfigurationFingerprint()
    );
}

function runnerAutoModeEnabled() {
    return Boolean(
        monitorState &&
        monitorState.ui.runnerAutoButton &&
        Number(monitorState.ui.runnerAutoButton.state) === Number($.NSControlStateValueOn)
    );
}

function shellQuote(value) {
    return "'" + String(value).replace(/'/g, "'\"'\"'") + "'";
}

function runnerFileExists() {
    return Boolean(
        $.NSFileManager.defaultManager.fileExistsAtPath(runnerSelectedScriptPath)
    );
}

function runnerPathDirectoryExists() {
    const isDirectory = Ref();
    return Boolean(
        $.NSFileManager.defaultManager.fileExistsAtPathIsDirectory(
            runnerRootDirectory(),
            isDirectory
        )
    ) && Boolean(isDirectory[0]);
}

function runnerDisplayState() {
    if (runnerTaskIsRunning()) {
        return "running";
    }
    if (orphanedRunner) {
        if (orphanedRunner.phase === "recoverable") {
            return "orphan recovery";
        }
        if (orphanedRunner.phase === "term-sent" ||
            orphanedRunner.phase === "kill-sent") {
            return "orphan stopping";
        }
        if (orphanedRunner.phase === "conflict" || orphanedRunner.phase === "foreign") {
            return "orphan conflict";
        }
        return "orphaned";
    }
    if (!runnerPathDirectoryAvailable) {
        return "path error";
    }
    if (sandboxIsEnabled() && !runnerExecutionAllowed()) {
        return "uninitialized";
    }
    if (runnerSentinelDetected) {
        return "sentinel";
    }
    return runnerReady ? "ready" : "idle";
}

function refreshRunnerPresence(now, force) {
    if (!force && now - lastRunnerPresenceCheckAt < RUNNER_PRESENCE_POLL_SECONDS * 1000) {
        return false;
    }

    const wasReady = runnerReady;
    const pathWasAvailable = runnerPathDirectoryAvailable;
    runnerPathDirectoryAvailable = runnerPathDirectoryExists();
    runnerReady = runnerPathDirectoryAvailable && runnerFileExists();
    if (!runnerReady) {
        runnerExistingScriptNotice = false;
    }
    lastRunnerPresenceCheckAt = now;
    if ((runnerReady !== wasReady || runnerPathDirectoryAvailable !== pathWasAvailable) &&
        !runnerTaskIsRunning()) {
        runnerStatusDetail = !runnerPathDirectoryAvailable
            ? `Project directory does not exist: ${runnerRootDirectory()}.`
            : runnerReady
                ? `${runnerScriptName()} is available.`
                : `Waiting for ${runnerScriptName()} to become available.`;
    }
    return runnerReady !== wasReady || runnerPathDirectoryAvailable !== pathWasAvailable;
}

function existingRunScriptNoticeText() {
    return `${runnerScriptName()} already exists. Auto Mode is off; once ready, ` +
        "click the status icon to execute and archive it.";
}

function disableSignalSources(ui) {
    if (!ui) {
        return false;
    }
    const changed = Number(ui.cpuActiveButton.state) === Number($.NSControlStateValueOn) ||
        Number(ui.waitActiveButton.state) === Number($.NSControlStateValueOn);
    ui.cpuActiveButton.setState($.NSControlStateValueOff);
    ui.waitActiveButton.setState($.NSControlStateValueOff);
    if (monitorState) {
        monitorState.trailingLowCPUSeconds = 0;
        monitorState.cpuWarning = false;
        monitorState.ui.cpuGraph.setAlphaValue(1.0);
        resetWaitProgress();
    }
    return changed;
}

function disableRunnerAutoMode(ui) {
    ui.runnerAutoButton.setState($.NSControlStateValueOff);
    runnerAutoTriggeredForPresence = false;
    disableSignalSources(ui);
}

function disableAutoModeForExistingRunScript(ui, showNotice) {
    if (!runnerFileExists()) {
        runnerExistingScriptNotice = false;
        return false;
    }

    disableRunnerAutoMode(ui);
    runnerExistingScriptNotice = Boolean(showNotice);
    return true;
}

function runnerOutputIsVisible() {
    return Boolean(
        monitorState &&
        monitorState.ui.runnerOutputCard &&
        !Boolean(monitorState.ui.runnerOutputCard.hidden)
    );
}

function runnerScriptPreviewAvailable() {
    return Boolean(
        monitorState &&
        runnerDisplayState() === "ready" &&
        !runnerAutoModeEnabled()
    );
}

function runnerOutputDesiredMode() {
    return runnerScriptPreviewAvailable() ? "script" : "output";
}

function setRunnerOutputText(text, scrollToEnd) {
    if (!runnerOutputTextView) {
        return;
    }
    runnerOutputTextView.setString(text);
    runnerOutputTextView.scrollRangeToVisible(
        $.NSMakeRange(scrollToEnd ? text.length : 0, 0)
    );
}

function pollRunnerScriptPreview(now, force) {
    if (!force && now - runnerScriptPreviewLastPollAt < 250) {
        return;
    }
    runnerScriptPreviewLastPollAt = now;

    const script = readTextFile(runnerSelectedScriptPath, true);
    const displayText = script === null
        ? `[Could not read watched script: ${runnerSelectedScriptPath}]`
        : script;
    if (displayText === runnerScriptPreviewLastText &&
        runnerOutputPresentationMode === "script") {
        return;
    }
    runnerScriptPreviewLastText = displayText;
    runnerOutputPresentationMode = "script";
    setRunnerOutputText(displayText, false);
}

function updateRunnerOutputPresentation(now, force) {
    if (!monitorState || !monitorState.ui.runnerOutputCard) {
        return;
    }
    const ui = monitorState.ui;
    const mode = runnerOutputDesiredMode();
    const visible = runnerOutputIsVisible();
    ui.runnerOutputButton.setTitle(visible
        ? "Signals"
        : mode === "script" ? "Script" : "Output");
    ui.runnerOutputButton.setToolTip(mode === "script"
        ? `Show the exact watched script at ${runnerSelectedScriptPath}.`
        : "Show the latest embedded runner output.");
    ui.runnerOutputSectionTitle.setStringValue(
        mode === "script" ? "WATCHED RUN SCRIPT" : "RUNNER OUTPUT"
    );
    ui.runnerOutputSectionTitle.setToolTip(
        mode === "script" ? runnerSelectedScriptPath : RUNNER_OUTPUT_PATH
    );

    if (!visible && !force) {
        return;
    }
    if (mode === "script") {
        pollRunnerScriptPreview(now, force);
    } else {
        pollRunnerOutput(now, force);
    }
}

function setRunnerOutputVisible(visible) {
    if (!monitorState || !monitorState.ui.runnerOutputCard) {
        return;
    }

    const ui = monitorState.ui;
    for (const view of ui.signalViews) {
        view.setHidden(visible);
    }
    for (const view of ui.runnerOutputViews) {
        view.setHidden(!visible);
    }
    updateRunnerOutputPresentation(Date.now(), visible);
}

function toggleRunnerOutput() {
    const willShowOutput = !runnerOutputIsVisible();
    if (willShowOutput && signalAnimation) {
        cancelSignalAnimation();
    }
    setRunnerOutputVisible(willShowOutput);
}

function pollRunnerOutput(now, force) {
    if (!force && now - runnerOutputLastPollAt < 250) {
        return;
    }
    runnerOutputLastPollAt = now;

    const output = readTextFile(RUNNER_OUTPUT_PATH, true) || "";
    if (output === runnerOutputLastText && runnerOutputPresentationMode === "output") {
        return;
    }
    runnerOutputLastText = output;

    const maximumCharacters = 500000;
    const displayText = output.length > maximumCharacters
        ? "[… earlier output omitted …]\n" + output.slice(-maximumCharacters)
        : output;
    runnerOutputPresentationMode = "output";
    setRunnerOutputText(displayText, true);
}

function launchRunnerTask(mode, argumentsList) {
    if (perplexityRestart || orphanedRunner) {
        return false;
    }
    if (signalAnimation) {
        cancelSignalAnimation();
    }
    if (runnerTaskIsRunning()) {
        return false;
    }

    if (!Boolean($.NSFileManager.defaultManager.isExecutableFileAtPath(RUNNER_PATH))) {
        runnerStatusDetail = `Runner is not executable: ${RUNNER_PATH}`;
        return false;
    }

    try {
        const outputPath = shellQuote(RUNNER_OUTPUT_PATH);
        const command = `: > ${outputPath}; exec \"$@\" >> ${outputPath} 2>&1`;
        const task = $.NSTask.alloc.init;
        task.setLaunchPath("/usr/bin/perl");
        task.setArguments([
            "-MPOSIX",
            "-e",
            "POSIX::setsid(); exec @ARGV",
            "/bin/sh",
            "-c",
            command,
            "runner-ui",
            RUNNER_PATH,
            ...argumentsList
        ]);
        task.setCurrentDirectoryPath(runnerRootDirectory());
        task.setStandardInput($.NSFileHandle.fileHandleWithNullDevice);
        task.launch;

        runnerTask = task;
        runnerTaskMode = mode;
        runnerTaskStartedAt = Date.now();
        runnerLastExitStatus = null;
        runnerKillRequested = false;
        runnerKillDeadline = null;
        runnerStatusDetail = "";
        runnerOutputLastText = "";
        runnerOutputLastPollAt = 0;
        runnerOutputPresentationMode = null;
        setRunnerOutputText("", true);
        if (mode === "run") {
            resetWaitProgress();
        }
        setRunnerOutputVisible(true);
        updateRunnerUI(Date.now());
        return true;
    } catch (error) {
        runnerTask = null;
        runnerTaskMode = null;
        runnerStatusDetail = `Could not launch runner: ${error}`;
        return false;
    }
}


function signalRunnerProcessGroup(pid, signalNumber) {
    const leaderPID = Math.trunc(Number(pid));
    if (!Number.isFinite(leaderPID) || leaderPID <= 0) {
        return false;
    }

    if (Number($.kill(-leaderPID, signalNumber)) === 0) {
        return true;
    }
    return Number($.kill(leaderPID, signalNumber)) === 0;
}

function requestRunnerStop(userInitiated) {
    if (!runnerTaskIsRunning()) {
        return;
    }

    const pid = Number(runnerTask.processIdentifier);
    runnerKillRequested = runnerKillRequested || userInitiated;
    runnerKillDeadline = Date.now() + 1200;
    signalRunnerProcessGroup(pid, 15);
}

function startRunnerSelfTest() {
    if (runnerOperationInProgress() || perplexityRestart) {
        return;
    }
    refreshRunnerPresence(Date.now(), true);
    if (!runnerPathDirectoryAvailable) {
        runnerSelfTestStatus = "unverified";
        runnerValidatedConfiguration = null;
        runnerStatusDetail = `Project directory does not exist: ${runnerRootDirectory()}.`;
        updateRunnerUI(Date.now());
        return;
    }

    runnerSelfTestStatus = "running";
    runnerValidatedConfiguration = null;
    runnerTaskConfiguration = runnerConfigurationFingerprint();
    if (!launchRunnerTask("selftest", [
        sandboxArgument(),
        "--self-test-only",
        runnerSelectedScriptPath
    ])) {
        runnerSelfTestStatus = "failed";
    }
}

function scriptContainsPromptSentinel(scriptText, sentinel) {
    return Boolean(sentinel) && String(scriptText).indexOf(sentinel) >= 0;
}

function disableAutoModeForRunnerSafety(message) {
    disableRunnerAutoMode(monitorState.ui);
    runnerExistingScriptNotice = false;
    runnerStatusDetail = message;
    scheduleConfigurationSave();
    updateRunnerUI(Date.now());
}

function uniqueRunnerStagingPath(kind) {
    const identifier = String(ObjC.unwrap($.NSUUID.UUID.UUIDString)).toLowerCase();
    return runnerRootDirectory() + `/.perplexity-cpu-loop-${kind}-${identifier}.sh`;
}

function restoreStagedScript(stagedPath, originalPath, reason) {
    const fileManager = $.NSFileManager.defaultManager;
    if (!Boolean(fileManager.fileExistsAtPath(stagedPath))) {
        return {
            restored: false,
            message: `${reason} The staged file is no longer available at ${stagedPath}.`
        };
    }
    if (Boolean(fileManager.fileExistsAtPath(originalPath))) {
        return {
            restored: false,
            message: `${reason} New work already exists at ${originalPath}; recovery file retained at ${stagedPath}.`
        };
    }
    if (Boolean(fileManager.moveItemAtPathToPathError(stagedPath, originalPath, undefined))) {
        return {
            restored: true,
            message: `${reason} The exact staged bytes were restored to ${originalPath}.`
        };
    }
    return {
        restored: false,
        message: `${reason} Restore failed; recovery file retained at ${stagedPath}.`
    };
}

function removeStagingPathIfPresent(path) {
    const fileManager = $.NSFileManager.defaultManager;
    return !Boolean(fileManager.fileExistsAtPath(path)) ||
        Boolean(fileManager.removeItemAtPathError(path, undefined));
}

function verifiedOrphanedRunnerProcess(orphan) {
    if (!orphan || !Number.isFinite(orphan.pid)) {
        return null;
    }
    for (const process of runnerProcessRows()) {
        if (process.pid === orphan.pid && processMatchesOwnedRunner(process, orphan)) {
            return process;
        }
    }
    return null;
}

function recoverOrphanedRunner(reason) {
    if (!orphanedRunner || !orphanedRunner.snapshotPath ||
        !orphanedRunner.selectedScriptPath) {
        return false;
    }
    const orphan = orphanedRunner;
    let recovery;
    if (runnerFileExists() && isRegularFileAtPath(orphan.snapshotPath)) {
        const recoveryPath = uniqueRunnerStagingPath("recovery");
        const moved = $.NSFileManager.defaultManager.moveItemAtPathToPathError(
            orphan.snapshotPath,
            recoveryPath,
            undefined
        );
        recovery = Boolean(moved)
            ? {
                restored: false,
                message: `${reason} New work already exists at ${orphan.selectedScriptPath}; ` +
                    `the orphan snapshot was preserved at ${recoveryPath}.`
            }
            : {
                restored: false,
                message: `${reason} New work already exists at ${orphan.selectedScriptPath}; ` +
                    `the orphan snapshot remains at ${orphan.snapshotPath}.`
            };
    } else {
        recovery = restoreStagedScript(
            orphan.snapshotPath,
            orphan.selectedScriptPath,
            reason
        );
    }
    if (!orphan.legacy) {
        clearActiveRunRecord(orphan.token);
    }
    orphanedRunner = null;
    disableRunnerAutoMode(monitorState.ui);
    runnerReady = runnerFileExists();
    runnerExistingScriptNotice = false;
    runnerAutoTriggeredForPresence = false;
    runnerStatusDetail = recovery.message;
    scheduleConfigurationSave();
    updateRunnerUI(Date.now());
    return true;
}

function signalOrphanedRunner(orphan, signalNumber) {
    if (orphan.descendant) {
        return Number($.kill(orphan.pid, signalNumber)) === 0;
    }
    return signalRunnerProcessGroup(orphan.pgid, signalNumber);
}

function requestOrphanedRunnerStop() {
    if (!orphanedRunner) {
        return;
    }
    if (orphanedRunner.phase === "recoverable") {
        recoverOrphanedRunner("Recovering an unowned execution snapshot.");
        return;
    }
    if (orphanedRunner.phase !== "running") {
        return;
    }

    const process = verifiedOrphanedRunnerProcess(orphanedRunner);
    if (!process) {
        recoverOrphanedRunner("Detached runner already exited before TERM.");
        return;
    }
    signalOrphanedRunner(orphanedRunner, 15);
    orphanedRunner.phase = "term-sent";
    orphanedRunner.killDeadline = Date.now() + ORPHAN_RUNNER_KILL_FALLBACK_MILLISECONDS;
    orphanedRunner.detail = orphanedRunner.descendant
        ? "TERM sent to the verified orphan snapshot process; KILL fallback armed."
        : "TERM sent to the verified orphan process group; KILL fallback armed.";
    updateRunnerUI(Date.now());
}

function orphanedRunnerTick(now, force) {
    if (!force && now - lastOrphanRunnerPollAt < ORPHAN_RUNNER_POLL_SECONDS * 1000) {
        return;
    }
    lastOrphanRunnerPollAt = now;

    if (!orphanedRunner) {
        const detected = detectOrphanedRunner();
        if (detected) {
            setDetectedOrphanedRunner(detected);
        }
        return;
    }

    if (orphanedRunner.phase === "running") {
        // Self-disappearance edge ("orphaned" -> "idle"): the detached
        // process may exit on its own (killed externally, crashed, or
        // completed) without any click on the LED. This branch is the
        // sole place that transition fires; no separate UI state is
        // needed since recoverOrphanedRunner() clears orphanedRunner and
        // the next runnerDisplayState() call naturally falls through to
        // "idle"/"ready". See /tmp/autodocs/_src/tools/orphan-state-diagram
        // for the corresponding dashed edge in the rendered diagram.
        if (!verifiedOrphanedRunnerProcess(orphanedRunner)) {
            recoverOrphanedRunner("Detached runner exited; recovering its unconsumed snapshot.");
        }
        return;
    }
    if (orphanedRunner.phase === "term-sent") {
        const process = verifiedOrphanedRunnerProcess(orphanedRunner);
        if (!process) {
            recoverOrphanedRunner("Detached runner stopped after TERM; recovering its snapshot.");
            return;
        }
        if (now >= orphanedRunner.killDeadline) {
            signalOrphanedRunner(orphanedRunner, 9);
            orphanedRunner.phase = "kill-sent";
            orphanedRunner.killDeadline = now + ORPHAN_RUNNER_KILL_VERIFY_MILLISECONDS;
            orphanedRunner.detail = orphanedRunner.descendant
                ? "KILL sent to the reverified orphan snapshot process; waiting for exit."
                : "KILL sent to the reverified orphan process group; waiting for exit.";
        }
        return;
    }
    if (orphanedRunner.phase === "kill-sent") {
        if (!verifiedOrphanedRunnerProcess(orphanedRunner)) {
            recoverOrphanedRunner("Detached runner stopped after KILL; recovering its snapshot.");
        } else if (now >= orphanedRunner.killDeadline) {
            orphanedRunner.phase = "conflict";
            orphanedRunner.detail = "Verified orphan still exists after KILL; refusing further automatic signals.";
        }
        return;
    }
    if (orphanedRunner.phase === "foreign") {
        const detected = detectOrphanedRunner();
        if (!detected) {
            orphanedRunner = null;
        } else {
            orphanedRunner = detected;
        }
    }
}

function failClaimedRunnerPreparation(claimPath, snapshotPath, message) {
    let cleanupDetail = "";
    if (snapshotPath && !removeStagingPathIfPresent(snapshotPath)) {
        cleanupDetail = ` Additional recovery file retained at ${snapshotPath}.`;
    }
    const recovery = restoreStagedScript(
        claimPath,
        runnerSelectedScriptPath,
        message
    );
    disableAutoModeForRunnerSafety(recovery.message + cleanupDetail);
    return null;
}

function prepareRunnerExecutionSnapshot() {
    const fileManager = $.NSFileManager.defaultManager;
    const originalPath = runnerSelectedScriptPath;
    const claimPath = uniqueRunnerStagingPath("claim");
    const snapshotPath = uniqueRunnerStagingPath("execution");
    if (!Boolean(fileManager.moveItemAtPathToPathError(originalPath, claimPath, undefined))) {
        disableAutoModeForRunnerSafety(
            `Runner start was blocked: could not atomically claim ${originalPath} for inspection.`
        );
        return null;
    }

    try {
    const scriptData = fileManager.contentsAtPath(claimPath);
    if (objcObjectIsNil(scriptData)) {
        return failClaimedRunnerPreparation(
            claimPath,
            null,
            `Runner start was blocked: could not read claimed script bytes at ${claimPath}.`
        );
    }
    const bytePreservingText = $.NSString.alloc.initWithDataEncoding(
        scriptData,
        $.NSISOLatin1StringEncoding
    );
    if (objcObjectIsNil(bytePreservingText)) {
        return failClaimedRunnerPreparation(
            claimPath,
            null,
            `Runner start was blocked: could not inspect claimed script bytes at ${claimPath}.`
        );
    }
    if (!Boolean(scriptData.writeToFileOptionsError(
        snapshotPath,
        $.NSDataWritingAtomic,
        undefined
    ))) {
        return failClaimedRunnerPreparation(
            claimPath,
            snapshotPath,
            `Runner start was blocked: could not atomically create execution snapshot ${snapshotPath}.`
        );
    }
    const claimedAttributes = fileManager.attributesOfItemAtPathError(claimPath, undefined);
    const claimedPermissions = !objcObjectIsNil(claimedAttributes)
        ? claimedAttributes.objectForKey($.NSFilePosixPermissions)
        : undefined;
    const snapshotAttributes = !objcObjectIsNil(claimedPermissions)
        ? $.NSDictionary.dictionaryWithObjectForKey(
            claimedPermissions,
            $.NSFilePosixPermissions
        )
        : undefined;
    if (objcObjectIsNil(snapshotAttributes) || !Boolean(fileManager.setAttributesOfItemAtPathError(
        snapshotAttributes,
        snapshotPath,
        undefined
    ))) {
        return failClaimedRunnerPreparation(
            claimPath,
            snapshotPath,
            `Runner start was blocked: could not preserve executable permissions on ${snapshotPath}.`
        );
    }

    const inspectedText = String(ObjC.unwrap(bytePreservingText));
    if (scriptContainsPromptSentinel(inspectedText, activePromptSentinel)) {
        const snapshotRemoved = removeStagingPathIfPresent(snapshotPath);
        const recovery = restoreStagedScript(
            claimPath,
            originalPath,
            "Prompt sentinel detected; Auto Mode disabled and runner was not started."
        );
        const cleanupDetail = snapshotRemoved
            ? ""
            : ` Duplicate execution snapshot also retained at ${snapshotPath}.`;
        disableAutoModeForRunnerSafety(recovery.message + cleanupDetail);
        return null;
    }

    if (!removeStagingPathIfPresent(claimPath)) {
        removeStagingPathIfPresent(snapshotPath);
        return failClaimedRunnerPreparation(
            claimPath,
            null,
            `Runner start was blocked: could not remove claimed inode ${claimPath} after snapshotting.`
        );
    }
    return {
        originalPath,
        snapshotPath,
        inspectedText
    };
    } catch (error) {
        return failClaimedRunnerPreparation(
            claimPath,
            snapshotPath,
            `Runner start was blocked by a claim/inspection error: ${error}`
        );
    }
}

function recoverSnapshotBeforeOwnershipTransfer(snapshotPath, originalPath, reason) {
    const recovery = restoreStagedScript(snapshotPath, originalPath, reason);
    disableAutoModeForRunnerSafety(recovery.message);
}

function startOneShotRunner() {
    refreshRunnerPresence(Date.now(), true);
    if (runnerOperationInProgress() || signalAnimation || perplexityRestart ||
        !runnerExecutionAllowed() || !runnerReady) {
        return;
    }

    runnerExistingScriptNotice = false;
    let prepared;
    try {
        prepared = prepareRunnerExecutionSnapshot();
    } catch (error) {
        disableAutoModeForRunnerSafety(
            `Runner start was blocked by an unexpected claim/inspection error: ${error}`
        );
        runnerReady = runnerFileExists();
        return;
    }
    if (!prepared) {
        runnerReady = runnerFileExists();
        return;
    }

    let runnerGuardSentinel;
    try {
        runnerGuardSentinel = generateRandomPromptSentinel();
        while (runnerGuardSentinel === activePromptSentinel ||
            scriptContainsPromptSentinel(prepared.inspectedText, runnerGuardSentinel)) {
            runnerGuardSentinel = generateRandomPromptSentinel();
        }
    } catch (error) {
        recoverSnapshotBeforeOwnershipTransfer(
            prepared.snapshotPath,
            prepared.originalPath,
            `Runner start was blocked before launch: ${error}`
        );
        runnerReady = runnerFileExists();
        return;
    }

    const ownershipToken = String(ObjC.unwrap(
        $.NSUUID.UUID.UUIDString
    )).toLowerCase();
    const ownershipRecord = {
        schemaVersion: ACTIVE_RUN_RECORD_SCHEMA_VERSION,
        token: ownershipToken,
        runnerPath: RUNNER_PATH,
        selectedScriptPath: prepared.originalPath,
        snapshotPath: prepared.snapshotPath,
        pid: null,
        pgid: null,
        createdAt: new Date().toISOString()
    };
    try {
        writeActiveRunRecord(ownershipRecord, false);
    } catch (error) {
        recoverSnapshotBeforeOwnershipTransfer(
            prepared.snapshotPath,
            prepared.originalPath,
            `Runner start was blocked because ownership could not be recorded: ${error}`
        );
        runnerReady = runnerFileExists();
        return;
    }

    runnerActiveOwnershipToken = ownershipToken;
    runnerAutoTriggeredForPresence = true;
    if (launchRunnerTask("run", [
        sandboxArgument(),
        "--sentinel",
        runnerGuardSentinel,
        "--ui-owner-token",
        ownershipToken,
        "--once",
        "--notify-wait",
        runnerNotifyWait().toFixed(1),
        "--notifier",
        "/usr/bin/true",
        prepared.snapshotPath
    ])) {
        runnerExecutionOriginalPath = prepared.originalPath;
        runnerExecutionSnapshotPath = prepared.snapshotPath;
        const pid = Number(runnerTask.processIdentifier);
        ownershipRecord.pid = pid;
        ownershipRecord.pgid = pid;
        try {
            writeActiveRunRecord(ownershipRecord, true);
        } catch (error) {
            runnerStatusDetail = `Runner launched, but PID ownership update failed: ${error}`;
        }
    } else {
        clearActiveRunRecord(ownershipToken);
        runnerActiveOwnershipToken = null;
        recoverSnapshotBeforeOwnershipTransfer(
            prepared.snapshotPath,
            prepared.originalPath,
            `Runner launch failed before ownership transferred: ${runnerStatusDetail}`
        );
        runnerReady = runnerFileExists();
    }
}


function runnerPromptForExitStatus(status) {
    if (!monitorState) {
        return null;
    }

    const success = status === 0;
    const enabledButton = success
        ? monitorState.ui.runnerSuccessPromptButton
        : monitorState.ui.runnerFailurePromptButton;
    const textField = success
        ? monitorState.ui.runnerSuccessPromptField
        : monitorState.ui.runnerFailurePromptField;
    if (!enabledButton ||
        Number(enabledButton.state) !== Number($.NSControlStateValueOn)) {
        return null;
    }

    const template = stringValue(textField).trim();
    if (!template) {
        return null;
    }
    return template
        .replace(/\{exit\}/g, String(status))
        .replace(/\{code\}/g, String(status))
        .replace(/\{script\}/g, runnerScriptName())
        .replace(/\{output\}/g, RUNNER_OUTPUT_PATH);
}

function finishRunnerTask(now) {
    const completedMode = runnerTaskMode;
    const completedConfiguration = runnerTaskConfiguration;
    const status = Number(runnerTask.terminationStatus);
    const wasKilledByUser = runnerKillRequested;
    runnerLastExitStatus = status;
    runnerTask = null;
    runnerTaskMode = null;

    setRunnerOutputVisible(false);
    pollRunnerOutput(now, true);
    if (completedMode === "selftest") {
        runnerValidatedConfiguration = null;
        if (wasKilledByUser) {
            runnerSelfTestStatus = "unverified";
            runnerStatusDetail = "Environment self-test stopped by user.";
        } else {
            runnerSelfTestStatus = status === 0 ? "passed" : "failed";
            runnerValidatedConfiguration = status === 0
                ? completedConfiguration
                : null;
            runnerStatusDetail = status === 0
                ? (runnerReady
                    ? `Environment self-test passed; ${runnerScriptName()} is ready.`
                    : `Environment self-test passed; waiting for ${runnerScriptName()}.`)
                : `Environment self-test failed with exit code ${status}; see output/run-sandbox-selftest.log.`;
        }
    } else if (completedMode === "run") {
        let recoveryDetail = "";
        let snapshotRecovered = false;
        if (runnerExecutionSnapshotPath &&
            Boolean($.NSFileManager.defaultManager.fileExistsAtPath(
                runnerExecutionSnapshotPath
            ))) {
            const recovery = restoreStagedScript(
                runnerExecutionSnapshotPath,
                runnerExecutionOriginalPath,
                "Runner exited before consuming its checked execution snapshot."
            );
            recoveryDetail = ` ${recovery.message}`;
            snapshotRecovered = true;
            disableRunnerAutoMode(monitorState.ui);
            scheduleConfigurationSave();
        }
        runnerExecutionSnapshotPath = null;
        runnerExecutionOriginalPath = null;
        runnerReady = runnerFileExists();
        if (!runnerReady) {
            runnerExistingScriptNotice = false;
        }
        runnerAutoTriggeredForPresence = false;
        runnerStatusDetail = (wasKilledByUser
            ? "Runner stopped by user."
            : `One-shot runner finished with exit code ${status}.`) + recoveryDetail;
        if (!wasKilledByUser && !snapshotRecovered) {
            const completionPrompt = runnerPromptForExitStatus(status);
            pendingRunnerPrompt = completionPrompt
                ? {
                    text: completionPrompt,
                    attempts: 0,
                    nextAttemptAt: now
                }
                : null;
        }
    }

    if (completedMode === "run" && runnerActiveOwnershipToken) {
        if (!clearActiveRunRecord(runnerActiveOwnershipToken)) {
            runnerStatusDetail += ` Ownership record retained at ${ACTIVE_RUN_RECORD_PATH}.`;
        }
        runnerActiveOwnershipToken = null;
    }
    runnerTaskConfiguration = null;
    runnerKillRequested = false;
    runnerKillDeadline = null;
}

function runnerTick(now) {
    refreshRunnerPresence(now, false);
    if (runnerReady && !runnerTaskIsRunning() &&
        now - lastRunnerSentinelCheckAt >= RUNNER_SENTINEL_POLL_SECONDS * 1000) {
        lastRunnerSentinelCheckAt = now;
        const scriptText = readTextFile(runnerSelectedScriptPath, true);
        runnerSentinelDetected = scriptContainsPromptSentinel(scriptText, activePromptSentinel);
    }
    orphanedRunnerTick(now, false);
    if (orphanedRunner) {
        return;
    }
    if (runnerStartupSelfTestPending) {
        runnerStartupSelfTestPending = false;
        startRunnerSelfTest();
        if (runnerTaskIsRunning()) {
            return;
        }
    }
    if (!runnerReady) {
        if (!(runnerTaskMode === "run" && runnerTask)) {
            runnerAutoTriggeredForPresence = false;
        }
        if (!runnerTaskIsRunning() && runnerSelfTestStatus === "passed") {
            runnerStatusDetail = `Waiting for ${runnerScriptName()} at the selected path.`;
        }
    }

    if (runnerTask) {
        pollRunnerOutput(now, false);
        if (runnerTaskIsRunning()) {
            if (runnerKillDeadline !== null && now >= runnerKillDeadline) {
                const pid = Number(runnerTask.processIdentifier);
                signalRunnerProcessGroup(pid, 9);
                runnerKillDeadline = null;
            }
            return;
        }
        finishRunnerTask(now);
    }

    if (!signalAnimation && !perplexityRestart && !orphanedRunner &&
        runnerAutoModeEnabled() &&
        runnerExecutionAllowed() &&
        runnerReady &&
        !runnerAutoTriggeredForPresence) {
        startOneShotRunner();
    }
}

function waitSignalIsDueAt(now) {
    if (!monitorState || !waitSignalIsEnabled() || monitorState.waitSignalLatched) {
        return false;
    }
    const elapsed = Math.max(0, (now - monitorState.lastTick) / 1000);
    const timeout = Number(monitorState.ui.waitSlider.doubleValue);
    return monitorState.waitSeconds + elapsed >= timeout;
}

function deliverPendingRunnerPrompt(now, mouseButtonIsReleased) {
    if (!pendingRunnerPrompt || !mouseButtonIsReleased || signalAnimation ||
        perplexityRestart || orphanedRunner || waitSignalIsDueAt(now) ||
        now < pendingRunnerPrompt.nextAttemptAt) {
        return false;
    }

    try {
        sendPrompt(pendingRunnerPrompt.text);
        pendingRunnerPrompt = null;
        runnerStatusDetail += " Completion prompt sent.";
        resetCPUProgress();
        monitorState.pulsePhase = false;
        monitorState.lastPulse = 0;
        monitorState.ui.title.setTextColor($.NSColor.labelColor);
    } catch (error) {
        pendingRunnerPrompt.attempts += 1;
        if (pendingRunnerPrompt.attempts >= 3) {
            runnerStatusDetail += ` Completion prompt failed after 3 attempts: ${error}`;
            pendingRunnerPrompt = null;
        } else {
            pendingRunnerPrompt.nextAttemptAt = now + 1000;
            runnerStatusDetail += ` Completion prompt attempt ${pendingRunnerPrompt.attempts} failed; retrying: ${error}`;
        }
    }
    updateRunnerUI(Date.now());
    return true;
}

function updateRunnerUI(now) {
    if (!monitorState || !monitorState.ui.runnerStatusLabel) {
        return;
    }

    const ui = monitorState.ui;
    const taskRunning = runnerTaskIsRunning();
    const orphanBusy = Boolean(orphanedRunner);
    const runnerBusy = taskRunning || orphanBusy;
    const autoAvailable = !orphanBusy && runnerPathDirectoryAvailable &&
        (!sandboxIsEnabled() || runnerExecutionAllowed());
    let autoEnabled = runnerAutoModeEnabled();
    if (!taskRunning && !autoAvailable && autoEnabled) {
        disableRunnerAutoMode(ui);
        scheduleConfigurationSave();
        autoEnabled = false;
    }
    const displayState = runnerDisplayState();
    updateRunnerOutputPresentation(now, false);

    ui.runnerWaitValue.setStringValue(`${runnerNotifyWait().toFixed(1)} s`);
    ui.runnerSelectedPathLabel.setStringValue(runnerSelectedScriptPath);
    ui.runnerSelfTestButton.setEnabled(
        !runnerBusy && !perplexityRestart && runnerPathDirectoryAvailable
    );
    ui.runnerChooseButton.setEnabled(!runnerBusy && !perplexityRestart);
    ui.runnerOutputButton.setEnabled(
        runnerScriptPreviewAvailable() || taskRunning || Boolean(runnerOutputLastText)
    );
    ui.runnerSandboxButton.setEnabled(!runnerBusy && !perplexityRestart);
    ui.runnerAutoButton.setEnabled(
        !orphanBusy && (runnerTaskMode === "run" || (!taskRunning && autoAvailable))
    );
    ui.runnerAutoButton.setToolTip(
        runnerTaskMode === "run"
            ? "Toggle Auto Mode for future run scripts. This does not stop or restart the current runner."
            : "When enabled, an eligible watched run.sh starts automatically."
    );
    ui.runnerWaitSlider.setEnabled(!runnerBusy);
    ui.runnerSuccessPromptButton.setEnabled(!runnerBusy);
    ui.runnerSuccessPromptField.setEnabled(!runnerBusy);
    ui.runnerFailurePromptButton.setEnabled(!runnerBusy);
    ui.runnerFailurePromptField.setEnabled(!runnerBusy);
    ui.promptInjectButton.setEnabled(
        !taskRunning && !signalAnimation && !perplexityRestart
    );
    ui.configurationSaveButton.setEnabled(
        !runnerBusy && !signalAnimation && !perplexityRestart
    );
    ui.configurationMenu.setEnabled(
        !runnerBusy && !signalAnimation && !perplexityRestart
    );
    const orphanActionAvailable = Boolean(orphanedRunner && (
        orphanedRunner.phase === "running" || orphanedRunner.phase === "recoverable"
    ));
    ui.runnerLEDButton.setEnabled(
        taskRunning || orphanActionAvailable || (!orphanBusy && !perplexityRestart)
    );
    ui.runnerLEDButton.setAlphaValue(
        (perplexityRestart && !taskRunning) ||
        (orphanBusy && !orphanActionAvailable) ? 0.5 : 1.0
    );
    setRunnerStatusButtonImage(ui.runnerLEDButton, displayState);
    updateAutoModeButtonAppearance(ui.runnerAutoButton);

    let statusText;
    if (displayState === "running") {
        const elapsedSeconds = Math.max(0, (now - runnerTaskStartedAt) / 1000);
        const taskName = runnerTaskMode === "selftest"
            ? "environment self-test"
            : runnerScriptName();
        statusText = runnerKillRequested
            ? `Stopping ${taskName} · TERM sent; KILL fallback armed`
            : `Running ${taskName} · ${elapsedSeconds.toFixed(1)} s — click the cross kill switch to stop`;
        ui.runnerLEDButton.setContentTintColor($.NSColor.systemRedColor);
        ui.runnerActivityLabel.setTextColor($.NSColor.systemRedColor);
        ui.runnerLEDButton.setToolTip(
            "Kill the active runner task: send TERM now, then KILL if it has not stopped after 1.2 seconds."
        );
    } else if (displayState === "orphaned") {
        statusText = `Detached runner PID ${orphanedRunner.pid} owns ${orphanedRunner.snapshotPath}. Click the cross to stop and recover it.`;
        ui.runnerLEDButton.setContentTintColor($.NSColor.systemRedColor);
        ui.runnerActivityLabel.setTextColor($.NSColor.systemRedColor);
        ui.runnerLEDButton.setToolTip(orphanedRunner.descendant
            ? "Stop the exact verified orphan snapshot process with TERM/KILL, then safely recover its snapshot."
            : "Stop the exact verified orphan process group with TERM/KILL, then safely recover its snapshot."
        );
    } else if (displayState === "orphan stopping") {
        statusText = orphanedRunner.detail;
        ui.runnerLEDButton.setContentTintColor($.NSColor.systemRedColor);
        ui.runnerActivityLabel.setTextColor($.NSColor.systemRedColor);
        ui.runnerLEDButton.setToolTip(orphanedRunner.descendant
            ? "The verified orphan snapshot process is stopping."
            : "The verified orphan process group is stopping."
        );
    } else if (displayState === "orphan recovery") {
        statusText = orphanedRunner.detail;
        ui.runnerLEDButton.setContentTintColor($.NSColor.systemOrangeColor);
        ui.runnerActivityLabel.setTextColor($.NSColor.systemOrangeColor);
        ui.runnerLEDButton.setToolTip(
            "Recover the exact unowned snapshot without overwriting a newer run.sh."
        );
    } else if (displayState === "orphan conflict") {
        statusText = orphanedRunner.detail;
        ui.runnerLEDButton.setContentTintColor($.NSColor.systemOrangeColor);
        ui.runnerActivityLabel.setTextColor($.NSColor.systemOrangeColor);
        ui.runnerLEDButton.setToolTip("Ownership could not be verified; no process will be signaled.");
    } else if (displayState === "path error") {
        statusText = `Project directory does not exist: ${runnerRootDirectory()}.`;
        ui.runnerLEDButton.setContentTintColor($.NSColor.systemRedColor);
        ui.runnerActivityLabel.setTextColor($.NSColor.systemRedColor);
        ui.runnerLEDButton.setToolTip("The selected run-script directory does not exist.");
    } else if (displayState === "uninitialized") {
        statusText = runnerSelfTestStatus === "failed"
            ? runnerStatusDetail || "Environment self-test failed; run Self-test again."
            : runnerStatusDetail || "Environment self-test required.";
        ui.runnerLEDButton.setContentTintColor($.NSColor.systemOrangeColor);
        ui.runnerActivityLabel.setTextColor($.NSColor.systemOrangeColor);
        ui.runnerLEDButton.setToolTip("The current path and sandbox configuration require a self-test.");
    } else if (displayState === "sentinel") {
        statusText = runnerLEDHovering
            ? `Click to delete ${runnerScriptName()} and rotate the sentinel.`
            : `Sentinel token found in ${runnerScriptName()}; runner halted for safety.`;
        ui.runnerLEDButton.setContentTintColor($.NSColor.systemRedColor);
        ui.runnerActivityLabel.setTextColor($.NSColor.systemRedColor);
        ui.runnerLEDButton.setToolTip(PROMPT_SENTINEL_TOOLTIP);
    } else if (displayState === "idle") {
        statusText = `Waiting for ${runnerScriptName()} to become available.`;
        ui.runnerLEDButton.setContentTintColor(
            $.NSColor.systemGrayColor.colorWithAlphaComponent(0.72)
        );
        ui.runnerActivityLabel.setTextColor($.NSColor.secondaryLabelColor);
        ui.runnerLEDButton.setToolTip("Runner is initialized and waiting for the run script.");
    } else {
        statusText = runnerStatusDetail || (autoEnabled
            ? `${runnerScriptName()} is ready; Auto Mode will start it.`
            : `${runnerScriptName()} is ready for one-shot execution.`);
        ui.runnerActivityLabel.setTextColor($.NSColor.systemGreenColor);
        ui.runnerLEDButton.setToolTip(
            autoEnabled
                ? "Run script available; Auto Mode is starting it now."
                : "Click to execute and archive the available run script. During execution, this becomes the cross kill switch."
        );
    }

    const showExistingScriptNotice = runnerExistingScriptNotice &&
        displayState === "ready";
    if (showExistingScriptNotice) {
        statusText = existingRunScriptNoticeText();
        ui.runnerStatusLabel.setTextColor($.NSColor.systemOrangeColor);
        ui.runnerStatusLabel.setToolTip(
            `${runnerSelectedScriptPath} already exists. Auto Mode was turned off. ` +
            "After the runner is initialized, click the green status icon to execute and archive this file."
        );
    } else if (displayState.indexOf("orphan") === 0) {
        ui.runnerStatusLabel.setTextColor(
            displayState === "orphaned" || displayState === "orphan stopping"
                ? $.NSColor.systemRedColor
                : $.NSColor.systemOrangeColor
        );
        ui.runnerStatusLabel.setToolTip(orphanedRunner.detail || statusText);
    } else {
        ui.runnerStatusLabel.setTextColor($.NSColor.secondaryLabelColor);
        ui.runnerStatusLabel.setToolTip("");
    }

    ui.runnerActivityLabel.setStringValue(displayState);
    ui.runnerStatusLabel.setStringValue(statusText);
}

function clamp(value, minimum, maximum) {
    return Math.max(minimum, Math.min(maximum, value));
}

function resetCPUProgress() {
    if (!monitorState) {
        return;
    }

    const now = Date.now();
    monitorState.cpuSamples = [];
    monitorState.cpuGraphData = [];
    monitorState.graphEndTime = now;
    monitorState.currentRawCPU = 0;
    monitorState.currentAverageCPU = 0;
    monitorState.trailingLowCPUSeconds = 0;
    monitorState.lastCPUSample = now;
    monitorState.cpuWarning = false;

    previousProcessCPUTimes = {};
    previousCPUSampleTime = null;

    const cpuDuration = Number(monitorState.ui.cpuDurationSlider.doubleValue);
    monitorState.ui.cpuGraph.setAlphaValue(1.0);
    monitorState.ui.cpuProgress.setMaxValue(Math.max(cpuDuration, 0.001));
    monitorState.ui.cpuProgress.setDoubleValue(cpuDuration);
    monitorState.ui.cpuGraph.setNeedsDisplay(true);
}

function resetWaitProgress() {
    if (!monitorState) {
        return;
    }

    monitorState.waitSeconds = 0;
    monitorState.waitSignalLatched = false;
    monitorState.waitRestartDetail = "";
    monitorState.lastTick = Date.now();
    monitorState.waitWarning = false;
    monitorState.ui.waitProgress.setDoubleValue(0);
    monitorState.ui.waitProgress.setAlphaValue(1.0);
}

function resetAllProgress() {
    if (!monitorState) {
        return;
    }

    resetCPUProgress();
    resetWaitProgress();
    monitorState.pulsePhase = false;
    monitorState.lastPulse = 0;
    monitorState.ui.title.setTextColor($.NSColor.labelColor);
}

function averageCPUAt(samples, endTime, windowSeconds) {
    const startTime = endTime - windowSeconds * 1000;
    let weightedTotal = 0;
    let coveredMilliseconds = 0;

    for (let index = samples.length - 1; index >= 0; index -= 1) {
        const sample = samples[index];
        if (sample.startTime >= endTime) {
            continue;
        }
        if (sample.endTime <= startTime) {
            break;
        }

        const overlapStart = Math.max(sample.startTime, startTime);
        const overlapEnd = Math.min(sample.endTime, endTime);
        const overlapMilliseconds = overlapEnd - overlapStart;
        if (overlapMilliseconds > 0) {
            weightedTotal += sample.percent * overlapMilliseconds;
            coveredMilliseconds += overlapMilliseconds;
        }
    }

    return coveredMilliseconds > 0 ? weightedTotal / coveredMilliseconds : 0;
}

function makeCPUGraphData(samples, endTime, historySeconds, averageWindowSeconds) {
    const effectiveHistorySeconds = Math.max(historySeconds, CPU_SAMPLE_SECONDS);
    const startTime = endTime - effectiveHistorySeconds * 1000;
    const data = [];

    for (const sample of samples) {
        if (sample.endTime <= startTime || sample.startTime >= endTime) {
            continue;
        }

        data.push({
            startTime: Math.max(sample.startTime, startTime),
            endTime: Math.min(sample.endTime, endTime),
            average: averageCPUAt(samples, sample.endTime, averageWindowSeconds)
        });
    }

    return data;
}

function trailingLowDuration(graphData, threshold, endTime) {
    let cursor = endTime;

    for (let index = graphData.length - 1; index >= 0; index -= 1) {
        const segment = graphData[index];
        const maximumGapMilliseconds = CPU_SAMPLE_SECONDS * 2000;

        if (cursor - segment.endTime > maximumGapMilliseconds || segment.average > threshold) {
            break;
        }

        cursor = Math.min(cursor, segment.startTime);
    }

    return Math.max(0, (endTime - cursor) / 1000);
}

function fillRect(color, rect) {
    color.setFill;
    $.NSRectFill(rect);
}

function drawCPUGraph(view) {
    const bounds = view.bounds;
    const width = Number(bounds.size.width);
    const height = Number(bounds.size.height);

    fillRect($.NSColor.textBackgroundColor, bounds);

    if (!monitorState || width <= 0 || height <= 0) {
        return;
    }

    const gridColor = $.NSColor.separatorColor.colorWithAlphaComponent(0.18);
    for (let column = 1; column < 6; column += 1) {
        const x = Math.round(width * column / 6);
        fillRect(gridColor, $.NSMakeRect(x, 0, 1, height));
    }
    for (let row = 1; row < 4; row += 1) {
        const y = Math.round(height * row / 4);
        fillRect(gridColor, $.NSMakeRect(0, y, width, 1));
    }

    const state = monitorState;
    const ui = state.ui;
    const threshold = Number(ui.cpuThresholdSlider.doubleValue);
    const historySeconds = Math.max(Number(ui.cpuDurationSlider.doubleValue), CPU_SAMPLE_SECONDS);
    const graphEndTime = state.graphEndTime || Date.now();
    const graphStartTime = graphEndTime - historySeconds * 1000;
    const graphData = state.cpuGraphData;

    let latestAboveThresholdIndex = -1;
    for (let index = 0; index < graphData.length; index += 1) {
        if (graphData[index].average > threshold) {
            latestAboveThresholdIndex = index;
        }
    }

    let activeColor = null;
    for (let index = 0; index < graphData.length; index += 1) {
        const segment = graphData[index];
        const x = clamp((segment.startTime - graphStartTime) / (historySeconds * 1000) * width, 0, width);
        const nextX = clamp((segment.endTime - graphStartTime) / (historySeconds * 1000) * width, x, width);
        const barWidth = Math.max(1, nextX - x);
        const barHeight = clamp(segment.average / CPU_THRESHOLD_MAX_PERCENT, 0, 1) * height;
        const belowThreshold = segment.average <= threshold;
        const isLatestAboveThreshold = index === latestAboveThresholdIndex;
        const colorName = isLatestAboveThreshold ? "blue" : belowThreshold ? "red" : "green";

        if (colorName !== activeColor) {
            const color = isLatestAboveThreshold
                ? $.NSColor.systemBlueColor
                : belowThreshold
                    ? $.NSColor.systemRedColor
                    : $.NSColor.systemGreenColor;
            color.colorWithAlphaComponent(0.72).setFill;
            activeColor = colorName;
        }

        if (barHeight > 0) {
            $.NSRectFill($.NSMakeRect(x, 0, barWidth, Math.max(1, barHeight)));
        }
    }

    const thresholdY = clamp(
        threshold / CPU_THRESHOLD_MAX_PERCENT * height,
        0,
        Math.max(0, height - 2)
    );
    fillRect($.NSColor.systemOrangeColor, $.NSMakeRect(0, thresholdY, width, 2));

    const borderColor = $.NSColor.separatorColor;
    fillRect(borderColor, $.NSMakeRect(0, 0, width, 1));
    fillRect(borderColor, $.NSMakeRect(0, Math.max(0, height - 1), width, 1));
    fillRect(borderColor, $.NSMakeRect(0, 0, 1, height));
    fillRect(borderColor, $.NSMakeRect(Math.max(0, width - 1), 0, 1, height));
}

function cpuSignalIsEnabled() {
    return Boolean(
        monitorState &&
        Number(monitorState.ui.cpuActiveButton.state) === Number($.NSControlStateValueOn)
    );
}

function waitSignalIsEnabled() {
    return Boolean(
        monitorState &&
        Number(monitorState.ui.waitActiveButton.state) === Number($.NSControlStateValueOn)
    );
}

function weightedPromptRowIndex(eligibleIndexes, randomValue) {
    if (eligibleIndexes.length === 0) {
        return null;
    }
    const totalWeight = eligibleIndexes.reduce(
        (total, index) => total + Math.max(0, Number(promptRows[index].slider.doubleValue)),
        0
    );
    if (totalWeight <= 0) {
        return null;
    }
    const boundedRandom = clamp(Number(randomValue), 0, 0.9999999999999999);
    const target = boundedRandom * totalWeight;
    let cumulativeWeight = 0;
    for (const index of eligibleIndexes) {
        cumulativeWeight += Math.max(0, Number(promptRows[index].slider.doubleValue));
        if (target < cumulativeWeight) {
            return index;
        }
    }
    return eligibleIndexes[eligibleIndexes.length - 1];
}

function promptRollDwellMilliseconds(weightPercent, progress, eligibleCount) {
    const normalizedProgress = clamp(progress, 0, 1);
    const deceleratingBase = 70 + 360 * Math.pow(normalizedProgress, 2.2);
    const proportionalFactor = Math.max(0, Number(weightPercent)) / 100 *
        Math.max(1, eligibleCount);
    return Math.max(
        PROMPT_ROLL_MIN_DWELL_MILLISECONDS,
        deceleratingBase * proportionalFactor
    );
}

function eligiblePromptIndexesForAnimation() {
    return promptRows
        .map((row, index) =>
            row.eligible && Number(row.slider.doubleValue) > 0 ? index : -1
        )
        .filter(index => index >= 0);
}

function signalSourceColor(source) {
    return source === "cpu"
        ? $.NSColor.systemOrangeColor
        : source === "wait" ? $.NSColor.systemBlueColor : $.NSColor.systemPurpleColor;
}

function signalConnectorPath(source) {
    const path = $.NSBezierPath.bezierPath;
    path.setLineCapStyle($.NSLineCapStyleRound);
    path.setLineJoinStyle($.NSLineJoinStyleRound);
    if (source === "cpu") {
        path.moveToPoint($.NSMakePoint(738, 520));
        path.curveToPointControlPoint1ControlPoint2(
            $.NSMakePoint(762, 540),
            $.NSMakePoint(750, 520),
            $.NSMakePoint(750, 540)
        );
    } else {
        path.moveToPoint($.NSMakePoint(738, 100));
        path.lineToPoint($.NSMakePoint(744, 100));
        path.curveToPointControlPoint1ControlPoint2(
            $.NSMakePoint(750, 106),
            $.NSMakePoint(748, 100),
            $.NSMakePoint(750, 102)
        );
        path.lineToPoint($.NSMakePoint(750, 434));
        path.curveToPointControlPoint1ControlPoint2(
            $.NSMakePoint(756, 440),
            $.NSMakePoint(750, 438),
            $.NSMakePoint(752, 440)
        );
        path.lineToPoint($.NSMakePoint(762, 440));
    }
    return path;
}

function drawSignalConnectors() {
    for (const source of ["cpu"]) {
        const highlighted = Boolean(signalAnimation && signalAnimation.source === source);
        let alpha = highlighted ? 0.88 : 0.42;
        if (highlighted && signalAnimation.phase === "edge") {
            const elapsed = Date.now() - signalAnimation.startedAt;
            alpha = 0.55 + 0.4 * Math.abs(Math.sin(elapsed / 90));
        }
        const color = highlighted
            ? signalSourceColor(source).colorWithAlphaComponent(alpha)
            : $.NSColor.separatorColor.colorWithAlphaComponent(alpha);
        color.setStroke;
        const path = signalConnectorPath(source);
        path.setLineWidth(highlighted ? 5 : 3);
        path.stroke;
    }
}

function updateSignalAnimationControls() {
    if (!monitorState) {
        return;
    }
    const ui = monitorState.ui;
    const active = Boolean(signalAnimation);
    const clientRestarting = Boolean(perplexityRestart);
    ui.cpuActiveButton.setEnabled(!active);
    ui.waitActiveButton.setEnabled(!active);
    ui.promptInjectButton.setEnabled(
        !active && !clientRestarting && !runnerTaskIsRunning()
    );
    ui.signalCancellationOverlay.setHidden(!active);
    for (const row of promptRows) {
        row.textField.setEnabled(!active);
        row.slider.setEnabled(!active && row.eligible);
        row.slider.setAlphaValue(row.eligible ? (active ? 0.5 : 1.0) : 0.4);
    }
    ui.configurationSaveButton.setEnabled(
        !active && !clientRestarting && !runnerTaskIsRunning()
    );
    ui.configurationMenu.setEnabled(
        !active && !clientRestarting && !runnerTaskIsRunning()
    );
}

function updateSignalAnimationVisuals() {
    if (!monitorState) {
        return;
    }
    const ui = monitorState.ui;
    const rolling = Boolean(signalAnimation && signalAnimation.phase === "rolling");
    ui.promptCard.setBorderWidth(rolling ? 3 : 1);
    ui.promptCard.setBorderColor(
        rolling
            ? signalSourceColor(signalAnimation.source).colorWithAlphaComponent(0.9)
            : $.NSColor.separatorColor.colorWithAlphaComponent(0.55)
    );
    for (let index = 0; index < promptRows.length; index += 1) {
        const row = promptRows[index];
        const highlighted = rolling && signalAnimation.highlightedRowIndex === index;
        const sourceColor = rolling
            ? signalSourceColor(signalAnimation.source)
            : $.NSColor.clearColor;
        row.highlightView.setBorderWidth(highlighted ? 2 : 0);
        row.highlightView.setBorderColor(
            highlighted ? sourceColor.colorWithAlphaComponent(0.95) : $.NSColor.clearColor
        );
        row.highlightView.setFillColor(
            highlighted ? sourceColor.colorWithAlphaComponent(0.34) : $.NSColor.clearColor
        );
        row.highlightView.setNeedsDisplay(true);
        row.textField.setBackgroundColor(
            highlighted
                ? sourceColor.colorWithAlphaComponent(0.48)
                : $.NSColor.textBackgroundColor
        );
        row.textField.setAlphaValue(rolling ? (highlighted ? 1.0 : 0.5) : 1.0);
        row.slider.setAlphaValue(
            rolling
                ? (highlighted ? 1.0 : 0.28)
                : row.eligible ? (signalAnimation ? 0.5 : 1.0) : 0.4
        );
        row.valueLabel.setAlphaValue(
            rolling ? (highlighted ? 1.0 : 0.38) : row.eligible ? 1.0 : 0.4
        );
        row.valueLabel.setTextColor(
            highlighted ? sourceColor : $.NSColor.labelColor
        );
    }
    ui.signalConnectorView.setNeedsDisplay(true);
}

function startPromptRoll(now) {
    if (!signalAnimation) {
        return;
    }
    const eligibleIndexes = eligiblePromptIndexesForAnimation();
    signalAnimation.phase = "rolling";
    signalAnimation.rollStartedAt = now;
    signalAnimation.rollEndsAt = now + PROMPT_ROLL_MILLISECONDS;
    signalAnimation.settleStartsAt = signalAnimation.rollEndsAt -
        PROMPT_ROLL_SETTLE_MILLISECONDS;
    signalAnimation.eligibleIndexes = eligibleIndexes;
    signalAnimation.selectedRowIndex = weightedPromptRowIndex(
        eligibleIndexes,
        Math.random()
    );
    signalAnimation.settling = false;
    signalAnimation.rollPosition = eligibleIndexes.length > 0
        ? Math.floor(Math.random() * eligibleIndexes.length)
        : -1;
    signalAnimation.highlightedRowIndex = signalAnimation.rollPosition >= 0
        ? eligibleIndexes[signalAnimation.rollPosition]
        : null;
    if (signalAnimation.highlightedRowIndex !== null) {
        const row = promptRows[signalAnimation.highlightedRowIndex];
        signalAnimation.nextStepAt = now + promptRollDwellMilliseconds(
            Number(row.slider.doubleValue),
            0,
            eligibleIndexes.length
        );
    } else {
        signalAnimation.nextStepAt = signalAnimation.rollEndsAt;
    }
    updateSignalAnimationVisuals();
}

function clearSignalAnimation(sendSelectedPrompt) {
    if (!signalAnimation) {
        return;
    }
    const selectedRowIndex = signalAnimation.selectedRowIndex;
    const rawPrompt = selectedRowIndex === null || selectedRowIndex === undefined
        ? "Read AGENTS.md and keep going."
        : stringValue(promptRows[selectedRowIndex].textField);
    try {
        if (sendSelectedPrompt) {
            sendPrompt(rawPrompt);
        }
    } finally {
        signalAnimation = null;
        updateSignalAnimationVisuals();
        updateSignalAnimationControls();
        resetCPUProgress();
        monitorState.pulsePhase = false;
        monitorState.lastPulse = 0;
        monitorState.ui.title.setTextColor($.NSColor.labelColor);
        updateRunnerUI(Date.now());
    }
}

function cancelSignalAnimation() {
    clearSignalAnimation(false);
}

function startManualPromptAnimation(now) {
    if (signalAnimation || perplexityRestart || runnerTaskIsRunning()) {
        return false;
    }
    if (runnerOutputIsVisible()) {
        setRunnerOutputVisible(false);
    }
    signalAnimation = {
        source: "manual",
        phase: "rolling",
        startedAt: now,
        highlightedRowIndex: null
    };
    monitorState.cpuWarning = false;
    monitorState.waitWarning = false;
    updateSignalAnimationControls();
    startPromptRoll(now);
    updateRunnerUI(now);
    return true;
}

function startSignalAnimation(source, now) {
    if (signalAnimation || perplexityRestart || runnerTaskIsRunning()) {
        return false;
    }
    if (runnerOutputIsVisible()) {
        setRunnerOutputVisible(false);
    }
    signalAnimation = {
        source,
        phase: "edge",
        startedAt: now,
        edgeEndsAt: now + SIGNAL_EDGE_PULSE_MILLISECONDS,
        highlightedRowIndex: null
    };
    monitorState.cpuWarning = false;
    monitorState.waitWarning = false;
    updateSignalAnimationControls();
    updateSignalAnimationVisuals();
    updateRunnerUI(now);
    return true;
}

function updateSignalAnimation(now) {
    if (!signalAnimation) {
        return;
    }
    if (signalAnimation.phase === "edge") {
        if (now >= signalAnimation.edgeEndsAt) {
            startPromptRoll(now);
        }
    } else if (signalAnimation.phase === "rolling") {
        if (now >= signalAnimation.settleStartsAt) {
            signalAnimation.settling = true;
            signalAnimation.highlightedRowIndex = signalAnimation.selectedRowIndex;
        } else {
            let steps = 0;
            while (signalAnimation && now >= signalAnimation.nextStepAt &&
                signalAnimation.nextStepAt < signalAnimation.settleStartsAt &&
                steps < 100) {
                signalAnimation.rollPosition = (
                    signalAnimation.rollPosition + 1
                ) % signalAnimation.eligibleIndexes.length;
                signalAnimation.highlightedRowIndex =
                    signalAnimation.eligibleIndexes[signalAnimation.rollPosition];
                const progress = (now - signalAnimation.rollStartedAt) /
                    PROMPT_ROLL_MILLISECONDS;
                const row = promptRows[signalAnimation.highlightedRowIndex];
                signalAnimation.nextStepAt += promptRollDwellMilliseconds(
                    Number(row.slider.doubleValue),
                    progress,
                    signalAnimation.eligibleIndexes.length
                );
                steps += 1;
            }
        }
        updateSignalAnimationVisuals();
        if (signalAnimation && now >= signalAnimation.rollEndsAt) {
            clearSignalAnimation(true);
            return;
        }
    }
    if (signalAnimation) {
        monitorState.ui.signalConnectorView.setNeedsDisplay(true);
    }
}

function monitorTick() {
    if (!monitorState) {
        return;
    }

    const state = monitorState;
    const ui = state.ui;
    const now = Date.now();
    const mouseButtonIsReleased = Number($.NSEvent.pressedMouseButtons) === 0;
    if (mouseButtonIsReleased) {
        promptWeightGestureSnapshot = null;
    }

    runnerTick(now);
    updatePerplexityClientRestart(now);
    updateRunnerUI(now);

    if (deliverPendingRunnerPrompt(now, mouseButtonIsReleased)) {
        return;
    }

    const elapsed = (now - state.lastTick) / 1000;
    state.lastTick = now;

    const cpuEnabled = cpuSignalIsEnabled();
    const waitEnabled = waitSignalIsEnabled();
    const cpuThreshold = Number(ui.cpuThresholdSlider.doubleValue);
    const cpuDuration = Number(ui.cpuDurationSlider.doubleValue);
    const averageWindow = Number(ui.averageWindowSlider.doubleValue);
    const waitTimeout = Number(ui.waitSlider.doubleValue);

    if (now - state.lastCPUSample >= CPU_SAMPLE_SECONDS * 1000) {
        const sample = sampleCPUPercent();
        state.lastCPUSample = now;

        if (sample) {
            state.currentRawCPU = sample.percent;
            state.cpuSamples.push(sample);

            const historyCutoff = now - (
                CPU_TIMEOUT_MAX_SECONDS + AVERAGE_WINDOW_MAX_SECONDS + 2
            ) * 1000;
            while (state.cpuSamples.length > 0 && state.cpuSamples[0].endTime < historyCutoff) {
                state.cpuSamples.shift();
            }
        }
    }

    const latestSample = state.cpuSamples.length > 0
        ? state.cpuSamples[state.cpuSamples.length - 1]
        : null;
    state.graphEndTime = latestSample ? latestSample.endTime : now;
    state.cpuGraphData = makeCPUGraphData(
        state.cpuSamples,
        state.graphEndTime,
        cpuDuration,
        averageWindow
    );
    state.currentAverageCPU = latestSample
        ? averageCPUAt(state.cpuSamples, latestSample.endTime, averageWindow)
        : 0;
    if (waitEnabled) {
        state.waitSeconds += elapsed;
    } else {
        state.waitSeconds = 0;
    }

    const hasCPUData = state.cpuGraphData.length > 0;
    const currentCPUIsLow = hasCPUData && state.currentAverageCPU <= cpuThreshold;
    if (cpuEnabled && currentCPUIsLow) {
        state.trailingLowCPUSeconds += elapsed;
    } else {
        state.trailingLowCPUSeconds = 0;
    }
    const cpuFired = cpuEnabled && currentCPUIsLow &&
        state.trailingLowCPUSeconds >= cpuDuration;
    const cpuWarningStart = Math.max(0, cpuDuration - WARNING_SECONDS);
    state.cpuWarning = cpuEnabled && !signalAnimation && currentCPUIsLow &&
        state.trailingLowCPUSeconds >= cpuWarningStart;

    const waitFired = waitEnabled && !state.waitSignalLatched &&
        state.waitSeconds >= waitTimeout;
    state.waitWarning = waitEnabled && !state.waitSignalLatched &&
        !signalAnimation && !perplexityRestart &&
        state.waitSeconds >= Math.max(0, waitTimeout - WARNING_SECONDS);

    const cpuRemainingSeconds = cpuEnabled
        ? Math.max(0, cpuDuration - state.trailingLowCPUSeconds)
        : cpuDuration;
    ui.cpuProgress.setMaxValue(Math.max(cpuDuration, 0.001));
    ui.cpuProgress.setDoubleValue(cpuRemainingSeconds);
    ui.waitProgress.setDoubleValue(
        waitEnabled ? Math.min(state.waitSeconds, WAIT_TIMEOUT_MAX_SECONDS) : 0
    );

    const cpuCondition = !cpuEnabled
        ? "DISABLED"
        : signalAnimation && signalAnimation.source === "cpu"
            ? "SIGNALING"
            : cpuFired
                ? "ACTIVE"
                : state.cpuWarning ? "APPROACHING" : "MONITORING";
    ui.graphStatus.setStringValue(
        `RAW ${state.currentRawCPU.toFixed(4)}%    AVG ${state.currentAverageCPU.toFixed(4)}%    THRESHOLD ${cpuThreshold.toFixed(3)}%    ${cpuCondition}`
    );
    ui.averageWindowValue.setStringValue(`${averageWindow.toFixed(1)} s`);
    ui.cpuDurationValue.setStringValue(`${cpuDuration.toFixed(1)} s`);
    ui.cpuProgressValue.setStringValue(
        cpuEnabled
            ? `${cpuRemainingSeconds.toFixed(1)} s remaining  ·  ${state.trailingLowCPUSeconds.toFixed(1)} s qualified`
            : "DISABLED · use the toggle switch to begin monitoring"
    );
    ui.waitValue.setStringValue(
        waitEnabled
            ? `${state.waitSeconds.toFixed(1)} s / ${waitTimeout.toFixed(1)} s` +
                (state.waitRestartDetail ? ` · ${state.waitRestartDetail}` : "")
            : `DISABLED  ·  threshold ${waitTimeout.toFixed(1)} s`
    );
    ui.waitValue.setToolTip(state.waitRestartDetail || "");

    if (state.waitWarning && now - state.lastPulse >= PULSE_INTERVAL_MILLISECONDS) {
        state.pulsePhase = !state.pulsePhase;
        state.lastPulse = now;
    } else if (!state.waitWarning) {
        state.pulsePhase = false;
    }

    ui.cpuGraph.setAlphaValue(1.0);
    ui.waitProgress.setAlphaValue(state.waitWarning && state.pulsePhase ? 0.35 : 1.0);
    ui.cpuGraph.setNeedsDisplay(true);

    if (signalAnimation) {
        updateSignalAnimation(now);
        return;
    }
    if (perplexityRestart) {
        return;
    }
    if (!runnerTaskIsRunning() && mouseButtonIsReleased && waitFired) {
        ui.cpuGraph.setAlphaValue(1.0);
        ui.waitProgress.setAlphaValue(1.0);
        startPerplexityClientRestart(now);
    } else if (!runnerTaskIsRunning() && mouseButtonIsReleased && cpuFired) {
        ui.cpuGraph.setAlphaValue(1.0);
        ui.waitProgress.setAlphaValue(1.0);
        startSignalAnimation("cpu", now);
    }
}

ObjC.registerSubclass({
    name: "MonitorController",
    protocols: ["NSWindowDelegate", "NSTextFieldDelegate"],
    methods: {
        "tick:": {
            types: ["void", ["id"]],
            implementation: function () {
                monitorTick();
            }
        },
        "saveConfiguration:": {
            types: ["void", ["id"]],
            implementation: function () {
                configurationSaveTimer = null;
                flushConfiguration(false);
            }
        },
        "configurationChanged:": {
            types: ["void", ["id"]],
            implementation: function () {
                scheduleConfigurationSave();
            }
        },
        "saveConfigurationNow:": {
            types: ["void", ["id"]],
            implementation: function () {
                if (!saveConfigurationNow()) {
                    showConfigurationSaveFailure();
                }
            }
        },

        "loadSavedConfiguration:": {
            types: ["void", ["id"]],
            implementation: function () {
                loadSavedConfiguration();
            }
        },
        "resetDefaultConfiguration:": {
            types: ["void", ["id"]],
            implementation: function () {
                resetDefaultConfiguration();
            }
        },
        "cpuSignalActiveChanged:": {
            types: ["void", ["id"]],
            implementation: function () {
                monitorState.cpuWarning = false;
                monitorState.ui.cpuGraph.setAlphaValue(1.0);
                scheduleConfigurationSave();
                monitorTick();
            }
        },
        "waitSignalActiveChanged:": {
            types: ["void", ["id"]],
            implementation: function () {
                resetWaitProgress();
                scheduleConfigurationSave();
                monitorTick();
            }
        },

        "controlTextDidChange:": {
            types: ["void", ["id"]],
            implementation: function (notification) {
                const tag = Number(notification.object.tag);
                if (tag >= PROMPT_TEXT_TAG_BASE &&
                    tag < PROMPT_TEXT_TAG_BASE + promptRows.length) {
                    promptTextChanged(tag - PROMPT_TEXT_TAG_BASE);
                } else {
                    scheduleConfigurationSave();
                }
            }
        },
        "resetWaitButton:": {
            types: ["void", ["id"]],
            implementation: function () {
                resetWaitProgress();
            }
        },
        "resetWait:": {
            types: ["void", ["id"]],
            implementation: function (recognizer) {
                const slider = recognizer.view;
                const point = recognizer.locationInView(slider);
                const width = Number(slider.bounds.size.width);
                const knobRadius = 10;
                const timeout = Number(slider.doubleValue);
                const knobCenterX = knobRadius +
                    timeout / WAIT_TIMEOUT_MAX_SECONDS * Math.max(0, width - knobRadius * 2);
                const knobLeftX = knobCenterX - knobRadius;

                if (Number(point.x) < knobLeftX) {
                    resetWaitProgress();
                }
            }
        },
        "promptWeightChanged:": {
            types: ["void", ["id"]],
            implementation: function (sender) {
                rebalancePromptWeights(Number(sender.tag), Number(sender.doubleValue));
            }
        },
        "promptInjectNow:": {
            types: ["void", ["id"]],
            implementation: function () {
                startManualPromptAnimation(Date.now());
            }
        },
        "runnerSelfTest:": {
            types: ["void", ["id"]],
            implementation: function () {
                startRunnerSelfTest();
            }
        },
        "runnerChoose:": {
            types: ["void", ["id"]],
            implementation: function () {
                if (runnerOperationInProgress() || perplexityRestart) {
                    return;
                }

                const panel = $.NSSavePanel.savePanel;
                panel.setTitle("Select run script path");
                panel.setMessage(
                    "Choose the run.sh path to watch. The file may already exist or may be created later; this dialog only selects a path and does not write it."
                );
                panel.setPrompt("Select Path");
                panel.setNameFieldLabel("Script:");
                panel.setNameFieldStringValue(runnerScriptName());
                panel.setCanCreateDirectories(true);
                panel.setDirectoryURL($.NSURL.fileURLWithPath(runnerRootDirectory()));
                if (Number(panel.runModal) !== Number($.NSModalResponseOK)) {
                    return;
                }

                runnerSelectedScriptPath = String(ObjC.unwrap(
                    panel.URL.path.stringByStandardizingPath
                ));
                refreshRunnerPresence(Date.now(), true);
                runnerAutoTriggeredForPresence = false;
                runnerSelfTestStatus = "unverified";
                runnerValidatedConfiguration = null;
                disableAutoModeForExistingRunScript(monitorState.ui, true);
                runnerStatusDetail = runnerPathDirectoryAvailable
                    ? "Run script path changed; environment self-test required."
                    : `Project directory does not exist: ${runnerRootDirectory()}.`;
                scheduleConfigurationSave();
                updateRunnerUI(Date.now());
            }
        },
        "runnerAuto:": {
            types: ["void", ["id"]],
            implementation: function () {
                if (orphanedRunner) {
                    disableRunnerAutoMode(monitorState.ui);
                    return;
                }
                runnerAutoTriggeredForPresence = false;
                refreshRunnerPresence(Date.now(), true);
                if (!runnerAutoModeEnabled()) {
                    disableSignalSources(monitorState.ui);
                } else if (runnerReady && runnerExecutionAllowed()) {
                    startOneShotRunner();
                }
                scheduleConfigurationSave();
                monitorTick();
            }
        },
        "runnerShowOutput:": {
            types: ["void", ["id"]],
            implementation: function () {
                toggleRunnerOutput();
            }
        },
        "runnerHideOutput:": {
            types: ["void", ["id"]],
            implementation: function () {
                setRunnerOutputVisible(false);
            }
        },
        "runnerLED:": {
            types: ["void", ["id"]],
            implementation: function () {
                const state = runnerDisplayState();
                if (state === "sentinel") {
                    const removeSucceeded = Boolean(
                        $.NSFileManager.defaultManager.removeItemAtPathError(
                            runnerSelectedScriptPath,
                            undefined
                        )
                    );
                    const previousSentinel = activePromptSentinel;
                    try {
                        activePromptSentinel = generateRandomPromptSentinel();
                    } catch (error) {
                        activePromptSentinel = previousSentinel;
                    }
                    runnerSentinelDetected = false;
                    runnerLEDHovering = false;
                    runnerReady = false;
                    runnerExistingScriptNotice = false;
                    runnerStatusDetail = removeSucceeded
                        ? `Sentinel ${runnerScriptName()} deleted and sentinel token rotated.`
                        : `Failed to delete sentinel ${runnerScriptName()}, but sentinel token was rotated.`;
                    scheduleConfigurationSave();
                    monitorTick();
                } else if (state === "running") {
                    requestRunnerStop(true);
                } else if (state === "orphaned" || state === "orphan recovery") {
                    requestOrphanedRunnerStop();
                } else if (state === "ready") {
                    startOneShotRunner();
                }
            }
        },
        "runnerSandboxChanged:": {
            types: ["void", ["id"]],
            implementation: function () {
                if (runnerOperationInProgress() || perplexityRestart) {
                    return;
                }
                runnerAutoTriggeredForPresence = false;
                scheduleConfigurationSave();
                runnerSelfTestStatus = "unverified";
                runnerValidatedConfiguration = null;
                runnerStatusDetail = sandboxIsEnabled()
                    ? "Sandbox enabled; environment self-test required."
                    : "Sandbox disabled; execution is available without self-test.";
                updateRunnerUI(Date.now());
            }
        },
        "windowShouldClose:": {
            types: ["bool", ["id"]],
            implementation: function () {
                return !Boolean(perplexityRestart);
            }
        },
        "windowWillClose:": {
            types: ["void", ["id"]],
            implementation: function () {
                if (signalAnimation) {
                    cancelSignalAnimation();
                }
                flushConfiguration(true);
                if (runnerTaskIsRunning()) {
                    const pid = Number(runnerTask.processIdentifier);
                    signalRunnerProcessGroup(pid, 15);
                }
                if (monitorTimer) {
                    monitorTimer.invalidate;
                }
                $.NSFileManager.defaultManager.removeItemAtPathError(
                    RUNNER_OUTPUT_PATH,
                    undefined
                );
                $.NSApplication.sharedApplication.terminate(null);
            }
        }
    }
});


function graphThresholdForY(y, height) {
    const ratio = height > 0 ? clamp(Number(y) / Number(height), 0, 1) : 0;
    return CPU_THRESHOLD_MIN_PERCENT +
        ratio * (CPU_THRESHOLD_MAX_PERCENT - CPU_THRESHOLD_MIN_PERCENT);
}

function graphWindowForHorizontalDelta(deltaX, width, initialWindow) {
    const range = AVERAGE_WINDOW_MAX_SECONDS - AVERAGE_WINDOW_MIN_SECONDS;
    const adjustment = width > 0 ? Number(deltaX) / Number(width) * range : 0;
    return clamp(
        Number(initialWindow) + adjustment,
        AVERAGE_WINDOW_MIN_SECONDS,
        AVERAGE_WINDOW_MAX_SECONDS
    );
}

function graphEventPoint(view, event) {
    const point = view.convertPointFromView(event.locationInWindow, undefined);
    return { x: Number(point.x), y: Number(point.y) };
}

function injectSyntheticThresholdSample() {
    if (!monitorState) {
        return;
    }
    const state = monitorState;
    const threshold = Number(state.ui.cpuThresholdSlider.doubleValue);
    const endTime = Date.now();
    const nominalStartTime = endTime - CPU_SAMPLE_SECONDS * 1000;
    const lastSample = state.cpuSamples.length > 0
        ? state.cpuSamples[state.cpuSamples.length - 1]
        : null;
    const previousEndTime = lastSample
        ? Math.min(Number(lastSample.endTime), endTime - 1)
        : nominalStartTime;
    state.cpuSamples.push({
        startTime: Math.max(nominalStartTime, previousEndTime),
        endTime,
        percent: threshold
    });
    state.currentRawCPU = threshold;
    state.graphEndTime = endTime;
    state.lastCPUSample = endTime;
    const duration = Number(state.ui.cpuDurationSlider.doubleValue);
    const smoothing = Number(state.ui.averageWindowSlider.doubleValue);
    state.cpuGraphData = makeCPUGraphData(
        state.cpuSamples,
        endTime,
        duration,
        smoothing
    );
    state.currentAverageCPU = averageCPUAt(state.cpuSamples, endTime, smoothing);
    state.trailingLowCPUSeconds = trailingLowDuration(
        state.cpuGraphData,
        threshold,
        endTime
    );
    state.ui.cpuGraph.setNeedsDisplay(true);
}

function updateGraphDrag(view, point) {
    if (!monitorState || !graphGestureMode) {
        return;
    }
    const width = Number(view.bounds.size.width);
    const height = Number(view.bounds.size.height);
    if (graphGestureMode === "threshold") {
        const threshold = graphThresholdForY(point.y, height);
        monitorState.ui.cpuThresholdSlider.setDoubleValue(threshold);
        monitorState.ui.graphStatus.setStringValue(
            `RAW ${monitorState.currentRawCPU.toFixed(4)}%    AVG ${monitorState.currentAverageCPU.toFixed(4)}%    THRESHOLD ${threshold.toFixed(3)}%    ${cpuSignalIsEnabled() ? "ADJUSTING" : "DISABLED"}`
        );
    } else {
        const smoothing = graphWindowForHorizontalDelta(
            point.x - graphClickStart.x,
            width,
            graphClickStart.smoothingWindowSeconds
        );
        monitorState.ui.averageWindowSlider.setDoubleValue(smoothing);
        monitorState.ui.averageWindowValue.setStringValue(`${smoothing.toFixed(1)} s`);
    }
    monitorState.ui.cpuGraph.setNeedsDisplay(true);
    scheduleConfigurationSave();
}

ObjC.registerSubclass({
    name: "CPUGraphView",
    superclass: "NSView",
    methods: {
        "drawRect:": {
            implementation: function () {
                drawCPUGraph(this);
            }
        },
        "mouseDown:": {
            types: ["void", ["id"]],
            implementation: function (event) {
                graphClickStart = graphEventPoint(this, event);
                graphClickStart.smoothingWindowSeconds = Number(
                    monitorState.ui.averageWindowSlider.doubleValue
                );
                graphGestureMode = null;
            }
        },
        "mouseDragged:": {
            types: ["void", ["id"]],
            implementation: function (event) {
                if (!graphClickStart) {
                    return;
                }
                const point = graphEventPoint(this, event);
                const deltaX = point.x - graphClickStart.x;
                const deltaY = point.y - graphClickStart.y;
                if (!graphGestureMode && Math.sqrt(deltaX * deltaX + deltaY * deltaY) > 3) {
                    graphGestureMode = Math.abs(deltaY) >= Math.abs(deltaX)
                        ? "threshold"
                        : "smoothing";
                }
                updateGraphDrag(this, point);
            }
        },
        "mouseUp:": {
            types: ["void", ["id"]],
            implementation: function (event) {
                if (graphClickStart && graphGestureMode) {
                    updateGraphDrag(this, graphEventPoint(this, event));
                } else if (graphClickStart) {
                    injectSyntheticThresholdSample();
                }
                graphClickStart = null;
                graphGestureMode = null;
            }
        },
        "scrollWheel:": {
            types: ["void", ["id"]],
            implementation: function (event) {
                if (!monitorState) {
                    return;
                }
                const deltaX = Number(event.scrollingDeltaX);
                const deltaY = Number(event.scrollingDeltaY);
                const momentumPhase = Number(event.momentumPhase);
                if (momentumPhase !== 0 ||
                    Math.abs(deltaX) <= Math.abs(deltaY) || deltaX === 0) {
                    return;
                }
                const normalizedDeltaX = Boolean(event.hasPreciseScrollingDeltas)
                    ? deltaX
                    : deltaX * 12;
                const smoothing = graphWindowForHorizontalDelta(
                    normalizedDeltaX,
                    Number(this.bounds.size.width),
                    Number(monitorState.ui.averageWindowSlider.doubleValue)
                );
                monitorState.ui.averageWindowSlider.setDoubleValue(smoothing);
                monitorState.ui.averageWindowValue.setStringValue(`${smoothing.toFixed(1)} s`);
                this.setNeedsDisplay(true);
                scheduleConfigurationSave();
            }
        }
    }
});

ObjC.registerSubclass({
    name: "SignalConnectorView",
    superclass: "NSView",
    methods: {
        "drawRect:": {
            implementation: function () {
                drawSignalConnectors();
            }
        },
        "hitTest:": {
            implementation: function () {
                return undefined;
            }
        }
    }
});

ObjC.registerSubclass({
    name: "SignalCancellationOverlay",
    superclass: "NSView",
    methods: {
        "mouseDown:": {
            types: ["void", ["id"]],
            implementation: function () {
                cancelSignalAnimation();
            }
        }
    }
});

ObjC.registerSubclass({
    name: "RunnerStatusButton",
    superclass: "NSButton",
    methods: {
        "updateTrackingAreas": {
            types: ["void", []],
            implementation: function () {
                // Note: JXA's ObjC.registerSubclass does not expose a
                // working "this.super" — calling this.super.updateTrackingAreas()
                // throws "TypeError: undefined is not an object
                // (evaluating 'this.super.updateTrackingAreas')" (-2700).
                // NSButton's default tracking-area setup is not needed here;
                // we only need to (re)install our own tracking area below.
                if (!this.__runnerTrackingArea) {
                    const options = $.NSTrackingMouseEnteredAndExited |
                        $.NSTrackingActiveInKeyWindow |
                        $.NSTrackingInVisibleRect;
                    this.__runnerTrackingArea = $.NSTrackingArea.alloc
                        .initWithRectOptionsOwnerUserInfo($.NSZeroRect, options, this, null);
                    this.addTrackingArea(this.__runnerTrackingArea);
                }
            }
        },
        "mouseEntered:": {
            types: ["void", ["id"]],
            implementation: function () {
                if (runnerDisplayState() === "sentinel") {
                    runnerLEDHovering = true;
                    updateRunnerUI(Date.now());
                }
            }
        },
        "mouseExited:": {
            types: ["void", ["id"]],
            implementation: function () {
                if (runnerLEDHovering) {
                    runnerLEDHovering = false;
                    updateRunnerUI(Date.now());
                }
            }
        }
    }
});

function byteAt(pointer, offset) {
    return Number(pointer[offset]) & 0xff;
}

function uint32At(pointer, offset) {
    return byteAt(pointer, offset) +
        byteAt(pointer, offset + 1) * 0x100 +
        byteAt(pointer, offset + 2) * 0x10000 +
        byteAt(pointer, offset + 3) * 0x1000000;
}

function uint64At(pointer, offset) {
    const low = uint32At(pointer, offset);
    const high = uint32At(pointer, offset + UINT32_SIZE);
    return high * 0x100000000 + low;
}

function stringAt(pointer, length) {
    let result = "";
    for (let index = 0; index < length; index += 1) {
        const byte = byteAt(pointer, index);
        if (byte === 0) {
            break;
        }
        result += String.fromCharCode(byte);
    }
    return result;
}

function refreshMatchingProcessPids(sampleTime) {
    if (sampleTime - lastPIDRefreshTime < PID_REFRESH_SECONDS * 1000) {
        return;
    }

    const estimatedCount = Number($.proc_listallpids(null, 0));
    const bufferSize = Math.max(estimatedCount + 128, 128) * UINT32_SIZE;
    const pidBuffer = $.malloc(bufferSize);
    const nameBuffer = $.malloc(PROCESS_NAME_BUFFER_SIZE);
    const result = [];

    try {
        const pidCount = Number($.proc_listallpids(pidBuffer, bufferSize));
        for (let index = 0; index < pidCount; index += 1) {
            const pid = uint32At(pidBuffer, index * UINT32_SIZE);
            if (pid === 0) {
                continue;
            }

            const nameLength = Number($.proc_name(pid, nameBuffer, PROCESS_NAME_BUFFER_SIZE));
            if (nameLength > 0 && stringAt(nameBuffer, nameLength) === PROCESS_NAME) {
                result.push(pid);
            }
        }
    } finally {
        $.free(nameBuffer);
        $.free(pidBuffer);
    }

    matchingProcessPids = result;
    lastPIDRefreshTime = sampleTime;
}

function processCPUTimes(sampleTime) {
    refreshMatchingProcessPids(sampleTime);

    const usageBuffer = $.malloc(RUSAGE_BUFFER_SIZE);
    const result = {};

    try {
        for (const pid of matchingProcessPids) {
            if (Number($.proc_pid_rusage(pid, RUSAGE_INFO_V2, usageBuffer)) !== 0) {
                continue;
            }

            const userNanoseconds = uint64At(usageBuffer, 16);
            const systemNanoseconds = uint64At(usageBuffer, 24);
            result[String(pid)] = userNanoseconds + systemNanoseconds;
        }
    } finally {
        $.free(usageBuffer);
    }

    return result;
}

function sampleCPUPercent() {
    const sampleTime = Date.now();
    const processTimes = processCPUTimes(sampleTime);

    if (previousCPUSampleTime === null) {
        previousProcessCPUTimes = processTimes;
        previousCPUSampleTime = sampleTime;
        return null;
    }

    const startTime = previousCPUSampleTime;
    const elapsedNanoseconds = (sampleTime - startTime) * 1000000;
    let consumedNanoseconds = 0;

    for (const pid in processTimes) {
        if (!Object.prototype.hasOwnProperty.call(processTimes, pid) ||
            !Object.prototype.hasOwnProperty.call(previousProcessCPUTimes, pid)) {
            continue;
        }

        const delta = processTimes[pid] - previousProcessCPUTimes[pid];
        if (delta > 0) {
            consumedNanoseconds += delta;
        }
    }

    previousProcessCPUTimes = processTimes;
    previousCPUSampleTime = sampleTime;

    if (elapsedNanoseconds <= 0) {
        return null;
    }

    return {
        startTime,
        endTime: sampleTime,
        percent: consumedNanoseconds / elapsedNanoseconds * 100
    };
}

function choosePrompt() {
    return weightedPromptText();
}

function frontmostProcessName(systemEvents) {
    const process = systemEvents.processes.whose({ frontmost: true })[0];
    return process ? process.name() : null;
}

function runningPerplexityApplications() {
    const applications = $.NSWorkspace.sharedWorkspace.runningApplications;
    const result = [];
    for (let index = 0; index < Number(applications.count); index += 1) {
        const application = applications.objectAtIndex(index);
        const bundleIdentifier = application.bundleIdentifier;
        if (!objcObjectIsNil(bundleIdentifier) &&
            String(ObjC.unwrap(bundleIdentifier)) === PERPLEXITY_BUNDLE_IDENTIFIER) {
            result.push(application);
        }
    }
    return result;
}

function restoreFrontmostProcess(processName) {
    if (!processName || processName === PROCESS_NAME) {
        return;
    }
    try {
        const processes = Application("System Events").processes.whose({
            name: processName
        });
        if (processes.length > 0) {
            processes[0].frontmost = true;
        }
    } catch (error) {
        // Restart success does not depend on restoring the previous foreground app.
    }
}

function finishPerplexityClientRestart(success, detail) {
    if (!perplexityRestart) {
        return;
    }
    const previousFrontmostName = perplexityRestart.previousFrontmostName;
    perplexityRestart = null;
    if (monitorState) {
        monitorState.waitWarning = false;
        monitorState.waitRestartDetail = success
            ? "RESTARTED · waiting for runner"
            : `RESTART FAILED · ${detail} · reset to retry`;
        monitorState.ui.waitProgress.setAlphaValue(1.0);
        monitorState.ui.signalConnectorView.setNeedsDisplay(true);
    }
    if (success) {
        restoreFrontmostProcess(previousFrontmostName);
    }
    updateSignalAnimationControls();
}

function launchPerplexityClientForRestart(now) {
    if (!perplexityRestart) {
        return;
    }
    perplexityRestart.phase = "launching";
    perplexityRestart.phaseStartedAt = now;
    perplexityRestart.nextPollAt = now + PERPLEXITY_RESTART_POLL_MILLISECONDS;
    monitorState.waitRestartDetail = "RESTARTING · launching Perplexity";
    try {
        Application(PERPLEXITY_BUNDLE_IDENTIFIER).activate();
    } catch (error) {
        finishPerplexityClientRestart(false, `launch failed: ${error}`);
    }
}

function forceTerminatePerplexityClient(now) {
    if (!perplexityRestart) {
        return;
    }
    try {
        const applications = runningPerplexityApplications();
        let accepted = false;
        for (const application of applications) {
            accepted = Boolean(application.forceTerminate) || accepted;
        }
        if (applications.length > 0 && !accepted) {
            finishPerplexityClientRestart(false, "Perplexity rejected force-quit");
            return;
        }
    } catch (error) {
        finishPerplexityClientRestart(false, `force-quit failed: ${error}`);
        return;
    }
    perplexityRestart.phase = "force-quitting";
    perplexityRestart.phaseStartedAt = now;
    perplexityRestart.nextPollAt = now + PERPLEXITY_RESTART_POLL_MILLISECONDS;
    monitorState.waitRestartDetail = "RESTARTING · force-quitting Perplexity";
}

function startPerplexityClientRestart(now) {
    if (!monitorState || perplexityRestart || monitorState.waitSignalLatched) {
        return false;
    }

    let previousFrontmostName = null;
    try {
        previousFrontmostName = frontmostProcessName(Application("System Events"));
    } catch (error) {
        previousFrontmostName = null;
    }

    monitorState.waitSignalLatched = true;
    monitorState.waitWarning = false;
    monitorState.waitRestartDetail = "RESTARTING · quitting Perplexity";
    perplexityRestart = {
        phase: "quitting",
        phaseStartedAt: now,
        nextPollAt: now,
        previousFrontmostName
    };
    updateSignalAnimationControls();

    try {
        const applications = runningPerplexityApplications();
        if (applications.length === 0) {
            launchPerplexityClientForRestart(now);
        } else {
            let accepted = false;
            for (const application of applications) {
                accepted = Boolean(application.terminate) || accepted;
            }
            if (!accepted) {
                forceTerminatePerplexityClient(now);
            }
        }
    } catch (error) {
        forceTerminatePerplexityClient(now);
    }
    return true;
}

function updatePerplexityClientRestart(now) {
    if (!perplexityRestart || now < perplexityRestart.nextPollAt) {
        return;
    }
    perplexityRestart.nextPollAt = now + PERPLEXITY_RESTART_POLL_MILLISECONDS;

    let applications;
    try {
        applications = runningPerplexityApplications();
    } catch (error) {
        finishPerplexityClientRestart(false, `process lookup failed: ${error}`);
        return;
    }
    if (perplexityRestart.phase === "quitting") {
        if (applications.length === 0) {
            launchPerplexityClientForRestart(now);
        } else if (now - perplexityRestart.phaseStartedAt >=
            PERPLEXITY_RESTART_QUIT_TIMEOUT_MILLISECONDS) {
            forceTerminatePerplexityClient(now);
        }
    } else if (perplexityRestart.phase === "force-quitting") {
        if (applications.length === 0) {
            launchPerplexityClientForRestart(now);
        } else if (now - perplexityRestart.phaseStartedAt >=
            PERPLEXITY_RESTART_FORCE_TIMEOUT_MILLISECONDS) {
            finishPerplexityClientRestart(false, "Perplexity did not quit");
        }
    } else if (perplexityRestart.phase === "launching") {
        if (applications.some(application => Boolean(application.isFinishedLaunching))) {
            finishPerplexityClientRestart(true, "");
        } else if (now - perplexityRestart.phaseStartedAt >=
            PERPLEXITY_RESTART_LAUNCH_TIMEOUT_MILLISECONDS) {
            finishPerplexityClientRestart(false, "Perplexity did not relaunch");
        }
    }
}

function sendPrompt(promptOverride) {
    const systemEvents = Application("System Events");
    const perplexity = Application("Perplexity");
    const previousFrontmostName = frontmostProcessName(systemEvents);
    const rawPromptText = arguments.length > 0 ? String(promptOverride) : choosePrompt();
    let perplexityIsReady = false;

    for (const retryDelay of [0.1, 0.2, 0.4, 0.8]) {
        perplexity.activate();
        delay(retryDelay);

        const processes = systemEvents.processes.whose({ name: "Perplexity" });
        if (processes.length > 0 && processes[0].frontmost()) {
            perplexityIsReady = true;
            break;
        }
    }

    if (!perplexityIsReady) {
        throw new Error("Perplexity did not become frontmost.");
    }

    const previousPromptSentinel = activePromptSentinel;
    activePromptSentinel = generateRandomPromptSentinel();
    if (!saveConfigurationNow()) {
        const message = configurationSaveFailureMessage() +
            " Prompt injection was cancelled so an untracked sentinel cannot be emitted.";
        activePromptSentinel = previousPromptSentinel;
        configurationDirty = true;
        runnerStatusDetail = message;
        updateRunnerUI(Date.now());
        if (previousFrontmostName && previousFrontmostName !== "Perplexity") {
            const previousProcesses = systemEvents.processes.whose({ name: previousFrontmostName });
            if (previousProcesses.length > 0) {
                previousProcesses[0].frontmost = true;
            }
        }
        throw new Error(message);
    }
    const promptText = expandPromptSentinel(rawPromptText, activePromptSentinel);

    systemEvents.keyCode(36);
    delay(0.2);
    systemEvents.keystroke("k", { using: ["command down"] });
    delay(0.1);
    systemEvents.keystroke("a", { using: ["command down"] });
    systemEvents.keystroke(promptText);
    systemEvents.keyCode(36);

    if (previousFrontmostName && previousFrontmostName !== "Perplexity") {
        const previousProcesses = systemEvents.processes.whose({ name: previousFrontmostName });
        if (previousProcesses.length > 0) {
            previousProcesses[0].frontmost = true;
        }
    }
}

function makeLabel(frame, text, fontSize) {
    const label = $.NSTextField.alloc.initWithFrame(frame);
    label.setStringValue(text);
    label.setEditable(false);
    label.setSelectable(false);
    label.setBezeled(false);
    label.setDrawsBackground(false);
    label.setFont($.NSFont.systemFontOfSize(fontSize));
    return label;
}

function makeSectionTitle(frame, text) {
    const label = makeLabel(frame, text, 13);
    label.setFont($.NSFont.systemFontOfSizeWeight(13, $.NSFontWeightSemibold));
    label.setTextColor($.NSColor.secondaryLabelColor);
    return label;
}

function makeCaptionLabel(frame, text) {
    const label = makeLabel(frame, text, 11);
    label.setTextColor($.NSColor.secondaryLabelColor);
    return label;
}

function makeValueLabel(frame, text) {
    const label = makeLabel(frame, text, 12);
    label.setFont($.NSFont.monospacedDigitSystemFontOfSizeWeight(12, $.NSFontWeightMedium));
    label.setAlignment($.NSTextAlignmentRight);
    return label;
}

function makeMultilineEditor(frame, text) {
    const field = $.NSTextField.alloc.initWithFrame(frame);
    field.setStringValue(text);
    field.setEditable(true);
    field.setSelectable(true);
    field.setBezeled(true);
    field.setDrawsBackground(true);
    field.setUsesSingleLineMode(false);
    field.setLineBreakMode($.NSLineBreakByWordWrapping);
    field.setMaximumNumberOfLines(3);
    field.cell.setWraps(true);
    field.cell.setScrollable(false);
    field.setFont($.NSFont.systemFontOfSize(11));
    return field;
}

function makePushButton(frame, title) {
    const button = $.NSButton.alloc.initWithFrame(frame);
    button.setTitle(title);
    button.setBezelStyle($.NSBezelStyleRounded);
    return button;
}

function makeSwitch(frame, title, enabled) {
    const button = $.NSButton.alloc.initWithFrame(frame);
    button.setButtonType($.NSSwitchButton);
    button.setTitle(title);
    button.setState(enabled ? $.NSControlStateValueOn : $.NSControlStateValueOff);
    return button;
}

function makeToggleSwitch(frame, enabled, toolTip) {
    const toggle = $.NSSwitch.alloc.initWithFrame(frame);
    toggle.setState(enabled ? $.NSControlStateValueOn : $.NSControlStateValueOff);
    toggle.setToolTip(toolTip);
    return toggle;
}

function runnerReadyStatusImage() {
    const size = 36;
    const image = $.NSImage.alloc.initWithSize($.NSMakeSize(size, size));
    image.lockFocus;
    $.NSColor.systemGreenColor.setFill;
    $.NSBezierPath.bezierPathWithOvalInRect(
        $.NSMakeRect(0, 0, size, size)
    ).fill;

    const walkerImage = $.NSImage.imageWithSystemSymbolNameAccessibilityDescription(
        "figure.walk",
        "Run script available"
    );
    const sizeConfiguration = $.NSImageSymbolConfiguration.configurationWithPointSizeWeight(
        23,
        $.NSFontWeightSemibold
    );
    const colorConfiguration =
        $.NSImageSymbolConfiguration.configurationWithHierarchicalColor(
            $.NSColor.darkGrayColor
        );
    const configuredWalker = walkerImage.imageWithSymbolConfiguration(
        sizeConfiguration.configurationByApplyingConfiguration(colorConfiguration)
    ) || walkerImage;
    configuredWalker.drawInRect($.NSMakeRect(7, 5, 22, 26));
    image.unlockFocus;
    image.setTemplate(false);
    return image;
}

function runnerStatusSymbolImage(state) {
    if (state === "ready") {
        return runnerReadyStatusImage();
    }
    if (state === "sentinel") {
        const image = $.NSImage.imageWithSystemSymbolNameAccessibilityDescription(
            runnerLEDHovering ? "trash.circle.fill" : "nosign",
            runnerLEDHovering
                ? "Delete run.sh and rotate sentinel"
                : "Sentinel detected; runner halted"
        );
        const configuration = $.NSImageSymbolConfiguration.configurationWithPointSizeWeight(
            36,
            $.NSFontWeightBold
        );
        return image.imageWithSymbolConfiguration(configuration) || image;
    }

    // "orphaned" icon rationale (see /tmp/autodocs/_src/tools/orphan-state-diagram
    // for the full state diagram and rendered source):
    //   Previously used "exclamationmark.triangle.fill", identical to
    //   "orphan conflict" and "path error". That made a normal, still-
    //   interruptible detached process look identical to an error state
    //   the app refuses to touch.
    //   Now uses "clock.badge.xmark": the clock face reads as "a process
    //   is still ongoing / time-based", and the small red x badge at the
    //   lower-right reads as "you can interrupt/stop it". This keeps
    //   "orphaned" visually distinct from "orphan stopping" (already
    //   mid-termination, xmark.circle.fill) and from "orphan conflict"
    //   (a dead end the app will not signal, exclamationmark.triangle.fill).
    const symbolNames = {
        running: "xmark.circle.fill",
        orphaned: "clock.badge.xmark",
        "orphan stopping": "xmark.circle.fill",
        "orphan recovery": "arrow.counterclockwise.circle.fill",
        "orphan conflict": "exclamationmark.triangle.fill",
        idle: "arrow.counterclockwise.circle.fill",
        uninitialized: "questionmark.circle.fill",
        "path error": "exclamationmark.triangle.fill"
    };
    const descriptions = {
        running: "Runner kill switch",
        orphaned: "Detached runner still active; click to interrupt",
        "orphan stopping": "Orphaned runner stopping",
        "orphan recovery": "Recover orphaned runner snapshot",
        "orphan conflict": "Orphaned runner ownership conflict",
        idle: "Runner idle",
        uninitialized: "Runner self-test required",
        "path error": "Runner path error"
    };
    const image = $.NSImage.imageWithSystemSymbolNameAccessibilityDescription(
        symbolNames[state],
        descriptions[state]
    );
    const configuration = $.NSImageSymbolConfiguration.configurationWithPointSizeWeight(
        36,
        state === "running" || state === "orphan stopping"
            ? $.NSFontWeightBold
            : $.NSFontWeightRegular
    );
    return image.imageWithSymbolConfiguration(configuration) || image;
}

function setRunnerStatusButtonImage(button, state) {
    if (runnerStatusImageMode === state) {
        return;
    }
    runnerStatusImageMode = state;
    button.setImage(runnerStatusSymbolImage(state));
}

function makeRunnerStatusButton(frame) {
    const button = $.RunnerStatusButton.alloc.initWithFrame(frame);
    button.setImagePosition($.NSImageOnly);
    button.setImageScaling($.NSImageScaleProportionallyUpOrDown);
    button.setBordered(false);
    button.setContentTintColor($.NSColor.systemGrayColor);
    button.setToolTip(
        "Runner status. While a task is active, this becomes a large cross kill switch."
    );
    setRunnerStatusButtonImage(button, "uninitialized");
    return button;
}

function updateAutoModeButtonAppearance(button) {
    const autoEnabled = Number(button.state) === Number($.NSControlStateValueOn);
    button.setTitle(autoEnabled ? "AUTO · ON" : "AUTO · OFF");
    button.setContentTintColor(
        autoEnabled ? $.NSColor.labelColor : $.NSColor.secondaryLabelColor
    );
    if (Boolean(button.respondsToSelector("setBezelColor:"))) {
        button.setBezelColor(
            autoEnabled
                ? $.NSColor.systemGreenColor.colorWithAlphaComponent(0.72)
                : $.NSColor.controlColor
        );
    }
    button.setAlphaValue(Boolean(button.enabled) ? 1.0 : 0.55);
}

function makeAutoModeButton(frame, enabled) {
    const button = $.NSButton.alloc.initWithFrame(frame);
    button.setButtonType($.NSButtonTypePushOnPushOff);
    button.setBezelStyle($.NSBezelStyleTexturedRounded);
    button.setFont($.NSFont.systemFontOfSizeWeight(14, $.NSFontWeightBold));
    button.setState(enabled ? $.NSControlStateValueOn : $.NSControlStateValueOff);
    button.setToolTip(
        "Large push-on/push-off Auto Mode control. When enabled, an eligible watched run.sh starts automatically."
    );
    updateAutoModeButtonAppearance(button);
    return button;
}

function makeCard(frame) {
    const card = $.NSBox.alloc.initWithFrame(frame);
    card.setBoxType($.NSBoxCustom);
    card.setBorderType($.NSLineBorder);
    card.setBorderWidth(1);
    card.setCornerRadius(12);
    card.setFillColor($.NSColor.controlBackgroundColor.colorWithAlphaComponent(0.42));
    card.setBorderColor($.NSColor.separatorColor.colorWithAlphaComponent(0.55));
    return card;
}

function makeProgressBar(frame, maximum) {
    const bar = $.NSProgressIndicator.alloc.initWithFrame(frame);
    bar.setIndeterminate(false);
    bar.setMinValue(0);
    bar.setMaxValue(maximum);
    bar.setDoubleValue(0);
    return bar;
}

function makeSlider(frame, minimum, maximum, initial) {
    const slider = $.NSSlider.alloc.initWithFrame(frame);
    slider.setMinValue(minimum);
    slider.setMaxValue(maximum);
    slider.setDoubleValue(initial);
    slider.setContinuous(true);
    slider.setNumberOfTickMarks(0);
    return slider;
}

function makeVerticalSlider(frame, minimum, maximum, initial) {
    const slider = makeSlider(frame, minimum, maximum, initial);
    slider.setVertical(true);
    return slider;
}


function createWindow(configuration) {
    const nsApp = $.NSApplication.sharedApplication;
    nsApp.setActivationPolicy($.NSApplicationActivationPolicyAccessory);
    nsApp.finishLaunching;

    const windowWidth = 1240;
    const windowHeight = 720;
    const cardX = 20;
    const cardWidth = 720;
    const contentX = 40;
    const contentWidth = 680;
    const graphX = 100;
    const graphWidth = 620;
    const graphY = 340;
    const graphHeight = 168;

    const style = $.NSWindowStyleMaskTitled |
        $.NSWindowStyleMaskClosable |
        $.NSWindowStyleMaskMiniaturizable;
    const frame = $.NSMakeRect(0, 0, windowWidth, windowHeight);
    const window = $.NSWindow.alloc.initWithContentRectStyleMaskBackingDefer(
        frame,
        style,
        $.NSBackingStoreBuffered,
        false
    );

    window.setTitle("Perplexity signal monitor");
    window.setBackgroundColor($.NSColor.windowBackgroundColor);
    window.center;
    window.setReleasedWhenClosed(false);
    window.setLevel($.NSFloatingWindowLevel);

    const content = $.NSView.alloc.initWithFrame(frame);
    window.setContentView(content);

    const promptCard = makeCard($.NSMakeRect(760, 380, 460, 320));
    const runnerCard = makeCard($.NSMakeRect(760, 25, 460, 335));

    const title = makeLabel(
        $.NSMakeRect(24, 680, 430, 24),
        "Perplexity activity guard",
        16
    );
    title.setFont($.NSFont.systemFontOfSizeWeight(16, $.NSFontWeightSemibold));
    const subtitle = makeCaptionLabel(
        $.NSMakeRect(24, 657, 610, 18),
        "Graph: click adds a threshold sample · drag vertically for threshold · horizontally for smoothing"
    );
    const configurationSaveButton = makePushButton(
        $.NSMakeRect(468, 676, 96, 28),
        "Save"
    );
    configurationSaveButton.setToolTip("Save the current configuration.");
    const configurationMenu = $.NSPopUpButton.alloc.initWithFramePullsDown(
        $.NSMakeRect(562, 676, 32, 28),
        true
    );
    configurationMenu.addItemsWithTitles([
        "▾",
        "Load Saved",
        "Reset Defaults"
    ]);
    configurationMenu.setToolTip("Load saved configuration or reset defaults.");
    const runnerOutputButton = makePushButton(
        $.NSMakeRect(650, 676, 86, 28),
        "Output"
    );

    const cpuCard = makeCard($.NSMakeRect(cardX, 195, cardWidth, 445));
    const waitCard = makeCard($.NSMakeRect(cardX, 25, cardWidth, 150));
    const signalConnectorView = $.SignalConnectorView.alloc.initWithFrame(frame);

    const cpuSectionTitle = makeSectionTitle(
        $.NSMakeRect(contentX, 608, contentWidth - 100, 20),
        "CPU SIGNAL"
    );
    const cpuActiveLabel = makeCaptionLabel(
        $.NSMakeRect(612, 607, 48, 18),
        "Active"
    );
    cpuActiveLabel.setAlignment($.NSTextAlignmentRight);
    const cpuActiveButton = makeToggleSwitch(
        $.NSMakeRect(670, 602, 42, 24),
        configuration.cpuSignalActive,
        "Enable or disable the CPU Signal."
    );
    const averageWindowLabel = makeCaptionLabel(
        $.NSMakeRect(contentX, 577, 220, 18),
        "Smoothing window"
    );
    const averageWindowValue = makeValueLabel(
        $.NSMakeRect(580, 577, 140, 18),
        ""
    );
    const averageWindowSlider = makeSlider(
        $.NSMakeRect(contentX, 548, contentWidth, 26),
        AVERAGE_WINDOW_MIN_SECONDS,
        AVERAGE_WINDOW_MAX_SECONDS,
        configuration.smoothingWindowSeconds
    );

    const graphTitle = makeSectionTitle(
        $.NSMakeRect(graphX, 515, 150, 18),
        "CPU HISTORY"
    );
    const qualifyingLegend = makeCaptionLabel(
        $.NSMakeRect(352, 515, 112, 18),
        "● Qualifying"
    );
    qualifyingLegend.setTextColor($.NSColor.systemRedColor);
    const aboveLegend = makeCaptionLabel(
        $.NSMakeRect(468, 515, 104, 18),
        "● Above"
    );
    aboveLegend.setTextColor($.NSColor.systemGreenColor);
    const latestLegend = makeCaptionLabel(
        $.NSMakeRect(576, 515, 144, 18),
        "● Latest exceedance"
    );
    latestLegend.setTextColor($.NSColor.systemBlueColor);

    const cpuGraph = $.CPUGraphView.alloc.initWithFrame(
        $.NSMakeRect(graphX, graphY, graphWidth, graphHeight)
    );
    cpuGraph.setToolTip(
        "Click to add one synthetic sample at the current threshold without clearing history. " +
        "Drag vertically to adjust CPU threshold; drag horizontally to adjust smoothing."
    );
    const cpuThresholdSlider = makeVerticalSlider(
        $.NSMakeRect(50, graphY, 30, graphHeight),
        CPU_THRESHOLD_MIN_PERCENT,
        CPU_THRESHOLD_MAX_PERCENT,
        configuration.cpuThresholdPercent
    );
    const thresholdMaximumLabel = makeCaptionLabel(
        $.NSMakeRect(34, graphY + graphHeight - 8, 44, 16),
        "1%"
    );
    const thresholdMinimumLabel = makeCaptionLabel(
        $.NSMakeRect(34, graphY - 8, 44, 16),
        "0%"
    );

    const graphStatus = makeCaptionLabel(
        $.NSMakeRect(graphX, 316, graphWidth, 18),
        ""
    );
    graphStatus.setFont($.NSFont.monospacedDigitSystemFontOfSizeWeight(11, $.NSFontWeightRegular));

    const cpuDurationLabel = makeCaptionLabel(
        $.NSMakeRect(contentX, 287, 260, 18),
        "Low-CPU duration / graph span"
    );
    const cpuDurationValue = makeValueLabel(
        $.NSMakeRect(580, 287, 140, 18),
        ""
    );
    const cpuDurationSlider = makeSlider(
        $.NSMakeRect(contentX, 258, contentWidth, 26),
        CPU_TIMEOUT_MIN_SECONDS,
        CPU_TIMEOUT_MAX_SECONDS,
        configuration.lowCPUCountdownSeconds
    );

    const cpuProgressLabel = makeCaptionLabel(
        $.NSMakeRect(contentX, 231, 180, 18),
        "Low-CPU countdown"
    );
    const cpuProgressValue = makeValueLabel(
        $.NSMakeRect(390, 231, 330, 18),
        ""
    );
    const cpuProgress = makeProgressBar(
        $.NSMakeRect(contentX, 211, contentWidth, 14),
        configuration.lowCPUCountdownSeconds
    );

    const waitSectionTitle = makeSectionTitle(
        $.NSMakeRect(contentX, 143, contentWidth - 190, 20),
        "WAIT SIGNAL · RESTART PERPLEXITY"
    );
    const waitActiveLabel = makeCaptionLabel(
        $.NSMakeRect(540, 142, 48, 18),
        "Active"
    );
    waitActiveLabel.setAlignment($.NSTextAlignmentRight);
    const waitActiveButton = makeToggleSwitch(
        $.NSMakeRect(594, 137, 42, 24),
        configuration.waitSignalActive,
        "Restart Perplexity once when the timeout is reached; a runner execution rearms the signal."
    );
    const waitResetButton = makePushButton(
        $.NSMakeRect(646, 135, 74, 28),
        "Reset"
    );
    const waitLabel = makeCaptionLabel(
        $.NSMakeRect(contentX, 113, 220, 18),
        "Elapsed / restart threshold"
    );
    const waitValue = makeValueLabel(
        $.NSMakeRect(500, 113, 220, 18),
        ""
    );
    const waitProgress = makeProgressBar(
        $.NSMakeRect(contentX + 8, 82, contentWidth - 16, 16),
        WAIT_TIMEOUT_MAX_SECONDS
    );
    const waitSlider = makeSlider(
        $.NSMakeRect(contentX, 73, contentWidth, 34),
        WAIT_TIMEOUT_MIN_SECONDS,
        WAIT_TIMEOUT_MAX_SECONDS,
        configuration.waitSignalTimeoutSeconds
    );
    waitSlider.setTrackFillColor($.NSColor.clearColor);
    const waitMinimumLabel = makeCaptionLabel(
        $.NSMakeRect(contentX, 49, 80, 16),
        "0 s"
    );
    const waitMaximumLabel = makeCaptionLabel(
        $.NSMakeRect(640, 49, 80, 16),
        "900 s"
    );
    waitMaximumLabel.setAlignment($.NSTextAlignmentRight);

    const promptSectionTitle = makeSectionTitle(
        $.NSMakeRect(780, 668, 180, 20),
        "PROMPT MIXER"
    );
    const promptInjectButton = makePushButton(
        $.NSMakeRect(1064, 660, 134, 28),
        "prompt now"
    );
    promptInjectButton.setToolTip(
        "Start the weighted Prompt Mixer animation now. Click anywhere during the roll to cancel."
    );
    const promptHint = makeCaptionLabel(
        $.NSMakeRect(780, 646, 418, 18),
        "Fresh 128-bit {sentinel}; empty rows off; click anywhere to cancel a roll."
    );
    promptHint.setToolTip(PROMPT_SENTINEL_TOOLTIP);

    promptRows = [];
    const promptControls = [];
    for (let index = 0; index < configuration.prompts.length; index += 1) {
        const rowY = 587 - index * 61;
        const highlightView = makeCard(
            $.NSMakeRect(772, rowY - 3, 434, 58)
        );
        highlightView.setBorderWidth(0);
        highlightView.setFillColor($.NSColor.clearColor);
        const slider = makeSlider(
            $.NSMakeRect(780, rowY + 17, 104, 26),
            0,
            100,
            configuration.prompts[index].weight
        );
        slider.setTag(index);
        const valueLabel = makeValueLabel(
            $.NSMakeRect(780, rowY, 104, 17),
            `${configuration.prompts[index].weight.toFixed(1)}%`
        );
        const textField = makeMultilineEditor(
            $.NSMakeRect(894, rowY, 304, 52),
            configuration.prompts[index].text
        );
        textField.setTag(PROMPT_TEXT_TAG_BASE + index);
        textField.setToolTip(PROMPT_SENTINEL_TOOLTIP);
        const row = { highlightView, slider, valueLabel, textField, eligible: true };
        promptRows.push(row);
        setPromptRowEligibility(row, Boolean(configuration.prompts[index].text.trim()));
        promptControls.push(highlightView, slider, valueLabel, textField);
    }

    const runnerSectionTitle = makeSectionTitle(
        $.NSMakeRect(780, 328, 190, 20),
        "LOCAL RUNNER"
    );
    // Keep all runner controls within runnerCard (x=760..1220). The LED and
    // its state name belong at the far right, with the state name centered
    // BELOW the LED so it does not collide with the status sentence.
    const runnerAutoButton = makeAutoModeButton(
        $.NSMakeRect(1012, 312, 118, 38),
        configuration.runner.autoMode
    );
    const runnerLEDButton = makeRunnerStatusButton(
        $.NSMakeRect(1142, 322, 44, 44)
    );
    const runnerActivityLabel = makeCaptionLabel(
        $.NSMakeRect(1116, 306, 96, 14),
        "uninitialized"
    );
    runnerActivityLabel.setAlignment($.NSTextAlignmentCenter);
    runnerActivityLabel.setFont(
        $.NSFont.systemFontOfSizeWeight(9, $.NSFontWeightSemibold)
    );
    const runnerStatusLabel = makeCaptionLabel(
        $.NSMakeRect(780, 276, 338, 32),
        "Environment self-test has not been run."
    );
    runnerStatusLabel.setMaximumNumberOfLines(2);
    runnerStatusLabel.setLineBreakMode($.NSLineBreakByWordWrapping);

    const runnerSelfTestButton = makePushButton(
        $.NSMakeRect(780, 238, 90, 30),
        "Self-test"
    );
    const runnerChooseButton = makePushButton(
        $.NSMakeRect(878, 238, 126, 30),
        "Choose path…"
    );

    const runnerScriptLabel = makeCaptionLabel(
        $.NSMakeRect(780, 210, 90, 18),
        "Run script"
    );
    const runnerSelectedPathLabel = makeCaptionLabel(
        $.NSMakeRect(870, 210, 160, 18),
        runnerSelectedScriptPath
    );
    const runnerSandboxButton = makeSwitch(
        $.NSMakeRect(1040, 207, 138, 24),
        "Use sandbox",
        configuration.runner.sandbox
    );
    runnerSelectedPathLabel.setLineBreakMode($.NSLineBreakByTruncatingMiddle);

    const runnerWaitLabel = makeCaptionLabel(
        $.NSMakeRect(780, 184, 190, 18),
        "Post-execution wait (0–20 s)"
    );
    const runnerWaitValue = makeValueLabel(
        $.NSMakeRect(1112, 184, 66, 18),
        `${configuration.postExecutionWaitSeconds.toFixed(1)} s`
    );
    const runnerWaitSlider = makeSlider(
        $.NSMakeRect(780, 158, 398, 24),
        RUNNER_NOTIFY_WAIT_MIN_SECONDS,
        RUNNER_NOTIFY_WAIT_MAX_SECONDS,
        configuration.postExecutionWaitSeconds
    );

    const runnerSuccessPromptButton = makeSwitch(
        $.NSMakeRect(780, 126, 98, 24),
        "On success",
        configuration.successPrompt.enabled
    );
    const runnerSuccessPromptField = $.NSTextField.alloc.initWithFrame(
        $.NSMakeRect(882, 123, 296, 27)
    );
    runnerSuccessPromptField.setStringValue(configuration.successPrompt.template);
    runnerSuccessPromptField.setEditable(true);
    runnerSuccessPromptField.setSelectable(true);
    runnerSuccessPromptField.setBezeled(true);

    const runnerFailurePromptButton = makeSwitch(
        $.NSMakeRect(780, 92, 98, 24),
        "On failure",
        configuration.failurePrompt.enabled
    );
    const runnerFailurePromptField = $.NSTextField.alloc.initWithFrame(
        $.NSMakeRect(882, 89, 296, 27)
    );
    runnerFailurePromptField.setStringValue(configuration.failurePrompt.template);
    runnerFailurePromptField.setEditable(true);
    runnerFailurePromptField.setSelectable(true);
    runnerFailurePromptField.setBezeled(true);

    const runnerModeHint = makeCaptionLabel(
        $.NSMakeRect(780, 62, 398, 18),
        "Templates support {exit}, {code}, {script}, and {output}."
    );

    const runnerOutputCard = makeCard($.NSMakeRect(cardX, 25, cardWidth, 615));
    const runnerOutputSectionTitle = makeSectionTitle(
        $.NSMakeRect(contentX, 608, contentWidth - 100, 20),
        "RUNNER OUTPUT"
    );
    const runnerOutputHideButton = makePushButton(
        $.NSMakeRect(646, 600, 74, 28),
        "Hide"
    );
    const runnerOutputScrollView = $.NSScrollView.alloc.initWithFrame(
        $.NSMakeRect(contentX, 50, contentWidth, 535)
    );
    runnerOutputScrollView.setHasVerticalScroller(true);
    runnerOutputScrollView.setHasHorizontalScroller(false);
    runnerOutputScrollView.setAutohidesScrollers(true);
    runnerOutputScrollView.setBorderType($.NSBezelBorder);

    runnerOutputTextView = $.NSTextView.alloc.initWithFrame(
        $.NSMakeRect(0, 0, contentWidth, 535)
    );
    runnerOutputTextView.setEditable(false);
    runnerOutputTextView.setSelectable(true);
    runnerOutputTextView.setRichText(false);
    runnerOutputTextView.setHorizontallyResizable(false);
    runnerOutputTextView.setVerticallyResizable(true);
    runnerOutputTextView.setMinSize($.NSMakeSize(0, 535));
    runnerOutputTextView.setMaxSize($.NSMakeSize(10000000, 10000000));
    runnerOutputTextView.setAutoresizingMask($.NSViewWidthSizable);
    runnerOutputTextView.textContainer.setContainerSize(
        $.NSMakeSize(contentWidth, 10000000)
    );
    runnerOutputTextView.textContainer.setWidthTracksTextView(true);
    runnerOutputTextView.setFont(
        $.NSFont.monospacedSystemFontOfSizeWeight(11, $.NSFontWeightRegular)
    );
    runnerOutputTextView.setString("");
    runnerOutputScrollView.setDocumentView(runnerOutputTextView);

    const signalViews = [
        cpuCard,
        waitCard,
        signalConnectorView,
        cpuSectionTitle,
        cpuActiveLabel,
        cpuActiveButton,
        averageWindowLabel,
        averageWindowValue,
        averageWindowSlider,
        graphTitle,
        qualifyingLegend,
        aboveLegend,
        latestLegend,
        cpuGraph,
        cpuThresholdSlider,
        thresholdMaximumLabel,
        thresholdMinimumLabel,
        graphStatus,
        cpuDurationLabel,
        cpuDurationValue,
        cpuDurationSlider,
        cpuProgressLabel,
        cpuProgressValue,
        cpuProgress,
        waitSectionTitle,
        waitActiveLabel,
        waitActiveButton,
        waitResetButton,
        waitLabel,
        waitValue,
        waitProgress,
        waitSlider,
        waitMinimumLabel,
        waitMaximumLabel
    ];
    const runnerOutputViews = [
        runnerOutputCard,
        runnerOutputSectionTitle,
        runnerOutputHideButton,
        runnerOutputScrollView
    ];
    for (const view of runnerOutputViews) {
        view.setHidden(true);
    }

    for (const control of [
        promptCard,
        runnerCard,
        title,
        subtitle,
        configurationSaveButton,
        configurationMenu,
        runnerOutputButton,
        ...signalViews,
        promptSectionTitle,
        promptInjectButton,
        promptHint,
        ...promptControls,
        runnerSectionTitle,
        runnerLEDButton,
        runnerActivityLabel,
        runnerStatusLabel,
        runnerSelfTestButton,
        runnerChooseButton,
        runnerSandboxButton,
        runnerAutoButton,
        runnerScriptLabel,
        runnerSelectedPathLabel,
        runnerWaitLabel,
        runnerWaitValue,
        runnerWaitSlider,
        runnerSuccessPromptButton,
        runnerSuccessPromptField,
        runnerFailurePromptButton,
        runnerFailurePromptField,
        runnerModeHint,
        ...runnerOutputViews
    ]) {
        content.addSubview(control);
    }

    const signalCancellationOverlay = $.SignalCancellationOverlay.alloc.initWithFrame(frame);
    signalCancellationOverlay.setHidden(true);
    signalCancellationOverlay.setToolTip("Click anywhere to cancel prompt selection and sending.");
    content.addSubview(signalCancellationOverlay);

    window.makeKeyAndOrderFront(null);
    nsApp.activateIgnoringOtherApps(true);

    return {
        nsApp,
        window,
        content,
        title,
        cpuGraph,
        graphStatus,
        cpuThresholdSlider,
        cpuDurationSlider,
        cpuDurationValue,
        averageWindowSlider,
        averageWindowValue,
        cpuProgressValue,
        cpuProgress,
        cpuActiveButton,
        waitValue,
        waitProgress,
        waitSlider,
        waitActiveButton,
        waitResetButton,
        signalViews,
        signalConnectorView,
        runnerOutputCard,
        runnerOutputViews,
        runnerOutputSectionTitle,
        runnerOutputHideButton,
        configurationSaveButton,
        configurationMenu,
        signalCancellationOverlay,
        promptCard,
        promptInjectButton,
        runnerLEDButton,
        runnerActivityLabel,
        runnerStatusLabel,
        runnerSelfTestButton,
        runnerChooseButton,
        runnerOutputButton,
        runnerSandboxButton,
        runnerAutoButton,
        runnerSelectedPathLabel,
        runnerWaitSlider,
        runnerWaitValue,
        runnerSuccessPromptButton,
        runnerSuccessPromptField,
        runnerFailurePromptButton,
        runnerFailurePromptField
    };
}

function run(argv) {
    if (argv.length > 1) {
        throw new Error(
            "Usage: perplexity-cpu-loop.js [PROJECT_DIRECTORY] — expected at most one positional argument."
        );
    }

    const configuration = loadConfiguration();
    if (argv.length === 1) {
        const projectDirectory = resolveProjectDirectory(argv[0]);
        configuration.runner.selectedScriptPath = String(ObjC.unwrap(
            $(projectDirectory).stringByAppendingPathComponent("run.sh")
                .stringByStandardizingPath
        ));
    }

    runnerSelectedScriptPath = configuration.runner.selectedScriptPath;
    activePromptSentinel = configuration.activePromptSentinel;
    const ui = createWindow(configuration);
    runnerPathDirectoryAvailable = runnerPathDirectoryExists();
    runnerReady = runnerPathDirectoryAvailable && runnerFileExists();
    const autoModeDisabledForExistingScript = disableAutoModeForExistingRunScript(
        ui,
        runnerReady
    );

    sampleCPUPercent();
    const now = Date.now();
    monitorState = {
        ui,
        cpuSamples: [],
        cpuGraphData: [],
        graphEndTime: now,
        currentRawCPU: 0,
        currentAverageCPU: 0,
        trailingLowCPUSeconds: 0,
        waitSeconds: 0,
        waitSignalLatched: false,
        waitRestartDetail: "",
        lastTick: now,
        lastCPUSample: now,
        pulsePhase: false,
        lastPulse: 0,
        cpuWarning: false,
        waitWarning: false
    };

    monitorController = $.MonitorController.alloc.init;
    ui.window.setDelegate(monitorController);

    for (let index = 0; index < promptRows.length; index += 1) {
        promptRows[index].slider.setTarget(monitorController);
        promptRows[index].slider.setAction("promptWeightChanged:");
        promptRows[index].textField.setDelegate(monitorController);
    }
    normalizePromptWeights();

    for (const control of [
        ui.averageWindowSlider,
        ui.cpuThresholdSlider,
        ui.cpuDurationSlider,
        ui.waitSlider,
        ui.runnerWaitSlider,
        ui.runnerSuccessPromptButton,
        ui.runnerFailurePromptButton
    ]) {
        control.setTarget(monitorController);
        control.setAction("configurationChanged:");
    }
    ui.runnerSuccessPromptField.setDelegate(monitorController);
    ui.runnerFailurePromptField.setDelegate(monitorController);

    ui.cpuActiveButton.setTarget(monitorController);
    ui.cpuActiveButton.setAction("cpuSignalActiveChanged:");
    ui.waitActiveButton.setTarget(monitorController);
    ui.waitActiveButton.setAction("waitSignalActiveChanged:");
    ui.configurationSaveButton.setTarget(monitorController);
    ui.configurationSaveButton.setAction("saveConfigurationNow:");
    ui.configurationMenu.itemAtIndex(1).setTarget(monitorController);
    ui.configurationMenu.itemAtIndex(1).setAction("loadSavedConfiguration:");
    ui.configurationMenu.itemAtIndex(2).setTarget(monitorController);
    ui.configurationMenu.itemAtIndex(2).setAction("resetDefaultConfiguration:");
    ui.promptInjectButton.setTarget(monitorController);
    ui.promptInjectButton.setAction("promptInjectNow:");
    ui.waitResetButton.setTarget(monitorController);
    ui.waitResetButton.setAction("resetWaitButton:");
    ui.runnerOutputHideButton.setTarget(monitorController);
    ui.runnerOutputHideButton.setAction("runnerHideOutput:");
    ui.runnerSelfTestButton.setTarget(monitorController);
    ui.runnerSelfTestButton.setAction("runnerSelfTest:");
    ui.runnerChooseButton.setTarget(monitorController);
    ui.runnerChooseButton.setAction("runnerChoose:");
    ui.runnerOutputButton.setTarget(monitorController);
    ui.runnerOutputButton.setAction("runnerShowOutput:");
    ui.runnerLEDButton.setTarget(monitorController);
    ui.runnerLEDButton.setAction("runnerLED:");
    ui.runnerSandboxButton.setTarget(monitorController);
    ui.runnerSandboxButton.setAction("runnerSandboxChanged:");
    ui.runnerAutoButton.setTarget(monitorController);
    ui.runnerAutoButton.setAction("runnerAuto:");

    const signalsDisabledWithAuto = !runnerAutoModeEnabled() && disableSignalSources(ui);
    if (autoModeDisabledForExistingScript || signalsDisabledWithAuto) {
        scheduleConfigurationSave();
    }
    updateSignalAnimationControls();
    updateSignalAnimationVisuals();

    waitClickRecognizer = $.NSClickGestureRecognizer.alloc.initWithTargetAction(
        monitorController,
        "resetWait:"
    );
    waitClickRecognizer.setNumberOfClicksRequired(1);
    waitClickRecognizer.setDelaysPrimaryMouseButtonEvents(true);
    ui.waitSlider.addGestureRecognizer(waitClickRecognizer);

    runnerStartupSelfTestPending = true;
    orphanedRunnerTick(Date.now(), true);
    if (!orphanedRunner) {
        runnerStartupSelfTestPending = false;
        startRunnerSelfTest();
    }

    monitorTimer = $.NSTimer.timerWithTimeIntervalTargetSelectorUserInfoRepeats(
        MONITOR_TICK_SECONDS,
        monitorController,
        "tick:",
        null,
        true
    );
    $.NSRunLoop.mainRunLoop.addTimerForMode(monitorTimer, $.NSRunLoopCommonModes);

    monitorTick();
    ui.nsApp.run;
}
