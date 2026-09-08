---
schema_version: "1.0"
id: "0033-05"
level: "task"
parent: "0033"
state: "closed"
visibility: "internal"
prerequisites:
  - "0033-01"
  - "0033-03"
  - "0033-04.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:812"
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
  - id: "AC-006"
    status: "active"
  - id: "AC-007"
    status: "active"
---

## Goal

PREREQ: 0033-05:0033-01, 0033-05:0033-03, 0033-05:0033-04.01 Implement strict package/envelope validation and canonical identity utilities without permissive coercion or uncaught type errors.

## Scope

- **Baseline findings:** `RRB-SCHEMA-001`, `RRB-SCHEMA-002`.
  - **Previous implementation flaws:** The hand-written validator accepted empty/bogus URLs and statuses, list-valued client versions, numeric actor/rationale/evidence fields, invalid evidence kinds, client-supplied `trust`/`received_at`, malformed UUIDs and timestamps, and reserved/sensitive fields; non-string IDs crashed; target version/hash were not bound to the canonical target.

## Acceptance criteria

- **AC-001** Validation enforces every documented type, enum, format, length, relationship, required/nullable field, additional-property rule, and server-owned-field prohibition
- **AC-002** uses robust parsers for canonical IDs, UUIDv7, UTC timestamps, semver, and URLs
- **AC-003** validates evidence-reference kind/value/note structure
- **AC-004** rejects credentials, tokens, IP/session/fingerprint fields and client-authored authoritative trust
- **AC-005** rejects disallowed URL schemes, embedded credentials, private/local targets where policy forbids them, control characters, unsafe HTML/script and Markdown-fence injection, and output-breaking text
- **AC-006** verifies version canonical prefix and embedded hash
- **AC-007** produces stable field-addressed diagnostics for every invalid input and never raises on untrusted JSON types. Canonicalization and idempotency helpers match all pinned vectors and preserve defined array ordering

## Definition of Done

Table-driven and adversarial tests include every historical malformed package plus boundary, nested-type, unknown-field, Unicode, size-limit, canonical-order, and round-trip cases; the former adversarial package produces multiple actionable errors and an integer request ID returns diagnostics rather than `TypeError`.
