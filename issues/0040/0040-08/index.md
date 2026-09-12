---
schema_version: "1.0"
id: "0040-08"
level: "task"
parent: "0040"
state: "open"
visibility: "internal"
prerequisites:
  - "0040-05"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:568"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0040-08:0040-05 Retrospectively assess the `0038-03` incident with the amended process as the first pilot, and record the disposition. REF: `7d0c78f35522739e0b1550efd3ed5eb13fc431a1`.

## Scope

- **Claim (2026-08-18):** Project-managed pilot via `TODO-zed-0040-08-20260818T174425Z-831efc7727f6.md`; owner_token `agent:zed:0040-08:20260818T174425Z-831efc7727f6`; branch `0040-08`; isolated worktree `.worktrees/0040-08`.
  - **Requirements covered:** pilot evidence toward `RQ-PROC-01`; supports the two-pilot requirement of `0039-01`.
  - **Origin — architect decision, not customer decision:** open question `OQ-5` was not answered in the review. The architect adds this Task because `0039-01` requires two pilot applications anyway and this incident is a fully evidenced candidate (`T1`–`T8`). It may be dropped without consequence for the rest of the Feature; nothing depends on it except `0040-09`'s completeness check.
  - **Implementation completion (2026-08-18):** The chronological pilot identifies the declared tracked-script plus `_src/validate.py` blocking design as the exact pre-mutation trigger, specifies the required record and distinct Architect review without inventing historical decisions, preserves bounded `[p]` preparation and conditional `[u]`, and explains why the green 99-file result could not establish scope correctness. T1–T8 are dispositioned; six residual escape paths are carried to `0040-09`, `0039-01`, `0037-10.03`/`.04`, existing measurements, or explicit ownership follow-up. Disposition: `effective-for-declared-0038-03-scope-with-recorded-residuals`. `0038-03` remains closed and unchanged. Independent peer review, links, automation safety, and `git diff --check` passed. This node is not a checkpoint; no `Acceptance: ✓` is created.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** a retrospective assessment that changes no foreign item and holds no authority; its findings are inputs to nodes that are themselves reviewed.

### Campaign D — Integration

## Acceptance criteria

- **AC-001** The incident is walked through the amended process and the assessment states, with evidence, at which step the defect would have surfaced, which record would have been produced, and which role would have made the call. Where the amended process would *still* not have caught it, that is recorded as a finding rather than argued away. The assessment explicitly does **not** re-open `0038-03` and does not alter its marker or acceptance state

## Definition of Done

Committed with real `REF`; the disposition is unambiguous; any finding is either fixed in the process Tasks of this Feature or carried as explicit downstream work.
