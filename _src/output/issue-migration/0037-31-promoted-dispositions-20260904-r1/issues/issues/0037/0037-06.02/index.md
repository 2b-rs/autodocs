---
schema_version: "1.0"
id: "0037-06.02"
level: "subtask"
parent: "0037-06"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-04"
  - "0037-06.01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2071"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-06.02:0037-04, 0037-06.02:0037-06.01 Define schema upgrades and independently authored event reconciliation. REF: 0cd6d346e5f8e6a7c8e18e1d13e02ef909ce2b54 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-06.02:5ea27c94b6d1`). Abgenommene Baseline `0cd6d346e5f8e6a7c8e18e1d13e02ef909ce2b54`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). schema-upgrade-reconciliation.md + Schema + 5/1 Fixtures, JSON gültig.

## Scope

- **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-06.02-5ea27c94b6d1.md`, `owner_token: agent:perplexity:0037-06.02:5ea27c94b6d1`, request ID `5ea27c94b6d1`, `base_commit: pending-discovery`. Prerequisites `0037-04` and `0037-06.01` are terminal.

## Acceptance criteria

- **AC-001** Schema upgrades are pure version-to-version transforms into a fresh root
- **AC-002** their result must semantically equal a clean import targeting the new schema. Post-import provenance remains outside disposable shadow item trees, is replayed once by immutable event ID only when authorized and based on compatible source/item identities, and never overwrites imported text/state. Conflicts, stale bases, deleted targets, representation drift, and duplicate events create stable blocking findings rather than automatic merges

## Definition of Done

Review-ready transform/replay contract and fixtures cover one source change plus one schema upgrade, authorized event preservation, collision/deletion conflicts, and clean-import equivalence.
