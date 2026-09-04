---
schema_version: "1.0"
id: "0046-06"
level: "task"
parent: "0046"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:994"
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

(P0; terminal integrating Task; Integration review: mandatory) Integrate the exact source-promotion, private activation and public-publication candidates; verify dual receipts, audit/recovery and Feature closure without publishing generated output to source-history `main`.

## Scope

- **Prerequisites:** `0046-04`, `0046-05`.
  - **Planned order:** position `11`, the sole terminal node.
  - **Test scope:** `end_to_end+integration-review`; complete happy path plus stale/duplicate/unauthorized/malformed/replay/conflict/partial-regeneration/partial-publication/restart/health/rollback/privacy/abuse matrix; verify exact ancestry and both repository receipts.
  - **Capability profile:** `capability_class=privileged; rights=["review exact candidates", "run hygiene and independent validation", "integrate only within reserved authority", "record canonical receipts"]; execution_needs=direct; cognitive_demand=critical; independence="reserved Integrator must be independent from decisive architects/implementers and cannot change product scope"`.
  - **Branch/worktree:** `parent: "main"; name: "0046-06"; worktree: "/Users/tobias.anton/devel/autodocs/.worktrees/0046-06"; created by reserved Integrator from current target after exact candidate pinning`.
  - **Exhaustive write scope:** `docs/campaign-evidence/0046-06-integration-report.md`, `docs/campaign-evidence/0046-06-completion-manifest.json`, `TODO.md`, and exact accepted root claim renames required by bookkeeping; no generated public asset is written to source-history `main`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0046-12/13/16/17, dual-receipt contract, and mandatory Feature integration floor", checked_at: "2026-09-01T07:46:00Z", recorded_by: "agent:data:agent-profile-feedback-loop-architecture-20260901:1788246769727-b6ee15d5" }`.
  - **Review rationale:** exactly one terminal checkpoint joins two repositories, private runtime activation, public external deployment, authority/privacy/security boundaries and Feature closure.

## Acceptance criteria

- **AC-001** exact candidates and prerequisites are ancestral
- **AC-002** both receipts bind the same approved source candidate
- **AC-003** Supervisor loaded the exact private revision with health proof
- **AC-004** public projection is reachable from exact remote commit with no forbidden content
- **AC-005** restart/rollback/audit tests pass
- **AC-006** all findings and required decisions are dispositioned

## Definition of Done

integration evidence and completion manifest are committed; source-history `main` contains only source/contracts/evidence; generated output remains on publication infrastructure; canonical receipts prove integration and any authorized Feature closure.
