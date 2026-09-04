---
schema_version: "1.0"
id: "0044-12"
level: "task"
parent: "0044"
state: "open"
visibility: "internal"
prerequisites:
  - "0044-01"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1217"
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

PREREQ: 0044-12:0044-01 Anchor recorded policy provenance: commit-trailer convention, `--no-ff` absorption rule, and the extended provenance check. Claim: `TODO-wesley-0044-12-20260824T161900Z-1787587942164.md` (owner token `agent:wesley:0044-12:20260824T161900Z-1787587942164`; candidate `b458fb33227cc554b57a4328a46b72391f222273`; current baseline `main@b32931d1dc3633934b297348aedf7b3259308b2c`).

## Scope

- REF: `b458fb33227cc554b57a4328a46b72391f222273` (0044-12 implementation completion; added by the privileged Integrator during checkpoint review to satisfy the repository's authoritative-REF bookkeeping convention — the commit itself was already cited above and in the Implementation completion note below, this only adds the recognized label).
  - **Implements:** `DEC-0044-008`, `DEC-0044-011` ([`dec-branching-merging-strategie.md`](docs/dossiers/dec-branching-merging-strategie.md)).
  - **Context:** `0044-01` established that policy provenance cannot be reconstructed from git topology: a commit absorbed by `git merge --ff-only`/`git update-ref` is indistinguishable from a natively authored one (third `[u]` verdict, `b62df43a8`). `DEC-0044-007` accepted that as a residual limitation with a prose `--no-ff` control scoped to the mechanical check. Management extended this repository-wide: provenance is **recorded**, not inferred, and the burden of proof lies with whoever introduces the commit.
  - **Integration review: mandatory.** **Rationale (provisional — conservative default, not an architect decision):** this changes binding merge semantics repository-wide, the same ground on which `0044-01` was flagged. Set by Projektleiter Kathryn, who does not set checkpoints; the contract offers only *mandatory* or a *no-checkpoint justification*, and only an architect may give the latter. Failing closed is therefore the sole honest default. The architect confirms this or downgrades it with a recorded justification, at the latest at `0044-08`. **Rationale (architect):** confirmed mandatory by Architect `seven` (Seven of Nine), 2026-08-24 — full statement in the Architect checkpoint decision immediately below.
  - **Implementation completion (2026-08-24, `agent:wesley:0044-12:20260824T161900Z-1787587942164`, capability class `unprivileged`):** Candidate REF: `b458fb33227cc554b57a4328a46b72391f222273`, after explicit `--no-ff` merge of current `main` into branch `0044-12` (merge tip `b458fb3`; no rebase/history rewrite). Focused provenance suite: 21/21 PASS, exit 0; `py_compile` PASS; `git diff --check` PASS. Live read-only provenance check `0044-12 → main`: exit 0, no foreign-branch or missing-trailer findings; expected `source-origin` and `target-pull-in-eligible` findings only. Targeted automation-safety validation retains pre-existing `AUTO001`/`AUTO010` at `_src/tools/test_check_policy_provenance.py:212` (unchanged since `675717c83e1f22e3d20be577b5c1f64b40ba1857`); strict process-doc validation retains the repository baseline of 30 findings, including pre-existing `DOC001`/`DOC003`. No Acceptance, checkpoint crossing, Feature/main integration, or `DONE.md` move performed.
    - **Architect checkpoint decision (2026-08-24, Architect `seven`, Seven of Nine; recorded per `process-roles.md` §Architect and the `AGENTS.md` checkpoint contract):** **confirmed — mandatory.** The node changes binding merge semantics repository-wide (`--no-ff` absorption rule, trailer requirement) and adds a provenance gate every future integration must satisfy: `material-architecture-or-repository-behavior` with plain cross-item reach, and a defect here ships silently into the provenance of everything integrated afterwards. The provisional rationale is adopted.

## Acceptance criteria

- **AC-001** A commit-trailer convention for policy-touching commits is specified (name, value, when required) in `branch-workflow.md` and consistent with `AGENTS.md`
- **AC-002** the `--no-ff` rule for absorption outside an item's own predecessor/successor chain is stated as binding, consistent with the existing `DEC-0044-007` paragraph
- **AC-003** `_src/tools/check_policy_provenance.py` verifies the trailer where required and reports a missing trailer as a finding, with tests
- **AC-004** `DEC-0044-002`'s extension by `DEC-0044-011` is recorded additively in the intake dossier without deleting the original text
- **AC-005** the effective date is stated and no retroactive claim is made against pre-decision history

## Definition of Done

Committed; authority documents agree; the check runs read-only against real branches; registered in `docs/pipeline/tools.md`; no contradiction with `DEC-0044-007` (which remains valid as the narrower case).
