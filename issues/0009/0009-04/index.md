---
schema_version: "1.0"
id: "0009-04"
level: "task"
parent: "0009"
state: "closed"
visibility: "internal"
prerequisites:
  - "0009-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:290"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0009-04:0009-02 — decide and implement how S-Core content changes are tracked over time (commit hash, tag, or release branch) as the S-Core equivalent of the AUTOSAR `@rel:<release>#<content-hash8>` version ID from **0006-15**, since S-Core has no discrete "release" concept comparable to AUTOSAR SWS releases. CLARIFIED 2026-08-14: decision made and documented in `docs/pipeline/score-identity-scheme.md`. A raw commit hash was rejected as canonical identity because it breaks under repo relocation/mirroring/import into another repository, which would invalidate the system's amendment/curation/supersession pinning. Decided: release tags first, named release branches second, resolved commit SHA recorded only as non-canonical provenance metadata (`source_commit`). Canonical version ID: `ECLIPSE/S-CORE/<kind>/<id>@rel:<release-label>#<content-hash8>`, matching **0006-15**'s format unchanged. Implementation of the scraper/registry/mapping/validation itself is not yet done (tracked by 0009-02/03/05/06).

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
