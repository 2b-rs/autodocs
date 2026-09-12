---
schema_version: "1.0"
id: "0040-03"
level: "task"
parent: "0040"
state: "closed"
visibility: "internal"
prerequisites:
  - "0040-01"
  - "0040-10"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:512"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0040-03:0040-01, 0040-03:0040-10 Define the mandatory decision record — time, deciding identity, technical justification — and the criterion that determines which decisions require one. REF: `7bca09caeea83b8e26e2d69dd4f837eaa2317f39`.

## Scope

- **Claim (2026-08-18):** Project-managed implementation via `TODO-zed-0040-03-20260818T154851Z-1d9d90dcf61d.md`; owner_token `agent:zed:0040-03:20260818T154851Z-1d9d90dcf61d`; branch `0040-03`; isolated worktree `.worktrees/0040-03`.
  - **Corrective claim (2026-08-19):** Current-user-authorized English documentation correction via `TODO-worf-0040-03-20260819T000400Z-corrective-4b8d7e.md`; owner_token `agent:worf-lursa-20260819t000400z:0040-03:20260819T000400Z-corrective-4b8d7e`; canonical branch `0040-03`; isolated worktree `.worktrees/0040-03`. This temporarily reopened implementation only; the prior implementation and acceptance history remain immutable.
  - **Corrective implementation REF (2026-08-19):** `baeb530b6eeaf03b675bb4abd012020cc9b1fe4c` — English translation of the Task-owned normative process documentation; schema literals, identifiers, provisional-record history, and acceptance history were preserved.
  - **Requirements covered:** `RQ-DEC-01`, `RQ-DEC-02`, `RQ-DEC-03`, `RQ-DEC-04`, `RQ-DEC-05`.
  - **Context:** This is the direct answer to `T6`. The scoping decision behind `0038-03` is nowhere recorded, so it could neither be reviewed nor found afterwards. The **blast-radius criterion** of `RQ-DEC-05` is the load-bearing part: difficulty and unfamiliarity are explicitly *not* triggers — reach is. A decision that can block other work units is always recordable, whether or not it looked hard at the time.
  - **Implementation completion (2026-08-18):** `decision-record@v1` now defines exact identifiers, timestamp/identity grammars, closed mandatory triggers, alternatives, consequences, affected units/gates, review participation, bounded waiver duration, and deterministic append-only correction bytes. Acceptance and integration verdicts remain specialized formats that reference separate decisions when needed. The four provisional Feature decisions remain byte-identical and are truthfully dispositioned through `decision-record-legacy-map@v1`: all are structurally legacy; `DEC-0040-002` … `004` are semantically complete, while `DEC-0040-001` remains incomplete only at management-owned `Waiver.Duration`. The authorized non-Task coordination record remains an explicit unsuppressed legacy-doctor limitation. Independent peer review passed after two remediation rounds; 35 links, content/preservation checks, full automation safety, and `git diff --check` passed. The global legacy doctor still reports 380 findings including the exact documented mismatch, so no global doctor pass is claimed. This node is not an integration checkpoint; no `Acceptance: ✓` is created.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** defines a record format without mutating existing records; the migration of `DEC-0040-001` … `-004` is additive and reversible. Aggregate review at `0040-09`.
  - **Carried finding (2026-08-18, found while creating this Feature):** `_src/tools/legacy_task_doctor.py` models only Task claims. `AGENTS.md` explicitly permits a **temporary coordination record for a user-directed activity that is not an existing Task**, but that shape has no schema: such a record necessarily carries an `owner_token` without a Task ID and is reported as `LTD-CLAIM-IDENTITY-MISMATCH`. The token cannot be retrofitted, because `AGENTS.md` declares a minted `owner_token` immutable — so conforming to the tool would require breaking a stronger rule. This Task defines the record format; either it extends the model to cover coordination records, or it records why the deviation stays permanent. Live example and reasoning: `TODO-claude-re-intake-20260818T003223Z-845170c0e4da.md`, section *Bekannte Abweichung*.

## Acceptance criteria

- **AC-001** A normative `docs/pipeline/decision-record.md` defines a record with stable ID, ISO-8601 timestamp including timezone, deciding identity as a session/role identity rather than a display name, subject, decision, technical justification, considered alternatives, and consequences. Records are append-only
- **AC-002** corrections add rather than replace, consistent with `task-acceptance.md`. The document states which decisions are mandatory, with the blast-radius criterion normative and at least three worked positive and two negative examples. The provisional records `DEC-0040-001` … `DEC-0040-004` are migrated into the final format, or the deviation is explicitly recorded. Where a decision is a bounded authority waiver, the record must carry scope and compensating control, as `DEC-0040-001` does

## Definition of Done

Committed with real `REF`; the format is machine-checkable in principle (fields, types, required-ness stated unambiguously) even if the checker itself belongs to `0040-04`; the existing acceptance and integration-verdict records are shown to be compatible with, or explicitly excluded from, the format.
