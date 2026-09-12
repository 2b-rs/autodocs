---
schema_version: "1.0"
id: "0043-01"
level: "task"
parent: "0043"
state: "open"
visibility: "internal"
prerequisites:
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:694"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

Repair run correlation: every publication run sets `RUN_ARCHIVE_REF`, and `combine` cannot starve on missing cohorts. **Acceptance: ✓** (2026-08-24, Integratorin `belanna`, unabhängig von Implementierer `agent:seven-icheb:0043-01:20260821T062923Z`). Abgenommene Baseline `d4741e906`; Review-REF `d8834121b` (`review-0043-04-belanna-20260823T212600Z`, induzierte prerequisite-closed Batch zum Checkpoint `0043-04`).

## Scope

- **Requirements covered:** `RQ-BR-02`.
  - **Context (finding B2):** `generate.py:176`, `validate.py:679`, `i18n_translate.py:60`, and `i18n_diagrams.py:49` already emit the field; only the setter is missing. The hardened fail-closed `combine` is correct and stays — the producers are brought up to it, not the gate loosened.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** wiring an existing field's setter; success is objectively checkable by one real combined report. Re-examined at `0043-07`.
  - **Completion (agent:seven-icheb:0043-01:20260821T062923Z, 2026-08-21, branch `0043-01`, REF `6786bcc70233331c3622e4267433bdd04ff058fa`):** `runner-host/run-loop.sh` now exports `RUN_ARCHIVE_REF="run-archive/${archive_base}"` before running the watched script; `_src/tools/build_report.py` gained a `mint-ref` subcommand minting a distinguishably `manual-`-prefixed fallback ref for out-of-runner builds; `_src/WARTUNG.md` documents both paths; `docs/pipeline/build-report-schema.md` documents both valid `run_archive_ref` producers (backward compatible, no schema bump). Validated with a real full build: `generate.py`, `validate.py`, `i18n_translate.py merge en`, `i18n_diagrams.py en` all wrote subreports sharing `run_archive_ref="manual-20260821T062231Z-3d0abeb5"`; `build_report.py combine` aggregated all 4 required stages into one cohort with that shared non-null ref (no starvation); combine's own `exit_code 1` reflects pre-existing unrelated dead-link findings from `validate.py`, not a correlation failure. Full validation log and evidence in `TODO-seven-icheb-0043-01-20260821T062923Z.md`. No merge to `0043`/`main` performed by this claim.

## Acceptance criteria

- **AC-001** The runner lifecycle and the documented manual build path (`WARTUNG.md`) both export a valid `RUN_ARCHIVE_REF` naming the run-archive pair
- **AC-002** a defined fallback mints a cohort ID for builds outside the runner so `combine` still correlates them (distinguishably marked)
- **AC-003** a real full build yields subreports with one shared non-null ref and a successful `combine` against real data

## Definition of Done

Committed; a real run's combined report exists with `run_archive_ref` set; `WARTUNG.md` documents the variable; no producer schema change breaks `docs/pipeline/build-report-schema.md` (extend it if needed).
