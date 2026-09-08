---
schema_version: "1.0"
id: "0041-03"
level: "task"
parent: "0041"
state: "closed"
visibility: "internal"
prerequisites:
  - "0041-02"
  - "1788"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1379"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0041-03:0041-02 Prepare the Acceptance-owned commit-reference transition against the reviewed atomic-check-in contract. Claim: `TODO-ash-0041-03-1788233354424.md`; owner_token: `agent:ash:0041-03:1788233354424-223d3b75`.

## Scope

- **Architecture graph repair (2026-08-30, `DEC-0041-007`):** Reopened for current-main re-derivation. Its candidate remains non-operative until `0041-06` integrates the complete synchronous cutover.
  - **Requirements covered:** `RQ-REF-01` … `RQ-REF-03`.
  - **Context (finding K):** The `TODO.md` header currently defines `[x]` as requiring a "real substantive `REF`", and `AGENTS.md` and `task-acceptance.md` repeat it. Changing one and not the others reproduces `T8` — documentation and binding instruction disagreeing, with the instruction winning.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** this is bounded non-operative preparation against a checkpoint-reviewed contract; `0041-06` owns the mandatory activation review and rejects byte or semantic drift.
  - **Task contract (`feature-breakdown@v1`):**
    ```yaml
    task_id: "0041-03"
    feature_id: "0041"
    role: implementer
    architecture_decisions:
      - decision: "Prepare Acceptance-owned REF governance candidate without separate activation"
        derives_from:
          requirements: ["RQ-REF-01", "RQ-REF-02", "RQ-REF-03", "REQ-0041-02-RD-03", "REQ-0041-02-RD-06"]
          decision_records: ["DEC-0041-006", "DEC-0041-007"]
          existing_architecture: ["atomic-checkin-contract@v1 from 0041-02"]
          repository_evidence: ["docs/dossiers/0041-fundstellen.md", "docs/dossiers/0041-02-current-main-rederivation.md@861d87b721c9b3dbb57612e1d84234c8575c2c3e"]
        authority_or_assumption: authority
    prerequisites:
      - task_id: "0041-02"
        derives_from: "reviewed atomic-checkin-contract@v1 grammar and activation manifest"
    planned_order:
      position: 2
      order: ["0041-02", "0041-03", "0041-06", "0041-05"]
      order_matters_because: "candidate wording must consume the stable grammar and remain non-operative until activation"
    write_scope: ["AGENTS.md", "SANDBOX.md", "PRIVILEGED.md", "TODO.md", "docs/pipeline/core-rules.md", "docs/pipeline/branch-workflow.md", "docs/pipeline/task-acceptance.md", "docs/dossiers/0041-03-acceptance-ref-transition.md", "docs/pipeline/fixtures/0041-03/**", "TODO-<owner>-0041-03-<request>.md"]
    test_scope:
      derives_from: ["authority parity", "Acceptance separation", "historical compatibility"]
      kind: integration
      evidence: "old/new phrase matrix, parser fixtures, process/legacy doctors, exact diff and digest handoff"
    capability_profile:
      capability_class: privileged
      rights: ["read repository/history", "author declared governance candidate paths in item worktree", "commit candidate only"]
      data: ["0041-02 contract/manifest", "current authority bytes", "historical terminal fixtures"]
      tools: ["Git", "stdlib Python", "repository validators"]
      execution_needs: direct
      cognitive_demand: high
      independence: "implementer distinct from Architect and activation Integrator; may not integrate or accept"
    cognitive_estimate: {estimator: "cognitive-demand-estimator@v1", scope_breadth: high, reasoning_depth: high, context_volume: high, ambiguity: medium, verification_hardness: high}
    advisory_estimate: {tokens: "35k-65k", tests: "15-30 min", runtime_cpu: "low", planned_duration: "180-300 min", uncertainty: "25-40%", risk: high}
    branch: {parent: "0041", name: "0041-03", create: "pre-provision from current Feature/main governance baseline and merge reviewed 0041-02 product; no stale lineage"}
    ```

## Acceptance criteria

- **AC-001** Prepare candidate bytes and fixtures that remove implementation-header `REF` and the separate implementation-bookkeeping step from `TODO.md` header, `AGENTS.md`, `core-rules.md`, `branch-workflow.md`, and `task-acceptance.md`
- **AC-002** retain the separate Acceptance evidence/bookkeeping commit and require it to pin exact carrying and review-decision commits, baseline, prerequisite closure, manifests, and digests. `SANDBOX.md` and `PRIVILEGED.md` must either align in the candidate or have committed byte-specific compatibility evidence. Bind every change to the reviewed `atomic-checkin-contract@v1` version/digest. Do not integrate any candidate path separately

## Definition of Done

One exact governance candidate, wording matrix, old/new negative grep, historical compatibility fixtures, and own claim are committed; no unrelated authority or role rule changes; existing terminal/accepted records remain valid; candidate is handed to `0041-06` and the operative main rule remains unchanged.
