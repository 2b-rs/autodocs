---
schema_version: "1.0"
id: "0014-04"
level: "task"
parent: "0014"
state: "open"
visibility: "internal"
prerequisites:
  - "0014-01"
  - "0015-06"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2889"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0014-04:0014-01, 0014-04:0015-06 Correct validation/reporting gate weaknesses, including real review/curation queue discovery, mandatory client-render coverage or approved exception, shared run identity, complete required subreports, and failure on missing/inconsistent stage evidence; add regression tests. Queue discovery under `_src/spec/*-queue`, curation-item conformance, malformed-JSON continuation, and regression tests were fixed on 2026-08-15; client-render enforcement, run correlation, complete subreports, and missing-stage failure remain open. **Claim reconciliation (2026-08-24):** The stale `[p]` marker had no claim reference, owner token, claim file, branch, or live owner and was returned to `[ ]`; this does not claim or discard the recorded partial implementation.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
