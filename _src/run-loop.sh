#!/usr/bin/env bash
set -euo pipefail

SLEEP_SECONDS=1
CYCLIC=false
CYCLE_TIME_SECONDS="$SLEEP_SECONDS"
ONCE=false
SELF_TEST_ONLY=false
SKIP_EXECUTION_SELF_TEST=false
NO_SELF_TEST=false
SANDBOX_ENABLED=true
RUN_SCRIPT_OPTION="run.sh"
RUN_SCRIPT_OPTION_SET=false
RUN_LOG_OPTION=""
RUN_LOG_OPTION_SET=false
CHECK_RUN_SCRIPT=false
NOTIFY_WAIT_SECONDS=2
NOTIFIER_OPTION=""
SIGNAL_PID=""
SENTINEL_TEXT="He's dead, Jim!"
UI_OWNER_TOKEN=""

usage() {
  printf 'Usage: %s [OPTIONS] [FILE]\n\n' "$(basename "$0")"
  printf '%s\n' \
    'Watch and execute FILE. Its parent directory is used for output and as the' \
    'working directory. FILE defaults to ./run.sh.' \
    '' \
    'Options:' \
    '  -c, --cyclic[=SECONDS]   Keep the run script and execute it repeatedly. The' \
    '                           optional cycle time is the delay between runs in' \
    "                           seconds (default: $SLEEP_SECONDS). It may also be" \
    '                           supplied separately, for example: --cyclic 5.' \
    '      --once               Wait for one run script, execute it, then exit.' \
    '  -t, --self-test-only     Run only the environment self-test, then exit.' \
    '      --skip-self-test     Skip the execution-time self-test; --self-test-only still runs.' \
    '      --no-self-test       Suppress every self-test, including --self-test-only.' \
    '      --sandbox            Execute the run script in the sandbox (default).' \
    '      --no-sandbox         Execute the run script without the sandbox.' \
    '      --sandbox=MODE       Set sandbox mode: enabled or disabled.' \
    '  -r, --run-script PATH    Use PATH instead of the positional FILE.' \
    '      --run-log PATH       Publish the active/latest run log at PATH.' \
    '                           Relative paths use the watched script directory.' \
    '  -e, --check-run-script   Check whether the watched file exists, then exit.' \
    '  -w, --notify-wait SEC    Wait SEC seconds after a run before notifying' \
    '                           (default: 2; decimals are accepted).' \
    '  -n, --notifier COMMAND   Invoke COMMAND instead of perplexity-echo. The' \
    '                           completion message is passed as one argument.' \
    '      --signal-pid PID     Send SIGUSR1 to PID instead of invoking a notifier.' \
    '  -s, --sentinel TEXT      Use TEXT as the run-script sentinel' \
    "                           (default: $SENTINEL_TEXT)." \
    '  -h, --help, --usage      Show this help message.'
}

is_seconds_argument() {
  [[ "$1" =~ ^[0-9]+([.][0-9]+)?$ ]]
}

set_cycle_time() {
  local value="$1"
  if ! is_seconds_argument "$value" || [[ "$value" =~ ^0+([.]0+)?$ ]]; then
    printf 'error: cycle time must be a positive number of seconds: %s\n' "$value" >&2
    exit 2
  fi
  CYCLE_TIME_SECONDS="$value"
}

set_notify_wait() {
  local value="$1"
  if ! is_seconds_argument "$value"; then
    printf 'error: notification wait must be a non-negative number of seconds: %s\n' "$value" >&2
    exit 2
  fi
  NOTIFY_WAIT_SECONDS="$value"
}

set_signal_pid() {
  local value="$1"
  if [[ ! "$value" =~ ^[1-9][0-9]*$ ]]; then
    printf 'error: signal PID must be a positive integer: %s\n' "$value" >&2
    exit 2
  fi
  SIGNAL_PID="$value"
}

set_ui_owner_token() {
  local value="$1"
  if [[ ! "$value" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    printf 'error: UI owner token must be a lowercase UUID: %s\n' "$value" >&2
    exit 2
  fi
  UI_OWNER_TOKEN="$value"
}

set_sandbox_mode() {
  case "$1" in
    enabled|true|yes|on|1) SANDBOX_ENABLED=true ;;
    disabled|false|no|off|0) SANDBOX_ENABLED=false ;;
    *)
      printf 'error: sandbox mode must be enabled or disabled: %s\n' "$1" >&2
      exit 2
      ;;
  esac
}

require_option_value() {
  local option="$1"
  local value="${2:-}"
  if [[ -z "$value" || "$value" == -* ]]; then
    printf 'error: option requires an argument: %s\n' "$option" >&2
    usage >&2
    exit 2
  fi
}

POSITIONAL_ARGS=()
while (( $# > 0 )); do
  case "$1" in
    -c|--cyclic)
      CYCLIC=true
      if (( $# > 1 )) && is_seconds_argument "$2"; then
        set_cycle_time "$2"
        shift
      fi
      ;;
    --cyclic=*)
      CYCLIC=true
      set_cycle_time "${1#*=}"
      ;;
    -c?*)
      CYCLIC=true
      set_cycle_time "${1#-c}"
      ;;
    --once)
      ONCE=true
      ;;
    -t|--self-test|--self-test-only)
      SELF_TEST_ONLY=true
      ;;
    --skip-self-test)
      SKIP_EXECUTION_SELF_TEST=true
      ;;
    --no-self-test)
      NO_SELF_TEST=true
      ;;
    --sandbox)
      SANDBOX_ENABLED=true
      if (( $# > 1 )); then
        case "$2" in
          enabled|true|yes|on|1|disabled|false|no|off|0)
            set_sandbox_mode "$2"
            shift
            ;;
        esac
      fi
      ;;
    --no-sandbox)
      SANDBOX_ENABLED=false
      ;;
    --sandbox=*)
      set_sandbox_mode "${1#*=}"
      ;;
    -r|--run-script)
      require_option_value "$1" "${2:-}"
      RUN_SCRIPT_OPTION="$2"
      RUN_SCRIPT_OPTION_SET=true
      shift
      ;;
    --run-script=*)
      RUN_SCRIPT_OPTION="${1#*=}"
      require_option_value "--run-script" "$RUN_SCRIPT_OPTION"
      RUN_SCRIPT_OPTION_SET=true
      ;;
    -r?*)
      RUN_SCRIPT_OPTION="${1#-r}"
      RUN_SCRIPT_OPTION_SET=true
      ;;
    --run-log)
      require_option_value "$1" "${2:-}"
      RUN_LOG_OPTION="$2"
      RUN_LOG_OPTION_SET=true
      shift
      ;;
    --run-log=*)
      RUN_LOG_OPTION="${1#*=}"
      require_option_value "--run-log" "$RUN_LOG_OPTION"
      RUN_LOG_OPTION_SET=true
      ;;
    -e|--check-run-script)
      CHECK_RUN_SCRIPT=true
      ;;
    -w|--notify-wait)
      require_option_value "$1" "${2:-}"
      set_notify_wait "$2"
      shift
      ;;
    --notify-wait=*)
      set_notify_wait "${1#*=}"
      ;;
    -w?*)
      set_notify_wait "${1#-w}"
      ;;
    -n|--notifier)
      require_option_value "$1" "${2:-}"
      NOTIFIER_OPTION="$2"
      shift
      ;;
    --notifier=*)
      NOTIFIER_OPTION="${1#*=}"
      require_option_value "--notifier" "$NOTIFIER_OPTION"
      ;;
    -n?*)
      NOTIFIER_OPTION="${1#-n}"
      ;;
    --signal-pid)
      require_option_value "$1" "${2:-}"
      set_signal_pid "$2"
      shift
      ;;
    --signal-pid=*)
      set_signal_pid "${1#*=}"
      ;;
    --ui-owner-token)
      require_option_value "$1" "${2:-}"
      set_ui_owner_token "$2"
      shift
      ;;
    --ui-owner-token=*)
      set_ui_owner_token "${1#*=}"
      ;;
    -s|--sentinel)
      require_option_value "$1" "${2:-}"
      SENTINEL_TEXT="$2"
      shift
      ;;
    --sentinel=*)
      sentinel_value="${1#*=}"
      if [[ -z "$sentinel_value" ]]; then
        printf 'error: option requires a non-empty argument: --sentinel\n' >&2
        usage >&2
        exit 2
      fi
      SENTINEL_TEXT="$sentinel_value"
      ;;
    -s?*)
      SENTINEL_TEXT="${1#-s}"
      ;;
    -h|--help|--usage)
      usage
      exit 0
      ;;
    --)
      shift
      while (( $# > 0 )); do
        POSITIONAL_ARGS+=("$1")
        shift
      done
      break
      ;;
    -*)
      printf 'error: unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      ;;
  esac
  shift
done

if (( ${#POSITIONAL_ARGS[@]} > 1 )); then
  printf 'error: expected at most one FILE argument\n' >&2
  usage >&2
  exit 2
fi

if (( ${#POSITIONAL_ARGS[@]} == 1 )) && [[ "$RUN_SCRIPT_OPTION_SET" == true ]]; then
  printf 'error: specify the watched file either as FILE or with --run-script, not both\n' >&2
  usage >&2
  exit 2
fi

if [[ "$ONCE" == true && "$CYCLIC" == true ]]; then
  printf 'error: --once and --cyclic are mutually exclusive\n' >&2
  exit 2
fi

if [[ -n "$NOTIFIER_OPTION" && -n "$SIGNAL_PID" ]]; then
  printf 'error: --notifier and --signal-pid are mutually exclusive\n' >&2
  exit 2
fi

RUN_SCRIPT_INPUT="${POSITIONAL_ARGS[0]:-$RUN_SCRIPT_OPTION}"
if [[ -z "$RUN_SCRIPT_INPUT" ]]; then
  printf 'error: watched file must not be empty\n' >&2
  exit 2
fi
if [[ -d "$RUN_SCRIPT_INPUT" ]]; then
  printf 'error: watched path is a directory; expected a file: %s\n' "$RUN_SCRIPT_INPUT" >&2
  exit 2
fi

RUN_SCRIPT_NAME="$(basename "$RUN_SCRIPT_INPUT")"
RUN_SCRIPT_PARENT="$(dirname "$RUN_SCRIPT_INPUT")"
if ! cd "$RUN_SCRIPT_PARENT"; then
  printf 'error: watched file parent directory does not exist: %s\n' "$RUN_SCRIPT_PARENT" >&2
  exit 2
fi
ROOT_DIR="$PWD"
ROOT_DIR_PHYSICAL="$(pwd -P)"
RUN_SCRIPT_PATH="$ROOT_DIR/$RUN_SCRIPT_NAME"

if [[ -z "$NOTIFIER_OPTION" ]]; then
  NOTIFIER_COMMAND="$ROOT_DIR/_src/perplexity-echo.as"
elif [[ "$NOTIFIER_OPTION" == /* || "$NOTIFIER_OPTION" != */* ]]; then
  NOTIFIER_COMMAND="$NOTIFIER_OPTION"
else
  NOTIFIER_COMMAND="$ROOT_DIR/$NOTIFIER_OPTION"
fi

if [[ "$CHECK_RUN_SCRIPT" == true ]]; then
  if [[ -f "$RUN_SCRIPT_PATH" ]]; then
    printf 'Run script exists: %s\n' "$RUN_SCRIPT_PATH"
    exit 0
  fi
  printf 'Run script does not exist: %s\n' "$RUN_SCRIPT_PATH" >&2
  exit 1
fi

OUTPUT_DIR="$ROOT_DIR/output"
ARCHIVE_DIR="$OUTPUT_DIR/run-archive"
STATE_FILE="$OUTPUT_DIR/run-counter.state"
if [[ "$RUN_LOG_OPTION_SET" == true ]]; then
  if [[ "$RUN_LOG_OPTION" == /* ]]; then
    CURRENT_LOG_LINK="$RUN_LOG_OPTION"
  else
    CURRENT_LOG_LINK="$ROOT_DIR/$RUN_LOG_OPTION"
  fi
else
  CURRENT_LOG_LINK="$OUTPUT_DIR/run-current.log"
fi
if [[ "$CURRENT_LOG_LINK" == "$RUN_SCRIPT_PATH" ]]; then
  printf 'error: run log path must differ from the watched script: %s\n' "$CURRENT_LOG_LINK" >&2
  exit 2
fi
if [[ -d "$CURRENT_LOG_LINK" ]]; then
  printf 'error: run log path is a directory: %s\n' "$CURRENT_LOG_LINK" >&2
  exit 2
fi
CURRENT_SCRIPT_LINK="$OUTPUT_DIR/run-current.sh"
GUARD_SECONDS=300
APPLESCRIPT_PATTERN='perplexity-loop[.]applescript'
SUSPENDED_APPLESCRIPT_PIDS=()
SANDBOX_PROFILE_PATH="$OUTPUT_DIR/run.sandbox.sb"
GITHUB_SSH_DIR="${GITHUB_SSH_DIR:-$HOME/devel}"
GITHUB_SSH_KEY_PATH="${GITHUB_SSH_KEY_PATH:-$GITHUB_SSH_DIR/identities/agent-commit-key/id_ed25519_agent_commit}"
GITHUB_ID_FILE="$OUTPUT_DIR/github-user.txt"
NPM_CACHE_DIR="$OUTPUT_DIR/npm-cache"

mkdir -p "$OUTPUT_DIR" "$ARCHIVE_DIR" "$GITHUB_SSH_DIR" "$NPM_CACHE_DIR" \
  "$(dirname "$CURRENT_LOG_LINK")"
export NPM_CONFIG_CACHE="$NPM_CACHE_DIR"
export npm_config_cache="$NPM_CACHE_DIR"

if [[ -f "$STATE_FILE" ]]; then
  read -r NUM < "$STATE_FILE"
  [[ "$NUM" =~ ^[0-9]+$ ]] || NUM=0
else
  NUM=0
fi

save_counter() {
  printf '%s\n' "$NUM" > "$STATE_FILE"
}

suspend_applescript() {
  SUSPENDED_APPLESCRIPT_PIDS=()
  while IFS= read -r pid; do
    [[ -n "$pid" ]] || continue
    if kill -STOP "$pid" 2>/dev/null; then
      SUSPENDED_APPLESCRIPT_PIDS+=("$pid")
    fi
  done < <(pgrep -f "$APPLESCRIPT_PATTERN" || true)
}

resume_applescript() {
  local pid
  if (( ${#SUSPENDED_APPLESCRIPT_PIDS[@]} )); then
    for pid in "${SUSPENDED_APPLESCRIPT_PIDS[@]}"; do
      kill -CONT "$pid" 2>/dev/null || true
    done
  fi
  SUSPENDED_APPLESCRIPT_PIDS=()
}

kill_applescript_if_requested() {
  if grep -Fq -- "$SENTINEL_TEXT" "$RUN_SCRIPT_PATH"; then
    pkill -KILL -f "$APPLESCRIPT_PATTERN" 2>/dev/null || true
    SUSPENDED_APPLESCRIPT_PIDS=()
    return 0
  fi
  return 1
}

send_completion_notification() {
  local message="$1"
  local timestamp="$2"
  local log_path="$3"

  if [[ "$NOTIFY_WAIT_SECONDS" != 0 && ! "$NOTIFY_WAIT_SECONDS" =~ ^0+([.]0+)?$ ]]; then
    sleep "$NOTIFY_WAIT_SECONDS"
  fi

  if [[ -n "$SIGNAL_PID" ]]; then
    if ! kill -s USR1 "$SIGNAL_PID" 2>/dev/null; then
      printf '[%s] warning: failed to send SIGUSR1 to PID %s\n' \
        "$timestamp" "$SIGNAL_PID" >> "$log_path"
    fi
  elif ! "$NOTIFIER_COMMAND" "$message"; then
    printf '[%s] warning: notifier %s failed for exit code %s\n' \
      "$timestamp" "$NOTIFIER_COMMAND" "$status" >> "$log_path"
  fi
}

trap 'resume_applescript' EXIT INT TERM

write_sandbox_profile() {
  cat > "$SANDBOX_PROFILE_PATH" <<EOF
(version 1)
(deny default)
(import "system.sb")

(allow process-exec process-fork process-info* sysctl-read)

; multiprocessing.Pool / concurrent.futures.ProcessPoolExecutor need POSIX
; semaphores (sem_open et al.) for their inter-process locks/queues, plus
; POSIX shared memory for some allocator backends. Without these, worker-pool
; construction fails immediately with PermissionError: [Errno 1] Operation
; not permitted at SemLock creation -- observed when parallelizing
; _src/tools/spec_upstream.py / spec_scrape.py. Note: sandbox-exec only knows
; the operation categories ipc-posix-sem and ipc-posix-shm -- there is no
; finer-grained ipc-posix-sem-signal/-wait/etc.; a prior attempt using those
; invented names failed with "unbound variable" at profile compile time.
(allow ipc-posix-sem)
(allow ipc-posix-shm)

(allow mach-lookup mach-issue-extension)
(deny mach-lookup (global-name "*"))
(deny mach-lookup (local-name "*"))
(deny mach-lookup (xpc-service-name "*"))
(deny mach-issue-extension (extension-class "com.apple.app-sandbox.read"))

; WebKit's UIProcess must vend a read-only sandbox extension to its nested
; WebContent process before file:// navigation. Limit that extension to the
; project tree already readable by this outer profile. Include both logical
; and physical paths because macOS resolves /tmp through /private/tmp when it
; evaluates extension requests.
(allow file-issue-extension
  (require-all
    (extension-class "com.apple.app-sandbox.read")
    (require-any
      (subpath "$ROOT_DIR")
      (subpath "$ROOT_DIR_PHYSICAL"))))

; Path walking needs metadata on ancestors like /private and /tmp.
(allow file-read-metadata)
(deny file-read-xattr)

; Data/exec reads: Node (Homebrew) + project tree only.
(allow file-read-data file-map-executable
  (subpath "/opt/homebrew")
  (subpath "/private/tmp/autodocs")
  (subpath "/tmp/autodocs"))

; Writes: create only, limited to this run's output area.
(allow file-write-create
  (subpath "/private/tmp/autodocs/output/"))

(allow signal)
(allow file-read-metadata)
(allow network-outbound)
(allow network-inbound (local ip "localhost:*"))
(allow mach-bootstrap)

; Permit WebKit to create and pass narrowly scoped sandbox extensions to its
; own Network, WebContent, GPU and auxiliary child processes.
(allow generic-issue-extension
  (extension-class "com.apple.webkit.mach-bootstrap")
  (extension-class "com.apple.coreservices.launchservicesd"))
(allow iokit-issue-extension
  (extension-class "com.apple.webkit.extension.iokit"))
(allow mach-issue-extension
  (extension-class "com.apple.webkit.extension.mach"))
(allow mach-lookup
  (global-name "com.apple.webinspectord")
  (xpc-service-name "com.apple.WebKit.GPU")
  (xpc-service-name "com.apple.WebKit.Model")
  (xpc-service-name "com.apple.WebKit.Networking")
  (xpc-service-name "com.apple.WebKit.WebContent")
  (xpc-service-name "com.apple.WebKit.WebContent.CaptivePortal")
  (xpc-service-name "com.apple.WebKit.WebContent.Development")
  (xpc-service-name "com.apple.WebKit.WebContent.EnhancedSecurity"))
(allow mach-register
  (global-name "com.apple.webkit.mach-bootstrap"))
(allow system-socket)

; WebKit registers for system power notifications while creating its page
; process. Permit only the corresponding root-domain IOKit user client.
(allow iokit-open-user-client
  (iokit-user-client-class "RootDomainUserClient"))

; Minimal AppKit services required by Playwright WebKit in headless mode.
(allow mach-lookup
  (global-name "com.apple.coreservices.launchservicesd")
  (global-name "com.apple.lsd.mapdb")
  (global-name "com.apple.pasteboard.1")
  (global-name "com.apple.windowserver.active")
  (global-name "com.apple.WindowServer")
  (global-name "com.apple.trustd.agent")
  (global-name "com.apple.fonts")
  (global-name "com.apple.webkit.mach-bootstrap"))

(allow file-read*
  (subpath "/System")
  (subpath "/Library")
  (subpath "/Applications")
  (subpath "/bin")
  (subpath "/sbin")
  (subpath "/usr")
  (subpath "/opt/homebrew")
  (subpath "/usr/local")
  (subpath "/opt")
  (subpath "/etc")
  (subpath "/private/etc")
  (subpath "$ROOT_DIR")
  (literal "$RUN_SCRIPT_PATH")
  (subpath "$GITHUB_SSH_DIR")
  (literal "$HOME/.gitconfig")
  (literal "$HOME/.config/git/config")
  (literal "$GITHUB_SSH_KEY_PATH")
  (literal "$GITHUB_SSH_KEY_PATH.pub")
  (subpath "$HOME/Library/Python")
  (subpath "$HOME/Library/Caches/ms-playwright")
  (subpath "/private/tmp")
  (subpath "/tmp")
  (subpath "/var/folders")
  (subpath "/private/var/folders"))

(allow file-write*
  (subpath "$OUTPUT_DIR")
  (subpath "$ARCHIVE_DIR")
  (subpath "$GITHUB_SSH_DIR")
  (subpath "/opt/homebrew")
  (subpath "/usr/local")
  (subpath "/private/tmp")
  (subpath "/tmp")
  (subpath "/var/folders")
  (subpath "/private/var/folders")
  (literal "/private/var/folders/50/mnp917ks6_zgm_pz0v3prqjw0000gn/T/xcrun_db")
  (literal "/private/var/folders/50/mnp917ks6_zgm_pz0v3prqjw0000gn/T/xcrun_db.lock")
  (subpath "$HOME/Library/Caches")
  (subpath "$HOME/Library/Developer")
  (subpath "$HOME/Library/Application Support")
  (subpath "$HOME/Library/Python"))

(deny file-write*
  (subpath "/Volumes")
  (subpath "/private/var/db")
  (subpath "/private/var/root")
  (subpath "/Library/Keychains")
  (subpath "$HOME/Library/Keychains")
  (subpath "$HOME/.ssh")
  (require-all (subpath "/private/var")
               (require-not (subpath "/private/var/folders"))))

(deny mach-lookup
  (global-name "com.apple.securityd")
  (global-name "com.apple.secd")
  (global-name "com.apple.keychain-circle-notification")
  (global-name "com.apple.trustd")
  (global-name "com.apple.ocspd"))
EOF
}

if [[ "$SANDBOX_ENABLED" == true ]]; then
  write_sandbox_profile
fi

if [[ "$NO_SELF_TEST" == true ]]; then
  echo "Suppressing all environment self-tests (--no-self-test)."
  if [[ "$SELF_TEST_ONLY" == true ]]; then
    exit 0
  fi
elif [[ "$SKIP_EXECUTION_SELF_TEST" == true && "$SELF_TEST_ONLY" == false ]]; then
  echo "Skipping execution-time environment self-test (--skip-self-test)."
else
  echo "Running environment self-test..."
SELFTEST_SCRIPT="$OUTPUT_DIR/run-sandbox-selftest.sh"
SELFTEST_LOG="$OUTPUT_DIR/run-sandbox-selftest.log"
export SELFTEST_LOG OUTPUT_DIR GITHUB_SSH_KEY_PATH RUN_SCRIPT_PATH NPM_CONFIG_CACHE npm_config_cache
cat > "$SELFTEST_SCRIPT" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail

print_selftest_result() {
  local name="$1"
  local value="$2"
  local label
  case "$name" in
    tmp_write_probe) label="Temp write access" ;;
    python_tempfile_probe) label="Python tempfile" ;;
    python_lxml_probe) label="Python import lxml" ;;
    python3_path) label="python3 path" ;;
    pip_path) label="pip path" ;;
    git_path) label="git path" ;;
    ssh_path) label="ssh path" ;;
    python_version_probe) label="python3 --version" ;;
    git_version_probe) label="git --version" ;;
    ssh_version_probe) label="ssh -V" ;;
    output_write_probe) label="Output write" ;;
    output_read_probe) label="Output read" ;;
    output_symlink_probe) label="Output symlink create" ;;
    output_symlink_target_probe) label="Output symlink resolve" ;;
    github_key_read_probe) label="GitHub SSH key readable" ;;
    npm_cache_path_probe) label="npm cache path" ;;
    npm_cache_write_probe) label="npm cache writable" ;;
    npm_install_probe) label="npm install into output prefix" ;;
    playwright_node_path_probe) label="playwright_node_path_probe" ;;
    playwright_node_bin_probe) label="playwright_node_bin_probe" ;;
    playwright_require_resolve_probe) label="Playwright require.resolve" ;;
    playwright_module_probe) label="Playwright Node module" ;;
    playwright_cache_read_probe) label="Playwright cache readable" ;;
    playwright_runner_exec_probe) label="WebKit runner executable" ;;
    playwright_webkit_page_probe) label="WebKit loads file:// page" ;;
    run_sh_zsh_status_probe) label="run_sh_zsh_status_probe" ;;
    *) label="$name" ;;
  esac
  if [[ "$value" == ok* ]]; then
    printf '  [OK]   %-28s %s\n' "$label" "$value"
  else
    printf '  [FAIL] %-28s %s\n' "$label" "$value"
  fi
}

append_selftest_log() {
  local name="$1"
  local value="$2"
  printf '%s=%s\n' "$name" "$value" >> "$SELFTEST_LOG"
  print_selftest_result "$name" "$value"
}

record() {
  local name="$1"
  local label="$2"
  shift 2
  local detail_file="$OUTPUT_DIR/run-sandbox-selftest-${name}.err"
  if "$@" >/dev/null 2>"$detail_file"; then
    append_selftest_log "$name" "ok"
    rm -f "$detail_file"
  else
    local detail
    if [[ "$name" == "playwright_webkit_page_probe" ]]; then
      detail="$(tail -n 12 "$detail_file" | tr '\n' ' ' | sed 's/[[:space:]][[:space:]]*/ /g; s/^ //; s/ $//' | cut -c1-240)"
    else
      detail="$(tr '\n' ' ' < "$detail_file" | sed 's/[[:space:]][[:space:]]*/ /g; s/^ //; s/ $//' | cut -c1-240)"
    fi
    if [[ -n "$detail" ]]; then
      append_selftest_log "$name" "fail ($detail)"
    else
      append_selftest_log "$name" "fail"
    fi
    if [[ "$name" == "playwright_webkit_page_probe" ]]; then
      cp "$detail_file" "$OUTPUT_DIR/run-sandbox-selftest-${name}-full.log"
    fi
    rm -f "$detail_file"
  fi
}

record_command() {
  local name="$1"
  local label="$2"
  local command_name="$3"
  local resolved
  resolved="$(command -v "$command_name" 2>/dev/null || true)"
  if [[ -n "$resolved" ]]; then
    append_selftest_log "$name" "ok ($resolved)"
  else
    append_selftest_log "$name" "fail"
  fi
}

printf '╔══════════════════════════════════════════════╗\n'
printf '║ Environment self-test                        ║\n'
printf '╚══════════════════════════════════════════════╝\n'

TMP_PROBE="/var/folders/50/mnp917ks6_zgm_pz0v3prqjw0000gn/T/run-loop-selftest.$$"
record tmp_write_probe "Temp write access" touch "$TMP_PROBE"
rm -f "$TMP_PROBE"

record python_tempfile_probe "Python tempfile" python3 -c 'import os, tempfile; fd, path = tempfile.mkstemp(prefix="run-loop-selftest-"); os.close(fd); os.unlink(path)'
record python_lxml_probe "Python import lxml" python3 -c 'import lxml'
record_command python3_path "python3 path" python3
record_command git_path "git path" git
record_command ssh_path "ssh path" ssh
record python_version_probe "python3 --version" python3 --version
record python_pip_probe "python3 -m pip" python3 -m pip --version
record git_version_probe "git --version" git --version
record ssh_version_probe "ssh -V" ssh -V

OUTPUT_PROBE="$OUTPUT_DIR/run-loop-selftest.$$"
OUTPUT_LINK="$OUTPUT_DIR/run-loop-selftest-link.$$"
record output_write_probe "Output write" sh -c 'printf selftest > "$1"' sh "$OUTPUT_PROBE"
record output_read_probe "Output read" test -s "$OUTPUT_PROBE"
record output_symlink_probe "Output symlink create" ln -sf "$OUTPUT_PROBE" "$OUTPUT_LINK"
record output_symlink_target_probe "Output symlink resolve" test "$(readlink "$OUTPUT_LINK" 2>/dev/null || true)" = "$OUTPUT_PROBE"
rm -f "$OUTPUT_LINK" "$OUTPUT_PROBE"

record npm_cache_path_probe "npm cache path" \
  sh -c 'test "$(npm config get cache)" = "$NPM_CONFIG_CACHE"'
record npm_cache_write_probe "npm cache writable" \
  sh -c 'probe="$NPM_CONFIG_CACHE/run-loop-selftest.$$"; : > "$probe" && rm -f "$probe"'
record github_key_read_probe "GitHub SSH key readable" test -r "$GITHUB_SSH_KEY_PATH"

# Regression checks for the Playwright/WebKit conditions that previously failed.
PLAYWRIGHT_WEBKIT_RUNNER="$HOME/Library/Caches/ms-playwright/webkit-2336/pw_run.sh"

# Local node_modules can be lost across reboots since only $OUTPUT_DIR is
# writable per the sandbox profile above. Install missing deps there (npm
# --prefix) rather than into the default (blocked) location, and point
# NODE_PATH at the resulting lib/node_modules so require("playwright")
# resolves. Only runs when the prefix directory is missing, to avoid
# reinstalling on every loop iteration.
NPM_INSTALL_PREFIX="$OUTPUT_DIR/npm-prefix"
if [[ -d "$OUTPUT_DIR" ]]; then
  if [[ ! -d "$NPM_INSTALL_PREFIX/node_modules/playwright" ]]; then
    record npm_install_probe "npm install into output prefix" \
      npm install --prefix "$NPM_INSTALL_PREFIX" playwright@^1.62.1
  fi
  export NODE_PATH="$NPM_INSTALL_PREFIX/node_modules${NODE_PATH:+:$NODE_PATH}"
  printf 'playwright_node_path_probe=ok (%s)\n' "$NODE_PATH" >> "$SELFTEST_LOG"
  printf 'playwright_node_bin_probe=ok (%s)\n' "$(command -v node 2>/dev/null || echo missing)" >> "$SELFTEST_LOG"
  record playwright_require_resolve_probe "Playwright require.resolve" \
    node -e 'console.log(process.env.NODE_PATH); console.log(require.resolve("playwright"))'
fi

record playwright_module_probe "Playwright Node module" node -e 'require("playwright")'
record playwright_cache_read_probe "Playwright cache readable" test -r "$PLAYWRIGHT_WEBKIT_RUNNER"
record playwright_runner_exec_probe "WebKit runner executable" test -x "$PLAYWRIGHT_WEBKIT_RUNNER"
WEBKIT_FILE_PROBE="$OUTPUT_DIR/run-loop-selftest-webkit-file.$$.html"
printf '%s\n' '<!doctype html><title>self-test</title><h1>ok</h1>' > "$WEBKIT_FILE_PROBE"
export WEBKIT_FILE_PROBE
record playwright_webkit_page_probe "WebKit loads file:// page" perl -e 'alarm shift; exec @ARGV' 15 env DEBUG="pw:browser,pw:protocol" PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright" node -e '
const { webkit } = require("playwright");
const { pathToFileURL } = require("node:url");
(async () => {
  const browser = await webkit.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 320, height: 240 } });
  const page = await context.newPage();
  await page.goto(pathToFileURL(process.env.WEBKIT_FILE_PROBE).href, { waitUntil: "load", timeout: 5000 });
  if (await page.title() !== "self-test" || await page.textContent("h1") !== "ok") {
    throw new Error("unexpected file URL page content");
  }
  await browser.close();
})().catch(error => { console.error(error.stack || error); process.exit(1); });
'
rm -f "$WEBKIT_FILE_PROBE"
unset WEBKIT_FILE_PROBE

# zsh reserves `status`; ensure generated run scripts are checked for this
# recurring portability issue before execution.
if [[ -f "$RUN_SCRIPT_PATH" ]] && grep -Eq '(^|[[:space:]])status=' "$RUN_SCRIPT_PATH"; then
  printf '%s\n' 'run_sh_zsh_status_probe=fail (run script assigns the zsh read-only variable status)' >> "$SELFTEST_LOG"
else
  printf '%s\n' 'run_sh_zsh_status_probe=ok' >> "$SELFTEST_LOG"
fi
EOF
chmod u+x "$SELFTEST_SCRIPT"
: > "$SELFTEST_LOG"
set +e
if [[ "$SANDBOX_ENABLED" == true ]]; then
  /usr/bin/sandbox-exec -f "$SANDBOX_PROFILE_PATH" "$SELFTEST_SCRIPT"
else
  "$SELFTEST_SCRIPT"
fi
SELFTEST_STATUS=$?
set -e
rm -f "$SELFTEST_SCRIPT"
echo
printf '  Log file: %s\n' "$SELFTEST_LOG"
if (( SELFTEST_STATUS != 0 )) || grep -q '=fail' "$SELFTEST_LOG"; then
  SELFTEST_STATUS=1
  printf '  Result: FAILED\n' >&2
else
  printf '  Result: PASSED\n'
fi

if [[ "$SELF_TEST_ONLY" == true ]]; then
  exit "$SELFTEST_STATUS"
fi
fi

save_counter

if [[ ! -f "$GITHUB_ID_FILE" ]]; then
  printf '%s\n' 'REPLACE_WITH_GITHUB_USERNAME' > "$GITHUB_ID_FILE"
fi

echo "Watching $RUN_SCRIPT_PATH"
echo "Persistent counter starts at: $NUM"
if [[ "$ONCE" == true ]]; then
  echo "Operation mode: ONE-SHOT"
elif [[ "$CYCLIC" == true ]]; then
  echo "Operation mode: CYCLIC (${CYCLE_TIME_SECONDS}s between runs)"
else
  echo "Operation mode: WATCH"
fi
if [[ "$SANDBOX_ENABLED" == true ]]; then
  echo "Run sandbox: ENABLED ($SANDBOX_PROFILE_PATH)"
else
  echo "Run sandbox: DISABLED"
fi
echo "GitHub SSH key path: $GITHUB_SSH_KEY_PATH"
echo "GitHub user file: $GITHUB_ID_FILE"
echo "npm cache: $NPM_CONFIG_CACHE"
echo "Post-run notification wait: ${NOTIFY_WAIT_SECONDS}s"
echo "Current run log: $CURRENT_LOG_LINK"
printf 'Run-script sentinel: %s\n' "$SENTINEL_TEXT"
if [[ -n "$SIGNAL_PID" ]]; then
  echo "Completion notification: SIGUSR1 to PID $SIGNAL_PID"
else
  echo "Completion notifier: $NOTIFIER_COMMAND"
fi

while true; do
  if [[ ! -f "$RUN_SCRIPT_PATH" ]]; then
    sleep "$SLEEP_SECONDS"
    continue
  fi

  chmod u+x "$RUN_SCRIPT_PATH"
  if [[ "$SANDBOX_ENABLED" == true ]]; then
    write_sandbox_profile
  fi

  if [[ -f "$GITHUB_ID_FILE" ]]; then
    GITHUB_USER="$(tr -d '\r' < "$GITHUB_ID_FILE" | head -n 1)"
  else
    GITHUB_USER=""
  fi

  export GITHUB_SSH_KEY_PATH
  export GITHUB_SSH_DIR
  export GITHUB_USER
  export GIT_SSH_COMMAND="ssh -i \"$GITHUB_SSH_KEY_PATH\" -o IdentitiesOnly=yes -o UserKnownHostsFile=\"$OUTPUT_DIR/github-known_hosts\""

  started_at_human="$(date '+%Y-%m-%d %H:%M:%S %Z')"
  started_at_stamp="$(date '+%Y-%m-%d_%H-%M-%S')"
  archive_base="run-${started_at_stamp}-n$(printf '%04d' "$NUM")"
  log_path="$ARCHIVE_DIR/${archive_base}.log"
  script_path="$ARCHIVE_DIR/${archive_base}.sh"

  : > "$log_path"
  ln -sf "$log_path" "$CURRENT_LOG_LINK"
  ln -sf "$RUN_SCRIPT_PATH" "$CURRENT_SCRIPT_LINK"

  echo
  echo "[$started_at_human] starting $RUN_SCRIPT_NAME (#$NUM)"
  echo "[$started_at_human] log: $log_path"
  if [[ "$SANDBOX_ENABLED" == true ]]; then
    echo "[$started_at_human] run sandbox: ENABLED ($SANDBOX_PROFILE_PATH)"
  else
    echo "[$started_at_human] run sandbox: DISABLED"
  fi
  echo "[$started_at_human] github ssh key path: $GITHUB_SSH_KEY_PATH"
  echo "[$started_at_human] github user: ${GITHUB_USER:-<unset>}"
  echo "[$started_at_human] npm cache: $NPM_CONFIG_CACHE"

  if kill_applescript_if_requested; then
    status=0
    printf '%s\n' "Sentinel found in $RUN_SCRIPT_NAME; killed the AppleScript without executing the run script." | tee -a "$log_path"
  else
    suspend_applescript
    set +e
    if [[ "$SANDBOX_ENABLED" == true ]]; then
      /usr/bin/perl -e 'alarm shift; exec @ARGV' "$GUARD_SECONDS" \
        /usr/bin/sandbox-exec -f "$SANDBOX_PROFILE_PATH" "$RUN_SCRIPT_PATH" 2>&1 | tee -a "$log_path"
      status=${PIPESTATUS[0]}
    else
      /usr/bin/perl -e 'alarm shift; exec @ARGV' "$GUARD_SECONDS" \
        "$RUN_SCRIPT_PATH" 2>&1 | tee -a "$log_path"
      status=${PIPESTATUS[0]}
    fi
    set -e
    resume_applescript
  fi

  finished_at_human="$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf '\n[%s] finished %s (#%s) with exit code %s\n' "$finished_at_human" "$RUN_SCRIPT_NAME" "$NUM" "$status"
  printf '[%s] exit_code=%s\n' "$finished_at_human" "$status" >> "$log_path"

  completion_message="$RUN_SCRIPT_NAME (#$NUM) finished with exit code $status. Find the output under $CURRENT_LOG_LINK"
  send_completion_notification "$completion_message" "$finished_at_human" "$log_path"

  if [[ "$CYCLIC" == true ]]; then
    cp -p "$RUN_SCRIPT_PATH" "$script_path"
  else
    mv "$RUN_SCRIPT_PATH" "$script_path"
  fi
  ln -sf "$script_path" "$CURRENT_SCRIPT_LINK"

  NUM=$((NUM + 1))
  save_counter

  if [[ "$ONCE" == true ]]; then
    exit "$status"
  fi

  if [[ "$CYCLIC" == true ]]; then
    sleep "$CYCLE_TIME_SECONDS"
  else
    sleep "$SLEEP_SECONDS"
  fi
done
