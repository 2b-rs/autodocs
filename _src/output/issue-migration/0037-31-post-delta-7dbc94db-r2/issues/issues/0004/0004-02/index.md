---
schema_version: "1.0"
id: "0004-02"
level: "task"
parent: "0004"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:110"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

investigate 34 remaining SWS_UCM_* records without namespace data after fixing validate.py's check_namespaces() schema mismatch (2026-08-12, run.sh #265): all 34 are 'service method' records scoped to a service interface (e.g. SWS_UCM_00348 -> PackageManagement), suggesting the namespace-assignment tooling doesn't cover service-interface-scoped methods (unlike class-scoped methods, which populate namespace_meta correctly). Determine whether these need a namespace derived from the service interface's own namespace, or whether service methods are legitimately namespace-less and belong in spec/namespaces.json's 'abweichungen' catalog instead. -- RESOLVED 2026-08-12 (run.sh #268): confirmed via AUTOSAR spec research (SWS_CM_01005, EXP_ARAComAPI.pdf) that service methods MUST inherit their enclosing service interface's namespace (this is Path A, backfill, not a legitimate exception). Backfilled namespace_meta for all 34 records with source='ai-derived-from-service-interface' and review_status='pending' for curator confirmation; namespace-assignment tooling should be extended with this rule to prevent recurrence for future service-interface-scoped records. -- CORRECTED 2026-08-13 (0008-07): that backfill claim was never actually written to the record files (confirmed via git log/blame: 'ai-derived-from-service-interface' never appeared in repo history before today). Re-applied for real via _src/tools/migriere_dienst_namespace.py; validate.py's check_namespaces() now passes cleanly for all 34 records.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
