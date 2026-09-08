---
schema_version: "1.0"
id: "0001-02"
level: "task"
parent: "0001"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:76"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

decide where build reports live in source control vs generated output (`_src/`, `output/`, published HTML), and document retention/overwrite/archive rules — DECIDED 2026-08-14: build reports live in **published HTML** (not just `output/build-reports/` as a private intermediate). This confirms the direction already implied by **0001-08** (publish the combined build report into the generated HTML tree) as the target state, not an open question. TODO (implementation, tracked by existing tasks): 0001-06 through 0001-11 still need to be built; additionally, retention/overwrite/archive rules for the *published* copies (e.g. keep every run's report indefinitely vs. only latest-per-branch, how old published report pages are superseded/archived when a new build runs) still need to be spelled out in **0001-11**'s documentation update — this decision fixes *where*, not yet the full retention policy.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
