---
schema_version: "1.0"
id: "0037-04"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-04.01"
  - "0037-04.02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2037"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-04:0037-04.01, 0037-04:0037-04.02 Complete the review-ready typed-reference, provenance-event, run, finding, and artifact-set contract. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-04:8c2e91f4b7ad`). Abgenommene Baseline `b69634793352f9ea2ad941fa2ea6ac2b53fb407b`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). Causal-Chain-Fixture gültiges JSON mit erwarteten Schlüsseln.

## Scope

- **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-04-8c2e91f4b7ad.md`, `owner_token: agent:perplexity:0037-04:8c2e91f4b7ad`, request ID `8c2e91f4b7ad`, `base_commit: pending-discovery`. Both prerequisite Subtasks are terminal.
  - **Closure (2026-08-16):** Aggregates typed-reference/provenance-event/run/finding contract `9aae0b7a295800478bc8eb0d0df795283b28c2a5` and artifact identity/storage contract `b6ebe46faf81cc3cf95def6c7d7e52304fd6a072`. Runner request `8c2e91f4b7ad-close01` verified valid JSON, all 14 required relations, all 12 endpoint kinds, and the linked event/finding/run/artifact causal chain in `provenance/fixtures/valid/provenance-chain.json`; both source contracts remain review-ready pending architecture approval `0037-07`. REF: b69634793352f9ea2ad941fa2ea6ac2b53fb407b

## Acceptance criteria

- **AC-001** The two Subtasks define one non-duplicated causal model that existing campaign/build/AI/version/evidence formats can adapt to without fabricating history

## Definition of Done

Both Subtasks and a complete bidirectional causal-chain fixture are included in the architecture review package.
