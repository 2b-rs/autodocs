---
schema_version: "1.0"
id: "0050-08"
level: "task"
parent: "0050"
state: "open"
visibility: "internal"
prerequisites:
  - "1788"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:265"
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
---

## Goal

(P0; terminal integrating Task; Integration review: mandatory) Integrate the reviewed agent-inbox lifecycle and autodocs evidence, activate only the exact validated candidate, and prove all-team quiescence, restart recovery and rollback without destructive cleanup.

## Scope

Claim: `DONE-obrien-0050-08-20260901.md`; owner_token:
  `agent:obrien:0050-08:1788297753802-f3b2ad09`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788297753802-f3b2ad09` (Offer `1788297753802-f3b2ad09` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T21:30:00Z`
  - **Task record:** `task_id: "0050-08"; feature_id: "0050"; role: integrator`.
  - **Architecture decisions and sources:** `DEC-0050-001`, every `REQ-0050-*`, `0050-00` review, implementation manifests and `0050-07` QA evidence.
  - **Prerequisites:** `0050-07`, `0050-09`; its closure includes `0050-00..06`.
  - **Planned order:** `position: 10`; sole terminal node.
  - **Test scope:** `kind: end_to_end`; independently rerun admission races, deadline decisions, blackout/preservation, restart, zero proof, resume and rollback against exact integrated candidates.
  - **Capability profile:** `capability_class=privileged; rights=["review exact candidates", "run hygiene/independent validation", "integrate under reserved authority", "record activation/rollback receipts"]; data=["complete prerequisite closure", "QA evidence", "journal fixtures"]; tools=["Git", "Python", "pytest", "browser harness"]; execution_needs=direct; cognitive_demand=critical; independence="Integrator is independent from decisive Architects/implementers/sole QA producer and cannot alter product direction"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=critical; reasoning_depth=critical; context_volume=critical; ambiguity=low; verification_hardness=critical`.
  - **Branch/worktree:** `parent: main; name: 0050-08; worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0050-08`; reserved Integrator creates from current target after pinning candidates.
  - **Exhaustive write scope:** `docs/campaign-evidence/0050-08/integration-report.md`, `docs/campaign-evidence/0050-08/completion-manifest.json`, `TODO.md`, and exact accepted root-claim renames required by bookkeeping; agent-inbox ref activation is separately exact and receipt-bound.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "DEC-0050-001, complete prerequisite closure and mandatory Feature integration floor", checked_at: "2026-09-01T10:38:08Z", recorded_by: "agent:data:team-pause-phaseout-architecture-20260901:1788258791125-23f83bfb" }`.
  - **Review rationale:** exactly one terminal checkpoint integrates a cross-repository, fleet-wide ownership and preservation gate.

## Acceptance criteria

- **AC-001** Exact candidates and reviews are ancestral
- **AC-002** all teams/races/recovery paths pass, including stale status and unknown legacy-record reconciliation
- **AC-003** activation receipt binds agent-inbox revision and schema digests
- **AC-004** rollback is proven
- **AC-005** zero proof uses authoritative sets plus typed legacy reconciliation receipts
- **AC-006** no evidence or useful work is deleted

## Definition of Done

Integration and activation receipts committed, no generated/live state enters source-history `main`, and any Feature closure follows separate current Acceptance authority.
