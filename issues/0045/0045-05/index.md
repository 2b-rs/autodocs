---
schema_version: "1.0"
id: "0045-05"
level: "task"
parent: "0045"
state: "open"
visibility: "internal"
prerequisites:
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:627"
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
  - id: "AC-006"
    status: "active"
  - id: "AC-007"
    status: "active"
---

## Goal

(E/P1) Implement the bounded S-Core Curator-decision UI and

## Scope

durable GitHub decision contract.
  Claim: `DONE-quark-0045-05-20260901.md`; owner_token:
  `agent:quark:0045-05:20260901`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788263673418-be788631` (Offer `1788263673418-be788631` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T13:05:00Z`
  - **Task record:**
    `task_id: "0045-05"; feature_id: "0045"; role: implementer`
  - **Architecture decisions and sources:** Implement `REQ-0045-04`,
    `REQ-0045-07`,
    `REQ-0045-09`, `REQ-0045-10`, `REQ-0045-13`, and `REQ-0045-14`.
    Agent-inbox HUD files are read-only design evidence, not a reusable package
    or write scope. Feature 0035 remains requester/submission-dialog UX.
  - **Prerequisites:** `0045-04` produces the exact proposal/handoff;
    `0033-07.01` produces authenticated role-enforced lifecycle transitions;
    `0033-10` browser packaging/staging; `0033-11` truthful
    receipt/stale/duplicate/failure presentation; `0033-12` accessibility and
    no-JS; `0033-13` the realistic browser/transport matrix including
    `0035-01..03` regressions. All are hard producer edges.
  - **Planned order:** `position: 8; order: [0045-00, 0045-01, 0045-02, 0045-03.01, 0045-03.02, 0045-03, 0045-04, 0045-05, 0045-06.01, 0045-06.02, 0045-06]`.
    The UI follows proposal production and precedes the terminal join.
  - **Test scope:** `kind: end_to_end`, derived from human authority,
    exact-diff/baseline binding, accessibility, no-JS, stale/retry, and durable
    GitHub decision risks. Evidence:
    `pytest -q _src/tests/test_score_curation_views.py _src/tests/test_score_curation.py _src/tests/test_score_curator_decision.py`
    plus the `0033-13` browser/transport matrix and retained manual
    accessibility/keyboard inspection for accept, reject, request-revision,
    stale, conflict, receipt, and recovery.
  - **Capability profile:** `capability_class=unprivileged; rights=["read exact proposal/baseline and predecessor evidence", "write declared autodocs UI/view/ingestion/test paths", "run local tests and browser fixture", "commit candidate without deciding a real proposal"]; data=["proposal and baseline fixtures", "Curator authority fixture", "GitHub decision/receipt fixtures", "0033 browser matrix"]; tools=["Git", "Python", "pytest", "browser test harness", "JavaScript"]; execution_needs=direct; cognitive_demand=critical; independence="implementer/test identity is not Curator authority and cannot accept work, apply facts, integrate, or release"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=high ("views, UI, ingestion, browser contracts"); reasoning_depth=critical ("human authority and stale decision binding"); context_volume=high ("proposal, evidence, chat, receipt, accessibility"); ambiguity=medium ("bounded UI, no generic HUD extraction"); verification_hardness=critical ("a false or stale acceptance could mutate canonical facts")`. Peak `critical` determines the class.
  - **Branch:** `parent: "0045"; name: "0045-05"; create: "pre-provision from parent; do not create from a stale checkout"`.
  - **Exhaustive write scope (autodocs repository):**
    `_src/tools/score_curation_views.py`, `_src/tools/curation_ingest.py`,
    `review.js`, `score_curator.js` (new),
    `_src/tests/test_score_curation_views.py`,
    `_src/tests/test_score_curation.py`, and
    `_src/tests/test_score_curator_decision.py` (new).
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0045-07/09/10/13/14 plus 0033 authenticated browser contracts; 0035 remains requester UX", checked_at: "2026-08-31T20:01:01Z", recorded_by: "agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17" }`
  - **Review rationale:** mandatory independent UX/accessibility/security review
    because the surface captures the sole human product decision.
    accessibility/browser evidence are committed; all stated tests pass; no
    real Curator decision or factual apply is fabricated.

## Acceptance criteria

- **AC-001** The Curator sees exact proposal, pinned published baseline, pretty diff, evidence, chat provenance, and current state
- **AC-002** can durably accept, reject, or request revision
- **AC-003** that durable decision is an arrival envelope, not yet trusted ingestion or apply authority, and its minimum safe-routing validation opens a priority-gated Project Lead offer before the selected downstream decision recipe runs
- **AC-004** the exact decision key `decision:<proposal-id>:<curator-decision-revision>` is replay-safe
- **AC-005** stale/conflicting/unauthorized decisions are effect-free
- **AC-006** no Feature 0035 ownership or generic HUD package is claimed
- **AC-007** no arrival check mutates proposal, queue, history, facts, or publication state

## Definition of Done

Scoped UI/view/ingestion/tests and retained
