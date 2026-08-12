#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-$PWD}"
cd "$ROOT_DIR"

OUTPUT_DIR="$ROOT_DIR/output"
ARCHIVE_DIR="$OUTPUT_DIR/run-archive"
STATE_FILE="$OUTPUT_DIR/run-counter.state"
CURRENT_LOG_LINK="$OUTPUT_DIR/run-current.log"
CURRENT_SCRIPT_LINK="$OUTPUT_DIR/run-current.sh"
SLEEP_SECONDS=1
GUARD_SECONDS=300
APPLESCRIPT_PATTERN='perplexity-loop[.]applescript'
SUSPENDED_APPLESCRIPT_PIDS=()
SANDBOX_PROFILE_PATH="$OUTPUT_DIR/run.sandbox.sb"
GITHUB_SSH_DIR="${GITHUB_SSH_DIR:-$HOME/devel}"
GITHUB_SSH_KEY_PATH="${GITHUB_SSH_KEY_PATH:-$GITHUB_SSH_DIR/aradocs-runner-key/id_ed25519}"
GITHUB_ID_FILE="$OUTPUT_DIR/github-user.txt"

mkdir -p "$OUTPUT_DIR" "$ARCHIVE_DIR" "$GITHUB_SSH_DIR"

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
  if grep -Fq -- "He's dead, Jim!" "$ROOT_DIR/run.sh"; then
    pkill -KILL -f "$APPLESCRIPT_PATTERN" 2>/dev/null || true
    SUSPENDED_APPLESCRIPT_PIDS=()
    return 0
  fi
  return 1
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

save_counter
write_sandbox_profile

echo "Running environment self-test..."
SELFTEST_SCRIPT="$OUTPUT_DIR/run-sandbox-selftest.sh"
SELFTEST_LOG="$OUTPUT_DIR/run-sandbox-selftest.log"
export SELFTEST_LOG OUTPUT_DIR GITHUB_SSH_KEY_PATH
cat > "$SELFTEST_SCRIPT" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail

record() {
  local name="$1"
  local label="$2"
  shift 2
  local detail_file="$OUTPUT_DIR/run-sandbox-selftest-${name}.err"
  if "$@" >/dev/null 2>"$detail_file"; then
    printf '%s=ok\n' "$name" >> "$SELFTEST_LOG"
    rm -f "$detail_file"
  else
    local detail
    detail="$(tr '\n' ' ' < "$detail_file" | sed 's/[[:space:]][[:space:]]*/ /g; s/^ //; s/ $//' | cut -c1-240)"
    if [[ -n "$detail" ]]; then
      printf '%s=fail (%s)\n' "$name" "$detail" >> "$SELFTEST_LOG"
    else
      printf '%s=fail\n' "$name" >> "$SELFTEST_LOG"
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
    printf '%s=ok (%s)\n' "$name" "$resolved" >> "$SELFTEST_LOG"
  else
    printf '%s=fail\n' "$name" >> "$SELFTEST_LOG"
  fi
}

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

record github_key_read_probe "GitHub SSH key readable" test -r "$GITHUB_SSH_KEY_PATH"

# Regression checks for the Playwright/WebKit conditions that previously failed.
PLAYWRIGHT_WEBKIT_RUNNER="$HOME/Library/Caches/ms-playwright/webkit-2336/pw_run.sh"
record playwright_module_probe "Playwright Node module" node -e 'require("playwright")'
record playwright_cache_read_probe "Playwright cache readable" test -r "$PLAYWRIGHT_WEBKIT_RUNNER"
record playwright_runner_exec_probe "WebKit runner executable" test -x "$PLAYWRIGHT_WEBKIT_RUNNER"
record playwright_webkit_page_probe "WebKit creates a page" perl -e 'alarm shift; exec @ARGV' 15 env DEBUG="pw:browser,pw:protocol" PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright" node -e '
const { webkit } = require("playwright");
(async () => {
  const browser = await webkit.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 320, height: 240 } });
  const page = await context.newPage();
  await page.setContent("<!doctype html><title>self-test</title><h1>ok</h1>", { timeout: 5000 });
  if (await page.textContent("h1") !== "ok") throw new Error("unexpected page content");
  await browser.close();
})().catch(error => { console.error(error.stack || error); process.exit(1); });
'

# zsh reserves `status`; ensure generated run.sh scripts are checked for this
# recurring portability issue before execution.
if [[ -f "$ROOT_DIR/run.sh" ]] && grep -Eq '(^|[[:space:]])status=' "$ROOT_DIR/run.sh"; then
  printf '%s\n' 'run_sh_zsh_status_probe=fail (run.sh assigns the zsh read-only variable status)' >> "$SELFTEST_LOG"
else
  printf '%s\n' 'run_sh_zsh_status_probe=ok' >> "$SELFTEST_LOG"
fi
EOF
chmod u+x "$SELFTEST_SCRIPT"
: > "$SELFTEST_LOG"
set +e
"$SELFTEST_SCRIPT"
SELFTEST_STATUS=$?
set -e
rm -f "$SELFTEST_SCRIPT"

echo
printf '╔══════════════════════════════════════════════╗\n'
printf '║ Environment self-test                        ║\n'
printf '╚══════════════════════════════════════════════╝\n'
while IFS= read -r line; do
  key="${line%%=*}"
  value="${line#*=}"
  case "$key" in
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
    playwright_module_probe) label="Playwright Node module" ;;
    playwright_cache_read_probe) label="Playwright cache readable" ;;
    playwright_runner_exec_probe) label="WebKit runner executable" ;;
    playwright_webkit_page_probe) label="WebKit creates a page" ;;
    *) label="$key" ;;
  esac
  if [[ "$value" == ok* ]]; then
    printf '  [OK]   %-28s %s\n' "$label" "$value"
  else
    printf '  [FAIL] %-28s %s\n' "$label" "$value"
  fi
done < "$SELFTEST_LOG"
echo
printf '  Log file: %s\n' "$SELFTEST_LOG"
if grep -q '=fail' "$SELFTEST_LOG"; then
  printf '  Result: FAILED\n' >&2
else
  printf '  Result: PASSED\n'
fi

if [[ ! -f "$GITHUB_ID_FILE" ]]; then
  printf '%s\n' 'REPLACE_WITH_GITHUB_USERNAME' > "$GITHUB_ID_FILE"
fi

echo "Watching $ROOT_DIR/run.sh"
echo "Persistent counter starts at: $NUM"
echo "Outer sandbox: ENABLED ($SANDBOX_PROFILE_PATH)"
echo "GitHub SSH key path: $GITHUB_SSH_KEY_PATH"
echo "GitHub user file: $GITHUB_ID_FILE"

while true; do
  if [[ ! -f run.sh ]]; then
    sleep "$SLEEP_SECONDS"
    continue
  fi

  chmod u+x run.sh
  write_sandbox_profile

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
  ln -sf "$ROOT_DIR/run.sh" "$CURRENT_SCRIPT_LINK"

  echo
  echo "[$started_at_human] starting run.sh (#$NUM)"
  echo "[$started_at_human] log: $log_path"
  echo "[$started_at_human] outer sandbox: ENABLED ($SANDBOX_PROFILE_PATH)"
  echo "[$started_at_human] github ssh key path: $GITHUB_SSH_KEY_PATH"
  echo "[$started_at_human] github user: ${GITHUB_USER:-<unset>}"

  if kill_applescript_if_requested; then
    status=0
    printf '%s\n' "Sentinel found in run.sh; killed the AppleScript without entering the sandbox." | tee -a "$log_path"
  else
    suspend_applescript
    set +e
    /usr/bin/perl -e 'alarm shift; exec @ARGV' "$GUARD_SECONDS" \
      /usr/bin/sandbox-exec -f "$SANDBOX_PROFILE_PATH" ./run.sh 2>&1 | tee -a "$log_path"
    status=${PIPESTATUS[0]}
    set -e
    resume_applescript
  fi

  finished_at_human="$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf '\n[%s] finished run.sh (#%s) with exit code %s\n' "$finished_at_human" "$NUM" "$status"
  printf '[%s] exit_code=%s\n' "$finished_at_human" "$status" >> "$log_path"

  "$ROOT_DIR/_src/perplexity-echo.as" "run.sh (#$NUM) finished with exit code $status. Find the output under $ROOT_DIR/output/run-current.log" || \
    printf '[%s] warning: failed to notify Perplexity about exit code %s\n' \
      "$finished_at_human" "$status" >> "$log_path"

  mv run.sh "$script_path"
  ln -sf "$script_path" "$CURRENT_SCRIPT_LINK"

  NUM=$((NUM + 1))
  save_counter

  sleep "$SLEEP_SECONDS"
done
