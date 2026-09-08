---
schema_version: "1.0"
id: "0037-02.03"
level: "subtask"
parent: "0037-02"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-02.01"
  - "0037-02.02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2017"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-02.03:0037-02.01, 0037-02.03:0037-02.02 Commit executable normalized-object schemas and fixtures for the issue item format. REF: 70bfe4aee2bf4d0a33711c1d42b743a62c4f1ace **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-02.03:e29f6c81b4d7`). Abgenommene Baseline `70bfe4aee2bf4d0a33711c1d42b743a62c4f1ace`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). run_fixtures.py unabhängig ausgeführt: 'OK: 3 valid + 14 invalid fixtures behaved as expected', exakt wie behauptet.

## Scope

- **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-02.03-e29f6c81b4d7.md`, `owner_token: agent:perplexity:0037-02.03:e29f6c81b4d7`, request ID `e29f6c81b4d7`, `base_commit: pending-discovery`. Self-selected per `AGENTS.md` rule 3; both prerequisites now `[x]`.

## Acceptance criteria

- **AC-001** `issues/_schema/issue-item-v1.schema.json` defines required/optional fields, closed unknown-field behavior, enums, timestamps-as-strings, parent/prefix/path rules, prerequisites, labels, work types, origins/relations, publication class, authority requirements, criteria/tombstones/supersession, extension/version negotiation, and limits. Schema validation occurs after strict front-matter parsing
- **AC-002** schema success never substitutes for Markdown/path/graph validation

## Definition of Done

Schema, normalized valid examples, one invalid fixture per rule, and a schema-fixture runner are review-ready and committed; no fixture depends on parser implementation from Campaign B.
