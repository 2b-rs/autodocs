---
schema_version: "1.0"
id: "0009-02"
level: "task"
parent: "0009"
state: "open"
visibility: "internal"
prerequisites:
  - "0009-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:288"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0009-02:0009-01 — build a repository crawler/scraper for the Eclipse S-Core codebase(s) that walks the relevant repos and emits one curatable record per identified unit (module, component-interface, design-doc, ...), analogous to `spec_scrape.py` for PDF-derived AUTOSAR records -- DONE 2026-08-14: implemented `_src/tools/score_scrape.py` + unit tests `_src/tools/test_score_scrape.py`, supporting extraction of `module`, `component`, `design-doc`, and `process-doc` records with conformant canonical IDs (`ECLIPSE/S-CORE/<kind>/<id>`), `@rel:<release>#<content-hash8>` version IDs, and full non-canonical provenance metadata. REF: pending commit

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
