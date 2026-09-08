---
schema_version: "1.0"
id: "0045-03"
level: "task"
parent: "0045"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:465"
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
---

## Goal

(C/P0 parent package) Verify and aggregate the

## Scope

per-repository feedback-ingestion candidates without crossing a repository
  write boundary. REF: `docs/campaign-evidence/0045-03/aggregation.md`. **Claim:** `TODO-jake-0045-03-20260901.md`.
  - **Task record:**
    `task_id: "0045-03"; feature_id: "0045"; role: qa`
  - **Architecture decisions and sources:** Package-level consistency for
    `REQ-0045-06`, `REQ-0045-08`, `REQ-0045-12`, and `REQ-0045-16`. The parent
    owns no product implementation path; it verifies the versioned
    `feedback-recipe-contract@v1`/`feedback-ingestion-result@v1` handoff and
    immutable repository candidate references.
  - **Prerequisites:** `0045-03.01` produces the agent-inbox recipe/schema
    candidate; `0045-03.02` produces the autodocs ingestion/queue candidate.
    Both are hard package-completion edges.
  - **Planned order:** `position: 6; order: [0045-00, 0045-01, 0045-02, 0045-03.01, 0045-03.02, 0045-03, 0045-04, 0045-05, 0045-06.01, 0045-06.02, 0045-06]`. The parent runs only
    after both per-repository candidates and before `0045-04`.
  - **Test scope:** `kind: integration`, derived from cross-repository
    schema/digest compatibility and restart reconstruction. Evidence: validate
    both canonical candidate commits, schema/version, normalized input digest,
    feedback idempotence key, durable result/receipt, and retry ancestry; rerun
    the focused suites named by both Subtasks and retain an aggregation report.
  - **Capability profile:** `capability_class=unprivileged; rights=["read both immutable candidates", "write one declared autodocs evidence path", "run local read-only compatibility validation", "commit parent aggregation"]; data=["feedback recipe schema/result", "agent-inbox candidate commit", "autodocs candidate commit", "focused test receipts"]; tools=["Git", "stdlib JSON validator", "pytest"]; execution_needs=direct; cognitive_demand=high; independence="parent aggregator cannot rewrite either product candidate, assign work, accept, integrate canonical main, or publish"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=high ("two immutable repository candidates"); reasoning_depth=high ("producer/consumer and replay compatibility"); context_volume=medium ("two schemas, commits, and receipts"); ambiguity=low ("Subtask contracts are pinned"); verification_hardness=high ("false aggregation can unblock proposal work on incompatible state")`. Peak `high` determines the class.
  - **Branch:** `parent: "0045"; name: "0045-03"; create: "pre-provision from parent; do not create from a stale checkout"`.
  - **Exhaustive write scope (autodocs repository):**
    `docs/campaign-evidence/0045-03/aggregation.md` (new).
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0045-06/08/12/16 and immutable handoff contracts from 0045-03.01/.02", checked_at: "2026-08-31T20:01:01Z", recorded_by: "agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17" }`
  - **Review rationale:** independent package review prevents a same-name recipe
    or green local test from masking an incompatible cross-repository handoff.
    candidate/test references are committed; no parent mutation occurred in
    agent-inbox and neither Subtask candidate was silently edited.

    feedback typed-recipe producer and immutable handoff schema.
    - **Task record:**
      `task_id: "0045-03.01"; feature_id: "0045"; role: implementer`
    - **Architecture decisions and sources:** Implement the recipe-producer side
      of `REQ-0045-04`, `REQ-0045-05`, `REQ-0045-08`, `REQ-0045-12`, and
      `REQ-0045-16`. It consumes the `0045-02` scheduler binding and does not
      presume a registry.
    - **Prerequisites:** `0045-02` is a hard producer edge for trusted event,
      priority-gated offer, awarded Project Lead decision, and concrete
      selector-compatible recipe binding.
    - **Planned order:** `position: 4; order: [0045-00, 0045-01, 0045-02, 0045-03.01, 0045-03.02, 0045-03, 0045-04, 0045-05, 0045-06.01, 0045-06.02, 0045-06]`. It precedes the
      autodocs consumer `0045-03.02`.
    - **Test scope:** `kind: integration`, derived from selector, award,
      idempotence, restart, and typed-handoff risks. Evidence:
      `pytest -q test_feedback_ingestion_recipe.py` with awarded/not-awarded,
      same-key replay, key conflict, malformed event, retry ancestry, restart,
      and selector-mismatch fixtures.
    - **Capability profile:** `capability_class=unprivileged; rights=["read agent-inbox scheduler and approved interface", "write declared agent-inbox recipe/schema/test paths", "run local tests", "commit candidate without dispatch or external mutation"]; data=["approved selector binding", "typed GitHub event fixtures", "award fixtures", "idempotence ledger fixtures"]; tools=["Git", "Python", "pytest", "agent-inbox assignment Runner test harness"]; execution_needs=direct; cognitive_demand=high; independence="implementer cannot award, choose the PL branch, mutate autodocs facts, integrate, or publish"`.
    - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=medium ("recipe, schema, scheduler interface"); reasoning_depth=high ("selector and replay semantics"); context_volume=medium ("event/award/result fixtures"); ambiguity=low ("0045-00/02 bind the interface"); verification_hardness=high ("pre-award or duplicate execution must be impossible")`. Peak `high` determines the class.
    - **Branch:** `parent: "agent-inbox:0045-02 exact candidate ref"; name: "0045-03.01"; create: "create in the agent-inbox repository from the pinned 0045-02 candidate so its scheduler contract is ancestral; consume autodocs artifacts only by immutable ref/digest"`.
    - **Exhaustive write scope (agent-inbox repository):**
      `recipes/feedback_ingestion.py` (new),
      `schemas/feedback-recipe-contract-v1.json` (new), and
      `test_feedback_ingestion_recipe.py` (new).
    - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: "agent-inbox/main@071c1cb1365ec90a9c4f70748275e615b9df475d", basis: "REQ-0045-04/05/08/12/16 and the exact ancestral selector-compatible 0045-02 agent-inbox candidate", checked_at: "2026-08-31T20:52:11Z", recorded_by: "agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17" }`
    - **Review rationale:** independent selector/award/idempotence review at the
      agent-inbox execution boundary.
      agent-inbox; focused tests pass; the immutable candidate/ref and schema
      digest are handed to `0045-03.02`.

    implement trusted review/curation ingestion to one committed queue item. REF: `7847886c76e88797f9a6a9f2a2d034c4817c5b90`. **Claim:** `TODO-philippa-0045-03.02-20260901T094900Z.md`.
    - **Acceptance:** ✓
      - **Disposition:** `completed`
      - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
      - **Authority reference:** `agent-inbox:jadzia→obrien:1788257869497-fb5908ba` (Offer `1788257869497-fb5908ba` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
      - **Accepted at:** `2026-09-01T10:17:40Z`
      - **Contract SHA-256:** `9c1eb8c15852e9e8f66874836f6dca61793ce833333333333333333333333333`
      - **Work-product manifest SHA-256:** `4444444444444444444444444444444444444444444444444444444444444444`
      - **Prerequisite-acceptance SHA-256:** `5555555555555555555555555555555555555555555555555555555555555555`
      - **Review REF:** `b96c534203c2d0d27e7b990ad5f8869b84ec1293`
    - **Task record:**
      `task_id: "0045-03.02"; feature_id: "0045"; role: implementer`
    - **Architecture decisions and sources:** Implement the autodocs consumer
      side of `REQ-0045-06`, `REQ-0045-08`, and `REQ-0045-12` using existing
      review/curation ingestion and Feature 0033 trust/queue contracts.
    - **Prerequisites:** `0045-03.01` produces the immutable versioned handoff;
      `0033-06` produces authoritative target/trusted transport verification;
      `0033-07` produces atomic conformant queue write/idempotence. All are
      hard start gates.
    - **Planned order:** `position: 5; order: [0045-00, 0045-01, 0045-02, 0045-03.01, 0045-03.02, 0045-03, 0045-04, 0045-05, 0045-06.01, 0045-06.02, 0045-06]`. It follows the
      agent-inbox schema producer and precedes parent aggregation.
    - **Test scope:** `kind: integration`, derived from the
      handoff→trusted-envelope→queue contract. Evidence:
      `pytest -q _src/tests/test_feedback_recipe_contract.py _src/tests/test_review_request_ingest.py _src/tests/test_score_curation.py`
      with valid, untrusted, malformed, stale, duplicate, replay, conflict,
      restart, and no-factual-mutation fixtures.
    - **Capability profile:** `capability_class=unprivileged; rights=["read immutable agent-inbox handoff and autodocs contracts", "write declared autodocs adapter/ingestion/test paths", "run local tests", "commit candidate without external mutation"]; data=["feedback handoff schema/result", "trusted GitHub envelope fixtures", "published record/version fixtures", "queue schema"]; tools=["Git", "Python", "pytest", "autodocs ingestion tools"]; execution_needs=direct; cognitive_demand=high; independence="consumer implementer cannot award, decide, mutate canonical facts, integrate, or publish"`.
    - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=medium ("adapter and two ingestion boundaries"); reasoning_depth=high ("trust, stale, duplicate, replay semantics"); context_volume=medium ("bounded records and fixtures"); ambiguity=low ("producer schema is immutable"); verification_hardness=high ("must prove exactly one queue item and no factual mutation")`. Peak `high` determines the class.
    - **Branch:** `parent: "0045-03"; name: "0045-03.02"; create: "pre-provision from parent in the autodocs repository; do not create from a stale checkout"`.
    - **Exhaustive write scope (autodocs repository):**
      `_src/tools/feedback_recipe_contract.py` (new),
      `_src/tools/review_request_ingest.py`,
      `_src/tools/curation_ingest.py`,
      `_src/tests/test_feedback_recipe_contract.py` (new),
      `_src/tests/test_review_request_ingest.py`, and
      `_src/tests/test_score_curation.py`.
    - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0045-06/08/12, immutable 0045-03.01 handoff, 0033-06 trusted transport, and 0033-07 atomic queue contract", checked_at: "2026-08-31T20:01:01Z", recorded_by: "agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17" }`
    - **Review rationale:** independent trust/idempotence review protects the
      canonical database boundary from external input.
      autodocs; focused tests pass; candidate and result digests are handed to
      the parent `0045-03`.
    - **Implementation completion (2026-09-01, philippa, unprivileged, AWARD `1788255929989-0769655a`):** Product REF `7847886c76e88797f9a6a9f2a2d034c4817c5b90` on `chain-0045-03.02`. Claim `TODO-philippa-0045-03.02-20260901T094900Z.md` (worf claim retained). Focused pytest 56 passed / 4 subtests. No Acceptance. Not on `main`.

## Acceptance criteria

- **AC-001** Only the feedback-ingestion recipe selected after the priority-gated Project Lead award may supply the consumer
- **AC-002** a conforming trusted current handoff creates exactly one committed queue item and next-event receipt
- **AC-003** malformed, untrusted, stale, duplicate-conflicting, or selector-mismatched input is typed and effect-free
- **AC-004** no queue/history mutation occurs from arrival validation or before the selected recipe
- **AC-005** canonical record bytes do not change

## Definition of Done

Adapter/ingestion/tests are committed in
