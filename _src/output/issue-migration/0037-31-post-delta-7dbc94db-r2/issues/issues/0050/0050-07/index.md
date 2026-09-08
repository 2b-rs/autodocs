---
schema_version: "1.0"
id: "0050-07"
level: "task"
parent: "0050"
state: "closed"
visibility: "internal"
prerequisites:
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:227"
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

(P0) Independently verify the complete all-team, mixed-provider race, deadline, recovery, privacy and abuse matrix against exact candidates.

## Scope

Claim: `DONE-seven-0050-07-20260901T2045Z.md`; owner_token:
  `agent:seven:0050-07:20260901T2045Z`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788296181871-26fb5c2a` (Offer `1788296181871-26fb5c2a` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T20:58:00Z`
  - **Task record:** `task_id: "0050-07"; feature_id: "0050"; role: qa`.
  - **Architecture decisions and sources:** every `REQ-0050-*`, reviewed interface and candidate manifests.
  - **Prerequisites:** `0050-06`.
  - **Planned order:** `position: 8`.
  - **Test scope:** `kind: end_to_end`; execute the requirements matrix plus property invariants, negative authorization/privacy cases, seeds/replay inputs and whole-population team coverage.
  - **Capability profile:** `capability_class=privileged; rights=["read exact candidates", "run isolated validation", "write QA evidence", "commit evidence"]; data=["candidate manifests", "fixtures", "logs by reference"]; tools=["Git", "Python", "pytest", "browser harness"]; execution_needs=direct; cognitive_demand=critical; independence="QA is distinct from decisive implementers and cannot integrate or accept residual risk"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=critical; reasoning_depth=high; context_volume=critical; ambiguity=low; verification_hardness=critical`.
  - **Branch/worktree:** `parent: 0050; name: 0050-07; worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0050-07`.
  - **Exhaustive write scope (autodocs):** `docs/campaign-evidence/0050-07/qa-report.md`, `docs/campaign-evidence/0050-07/case-manifest.json`, and exact item claim.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0050 verification matrix and exact cross-repository candidates", checked_at: "2026-09-01T10:38:08Z", recorded_by: "agent:data:team-pause-phaseout-architecture-20260901:1788258791125-23f83bfb" }`.
  - **No-checkpoint justification (architect):** evidence-only QA node; its exact report is a hard prerequisite of terminal `0050-08`.

## Acceptance criteria

- **AC-001** Every team and named failure/race path has observed results
- **AC-002** property boundaries and counts are retained
- **AC-003** critical/major findings remain blocking and are not converted to Management questions

## Definition of Done

Reproducible QA evidence committed against exact candidate digests.
