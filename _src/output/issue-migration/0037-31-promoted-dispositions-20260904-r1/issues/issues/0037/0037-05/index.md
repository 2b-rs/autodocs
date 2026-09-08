---
schema_version: "1.0"
id: "0037-05"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-01"
  - "0037-02"
  - "0037-04"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2053"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-05:0037-01, 0037-05:0037-02, 0037-05:0037-04 Define the source/derived matrix and executable regeneration DAG in `docs/pipeline/issue-derived-artifacts.md` and `docs/pipeline/issue-derived-artifacts-v1.json`. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-05:ef6b49a27c81`). Abgenommene Baseline `f05ce02a7c69e9b3d1eafb66ac815183dcc3b13e`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). DAG-Schema + 1 valid/5 invalid Fixtures exakt wie im DoD benannt.

## Scope

- **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-05-ef6b49a27c81.md`, `owner_token: agent:perplexity:0037-05:ef6b49a27c81`, request ID `ef6b49a27c81`, `base_commit: pending-discovery`. Prerequisites `0037-01`, `0037-02`, and `0037-04` are terminal.
  - **Closure (2026-08-16):** Defined `issue-regeneration-dag@v1` schema, complete executable manifest, source/derived matrix, and valid plus five invalid cycle/writer/staleness/report/missing-stage fixtures. Revalidation passed for schema JSON, dependencies, sole writers, derived-input producers, argv arrays, required stages, report isolation, and no-SQLite v1. REF: f05ce02a7c69e9b3d1eafb66ac815183dcc3b13e

## Acceptance criteria

- **AC-001** The JSON format `issue-regeneration-dag@v1` gives each stage a stable ID, argv array (not a shell string), dependencies, typed input globs, exact outputs, sole writer, required/conditional status, committed/ephemeral retention, privacy class, byte/semantic determinism rule, immutable-tree promotion group, cleanup, and validator. Classify canonical issue/provenance/evidence and agent-instruction inputs (`SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, `agent-workflow.json`) versus `TODO.md`, `DONE.md`, internal catalogs, public projection, graph JSON/DOT/SVG, page models, i18n registers, HTML trees, and reports. Volatile UUIDv7 execution-run IDs exist only in external run manifests
- **AC-002** deterministic artifacts embed a content-derived generation ID computed from declared input/schema/tool/config digests. No SQLite stage exists in v1. Detect cycles, undeclared writers/outputs, self-consuming reports, stale inputs, and missing required stages

## Definition of Done

Review-ready JSON Schema for the DAG, complete manifest, human matrix, and cycle/writer/staleness fixtures agree; every derived path has exactly one stage and validation rule.
