# Claim: 0022-breakdown-activation

state: [p]
owner_token: agent:tuvok:0022-breakdown-activation:20260828T1202Z
request_id: 1787918503462-a563fbcf
capability_class: unprivileged
base_commit: 3c8538727d85f3d6851cb625b5583b00603094b2
execution_authority: direct local Git and read-only validators in this item-owned worktree; no runner queue; no main movement
startup_review: AGENTS.md (claim/marker contract, autonomous backlog repair limits), SANDBOX.md (unprivileged capability class), docs/pipeline/feature-breakdown.md (Gate A1), docs/dossiers/dec-0022-001.md, docs/dossiers/0022-feature-breakdown-proposal.md, TODO.md Feature 0022 block

Note on identity: this is a governance/backlog **activation** activity, not a
`TODO.md` Task, so no `task_id` is declared. Per `AGENTS.md`, a directed activity
that is not an existing Task may use a coordination claim, and must not falsely
mark an unrelated Task `[p]`. Declaring a `task_id` here would invent one.

**Known residual finding, accepted deliberately.** `legacy_task_doctor` reports one
`LTD-CLAIM-IDENTITY-MISMATCH` against this file: `OWNER_TOKEN_RE`
(`_src/tools/legacy_task_doctor.py:33-37`) requires the `<task>` segment to match
`[0-9]{4}-[0-9]{2}(\.[0-9]{2})?`, so an owner token for a non-Task activity cannot
satisfy it. The two ways to clear it are both worse than the finding: binding the
token to `0022-01`, the Task this contract explicitly forbids me to implement, or
inventing a Task ID that exists nowhere in `TODO.md`. Either would make the claim
assert something untrue to satisfy a checker. **The finding is left standing and
reported as a schema gap** — the canonical claim schema has no representation for
the non-Task coordination claim that `AGENTS.md` expressly permits.

- **persona:** Tuvok, Security Engineer, Team Voyager — Implementer of the backlog activation only
- **award:** offer `1787918503462-a563fbcf`, coordinator `jean-luc`, notice `agent-inbox:1787918503463-119d5bf6`
- **branch:** `activate-0022-breakdown-tuvok-20260828`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/activate-0022-breakdown-tuvok-20260828`
- **base pin:** `main@3c8538727d85f3d6851cb625b5583b00603094b2` — verified equal to `main` at award time, zero drift

## Gate A1 — structured branch-time evidence

    field: A1-target-policy-integrability
    verdict: fits
    checked_target: main
    basis: "DEC-0022-001 (docs/dossiers/dec-0022-001.md, CON-01..CON-06) and its independent supporting review PART-01 agent:saru:0022-01-scope-review:20260828T100338Z (scope-ok-with-conditions at aebc93ede12ec979d7c84b3bf1574c48359429ec); breakdown proposal docs/dossiers/0022-feature-breakdown-proposal.md graph section; governance integration evidence docs/campaign-evidence/0022-01/governance-integration-geordi-20260828.md; TODO.md Feature 0022 block at the pinned base"
    checked_at: "2026-08-28T12:20:00Z"
    recorded_by: "Implementer (Security Engineer Tuvok), agent:tuvok:0022-breakdown-activation:20260828T1202Z"

The change is backlog activation of an already-decided and independently reviewed
decomposition. It adds no product, no schema, no validator, and no new start edge to any
consumer outside Feature `0022`; it therefore integrates into `main` without altering any
other work unit's contract.

## Contract being implemented (not authored by me)

- `DEC-0022-001` `CON-01`: preserve order `0022-01` → `0022-02.01` → `0022-02.02` → `0022-02` → `0022-03`; `0022-01` and terminal `0022-03` carry mandatory checkpoints.
- `CON-02`: `0022-02.02` stays candidate-root-only; no default shared gate.
- `ALT-04` rejected: **no** start edge added to `0023-11`, `0024-02`, or `0028-01`.
- Existing conditional `0029-01`, `0030-01`, `0031-01`, `0032-01` edges and the Feature prereqs `0022:0020`, `0022:0027-05` are preserved unchanged.

## write_scope (exact)

- `TODO.md`, **only** within the Feature `0022` block
- this claim file

## prohibitions (accepted)

No products, schemas, or validators; no modification of any consumer block outside Feature
`0022`; no implementation of `0022-01`; no Acceptance, checkpoint crossing, integration,
`main` move, or `DONE.md`; no foreign-state cleanup; no push or external effect; no gate
widening. Stop on baseline drift, decision/review mismatch, or ambiguity.

## progress

- 2026-08-28T12:02Z AWARDED via offer_reply; announced busy until 12:50Z.
- 2026-08-28T12:05Z Base pin verified equal to `main`; no prior involvement with Feature `0022`.
- 2026-08-28T12:20Z Claim and A1 field recorded **before** any `TODO.md` mutation. Next step: mutate the Feature `0022` block per `CON-01`, then validate identifiers, endpoints, direction, cycles, and markers.

## Write scope (exact paths)

- `TODO.md` — only within the Feature `0022` block
- `TODO-tuvok-0022-breakdown-activation-20260828T1202Z.md` — this claim

## Next step

Report the candidate tip to coordinator `jean-luc` and hand off for privileged
governance integration. No further mutation by this session: Acceptance,
checkpoint crossing, integration, and the `main` move are outside this claim.
