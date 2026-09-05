---
schema_version: "1.0"
id: "0037-34.02"
level: "subtask"
parent: "0037-34"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-33"
  - "0037-34.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2527"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-34.02:0037-33, 0037-34.02:0037-34.01 Apply the authorized patch as the atomic authority-switch commit.

## Scope

- **Integration review: mandatory.** **Rationale (architect):** this is the atomic authority-switch boundary.

## Acceptance criteria

- **AC-001** Verify integration HEAD equals the authorized control base, clean index/worktree, candidate/patch/approval digests, policy revision/signature validity, zero active claims, enforced issue-write freeze, and complete file list before applying. One commit applies the exact independently audited final authority tree, makes `issues/` authoritative and all legacy lists/catalogs/graphs/public payloads generated, activates validation/regeneration but keeps claim/item writes disabled by the `issue-store-frozen` selector and command fencing through `0037-40`, retains source/migration/audit/rollback evidence, and leaves no legacy parser/owner path. A follow-up reference commit records the actual cutover hash/UTC time and closes `0037-32`, `0037-33`, `0037-34.02`, and aggregate Task `0037-34` without amending or weakening authorized content
- **AC-002** no dual-authority gap exists

## Definition of Done

Cutover and follow-up reference commits match authorization; immediate post-commit validation reports exactly one authority, one consistent artifact lineage, and zero stale/obsolete paths.
