---
schema_version: "1.0"
id: "0037-48"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1984"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

Qualify and freeze the legacy singleton runner bootstrap for sandboxed/grunt execution before any other Feature `0037` Task starts. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-48:a7f3c1e29b04`). Abgenommene Baseline `e3a176aeb8e10a0d08a977e08db1aaec6d69cb4f`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). 9 Evidenzdateien, Claimdatei, Singleton-Slot-Zustand verifiziert; Fixture-Commits erwartungsgemäss nur im verworfenen Fixture-Repo, nicht im echten.

## Scope

- **Closed (2026-08-16):** Discovery resolved `base_commit: df7e8794bbebde6fc73fc82b0e06dca7b73530fb` (request `b2e91f6d4a83`, exit 0). Qualification transaction (request `c491a08e5f76`, exit 0, `validation=passed mutation=none_to_real_repo`) proved on an isolated throwaway fixture repo: base-match fail-closed guard, substantive commit `c04abfe37be2dcdf0ab809a7d79f682a49846202` (reachability-verified), a distinct second bookkeeping/REF commit `fb2622ccee1f7abd68c6570061c82d4b4280e590` (two-commit closure), an injected-failure recovery check (fixture HEAD unchanged, exit status 1), and zero mutation to the real repo (HEAD/status unchanged throughout). Nine evidence files retained under `logs/runner-qualification-0037-48/c491a08e5f76/`, verified present. Singleton slot confirmed absent post-execution. See `TODO-perplexity-0037-48-a7f3c1e29b04.md` for full evidence trail.
  - REF: e3a176aeb8e10a0d08a977e08db1aaec6d69cb4f
  - **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-48-a7f3c1e29b04.md`, `owner_token: agent:perplexity:0037-48:a7f3c1e29b04`, request ID `a7f3c1e29b04`, `base_commit: pending-discovery`. Self-selected per `AGENTS.md` rule 3 as the mandatory first Feature `0037` pickup; the two pre-existing claim files are Feature 0034 scoped, carry no matching owner token, and were left untouched. Holds exclusive singleton runner scope for Feature `0037` until queue activation.
  - **Progress (2026-08-16):** Discovery attempt 1 FAILED CLOSED, runner exit status 20. The claim turn exhausted its tool budget and prematurely recorded publication, so no `run.sh` actually existed; the runner correctly rejected the request with `ERROR missing required path: run.sh` and reported `validation=failed mutation=none`. This is the intended fail-closed behavior on a missing declared input and is retained as positive qualification evidence for the preflight guard. Base commit remains UNRESOLVED (`pending-discovery`); no commits, no executed mutations, no validation claimed.
  - **Progress (2026-08-16):** Discovery attempt 2 published — the real fixed-profile read-only `run.sh` (`expected_base: discover`, request `a7f3c1e29b04`, owner_token asserted) now occupies the singleton slot with seven read-only phases, fail-closed preflight/claim/authority guards, `--no-optional-locks` Git reads, a `mktemp` staging dir removed by a cleanup trap, and a before/after HEAD+status byte-identity zero-mutation proof. Awaiting the runner result to resolve `pending-discovery` before any mutating request.
  - **Qualification finding RETRACTED (2026-08-16):** The earlier "all probes OK but Result: FAILED" self-test inconsistency is NOT a runner defect. On run #256 the identical all-`[OK]` probe set reported `Result: PASSED`, so the aggregate verdict on run #255 was reporting the exit status of the *requested script* (the missing-`run.sh` rejection), not a broken probe aggregation. The finding is withdrawn and does not block the Definition of Done.
  - **Progress (2026-08-16):** Discovery attempt 2 FAILED CLOSED, runner exit status 20, `mutation=none`. Preflight passed required-paths and git-dependency gates, then correctly rejected the request: `ERROR claim ... does not carry owner_token agent:perplexity:0037-48:a7f3c1e29b04`. Root cause is a self-inflicted format mismatch, not a runner or authority defect: the claim recorded the field as a Markdown list item with a backticked key (``- `owner_token`: agent:...``), while the guard greps the literal string `owner_token: agent:...`. Fixed by writing `request_id`, `owner_token`, and `base_commit` as plain unquoted `key: value` lines in the claim, with a note forbidding reintroduction of backticked keys. Base commit still UNRESOLVED (`pending-discovery`); no commits, no executed mutations, no validation claimed.
  - **Qualification evidence accumulated so far (2026-08-16):** Two independent fail-closed branches of the singleton bootstrap are now proven with retained logs and zero mutation — (a) missing declared input path, run #255, archived `output/run-archive/run-2026-08-16_02-56-07-n0255.log`; (b) active-claim/owner_token validation mismatch, run #256, archived `output/run-archive/run-2026-08-16_02-57-35-n0256.log`. Both retained the claim and left `0037-48` `[p]` exactly as the recovery contract requires. Runner environment: `python3 /usr/bin/python3`, `git /usr/bin/git`, `ssh /usr/bin/ssh`, lxml importable, Playwright/WebKit loads `file://`, run sandbox ENABLED via `output/run.sandbox.sb`, one-shot mode.

## Acceptance criteria

- **AC-001** If no Task is assigned, the first sandboxed agent deterministically self-selects this open/unclaimed Task, mints a collision-resistant request ID and derived immutable session `owner_token`, creates the matching task-scoped claim with `base_commit: pending-discovery`, and exclusive singleton runner scope, marks `0037-48` `[p]`, and serializes all Feature `0037` runner use until queue activation. It then publishes the fixed-profile claimed read-only `run.sh` with `expected_base: discover`
- **AC-002** the runner accepts only the matching active claim/request, rejects conflicts, returns exact HEAD, authority state, working-tree/index status, active claims, and slot state with zero mutation, and cleans the slot. The agent records the returned base before mutation. Execute one bounded self-contained qualification transaction on isolated fixtures proving preflight, validation, timeout/progress/result capture, path/mutation guards, cleanup, path-limited substantive commit, capture/reachability of its hash, exact second bookkeeping/REF commit, claim retention on every injected partial failure, and singleton cleanup/recovery. The qualification transaction may close this Task only after all fixture gates pass and must preserve unrelated staged/unstaged/untracked work

## Definition of Done

Retained runner script/log/result and before/intermediate/final Git status/tree evidence identify the runner environment and prove autonomous Task pickup, pending-discovery resolution, active-claim/request validation, one-owner serialization, successful two-commit closure, and every recovery branch without user or privileged-agent execution. Failure keeps `0037-48` `[p]` and blocks all other Feature `0037` work.
