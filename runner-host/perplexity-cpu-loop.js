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
const CPU_THRESHOLD_MAX_PERCENT = 20;
const CPU_GRAPH_RANGE_DEFAULT_PERCENT = 1;
const CPU_GRAPH_RANGE_MIN_PERCENT = 0.02;
const CPU_GRAPH_RANGE_MAX_PERCENT = 20;
const CPU_GRAPH_RANGE_SCROLL_SENSITIVITY = 0.25;
const CPU_TIMEOUT_DEFAULT_SECONDS = 10;
const CPU_TIMEOUT_MIN_SECONDS = 0;
const CPU_TIMEOUT_MAX_SECONDS = 120;
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
const RESTART_PROMPT_DELAY_MILLISECONDS = 5000;
const RESTART_PROMPT_RETRY_MILLISECONDS = 1000;
const RESTART_PROMPT_MAX_ATTEMPTS = 3;
const WAIT_RESTART_PROMPT_DEFAULT =
    "Perplexity was restarted. Continue with your task. If you're stuck or finished, " +
    "write \"{sentinel}\" into run.sh.";
const RUNNER_NOTIFY_WAIT_DEFAULT_SECONDS = 2;
const RUNNER_NOTIFY_WAIT_MIN_SECONDS = 0;
const RUNNER_NOTIFY_WAIT_MAX_SECONDS = 20;
const WARNING_SECONDS = 3;
const PULSE_INTERVAL_MILLISECONDS = 300;
const MONITOR_TICK_SECONDS = 0.05;
const CPU_SAMPLE_SECONDS = 0.1;
const PID_REFRESH_SECONDS = 1;
const MESSAGES_COMMAND_POLL_MILLISECONDS = 1000;
const MESSAGES_CHAT_RESOLVE_MILLISECONDS = 5000;
const IMESSAGE_CHUNK_CHARACTERS = 7000;
const MESSAGES_PROCESSED_GUID_LIMIT = 2000;
const MESSAGE_LOG_COLLAPSED_HEIGHT = 52;
const MESSAGE_LOG_EXPANDED_HEIGHT = 220;
const MESSAGE_LOG_ENTRY_LIMIT = 500;
const RUNNER_PRESENCE_POLL_SECONDS = 1;
const ORPHAN_RUNNER_POLL_SECONDS = 1;
const ORPHAN_RUNNER_KILL_FALLBACK_MILLISECONDS = 1200;
const ORPHAN_RUNNER_KILL_VERIFY_MILLISECONDS = 3000;
const ACTIVE_RUN_RECORD_SCHEMA_VERSION = 1;
const EXECUTION_SNAPSHOT_NAME_PATTERN =
    /^\.perplexity-cpu-loop-execution-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.sh$/;
const PROCESS_NAME = "Perplexity";
const PERPLEXITY_BUNDLE_IDENTIFIER = "ai.perplexity.macv3";
const SENTINEL_IMESSAGE_RECIPIENT = "+4915121191462";
const MESSAGES_COMMAND_HANDLE = "+4915121191462";
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
const CPU_GRAPH_TOOLTIP =
    "Press to capture the current smoothing width and set absolute CPU threshold from pointer y; " +
    "horizontal movement adjusts smoothing relatively, scaled by low-CPU duration divided by the smoothing-width range. " +
    "While pressed, filled bars use the captured width and a black upper-envelope surface traces the live width using bar tops and their connections. " +
    "Releasing outside restores the captured width. Trackpad scrolling changes low-CPU duration logarithmically " +
    "(horizontal, up to 120 s) and the 0.02–20% displayed CPU-load range (vertical).";
const GRAPH_TOOLTIP_RESTORE_SECONDS = 0.35;
const PROMPT_SENTINEL_TOOLTIP =
    "The UI remembers one cryptographically random 128-bit Base64 token and rotates it only after a " +
    "successful Perplexity restart. If the watched run.sh still contains the active token, the restart " +
    "preserves it for safety. Every {sentinel} occurrence expands to the active token only at injection " +
    "time; the stored field text is unchanged. Before starting run.sh, the UI checks for that token. " +
    "If found, it disables Auto Mode, leaves run.sh untouched, and skips execution.";
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
let graphMousePressed = false;
let graphWindowBeforeMouseDown = null;
let graphMouseDownX = null;
let graphToolTipRestoreTimer = null;
let cpuSliderPreview = null;
let cpuGraphTransition = null;
let cpuGraphTransitionTimer = null;
let promptRows = [];
let promptEditorEntries = [];
let promptEditorLayout = null;
let promptEditorResize = null;
let promptEditorEditSession = null;
let promptCollapseMenuItem = null;
let signalAnimation = null;
let perplexityRestart = null;
let restartPromptDelivery = null;
let perplexityClientRunning = false;
let perplexityPresenceLastCheckedAt = 0;
let activePromptSentinel = "";
let promptWeightGestureSnapshot = null;
let configurationSaveTimer = null;
let configurationDirty = false;
let configurationLastError = "";

let runnerTask = null;
let runnerTaskMode = null;
let runnerTaskStartedAt = 0;
let runnerLastCompletedAt = null;
let runnerReady = false;
let runnerPathDirectoryAvailable = false;
let runnerSelfTestStatus = "unverified";
let runnerAcknowledgedSelfTestConfiguration = null;
let runnerCommandLineSkipSelfTest = false;
let runnerCommandLineNoSelfTest = false;
let runnerLastExitStatus = null;
let runnerSelectedScriptPath = null;
let runnerSelectedLogPath = null;
let runnerKillRequested = false;
let runnerKillDeadline = null;
let runnerStatusDetail = "";
let runnerValidatedConfiguration = null;
let runnerTaskConfiguration = null;
let runnerExecutionSnapshotPath = null;
let runnerExecutionOriginalPath = null;
let runnerExecutionPreviewPath = null;
let runnerExecutionPreviewText = null;
let runnerExecutionDiagnosticName = null;
let runnerOutputLastPollAt = 0;
let runnerOutputLastText = "";
let runnerScriptPreviewLastPollAt = 0;
let runnerScriptPreviewLastText = null;
let runnerOutputPresentationMode = null;
let runnerOutputTextView = null;
let runnerViewMode = "signals";
let runnerContentMode = "script";
let runnerOutputJumpMarker = null;
let runnerOutputLastMarkerKey = null;
let runnerOutputReturnTimer = null;
let runnerOutputReturnMouseDownGeneration = null;
let runnerMouseDownGeneration = 0;
let runnerLastObservedMouseDownEventNumber = null;
let runnerOutputButtonImageMode = null;
let cpuPauseButtonImageMode = null;
let waitPauseButtonImageMode = null;
let runnerAutoButtonAppearanceMode = null;
let runnerStatusImageMode = null;
let runnerSentinelDetected = false;
let runnerLEDHovering = false;
let lastRunnerSentinelCheckAt = 0;
let messagesCommandCursorRowID = null;
let messagesCommandChatID = null;
let lastMessagesCommandPollAt = 0;
let messagesCommandLastError = "";
let messagesCommandProcessedGUIDs = [];
let lastMessagesChatResolveAt = 0;
let recentUIMessageTexts = [];
let messageDetectionLogEntries = [];
let messageDetectionLogUI = null;
let messageDetectionLogMainViews = [];
let messageDetectionLogExpanded = false;
let messageDetectionLogActiveHeight = 0;
let messageDetectionLogCollapsedWindowFrame = null;
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
const MESSAGES_DATABASE_PATH = HOME_DIRECTORY + "/Library/Messages/chat.db";
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
        cpuGraphRangePercent: CPU_GRAPH_RANGE_DEFAULT_PERCENT,
        lowCPUCountdownSeconds: CPU_TIMEOUT_DEFAULT_SECONDS,
        waitSignalTimeoutSeconds: WAIT_TIMEOUT_DEFAULT_SECONDS,
        cpuSignalActive: false,
        waitSignalActive: false,
        waitRestartPrompt: WAIT_RESTART_PROMPT_DEFAULT,
        processedMessageGUIDs: [],
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
            selectedLogPath: defaultRunnerLogPath(DEFAULT_RUN_SCRIPT_PATH),
            sandbox: true,
            selfTestRequired: true,
            autoMode: false
        }
    };
}

function defaultRunnerLogPath(scriptPath) {
    const directory = String(ObjC.unwrap($(scriptPath).stringByDeletingLastPathComponent));
    return String(ObjC.unwrap(
        $(directory + "/output/run-current.log").stringByStandardizingPath
    ));
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
    configuration.cpuGraphRangePercent = Math.max(
        configuration.cpuThresholdPercent,
        validatedNumber(
            rawConfiguration.cpuGraphRangePercent,
            CPU_GRAPH_RANGE_MIN_PERCENT,
            CPU_GRAPH_RANGE_MAX_PERCENT,
            configuration.cpuGraphRangePercent
        )
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
    configuration.waitRestartPrompt = validatedString(
        rawConfiguration.waitRestartPrompt,
        configuration.waitRestartPrompt,
        100000,
        false
    );
    configuration.activePromptSentinel = validatedActivePromptSentinel(
        rawConfiguration.activePromptSentinel
    );
    if (Array.isArray(rawConfiguration.processedMessageGUIDs)) {
        configuration.processedMessageGUIDs = rawConfiguration.processedMessageGUIDs
            .filter(value => typeof value === "string" && value.length <= 200)
            .slice(-MESSAGES_PROCESSED_GUID_LIMIT);
    }

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
        configuration.runner.selectedLogPath = validatedString(
            runner.selectedLogPath,
            defaultRunnerLogPath(configuration.runner.selectedScriptPath),
            4096,
            false
        );
        configuration.runner.sandbox = validatedBoolean(
            runner.sandbox,
            configuration.runner.sandbox
        );
        configuration.runner.selfTestRequired = validatedBoolean(
            runner.selfTestRequired,
            configuration.runner.selfTestRequired
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
        smoothingWindowSeconds: cpuSliderPreview
            ? Number(monitorState.committedSmoothingWindowSeconds)
            : Number(ui.averageWindowSlider.doubleValue),
        cpuThresholdPercent: cpuSliderPreview
            ? Number(monitorState.committedCPUThresholdPercent)
            : Number(ui.cpuThresholdSlider.doubleValue),
        cpuGraphRangePercent: Number(monitorState.cpuGraphRangePercent),
        lowCPUCountdownSeconds: Number(ui.cpuDurationSlider.doubleValue),
        waitSignalTimeoutSeconds: Number(ui.waitSlider.doubleValue),
        cpuSignalActive: cpuSignalIsEnabled(),
        waitSignalActive: waitSignalIsEnabled(),
        waitRestartPrompt: stringValue(ui.waitRestartPromptField),
        postExecutionWaitSeconds: Number(ui.runnerWaitSlider.doubleValue),
        activePromptSentinel,
        processedMessageGUIDs: messagesCommandProcessedGUIDs.slice(
            -MESSAGES_PROCESSED_GUID_LIMIT
        ),
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
            selectedLogPath: runnerSelectedLogPath,
            sandbox: Number(ui.runnerSandboxButton.state) === Number($.NSControlStateValueOn),
            selfTestRequired: Number(ui.runnerSelfTestRequiredButton.state) ===
                Number($.NSControlStateValueOn),
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
    if (!monitorState || runnerOperationInProgress() || signalAnimation ||
        perplexityRestart || restartPromptDelivery) {
        return false;
    }

    const previousSelfTestStatus = runnerSelfTestStatus;
    const previousValidatedConfiguration = runnerValidatedConfiguration;
    const configuration = validateConfiguration(rawConfiguration);
    const ui = monitorState.ui;
    const autoModeWasEnabled = Number(ui.runnerAutoButton.state) ===
        Number($.NSControlStateValueOn);
    const graphRange = clamp(
        Math.max(configuration.cpuGraphRangePercent, configuration.cpuThresholdPercent),
        CPU_GRAPH_RANGE_MIN_PERCENT,
        CPU_GRAPH_RANGE_MAX_PERCENT
    );
    monitorState.cpuGraphRangePercent = graphRange;
    ui.cpuThresholdSlider.setMaxValue(graphRange);
    ui.thresholdMaximumLabel.setStringValue(`${Number(graphRange.toFixed(2))}%`);
    ui.averageWindowSlider.setDoubleValue(configuration.smoothingWindowSeconds);
    ui.cpuThresholdSlider.setDoubleValue(configuration.cpuThresholdPercent);
    ui.cpuDurationSlider.setDoubleValue(configuration.lowCPUCountdownSeconds);
    ui.waitSlider.setDoubleValue(configuration.waitSignalTimeoutSeconds);
    setCPUSignalEnabled(configuration.cpuSignalActive);
    setWaitSignalEnabled(configuration.waitSignalActive);
    ui.waitRestartPromptField.setStringValue(configuration.waitRestartPrompt);
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
    runnerSelectedLogPath = configuration.runner.selectedLogPath;
    ui.runnerSelectedLogPathLabel.setStringValue(runnerSelectedLogPath);
    clearRunnerExecutionPreview();
    ui.runnerSandboxButton.setState(
        configuration.runner.sandbox
            ? $.NSControlStateValueOn
            : $.NSControlStateValueOff
    );
    ui.runnerSelfTestRequiredButton.setState(
        configuration.runner.selfTestRequired
            ? $.NSControlStateValueOn
            : $.NSControlStateValueOff
    );
    ui.runnerAutoButton.setState(
        configuration.runner.autoMode
            ? $.NSControlStateValueOn
            : $.NSControlStateValueOff
    );
    for (const guid of configuration.processedMessageGUIDs) {
        if (messagesCommandProcessedGUIDs.indexOf(guid) < 0) {
            messagesCommandProcessedGUIDs.push(guid);
        }
    }
    messagesCommandProcessedGUIDs = messagesCommandProcessedGUIDs.slice(
        -MESSAGES_PROCESSED_GUID_LIMIT
    );
    runnerPathDirectoryAvailable = runnerPathDirectoryExists();
    runnerReady = runnerPathDirectoryAvailable && runnerFileExists();
    runnerAutoTriggeredForPresence = false;
    const fingerprint = runnerConfigurationFingerprint();
    if (runnerAcknowledgedSelfTestConfiguration !== fingerprint) {
        runnerAcknowledgedSelfTestConfiguration = null;
    }
    const validationRemainsCurrent = previousSelfTestStatus === "passed" &&
        previousValidatedConfiguration === fingerprint;
    runnerSelfTestStatus = validationRemainsCurrent ? "passed" : "unverified";
    runnerValidatedConfiguration = validationRemainsCurrent ? fingerprint : null;
    runnerTaskConfiguration = null;
    setRunnerOutputVisible(false);
    resetAllProgress();
    cpuSliderPreview = null;
    stopCPUGraphTransition();
    graphMousePressed = false;
    graphWindowBeforeMouseDown = null;
    graphMouseDownX = null;
    commitCPUControlValues();

    const autoModeTransitionedOff = autoModeWasEnabled &&
        !configuration.runner.autoMode;
    if (autoModeTransitionedOff) {
        disableSignalSources(ui);
    }
    const autoDisabled = disableAutoModeForExistingRunScript(ui, true);
    if (autoDisabled || autoModeTransitionedOff) {
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
    if (runnerOperationInProgress() || signalAnimation || perplexityRestart ||
        restartPromptDelivery) {
        return;
    }
    applyConfigurationToUI(loadConfiguration());
}

function resetDefaultConfiguration() {
    if (runnerOperationInProgress() || signalAnimation || perplexityRestart ||
        restartPromptDelivery) {
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

function cyclePromptSentinelAfterPerplexityRestart() {
    const scriptText = readTextFile(runnerSelectedScriptPath, true);
    if (scriptContainsPromptSentinel(scriptText, activePromptSentinel)) {
        return {
            cycled: false,
            message: "Sentinel token preserved because the watched script still contains it."
        };
    }

    const previousSentinel = activePromptSentinel;
    let nextSentinel = generateRandomPromptSentinel();
    while (nextSentinel === previousSentinel) {
        nextSentinel = generateRandomPromptSentinel();
    }
    activePromptSentinel = nextSentinel;
    if (!saveConfigurationNow()) {
        activePromptSentinel = previousSentinel;
        configurationDirty = true;
        throw new Error(configurationSaveFailureMessage());
    }
    return {
        cycled: true,
        message: "Sentinel token rotated after the successful Perplexity restart."
    };
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

function capturedCommandResult(launchPath, argumentsList) {
    const task = $.NSTask.alloc.init;
    const outputPipe = $.NSPipe.pipe;
    const errorPipe = $.NSPipe.pipe;
    task.setLaunchPath(launchPath);
    task.setArguments(argumentsList);
    task.setStandardOutput(outputPipe);
    task.setStandardError(errorPipe);
    task.launch;
    const outputData = outputPipe.fileHandleForReading.readDataToEndOfFile;
    const errorData = errorPipe.fileHandleForReading.readDataToEndOfFile;
    task.waitUntilExit;
    function decode(data) {
        if (objcObjectIsNil(data)) {
            return "";
        }
        const text = $.NSString.alloc.initWithDataEncoding(data, $.NSUTF8StringEncoding);
        return objcObjectIsNil(text) ? "" : String(ObjC.unwrap(text));
    }
    return {
        status: Number(task.terminationStatus),
        output: decode(outputData),
        error: decode(errorData).trim()
    };
}

function messagesDatabaseRows(query) {
    const result = capturedCommandResult("/usr/bin/sqlite3", [
        "-readonly",
        MESSAGES_DATABASE_PATH,
        "-json",
        query
    ]);
    if (result.status !== 0) {
        throw new Error(
            result.error ||
            "Could not read the Messages database. Full Disk Access may be required."
        );
    }
    try {
        return result.output.trim() ? JSON.parse(result.output) : [];
    } catch (error) {
        throw new Error(`Could not parse Messages database output: ${error}`);
    }
}

function latestMessagesRowID() {
    const rows = messagesDatabaseRows(
        "SELECT COALESCE(MAX(ROWID), 0) AS row_id FROM message;"
    );
    return rows.length > 0 ? Number(rows[0].row_id) : 0;
}

function dataFromHexString(hex) {
    const length = Math.floor(String(hex).length / 2);
    if (length <= 0) {
        return null;
    }
    const pointer = $.malloc(length);
    try {
        for (let index = 0; index < length; index += 1) {
            pointer[index] = parseInt(String(hex).slice(index * 2, index * 2 + 2), 16);
        }
        return $.NSData.dataWithBytesLength(pointer, length);
    } finally {
        $.free(pointer);
    }
}

function unarchiveMessageAttributedBody(hex) {
    const data = dataFromHexString(hex);
    if (objcObjectIsNil(data)) {
        return null;
    }
    for (const unarchive of [
        value => $.NSUnarchiver.unarchiveObjectWithData(value),
        value => $.NSKeyedUnarchiver.unarchiveObjectWithData(value)
    ]) {
        try {
            const object = unarchive(data);
            if (objcObjectIsNil(object)) {
                continue;
            }
            if (!objcObjectIsNil(object.string)) {
                return String(ObjC.unwrap(object.string));
            }
            const value = ObjC.unwrap(object);
            if (typeof value === "string") {
                return value;
            }
        } catch (error) {
            // Try the next archive decoder, then the conservative ASCII fallback.
        }
    }

    return null;
}

function messageTextFromDatabaseRow(row) {
    if (typeof row.text === "string" && row.text.length > 0) {
        return row.text;
    }
    const attributedText = typeof row.attributed_hex === "string" &&
        row.attributed_hex.length > 0
        ? unarchiveMessageAttributedBody(row.attributed_hex)
        : null;
    return attributedText !== null
        ? attributedText
        : typeof row.text === "string" ? row.text : null;
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
    const snapshotText = readTextFile(orphan.snapshotPath, true);
    if (snapshotText !== null) {
        runnerExecutionPreviewPath = orphan.snapshotPath;
        runnerExecutionPreviewText = snapshotText;
        runnerExecutionDiagnosticName = String(ObjC.unwrap(
            $(orphan.snapshotPath).lastPathComponent
        ));
        runnerScriptPreviewLastText = null;
    }
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

function configuredRunnerSelfTestRequired() {
    return !monitorState || !monitorState.ui.runnerSelfTestRequiredButton ||
        Number(monitorState.ui.runnerSelfTestRequiredButton.state) ===
            Number($.NSControlStateValueOn);
}

function runnerStartupSelfTestEnabled() {
    return !runnerCommandLineNoSelfTest &&
        (runnerCommandLineSkipSelfTest || configuredRunnerSelfTestRequired());
}

function runnerSelfTestRequired() {
    return !runnerCommandLineNoSelfTest && !runnerCommandLineSkipSelfTest &&
        configuredRunnerSelfTestRequired();
}

function runnerSelfTestPolicyForStatus() {
    if (runnerCommandLineNoSelfTest) {
        return "DISABLED BY --no-self-test";
    }
    if (runnerCommandLineSkipSelfTest) {
        return "STARTUP ONLY · --skip-self-test";
    }
    return configuredRunnerSelfTestRequired() ? "REQUIRED" : "OPTIONAL";
}

function runnerExecutionAllowed() {
    const fingerprint = runnerConfigurationFingerprint();
    return !sandboxIsEnabled() || !runnerSelfTestRequired() ||
        runnerAcknowledgedSelfTestConfiguration === fingerprint || (
            runnerSelfTestStatus === "passed" &&
            runnerValidatedConfiguration === fingerprint
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
    const changed = cpuSignalIsEnabled() || waitSignalIsEnabled();
    if (monitorState) {
        setCPUSignalEnabled(false);
        setWaitSignalEnabled(false);
        monitorState.trailingLowCPUSeconds = 0;
    }
    return changed;
}

function disableRunnerAutoMode(ui) {
    const autoModeWasEnabled = Number(ui.runnerAutoButton.state) ===
        Number($.NSControlStateValueOn);
    ui.runnerAutoButton.setState($.NSControlStateValueOff);
    runnerAutoTriggeredForPresence = false;
    if (autoModeWasEnabled) {
        disableSignalSources(ui);
    }
    return autoModeWasEnabled;
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
    return runnerViewMode === "runner";
}

function runnerDisplayedLogPath() {
    return runnerTaskMode === "selftest"
        ? RUNNER_OUTPUT_PATH
        : runnerSelectedLogPath;
}

function cancelRunnerOutputReturn() {
    if (runnerOutputReturnTimer) {
        runnerOutputReturnTimer.invalidate;
        runnerOutputReturnTimer = null;
    }
    runnerOutputReturnMouseDownGeneration = null;
}

function scheduleRunnerOutputReturn() {
    cancelRunnerOutputReturn();
    runnerOutputReturnMouseDownGeneration = runnerMouseDownGeneration;
    runnerOutputReturnTimer = $.NSTimer.timerWithTimeIntervalTargetSelectorUserInfoRepeats(
        2,
        monitorController,
        "returnToRunnerOutput:",
        null,
        false
    );
    $.NSRunLoop.mainRunLoop.addTimerForMode(
        runnerOutputReturnTimer,
        $.NSRunLoopCommonModes
    );
}

function observeCurrentMouseDownEvent() {
    const event = $.NSApplication.sharedApplication.currentEvent;
    if (objcObjectIsNil(event)) {
        return;
    }
    const type = Number(event.type);
    if ([
        Number($.NSEventTypeLeftMouseDown),
        Number($.NSEventTypeRightMouseDown),
        Number($.NSEventTypeOtherMouseDown)
    ].indexOf(type) < 0) {
        return;
    }
    const eventNumber = Number(event.eventNumber);
    if (eventNumber !== runnerLastObservedMouseDownEventNumber) {
        runnerLastObservedMouseDownEventNumber = eventNumber;
        runnerMouseDownGeneration += 1;
    }
}

function setRunnerOutputText(text, scrollToEnd, targetRange) {
    if (!runnerOutputTextView) {
        return;
    }
    runnerOutputTextView.setString(text);
    if (targetRange) {
        runnerOutputTextView.setSelectedRange(targetRange);
        runnerOutputTextView.scrollRangeToVisible(
            $.NSMakeRange(Number(targetRange.location), 0)
        );
        scheduleRunnerOutputReturn();
        return;
    }
    cancelRunnerOutputReturn();
    runnerOutputTextView.setSelectedRange($.NSMakeRange(0, 0));
    runnerOutputTextView.scrollRangeToVisible(
        $.NSMakeRange(scrollToEnd ? text.length : 0, 0)
    );
}

function clearRunnerExecutionPreview() {
    runnerExecutionPreviewPath = null;
    runnerExecutionPreviewText = null;
    runnerExecutionDiagnosticName = null;
    runnerScriptPreviewLastText = null;
}

function runnerScriptPreviewPath() {
    return runnerExecutionPreviewPath || runnerSelectedScriptPath;
}

function pollRunnerScriptPreview(now, force) {
    if (!force && now - runnerScriptPreviewLastPollAt < 250) {
        return;
    }
    runnerScriptPreviewLastPollAt = now;

    const previewPath = runnerScriptPreviewPath();
    const script = runnerExecutionPreviewText !== null
        ? runnerExecutionPreviewText
        : readTextFile(previewPath, true);
    const displayText = script === null
        ? `[Could not read watched script: ${previewPath}]`
        : script;
    if (!force && displayText === runnerScriptPreviewLastText &&
        runnerOutputPresentationMode === "script") {
        return;
    }
    runnerScriptPreviewLastText = displayText;
    runnerOutputPresentationMode = "script";
    const sourceRange = runnerOutputJumpMarker
        ? textRangeForLineNumber(displayText, runnerOutputJumpMarker.sourceLine)
        : null;
    setRunnerOutputText(displayText, false, sourceRange);
}

function updateRunnerViewChrome() {
    if (!monitorState || !monitorState.ui.runnerOutputCard) {
        return;
    }
    const ui = monitorState.ui;
    setRunnerOutputButtonPresentation(ui.runnerOutputButton, runnerViewMode);
    ui.runnerOutputSectionTitle.setStringValue(
        runnerContentMode === "script"
            ? runnerExecutionPreviewText !== null
                ? "EXECUTION SCRIPT COPY"
                : "WATCHED RUN SCRIPT"
            : "RUN LOG"
    );
    ui.runnerOutputSectionTitle.setToolTip(
        runnerContentMode === "script" ? runnerScriptPreviewPath() : runnerDisplayedLogPath()
    );
    ui.runnerContentToggleButton.setTitle(
        runnerContentMode === "script" ? "Show log" : "Show script"
    );
    ui.runnerContentToggleButton.setToolTip(
        runnerContentMode === "script"
            ? `Show the run log at ${runnerDisplayedLogPath()}.`
            : `Show the script at ${runnerScriptPreviewPath()}.`
    );
}

function updateRunnerOutputPresentation(now, force) {
    if (!monitorState || !monitorState.ui.runnerOutputCard) {
        return;
    }
    updateRunnerViewChrome();
    if (!runnerOutputIsVisible()) {
        return;
    }
    if (runnerContentMode === "script") {
        pollRunnerScriptPreview(now, force);
    } else {
        pollRunnerOutput(now, force);
    }
}

function applyRunnerViewVisibility() {
    if (!monitorState || !monitorState.ui.runnerOutputCard) {
        return;
    }
    const contentVisible = runnerOutputIsVisible();
    for (const view of monitorState.ui.signalViews) {
        view.setHidden(contentVisible);
    }
    for (const view of monitorState.ui.runnerOutputViews) {
        view.setHidden(!contentVisible);
    }
}

function setRunnerViewMode(mode, refresh) {
    if (["signals", "runner"].indexOf(mode) < 0) {
        return;
    }
    if (mode !== "signals" && signalAnimation) {
        cancelSignalAnimation();
    }
    runnerViewMode = mode;
    applyRunnerViewVisibility();
    updateRunnerViewChrome();
    if (refresh !== false) {
        updateRunnerOutputPresentation(Date.now(), true);
    }
}

function setRunnerOutputVisible(visible) {
    if (visible) {
        runnerContentMode = "log";
    }
    setRunnerViewMode(visible ? "runner" : "signals", true);
}

function cycleRunnerViewMode() {
    setRunnerViewMode(runnerViewMode === "signals" ? "runner" : "signals", true);
}

function toggleRunnerContentMode() {
    runnerContentMode = runnerContentMode === "script" ? "log" : "script";
    runnerOutputLastPollAt = 0;
    runnerScriptPreviewLastPollAt = 0;
    updateRunnerOutputPresentation(Date.now(), true);
}

function escapeRegularExpression(text) {
    return String(text).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function runnerDiagnosticScriptNames() {
    return [runnerExecutionDiagnosticName || runnerScriptName()];
}

function latestRunnerOutputLineMarker(output, searchStart) {
    const diagnosticNames = runnerDiagnosticScriptNames();
    const scriptNames = diagnosticNames.map(escapeRegularExpression).join("|");
    const pattern = new RegExp(
        `(^|[^A-Za-z0-9_.-])(?:${scriptNames}):(?:[ \\t]+line[ \\t]+)?([0-9]+)(?=[:\\s]|$)`,
        "gm"
    );
    pattern.lastIndex = Math.max(0, Number(searchStart) || 0);
    let latest = null;
    let match;
    while ((match = pattern.exec(output)) !== null) {
        const diagnosticStart = match.index + match[1].length;
        const lineStart = output.lastIndexOf("\n", diagnosticStart) + 1;
        const lineEndIndex = output.indexOf("\n", diagnosticStart);
        const lineEnd = lineEndIndex < 0 ? output.length : lineEndIndex;
        latest = {
            start: lineStart,
            end: lineEnd,
            matchStart: diagnosticStart,
            matchEnd: match.index + match[0].length,
            sourceLine: Number(match[2]),
            key: `${diagnosticStart}:${match[2]}`
        };
    }
    return latest;
}

function runnerOutputDisplay(output) {
    const maximumCharacters = 500000;
    if (output.length <= maximumCharacters) {
        return { text: output, omittedCharacters: 0, prefixLength: 0 };
    }
    const prefix = "[… earlier output omitted …]\n";
    return {
        text: prefix + output.slice(-maximumCharacters),
        omittedCharacters: output.length - maximumCharacters,
        prefixLength: prefix.length
    };
}

function textRangeForLineNumber(text, lineNumber) {
    const targetLine = Math.max(1, Math.floor(Number(lineNumber) || 1));
    let lineStart = 0;
    for (let line = 1; line < targetLine; line += 1) {
        const newline = text.indexOf("\n", lineStart);
        if (newline < 0) {
            return null;
        }
        lineStart = newline + 1;
    }
    const newline = text.indexOf("\n", lineStart);
    let lineEnd = newline < 0 ? text.length : newline;
    if (lineEnd > lineStart && text.charAt(lineEnd - 1) === "\r") {
        lineEnd -= 1;
    }
    return $.NSMakeRange(lineStart, Math.max(0, lineEnd - lineStart));
}

function pollRunnerOutput(now, force) {
    if (!force && now - runnerOutputLastPollAt < 250) {
        return;
    }
    runnerOutputLastPollAt = now;

    const displayedLogPath = runnerDisplayedLogPath();
    const output = readTextFile(displayedLogPath, true) ||
        readTextFile(RUNNER_OUTPUT_PATH, true) || "";
    const previousOutput = runnerOutputLastText;
    const previousOutputLength = previousOutput.length;
    const outputChanged = output !== previousOutput;
    if (outputChanged) {
        const outputWasAppended = output.length >= previousOutputLength &&
            output.indexOf(previousOutput) === 0;
        if (!outputWasAppended) {
            runnerOutputJumpMarker = null;
            runnerOutputLastMarkerKey = null;
        }
        const longestNameLength = runnerDiagnosticScriptNames().reduce(
            (maximum, name) => Math.max(maximum, name.length),
            0
        );
        const searchStart = outputWasAppended
            ? Math.max(0, previousOutputLength - longestNameLength - 32)
            : 0;
        runnerOutputLastText = output;
        const marker = latestRunnerOutputLineMarker(output, searchStart);
        if (marker) {
            const markerIsNew = marker.key !== runnerOutputLastMarkerKey;
            runnerOutputJumpMarker = marker;
            runnerOutputLastMarkerKey = marker.key;
            if (markerIsNew && runnerTask) {
                runnerContentMode = "script";
                setRunnerViewMode("runner", false);
                pollRunnerScriptPreview(now, true);
            }
        }
    }

    if (!runnerOutputIsVisible() || runnerContentMode !== "log" ||
        (!force && !outputChanged && runnerOutputPresentationMode === "output")) {
        return;
    }

    const display = runnerOutputDisplay(output);
    runnerOutputPresentationMode = "output";
    setRunnerOutputText(display.text, true);
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
        if (!Boolean($("").writeToFileAtomicallyEncodingError(
            RUNNER_OUTPUT_PATH,
            true,
            $.NSUTF8StringEncoding,
            undefined
        ))) {
            throw new Error(`Could not clear runner output at ${RUNNER_OUTPUT_PATH}.`);
        }
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
        runnerOutputJumpMarker = null;
        runnerOutputLastMarkerKey = null;
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
    if (runnerCommandLineNoSelfTest) {
        runnerSelfTestStatus = "unverified";
        runnerValidatedConfiguration = null;
        runnerAcknowledgedSelfTestConfiguration = null;
        runnerStatusDetail = "All environment self-tests are disabled by --no-self-test.";
        updateRunnerUI(Date.now());
        return;
    }
    runnerAcknowledgedSelfTestConfiguration = null;
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

function removeSentinelRunScript() {
    const originalPath = runnerSelectedScriptPath;
    const scriptName = runnerScriptName();
    const claimPath = uniqueRunnerStagingPath("sentinel-removal");
    const claimed = $.NSFileManager.defaultManager.moveItemAtPathToPathError(
        originalPath,
        claimPath,
        undefined
    );
    if (!Boolean(claimed)) {
        disableRunnerAutoMode(monitorState.ui);
        runnerStatusDetail = `Could not atomically claim sentinel ${scriptName}; ` +
            "it was left untouched and Auto Mode was disabled.";
        scheduleConfigurationSave();
        return { removed: false, message: runnerStatusDetail };
    }

    const claimedText = readTextFile(claimPath, true);
    if (!scriptContainsPromptSentinel(claimedText, activePromptSentinel)) {
        const recovery = restoreStagedScript(
            claimPath,
            originalPath,
            "The atomically claimed script did not contain the active sentinel."
        );
        disableRunnerAutoMode(monitorState.ui);
        runnerReady = runnerFileExists();
        runnerSentinelDetected = false;
        runnerStatusDetail = recovery.message;
        scheduleConfigurationSave();
        return { removed: false, message: runnerStatusDetail };
    }

    const removed = Boolean(
        $.NSFileManager.defaultManager.removeItemAtPathError(claimPath, undefined)
    );
    if (!removed) {
        const recovery = restoreStagedScript(
            claimPath,
            originalPath,
            `Failed to delete atomically claimed sentinel ${scriptName}.`
        );
        disableRunnerAutoMode(monitorState.ui);
        runnerReady = runnerFileExists();
        runnerStatusDetail = recovery.message;
        scheduleConfigurationSave();
        return { removed: false, message: runnerStatusDetail };
    }

    const replacementExists = runnerFileExists();
    if (replacementExists) {
        disableRunnerAutoMode(monitorState.ui);
    }
    runnerSentinelDetected = false;
    runnerLEDHovering = false;
    runnerReady = replacementExists;
    runnerExistingScriptNotice = false;
    runnerStatusDetail = replacementExists
        ? `Sentinel ${scriptName} deleted; newer work at the watched path was preserved and Auto Mode was disabled.`
        : `Sentinel ${scriptName} deleted; the sentinel token remains unchanged until Perplexity restarts.`;
    scheduleConfigurationSave();
    return { removed: true, message: runnerStatusDetail };
}

function continueFromSentinel(now) {
    if (signalAnimation || perplexityRestart || restartPromptDelivery ||
        runnerTaskIsRunning()) {
        return {
            removed: false,
            message: "Prompt Mixer is currently unavailable; the sentinel was left untouched."
        };
    }
    const removal = removeSentinelRunScript();
    if (!removal.removed) {
        return removal;
    }
    const mixerStarted = startManualPromptAnimation(now);
    return {
        removed: true,
        message: mixerStarted
            ? `${removal.message} Prompt Mixer activated.`
            : `${removal.message} Prompt Mixer could not be activated.`
    };
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

    runnerExecutionPreviewPath = prepared.snapshotPath;
    runnerExecutionPreviewText = prepared.inspectedText;
    runnerExecutionDiagnosticName = String(ObjC.unwrap(
        $(prepared.snapshotPath).lastPathComponent
    ));
    runnerScriptPreviewLastText = null;
    runnerActiveOwnershipToken = ownershipToken;
    runnerAutoTriggeredForPresence = true;
    const runnerArguments = [sandboxArgument()];
    if (runnerCommandLineNoSelfTest) {
        runnerArguments.push("--no-self-test");
    } else if (runnerCommandLineSkipSelfTest) {
        runnerArguments.push("--skip-self-test");
    } else if (!configuredRunnerSelfTestRequired()) {
        runnerArguments.push("--no-self-test");
    }
    runnerArguments.push(
        "--sentinel",
        runnerGuardSentinel,
        "--ui-owner-token",
        ownershipToken,
        "--once",
        "--notify-wait",
        runnerNotifyWait().toFixed(1),
        "--run-log",
        runnerSelectedLogPath,
        "--notifier",
        "/usr/bin/true",
        prepared.snapshotPath
    );
    if (launchRunnerTask("run", runnerArguments)) {
        runnerExecutionOriginalPath = prepared.originalPath;
        runnerExecutionSnapshotPath = prepared.snapshotPath;
        runnerOutputLastText = "";
        runnerOutputLastPollAt = 0;
        pollRunnerOutput(Date.now(), true);
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
        clearRunnerExecutionPreview();
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
        .replace(/\{output\}/g, runnerSelectedLogPath || RUNNER_OUTPUT_PATH);
}

function finishRunnerTask(now) {
    const completedMode = runnerTaskMode;
    const completedConfiguration = runnerTaskConfiguration;
    const status = Number(runnerTask.terminationStatus);
    const wasKilledByUser = runnerKillRequested;
    pollRunnerOutput(now, true);
    const preserveDiagnosticView = Boolean(
        runnerOutputJumpMarker && runnerOutputIsVisible() && runnerContentMode === "script"
    );
    runnerLastExitStatus = status;
    runnerLastCompletedAt = now;
    runnerTask = null;
    runnerTaskMode = null;

    if (!preserveDiagnosticView) {
        setRunnerOutputVisible(false);
    }
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
                : runnerCommandLineSkipSelfTest
                    ? `Environment startup self-test failed with exit code ${status}, but --skip-self-test bypasses the failed intermediate state; see output/run-sandbox-selftest.log.`
                    : `Environment self-test failed with exit code ${status}; click the runner LED to acknowledge and continue, or run Self-test again. See output/run-sandbox-selftest.log.`;
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

function rememberUIMessageText(text) {
    const value = String(text);
    recentUIMessageTexts.push(value);
    if (recentUIMessageTexts.length > 200) {
        recentUIMessageTexts = recentUIMessageTexts.slice(-200);
    }
}

function messageWasSentByUI(text) {
    return recentUIMessageTexts.indexOf(String(text)) >= 0;
}

function messageLooksLikeUIOutput(text) {
    const value = String(text).trim();
    return value.indexOf("Sentinel detected in ") === 0 ||
        value.indexOf("Test from Perplexity signal monitor:") === 0 ||
        value === "(empty)" ||
        /^\[(?:\d+\/\d+|help|status|log|script|prompt|continue|restart|enable (?:cpu|wait|all|both|signals|both signals|auto|automode|auto mode)|disable (?:cpu|wait|all|both|signals|both signals|auto|automode|auto mode)|error)\]/i.test(value);
}

function messageGUIDWasProcessed(guid) {
    return messagesCommandProcessedGUIDs.indexOf(String(guid)) >= 0;
}

function recordProcessedMessageGUID(guid) {
    messagesCommandProcessedGUIDs.push(String(guid));
    if (messagesCommandProcessedGUIDs.length > MESSAGES_PROCESSED_GUID_LIMIT) {
        messagesCommandProcessedGUIDs = messagesCommandProcessedGUIDs.slice(
            -MESSAGES_PROCESSED_GUID_LIMIT
        );
    }
    configurationDirty = true;
    return saveConfigurationNow();
}

function sendIMessageText(messageText) {
    const script = [
        "on run argv",
        "set recipientHandle to item 1 of argv",
        "set messageText to item 2 of argv",
        "tell application \"Messages\"",
        "set targetService to first service whose service type = iMessage",
        "set targetBuddy to buddy recipientHandle of targetService",
        "send messageText to targetBuddy",
        "end tell",
        "end run"
    ].join("\n");
    const errorPipe = $.NSPipe.pipe;
    const task = $.NSTask.alloc.init;
    task.setLaunchPath("/usr/bin/osascript");
    task.setArguments([
        "-e",
        script,
        SENTINEL_IMESSAGE_RECIPIENT,
        String(messageText)
    ]);
    task.setStandardOutput($.NSFileHandle.fileHandleWithNullDevice);
    task.setStandardError(errorPipe);
    task.launch;
    task.waitUntilExit;
    if (Number(task.terminationStatus) !== 0) {
        const data = errorPipe.fileHandleForReading.readDataToEndOfFile;
        const errorText = objcObjectIsNil(data)
            ? null
            : $.NSString.alloc.initWithDataEncoding(data, $.NSUTF8StringEncoding);
        const text = objcObjectIsNil(errorText)
            ? "unknown Messages error"
            : String(ObjC.unwrap(errorText)).trim();
        throw new Error(text || "Messages rejected the message.");
    }
    rememberUIMessageText(messageText);
}

function utf16SafePrefix(value, maximumLength) {
    let end = Math.min(String(value).length, Math.max(0, Math.floor(maximumLength)));
    if (end > 0 && end < value.length) {
        const finalCodeUnit = value.charCodeAt(end - 1);
        const nextCodeUnit = value.charCodeAt(end);
        if (finalCodeUnit >= 0xd800 && finalCodeUnit <= 0xdbff &&
            nextCodeUnit >= 0xdc00 && nextCodeUnit <= 0xdfff) {
            end -= 1;
        }
    }
    return value.slice(0, end);
}

function utf16SafeSuffix(value, maximumLength) {
    const text = String(value);
    let start = Math.max(0, text.length - Math.max(0, Math.floor(maximumLength)));
    if (start > 0 && start < text.length) {
        const previousCodeUnit = text.charCodeAt(start - 1);
        const firstCodeUnit = text.charCodeAt(start);
        if (previousCodeUnit >= 0xd800 && previousCodeUnit <= 0xdbff &&
            firstCodeUnit >= 0xdc00 && firstCodeUnit <= 0xdfff) {
            start += 1;
        }
    }
    return text.slice(start);
}

function middleElidedText(value, maximumLength) {
    const text = String(value);
    const limit = Math.max(0, Math.floor(maximumLength));
    if (text.length <= limit) {
        return text;
    }
    const marker = "\n\n… middle omitted …\n\n";
    if (limit <= marker.length) {
        return utf16SafePrefix(text, limit);
    }

    const availableLength = limit - marker.length;
    const prefixBudget = Math.ceil(availableLength / 2);
    const suffixBudget = availableLength - prefixBudget;
    let prefix = utf16SafePrefix(text, prefixBudget);
    let suffix = utf16SafeSuffix(text, suffixBudget);

    const prefixLineEnd = prefix.lastIndexOf("\n");
    if (prefixLineEnd >= Math.floor(prefix.length * 0.7)) {
        prefix = prefix.slice(0, prefixLineEnd);
    }
    const suffixLineStart = suffix.indexOf("\n");
    if (suffixLineStart >= 0 && suffixLineStart <= Math.ceil(suffix.length * 0.3)) {
        suffix = suffix.slice(suffixLineStart + 1);
    }
    return prefix + marker + suffix;
}

function sendIMessageChunks(text) {
    const value = String(text);
    if (!value) {
        sendIMessageText("(empty)");
        return;
    }
    const chunks = [];
    const bodyLimit = IMESSAGE_CHUNK_CHARACTERS - 32;
    let offset = 0;
    while (offset < value.length) {
        let end = Math.min(value.length, offset + bodyLimit);
        if (end < value.length) {
            const finalCodeUnit = value.charCodeAt(end - 1);
            const nextCodeUnit = value.charCodeAt(end);
            if (finalCodeUnit >= 0xd800 && finalCodeUnit <= 0xdbff &&
                nextCodeUnit >= 0xdc00 && nextCodeUnit <= 0xdfff) {
                end -= 1;
            }
        }
        chunks.push(value.slice(offset, end));
        offset = end;
    }
    for (let index = 0; index < chunks.length; index += 1) {
        const prefix = chunks.length > 1 ? `[${index + 1}/${chunks.length}]\n` : "";
        sendIMessageText(prefix + chunks[index]);
    }
}

function sentinelNotificationText() {
    return `Sentinel detected in ${runnerScriptName()} at ${runnerSelectedScriptPath}.\n` +
        "Auto Mode will not execute it. Reply with one command per line:\n" +
        "help\nstatus\nlog\nscript\nprompt <text>\ncontinue\nrestart\n" +
        "enable cpu [signal]\ndisable cpu [signal]\n" +
        "enable wait [signal]\ndisable wait [signal]\n" +
        "enable|disable both|signals\n" +
        "enable|disable auto|automode|auto mode\n" +
        "enable|disable all";
}

function notifySentinelTransition() {
    try {
        sendIMessageText(sentinelNotificationText());
        runnerStatusDetail += ` iMessage sent to ${SENTINEL_IMESSAGE_RECIPIENT}.`;
    } catch (error) {
        runnerStatusDetail += ` Sentinel iMessage failed: ${error}`;
    }
}

function sqlStringLiteral(value) {
    return `'${String(value).replace(/'/g, "''")}'`;
}

function messagesChatIDForRecipient() {
    const recipient = sqlStringLiteral(MESSAGES_COMMAND_HANDLE);
    const rows = messagesDatabaseRows(
        "SELECT chj.chat_id AS chat_id FROM handle AS h " +
        "JOIN chat_handle_join AS chj ON chj.handle_id = h.ROWID " +
        "JOIN chat AS c ON c.ROWID = chj.chat_id " +
        `WHERE h.id = ${recipient} AND c.chat_identifier = ${recipient} ` +
        "AND c.service_name = 'iMessage' " +
        "AND (SELECT COUNT(*) FROM chat_handle_join AS members " +
        "WHERE members.chat_id = c.ROWID) = 1 " +
        "ORDER BY c.ROWID DESC LIMIT 1;"
    );
    return rows.length > 0 ? Number(rows[0].chat_id) : null;
}

function messagesRowsAfter(rowID, chatID) {
    const safeRowID = Math.max(0, Math.floor(Number(rowID) || 0));
    const chatFilter = chatID === null || chatID === undefined
        ? ""
        : ` AND cmj.chat_id = ${Math.max(0, Math.floor(Number(chatID) || 0))}`;
    return messagesDatabaseRows(
        "SELECT m.ROWID AS row_id, m.guid AS guid, cmj.chat_id AS chat_id, " +
        "m.text AS text, hex(m.attributedBody) AS attributed_hex, m.is_from_me AS is_from_me, " +
        "m.item_type AS item_type, m.associated_message_type AS associated_message_type, " +
        "m.associated_message_guid AS associated_message_guid, m.service AS service " +
        "FROM message AS m JOIN chat_message_join AS cmj ON cmj.message_id = m.ROWID " +
        `WHERE m.ROWID > ${safeRowID}${chatFilter} ` +
        "ORDER BY m.ROWID ASC LIMIT 500;"
    );
}

function sendCommandReply(command, body) {
    sendIMessageChunks(`[${command}]\n${String(body)}`);
}

function sendBoundedCommandReply(command, body) {
    const prefix = `[${command}]\n`;
    const bodyLimit = Math.max(0, IMESSAGE_CHUNK_CHARACTERS - prefix.length);
    sendIMessageText(prefix + middleElidedText(body, bodyLimit));
}

function latestRunnerScriptLogText() {
    return readTextFile(runnerSelectedLogPath, true) ||
        readTextFile(RUNNER_OUTPUT_PATH, true) ||
        runnerOutputLastText ||
        "";
}

function latestRunnerLogLines(limit) {
    return latestRunnerScriptLogText()
        .replace(/\r\n?/g, "\n")
        .split("\n")
        .filter(line => line.trim() !== "")
        .slice(-limit);
}

function runnerScriptSummaryLines(scriptText, maximumLines) {
    if (typeof scriptText !== "string" || !scriptText.trim()) {
        return [];
    }
    const lines = scriptText.replace(/\r\n?/g, "\n").split("\n");
    const limit = Math.max(0, Math.floor(maximumLines));
    if (limit === 0) {
        return [];
    }
    for (let index = 0; index < Math.min(lines.length, 40); index += 1) {
        const match = lines[index].match(
            /^\s*cat(?:\s+[^<\s]+)*\s+<<-?\s*['"]?([A-Za-z_][A-Za-z0-9_]*)['"]?/
        );
        if (!match) {
            continue;
        }
        const delimiter = match[1];
        const summary = [];
        for (let lineIndex = index + 1; lineIndex < lines.length; lineIndex += 1) {
            if (lines[lineIndex].trim() === delimiter) {
                break;
            }
            if (lines[lineIndex].trim()) {
                summary.push(lines[lineIndex].trim());
                if (summary.length >= limit) {
                    return summary;
                }
            }
        }
        if (summary.length > 0) {
            return summary;
        }
    }

    const labeledLine = lines.findIndex((line, index) =>
        index < 80 && /^(?:\s*#\s*)?(?:TITLE|SUMMARY|STRUCTURE|GOAL|OBJECTIVE|PURPOSE|ESTIMATE)\s*:/i.test(line)
    );
    if (labeledLine >= 0) {
        return lines.slice(labeledLine, labeledLine + limit)
            .map(line => line.replace(/^\s*#\s?/, "").trim())
            .filter(Boolean)
            .slice(0, limit);
    }

    const echoedSummary = lines.slice(1, 40)
        .map(line => line.match(/^\s*echo\s+(["'])(.*)\1\s*$/))
        .filter(Boolean)
        .map(match => match[2].trim())
        .filter(Boolean);
    if (echoedSummary.length >= 2) {
        return echoedSummary.slice(0, limit);
    }

    return lines.slice(1, 30)
        .filter(line => /^\s*#(?!\!)/.test(line))
        .map(line => line.replace(/^\s*#\s?/, "").trim())
        .filter(Boolean)
        .slice(0, limit);
}

function latestRunnerScriptTextForMessage() {
    const currentScript = readTextFile(runnerSelectedScriptPath, true);
    return currentScript !== null ? currentScript : runnerExecutionPreviewText;
}

function runnerStatusForMessage() {
    const autoMode = runnerAutoModeEnabled() ? "ON" : "OFF";
    const state = runnerDisplayState().toUpperCase();
    const selfTestMode = runnerSelfTestPolicyForStatus();
    const acknowledged = runnerAcknowledgedSelfTestConfiguration ===
        runnerConfigurationFingerprint();
    const selfTestState = runnerSelfTestStatus.toUpperCase() +
        (acknowledged ? " · ACKNOWLEDGED" : "");
    const running = runnerTaskIsRunning();
    const executionTime = running ? runnerTaskStartedAt : runnerLastCompletedAt;
    const timeText = executionTime ? new Date(executionTime).toISOString() : "unavailable";
    const returnCode = running
        ? "running"
        : runnerLastExitStatus === null
            ? "unavailable"
            : String(runnerLastExitStatus);
    const summaryLines = runnerScriptSummaryLines(
        latestRunnerScriptTextForMessage(),
        3
    );
    const summaryText = summaryLines.length > 0
        ? summaryLines.join("\n")
        : "unavailable";
    const logLines = latestRunnerLogLines(2);
    const logText = logLines.length > 0 ? logLines.join("\n") : "unavailable";
    const detail = runnerStatusDetail ? `\n${runnerStatusDetail}` : "";
    return `Auto Mode: ${autoMode}\nRunner state: ${state}\n` +
        `Self-test: ${selfTestMode} · ${selfTestState}\n` +
        `Script summary:\n${summaryText}\n` +
        `Latest run time: ${timeText}\nReturn code: ${returnCode}\n` +
        `Latest log:\n${logText}${detail}`;
}

function latestRunnerLogForMessage() {
    const output = latestRunnerScriptLogText().replace(/\r\n?/g, "\n");
    return output
        ? output
        : "No runner output is available.";
}

function latestRunnerScriptForMessage() {
    const script = latestRunnerScriptTextForMessage();
    return script === null || script === ""
        ? `No run script is available at ${runnerSelectedScriptPath}.`
        : script;
}

function enableCPUSignalFromMessage() {
    if (perplexityRestart || restartPromptDelivery || signalAnimation) {
        return "CPU signal activation is currently unavailable.";
    }
    const wasEnabled = cpuSignalIsEnabled();
    setCPUSignalEnabled(true);
    scheduleConfigurationSave();
    updateSignalAnimationControls();
    return wasEnabled ? "CPU signal was already enabled." : "CPU signal enabled.";
}

function disableCPUSignalFromMessage() {
    if (perplexityRestart || restartPromptDelivery || signalAnimation) {
        return "CPU signal deactivation is currently unavailable.";
    }
    const wasEnabled = cpuSignalIsEnabled();
    setCPUSignalEnabled(false);
    monitorState.trailingLowCPUSeconds = 0;
    scheduleConfigurationSave();
    return wasEnabled ? "CPU signal disabled." : "CPU signal was already disabled.";
}

function enableWaitSignalFromMessage() {
    if (perplexityRestart || restartPromptDelivery || signalAnimation) {
        return "Wait signal activation is currently unavailable.";
    }
    const wasEnabled = waitSignalIsEnabled();
    if (!wasEnabled) {
        setWaitSignalEnabled(true);
        scheduleConfigurationSave();
    }
    return wasEnabled ? "Wait signal was already enabled." : "Wait signal enabled.";
}

function disableWaitSignalFromMessage() {
    if (perplexityRestart || restartPromptDelivery || signalAnimation) {
        return "Wait signal deactivation is currently unavailable.";
    }
    const wasEnabled = waitSignalIsEnabled();
    if (wasEnabled) {
        setWaitSignalEnabled(false);
        scheduleConfigurationSave();
    }
    return wasEnabled ? "Wait signal disabled." : "Wait signal was already disabled.";
}

function setBothSignalsFromMessage(enabled) {
    const cpuResult = enabled
        ? enableCPUSignalFromMessage()
        : disableCPUSignalFromMessage();
    const waitResult = enabled
        ? enableWaitSignalFromMessage()
        : disableWaitSignalFromMessage();
    return `${cpuResult}\n${waitResult}`;
}

function setRunnerAutoModeFromMessage(enabled) {
    if (perplexityRestart || restartPromptDelivery || signalAnimation || orphanedRunner) {
        return "Runner Auto Mode change is currently unavailable.";
    }
    const ui = monitorState.ui;
    const wasEnabled = runnerAutoModeEnabled();
    ui.runnerAutoButton.setState(
        enabled ? $.NSControlStateValueOn : $.NSControlStateValueOff
    );
    runnerAutoTriggeredForPresence = false;
    refreshRunnerPresence(Date.now(), true);
    scheduleConfigurationSave();
    updateRunnerUI(Date.now());
    if (enabled && !runnerTaskIsRunning() && runnerExecutionAllowed() && runnerReady) {
        startOneShotRunner();
    }
    if (wasEnabled === enabled) {
        return `Runner Auto Mode was already ${enabled ? "enabled" : "disabled"}.`;
    }
    return `Runner Auto Mode ${enabled ? "enabled" : "disabled"}.`;
}

function messagesCommandHelp() {
    return [
        "help",
        "status",
        "log",
        "script",
        "prompt <text>",
        "continue",
        "restart",
        "enable|disable cpu [signal]",
        "enable|disable wait [signal]",
        "enable|disable both|signals",
        "enable|disable auto|automode|auto mode",
        "enable|disable all"
    ].join("\n");
}

function executeMessagesCommand(line, now) {
    const trimmed = String(line).trim();
    if (!trimmed) {
        return;
    }
    const separator = trimmed.search(/[\s:]/);
    const command = (separator < 0 ? trimmed : trimmed.slice(0, separator)).toLowerCase();
    const argument = separator < 0
        ? ""
        : trimmed.slice(separator + 1).replace(/^\s+/, "");
    try {
        if (command === "help" && !argument) {
            sendCommandReply("help", messagesCommandHelp());
        } else if (command === "status" && !argument) {
            sendCommandReply("status", runnerStatusForMessage());
        } else if (command === "log" && !argument) {
            sendBoundedCommandReply("log", latestRunnerLogForMessage());
        } else if (command === "script" && !argument) {
            sendBoundedCommandReply("script", latestRunnerScriptForMessage());
        } else if (command === "prompt" && argument) {
            if (perplexityRestart || restartPromptDelivery || signalAnimation) {
                sendCommandReply("prompt", "Prompting is currently unavailable.");
            } else {
                sendPrompt(argument);
                sendCommandReply("prompt", "Prompt submitted to Perplexity.");
            }
        } else if (command === "continue" && !argument) {
            const result = continueFromSentinel(now);
            sendCommandReply("continue", result.message);
        } else if (command === "restart" && !argument) {
            if (perplexityRestart || restartPromptDelivery) {
                sendCommandReply("restart", "A restart transaction is already active.");
            } else {
                if (signalAnimation) {
                    cancelSignalAnimation();
                }
                resetWaitProgress();
                const started = startPerplexityClientRestart(now);
                sendCommandReply(
                    "restart",
                    started ? "Perplexity restart requested." : "Restart request was rejected."
                );
            }
        } else if (command === "enable" || command === "disable") {
            const target = argument.toLowerCase().trim().replace(/\s+/g, " ");
            const enabling = command === "enable";
            if (/^cpu(?: (?:signal|\[signal\]))?$/.test(target)) {
                sendCommandReply(
                    `${command} cpu`,
                    enabling
                        ? enableCPUSignalFromMessage()
                        : disableCPUSignalFromMessage()
                );
            } else if (/^wait(?: (?:signal|\[signal\]))?$/.test(target)) {
                sendCommandReply(
                    `${command} wait`,
                    enabling
                        ? enableWaitSignalFromMessage()
                        : disableWaitSignalFromMessage()
                );
            } else if (/^(?:both|signals|both signals)$/.test(target)) {
                sendCommandReply(
                    `${command} ${target}`,
                    setBothSignalsFromMessage(enabling)
                );
            } else if (/^(?:auto|automode|auto mode)$/.test(target)) {
                sendCommandReply(
                    `${command} ${target}`,
                    setRunnerAutoModeFromMessage(enabling)
                );
            } else if (target === "all") {
                const signalsResult = setBothSignalsFromMessage(enabling);
                const autoResult = setRunnerAutoModeFromMessage(enabling);
                sendCommandReply(
                    `${command} all`,
                    `${signalsResult}\n${autoResult}`
                );
            } else {
                sendCommandReply(
                    "error",
                    `Use ${command} cpu, wait, both, signals, auto, automode, auto mode, or all.`
                );
            }
        } else {
            sendCommandReply(
                "error",
                `Unknown or malformed command: ${trimmed}\n` +
                    "Send help for the supported command list."
            );
        }
    } catch (error) {
        try {
            sendCommandReply(command || "error", `Command failed: ${error}`);
        } catch (replyError) {
            runnerStatusDetail += ` iMessage command/reply failed: ${error}; ${replyError}`;
        }
    }
}

function consumeMessagesCommands(text, now) {
    const lines = String(text).replace(/\r\n?/g, "\n").split("\n");
    for (const line of lines) {
        executeMessagesCommand(line, now);
    }
}

function messageDetectionTextPreview(text) {
    if (typeof text !== "string") {
        return "(message body unavailable)";
    }
    const normalized = text.replace(/\r\n?/g, "\n");
    return normalized.length <= 1200
        ? normalized
        : normalized.slice(0, 1200) + "\n… (preview truncated)";
}

function messageDetectionLogText() {
    return messageDetectionLogEntries.join("\n\n");
}

function updateMessageDetectionLogUI() {
    if (!messageDetectionLogUI) {
        return;
    }
    const count = messageDetectionLogEntries.length;
    const latest = count > 0
        ? messageDetectionLogEntries[count - 1].split(" ")[1]
        : "EMPTY";
    messageDetectionLogUI.title.setStringValue(
        `MESSAGE DETECTION LOG · ${count} · ${latest}`
    );
    const text = messageDetectionLogText();
    messageDetectionLogUI.textView.setString(text);
    if (messageDetectionLogExpanded) {
        messageDetectionLogUI.textView.scrollRangeToVisible(
            $.NSMakeRange(text.length, 0)
        );
    }
}

function appendMessageDetectionLogEntry(row, accepted, reason, text) {
    const timestamp = new Date().toISOString();
    const entry = `${timestamp} ${accepted ? "ACCEPTED" : "REJECTED"}\n` +
        `Reason: ${reason}\n` +
        `Row: ${Number(row.row_id)}\n` +
        `GUID: ${typeof row.guid === "string" ? row.guid : "(none)"}\n` +
        `Service: ${typeof row.service === "string" ? row.service : "(none)"}\n` +
        messageDetectionTextPreview(text);
    messageDetectionLogEntries.push(entry);
    if (messageDetectionLogEntries.length > MESSAGE_LOG_ENTRY_LIMIT) {
        messageDetectionLogEntries = messageDetectionLogEntries.slice(
            -MESSAGE_LOG_ENTRY_LIMIT
        );
    }
    updateMessageDetectionLogUI();
}

function rejectDetectedMessage(row, reason, text) {
    appendMessageDetectionLogEntry(row, false, reason, text);
}

function shiftMessageLogMainViews(delta) {
    for (const view of messageDetectionLogMainViews) {
        const frame = view.frame;
        view.setFrame($.NSMakeRect(
            Number(frame.origin.x),
            Number(frame.origin.y) + delta,
            Number(frame.size.width),
            Number(frame.size.height)
        ));
    }
}

function layoutMessageDetectionLog() {
    if (!messageDetectionLogUI) {
        return;
    }
    const cardY = 10;
    const cardHeight = 42 + (messageDetectionLogExpanded
        ? messageDetectionLogActiveHeight
        : 0);
    messageDetectionLogUI.card.setFrame(
        $.NSMakeRect(20, cardY, 1200, cardHeight)
    );
    const headerY = cardY + cardHeight - 31;
    messageDetectionLogUI.title.setFrame($.NSMakeRect(40, headerY + 4, 700, 20));
    messageDetectionLogUI.button.setFrame($.NSMakeRect(1102, headerY, 96, 28));
    messageDetectionLogUI.button.setTitle(
        messageDetectionLogExpanded ? "Hide log" : "Show log"
    );
    messageDetectionLogUI.scrollView.setFrame(
        $.NSMakeRect(40, 24, 1158, Math.max(32, messageDetectionLogActiveHeight - 16))
    );
    messageDetectionLogUI.scrollView.setHidden(!messageDetectionLogExpanded);
}

function setMessageDetectionLogExpanded(expanded) {
    const target = Boolean(expanded);
    if (!messageDetectionLogUI || target === messageDetectionLogExpanded) {
        return;
    }
    if (target && promptEditorLayout && promptEditorLayout.expandedIndex !== null) {
        setPromptEditorExpansion(null, 0);
    }
    const window = messageDetectionLogUI.window;
    if (target) {
        const frame = window.frame;
        const screen = objcObjectIsNil(window.screen)
            ? $.NSScreen.mainScreen
            : window.screen;
        const visibleFrame = screen.visibleFrame;
        const availableHeight = Math.max(
            0,
            Number(visibleFrame.size.height) - Number(frame.size.height)
        );
        messageDetectionLogActiveHeight = Math.min(
            MESSAGE_LOG_EXPANDED_HEIGHT,
            availableHeight
        );
        if (messageDetectionLogActiveHeight < 32) {
            return;
        }
        messageDetectionLogCollapsedWindowFrame = frame;
        messageDetectionLogExpanded = true;
        shiftMessageLogMainViews(messageDetectionLogActiveHeight);
        const expandedHeight = Number(frame.size.height) +
            messageDetectionLogActiveHeight;
        const minimumY = Number(visibleFrame.origin.y);
        const maximumY = minimumY + Number(visibleFrame.size.height) - expandedHeight;
        const desiredY = Number(frame.origin.y) - messageDetectionLogActiveHeight;
        window.setFrameDisplay(
            $.NSMakeRect(
                Number(frame.origin.x),
                clamp(desiredY, minimumY, maximumY),
                Number(frame.size.width),
                expandedHeight
            ),
            true
        );
    } else {
        const delta = -messageDetectionLogActiveHeight;
        messageDetectionLogExpanded = false;
        shiftMessageLogMainViews(delta);
        if (messageDetectionLogCollapsedWindowFrame) {
            window.setFrameDisplay(messageDetectionLogCollapsedWindowFrame, true);
        }
        messageDetectionLogCollapsedWindowFrame = null;
        messageDetectionLogActiveHeight = 0;
    }
    layoutMessageDetectionLog();
    updateMessageDetectionLogUI();
}

function pollMessagesCommands(now) {
    if (now - lastMessagesCommandPollAt < MESSAGES_COMMAND_POLL_MILLISECONDS) {
        return;
    }
    lastMessagesCommandPollAt = now;
    try {
        if (messagesCommandCursorRowID === null) {
            messagesCommandCursorRowID = latestMessagesRowID();
            messagesCommandChatID = messagesChatIDForRecipient();
            lastMessagesChatResolveAt = now;
            messagesCommandLastError = "";
            return;
        }
        if (messagesCommandChatID === null ||
            now - lastMessagesChatResolveAt >= MESSAGES_CHAT_RESOLVE_MILLISECONDS) {
            messagesCommandChatID = messagesChatIDForRecipient();
            lastMessagesChatResolveAt = now;
            if (messagesCommandChatID === null) {
                return;
            }
        }

        const rows = messagesRowsAfter(
            messagesCommandCursorRowID,
            messagesCommandChatID
        );
        for (const row of rows) {
            messagesCommandCursorRowID = Number(row.row_id);
            const text = messageTextFromDatabaseRow(row);
            const itemType = Number(row.item_type) || 0;
            if (Number(row.is_from_me) !== 0) {
                rejectDetectedMessage(row, "outgoing copy of the self-chat message", text);
                continue;
            }
            const associatedType = Number(row.associated_message_type) || 0;
            if (itemType !== 0) {
                rejectDetectedMessage(row, `item_type ${itemType} is not a command message`, text);
                continue;
            }
            if (associatedType !== 0 ||
                (typeof row.associated_message_guid === "string" &&
                    row.associated_message_guid.length > 0)) {
                rejectDetectedMessage(row, "tapback or associated-message record", text);
                continue;
            }
            if (row.service !== "iMessage") {
                rejectDetectedMessage(row, "message service is not iMessage", text);
                continue;
            }
            if (typeof text !== "string") {
                rejectDetectedMessage(row, "message body could not be decoded", text);
                runnerStatusDetail += " A new iMessage command could not be decoded.";
                continue;
            }
            if (!text.trim()) {
                rejectDetectedMessage(row, "message body is empty", text);
                continue;
            }
            if (messageWasSentByUI(text) || messageLooksLikeUIOutput(text)) {
                rejectDetectedMessage(row, "message was generated by this UI", text);
                continue;
            }
            const guid = typeof row.guid === "string" ? row.guid : "";
            if (!guid) {
                rejectDetectedMessage(row, "message has no stable GUID", text);
                runnerStatusDetail += " An iMessage command without a GUID was ignored.";
                continue;
            }
            if (messageGUIDWasProcessed(guid)) {
                rejectDetectedMessage(row, "message GUID was already processed", text);
                continue;
            }
            if (!recordProcessedMessageGUID(guid)) {
                rejectDetectedMessage(row, "message GUID could not be persisted", text);
                runnerStatusDetail += " An iMessage command was ignored because its GUID could not be persisted.";
                continue;
            }
            appendMessageDetectionLogEntry(
                row,
                true,
                "new command message; processing lines in order",
                text
            );
            consumeMessagesCommands(text, now);
        }
        messagesCommandLastError = "";
    } catch (error) {
        const message = String(error);
        if (message !== messagesCommandLastError) {
            messagesCommandLastError = message;
            runnerStatusDetail += ` iMessage commands unavailable: ${message}`;
        }
    }
}

function runnerTick(now) {
    pollMessagesCommands(now);
    refreshRunnerPresence(now, false);
    if (!runnerReady) {
        runnerSentinelDetected = false;
        runnerLEDHovering = false;
    }
    if (runnerReady && !runnerTaskIsRunning() &&
        now - lastRunnerSentinelCheckAt >= RUNNER_SENTINEL_POLL_SECONDS * 1000) {
        lastRunnerSentinelCheckAt = now;
        const scriptText = readTextFile(runnerSelectedScriptPath, true);
        const sentinelWasDetected = runnerSentinelDetected;
        runnerSentinelDetected = scriptContainsPromptSentinel(
            scriptText,
            activePromptSentinel
        );
        if (runnerSentinelDetected && !sentinelWasDetected) {
            notifySentinelTransition();
        }
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

function runnerStateSuppressesWaitSignal(state) {
    return state === "ready" || state === "sentinel";
}

function waitSignalIsDueAt(now) {
    if (!monitorState || !waitSignalIsEnabled() || monitorState.waitSignalLatched ||
        runnerTaskIsRunning() || runnerStateSuppressesWaitSignal(runnerDisplayState())) {
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
    updateWaitRestartButtonPresentation(now);

    ui.runnerWaitValue.setStringValue(`${runnerNotifyWait().toFixed(1)} s`);
    ui.runnerSelectedPathLabel.setStringValue(runnerSelectedScriptPath);
    ui.runnerSelectedLogPathLabel.setStringValue(runnerSelectedLogPath);
    ui.runnerChooseButton.setEnabled(!runnerBusy && !perplexityRestart);
    ui.runnerChooseLogButton.setEnabled(!runnerBusy && !perplexityRestart);
    ui.runnerOutputButton.setEnabled(true);
    ui.runnerContentToggleButton.setEnabled(true);
    ui.runnerSandboxButton.setEnabled(!runnerBusy && !perplexityRestart);
    ui.runnerSelfTestRequiredButton.setEnabled(
        !runnerBusy && !perplexityRestart &&
        !runnerCommandLineNoSelfTest && !runnerCommandLineSkipSelfTest
    );
    if (runnerCommandLineNoSelfTest) {
        ui.runnerSelfTestRequiredButton.setToolTip(
            "The saved UI policy is overridden for this launch: --no-self-test suppresses startup, manual, and execution-time self-tests."
        );
    } else if (runnerCommandLineSkipSelfTest) {
        ui.runnerSelfTestRequiredButton.setToolTip(
            "The saved UI policy is overridden for this launch: startup and manual self-tests remain available, but execution-time self-tests and the failed startup state are bypassed."
        );
    }
    ui.runnerAutoButton.setEnabled(
        !orphanBusy && (runnerTaskMode === "run" || (!taskRunning && autoAvailable))
    );
    ui.runnerAutoButton.setToolTip(
        runnerTaskMode === "run"
            ? "Toggle Auto Mode for future run scripts. This does not stop or restart the current runner."
            : "When enabled, an eligible watched run.sh starts automatically."
    );
    ui.runnerWaitSlider.setEnabled(!runnerBusy);
    ui.waitPauseButton.setEnabled(
        !signalAnimation && !perplexityRestart && !restartPromptDelivery
    );
    ui.runnerSuccessPromptButton.setEnabled(!runnerBusy);
    ui.runnerSuccessPromptField.setEnabled(!runnerBusy);
    ui.runnerFailurePromptButton.setEnabled(!runnerBusy);
    ui.runnerFailurePromptField.setEnabled(!runnerBusy);
    ui.promptInjectButton.setTitle(signalAnimation ? "Cancel" : "Prompt now");
    ui.promptInjectButton.setEnabled(
        Boolean(signalAnimation) ||
        (!taskRunning && !perplexityRestart && !restartPromptDelivery)
    );
    updatePromptSentinelLabel(ui.promptHint);
    ui.configurationSaveButton.setEnabled(
        !runnerBusy && !signalAnimation && !perplexityRestart &&
        !restartPromptDelivery
    );
    ui.configurationMenu.setEnabled(
        !runnerBusy && !signalAnimation && !perplexityRestart &&
        !restartPromptDelivery
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
        ui.runnerLEDButton.setToolTip(
            runnerSelfTestStatus === "failed"
                ? "Acknowledge the failed startup self-test and unlock execution for the current path and sandbox configuration."
                : "Click to run the environment self-test for the current path and sandbox configuration."
        );
    } else if (displayState === "sentinel") {
        statusText = runnerLEDHovering
            ? `Click to delete ${runnerScriptName()}; the sentinel remains active until Perplexity restarts.`
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
        ui.runnerLEDButton.setToolTip(
            runnerCommandLineNoSelfTest
                ? "Runner is waiting for the run script; self-tests are disabled by --no-self-test."
                : "Runner is waiting for the run script. Click to rerun the environment self-test."
        );
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

    setRunnerActivityLabel(
        ui.runnerActivityLabel,
        ui.runnerLEDButton,
        displayState
    );
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
    monitorState.waitPromptDetail = "";
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

function currentCPUGraphComputationContext() {
    if (!monitorState) {
        return null;
    }
    const samples = monitorState.cpuSamples;
    const latestSample = samples.length > 0 ? samples[samples.length - 1] : null;
    return {
        samples,
        latestSample,
        endTime: latestSample
            ? latestSample.endTime
            : monitorState.graphEndTime || Date.now(),
        historySeconds: Number(monitorState.ui.cpuDurationSlider.doubleValue)
    };
}

function graphDataForSmoothingWindow(context, windowSeconds) {
    return makeCPUGraphData(
        context.samples,
        context.endTime,
        context.historySeconds,
        windowSeconds
    );
}

function maximumAverageInGraphData(graphData) {
    if (graphData.length === 0) {
        return null;
    }
    let maximum = -Infinity;
    for (const segment of graphData) {
        maximum = Math.max(maximum, Number(segment.average));
    }
    return Number.isFinite(maximum) ? maximum : null;
}

function maximumGraphAverageForWindow(context, windowSeconds) {
    return maximumAverageInGraphData(
        graphDataForSmoothingWindow(context, windowSeconds)
    );
}

function applySmoothingWindowToGraph(context, windowSeconds) {
    const graphData = graphDataForSmoothingWindow(context, windowSeconds);
    monitorState.graphEndTime = context.endTime;
    monitorState.cpuGraphData = graphData;
    monitorState.currentAverageCPU = context.latestSample
        ? averageCPUAt(context.samples, context.latestSample.endTime, windowSeconds)
        : 0;
    monitorState.ui.averageWindowValue.setStringValue(`${windowSeconds.toFixed(1)} s`);
    monitorState.ui.cpuGraph.setNeedsDisplay(true);
    return graphData;
}

function adaptThresholdToSmoothingWindow(windowSeconds) {
    const context = currentCPUGraphComputationContext();
    if (!context) {
        return;
    }
    const graphData = applySmoothingWindowToGraph(context, windowSeconds);
    const maximum = maximumAverageInGraphData(graphData);
    if (maximum !== null) {
        monitorState.ui.cpuThresholdSlider.setDoubleValue(clamp(
            maximum,
            CPU_THRESHOLD_MIN_PERCENT,
            Number(monitorState.cpuGraphRangePercent)
        ));
    }
}

function smoothingWindowForThreshold(threshold) {
    const context = currentCPUGraphComputationContext();
    if (!context || context.samples.length === 0) {
        return null;
    }

    const minimumMaximum = maximumGraphAverageForWindow(
        context,
        AVERAGE_WINDOW_MIN_SECONDS
    );
    if (minimumMaximum === null || minimumMaximum <= threshold) {
        return AVERAGE_WINDOW_MIN_SECONDS;
    }

    const maximumMaximum = maximumGraphAverageForWindow(
        context,
        AVERAGE_WINDOW_MAX_SECONDS
    );
    if (maximumMaximum === null || maximumMaximum > threshold) {
        return null;
    }

    let lowerBound = AVERAGE_WINDOW_MIN_SECONDS;
    let upperBound = AVERAGE_WINDOW_MAX_SECONDS;
    for (let iteration = 0; iteration < 18; iteration += 1) {
        const candidate = (lowerBound + upperBound) / 2;
        const candidateMaximum = maximumGraphAverageForWindow(context, candidate);
        if (candidateMaximum !== null && candidateMaximum <= threshold) {
            upperBound = candidate;
        } else {
            lowerBound = candidate;
        }
    }
    return upperBound;
}

function adaptSmoothingWindowToThreshold(threshold) {
    const windowSeconds = smoothingWindowForThreshold(threshold);
    if (windowSeconds === null) {
        return;
    }
    monitorState.ui.averageWindowSlider.setDoubleValue(windowSeconds);
    const context = currentCPUGraphComputationContext();
    if (context) {
        applySmoothingWindowToGraph(context, windowSeconds);
    }
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
    const displayRange = clamp(
        Number(state.cpuGraphRangePercent),
        CPU_GRAPH_RANGE_MIN_PERCENT,
        CPU_GRAPH_RANGE_MAX_PERCENT
    );
    const historySeconds = Math.max(Number(ui.cpuDurationSlider.doubleValue), CPU_SAMPLE_SECONDS);
    const graphEndTime = state.graphEndTime || Date.now();
    const graphStartTime = graphEndTime - historySeconds * 1000;
    const graphData = state.cpuGraphData;
    let filledGraphData = graphData;
    let overlayGraphData = [];
    let overlayAlpha = 1;
    const context = graphMousePressed || cpuGraphTransition
        ? currentCPUGraphComputationContext()
        : null;
    if (graphMousePressed && graphWindowBeforeMouseDown !== null && context) {
        filledGraphData = graphDataForSmoothingWindow(
            context,
            graphWindowBeforeMouseDown
        );
        overlayGraphData = graphData;
    } else if (cpuGraphTransition && context) {
        const progress = clamp(
            (Date.now() - cpuGraphTransition.startedAt) /
                cpuGraphTransition.durationMilliseconds,
            0,
            1
        );
        const easedProgress = progress * progress * (3 - 2 * progress);
        const transition = cpuGraphTransition;
        const filledWindow = transition.aborted
            ? transition.fromWindowSeconds
            : transition.fromWindowSeconds +
                (transition.toWindowSeconds - transition.fromWindowSeconds) *
                    easedProgress;
        const overlayWindow = transition.aborted
            ? transition.previewWindowSeconds
            : transition.toWindowSeconds;
        filledGraphData = graphDataForSmoothingWindow(context, filledWindow);
        overlayGraphData = graphDataForSmoothingWindow(context, overlayWindow);
        overlayAlpha = 1 - easedProgress;
    }

    const filledValue = segment => segment.average;
    let latestFilledAboveThresholdIndex = -1;
    for (let index = 0; index < filledGraphData.length; index += 1) {
        if (filledValue(filledGraphData[index]) > threshold) {
            latestFilledAboveThresholdIndex = index;
        }

    }

    let activeColor = null;
    for (let index = 0; index < filledGraphData.length; index += 1) {
        const segment = filledGraphData[index];
        const value = filledValue(segment);
        const x = clamp((segment.startTime - graphStartTime) / (historySeconds * 1000) * width, 0, width);
        const nextX = clamp((segment.endTime - graphStartTime) / (historySeconds * 1000) * width, x, width);
        const barWidth = Math.max(1, nextX - x);
        const barHeight = clamp(value / displayRange, 0, 1) * height;
        const belowThreshold = value <= threshold;
        const isLatestAboveThreshold = index === latestFilledAboveThresholdIndex;
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
        threshold / displayRange * height,
        0,
        Math.max(0, height - 2)
    );
    fillRect($.NSColor.systemOrangeColor, $.NSMakeRect(0, thresholdY, width, 2));

    const borderColor = $.NSColor.separatorColor;
    fillRect(borderColor, $.NSMakeRect(0, 0, width, 1));
    fillRect(borderColor, $.NSMakeRect(0, Math.max(0, height - 1), width, 1));
    fillRect(borderColor, $.NSMakeRect(0, 0, 1, height));
    fillRect(borderColor, $.NSMakeRect(Math.max(0, width - 1), 0, 1, height));

    if ((graphMousePressed || cpuGraphTransition) && overlayGraphData.length > 0 &&
        overlayAlpha > 0) {
        const surface = $.NSBezierPath.bezierPath;
        let previousEndTime = null;
        let hasSurface = false;
        for (const segment of overlayGraphData) {
            const x = clamp((segment.startTime - graphStartTime) / (historySeconds * 1000) * width, 0, width);
            const nextX = clamp((segment.endTime - graphStartTime) / (historySeconds * 1000) * width, x, width);
            const topY = clamp(
                segment.average / displayRange * height,
                0.5,
                Math.max(0.5, height - 0.5)
            );
            const startsNewSurface = previousEndTime === null ||
                segment.startTime - previousEndTime > CPU_SAMPLE_SECONDS * 2000;
            if (startsNewSurface) {
                surface.moveToPoint($.NSMakePoint(x, topY));
            } else {
                surface.lineToPoint($.NSMakePoint(x, topY));
            }
            surface.lineToPoint($.NSMakePoint(nextX, topY));
            previousEndTime = segment.endTime;
            hasSurface = true;
        }
        if (hasSurface) {
            $.NSColor.blackColor.colorWithAlphaComponent(overlayAlpha).setStroke;
            surface.setLineWidth(1);
            surface.stroke;
        }
    }
}

function setCPUSignalEnabled(enabled) {
    const active = Boolean(enabled);
    const wasPaused = Boolean(monitorState.cpuMonitoringPaused);
    monitorState.cpuMonitoringPaused = !active;
    monitorState.ui.cpuActiveButton.setState(
        active ? $.NSControlStateValueOn : $.NSControlStateValueOff
    );
    if (active && wasPaused) {
        previousProcessCPUTimes = {};
        previousCPUSampleTime = null;
        sampleCPUPercent();
        monitorState.lastCPUSample = Date.now();
    }
    monitorState.cpuWarning = false;
    monitorState.ui.cpuGraph.setAlphaValue(1.0);
    setSignalPauseButtonPresentation(
        monitorState.ui.cpuPauseButton,
        active,
        "CPU"
    );
}

function setWaitSignalEnabled(enabled) {
    const active = Boolean(enabled);
    monitorState.ui.waitActiveButton.setState(
        active ? $.NSControlStateValueOn : $.NSControlStateValueOff
    );
    resetWaitProgress();
    setSignalPauseButtonPresentation(
        monitorState.ui.waitPauseButton,
        active,
        "Wait"
    );
}

function cpuSignalIsEnabled() {
    return Boolean(monitorState && !monitorState.cpuMonitoringPaused);
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

function refreshPerplexityClientPresence(now, force) {
    if (!force && now - perplexityPresenceLastCheckedAt < 500) {
        return perplexityClientRunning;
    }
    perplexityPresenceLastCheckedAt = now;
    try {
        perplexityClientRunning = runningPerplexityApplications().length > 0;
    } catch (error) {
        // Preserve the last known state when NSWorkspace cannot be queried.
    }
    return perplexityClientRunning;
}

function updateWaitRestartButtonPresentation(now) {
    if (!monitorState) {
        return;
    }
    const pending = Boolean(restartPromptDelivery);
    const running = refreshPerplexityClientPresence(now, false);
    monitorState.ui.waitResetButton.setTitle(
        pending ? "Cancel prompt" : "restart Perplexity"
    );
    monitorState.ui.waitResetButton.setToolTip(
        pending
            ? "Cancel the prompt scheduled after this restart."
            : running
                ? "Restart the Perplexity client immediately."
                : "Start Perplexity and initialize the agent immediately."
    );
}

function updateSignalAnimationControls() {
    if (!monitorState) {
        return;
    }
    const ui = monitorState.ui;
    const active = Boolean(signalAnimation);
    const clientRestarting = Boolean(perplexityRestart);
    const restartPromptPending = Boolean(restartPromptDelivery);
    ui.cpuPauseButton.setEnabled(!active);
    ui.waitPauseButton.setEnabled(
        !active && !clientRestarting && !restartPromptPending
    );
    updateWaitRestartButtonPresentation(Date.now());
    ui.waitResetButton.setEnabled(restartPromptPending || !clientRestarting);
    ui.waitRestartPromptField.setEnabled(!active && !restartPromptPending);
    ui.promptInjectButton.setTitle(active ? "Cancel" : "Prompt now");
    ui.promptInjectButton.setEnabled(
        active || (!clientRestarting && !runnerTaskIsRunning())
    );
    ui.signalCancellationOverlay.setHidden(!active);
    for (const row of promptRows) {
        row.textField.setEnabled(!active);
        row.slider.setEnabled(!active && row.eligible);
        row.slider.setAlphaValue(row.eligible ? (active ? 0.5 : 1.0) : 0.4);
    }
    for (const entry of promptEditorEntries) {
        entry.resizeHandle.setHidden(
            active || (entry.kind === "initialization" && restartPromptPending)
        );
    }
    ui.configurationSaveButton.setEnabled(
        !active && !clientRestarting && !restartPromptPending &&
        !runnerTaskIsRunning()
    );
    ui.configurationMenu.setEnabled(
        !active && !clientRestarting && !restartPromptPending &&
        !runnerTaskIsRunning()
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
    if (signalAnimation || perplexityRestart || restartPromptDelivery ||
        runnerTaskIsRunning()) {
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
    if (signalAnimation || perplexityRestart || restartPromptDelivery ||
        runnerTaskIsRunning()) {
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
    observeCurrentMouseDownEvent();
    const pressedMouseButtons = Number($.NSEvent.pressedMouseButtons);
    const primaryMouseButtonIsReleased = (pressedMouseButtons & 1) === 0;
    const mouseButtonIsReleased = pressedMouseButtons === 0;
    if (primaryMouseButtonIsReleased && cpuSliderPreview) {
        finishCPUSliderPreview();
    }
    if (mouseButtonIsReleased) {
        promptWeightGestureSnapshot = null;
        if (!cpuSliderPreview && !graphMousePressed) {
            commitCPUControlValues();
        }
    }

    const runnerBlockedWaitAtStart = runnerTaskIsRunning() ||
        runnerStateSuppressesWaitSignal(runnerDisplayState());
    runnerTick(now);
    const runnerBlocksWaitDuringTick = runnerBlockedWaitAtStart ||
        runnerTaskIsRunning() ||
        runnerStateSuppressesWaitSignal(runnerDisplayState());
    updatePerplexityClientRestart(now);
    updateRestartPrompt(now);
    updateRunnerUI(now);

    if (deliverPendingRunnerPrompt(now, mouseButtonIsReleased)) {
        return;
    }

    const elapsed = (now - state.lastTick) / 1000;
    state.lastTick = now;

    const cpuEnabled = cpuSignalIsEnabled();
    const cpuPaused = Boolean(state.cpuMonitoringPaused);
    const cpuControlPreviewing = Boolean(cpuSliderPreview);
    const waitEnabled = waitSignalIsEnabled();
    const cpuThreshold = Number(ui.cpuThresholdSlider.doubleValue);
    const cpuDuration = Number(ui.cpuDurationSlider.doubleValue);
    const averageWindow = Number(ui.averageWindowSlider.doubleValue);
    const waitTimeout = Number(ui.waitSlider.doubleValue);

    if (!cpuPaused && now - state.lastCPUSample >= CPU_SAMPLE_SECONDS * 1000) {
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
    if (waitEnabled && !runnerBlocksWaitDuringTick &&
        !state.waitSignalLatched) {
        state.waitSeconds += elapsed;
    } else if (!waitEnabled) {
        state.waitSeconds = 0;
    }

    const hasCPUData = state.cpuGraphData.length > 0;
    const currentCPUIsLow = hasCPUData && state.currentAverageCPU <= cpuThreshold;
    if (!cpuPaused && !cpuControlPreviewing) {
        if (cpuEnabled && currentCPUIsLow) {
            state.trailingLowCPUSeconds += elapsed;
        } else {
            state.trailingLowCPUSeconds = 0;
        }
    }
    const cpuFired = cpuEnabled && !cpuPaused && !cpuControlPreviewing &&
        currentCPUIsLow &&
        state.trailingLowCPUSeconds >= cpuDuration;
    const cpuWarningStart = Math.max(0, cpuDuration - WARNING_SECONDS);
    state.cpuWarning = cpuEnabled && !cpuPaused && !cpuControlPreviewing &&
        !signalAnimation && currentCPUIsLow &&
        state.trailingLowCPUSeconds >= cpuWarningStart;

    const waitFired = waitEnabled && !runnerBlocksWaitDuringTick &&
        !state.waitSignalLatched && state.waitSeconds >= waitTimeout;
    state.waitWarning = waitEnabled && !runnerBlocksWaitDuringTick &&
        !state.waitSignalLatched && !signalAnimation && !perplexityRestart &&
        state.waitSeconds >= Math.max(0, waitTimeout - WARNING_SECONDS);

    const cpuRemainingSeconds = cpuEnabled || cpuPaused
        ? Math.max(0, cpuDuration - state.trailingLowCPUSeconds)
        : cpuDuration;
    ui.cpuProgress.setMaxValue(Math.max(cpuDuration, 0.001));
    ui.cpuProgress.setDoubleValue(cpuRemainingSeconds);
    ui.waitProgress.setDoubleValue(
        waitEnabled ? Math.min(state.waitSeconds, WAIT_TIMEOUT_MAX_SECONDS) : 0
    );

    const cpuCondition = cpuPaused
        ? "PAUSED"
        : cpuControlPreviewing
            ? "PREVIEW"
            : !cpuEnabled
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
    ui.cpuPauseButton.setEnabled(!signalAnimation);
    setSignalPauseButtonPresentation(ui.cpuPauseButton, cpuEnabled, "CPU");
    setSignalPauseButtonPresentation(ui.waitPauseButton, waitEnabled, "Wait");
    ui.cpuProgressValue.setStringValue(
        cpuPaused
            ? `PAUSED · ${cpuRemainingSeconds.toFixed(1)} s remaining  ·  ${state.trailingLowCPUSeconds.toFixed(1)} s qualified`
            : cpuEnabled
                ? `${cpuRemainingSeconds.toFixed(1)} s remaining  ·  ${state.trailingLowCPUSeconds.toFixed(1)} s qualified`
                : "PAUSED · press play to begin monitoring"
    );
    const waitStatusDetail = [
        state.waitRestartDetail,
        restartPromptStatusDetail(now)
    ].filter(Boolean).join(" · ");
    ui.waitValue.setStringValue(
        waitEnabled
            ? `${state.waitSeconds.toFixed(1)} s / ${waitTimeout.toFixed(1)} s` +
                (waitStatusDetail ? ` · ${waitStatusDetail}` : "")
            : `PAUSED  ·  threshold ${waitTimeout.toFixed(1)} s` +
                (waitStatusDetail ? ` · ${waitStatusDetail}` : "")
    );
    ui.waitValue.setToolTip(waitStatusDetail);

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
    if (!runnerBlocksWaitDuringTick && mouseButtonIsReleased && waitFired) {
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
        "cpuGraphTransitionTick:": {
            types: ["void", ["id"]],
            implementation: function () {
                if (!cpuGraphTransition || !monitorState) {
                    stopCPUGraphTransition();
                    return;
                }
                const elapsed = Date.now() - cpuGraphTransition.startedAt;
                if (elapsed >= cpuGraphTransition.durationMilliseconds) {
                    stopCPUGraphTransition();
                }
                monitorState.ui.cpuGraph.setNeedsDisplay(true);
            }
        },

        "returnToRunnerOutput:": {
            types: ["void", ["id"]],
            implementation: function () {
                runnerOutputReturnTimer = null;
                const expectedGeneration = runnerOutputReturnMouseDownGeneration;
                runnerOutputReturnMouseDownGeneration = null;
                if (runnerOutputIsVisible() && runnerContentMode === "script" &&
                    runnerMouseDownGeneration === expectedGeneration) {
                    runnerContentMode = "log";
                    updateRunnerOutputPresentation(Date.now(), true);
                }
            }
        },
        "restoreGraphToolTip:": {
            types: ["void", ["id"]],
            implementation: function () {
                graphToolTipRestoreTimer = null;
                if (monitorState && monitorState.ui.cpuGraph) {
                    monitorState.ui.cpuGraph.setToolTip(CPU_GRAPH_TOOLTIP);
                }
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
        "smoothingWindowChanged:": {
            types: ["void", ["id"]],
            implementation: function (sender) {
                const trackingEvent = currentCPUSliderTrackingEvent();
                if (trackingEvent) {
                    beginCPUSliderPreview("smoothing");
                    updateCPUSliderPreviewPointer(sender, trackingEvent);
                }
                adaptThresholdToSmoothingWindow(Number(sender.doubleValue));
                if (trackingEvent && Number(trackingEvent.type) ===
                    Number($.NSEventTypeLeftMouseUp)) {
                    finishCPUSliderPreview(cpuSliderPreview.pointerInside);
                } else if (!trackingEvent) {
                    commitCPUControlValues();
                    scheduleConfigurationSave();
                }
            }
        },
        "cpuThresholdChanged:": {
            types: ["void", ["id"]],
            implementation: function (sender) {
                const trackingEvent = currentCPUSliderTrackingEvent();
                if (trackingEvent) {
                    beginCPUSliderPreview("threshold");
                    updateCPUSliderPreviewPointer(sender, trackingEvent);
                }
                adaptSmoothingWindowToThreshold(Number(sender.doubleValue));
                monitorState.cpuWarning = false;
                monitorState.ui.cpuGraph.setAlphaValue(1.0);
                if (trackingEvent && Number(trackingEvent.type) ===
                    Number($.NSEventTypeLeftMouseUp)) {
                    finishCPUSliderPreview(cpuSliderPreview.pointerInside);
                } else if (!trackingEvent) {
                    commitCPUControlValues();
                    scheduleConfigurationSave();
                }
            }
        },
        "waitTimeoutChanged:": {
            types: ["void", ["id"]],
            implementation: function (sender) {
                const timeout = Number(sender.doubleValue);
                if (monitorState.waitSeconds > timeout) {
                    monitorState.waitSeconds = timeout;
                    monitorState.waitWarning = false;
                    monitorState.pulsePhase = false;
                    monitorState.lastPulse = 0;
                    monitorState.ui.waitProgress.setDoubleValue(timeout);
                    monitorState.ui.waitProgress.setAlphaValue(1.0);
                }
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
        "cpuPause:": {
            types: ["void", ["id"]],
            implementation: function () {
                setCPUSignalEnabled(!cpuSignalIsEnabled());
                if (!cpuSignalIsEnabled()) {
                    monitorState.trailingLowCPUSeconds = 0;
                }
                scheduleConfigurationSave();
                monitorTick();
            }
        },
        "waitPause:": {
            types: ["void", ["id"]],
            implementation: function () {
                setWaitSignalEnabled(!waitSignalIsEnabled());
                scheduleConfigurationSave();
                monitorTick();
            }
        },

        "textUndo:": {
            types: ["void", ["id"]],
            implementation: function (sender) {
                performTextEditingCommand(sender, "undo:");
            }
        },
        "textRedo:": {
            types: ["void", ["id"]],
            implementation: function (sender) {
                performTextEditingCommand(sender, "redo:");
            }
        },
        "textCut:": {
            types: ["void", ["id"]],
            implementation: function (sender) {
                performTextEditingCommand(sender, "cut:");
            }
        },
        "textCopy:": {
            types: ["void", ["id"]],
            implementation: function (sender) {
                performTextEditingCommand(sender, "copy:");
            }
        },
        "textPaste:": {
            types: ["void", ["id"]],
            implementation: function (sender) {
                performTextEditingCommand(sender, "paste:");
            }
        },
        "textSelectAll:": {
            types: ["void", ["id"]],
            implementation: function (sender) {
                performTextEditingCommand(sender, "selectAll:");
            }
        },
        "collapsePromptEditor:": {
            types: ["void", ["id"]],
            implementation: function () {
                collapseExpandedPromptEditor();
            }
        },
        "control:textView:doCommandBySelector:": {
            types: ["bool", ["id", "id", "SEL"]],
            implementation: function (control, textView, commandSelector) {
                const command = String(commandSelector);
                if (command === "cancelOperation:") {
                    return collapseExpandedPromptEditor();
                }
                if (command === "insertNewline:") {
                    return acceptExpandedPromptEditor();
                }
                return false;
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
        "restartPerplexityNow:": {
            types: ["void", ["id"]],
            implementation: function () {
                if (cancelRestartPrompt()) {
                    monitorTick();
                    return;
                }
                if (perplexityRestart) {
                    return;
                }
                if (signalAnimation) {
                    cancelSignalAnimation();
                }
                resetWaitProgress();
                startPerplexityClientRestart(Date.now());
                updateRunnerUI(Date.now());
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
                if (signalAnimation) {
                    cancelSignalAnimation();
                } else {
                    startManualPromptAnimation(Date.now());
                }
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

                const previousScriptPath = runnerSelectedScriptPath;
                const previousDefaultLogPath = defaultRunnerLogPath(previousScriptPath);
                runnerSelectedScriptPath = String(ObjC.unwrap(
                    panel.URL.path.stringByStandardizingPath
                ));
                if (runnerSelectedLogPath === previousDefaultLogPath) {
                    runnerSelectedLogPath = defaultRunnerLogPath(runnerSelectedScriptPath);
                }
                clearRunnerExecutionPreview();
                refreshRunnerPresence(Date.now(), true);
                runnerAutoTriggeredForPresence = false;
                runnerSelfTestStatus = "unverified";
                runnerValidatedConfiguration = null;
                runnerAcknowledgedSelfTestConfiguration = null;
                disableAutoModeForExistingRunScript(monitorState.ui, true);
                runnerStatusDetail = runnerPathDirectoryAvailable
                    ? (runnerSelfTestRequired()
                        ? "Run script path changed; environment self-test required."
                        : "Run script path changed; self-test is optional.")
                    : `Project directory does not exist: ${runnerRootDirectory()}.`;
                scheduleConfigurationSave();
                updateRunnerUI(Date.now());
            }
        },
        "runnerChooseLog:": {
            types: ["void", ["id"]],
            implementation: function () {
                if (runnerOperationInProgress() || perplexityRestart) {
                    return;
                }
                const panel = $.NSSavePanel.savePanel;
                panel.setTitle("Select current run log path");
                panel.setMessage(
                    "Choose where run-loop.sh publishes the active/latest run log. The file may be created later."
                );
                panel.setPrompt("Select Log");
                panel.setNameFieldLabel("Log:");
                panel.setNameFieldStringValue(
                    String(ObjC.unwrap($(runnerSelectedLogPath).lastPathComponent))
                );
                panel.setCanCreateDirectories(true);
                panel.setDirectoryURL($.NSURL.fileURLWithPath(
                    String(ObjC.unwrap($(runnerSelectedLogPath).stringByDeletingLastPathComponent))
                ));
                if (Number(panel.runModal) !== Number($.NSModalResponseOK)) {
                    return;
                }
                const selectedPath = String(ObjC.unwrap(
                    panel.URL.path.stringByStandardizingPath
                ));
                if (selectedPath === runnerSelectedScriptPath) {
                    runnerStatusDetail = "Run log path must differ from the watched run script.";
                    updateRunnerUI(Date.now());
                    return;
                }
                runnerSelectedLogPath = selectedPath;
                runnerOutputLastPollAt = 0;
                runnerOutputLastText = "";
                runnerStatusDetail = `Run log path changed to ${runnerSelectedLogPath}.`;
                scheduleConfigurationSave();
                updateRunnerUI(Date.now());
                if (runnerOutputIsVisible() && runnerContentMode === "log") {
                    updateRunnerOutputPresentation(Date.now(), true);
                }
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
                updateSignalAnimationControls();
                scheduleConfigurationSave();
                monitorTick();
            }
        },
        "runnerShowOutput:": {
            types: ["void", ["id"]],
            implementation: function () {
                cycleRunnerViewMode();
            }
        },
        "runnerToggleScriptLog:": {
            types: ["void", ["id"]],
            implementation: function () {
                toggleRunnerContentMode();
            }
        },
        "toggleMessageDetectionLog:": {
            types: ["void", ["id"]],
            implementation: function () {
                setMessageDetectionLogExpanded(!messageDetectionLogExpanded);
            }
        },
        "runnerLED:": {
            types: ["void", ["id"]],
            implementation: function () {
                const state = runnerDisplayState();
                if (state === "sentinel") {
                    removeSentinelRunScript();
                    monitorTick();
                } else if (state === "running") {
                    requestRunnerStop(true);
                } else if (state === "orphaned" || state === "orphan recovery") {
                    requestOrphanedRunnerStop();
                } else if (state === "uninitialized" && runnerSelfTestStatus === "failed") {
                    runnerAcknowledgedSelfTestConfiguration = runnerConfigurationFingerprint();
                    runnerAutoTriggeredForPresence = false;
                    runnerStatusDetail = "Failed startup self-test acknowledged; execution is unlocked for the current path and sandbox configuration.";
                    updateRunnerUI(Date.now());
                } else if (state === "uninitialized" || state === "idle") {
                    startRunnerSelfTest();
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
                runnerAcknowledgedSelfTestConfiguration = null;
                runnerStatusDetail = sandboxIsEnabled()
                    ? (runnerSelfTestRequired()
                        ? "Sandbox enabled; environment self-test required."
                        : "Sandbox enabled; self-test is optional.")
                    : "Sandbox disabled; execution is available without self-test.";
                updateRunnerUI(Date.now());
            }
        },
        "runnerSelfTestRequiredChanged:": {
            types: ["void", ["id"]],
            implementation: function () {
                if (runnerOperationInProgress() || perplexityRestart ||
                    runnerCommandLineNoSelfTest || runnerCommandLineSkipSelfTest) {
                    return;
                }
                runnerAutoTriggeredForPresence = false;
                const required = runnerSelfTestRequired();
                if (required) {
                    runnerSelfTestStatus = "unverified";
                    runnerValidatedConfiguration = null;
                    runnerAcknowledgedSelfTestConfiguration = null;
                    if (runnerAutoModeEnabled()) {
                        monitorState.ui.runnerAutoButton.setState($.NSControlStateValueOff);
                    }
                }
                runnerStatusDetail = required
                    ? "Environment self-test requirement enabled; runner returned to uninitialized state."
                    : "Environment self-test is optional; sandboxed execution may proceed without it.";
                scheduleConfigurationSave();
                refreshRunnerPresence(Date.now(), true);
                if (!required && runnerAutoModeEnabled() && runnerReady) {
                    startOneShotRunner();
                }
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
                if (graphToolTipRestoreTimer) {
                    graphToolTipRestoreTimer.invalidate;
                    graphToolTipRestoreTimer = null;
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
    const displayRange = monitorState
        ? clamp(
            Number(monitorState.cpuGraphRangePercent),
            CPU_GRAPH_RANGE_MIN_PERCENT,
            CPU_GRAPH_RANGE_MAX_PERCENT
        )
        : CPU_GRAPH_RANGE_DEFAULT_PERCENT;
    return CPU_THRESHOLD_MIN_PERCENT +
        ratio * (displayRange - CPU_THRESHOLD_MIN_PERCENT);
}


function graphValueForRelativeDelta(value, delta, dimension, minimum, maximum) {
    const range = maximum - minimum;
    const adjustment = dimension > 0 ? Number(delta) / Number(dimension) * range : 0;
    return clamp(Number(value) + adjustment, minimum, maximum);
}

function graphSmoothingDragZoomFactor() {
    if (!monitorState) {
        return 1;
    }
    const smoothingRange = AVERAGE_WINDOW_MAX_SECONDS -
        AVERAGE_WINDOW_MIN_SECONDS;
    return smoothingRange > 0
        ? Number(monitorState.ui.cpuDurationSlider.doubleValue) / smoothingRange
        : 1;
}

function graphDurationForHorizontalScroll(value, delta, dimension) {
    if (dimension <= 0) {
        return clamp(
            Number(value),
            CPU_TIMEOUT_MIN_SECONDS,
            CPU_TIMEOUT_MAX_SECONDS
        );
    }
    const offset = CPU_SAMPLE_SECONDS;
    const logarithmicSpan = Math.log(
        (CPU_TIMEOUT_MAX_SECONDS + offset) /
            (CPU_TIMEOUT_MIN_SECONDS + offset)
    );
    return clamp(
        (Number(value) + offset) * Math.exp(
            Number(delta) / Number(dimension) * logarithmicSpan
        ) - offset,
        CPU_TIMEOUT_MIN_SECONDS,
        CPU_TIMEOUT_MAX_SECONDS
    );
}

function graphRangeForRelativeDelta(value, delta, dimension) {
    if (dimension <= 0) {
        return clamp(
            Number(value),
            CPU_GRAPH_RANGE_MIN_PERCENT,
            CPU_GRAPH_RANGE_MAX_PERCENT
        );
    }
    const logarithmicSpan = Math.log(
        CPU_GRAPH_RANGE_MAX_PERCENT / CPU_GRAPH_RANGE_MIN_PERCENT
    );
    return clamp(
        Number(value) * Math.exp(
            Number(delta) / Number(dimension) * logarithmicSpan *
                CPU_GRAPH_RANGE_SCROLL_SENSITIVITY
        ),
        CPU_GRAPH_RANGE_MIN_PERCENT,
        CPU_GRAPH_RANGE_MAX_PERCENT
    );
}


function graphEventPoint(view, event) {
    const point = view.convertPointFromView(event.locationInWindow, undefined);
    return { x: Number(point.x), y: Number(point.y) };
}

function hideCPUGraphToolTip(view) {
    if (graphToolTipRestoreTimer) {
        graphToolTipRestoreTimer.invalidate;
        graphToolTipRestoreTimer = null;
    }
    view.setToolTip(null);
}

function commitCPUControlValues() {
    if (!monitorState) {
        return;
    }
    monitorState.committedSmoothingWindowSeconds = Number(
        monitorState.ui.averageWindowSlider.doubleValue
    );
    monitorState.committedCPUThresholdPercent = Number(
        monitorState.ui.cpuThresholdSlider.doubleValue
    );
}

function beginCPUSliderPreview(kind) {
    if (!monitorState || cpuSliderPreview) {
        return;
    }
    stopCPUGraphTransition();
    cpuSliderPreview = {
        kind,
        smoothingWindowSeconds: Number(
            monitorState.committedSmoothingWindowSeconds
        ),
        cpuThresholdPercent: Number(
            monitorState.committedCPUThresholdPercent
        ),
        pointerInside: true
    };
    graphWindowBeforeMouseDown = cpuSliderPreview.smoothingWindowSeconds;
    graphMouseDownX = null;
    graphMousePressed = true;
    monitorState.ui.cpuGraph.setNeedsDisplay(true);
}

function currentCPUSliderTrackingEvent() {
    const event = $.NSApplication.sharedApplication.currentEvent;
    if (objcObjectIsNil(event)) {
        return null;
    }
    const type = Number(event.type);
    const mouseTrackingTypes = [
        Number($.NSEventTypeLeftMouseDown),
        Number($.NSEventTypeLeftMouseUp),
        Number($.NSEventTypeLeftMouseDragged)
    ];
    return mouseTrackingTypes.indexOf(type) >= 0 ? event : null;
}

function eventIsInsideView(view, event) {
    const point = view.convertPointFromView(event.locationInWindow, undefined);
    const width = Number(view.bounds.size.width);
    const height = Number(view.bounds.size.height);
    return Number(point.x) >= 0 && Number(point.x) < width &&
        Number(point.y) >= 0 && Number(point.y) < height;
}

function updateCPUSliderPreviewPointer(control, event) {
    if (!cpuSliderPreview || !event) {
        return;
    }
    cpuSliderPreview.pointerInside = eventIsInsideView(control, event) ||
        eventIsInsideView(monitorState.ui.cpuGraph, event);
}

function stopCPUGraphTransition() {
    if (cpuGraphTransitionTimer) {
        cpuGraphTransitionTimer.invalidate;
        cpuGraphTransitionTimer = null;
    }
    cpuGraphTransition = null;
}

function startCPUGraphTransition(preview, acceptedWindowSeconds, aborted) {
    stopCPUGraphTransition();
    const oldWindowSeconds = Number(preview.smoothingWindowSeconds);
    const liveWindowSeconds = Number(acceptedWindowSeconds);
    if (Math.abs(liveWindowSeconds - oldWindowSeconds) < 0.0001) {
        return;
    }
    cpuGraphTransition = {
        aborted: Boolean(aborted),
        fromWindowSeconds: oldWindowSeconds,
        previewWindowSeconds: liveWindowSeconds,
        toWindowSeconds: aborted ? oldWindowSeconds : liveWindowSeconds,
        startedAt: Date.now(),
        durationMilliseconds: 320
    };
    cpuGraphTransitionTimer = $.NSTimer.timerWithTimeIntervalTargetSelectorUserInfoRepeats(
        1 / 60,
        monitorController,
        "cpuGraphTransitionTick:",
        null,
        true
    );
    $.NSRunLoop.mainRunLoop.addTimerForMode(
        cpuGraphTransitionTimer,
        $.NSRunLoopCommonModes
    );
}

function finishCPUSliderPreview(releasedInsideOverride) {
    if (!monitorState || !cpuSliderPreview) {
        return;
    }
    const preview = cpuSliderPreview;
    const releasedInside = typeof releasedInsideOverride === "boolean"
        ? releasedInsideOverride
        : Boolean(preview.pointerInside);
    const liveWindowSeconds = Number(
        monitorState.ui.averageWindowSlider.doubleValue
    );
    cpuSliderPreview = null;
    graphMousePressed = false;
    graphWindowBeforeMouseDown = null;
    graphMouseDownX = null;

    if (!releasedInside) {
        monitorState.ui.averageWindowSlider.setDoubleValue(
            preview.smoothingWindowSeconds
        );
        monitorState.ui.cpuThresholdSlider.setDoubleValue(
            preview.cpuThresholdPercent
        );
        const context = currentCPUGraphComputationContext();
        if (context) {
            applySmoothingWindowToGraph(
                context,
                preview.smoothingWindowSeconds
            );
        }
    }
    commitCPUControlValues();
    scheduleConfigurationSave();
    startCPUGraphTransition(preview, liveWindowSeconds, !releasedInside);
    monitorState.ui.cpuGraph.setNeedsDisplay(true);
}

function restoreCPUGraphToolTip(view) {
    if (graphToolTipRestoreTimer) {
        graphToolTipRestoreTimer.invalidate;
        graphToolTipRestoreTimer = null;
    }
    view.setToolTip(CPU_GRAPH_TOOLTIP);
}

function scheduleCPUGraphToolTipRestore() {
    if (!monitorController) {
        return;
    }
    if (graphToolTipRestoreTimer) {
        graphToolTipRestoreTimer.invalidate;
    }
    graphToolTipRestoreTimer = $.NSTimer.timerWithTimeIntervalTargetSelectorUserInfoRepeats(
        GRAPH_TOOLTIP_RESTORE_SECONDS,
        monitorController,
        "restoreGraphToolTip:",
        null,
        false
    );
    $.NSRunLoop.mainRunLoop.addTimerForMode(
        graphToolTipRestoreTimer,
        $.NSRunLoopCommonModes
    );
}


function applyGraphPoint(view, point) {
    if (!monitorState) {
        return;
    }
    const width = Number(view.bounds.size.width);
    const height = Number(view.bounds.size.height);
    const threshold = graphThresholdForY(point.y, height);
    const smoothing = graphMousePressed && graphWindowBeforeMouseDown !== null &&
        graphMouseDownX !== null
        ? graphValueForRelativeDelta(
            graphWindowBeforeMouseDown,
            (point.x - graphMouseDownX) * graphSmoothingDragZoomFactor(),
            width,
            AVERAGE_WINDOW_MIN_SECONDS,
            AVERAGE_WINDOW_MAX_SECONDS
        )
        : Number(monitorState.ui.averageWindowSlider.doubleValue);
    monitorState.ui.cpuThresholdSlider.setDoubleValue(threshold);
    monitorState.ui.averageWindowSlider.setDoubleValue(smoothing);
    const context = currentCPUGraphComputationContext();
    if (context) {
        applySmoothingWindowToGraph(context, smoothing);
    }
    monitorState.ui.graphStatus.setStringValue(
        `RAW ${monitorState.currentRawCPU.toFixed(4)}%    AVG ${monitorState.currentAverageCPU.toFixed(4)}%    THRESHOLD ${threshold.toFixed(3)}%    ${cpuSignalIsEnabled() ? "ADJUSTING" : "DISABLED"}`
    );
    monitorState.ui.cpuGraph.setNeedsDisplay(true);
    scheduleConfigurationSave();
}

function promptEditorFrameSnapshot(view) {
    const frame = view.frame;
    return {
        x: Number(frame.origin.x),
        y: Number(frame.origin.y),
        width: Number(frame.size.width),
        height: Number(frame.size.height)
    };
}

function setPromptEditorFrame(view, frame) {
    view.setFrame($.NSMakeRect(frame.x, frame.y, frame.width, frame.height));
}

function capturePromptEditorLayout(content) {
    promptEditorLayout = {
        content,
        entries: promptEditorEntries.map(entry => ({
            textField: promptEditorFrameSnapshot(entry.textField),
            resizeHandle: promptEditorFrameSnapshot(entry.resizeHandle)
        })),
        expandedIndex: null,
        extraHeight: 0
    };
}

function positionPromptEditorResizeHandle(index, floating) {
    if (!promptEditorLayout || index === null || index < 0 ||
        index >= promptEditorEntries.length) {
        return;
    }
    const layout = promptEditorLayout;
    const handle = promptEditorEntries[index].resizeHandle;
    handle.removeFromSuperviewWithoutNeedingDisplay;
    if (floating || !monitorState || !monitorState.ui.signalCancellationOverlay) {
        layout.content.addSubviewPositionedRelativeTo(
            handle,
            $.NSWindowAbove,
            null
        );
    } else {
        layout.content.addSubviewPositionedRelativeTo(
            handle,
            $.NSWindowBelow,
            monitorState.ui.signalCancellationOverlay
        );
    }
}

function setPromptEditorExpansion(index, requestedHeight) {
    if (!promptEditorLayout) {
        return;
    }
    const layout = promptEditorLayout;
    const previousExpandedIndex = layout.expandedIndex;
    const validIndex = index !== null && index >= 0 && index < layout.entries.length;
    const extraHeight = validIndex
        ? clamp(Number(requestedHeight), 0, 280)
        : 0;
    const expandedIndex = extraHeight > 0 ? index : null;

    for (let entryIndex = 0; entryIndex < layout.entries.length; entryIndex += 1) {
        const entry = promptEditorEntries[entryIndex];
        const base = layout.entries[entryIndex];
        setPromptEditorFrame(entry.textField, base.textField);
        setPromptEditorFrame(entry.resizeHandle, base.resizeHandle);
    }

    if (previousExpandedIndex !== null && expandedIndex === null && monitorState &&
        monitorState.ui.signalCancellationOverlay) {
        const previousEntry = promptEditorEntries[previousExpandedIndex];
        previousEntry.textField.removeFromSuperviewWithoutNeedingDisplay;
        layout.content.addSubviewPositionedRelativeTo(
            previousEntry.textField,
            $.NSWindowBelow,
            monitorState.ui.signalCancellationOverlay
        );
        if (!promptEditorResize) {
            positionPromptEditorResizeHandle(previousExpandedIndex, false);
        }
    }

    if (expandedIndex !== null) {
        const entry = promptEditorEntries[expandedIndex];
        const base = layout.entries[expandedIndex];
        const newHeight = base.textField.height + extraHeight;
        const desiredTop = base.textField.y + newHeight;
        const contentTop = Number(layout.content.bounds.size.height) - 8;
        const top = Math.min(desiredTop, contentTop);
        entry.textField.setFrame($.NSMakeRect(
            base.textField.x,
            top - newHeight,
            base.textField.width,
            newHeight
        ));
        const handleTopInset = base.textField.y + base.textField.height -
            base.resizeHandle.y;
        entry.resizeHandle.setFrame($.NSMakeRect(
            base.resizeHandle.x,
            top - handleTopInset,
            base.resizeHandle.width,
            base.resizeHandle.height
        ));
        if (previousExpandedIndex !== expandedIndex) {
            entry.textField.removeFromSuperviewWithoutNeedingDisplay;
            layout.content.addSubviewPositionedRelativeTo(
                entry.textField,
                $.NSWindowAbove,
                null
            );

        }
        entry.resizeHandle.setNeedsDisplay(true);
    }

    layout.expandedIndex = expandedIndex;
    layout.extraHeight = extraHeight;
    if (promptCollapseMenuItem) {
        promptCollapseMenuItem.setEnabled(expandedIndex !== null);
    }
}

function finishPromptEditorEditing(restoreOriginal) {
    if (!promptEditorLayout || promptEditorLayout.expandedIndex === null) {
        return false;
    }
    const index = promptEditorLayout.expandedIndex;
    const entry = promptEditorEntries[index];
    const window = entry.textField.window;
    if (!objcObjectIsNil(window)) {
        window.endEditingFor(entry.textField);
    }
    if (restoreOriginal && promptEditorEditSession &&
        promptEditorEditSession.index === index) {
        entry.textField.setStringValue(promptEditorEditSession.originalText);
        const tag = Number(entry.textField.tag);
        if (tag >= PROMPT_TEXT_TAG_BASE &&
            tag < PROMPT_TEXT_TAG_BASE + promptRows.length) {
            promptTextChanged(tag - PROMPT_TEXT_TAG_BASE);
        } else {
            scheduleConfigurationSave();
        }
    }
    promptEditorEditSession = null;
    setPromptEditorExpansion(null, 0);
    return true;
}

function collapseExpandedPromptEditor() {
    return finishPromptEditorEditing(true);
}

function acceptExpandedPromptEditor() {
    return finishPromptEditorEditing(false);
}

function promptEditorIndexForResizeHandle(handle) {
    for (let index = 0; index < promptEditorEntries.length; index += 1) {
        if (Boolean(promptEditorEntries[index].resizeHandle.isEqual(handle))) {
            return index;
        }
    }
    return -1;
}

function beginPromptEditorResize(index, screenY) {
    if (!promptEditorLayout || signalAnimation || index < 0 ||
        index >= promptEditorEntries.length ||
        !Boolean(promptEditorEntries[index].textField.enabled)) {
        return;
    }
    if (messageDetectionLogExpanded) {
        setMessageDetectionLogExpanded(false);
    }
    if (promptEditorLayout.expandedIndex !== null &&
        promptEditorLayout.expandedIndex !== index) {
        acceptExpandedPromptEditor();
    }
    if (!promptEditorEditSession || promptEditorEditSession.index !== index) {
        promptEditorEditSession = {
            index,
            originalText: stringValue(promptEditorEntries[index].textField)
        };
    }
    promptEditorResize = {
        index,
        startScreenY: Number(screenY),
        startHeight: promptEditorLayout.expandedIndex === index
            ? promptEditorLayout.extraHeight
            : 0
    };
}

function updatePromptEditorResize(screenY) {
    if (!promptEditorResize) {
        return;
    }
    const delta = Number(screenY) - promptEditorResize.startScreenY;
    setPromptEditorExpansion(
        promptEditorResize.index,
        promptEditorResize.startHeight + delta
    );
}

function finishPromptEditorResize(screenY) {
    if (!promptEditorResize) {
        return;
    }
    const index = promptEditorResize.index;
    updatePromptEditorResize(screenY);
    promptEditorResize = null;
    positionPromptEditorResizeHandle(
        index,
        Boolean(promptEditorLayout && promptEditorLayout.expandedIndex === index)
    );
    const entry = promptEditorEntries[index];
    const window = entry.textField.window;
    if (promptEditorLayout.expandedIndex === index && !objcObjectIsNil(window)) {
        window.makeFirstResponder(entry.textField);
    } else {
        promptEditorEditSession = null;
    }
}

function drawPromptEditorResizeHandle(view) {
    const bounds = view.bounds;
    $.NSColor.tertiaryLabelColor.setStroke;
    const path = $.NSBezierPath.bezierPath;
    path.setLineWidth(1.25);
    for (let offset = 0; offset < 3; offset += 1) {
        const inset = 2 + offset * 3;
        path.moveToPoint($.NSMakePoint(
            Number(bounds.size.width) - inset,
            Number(bounds.size.height) - 2
        ));
        path.lineToPoint($.NSMakePoint(
            Number(bounds.size.width) - 2,
            Number(bounds.size.height) - inset
        ));
    }
    path.stroke;
}

ObjC.registerSubclass({
    name: "PromptEditorResizeHandle",
    superclass: "NSView",
    methods: {
        "drawRect:": {
            implementation: function () {
                drawPromptEditorResizeHandle(this);
            }
        },
        "acceptsFirstMouse:": {
            types: ["bool", ["id"]],
            implementation: function () {
                return true;
            }
        },
        "acceptsFirstResponder": {
            types: ["bool", []],
            implementation: function () {
                return true;
            }
        },
        "keyDown:": {
            types: ["void", ["id"]],
            implementation: function (event) {
                if (Number(event.keyCode) === 53) {
                    collapseExpandedPromptEditor();
                }
            }
        },
        "mouseDown:": {
            types: ["void", ["id"]],
            implementation: function () {
                const window = this.window;
                if (!objcObjectIsNil(window)) {
                    window.makeKeyAndOrderFront(null);
                    window.makeFirstResponder(this);
                }
                $.NSApplication.sharedApplication.activateIgnoringOtherApps(true);
                beginPromptEditorResize(
                    promptEditorIndexForResizeHandle(this),
                    Number($.NSEvent.mouseLocation.y)
                );
            }
        },
        "mouseDragged:": {
            types: ["void", ["id"]],
            implementation: function () {
                updatePromptEditorResize(Number($.NSEvent.mouseLocation.y));
            }
        },
        "mouseUp:": {
            types: ["void", ["id"]],
            implementation: function () {
                finishPromptEditorResize(Number($.NSEvent.mouseLocation.y));
            }
        },
        "resetCursorRects": {
            types: ["void", []],
            implementation: function () {
                this.addCursorRectCursor(this.bounds, $.NSCursor.resizeUpDownCursor);
            }
        }
    }
});

ObjC.registerSubclass({
    name: "CPUGraphView",
    superclass: "NSView",
    methods: {
        "drawRect:": {
            implementation: function () {
                drawCPUGraph(this);
            }
        },
        "acceptsFirstMouse:": {
            types: ["bool", ["id"]],
            implementation: function () {
                return true;
            }
        },
        "mouseDown:": {
            types: ["void", ["id"]],
            implementation: function (event) {
                hideCPUGraphToolTip(this);
                stopCPUGraphTransition();
                const point = graphEventPoint(this, event);
                graphWindowBeforeMouseDown = Number(
                    monitorState.ui.averageWindowSlider.doubleValue
                );
                graphMouseDownX = point.x;
                graphMousePressed = true;
                applyGraphPoint(this, point);
            }
        },
        "mouseDragged:": {
            types: ["void", ["id"]],
            implementation: function (event) {
                hideCPUGraphToolTip(this);
                applyGraphPoint(this, graphEventPoint(this, event));
            }
        },
        "mouseUp:": {
            types: ["void", ["id"]],
            implementation: function (event) {
                const point = graphEventPoint(this, event);
                const width = Number(this.bounds.size.width);
                const height = Number(this.bounds.size.height);
                const releasedOutside = point.x < 0 || point.x >= width ||
                    point.y < 0 || point.y >= height;
                const previousWindow = graphWindowBeforeMouseDown;
                const liveWindow = Number(
                    monitorState.ui.averageWindowSlider.doubleValue
                );
                graphMousePressed = false;
                graphWindowBeforeMouseDown = null;
                graphMouseDownX = null;
                if (releasedOutside && previousWindow !== null) {
                    monitorState.ui.averageWindowSlider.setDoubleValue(previousWindow);
                    const context = currentCPUGraphComputationContext();
                    if (context) {
                        applySmoothingWindowToGraph(context, previousWindow);
                    }
                    scheduleConfigurationSave();
                }
                commitCPUControlValues();
                if (previousWindow !== null) {
                    startCPUGraphTransition(
                        { smoothingWindowSeconds: previousWindow },
                        liveWindow,
                        releasedOutside
                    );
                }
                this.setNeedsDisplay(true);
                restoreCPUGraphToolTip(this);
            }
        },
        "scrollWheel:": {
            types: ["void", ["id"]],
            implementation: function (event) {
                if (!monitorState) {
                    return;
                }
                hideCPUGraphToolTip(this);
                scheduleCPUGraphToolTipRestore();
                if (Number(event.momentumPhase) !== 0) {
                    return;
                }
                const precise = Boolean(event.hasPreciseScrollingDeltas);
                const deltaX = Number(event.scrollingDeltaX) * (precise ? 1 : 12);
                const deltaY = Number(event.scrollingDeltaY) * (precise ? 1 : 12);
                if (deltaX === 0 && deltaY === 0) {
                    return;
                }
                const width = Number(this.bounds.size.width);
                const height = Number(this.bounds.size.height);
                const duration = graphDurationForHorizontalScroll(
                    monitorState.ui.cpuDurationSlider.doubleValue,
                    deltaX,
                    width
                );
                const displayRange = graphRangeForRelativeDelta(
                    monitorState.cpuGraphRangePercent,
                    deltaY,
                    height
                );
                monitorState.cpuGraphRangePercent = displayRange;
                monitorState.ui.cpuDurationSlider.setDoubleValue(duration);
                monitorState.ui.cpuThresholdSlider.setMaxValue(displayRange);
                if (Number(monitorState.ui.cpuThresholdSlider.doubleValue) > displayRange) {
                    monitorState.ui.cpuThresholdSlider.setDoubleValue(displayRange);
                }
                monitorState.ui.thresholdMaximumLabel.setStringValue(
                    `${Number(displayRange.toFixed(2))}%`
                );
                monitorState.ui.cpuDurationValue.setStringValue(`${duration.toFixed(1)} s`);
                monitorState.ui.cpuProgress.setMaxValue(Math.max(duration, 0.001));
                const context = currentCPUGraphComputationContext();
                if (context) {
                    applySmoothingWindowToGraph(
                        context,
                        Number(monitorState.ui.averageWindowSlider.doubleValue)
                    );
                }
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

function restartPromptStatusDetail(now) {
    if (!restartPromptDelivery) {
        return monitorState ? monitorState.waitPromptDetail : "";
    }
    const remainingSeconds = Math.max(
        0,
        (restartPromptDelivery.sendAt - now) / 1000
    );
    if (remainingSeconds <= 0 && perplexityRestart) {
        return "PROMPT READY · WAITING FOR RESTART";
    }
    return restartPromptDelivery.attempts > 0
        ? `PROMPT RETRY IN ${remainingSeconds.toFixed(1)} s`
        : `PROMPT IN ${remainingSeconds.toFixed(1)} s`;
}

function scheduleRestartPrompt(now) {
    if (!monitorState) {
        return;
    }
    const configuredPrompt = stringValue(
        monitorState.ui.waitRestartPromptField
    );
    restartPromptDelivery = {
        rawPrompt: configuredPrompt.trim()
            ? configuredPrompt
            : WAIT_RESTART_PROMPT_DEFAULT,
        sendAt: now + RESTART_PROMPT_DELAY_MILLISECONDS,
        attempts: 0
    };
    monitorState.waitPromptDetail = "";
    updateSignalAnimationControls();
}

function cancelRestartPrompt() {
    if (!restartPromptDelivery) {
        return false;
    }
    restartPromptDelivery = null;
    if (monitorState) {
        monitorState.waitPromptDetail = "PROMPT CANCELLED";
    }
    updateSignalAnimationControls();
    return true;
}

function updateRestartPrompt(now) {
    if (!restartPromptDelivery || now < restartPromptDelivery.sendAt ||
        perplexityRestart || signalAnimation) {
        return;
    }
    const delivery = restartPromptDelivery;
    try {
        sendPrompt(delivery.rawPrompt);
        restartPromptDelivery = null;
        monitorState.waitPromptDetail = "PROMPT SENT";
    } catch (error) {
        delivery.attempts += 1;
        if (delivery.attempts >= RESTART_PROMPT_MAX_ATTEMPTS) {
            restartPromptDelivery = null;
            monitorState.waitPromptDetail = `PROMPT FAILED · ${error}`;
        } else {
            delivery.sendAt = Date.now() + RESTART_PROMPT_RETRY_MILLISECONDS;
            monitorState.waitPromptDetail = `PROMPT ATTEMPT ${delivery.attempts} FAILED`;
        }
    }
    updateSignalAnimationControls();
}

function finishPerplexityClientRestart(success, detail) {
    if (!perplexityRestart) {
        return;
    }
    const previousFrontmostName = perplexityRestart.previousFrontmostName;
    let sentinelDetail = "";
    if (success) {
        try {
            const sentinelResult = cyclePromptSentinelAfterPerplexityRestart();
            sentinelDetail = sentinelResult.cycled
                ? " · sentinel rotated"
                : " · sentinel preserved";
            runnerStatusDetail = sentinelResult.message;
        } catch (error) {
            sentinelDetail = " · SENTINEL ROTATION FAILED";
            runnerStatusDetail = `Perplexity restarted, but sentinel rotation failed: ${error}`;
            if (restartPromptDelivery) {
                restartPromptDelivery = null;
                monitorState.waitPromptDetail = "PROMPT CANCELLED · SENTINEL ROTATION FAILED";
            }
        }
    }
    perplexityRestart = null;
    if (monitorState) {
        monitorState.waitWarning = false;
        if (!success && restartPromptDelivery) {
            restartPromptDelivery = null;
            monitorState.waitPromptDetail = "PROMPT CANCELLED · RESTART FAILED";
        }
        monitorState.waitRestartDetail = success
            ? `RESTARTED · waiting for runner${sentinelDetail}`
            : `RESTART FAILED · ${detail} · use Restart now to retry`;
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

    monitorState.waitSeconds = 0;
    monitorState.waitSignalLatched = true;
    monitorState.waitWarning = false;
    monitorState.lastTick = now;
    monitorState.ui.waitProgress.setDoubleValue(0);
    monitorState.ui.waitProgress.setAlphaValue(1.0);
    monitorState.waitRestartDetail = "RESTARTING · quitting Perplexity";
    scheduleRestartPrompt(now);
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

    if (rawPromptText.indexOf("{sentinel}") >= 0 &&
        !ACTIVE_SENTINEL_PATTERN.test(activePromptSentinel)) {
        restoreFrontmostProcess(previousFrontmostName);
        throw new Error(
            "No active sentinel token is available. Restart Perplexity before sending this prompt."
        );
    }
    const promptText = expandPromptSentinel(rawPromptText, activePromptSentinel);

    systemEvents.keyCode(36);
    delay(0.2);
    systemEvents.keystroke("k", { using: ["command down"] });
    delay(0.1);
    systemEvents.keystroke("a", { using: ["command down"] });
    systemEvents.keystroke(promptText);
    systemEvents.keyCode(36);

    restoreFrontmostProcess(previousFrontmostName);
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

function updatePromptSentinelLabel(label) {
    const placeholder = "{sentinel}";
    const text = `Current ${placeholder}: ${activePromptSentinel || "none generated yet"}`;
    if (stringValue(label) === text) {
        return;
    }

    label.setStringValue(text);
    const attributedText = label.attributedStringValue.mutableCopy;
    attributedText.addAttributeValueRange(
        $.NSFontAttributeName,
        $.NSFont.systemFontOfSize(11),
        $.NSMakeRange(0, text.length)
    );
    attributedText.addAttributeValueRange(
        $.NSForegroundColorAttributeName,
        $.NSColor.secondaryLabelColor,
        $.NSMakeRange(0, text.length)
    );
    attributedText.addAttributeValueRange(
        $.NSFontAttributeName,
        $.NSFont.boldSystemFontOfSize(11),
        $.NSMakeRange("Current ".length, placeholder.length)
    );
    label.setAttributedStringValue(attributedText);
}

function makeValueLabel(frame, text) {
    const label = makeLabel(frame, text, 12);
    label.setFont($.NSFont.monospacedDigitSystemFontOfSizeWeight(12, $.NSFontWeightMedium));
    label.setAlignment($.NSTextAlignmentRight);
    return label;
}

function makeEditMenuItem(title, action, keyEquivalent, modifierMask) {
    const item = $.NSMenuItem.alloc.initWithTitleActionKeyEquivalent(
        title,
        action,
        keyEquivalent || ""
    );
    item.setTarget(null);
    if (modifierMask !== undefined && modifierMask !== null) {
        item.setKeyEquivalentModifierMask(modifierMask);
    }
    return item;
}

function makeTextEditingContextMenu() {
    const menu = $.NSMenu.alloc.initWithTitle("Text editing");
    for (const spec of [
        ["Cut", "textCut:"],
        ["Copy", "textCopy:"],
        ["Paste", "textPaste:"],
        ["Select All", "textSelectAll:"]
    ]) {
        menu.addItem(makeEditMenuItem(spec[0], spec[1], "", null));
    }
    return menu;
}

function installApplicationEditMenu(nsApp) {
    const command = $.NSEventModifierFlagCommand;
    const commandShift = command | $.NSEventModifierFlagShift;
    const mainMenu = $.NSMenu.alloc.initWithTitle("Main menu");
    const editRoot = $.NSMenuItem.alloc.initWithTitleActionKeyEquivalent(
        "Edit",
        null,
        ""
    );
    const editMenu = $.NSMenu.alloc.initWithTitle("Edit");
    editMenu.addItem(makeEditMenuItem("Undo", "textUndo:", "z", command));
    editMenu.addItem(makeEditMenuItem("Redo", "textRedo:", "Z", commandShift));
    editMenu.addItem($.NSMenuItem.separatorItem);
    editMenu.addItem(makeEditMenuItem("Cut", "textCut:", "x", command));
    editMenu.addItem(makeEditMenuItem("Copy", "textCopy:", "c", command));
    editMenu.addItem(makeEditMenuItem("Paste", "textPaste:", "v", command));
    editMenu.addItem(makeEditMenuItem("Select All", "textSelectAll:", "a", command));
    editMenu.addItem($.NSMenuItem.separatorItem);
    promptCollapseMenuItem = makeEditMenuItem(
        "Cancel Editor",
        "collapsePromptEditor:",
        "\u001b",
        0
    );
    promptCollapseMenuItem.setEnabled(false);
    editMenu.addItem(promptCollapseMenuItem);
    editRoot.setSubmenu(editMenu);
    mainMenu.addItem(editRoot);
    nsApp.setMainMenu(mainMenu);
}

function performTextEditingCommand(sender, action) {
    const nsApp = $.NSApplication.sharedApplication;
    let control = null;
    try {
        const representedObject = sender ? sender.representedObject : null;
        if (!objcObjectIsNil(representedObject)) {
            control = representedObject;
        }
    } catch (error) {
        control = null;
    }

    let window = control && !objcObjectIsNil(control.window)
        ? control.window
        : nsApp.keyWindow;
    if (objcObjectIsNil(window)) {
        window = nsApp.mainWindow;
    }
    if (objcObjectIsNil(window)) {
        return false;
    }
    let responder;
    if (control) {
        responder = window.fieldEditorForObject(false, control);
        if (objcObjectIsNil(responder)) {
            window.makeFirstResponder(control);
            responder = window.fieldEditorForObject(true, control);
        }
    } else {
        responder = window.firstResponder;
    }
    if (objcObjectIsNil(responder)) {
        return false;
    }
    try {
        if (action === "undo:") {
            const undoManager = responder.undoManager;
            if (!objcObjectIsNil(undoManager) && Boolean(undoManager.canUndo)) {
                undoManager.undo;
                return true;
            }
            return false;
        }
        if (action === "redo:") {
            const undoManager = responder.undoManager;
            if (!objcObjectIsNil(undoManager) && Boolean(undoManager.canRedo)) {
                undoManager.redo;
                return true;
            }
            return false;
        }
        if (action === "cut:") {
            responder.cut(null);
        } else if (action === "copy:") {
            responder.copy(null);
        } else if (action === "paste:") {
            responder.paste(null);
        } else if (action === "selectAll:") {
            responder.selectAll(null);
        } else {
            return false;
        }
        return true;
    } catch (error) {
        return false;
    }
}

function configureTextEditingMenuTargets(nsApp, controller) {
    const mainMenu = nsApp.mainMenu;
    if (!objcObjectIsNil(mainMenu) && Number(mainMenu.numberOfItems) > 0) {
        const editMenu = mainMenu.itemAtIndex(0).submenu;
        if (!objcObjectIsNil(editMenu)) {
            for (let index = 0; index < Number(editMenu.numberOfItems); index += 1) {
                const item = editMenu.itemAtIndex(index);
                if (!Boolean(item.separatorItem)) {
                    item.setTarget(controller);
                }
            }
        }
    }
    for (const entry of promptEditorEntries) {
        const menu = entry.textField.menu;
        if (objcObjectIsNil(menu)) {
            continue;
        }
        for (let index = 0; index < Number(menu.numberOfItems); index += 1) {
            const item = menu.itemAtIndex(index);
            item.setTarget(controller);
            item.setRepresentedObject(entry.textField);
        }
    }
}

function makeMultilineEditor(frame, text) {
    const field = $.NSTextField.alloc.initWithFrame(frame);
    field.setStringValue(text);
    field.setEditable(true);
    field.setSelectable(true);
    field.setBezeled(true);
    field.setDrawsBackground(true);
    field.setBackgroundColor($.NSColor.textBackgroundColor);
    field.setUsesSingleLineMode(false);
    field.setLineBreakMode($.NSLineBreakByWordWrapping);
    field.setMaximumNumberOfLines(0);
    field.cell.setWraps(true);
    field.cell.setScrollable(false);
    field.setFont($.NSFont.systemFontOfSize(11));
    field.setMenu(makeTextEditingContextMenu());
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

function configuredSystemSymbolImage(symbolNames, description, pointSize, weight, color) {
    for (const symbolName of symbolNames) {
        const image = $.NSImage.imageWithSystemSymbolNameAccessibilityDescription(
            symbolName,
            description
        );
        if (!objcObjectIsNil(image)) {
            let configuration =
                $.NSImageSymbolConfiguration.configurationWithPointSizeWeight(
                    pointSize,
                    weight
                );
            if (color) {
                const colorConfiguration =
                    $.NSImageSymbolConfiguration.configurationWithHierarchicalColor(color);
                configuration = configuration.configurationByApplyingConfiguration(
                    colorConfiguration
                );
            }
            return image.imageWithSymbolConfiguration(configuration) || image;
        }
    }
    return null;
}

function setSignalPauseButtonPresentation(button, active, signalName) {
    const mode = active ? "pause" : "play";
    const isCPU = signalName === "CPU";
    if ((isCPU ? cpuPauseButtonImageMode : waitPauseButtonImageMode) === mode) {
        return;
    }
    const action = active ? "Pause" : "Resume";
    button.setTitle("");
    button.setImage(configuredSystemSymbolImage(
        active ? ["pause.fill", "pause"] : ["play.fill", "play"],
        `${action} ${signalName} monitoring`,
        16,
        $.NSFontWeightSemibold
    ));
    button.setImagePosition($.NSImageOnly);
    button.setImageScaling($.NSImageScaleProportionallyDown);
    button.setAccessibilityLabel(`${action} ${signalName} monitoring`);
    button.setToolTip(
        active
            ? `Pause ${signalName} monitoring. Paused means inactive.`
            : `Resume ${signalName} monitoring and activate its signal.`
    );
    if (isCPU) {
        cpuPauseButtonImageMode = mode;
    } else {
        waitPauseButtonImageMode = mode;
    }
}

function setRunnerOutputButtonPresentation(button, presentationMode) {
    if (runnerOutputButtonImageMode === presentationMode) {
        return;
    }

    const presentations = {
        signals: {
            symbols: ["terminal", "chevron.right.square"],
            description: "Open script card",
            toolTip: "Showing CPU and wait signals. Click to open the script card."
        },
        runner: {
            symbols: ["waveform.path.ecg.rectangle", "waveform.path.ecg"],
            description: "Return to signals",
            toolTip: "Showing the script card. Click to return to CPU and wait signals."
        }
    };
    const presentation = presentations[presentationMode] || presentations.signals;
    button.setTitle("");
    button.setImage(configuredSystemSymbolImage(
        presentation.symbols,
        presentation.description,
        18,
        $.NSFontWeightMedium
    ));
    button.setToolTip(presentation.toolTip);
    button.setAccessibilityLabel(presentation.description);
    runnerOutputButtonImageMode = presentationMode;
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

function runnerIdleStatusImage(autoModeEnabled) {
    const size = 36;
    const image = $.NSImage.alloc.initWithSize($.NSMakeSize(size, size));
    const documentImage = configuredSystemSymbolImage(
        ["doc.text.fill", "doc.fill"],
        autoModeEnabled
            ? "Runner idle in Auto Mode"
            : "Runner idle in manual mode",
        30,
        $.NSFontWeightRegular,
        $.NSColor.systemGrayColor
    );
    image.lockFocus;
    documentImage.drawInRect($.NSMakeRect(3, 3, 27, 30));
    if (autoModeEnabled) {
        const repeatImage = configuredSystemSymbolImage(
            ["arrow.counterclockwise.circle.fill", "arrow.counterclockwise.circle"],
            "Auto Mode enabled",
            16,
            $.NSFontWeightSemibold,
            $.NSColor.systemGreenColor
        );
        repeatImage.drawInRect($.NSMakeRect(20, 0, 16, 16));
    }
    image.unlockFocus;
    image.setTemplate(false);
    return image;
}

function runnerStatusSymbolImage(state, autoModeEnabled) {
    if (state === "ready") {
        return runnerReadyStatusImage();
    }
    if (state === "idle") {
        return runnerIdleStatusImage(autoModeEnabled);
    }
    if (state === "sentinel") {
        const image = $.NSImage.imageWithSystemSymbolNameAccessibilityDescription(
            runnerLEDHovering ? "trash.circle.fill" : "nosign",
            runnerLEDHovering
                ? "Delete run.sh; preserve sentinel until restart"
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
        uninitialized: "questionmark.circle.fill",
        "path error": "exclamationmark.triangle.fill"
    };
    const descriptions = {
        running: "Runner kill switch",
        orphaned: "Detached runner still active; click to interrupt",
        "orphan stopping": "Orphaned runner stopping",
        "orphan recovery": "Recover orphaned runner snapshot",
        "orphan conflict": "Orphaned runner ownership conflict",
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
    const autoModeEnabled = state === "idle" && runnerAutoModeEnabled();
    const imageMode = autoModeEnabled ? "idle:auto" : state;
    if (runnerStatusImageMode === imageMode) {
        return;
    }
    runnerStatusImageMode = imageMode;
    button.setImage(runnerStatusSymbolImage(state, autoModeEnabled));
}

function setRunnerActivityLabel(label, statusButton, text) {
    label.setStringValue(text);
    label.sizeToFit;
    const fittedWidth = Math.ceil(Number(label.frame.size.width)) + 2;
    const buttonFrame = statusButton.frame;
    label.setFrame($.NSMakeRect(
        Number(buttonFrame.origin.x) +
            (Number(buttonFrame.size.width) - fittedWidth) / 2,
        Number(buttonFrame.origin.y) - 17,
        fittedWidth,
        14
    ));
    label.setAlignment($.NSTextAlignmentCenter);
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
    const buttonEnabled = Boolean(button.enabled);
    const appearanceMode = `${autoEnabled ? "on" : "off"}:${buttonEnabled ? "enabled" : "disabled"}`;
    if (runnerAutoButtonAppearanceMode === appearanceMode) {
        return;
    }

    const title = autoEnabled ? "AUTO · ON" : "AUTO · OFF";
    const titleColor = autoEnabled
        ? $.NSColor.whiteColor
        : $.NSColor.secondaryLabelColor;
    const backgroundColor = autoEnabled
        ? $.NSColor.systemGreenColor.colorWithAlphaComponent(0.82)
        : $.NSColor.controlColor;
    const borderColor = autoEnabled
        ? $.NSColor.systemGreenColor
        : $.NSColor.separatorColor;

    button.setTitle(title);
    const attributedTitle = button.attributedTitle.mutableCopy;
    attributedTitle.addAttributeValueRange(
        $.NSFontAttributeName,
        $.NSFont.systemFontOfSizeWeight(14, $.NSFontWeightBold),
        $.NSMakeRange(0, title.length)
    );
    attributedTitle.addAttributeValueRange(
        $.NSForegroundColorAttributeName,
        titleColor,
        $.NSMakeRange(0, title.length)
    );
    button.setAttributedTitle(attributedTitle);
    button.layer.setBackgroundColor(backgroundColor.CGColor);
    button.layer.setBorderColor(borderColor.CGColor);
    button.setAlphaValue(buttonEnabled ? 1.0 : 0.55);
    runnerAutoButtonAppearanceMode = appearanceMode;
}

function makeAutoModeButton(frame, enabled) {
    const button = $.NSButton.alloc.initWithFrame(frame);
    button.setButtonType($.NSButtonTypePushOnPushOff);
    button.setBordered(false);
    button.setWantsLayer(true);
    button.layer.setCornerRadius(8);
    button.layer.setBorderWidth(1);
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
    installApplicationEditMenu(nsApp);

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
        "Graph: drag Δx = duration-scaled smoothing · y = absolute threshold · trackpad Δx = log span"
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
        $.NSMakeRect(694, 676, 42, 28),
        ""
    );
    runnerOutputButton.setImagePosition($.NSImageOnly);
    runnerOutputButton.setImageScaling($.NSImageScaleProportionallyDown);
    setRunnerOutputButtonPresentation(runnerOutputButton, "signals");

    const cpuCard = makeCard($.NSMakeRect(cardX, 195, cardWidth, 445));
    const waitCard = makeCard($.NSMakeRect(cardX, 25, cardWidth, 150));
    const signalConnectorView = $.SignalConnectorView.alloc.initWithFrame(frame);

    const cpuSectionTitle = makeSectionTitle(
        $.NSMakeRect(contentX, 608, contentWidth - 100, 20),
        "CPU SIGNAL"
    );
    const cpuPauseButton = makePushButton(
        $.NSMakeRect(672, 600, 40, 28),
        ""
    );
    const cpuActiveButton = makeToggleSwitch(
        $.NSMakeRect(0, 0, 0, 0),
        configuration.cpuSignalActive,
        "Internal CPU signal state"
    );
    setSignalPauseButtonPresentation(
        cpuPauseButton,
        configuration.cpuSignalActive,
        "CPU"
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
    averageWindowSlider.setToolTip(
        "Set smoothing-window width; moving this knob previews the live result as a black envelope over the captured reference and sets threshold to the displayed maximum. Release over this slider or the CPU graph to commit; release elsewhere to restore the captured window and threshold."
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
    cpuGraph.setToolTip(CPU_GRAPH_TOOLTIP);
    const initialCPUGraphRange = clamp(
        Math.max(configuration.cpuGraphRangePercent, configuration.cpuThresholdPercent),
        CPU_GRAPH_RANGE_MIN_PERCENT,
        CPU_GRAPH_RANGE_MAX_PERCENT
    );
    const cpuThresholdSlider = makeVerticalSlider(
        $.NSMakeRect(50, graphY, 30, graphHeight),
        CPU_THRESHOLD_MIN_PERCENT,
        initialCPUGraphRange,
        configuration.cpuThresholdPercent
    );
    cpuThresholdSlider.setToolTip(
        "Set CPU threshold; moving this knob previews the live result and selects the smallest feasible smoothing window. If the threshold is below the maximum-smoothed water level, smoothing width remains unchanged. Release over this slider or the CPU graph to commit; release elsewhere to restore the captured threshold and window."
    );
    const thresholdMaximumLabel = makeCaptionLabel(
        $.NSMakeRect(34, graphY + graphHeight - 8, 44, 16),
        `${Number(initialCPUGraphRange.toFixed(2))}%`
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
        "WAIT SIGNAL"
    );
    const waitActiveButton = makeToggleSwitch(
        $.NSMakeRect(0, 0, 0, 0),
        configuration.waitSignalActive,
        "Internal wait signal state"
    );
    const waitPauseButton = makePushButton(
        $.NSMakeRect(548, 135, 40, 28),
        ""
    );
    setSignalPauseButtonPresentation(
        waitPauseButton,
        configuration.waitSignalActive,
        "Wait"
    );
    const waitResetButton = makePushButton(
        $.NSMakeRect(598, 135, 122, 28),
        "restart Perplexity"
    );
    waitResetButton.setToolTip("Restart the Perplexity client immediately.");
    const waitLabel = makeCaptionLabel(
        $.NSMakeRect(contentX, 113, 220, 18),
        "Elapsed / restart threshold"
    );
    const waitValue = makeValueLabel(
        $.NSMakeRect(280, 113, 440, 18),
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
        $.NSMakeRect(contentX, 52, 80, 16),
        "0 s"
    );
    const waitMaximumLabel = makeCaptionLabel(
        $.NSMakeRect(640, 52, 80, 16),
        "900 s"
    );
    waitMaximumLabel.setAlignment($.NSTextAlignmentRight);
    const waitRestartPromptLabel = makeCaptionLabel(
        $.NSMakeRect(contentX, 30, 112, 18),
        "Post-restart prompt"
    );
    const waitRestartPromptField = $.NSTextField.alloc.initWithFrame(
        $.NSMakeRect(154, 26, 566, 24)
    );
    waitRestartPromptField.setStringValue(configuration.waitRestartPrompt);
    waitRestartPromptField.setEditable(true);
    waitRestartPromptField.setSelectable(true);
    waitRestartPromptField.setBezeled(true);
    waitRestartPromptField.setDrawsBackground(true);
    waitRestartPromptField.setBackgroundColor($.NSColor.textBackgroundColor);
    waitRestartPromptField.setUsesSingleLineMode(false);
    waitRestartPromptField.setLineBreakMode($.NSLineBreakByWordWrapping);
    waitRestartPromptField.setMaximumNumberOfLines(0);
    waitRestartPromptField.cell.setWraps(true);
    waitRestartPromptField.cell.setScrollable(false);
    waitRestartPromptField.setMenu(makeTextEditingContextMenu());
    waitRestartPromptField.setToolTip(
        "Prompt sent five seconds after the restart signal fires. Supports {sentinel} expansion like Prompt Mixer entries."
    );
    waitRestartPromptField.setAccessibilityLabel("Post-restart prompt");
    const waitRestartPromptResizeHandle =
        $.PromptEditorResizeHandle.alloc.initWithFrame(
            $.NSMakeRect(720, 36, 12, 12)
        );
    waitRestartPromptResizeHandle.setToolTip(
        "Drag upward to edit. Escape restores the old text; Enter accepts the edit."
    );

    const promptSectionTitle = makeSectionTitle(
        $.NSMakeRect(780, 668, 180, 20),
        "PROMPT MIXER"
    );
    const promptInjectButton = makePushButton(
        $.NSMakeRect(1064, 660, 134, 28),
        "Prompt now"
    );
    promptInjectButton.setToolTip(
        "Start the weighted Prompt Mixer animation. Click anywhere during a roll to cancel it."
    );
    const promptHint = makeCaptionLabel(
        $.NSMakeRect(780, 646, 418, 18),
        ""
    );
    updatePromptSentinelLabel(promptHint);
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
        const resizeHandle = $.PromptEditorResizeHandle.alloc.initWithFrame(
            $.NSMakeRect(1200, rowY + 38, 12, 12)
        );
        resizeHandle.setToolTip(
            "Drag upward to edit. Escape restores the old text; Enter accepts the edit."
        );
        const row = {
            highlightView,
            slider,
            valueLabel,
            textField,
            resizeHandle,
            eligible: true
        };
        promptRows.push(row);
        setPromptRowEligibility(row, Boolean(configuration.prompts[index].text.trim()));
        promptControls.push(highlightView, slider, valueLabel, textField, resizeHandle);
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
    const runnerLEDFrame = $.NSMakeRect(1142, 310, 44, 44);
    const runnerLEDButton = makeRunnerStatusButton(runnerLEDFrame);
    const runnerActivityLabel = makeCaptionLabel(
        $.NSMakeRect(1142, 293, 44, 14),
        "uninitialized"
    );
    runnerActivityLabel.setFont(
        $.NSFont.systemFontOfSizeWeight(9, $.NSFontWeightSemibold)
    );
    setRunnerActivityLabel(
        runnerActivityLabel,
        runnerLEDButton,
        "uninitialized"
    );
    const runnerStatusLabel = makeCaptionLabel(
        $.NSMakeRect(780, 276, 338, 32),
        "Environment self-test has not been run."
    );
    runnerStatusLabel.setMaximumNumberOfLines(2);
    runnerStatusLabel.setLineBreakMode($.NSLineBreakByWordWrapping);

    const runnerSelfTestRequiredButton = makeSwitch(
        $.NSMakeRect(780, 241, 176, 24),
        "Require self-test",
        configuration.runner.selfTestRequired
    );
    runnerSelfTestRequiredButton.setToolTip(
        "When enabled, sandboxed execution requires a passing self-test for the current path and sandbox configuration. Click the runner LED in uninitialized or idle state to run the self-test."
    );
    const runnerSandboxButton = makeSwitch(
        $.NSMakeRect(1020, 241, 158, 24),
        "Use sandbox",
        configuration.runner.sandbox
    );

    const runnerLogLabel = makeCaptionLabel(
        $.NSMakeRect(780, 214, 70, 18),
        "Run log"
    );
    const runnerSelectedLogPathLabel = makeCaptionLabel(
        $.NSMakeRect(850, 214, 248, 18),
        runnerSelectedLogPath
    );
    runnerSelectedLogPathLabel.setLineBreakMode($.NSLineBreakByTruncatingMiddle);
    const runnerChooseLogButton = makePushButton(
        $.NSMakeRect(1106, 208, 72, 28),
        "Choose…"
    );

    const runnerScriptLabel = makeCaptionLabel(
        $.NSMakeRect(780, 184, 70, 18),
        "Run script"
    );
    const runnerSelectedPathLabel = makeCaptionLabel(
        $.NSMakeRect(850, 184, 248, 18),
        runnerSelectedScriptPath
    );
    runnerSelectedPathLabel.setLineBreakMode($.NSLineBreakByTruncatingMiddle);
    const runnerChooseButton = makePushButton(
        $.NSMakeRect(1106, 178, 72, 28),
        "Choose…"
    );

    const runnerWaitLabel = makeCaptionLabel(
        $.NSMakeRect(780, 157, 190, 18),
        "Post-execution wait (0–20 s)"
    );
    const runnerWaitValue = makeValueLabel(
        $.NSMakeRect(1112, 157, 66, 18),
        `${configuration.postExecutionWaitSeconds.toFixed(1)} s`
    );
    const runnerWaitSlider = makeSlider(
        $.NSMakeRect(780, 131, 398, 24),
        RUNNER_NOTIFY_WAIT_MIN_SECONDS,
        RUNNER_NOTIFY_WAIT_MAX_SECONDS,
        configuration.postExecutionWaitSeconds
    );

    const runnerSuccessPromptButton = makeSwitch(
        $.NSMakeRect(780, 99, 98, 24),
        "On success",
        configuration.successPrompt.enabled
    );
    const runnerSuccessPromptField = $.NSTextField.alloc.initWithFrame(
        $.NSMakeRect(882, 96, 296, 27)
    );
    runnerSuccessPromptField.setStringValue(configuration.successPrompt.template);
    runnerSuccessPromptField.setEditable(true);
    runnerSuccessPromptField.setSelectable(true);
    runnerSuccessPromptField.setBezeled(true);
    runnerSuccessPromptField.setDrawsBackground(true);
    runnerSuccessPromptField.setBackgroundColor($.NSColor.textBackgroundColor);
    runnerSuccessPromptField.setUsesSingleLineMode(false);
    runnerSuccessPromptField.setLineBreakMode($.NSLineBreakByWordWrapping);
    runnerSuccessPromptField.setMaximumNumberOfLines(0);
    runnerSuccessPromptField.cell.setWraps(true);
    runnerSuccessPromptField.cell.setScrollable(false);
    runnerSuccessPromptField.setMenu(makeTextEditingContextMenu());
    const runnerSuccessPromptResizeHandle =
        $.PromptEditorResizeHandle.alloc.initWithFrame(
            $.NSMakeRect(1180, 109, 12, 12)
        );
    runnerSuccessPromptResizeHandle.setToolTip(
        "Drag upward to edit. Escape restores the old text; Enter accepts the edit."
    );

    const runnerFailurePromptButton = makeSwitch(
        $.NSMakeRect(780, 65, 98, 24),
        "On failure",
        configuration.failurePrompt.enabled
    );
    const runnerFailurePromptField = $.NSTextField.alloc.initWithFrame(
        $.NSMakeRect(882, 62, 296, 27)
    );
    runnerFailurePromptField.setStringValue(configuration.failurePrompt.template);
    runnerFailurePromptField.setEditable(true);
    runnerFailurePromptField.setSelectable(true);
    runnerFailurePromptField.setBezeled(true);
    runnerFailurePromptField.setDrawsBackground(true);
    runnerFailurePromptField.setBackgroundColor($.NSColor.textBackgroundColor);
    runnerFailurePromptField.setUsesSingleLineMode(false);
    runnerFailurePromptField.setLineBreakMode($.NSLineBreakByWordWrapping);
    runnerFailurePromptField.setMaximumNumberOfLines(0);
    runnerFailurePromptField.cell.setWraps(true);
    runnerFailurePromptField.cell.setScrollable(false);
    runnerFailurePromptField.setMenu(makeTextEditingContextMenu());
    const runnerFailurePromptResizeHandle =
        $.PromptEditorResizeHandle.alloc.initWithFrame(
            $.NSMakeRect(1180, 75, 12, 12)
        );
    runnerFailurePromptResizeHandle.setToolTip(
        "Drag upward to edit. Escape restores the old text; Enter accepts the edit."
    );

    promptEditorEntries = [
        {
            textField: waitRestartPromptField,
            resizeHandle: waitRestartPromptResizeHandle,
            kind: "initialization"
        },
        {
            textField: runnerSuccessPromptField,
            resizeHandle: runnerSuccessPromptResizeHandle,
            kind: "runner"
        },
        {
            textField: runnerFailurePromptField,
            resizeHandle: runnerFailurePromptResizeHandle,
            kind: "runner"
        },
        ...promptRows.map(row => ({
            textField: row.textField,
            resizeHandle: row.resizeHandle,
            kind: "mixer"
        }))
    ];

    const runnerModeHint = makeCaptionLabel(
        $.NSMakeRect(780, 38, 398, 18),
        "Templates support {exit}, {code}, {script}, and {output}."
    );

    const runnerOutputCard = makeCard($.NSMakeRect(cardX, 25, cardWidth, 615));
    const runnerOutputSectionTitle = makeSectionTitle(
        $.NSMakeRect(contentX, 608, contentWidth - 110, 20),
        "WATCHED RUN SCRIPT"
    );
    const runnerContentToggleButton = makePushButton(
        $.NSMakeRect(624, 600, 96, 28),
        "Show log"
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
        cpuPauseButton,
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
        waitPauseButton,
        waitResetButton,
        waitLabel,
        waitValue,
        waitProgress,
        waitSlider,
        waitMinimumLabel,
        waitMaximumLabel,
        waitRestartPromptLabel,
        waitRestartPromptField,
        waitRestartPromptResizeHandle
    ];
    const runnerOutputViews = [
        runnerOutputCard,
        runnerOutputSectionTitle,
        runnerContentToggleButton,
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
        runnerSelfTestRequiredButton,
        runnerSandboxButton,
        runnerAutoButton,
        runnerLogLabel,
        runnerSelectedLogPathLabel,
        runnerChooseLogButton,
        runnerScriptLabel,
        runnerSelectedPathLabel,
        runnerChooseButton,
        runnerWaitLabel,
        runnerWaitValue,
        runnerWaitSlider,
        runnerSuccessPromptButton,
        runnerSuccessPromptField,
        runnerSuccessPromptResizeHandle,
        runnerFailurePromptButton,
        runnerFailurePromptField,
        runnerFailurePromptResizeHandle,
        runnerModeHint,
        ...runnerOutputViews
    ]) {
        content.addSubview(control);
    }

    const signalCancellationOverlay = $.SignalCancellationOverlay.alloc.initWithFrame(frame);
    signalCancellationOverlay.setHidden(true);
    signalCancellationOverlay.setToolTip("Click anywhere to cancel prompt selection and sending.");
    content.addSubview(signalCancellationOverlay);
    content.addSubviewPositionedRelativeTo(
        waitResetButton,
        $.NSWindowAbove,
        signalCancellationOverlay
    );

    messageDetectionLogMainViews = [];
    const existingSubviews = content.subviews;
    for (let index = 0; index < Number(existingSubviews.count); index += 1) {
        messageDetectionLogMainViews.push(existingSubviews.objectAtIndex(index));
    }
    shiftMessageLogMainViews(MESSAGE_LOG_COLLAPSED_HEIGHT);
    const initialWindowFrame = window.frame;
    const initialScreen = objcObjectIsNil(window.screen)
        ? $.NSScreen.mainScreen
        : window.screen;
    const initialVisibleFrame = initialScreen.visibleFrame;
    const collapsedWindowHeight = Number(initialWindowFrame.size.height) +
        MESSAGE_LOG_COLLAPSED_HEIGHT;
    const initialMinimumY = Number(initialVisibleFrame.origin.y);
    const initialMaximumY = initialMinimumY + Number(initialVisibleFrame.size.height) -
        collapsedWindowHeight;
    window.setFrameDisplay(
        $.NSMakeRect(
            Number(initialWindowFrame.origin.x),
            clamp(
                Number(initialWindowFrame.origin.y) - MESSAGE_LOG_COLLAPSED_HEIGHT,
                initialMinimumY,
                Math.max(initialMinimumY, initialMaximumY)
            ),
            Number(initialWindowFrame.size.width),
            collapsedWindowHeight
        ),
        false
    );
    capturePromptEditorLayout(content);

    const messageLogCard = makeCard($.NSMakeRect(20, 10, 1200, 42));
    const messageLogTitle = makeSectionTitle(
        $.NSMakeRect(40, 25, 700, 20),
        "MESSAGE DETECTION LOG · 0 · EMPTY"
    );
    const messageLogButton = makePushButton(
        $.NSMakeRect(1102, 21, 96, 28),
        "Show log"
    );
    const messageLogScrollView = $.NSScrollView.alloc.initWithFrame(
        $.NSMakeRect(40, 24, 1158, MESSAGE_LOG_EXPANDED_HEIGHT - 16)
    );
    messageLogScrollView.setHasVerticalScroller(true);
    messageLogScrollView.setHasHorizontalScroller(false);
    messageLogScrollView.setAutohidesScrollers(true);
    messageLogScrollView.setBorderType($.NSBezelBorder);
    const messageLogTextView = $.NSTextView.alloc.initWithFrame(
        $.NSMakeRect(0, 0, 1158, MESSAGE_LOG_EXPANDED_HEIGHT - 16)
    );
    messageLogTextView.setEditable(false);
    messageLogTextView.setSelectable(true);
    messageLogTextView.setRichText(false);
    messageLogTextView.setHorizontallyResizable(false);
    messageLogTextView.setVerticallyResizable(true);
    messageLogTextView.setAutoresizingMask($.NSViewWidthSizable);
    messageLogTextView.textContainer.setContainerSize(
        $.NSMakeSize(1158, 10000000)
    );
    messageLogTextView.textContainer.setWidthTracksTextView(true);
    messageLogTextView.setFont(
        $.NSFont.monospacedSystemFontOfSizeWeight(11, $.NSFontWeightRegular)
    );
    messageLogTextView.setString("");
    messageLogScrollView.setDocumentView(messageLogTextView);
    messageLogScrollView.setHidden(true);
    for (const control of [
        messageLogCard,
        messageLogTitle,
        messageLogButton,
        messageLogScrollView
    ]) {
        content.addSubview(control);
    }
    messageDetectionLogExpanded = false;
    messageDetectionLogActiveHeight = 0;
    messageDetectionLogCollapsedWindowFrame = null;
    messageDetectionLogUI = {
        window,
        card: messageLogCard,
        title: messageLogTitle,
        button: messageLogButton,
        scrollView: messageLogScrollView,
        textView: messageLogTextView
    };
    layoutMessageDetectionLog();
    updateMessageDetectionLogUI();

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
        thresholdMaximumLabel,
        cpuDurationSlider,
        cpuDurationValue,
        averageWindowSlider,
        averageWindowValue,
        cpuProgressValue,
        cpuProgress,
        cpuActiveButton,
        cpuPauseButton,
        waitValue,
        waitProgress,
        waitSlider,
        waitActiveButton,
        waitPauseButton,
        waitResetButton,
        waitRestartPromptField,
        messageLogButton,
        signalViews,
        signalConnectorView,
        runnerOutputCard,
        runnerOutputViews,
        runnerOutputSectionTitle,
        runnerContentToggleButton,
        configurationSaveButton,
        configurationMenu,
        signalCancellationOverlay,
        promptCard,
        promptInjectButton,
        promptHint,
        runnerLEDButton,
        runnerActivityLabel,
        runnerStatusLabel,
        runnerChooseButton,
        runnerChooseLogButton,
        runnerSelfTestRequiredButton,
        runnerOutputButton,
        runnerSandboxButton,
        runnerAutoButton,
        runnerSelectedPathLabel,
        runnerSelectedLogPathLabel,
        runnerWaitSlider,
        runnerWaitValue,
        runnerSuccessPromptButton,
        runnerSuccessPromptField,
        runnerFailurePromptButton,
        runnerFailurePromptField
    };
}

function monitorCommandLineOptions(argv) {
    const options = {
        projectDirectory: null,
        skipSelfTest: false,
        noSelfTest: false
    };
    for (const argumentValue of argv) {
        const argument = String(argumentValue);
        if (argument === "--skip-self-test") {
            options.skipSelfTest = true;
        } else if (argument === "--no-self-test") {
            options.noSelfTest = true;
        } else if (argument.indexOf("-") === 0) {
            throw new Error(
                `Unknown option: ${argument}. Usage: perplexity-cpu-loop.js ` +
                "[--skip-self-test|--no-self-test] [PROJECT_DIRECTORY]"
            );
        } else if (options.projectDirectory !== null) {
            throw new Error(
                "Usage: perplexity-cpu-loop.js [--skip-self-test|--no-self-test] " +
                "[PROJECT_DIRECTORY] — expected at most one positional argument."
            );
        } else {
            options.projectDirectory = argument;
        }
    }
    return options;
}

function run(argv) {
    const commandLine = monitorCommandLineOptions(argv);
    runnerCommandLineSkipSelfTest = commandLine.skipSelfTest;
    runnerCommandLineNoSelfTest = commandLine.noSelfTest;

    const configuration = loadConfiguration();
    if (commandLine.projectDirectory !== null) {
        const projectDirectory = resolveProjectDirectory(commandLine.projectDirectory);
        configuration.runner.selectedScriptPath = String(ObjC.unwrap(
            $(projectDirectory).stringByAppendingPathComponent("run.sh")
                .stringByStandardizingPath
        ));
        configuration.runner.selectedLogPath = defaultRunnerLogPath(
            configuration.runner.selectedScriptPath
        );
    }

    runnerSelectedScriptPath = configuration.runner.selectedScriptPath;
    runnerSelectedLogPath = configuration.runner.selectedLogPath;
    activePromptSentinel = configuration.activePromptSentinel;
    let promptSentinelInitialized = false;
    if (!ACTIVE_SENTINEL_PATTERN.test(activePromptSentinel)) {
        activePromptSentinel = generateRandomPromptSentinel();
        configuration.activePromptSentinel = activePromptSentinel;
        promptSentinelInitialized = true;
    }
    messagesCommandProcessedGUIDs = configuration.processedMessageGUIDs.slice(
        -MESSAGES_PROCESSED_GUID_LIMIT
    );
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
        cpuGraphRangePercent: Number(ui.cpuThresholdSlider.maxValue),
        cpuMonitoringPaused: !configuration.cpuSignalActive,
        committedSmoothingWindowSeconds: Number(ui.averageWindowSlider.doubleValue),
        committedCPUThresholdPercent: Number(ui.cpuThresholdSlider.doubleValue),
        trailingLowCPUSeconds: 0,
        waitSeconds: 0,
        waitSignalLatched: false,
        waitRestartDetail: "",
        waitPromptDetail: "",
        lastTick: now,
        lastCPUSample: now,
        pulsePhase: false,
        lastPulse: 0,
        cpuWarning: false,
        waitWarning: false
    };

    monitorController = $.MonitorController.alloc.init;
    ui.window.setDelegate(monitorController);
    configureTextEditingMenuTargets(ui.nsApp, monitorController);

    for (let index = 0; index < promptRows.length; index += 1) {
        promptRows[index].slider.setTarget(monitorController);
        promptRows[index].slider.setAction("promptWeightChanged:");
        promptRows[index].textField.setDelegate(monitorController);
    }
    normalizePromptWeights();

    for (const control of [
        ui.cpuDurationSlider,
        ui.runnerWaitSlider,
        ui.runnerSuccessPromptButton,
        ui.runnerFailurePromptButton
    ]) {
        control.setTarget(monitorController);
        control.setAction("configurationChanged:");
    }
    ui.averageWindowSlider.setTarget(monitorController);
    ui.averageWindowSlider.setAction("smoothingWindowChanged:");
    ui.cpuThresholdSlider.setTarget(monitorController);
    ui.cpuThresholdSlider.setAction("cpuThresholdChanged:");
    ui.runnerSuccessPromptField.setDelegate(monitorController);
    ui.runnerFailurePromptField.setDelegate(monitorController);
    ui.waitRestartPromptField.setDelegate(monitorController);

    ui.cpuPauseButton.setTarget(monitorController);
    ui.cpuPauseButton.setAction("cpuPause:");
    ui.waitPauseButton.setTarget(monitorController);
    ui.waitPauseButton.setAction("waitPause:");
    ui.waitSlider.setTarget(monitorController);
    ui.waitSlider.setAction("waitTimeoutChanged:");
    ui.waitRestartPromptField.setTarget(monitorController);
    ui.waitRestartPromptField.setAction("configurationChanged:");
    ui.configurationSaveButton.setTarget(monitorController);
    ui.configurationSaveButton.setAction("saveConfigurationNow:");
    ui.configurationMenu.itemAtIndex(1).setTarget(monitorController);
    ui.configurationMenu.itemAtIndex(1).setAction("loadSavedConfiguration:");
    ui.configurationMenu.itemAtIndex(2).setTarget(monitorController);
    ui.configurationMenu.itemAtIndex(2).setAction("resetDefaultConfiguration:");
    ui.promptInjectButton.setTarget(monitorController);
    ui.promptInjectButton.setAction("promptInjectNow:");
    ui.waitResetButton.setTarget(monitorController);
    ui.waitResetButton.setAction("restartPerplexityNow:");
    ui.runnerChooseButton.setTarget(monitorController);
    ui.runnerChooseButton.setAction("runnerChoose:");
    ui.runnerChooseLogButton.setTarget(monitorController);
    ui.runnerChooseLogButton.setAction("runnerChooseLog:");
    ui.runnerOutputButton.setTarget(monitorController);
    ui.runnerOutputButton.setAction("runnerShowOutput:");
    ui.runnerContentToggleButton.setTarget(monitorController);
    ui.runnerContentToggleButton.setAction("runnerToggleScriptLog:");
    ui.messageLogButton.setTarget(monitorController);
    ui.messageLogButton.setAction("toggleMessageDetectionLog:");
    ui.runnerLEDButton.setTarget(monitorController);
    ui.runnerLEDButton.setAction("runnerLED:");
    ui.runnerSandboxButton.setTarget(monitorController);
    ui.runnerSandboxButton.setAction("runnerSandboxChanged:");
    ui.runnerSelfTestRequiredButton.setTarget(monitorController);
    ui.runnerSelfTestRequiredButton.setAction("runnerSelfTestRequiredChanged:");
    ui.runnerAutoButton.setTarget(monitorController);
    ui.runnerAutoButton.setAction("runnerAuto:");

    if (promptSentinelInitialized) {
        if (!saveConfigurationNow()) {
            throw new Error(
                configurationSaveFailureMessage() +
                " The initial sentinel token could not be persisted."
            );
        }
    } else if (autoModeDisabledForExistingScript) {
        scheduleConfigurationSave();
    }
    updateSignalAnimationControls();
    updateSignalAnimationVisuals();

    runnerStartupSelfTestPending = runnerStartupSelfTestEnabled();
    orphanedRunnerTick(Date.now(), true);
    if (!orphanedRunner && runnerStartupSelfTestPending) {
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
