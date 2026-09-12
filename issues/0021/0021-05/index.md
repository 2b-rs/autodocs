---
schema_version: "1.0"
id: "0021-05"
level: "task"
parent: "0021"
state: "closed"
visibility: "internal"
prerequisites:
  - "0021-03"
  - "0021-04"
labels:
  - "archived-not-accepted"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:338"
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
---

## Goal

PREREQ: 0021-05:0021-03, 0021-05:0021-04 Implement the browser-side “Flag for review” flow on generated record pages. REF: 62f638bf

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Generated pages expose an accessible action and dialog/form
- **AC-002** the form binds the rendered record’s canonical/version ID, current hash, status, and source URL without user re-entry
- **AC-003** it validates required inputs locally, produces the specified request package, and uses GitHub submission or JSON export without browser-side record mutation. The UI distinguishes `exported`, `submitted`, and `ingested/queued`
- **AC-004** a JSON download is never presented as submitted or queued, a submitted GitHub issue shows only its transport receipt until ingestion, and queue identity/linkage appears only after trusted ingestion returns or publishes it

## Definition of Done

Desktop/mobile/browser tests verify keyboard accessibility, visible focus, accessible labels/errors, request serialization, cancellation, transport failure, and no-JavaScript fallback behavior; generated HTML remains deterministic.
