---
schema_version: "1.0"
id: "0037-38"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-24"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2411"
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

PREREQ: 0037-38:0037-24 Populate and independently review every required public issue-title and graph-UI translation.

## Scope

- **Rescoping pending (`0037-49`, `DEC-0044-014`):** This Task's role/signer requirements below still name distributed roles. When this Task is next worked, rescope them to the single repository-owner authority per `0037-49`'s single-authority model before implementing against them.

## Acceptance criteria

- **AC-001** Freeze the public item/title/UI source hashes and language set from `_src/site.json`
- **AC-002** generate bounded translation work packages
- **AC-003** produce canonical-language plus every target `issues.json` and UI entry through the existing split/merge path
- **AC-004** retain translator identity/method and reviewer decision
- **AC-005** prohibit untranslated fallback, changed protected tokens, stale hashes, machine-output self-approval, and unrelated register changes. Apply `issues/_policy/translation-review-profile.json`: a registered `translation-reviewer` who authored none of the reviewed records semantically reviews 100% of graph UI strings and 100% of public titles in every configured language, records pass/finding/disposition per string, and permits zero unresolved semantic, terminology, safety, protected-token, or RTL findings

## Definition of Done

Signed review records and the all-language completeness report account for every expected `(source-id, language, source-hash)` tuple; all findings are closed by corrected translation or authorized rejection, all source hashes remain frozen, and no required string is missing, stale, fallback, or unreviewed.
