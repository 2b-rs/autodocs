---
schema_version: "1.0"
id: "0009-01"
level: "task"
parent: "0009"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:287"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

define Eclipse S-Core's concrete `kind`/ID-minting convention — uncoupled 2026-08-13 from **0006-02**, which only defines the `project/kind/id` canonical identity scheme in the abstract; S-Core is a live codebase, not a PDF spec, so there is no upstream `SWS_xxx`-style source ID to inherit. CLARIFIED 2026-08-14: decision made and documented in `docs/pipeline/score-identity-scheme.md`. `kind` values fixed to `module` (Bazel `MODULE.bazel` name, fallback GitHub repo slug), `component` (Bazel package path, fallback GitHub repo `node_id`), `design-doc` and `process-doc` (existing sphinx-needs ID, not re-minted). Format unchanged from 0006-02: `ECLIPSE/S-CORE/<kind>/<id>`. Unblocks 0009-02/03/05/06. Implementation of the scraper/registry/mapping/validation itself is not yet done (tracked by those tasks).

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
