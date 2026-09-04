---
schema_version: "1.0"
id: "0041-04"
level: "task"
parent: "0041"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-51"
  - "0041-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1424"
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

PREREQ: 0041-04:0041-01, 0041-04:0037-51 Implement direct item-scoped branch publication with protected-ref and compare-and-swap guards. REF: `610b0dae880aa80e0217fad810326e0a38681d9e`.

## Scope

- **Architecture graph repair (2026-08-30, `DEC-0041-007`):** Reopened and detached from `0041-02`; publication does not consume completion semantics. Accepted `0037-51` is the binding direct-execution predecessor. Historical host-runner candidates are prohibited inputs.
  - **Requirements covered:** `RQ-WT-03`, `RQ-WT-06`; resolves the open point of section 5 of the requirements baseline.
  - **Context:** Publication remains an item-bound Git operation, but `0037-51` removed host-runner transport as a mandatory layer. A direct agent needs one deterministic interface that binds assigned item, source branch, expected remote target, and expected old target object before mutation.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** the interface is fail-closed, item-scoped, non-force, CAS-bound, and hermetically testable; it grants no review or Acceptance authority and is exercised again by terminal `0041-05`.
  - **Task contract (`feature-breakdown@v1`):**
    ```yaml
    task_id: "0041-04"
    feature_id: "0041"
    role: implementer
    architecture_decisions:
      - decision: "Use direct item-scoped publication; do not restore host-runner transport"
        derives_from:
          requirements: ["RQ-WT-03", "RQ-WT-06"]
          decision_records: ["DEC-0037-002", "DEC-0041-007"]
          existing_architecture: ["docs/pipeline/worker-clone-provisioning.md", "direct execution model from 0037-51"]
          repository_evidence: ["docs/dossiers/0037-51-de-sandboxing-scope-review.md@f3522aaaa80d851f3ba28744b08956a52eb63275"]
        authority_or_assumption: authority
    prerequisites:
      - task_id: "0041-01"
        derives_from: "clone/provisioning branch interface"
      - task_id: "0037-51"
        derives_from: "accepted direct-execution architecture and required 0041 rewrite edge"
    planned_order:
      position: 2
      order: ["0041-01", "0041-04", "0041-05"]
      order_matters_because: "publication is independent of completion activation but must exist before end-to-end integration"
    write_scope: ["_src/tools/publish_item_branch.py", "_src/tests/test_publish_item_branch.py", "docs/pipeline/item-branch-publication.md", "docs/pipeline/tools.md", "TODO-<owner>-0041-04-<request>.md"]
    test_scope:
      derives_from: ["item/branch guard", "protected-ref boundary", "CAS/recovery", "canonical-tree non-mutation"]
      kind: integration
      evidence: "disposable-local-repository suite plus automation_safety and before/after canonical status digest"
    capability_profile:
      capability_class: unprivileged
      rights: ["read repository/history", "write declared paths", "direct Git against disposable local remotes"]
      data: ["assigned item/branch", "explicit remote/expected old object", "no credentials"]
      tools: ["Git", "stdlib Python", "repository validators"]
      execution_needs: direct
      cognitive_demand: high
      independence: "implementer has no protected-ref, checkpoint, Acceptance, credential, or release authority"
    cognitive_estimate: {estimator: "cognitive-demand-estimator@v1", scope_breadth: medium, reasoning_depth: high, context_volume: medium, ambiguity: medium, verification_hardness: high}
    advisory_estimate: {tokens: "25k-45k", tests: "20-40 min", runtime_cpu: "medium", planned_duration: "180-300 min", uncertainty: "20-35%", risk: high}
    branch: {parent: "0041", name: "0041-04", create: "pre-provision from current Feature branch with accepted 0037-51 reachable; no historical host-runner candidate"}
    ```

## Acceptance criteria

- **AC-001** `_src/tools/publish_item_branch.py` accepts explicit repository, assigned item ID, source branch, target branch, remote, and expected old object
- **AC-002** verifies the target is the canonical bare item branch for that item
- **AC-003** refuses protected refs, force/non-fast-forward updates, missing/mismatched assignment, dirty/unrelated candidate state, stale expected old object, ambiguous remote, and source/target identity mismatch before push. It performs no credential discovery or authority inference, preserves canonical worktree bytes, emits machine-readable outcome/recovery evidence, and supports a dry-run. Tests use disposable local repositories and cover success, every refusal, CAS race, interruption/retry, and idempotent already-published state

## Definition of Done

Tool, hermetic tests, registered direct-publication documentation, compatibility note for `0041-01`, and own claim are committed; focused suite and automation safety pass; no external remote, credentials, protected ref, Acceptance, integration, or release action occurs during implementation.
