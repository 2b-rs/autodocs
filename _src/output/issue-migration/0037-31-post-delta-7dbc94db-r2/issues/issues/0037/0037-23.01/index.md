---
schema_version: "1.0"
id: "0037-23.01"
level: "subtask"
parent: "0037-23"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-01"
  - "0037-12"
  - "0037-17.03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2391"
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

PREREQ: 0037-23.01:0037-01, 0037-23.01:0037-12, 0037-23.01:0037-17.03 Implement the locale-neutral privacy projector for `_src/data/issue-graph-public.json`. **Claim:** `TODO-benjamin-chain-0037-22-20260828.md` (`owner_token: agent:deepspace9:chain-0037-22:20260828T223500Z`).

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Include only items explicitly marked `public-summary` and only approved ID/level/title-key/title-source-hash/coarse-state/public-summary/public prerequisites/link fields, with no translated title
- **AC-002** exclude claims, identities, private paths, detailed findings/decisions/evidence, security/unreleased items, and all incident edges to omitted nodes. Emit an aggregate restricted count without identifiers
- **AC-003** fail closed on unknown fields/classes, dangling public edges, missing privacy decisions, or leaked restricted fixture tokens
- **AC-004** record input/output artifact sets and policy digest

## Definition of Done

Allowlist and adversarial leak tests, schema validation, deterministic output, reverse privacy checks, and mutation tests prove the public artifact cannot reveal omitted IDs or fields.
