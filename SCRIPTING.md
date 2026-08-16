# run.sh — Known Environment Issues and Fixes

This file records sandbox/tooling quirks discovered while writing `run.sh`
scripts for this project, so future agents don't re-diagnose them from
scratch. Append new entries; do not delete resolved ones (mark them instead).

## 1. `timeout` is not available (macOS runner)

**Symptom:** `run.sh` exits 127 with `line N: timeout: command not found`.

**Cause:** The runner executes on macOS. `timeout(1)` is a GNU coreutils
utility and is not installed by default on macOS/BSD userland. Any `run.sh`
that writes `timeout 60s some_command ...` will fail before `some_command`
ever starts.

**Fix:** Do not depend on `timeout`. Use a portable background-process +
watchdog pattern instead, e.g.:

```bash
some_command &
cmd_pid=$!
( sleep 60; kill -TERM "${cmd_pid}" 2>/dev/null ) &
watchdog_pid=$!
wait "${cmd_pid}"
cmd_status=$?
kill "${watchdog_pid}" 2>/dev/null
```

**Status:** Open — must be applied to every `run.sh` job that needs a hard
timeout (e.g. the Playwright/WebKit checker, which has previously hung).

## 2. `npm ci` / `npm install` fail with `EPERM` on root-owned cache files

**Symptom:** `npm error code EPERM ... Your cache folder contains root-owned
files`, pointing at `/Users/tobias.anton/.npm/_cacache/...`.

**Cause:** The user's global npm cache directory contained root-owned files
from a prior `sudo npm` invocation outside this project. This blocked writes
from the (non-root) runner sandbox.

**Fix applied:** User resolved this externally (cache ownership corrected).
No `run.sh` change was needed once fixed.

**Fallback option (not currently used):** If this recurs and cannot be fixed
out-of-band, redirect npm's cache into the project sandbox instead of `~/.npm`:

```bash
export npm_config_cache="$(pwd)/.npm-cache"
npm install
```

**Status:** Resolved (2026-08-15, externally by user).

## 3. Validation job called `check_review_request_ui.cjs` with no argument

**Symptom:** Job prints `usage: node check_review_request_ui.cjs <html-file>`
and exits non-zero; looks like a failure but is actually a job-configuration
bug, not feature evidence.

**Cause:** The standalone `playwright_ui_check` job in `run.sh` invoked the
checker script without generating/pointing it at any HTML fixture first. The
script requires `process.argv[2]` to be a path to a rendered HTML page.

**Fix:** Any `run.sh` job that calls `check_review_request_ui.cjs` directly
(outside of pytest, which builds its own fixture) must first render a fixture
page via `lib_docmodel.render_page` (see the `generate_fixture` step) and pass
its path as the sole argument.

**Status:** Resolved in the diagnostic `run.sh` variant (2026-08-15).

## 4. Checker/WebKit launch appears to hang under pytest's subprocess call

**Symptom:** `test_browser_flow_exported_not_submitted` fails with
`subprocess.TimeoutExpired` after the test's own hardcoded 30s timeout; zero
console/page output is captured, suggesting the hang happens at or before
`webkit.launch()`, not inside the page-interaction logic.

**Status:** RESOLVED (diagnosis) — not an environment issue. A debug run with
`DEBUG=pw:browser,pw:api` and the portable watchdog (item 1) shows WebKit
launches, navigates, and successfully clicks `[data-review-request-open]`
within ~1.3s. The hang is `page.selectOption` waiting 30s for
`locator('[data-category]')`, which never appears after the trigger click.
This is a real defect candidate in `review_request.js` (dialog/category
select not rendering or not gaining the `data-category` attribute after the
trigger click), not a sandbox/Playwright/WebKit problem. See
TODO-perplexity.md progress log for the finding and next action on Task
0021-05.

**Full debug trace (for reference):** click on `[data-review-request-open]`
succeeds at T+~1.3s; `page.selectOption` on `[data-category]` then times out
at 30000ms with no further console/page errors logged by the checker script
itself (the checker only reports page errors caught via its own `pageerror`
listener, so this dialog-open path may need additional checker
instrumentation to capture DOM state at the point of failure).
