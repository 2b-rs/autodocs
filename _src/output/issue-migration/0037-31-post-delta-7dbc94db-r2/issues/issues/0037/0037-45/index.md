---
schema_version: "1.0"
id: "0037-45"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-01"
  - "0037-03"
  - "0037-06.03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2081"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-45:0037-01, 0037-45:0037-03, 0037-45:0037-06.03 Define the two-agent-class capability model and versioned sandboxed-runner request/result contract. REF: b01d56f134671c89693a9f7a3781b43f761ffd29 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-45`). Abgenommene Baseline `b01d56f134671c89693a9f7a3781b43f761ffd29`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). agent-execution.md + drei Schemas + runner-protocol-v1-Fixtures (8/2) exakt wie im DoD benannt.

## Scope

- **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-45-20260816-1435.md`, `owner_token: agent:perplexity:0037-45:0037-45-20260816-1435`, request ID `0037-45-20260816-1435`, `base_commit: pending-discovery`. Prerequisites `0037-01`, `0037-03`, and `0037-06.03` are terminal.

## Acceptance criteria

- **AC-001** Create `docs/pipeline/agent-execution.md`, `issues/_schema/agent-capability-v1.schema.json`, `issues/_schema/runner-request-v1.schema.json`, and `issues/_schema/runner-result-v1.schema.json`. Define `sandboxed-grunt` versus explicit `privileged`, fail-safe defaulting, allowed non-execution tools, prohibited direct process/Git/network execution, singleton-root bootstrap versus conflict-free versioned request queue, request/claim ownership, action allowlist and typed arguments, expected base commit/authority epoch, read/write/mutation scopes, inputs/outputs/digests, preflight, dependencies, timeout/CPU/memory/workers, network hosts/traffic, credential handles without secret values, idempotence, temporary paths, cleanup, progress, structured logs/results, retry/recovery, and cancellation. Define the legacy claimed pending-discovery exception plus runner-issued post-discovery request reservations/leases and runner transactions for read-only discovery, focused validation, generation, external-service configuration, signing verification, path-limited substantive commit, and optional two-commit substantive/bookkeeping closure. No contract step may require the user or a privileged agent to execute the request

## Definition of Done

Review-ready capability/runner schemas, security/threat model, lifecycle/state table, and valid/invalid fixtures cover slot/queue races, stale base/epoch, overlapping scopes, unknown action, missing dependency/credential, timeout, partial mutation, failed validation, interrupted commit, result tampering, retry, and two-commit REF injection; every remaining Feature `0037` Task can be mapped to non-execution edits plus declared runner actions or is split before approval.
