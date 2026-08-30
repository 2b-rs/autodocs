# Architect coordination — `0041-02` atomic cutover task-graph repair

record_kind: architecture-coordination
task_id: 0041-02
feature_id: 0041
request_id: 20260830
assignment_id: 1788070303437-da755a3f
owner_token: agent:data:0041-02:20260830
base_commit: 4022945cb123d4d619da5dd60527ab3e7bd61428
capability_class: privileged
execution_authority: direct
startup_review: AGENTS.md; SANDBOX.md; TODO.md; docs/pipeline/roles/architect.md; docs/pipeline/core-rules.md; docs/pipeline/feature-breakdown.md; docs/pipeline/decision-record.md; DEC-0041-006; Saru review 8ba8521b02c3e9c4674347a5731676365f331131; Beverly rederivation 861d87b721c9b3dbb57612e1d84234c8575c2c3e; accepted 0037-51 direct-execution disposition reviewed before substantive mutation
state: [p]
recorded_task_state: [x]
coordination_state: in_progress
lease_active: true
branch: 0041-02-atomic-cutover-graph-repair-data-20260830
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0041-02-atomic-cutover-graph-repair-data-20260830
write_scope: ["TODO.md", "TODO-data-0041-02-atomic-cutover-graph-repair-20260830.md", "docs/dossiers/dec-0041-006-atomic-implementation-checkin.md", "docs/dossiers/dec-0041-007-atomic-cutover-task-graph.md", "docs/dossiers/0041-02-atomic-cutover-graph-repair-scope-review.md"]

## Assignment and authority

Atomic award `1788070303437-da755a3f` assigns Data, a privileged
Management-instantiated Architect distinct from every future Implementer and
Integrator, to record the smallest intent-preserving Feature `0041` task-graph
repair and independent cross-item gate-scope review. Management decision
`decision-1788047962210-6bdc03d2`, resolved option A, is the authority source;
mail coordinates the work but does not create that authority.

The assignment affects only `0041-02`, `0041-03`, `0041-04`, and `0041-06`.
It permits architecture and backlog repair only. It prohibits implementation
or activation of governance/tools, Acceptance, integration or checkpoint
review, upward/main merge, Feature/DONE closure, successor start, unrelated
claim or Feature mutation, external resources/effects, and foreign cleanup.

## Intended write scope

- `TODO.md`
- `TODO-data-0041-02-atomic-cutover-graph-repair-20260830.md`
- `docs/dossiers/dec-0041-006-atomic-implementation-checkin.md`
- `docs/dossiers/dec-0041-007-atomic-cutover-task-graph.md`
- `docs/dossiers/0041-02-atomic-cutover-graph-repair-scope-review.md`

## Startup review

- Exact branch/worktree and clean base verified at
  `4022945cb123d4d619da5dd60527ab3e7bd61428`.
- Existing `TODO.md` records `0041-02`, `0041-03`, `0041-04`, and `0041-06`
  as historical `[x]` Tasks while `DEC-0041-006` requires current-main manual
  re-derivation and a single atomic reviewed cutover.
- The existing `0041-02` hold forbids integrating historical candidate
  `8b1afb933f` and permits no early activation.
- Required architecture sources to read completely before substantive mutation:
  `docs/pipeline/feature-breakdown.md`, `docs/pipeline/decision-record.md`,
  applicable gate rules, `DEC-0041-006`, Saru's current scope review, and
  Beverly's current-main rederivation.
- External-resource needs: none. Network and external effects are prohibited.
- Assumption: claim-first bookkeeping is non-operative architecture setup and
  does not itself alter any cross-item gate behavior.

```yaml
target_policy_check:
  field: A1-target-policy-integrability
  verdict: fits
  checked_target: main
  basis: "Exact current-main base; Management option A; architecture-only repair before any gate mutation"
  checked_at: "2026-08-30T08:12:17+02:00"
  recorded_by: "Architect agent:data:0041-02:20260830"
```

## Intended work and validation

Derive the smallest prerequisite/package correction that makes the synchronous
`DEC-0041-006` cutover executable without weakening consumer agreement,
rollback, validation, independence, or the Feature's mandatory checkpoint.
Record a conforming append-only decision update or verified-free `DEC-0041-007`,
plus a distinct Architect scope-review artifact. Amend only the affected
Feature `0041` graph and criteria when the derivation justifies it.

Before handoff, validate decision shape and identifier uniqueness, prerequisite
endpoints/direction/cycles, markers and checkpoint placement, repository
doctors, exact scope, and `git diff --check`. Return a committed architecture
candidate only; Data does not implement, accept, integrate, or activate it.

## Progress

- Claim-first record created before substantive architecture analysis.
- Inbox MCP was unavailable when the award arrived; the award body was read
  from Data's authorized read-only mailbox projection. Announce and ack remain
  pending until the connector returns.

## Next step

Validate and reconcile the exact architecture candidate, finalize this claim,
commit the four-path substantive delta, and return the immutable REF to Lore.
