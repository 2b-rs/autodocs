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
state: [ ]
recorded_task_state: [ ]
coordination_state: complete
restart_recovery_state: terminal
lease_active: false
architect_work_product_status: [x]
substantive_ref: 14ca63e94d8d1a06d8f15f047b8b2d299d41eff1
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
  from Data's authorized read-only mailbox projection. The connector later
  returned; Data announced busy, transitioned the assignment to `in_progress`,
  acted on all delivered mail, and acknowledged it.

## Result and validation

- Claim-first REF: `745f2a9db1f41a6563e6d3aba1703eec40279dc0`.
- Substantive architecture REF:
  `14ca63e94d8d1a06d8f15f047b8b2d299d41eff1`.
- Exact substantive paths: `TODO.md`, this claim,
  `docs/dossiers/dec-0041-007-atomic-cutover-task-graph.md`, and
  `docs/dossiers/0041-02-atomic-cutover-graph-repair-scope-review.md`.
- `DEC-0041-007` was absent from exact base
  `4022945cb123d4d619da5dd60527ab3e7bd61428`; the new record is cited by
  `TODO.md` and the scope review.
- `git diff --cached --check` before substantive commit: PASS.
- `process_doc_doctor.py --root . --json`: exit `0`, `ok: true`, zero
  findings attributable to either new dossier; two inherited link errors.
- `legacy_task_doctor.py --root . --json`: no cycle, unknown-endpoint,
  self-edge, or malformed affected-task finding. Disclosed target findings:
  the award-mandated claim filename differs from the Doctor's derived filename;
  two older `0041-02` architecture claims retain historical `[x]`; and existing
  `0041-05 [x]` now reports four terminal-unsatisfied-prerequisite findings
  after the four authorized predecessors reopen, in addition to its inherited
  missing-REF finding. The exact `0041-05` lifecycle impact and required
  separately scoped reconciliation are recorded in the scope review; this
  assignment did not mutate `0041-05` or foreign claims.
- No `DEC-0041-006` byte, implementation/tool path, other Feature/claim,
  Acceptance, checkpoint verdict, `DONE.md`, root/main ref, credential,
  external resource, or external system was mutated.

## Next step

Lore reviews `14ca63e94d8d1a06d8f15f047b8b2d299d41eff1`, routes the separately
scoped `0041-05` lifecycle reconciliation recorded by the scope review, and
then assembles an authorized integration candidate. No successor starts from
this architecture branch.

## Supervisor restart recovery — 2026-08-30

- **Disposition:** Data's architecture coordination is terminal and released;
  do not resume this owner token. `state: [ ]` and `recorded_task_state: [ ]`
  preserve the distinct current implementation Task state, while
  `coordination_state: complete` and `restart_recovery_state: terminal` record
  the final disposition of this architecture-only claim.
- The architecture handoff tip is `52b90dad40be8386b253f952ed5763966db2a7c3`.
  The mandatory checkpoint review is `94a681be11118e6e8e3c6bb42c63150d7286d9a8`,
  and current `main@f5763cf21e98066f7e932d50a2b0e9c5802550f9`
  carries the reviewed candidate.
- Implementation of `0041-02` belongs to the separately awarded Enterprise
  chain. This recovery grants Data no implementation, Acceptance, checkpoint,
  integration, or successor-start authority.
