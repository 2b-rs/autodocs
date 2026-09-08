---
schema_version: "1.0"
id: "0038-11"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-04"
  - "0038-10"
  - "0038-12"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1726"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

PREREQ: 0038-11:0038-04, 0038-11:0038-10, 0038-11:0038-12 Implement claim-aware artifact quarantine, retention, and garbage collection. REF: `5246557ec96725bcb9c5656736908de99385da83` **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-11-Commit)`). Abgenommene Baseline `5246557ec96725bcb9c5656736908de99385da83`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). 27/27 Tests, automation_safety PASS 6/0/0/0 — exakt wie behauptet.

## Scope

- **Completion evidence (2026-08-20):** Added `_src/tools/artifact_retention.py` (`quarantine_artifact()` for run-specific `.partial` quarantine of partial/failed/interrupted/superseded artifacts with `artifact-quarantine@v1` side-cars; `plan_gc()`/`gc()` dry-run-first classifier/deleter over `output/logs/<task-id>/**` into `successful-log`/`failed-trace`/`cache`/`scratch`/`permanent-manifest` tiers, refusing live claims, unfinalized `0038-10` journals, unknown state, and the `current.json` pointer target, and cross-checking `0038-12` `task-evidence-pack@v1` manifest references before any deletion; real deletion opt-in via `--apply`) and its hermetic test module `_src/tests/test_artifact_retention.py` in `5246557ec` on branch `0038-11` (based off Feature branch `0038` at `41f70cc72`, fast-forward merging prerequisite branch `0038-10` to tip `539ea06bb` then `0038-12` to tip `284b51e9f`; prerequisite `0038-09`/`0038-04` were already present on `0038`). 27/27 tests passed, covering all nine named Definition-of-Done fixtures (fixed-path export deletion, empty service-error files, failed-sentinel outputs, empty request directories, interrupted attempts, reused log names, live claims, clock skew, rollback) plus quarantine-API, permanent-manifest, current-pointer, TTL-tier, task-id-filter, and CLI dry-run/apply coverage. `python3 -m py_compile` passed on both files. `python3 _src/tools/automation_safety.py --path _src/tools/artifact_retention.py --json` returned `verdict: PASS`, `unresolved_critical: 0`, `disposed_critical: 0` (6 advisory, non-critical `AUTO010` findings on the `shutil.rmtree`/`unlink` calls inside `apply_gc()`, expected for a deletion tool gated behind `--apply`); the same check on the test module returned `PASS` with zero findings. Claim `TODO-seven-marla-0038-11-20260820T025849Z.md` travels on branch `0038-11` per `docs/pipeline/branch-workflow.md`; branch left at rest, not merged into `0038`/`main` by this unprivileged session.

## Acceptance criteria

- **AC-001** Partial/failed translations, exports, generated trees, reports, and scratch attempts use run-specific `.partial`/quarantine roots plus structured state/error/source/output digests and retry eligibility. A dry-run GC removes only terminal, unowned artifacts after policy TTL
- **AC-002** refuses live claims, unfinalized journals, and unknown state
- **AC-003** prunes safe empty tombstones
- **AC-004** and applies explicit successful-log, failed-trace, cache, scratch, and permanent-manifest retention tiers

## Definition of Done

Fixtures cover fixed-path export deletion, empty service-error files, failed-sentinel outputs, empty request directories, interrupted attempts, reused log names, live claims, clock skew, and rollback; no retained evidence link silently points to a deleted artifact without a manifest/digest disposition.
