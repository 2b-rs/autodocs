---
schema_version: "1.0"
id: "0043-02"
level: "task"
parent: "0043"
state: "closed"
visibility: "internal"
prerequisites:
  - "0043-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:702"
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
  - id: "AC-005"
    status: "active"
---

## Goal

PREREQ: 0043-02:0043-01 Introduce the tracked append-only build ledger. REF `56560fa2c` (branch `0043-02`, not merged). Claim: `TODO-seven-rebi-0043-02-20260821T080000Z.md` (`agent:seven-rebi:0043-02:20260821T080000Z`) **Acceptance: ✓** (2026-08-24, Integratorin `belanna`, unabhängig von Implementierer `agent:seven-rebi:0043-02:20260821T080000Z`). Abgenommene Baseline `946e5e4ab`; Review-REF `d8834121b`. Validierung unabhängig nachgefahren: Ledger- und Report-Tests 34/34.

## Scope

- **Requirements covered:** `RQ-BR-03`; implements `DEC-0043-001`.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** an append-only data file with tests; the CM-policy decision it rests on is already recorded as `DEC-0043-001`. Re-examined at `0043-07`.
  - **Implementation note (seven-rebi, `agent:seven-rebi:0043-02:20260821T080000Z`, 2026-08-21):** Ledger is `docs/evidence/build-ledger.jsonl` (JSON Lines, one line per publication run), written by `_src/tools/build_ledger.py` and appended by `build_report.py combine`/`publish`. Append-only is enforced in three layers: `O_APPEND`-only writes, idempotence per `run_archive_ref` (so `publish` after `combine` does not double-record), and `build_ledger.py verify --baseline=<rev>`, which requires the committed ledger to be a byte-exact prefix of the working copy and therefore detects a rewritten entry even when the rewrite is itself schema-valid. Raw logs stay git-ignored per the `DEC-0043-001` boundary; the ledger only references and SHA-256-pins them. Entry 1 is the backfilled historic 2026-08-13/14 run with honestly `null` `run_archive_ref`/`repo_commit` (it predates `0043-01`) and a `note` recording why. Schema and the consumer contract for `0043-03`/`0043-04`: `docs/pipeline/build-ledger.md`; also documented in `_src/WARTUNG.md`, `docs/pipeline/tools.md`, `docs/pipeline/README.md` and `docs/pipeline/build-report-schema.md`. **Validation:** `_src/tests/test_build_ledger.py` 26/26 pass (append, no-rewrite against a real throwaway git repo, malformed-entry detection); `_src/tools/test_build_report.py` 7/7 unchanged; plus a real end-to-end run — minted ref `manual-20260821T130403Z-d40f5b1d`, real `generate.py` (428 pages) and real `validate.py` (11 checks, 14 findings, run in a scratch venv since `lxml` is absent system-wide), then real `combine` (one entry appended, `repo_commit 7ba6f4e39`, `exit_code 1` because the two i18n stages did not run in this manual build) and real `publish` (no second entry). That proof run was directed at a scratch ledger so a partial diagnostic build does not enter the permanent, irreversible history. Branch `0043-02` left at rest, not merged; no `Acceptance: ✓` created, `DONE.md` untouched.

## Acceptance criteria

- **AC-001** A tracked, append-only ledger (one machine-readable entry per publication run: timestamp, `run_archive_ref`, repository commit, exit status, per-stage counters, findings count, combined-report digest) is written by `build_report.py` at `combine`/`publish` time
- **AC-002** its schema is documented
- **AC-003** entries are never rewritten
- **AC-004** raw logs stay git-ignored (`DEC-0043-001` boundary)
- **AC-005** the historical 2026-08-13/14 run is backfilled as the first entry, marked as backfilled

## Definition of Done

Committed with schema documentation and focused tests (append, no-rewrite, malformed-entry detection); the ledger location is named in `WARTUNG.md` and `docs/pipeline/`.
