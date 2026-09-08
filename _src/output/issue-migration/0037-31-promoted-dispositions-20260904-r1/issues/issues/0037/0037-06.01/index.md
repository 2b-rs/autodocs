---
schema_version: "1.0"
id: "0037-06.01"
level: "subtask"
parent: "0037-06"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-01"
  - "0037-02"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2065"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0037-06.01:0037-01, 0037-06.01:0037-02 Define immutable legacy-source watermarks and disposable full shadow imports. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-06.01:c91d87f44a3e`). Abgenommene Baseline `1e761bcc388e637cb516934770ce9299713bc233`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). migration-state-v1.schema.json + Fixture-Verzeichnis vorhanden.

## Scope

- **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-06.01-c91d87f44a3e.md`, `owner_token: agent:perplexity:0037-06.01:c91d87f44a3e`, request ID `c91d87f44a3e`, `base_commit: pending-discovery`. Prerequisites `0037-01` and `0037-02` are terminal.
  - **Closure (2026-08-16):** Defined `migration-state@v1`, immutable committed-tree source boundaries, baseline/latest/candidate watermarks, fresh disposable candidate/report roots, promotion gates, sequence diagram, and scenario fixtures for source changes, identity conflicts, malformed/interrupted inputs, and stale candidates. Revalidation passed. REF: 1e761bcc388e637cb516934770ce9299713bc233

## Acceptance criteria

- **AC-001** Import only `TODO.md`, `DONE.md`, and claim blobs read from an exact committed Git tree, never the working tree
- **AC-002** record source commit, importer commit/digest, schema versions, and baseline/latest-source/candidate watermarks. Every run creates fresh `_src/output/issue-migration/<run-id>/issues/` candidate and `<run-id>/reports/` roots, includes the latest committed Feature `0037`, and promotes only a validated immutable Git tree object. Dirty/staged backlog state blocks a final source watermark
- **AC-003** manual shadow edits never win

## Definition of Done

Review-ready migration-state schema and sequence diagrams cover first import, new legacy commits, deleted/reused IDs, moved tasks, changed prerequisites, malformed source, interrupted import, and stale candidate rejection.
