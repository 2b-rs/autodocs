---
schema_version: "1.0"
id: "0021-03"
level: "task"
parent: "0021"
state: "closed"
visibility: "internal"
prerequisites:
  - "0021-02"
labels:
  - "archived-not-accepted"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:328"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0021-03:0021-02 Extend the ingestion boundary to recognize, validate, de-duplicate, and route website re-curation submissions. REF: a03be1e6

## Scope

### Campaign B — Website Experience and Generated Views

## Acceptance criteria

- **AC-001** `curation_ingest.py` or a clearly delegated adapter accepts only schema-valid packages, verifies target record/version/hash, derives authoritative identity/trust only from the trusted transport envelope, rejects spoofed trust claims, preserves a lossless mapping of submission identity/context into the queue item, creates an `open` curation-queue item with record linkage, and rejects malformed/stale/duplicate inputs with actionable diagnostics
- **AC-002** no rejected input creates history and no accepted input directly writes factual record fields

## Definition of Done

Automated tests cover happy path, unknown record, obsolete version/hash, malformed schema, duplicate submission, unsupported category, insufficient attribution, spoofed trust metadata, and lossless submission-to-queue mapping; output conforms to `curation-item@v1` (or a deliberately versioned successor) and unified lifecycle validation.
