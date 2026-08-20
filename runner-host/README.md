# `runner-host/` — tracked source for the privileged host execution environment

## What this package is

This directory holds the **tracked source** of the four scripts that make up the
privileged host side of the sandbox/runner architecture described in
[`SANDBOX.md`](../SANDBOX.md) and [`docs/pipeline/tools.md`](../docs/pipeline/tools.md):

| File | Role |
|---|---|
| `run-loop.sh` | Legacy watch-/one-shot runner: sandbox setup, environment self-test, explicit first-time initialization via `--init`, and dispatch of the singleton `run.sh` slot. |
| `perplexity-cpu-loop.js` | Host-side JXA (`osascript -l JavaScript`) CPU/process-state watch loop used to detect when the driving agent process is idle. |
| `perplexity-echo.as` | Host-side AppleScript notifier: injects one prompt into the Perplexity app window. |
| `perplexity-loop.applescript` | Host-side AppleScript continuation-prompt loop that repeatedly re-prompts the driving agent. |

These files were relocated here from `_src/` by Task `0038-24` (see `TODO.md`)
without functional modification (only the one internal cross-reference from
`run-loop.sh` to `perplexity-echo.as` was updated to the new relative path).
The exact digests of the current tracked content are pinned in
[`MANIFEST.json`](MANIFEST.json).

## Tracked source vs. installed/running host service — read this before assuming anything is "live"

**Nothing in this directory is, by itself, a running service.** These are the
files an operator installs and runs manually on a macOS host outside the
sandbox to bootstrap and drive an agent session against a worker clone (see
`issues/_policy/runner-service.json` for the one operator's actual current
deployment record — `repo_path`, `runner_executable`, launch/health/restart/
rollback/revocation paths — which is host-specific operational data, not part
of this tracked-source package).

This package makes **no** claim that:

- any of these scripts is currently running anywhere;
- installing/qualifying/activating a live instance has been performed by
  Task `0038-24` or by committing this package;
- any external resource, credential, or network endpoint has been provisioned,
  contacted, or verified;
- privileged qualification (independent review of this code path's actual
  runtime behavior, sandbox profile correctness, or operational safety) has
  been performed here. That remains a separate, explicitly privileged
  activity and is unaffected by this package's existence — it still applies
  through manifest/path-bound checks against these files, at whatever point
  it is performed.

## What ordinary sandboxed Task validation does and does not do against this package

A sandboxed/grunt agent cannot execute shell, `osascript`, or Node directly
(`SANDBOX.md`) — this is a **capability-class** restriction, not a
package-specific exclusion. Ordinary sandboxed Task validation therefore never
invokes `run-loop.sh`, `perplexity-cpu-loop.js`, `perplexity-echo.as`, or
`perplexity-loop.applescript` as a live process, and never will, regardless of
where these files live in the tree.

What ordinary sandboxed validation **does** do against this package, and
continues to do after the move, because these are static, non-executing
checks runnable through the sandboxed-agent runner:

- `_src/tools/automation_safety.py` (invoked by `_src/validate.py`) statically
  scans `runner-host/run-loop.sh` for the same mutating-call safety rules it
  scanned `_src/run-loop.sh` for before the move — relocating the file does
  **not** remove it from `tracked_automation_paths()`'s scan, because that
  scan selects targets by file extension across all tracked paths, independent
  of directory. The package is not hidden from this scan; see
  `_src/tools/automation_safety_policy.json` for the current disposition
  entries against this file (owned by Task `0040-10`, which independently
  repairs the file's automation-safety findings — see the "Interaction with
  `0038-24`" note under both Tasks in `TODO.md`).
- `_src/tools/chore_tool_inventory.py --check` cross-references this package's
  tracked `.sh` file against the live tracked-script enumeration.
- Manifest/digest verification (`MANIFEST.json` above) is a plain hash
  comparison, runnable anywhere.

This division — static analysis and manifest verification always run through
the ordinary sandboxed validation profile; live execution never does, by
capability class — is the intended boundary. It is enforced by what a
sandboxed/grunt agent's tools can physically do, not by an added exclusion
rule that would hide this package from scanning.

## Non-host `_src/` sources are unaffected

This move relocates exactly these four files. It does not relocate, rename, or
duplicate any other `_src/` source. See [`_src/README.md`](../_src/README.md)
for the map of what remains under `_src/` and the deferred clustering plan for
that tree.
