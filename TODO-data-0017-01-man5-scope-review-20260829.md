# Coordination claim — `0017-01` MAN.5 option-A decision and scope review

item: 0017-01-option-a-decision-scope-review
task_id: 0017-01
feature_id: 0017
owner: data
owner_token: agent:data:0017-01:1787973576019-d6c3b9ea
assignment_id: 1787973576019-d6c3b9ea
status: [x]
coordination_state: review_ready
lease_active: false
capability_class: privileged
execution_authority: direct local execution in this item-owned sparse worktree only
branch: gov-0017-01-option-a-data-20260829
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/gov-0017-01-option-a-data-20260829
base_commit: 8b966a2f85ca517029ed516ed496d4cc3287c15c

## Atomic award and exact scope

- Award: `1787973576019-d6c3b9ea`, due `2026-08-29T04:50:07Z`.
- Process: Architecture and Governance Decision Recording.
- Scope: Feature `0017` MAN.5 strategy activation boundary.
- Implementer candidate: `fe645c415c498a4fd83ccc6b5371c6ba28d2aba1`.
- Management decision: `decision-1787972295293-da9db52e`, option A;
  resolution notice `agent-inbox:1787973446577-7e3616ba`.
- Write paths are exactly:
  - `docs/dossiers/dec-0017-001-man5-risk-strategy.md`
  - `docs/dossiers/0017-01-man5-risk-strategy-scope-review.md`
  - `TODO-data-0017-01-man5-scope-review-20260829.md`

No candidate, `TODO.md`, `DONE.md`, Acceptance, integration, Feature/main ref,
gate activation, release, specialist decision, ECU evidence, external system, or
Memory scope is writable or authorized.

## Startup and authority verification

- Supplied branch/worktree existed clean at exact `main@8b966a2f85` and sparse
  checkout listed exactly the three writable paths.
- `DEC-0017-001` was absent from current `main` before allocation.
- The durable decision archive reports option A resolved at
  `2026-08-29T03:17:26Z` for Management.
- Data is distinct from Implementer Tasha and Project Lead Jean-Luc. This is an
  independent pre-mutation Architect scope review, not Acceptance or integration.

## Planned validation and recovery

- Validate exact `decision-record@v1` field order, cardinalities, IDs, trigger
  vocabulary, work-unit/gate references, participation and waiver.
- Validate the option-A scales, bands, escalation times, centralized interim
  human roles, authority non-transfer, cross-item consumers, evidence-origin
  boundary, safety/cybersecurity interface, activation, drift and recovery.
- Run exact-path status, placeholder scan, link/anchor checks where applicable,
  repository document validator, and `git diff --check`.
- Commit only the three paths. Before integration, recovery is to withhold the
  candidate branch. Corrections after publication are additive.

## Current result

**Verdict:** `scope-ok-with-conditions` for the exact pinned candidate and
Management option A. The decision and review preserve all authority,
safety/cybersecurity, evidence-origin, activation, drift, recovery, and
no-grandfathering boundaries. No gate is activated by this branch.

Validation before commit:

- anchored `decision-record@v1` structural check: PASS; 15 ordered top-level
  fields each occur exactly once, three alternatives are contiguous with one
  selected, eight consequences, eight work units, ten gates, five unique valid
  triggers, one supporting participant, and `Waiver: none`;
- option-A semantic scan: PASS for `1–5`, `1–4`/`5–9`/`10–15`/`16–25`, High
  within one working day, Critical immediate escalation/containment, registered
  Management's five interim roles, sole residual-risk authority for every
  class, and no agent/repository-role delegation;
- cross-item review: PASS with conditions C-01 through C-09 for `0017-02`,
  `0017-03`, `0017-07`, `0027-03`, baseline, verification, release,
  safety/cybersecurity, authority separation, evidence origin and recovery;
- exact changed-path audit: PASS; only the three awarded paths are present;
- reserved drafting-placeholder scan: PASS;
- `git diff --check`: PASS;
- `process_doc_doctor.py --root . --json`: unavailable in the intentional
  three-path sparse checkout, exit `2` because `AGENTS.md` is not materialized;
  no pass is claimed from that tool.

Terminal handoff: commit only these three paths, transition the assignment to
review, and report the exact REF to Jean-Luc. A separately assigned privileged
Integrator owns any later review/integration. Data retains no implementation,
Acceptance, integration, activation, main/Feature-ref, residual-risk, release,
or specialist authority.
