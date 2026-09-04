---
schema_version: "1.0"
id: "0037-01"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-48"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1996"
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
  - id: "AC-008"
    status: "active"
  - id: "AC-009"
    status: "active"
  - id: "AC-010"
    status: "active"
  - id: "AC-011"
    status: "active"
  - id: "AC-012"
    status: "active"
---

## Goal

PREREQ: 0037-01:0037-48 Record the canonical path, identity, hierarchy, authority, privacy, and source-versus-derived contract in `docs/pipeline/issue-store.md`. REF: 94a697b647c930687d55fcbec837421a7e674e80 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-01:d83a7c4f19e2`). Abgenommene Baseline `94a697b647c930687d55fcbec837421a7e674e80`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). issue-store.md (161 Zeilen) + 5 Fixtures vorhanden, inhaltlich konsistent.

## Scope

- **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-01-d83a7c4f19e2.md`, `owner_token: agent:perplexity:0037-01:d83a7c4f19e2`, request ID `d83a7c4f19e2`, `base_commit: pending-discovery`. Self-selected per `AGENTS.md` rule 3 as the first open Task with terminal prerequisites now that `0037-48` is `[x]`.

## Acceptance criteria

- **AC-001** Pin `issues/XXXX/index.md` and `issues/XXXX/XXXX-YY[.ZZ]/index.md`
- **AC-002** flat item directories and structured `parent`
- **AC-003** immutable ID-derived paths
- **AC-004** item-local `claim.json`, `closure.json`, `decisions/`, and `attachments/`
- **AC-005** schema roots `issues/_schema/` and `provenance/_schema/`
- **AC-006** internal views `issues/_views/`
- **AC-007** public projection `_src/data/issue-graph-public.json`
- **AC-008** public page model `_src/sources/pages/issues.json`
- **AC-009** canonical instruction interfaces `SANDBOX.md`, `AGENTS.md`, and `agent-workflow.json`
- **AC-010** provenance and migration paths from the resolved baseline
- **AC-011** authority/cutover rules
- **AC-012** and the internal-by-default allowlist/redaction policy. Generated or shadow files must never become parser inputs or a second authority

## Definition of Done

The contract is review-ready, every path has one owner/retention/privacy class, positive/negative path and projection fixtures are committed, and an item ID/level can be derived from every canonical path without title/state heuristics.
