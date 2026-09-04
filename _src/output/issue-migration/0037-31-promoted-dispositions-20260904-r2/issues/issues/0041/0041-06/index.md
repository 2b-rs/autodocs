---
schema_version: "1.0"
id: "0041-06"
level: "task"
parent: "0041"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-51"
  - "0038-02"
  - "0041-02"
  - "0041-03"
  - "1788"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1471"
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
---

## Goal

PREREQ: 0041-06:0041-02, 0041-06:0041-03, 0041-06:0037-51, 0041-06:0038-02 Assemble, validate, and atomically activate every completion-contract consumer.

## Scope

Claim: `DONE-worf-0041-06-20260901.md`; owner_token:
  `agent:worf:0041-06:1788260931485-5adf1b20`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788263465631-65612af1` (Offer `1788263465631-65612af1` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T11:59:30Z`
  - **Architecture graph repair (2026-08-30, `DEC-0041-007`):** Reopened as the sole synchronous activation owner. It consumes fresh `0041-02`/`0041-03` products, not historical lineages; candidate preparation remains non-operative until its mandatory checkpoint and authorized main-ref advance.
  - **Origin:** `DEC-0041-005`; discovered during `0041-04` integration preflight.
  - **Integration review:** **mandatory.** **Rationale (architect):** this is the repository-wide activation point. A missed consumer can block all later Task completion or silently accept invalid terminal state; rollback and history compatibility span every work unit. The Integrator must pin and review the exact combined tree, not isolated predecessor results.
  - **Task contract (`feature-breakdown@v1`):**
    ```yaml
    task_id: "0041-06"
    feature_id: "0041"
    role: implementer
    architecture_decisions:
      - decision: "Own the sole synchronous atomic-checkin activation tree and checkpoint"
        derives_from:
          requirements: ["RQ-CI-01", "RQ-CI-02", "RQ-CI-03", "RQ-CI-04", "RQ-CI-05", "RQ-REF-01", "RQ-REF-02", "RQ-REF-03", "REQ-0041-02-RD-01", "REQ-0041-02-RD-02", "REQ-0041-02-RD-03", "REQ-0041-02-RD-04", "REQ-0041-02-RD-05", "REQ-0041-02-RD-06"]
          decision_records: ["DEC-0037-002", "DEC-0041-006", "DEC-0041-007"]
          existing_architecture: ["atomic-checkin-contract@v1", "acceptance-ref-transition@v1", "runner transaction/recovery contract from 0038-02"]
          repository_evidence: ["docs/dossiers/0041-02-current-main-rederivation.md@861d87b721c9b3dbb57612e1d84234c8575c2c3e", "docs/dossiers/0041-02-atomic-cutover-graph-repair-scope-review.md"]
        authority_or_assumption: authority
    prerequisites:
      - task_id: "0041-02"
        derives_from: "checkpoint-reviewed contract and activation manifest"
      - task_id: "0041-03"
        derives_from: "governance candidate and Acceptance transition fixtures"
      - task_id: "0037-51"
        derives_from: "accepted direct-execution architecture"
      - task_id: "0038-02"
        derives_from: "journal/CAS/rollback/path-isolation transaction guarantees"
    planned_order:
      position: 3
      order: ["0041-02", "0041-03", "0041-06", "0041-05"]
      order_matters_because: "preparation must remain non-operative until the complete consumer tree can cross one checkpoint and activate together"
    write_scope: ["AGENTS.md", "SANDBOX.md", "PRIVILEGED.md", "TODO.md", "_src/tools/legacy_task_editor.py", "_src/tools/runner_transaction.py", "_src/tools/legacy_task_doctor.py", "_src/tools/check_integration_hygiene.py", "_src/tests/test_legacy_task_editor.py", "_src/tests/test_runner_transaction.py", "_src/tests/test_legacy_task_doctor.py", "_src/tests/test_check_integration_hygiene.py", "docs/pipeline/core-rules.md", "docs/pipeline/branch-workflow.md", "docs/pipeline/task-acceptance.md", "docs/pipeline/runner-transaction.md", "docs/pipeline/agent-execution.md", "docs/pipeline/issue-lifecycle.md", "docs/pipeline/legacy-handoff-manifest.md", "docs/pipeline/legacy-task-doctor.md", "docs/pipeline/tools.md", "docs/dossiers/0041-06-atomic-cutover-activation.md", "docs/pipeline/fixtures/0041-06/**", "TODO-<owner>-0041-06-<request>.md"]
    test_scope:
      derives_from: ["complete consumer manifest", "atomic tree/trailers", "journal/CAS/recovery", "migration/rollback", "integration hygiene", "Acceptance separation"]
      kind: integration
      evidence: "whole manifest-bound hermetic matrix, old-writer discovery, process/legacy doctors, candidate/root hygiene, pre/post activation and rollback rehearsal"
    capability_profile:
      capability_class: privileged
      rights: ["read repository/history", "write declared activation paths in item worktree", "assemble predecessor candidates", "run direct Git/tests"]
      data: ["reviewed predecessor refs/digests", "current-main consumer bytes", "historical fixtures", "no credentials"]
      tools: ["Git", "stdlib Python", "repository validators and hygiene checker"]
      execution_needs: direct
      cognitive_demand: critical
      independence: "implementation owner cannot perform mandatory checkpoint, Acceptance, Feature closure, or main integration; separately assigned privileged Integrator required"
    cognitive_estimate: {estimator: "cognitive-demand-estimator@v1", scope_breadth: critical, reasoning_depth: critical, context_volume: critical, ambiguity: high, verification_hardness: critical}
    advisory_estimate: {tokens: "70k-130k", tests: "45-120 min", runtime_cpu: "high", planned_duration: "480-900 min", uncertainty: "35-55%", risk: critical}
    branch: {parent: "0041", name: "0041-06", create: "pre-provision from current Feature/main governance baseline; merge exact reviewed 0041-02 and fresh 0041-03 products; never reuse historical lineage"}
    ```

## Acceptance criteria

- **AC-001** Bind exact reviewed `0041-02` contract/manifest and `0041-03` candidate digests
- **AC-002** integrate their governance candidate bytes with fresh direct-execution changes to `_src/tools/legacy_task_editor.py`, `_src/tools/runner_transaction.py`, `_src/tools/legacy_task_doctor.py`, any evidenced `_src/tools/check_integration_hygiene.py` dependency, registered tool docs, and all matching guidance. Produce one activation tree where every live writer/parser/gate uses `Task-ID`/`Base-Ref`, terminal tree/claim invariants, and Acceptance-owned commit references
- **AC-003** no reachable path requires or creates implementation-header `REF` or a second implementation-bookkeeping commit. Reject mismatched/duplicate trailers, non-ancestor or stale Base-Ref, marker/claim/partial-tree mismatch, stale/CAS-lost state, old manifests, ambiguous history, and unauthorized Acceptance/checkpoint transitions. Preserve path isolation, journal, rollback, crash recovery, provenance, dirty/unrelated work, historical contracts, and direct-execution boundaries. Activation is exactly one separately reviewed main-ref advance
- **AC-004** candidate commits do not activate

## Definition of Done

Exact activation and rollback manifests, merged candidate tree, consumer/digest inventory, old-writer proof, migration matrix, and complete hermetic evidence are committed. Focused fixtures cover success, every negative above, failed validation, CAS loss, hard-kill/recovery, dirty/unrelated preservation, historical and reopened work, Acceptance separation, hygiene candidate/root pre/post checks, and rollback. Process/legacy doctors and exact-scope/diff checks pass or only disclose pinned unrelated baseline findings. Independent mandatory checkpoint passes before any main advance.
