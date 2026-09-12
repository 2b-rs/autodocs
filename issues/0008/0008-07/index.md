---
schema_version: "1.0"
id: "0008-07"
level: "task"
parent: "0008"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:280"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

investigate stale/incorrect claim in **0004-02**: that entry says 34 SWS_UCM_* records were "backfilled" with `namespace_meta.source='ai-derived-from-service-interface'`, but as of 2026-08-13 the actual record files (e.g. `spec/records/SWS_UCM/SWS_UCM_00348.json`) carry `namespace_meta.source='dienst'` plus a `deviation` key and NO `namespace` key at all -- `validate.py`'s `check_namespaces()` still flags these (and `SWS_CM_10048..10050`, `SWS_SM_91100..91109`, total 34) as having no explicit namespace. Either the claimed backfill was never actually written to these files, or a later change reverted/superseded it without updating the TODO note. Determine ground truth (git log/blame on the record files since 0004-02's commit) and either (a) redo the backfill for real, or (b) if `source='dienst'` + `deviation` is now the intentional final design (service-interface-scoped methods deliberately namespace-less), update `check_namespaces()` to accept that shape instead of flagging it, and correct 0004-02's wording accordingly (found 2026-08-13 via run.sh #67/#68, full `validate.py` run while working on 0008-03) -- RESOLVED 2026-08-13: ground truth confirmed via git log/blame -- 'ai-derived-from-service-interface' never existed in repo history, so 0004-02's claimed backfill was never actually written (option from this task's own text: (a) redo the backfill for real, not (b) accept namespace-less as final design, since 0004-02's underlying AUTOSAR-spec research was correct). Re-applied via new `_src/tools/migriere_dienst_namespace.py`, deriving namespace='ara::<module>' and enclosing='ara::<module>::<ServiceInterface>' from each record's Scope field (module was already correct; only namespace/enclosing/source/review_status were missing). `validate.py`'s `check_namespaces()` now passes with 0 unresolved records; `generate.py --check` confirmed byte-exact reproducibility unaffected. 0004-02's own TODO text corrected to note the prior claim was false. REF: 4fcb351e

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
