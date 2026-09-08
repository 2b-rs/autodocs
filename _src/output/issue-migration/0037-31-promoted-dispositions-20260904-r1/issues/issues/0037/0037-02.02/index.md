---
schema_version: "1.0"
id: "0037-02.02"
level: "subtask"
parent: "0037-02"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2012"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-02.02:0037-01 Define the constrained Markdown profile and stable acceptance-criterion lifecycle in `docs/pipeline/issue-store.md`. REF: 55abebbb5a4f251da5dc07c6077082d0c5e03fa3 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-02.02:a4c7f92e6d18`). Abgenommene Baseline `55abebbb5a4f251da5dc07c6077082d0c5e03fa3`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). Anhang an issue-store.md + 12 Markdown-Fixtures vorhanden.

## Scope

- **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-02.02-a4c7f92e6d18.md`, `owner_token: agent:perplexity:0037-02.02:a4c7f92e6d18`, request ID `a4c7f92e6d18`, `base_commit: pending-discovery`. Self-selected per `AGENTS.md` rule 3 as the first eligible item now that `0037-02.01` is `[x]`.

## Acceptance criteria

- **AC-001** Normative sections are `Goal`, `Scope`, `Acceptance criteria`, and `Definition of Done`
- **AC-002** informative findings/history are structurally separate. Criteria use item-local `AC-NNN`: append-only allocation, no reuse/renumbering, retained withdrawal tombstones, same-intent edit retention, new-ID supersession for changed intent/verification, and new-ID plus `derived-from` when moved. Define canonical criterion refs, insertion/deletion/move/text-edit algorithms, source locators, Unicode/multiline/size rules, and migration assignment by legacy document order

## Definition of Done

Review-ready valid/invalid Feature, Task, and Subtask Markdown fixtures include insert, edit, withdraw, supersede, move, and deterministic legacy migration cases; each operation has one expected normalized result.
