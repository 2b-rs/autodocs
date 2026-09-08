---
schema_version: "1.0"
id: "0037-44"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-10"
  - "0037-17"
  - "0037-19"
  - "0037-25"
  - "0037-42"
  - "0037-51"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2490"
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

PREREQ: 0037-44:0037-10, 0037-44:0037-17, 0037-44:0037-19, 0037-44:0037-25, 0037-44:0037-42, 0037-44:0037-51 Implement and rehearse post-activation emergency freeze, export, restore, event replay, and forward repair. **REF:** `e6a9251b1a6a98c53a8dc22ab2d6fffa288d79aa`.

## Scope

- **DEC-0037-002 execution model:** Recovery is invoked directly by an authorized agent; an optional Runner controls a long job but never supplies authorization.
  - **Implementation completion (frozen closure delta):** The substantive product `e6a9251b1a6a98c53a8dc22ab2d6fffa288d79aa` and canonical integration receipt `e54ebbb41bab6bc66b8f028735cd446628fd9db7` are ancestors of the assignment-bound base. Transaction `0037-43-44-closure-delta-1788512992649-36e30730` records implementation completion only; no Acceptance or checkpoint crossing is inferred.

## Acceptance criteria

- **AC-001** Each run uses Git blobs, fresh `_src/output/issue-migration/<run-id>/issues/` and `<run-id>/reports/` roots, and recorded source/candidate/tool/schema/artifact identities
- **AC-002** includes every newly committed legacy change
- **AC-003** regenerates views/reports
- **AC-004** links each mismatch to a bounded issue or signed disposition
- **AC-005** and is visibly non-authoritative. Manual shadow edits are discarded, not reconciled

## Definition of Done

At least two increasing source-watermark runs plus one schema/tool-change rerun converge to zero unexplained loss/duplication and a passing retained report; prior run/report/finding links remain queryable.
