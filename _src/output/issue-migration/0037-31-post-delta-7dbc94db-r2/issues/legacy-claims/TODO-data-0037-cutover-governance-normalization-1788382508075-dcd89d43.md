# Architect claim — Feature `0037` Wave-B governance normalization

- **owner_token:** `agent:data:0037-cutover-governance-normalization:1788382508075-dcd89d43`
- **request_id:** `1788382508075-dcd89d43`
- **assignment/award:** `agent-inbox:1788383431170-a516ad6c`
- **process:** Architecture
- **status:** `[x]` — bounded Architecture record complete and ready for distinct review/integration
- **architect_work_product_status:** `[x]`
- **capability_class:** `privileged`
- **execution_authority:** Direct local execution in this item-owned worktree; no acceptance, integration, release, external-effect, or `main`-advance authority is exercised.
- **branch:** `0037-cutover-governance-normalization-20260902`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-cutover-governance-normalization-20260902`
- **base_commit:** `a0623411bfb3590ae4a3d8d08177064554651401` (`refs/heads/main` at claim creation)
- **write_scope:** this claim and `docs/dossiers/dec-0037-006-wave-b-governance-normalization.md`
- **external_resources:** none
- **prerequisites:** current `main`; `DEC-0037-005`; current Feature `0037` cutover contracts and Tasks `0037-34.02`/`0037-40`

## Bounded contract

Create `DEC-0037-006` as one conforming `decision-record@v1` that resolves only these four
Feature `0037` effectful Wave-B contradictions:

1. After `0037-34.02`, the issue store is authoritative while issue-item and
   claim writes remain frozen until `0037-40`; provenance/control evidence is
   the only permitted write class in the interim.
2. The canonical selector vocabulary is `issue-store-write-frozen` with
   `write_phase: frozen`; prose or data spelling `issue-store-frozen` is an
   obsolete alias to map during migration and then retire.
3. The canonical approval namespace is plural
   `refs/autodocs/approvals/...`.
4. Native multi-ref CAS updates only dedicated authority/resource refs and
   MUST NOT move `refs/heads/main`; reviewed source integration remains a
   separate root-checkout `git merge --ff-only` operation under hygiene gates.

The record names affected work units and gates, alternatives, consequences,
rollback, and the exactly-one-writable-authority invariant. It does not
implement commands, change selectors, mutate `TODO.md`/`DONE.md`, accept work,
perform a distinct scope review, cross an integration checkpoint, advance
`main`, push, or move Feature `0037` to `DONE.md`.

## Sources and startup evidence

- Authoritative award: `agent-inbox:1788383431170-a516ad6c`, created from
  priority offer/preparation `1788382508075-dcd89d43`.
- Normative sources: `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`,
  `docs/pipeline/feature-breakdown.md`, `docs/pipeline/decision-record.md`,
  `docs/pipeline/task-acceptance.md`, and the Architect role SOP.
- Architecture sources: Feature `0037` in `TODO.md`, Tasks `0037-34.02` and
  `0037-40`, `docs/pipeline/agent-workflow.md`,
  `docs/pipeline/issue-cutover-rollback.md`, and `DEC-0037-005`.
- Repository evidence: live `main` was `a0623411bfb3590ae4a3d8d08177064554651401`;
  no `DEC-0037-006` record, target branch, or target worktree existed before
  creation; the new worktree was clean at that exact base.
- Assumption: the award is the already-resolved Architecture decision input,
  so no unresolved `decision-request@v1` is created.

```yaml
target_policy_check:
  field: A1-target-policy-integrability
  verdict: fits
  checked_target: main
  basis: "The award resolves contradictions already present across Feature 0037 cutover contracts; the candidate records governance only and leaves implementation, integration, and activation to their existing gates."
  checked_at: "2026-09-03T00:04:12+02:00"
  recorded_by: "Architect agent:data:0037-cutover-governance-normalization:1788382508075-dcd89d43"
```

## Recovery and validation

- Before integration, abandoning this branch/worktree leaves `main` unchanged;
  retain the branch because its reachability must be proved before deletion.
- Validate the exact record shape, unique identifier, required vocabulary,
  four resolved contradictions, affected units/gates, rollback, and prohibited
  effects. Run exact-path diff/status checks and `git diff --check`.
- Commit only the two declared paths with `Task-ID` and `Base-Ref` trailers,
  then return the exact commit plus preparation/award identifiers.

## Completion evidence

- `DEC-0037-006` is unique against live `main`; required fields occur once in
  normative order, with four alternatives, one selected disposition, nine
  consequences, and every assigned term present.
- `python3 _src/tools/process_doc_doctor.py --json` reports no error on either
  assigned path. It reports one non-blocking `DOC005` warning on the new
  decision because the doctor excludes coordination claims from durable
  cross-document citation credit; an implementing Wave-B consumer must add the
  first operative citation during its separately assigned mutation. The full
  baseline reports 2 errors and 35 warnings, with no other finding on either
  assigned path.
- `git diff --check` passes; the candidate path population is exactly this
  claim plus `docs/dossiers/dec-0037-006-wave-b-governance-normalization.md`.
- No selector, effect command, approval ref, Task marker, Acceptance record,
  integration ref, `main` ref, external system, or prior `0046-01.01` file was
  mutated.

## Preserved prior follow-up

The older `0046-01.01` award (`agent-inbox:1788291607270-deb257f8`) has no
matching active Data claim on current `main`; its assigned worktree contains
four untracked deliverables under that award's declared write scope. They are
preserved untouched. Reconciliation of that assignment remains a separate
coordinator action after this newer priority Architecture award and is not
part of this claim.
