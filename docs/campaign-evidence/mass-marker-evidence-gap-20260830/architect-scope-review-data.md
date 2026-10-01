# Independent Architect scope review — misc-chain 12–23 marker correction

- **Review type:** pre-mutation cross-item gate-scope review; not Task
  Acceptance, integration review, release/risk approval, or implementation
- **Recorded at:** `2026-08-30T10:44:37+02:00`
- **Reviewer:** `agent:data:mass-marker-evidence-reconciliation-architect-review-data-20260830:1788078984596-2daa44e0`
- **Persona:** Data, Team Enterprise Architect; distinct from the inventory
  author, future correction Implementer, and Integrator
- **Assignment:** child AWARD `1788078984596-2daa44e0`
- **Dispatcher:** `william`, bound by
  `TODO-william-mass-marker-evidence-reconciliation-20260830.md`, parent AWARD
  `1788078667558-99919afc`, child AWARD `1788078984596-2daa44e0`, and Project
  Lead confirmation `1788079127323-97fac035`
- **Reviewed baseline:**
  `9875ede2c6ae9bbdfbde8422b05809b747948646`
- **Reviewed plan:**
  `docs/campaign-evidence/mass-marker-evidence-gap-20260830/marker-inventory-and-correction-plan.md`
- **Verdict:** **SCOPE SUPPORTED WITH MANDATORY PRECONDITIONS**

## Decision

Reverting exactly the 54 listed `[x]` markers to `[ ]` in one later,
current-`main`, compare-and-swap governance correction is the smallest complete
and intent-preserving correction scope. All 54 current completion projections
are unsupported on the reviewed authoritative lineage. No reviewed marker may
remain `[x]` on the strength of the misc-chain commits, their claims, the four
companion summaries, or unintegrated side-branch work.

This review supports only the scope. It does not authorize the mutation. Before
the first `TODO.md` marker change, a conforming `decision-record@v1` must be
reachable from current `main` and must name all 54 affected Tasks and the
successor gates below. This distinct Architect review must also be reachable
from the correction baseline. William supplied the Project Lead
`cross-item-blast-radius` confirmation as `1788079082806-e52e14be` through
message `1788079092620-12a68ac9`. A Project Lead re-plan is required before any
successor resumes from the corrected graph.

## Why the exact 54-marker unit is minimal

1. Each of the 12 incident commits changes only the selected `TODO.md` marker
   pairs from `[ ]` to `[x]`; their combined marker population is exactly 54.
   The Benjamin commits add only claims, and the four Worf companion commits add
   only claims plus prose summaries. None supplies a product/test delta bound to
   the affected Task criterion.
2. The current normalized authority projection contains zero visible
   authoritative `REF` records for all 54 Tasks and zero current Acceptance
   records for all 54. The companion summaries identify no exact product
   revision, test revision, command, retained output, signer, approval, or
   independent-review identity.
3. The 54 Tasks form 94 internal prerequisite edges and 50 successor Task-start
   gates. Correcting only a subset would leave at least one known unsupported
   completion projection available to open downstream work. One exact
   compare-and-swap transaction gives scanners and planners one coherent
   corrected baseline and avoids a partially repaired graph.
4. No additional Task marker is required in the correction. The only direct
   prerequisite successors outside the 54 are Feature nodes `0018` and `0026`;
   their closure gates become unsatisfied automatically. Changing their prose,
   any claim, any companion summary, any prerequisite, or any successor marker
   would exceed the smallest safe correction.

The correction must preserve the incident commits, claims, summaries, complete
Task text, prerequisite graph, checkpoint attributes, prior findings, and
history. A short append-only incident reference may be added only under the
separately authorized decision/re-plan; it is not required to make the marker
characters truthful.

## Affected successor gates

### Task-start gates

The exact graph has 94 edges from the 54 corrected Tasks to 50 corrected
successor Tasks. Those successor start gates are:

- Feature `0015`: `0015-10`.
- Feature `0018`: `0018-01`, `0018-02`, `0018-03`, `0018-04`, `0018-05`,
  `0018-06`, `0018-07`, `0018-08`, `0018-09`, `0018-10`.
- Feature `0023`: `0023-10`.
- Feature `0024`: `0024-01`, `0024-02`.
- Feature `0025`: `0025-02`, `0025-03`, `0025-04`, `0025-05`, `0025-06`,
  `0025-07`, `0025-08`, `0025-09`, `0025-10`.
- Feature `0033`: `0033-07.03`, `0033-07.04`, `0033-08`, `0033-09`,
  `0033-10`, `0033-11`, `0033-12`, `0033-13`, `0033-14`, `0033-15`,
  `0033-15.01`, `0033-15.02`, `0033-16`, `0033-16.01`.
- Feature `0035`: `0035-01`, `0035-02`, `0035-03`.
- Feature `0037`: `0037-32`, `0037-33`, `0037-34`, `0037-34.01`,
  `0037-34.02`, `0037-35`, `0037-35.01`, `0037-35.02`, `0037-36`,
  `0037-40`.

The four roots within the correction population are `0037-31`, `0033-07.01`,
`0033-07.02`, and `0023-09`; their own work must be re-established before the
listed successor chains can reopen. The two direct external prerequisite edges
are `0025-10 -> feature:0018` and `0023-10 -> feature:0026`.

### Validation, Acceptance, integration, publication, and closure gates

- **Validation:** all 54 Task-specific completion validations reopen. Material
  named gates include the `0033-08` real-store security/side-effect regression
  gate, `0025-02` selected-profile readiness gate, `0037-31` frozen migration
  candidate validation, clean/recovery checks `0037-35.01/.02`, and assessment
  evidence validation `0025-03/.04` and `0018-04/.05`.
- **Acceptance:** none of the 54 has current `Acceptance: ✓`. Reversion therefore
  invalidates no existing acceptance record; it prevents any future
  prerequisite-closed Acceptance batch from treating these unsupported states
  as terminal until ordinary work products, validation, real REF, claim, and
  required authority/independence exist.
- **Integration:** mandatory checkpoints `0037-34.02` and `0037-40` are affected
  and currently have no Acceptance. Their integration boundaries remain closed.
  The review does not move, add, remove, or satisfy either checkpoint.
- **Publication/release/external effect:** affected gates include `0024-02`
  release/delivery/receipt, `0025-09` assessment publication, `0025-10` Level-1
  success/CL2 handoff, `0018-09` result publication, `0018-10` CL2 claim,
  `0033-15.02` website release decision, `0033-16.01` post-decision audit and
  closure, `0037-34.02` authority cutover, and `0037-40` closure activation and
  write-freeze lift.
- **Feature closure:** contained work re-closes Features `0015`, `0018`, `0023`,
  `0024`, `0025`, `0033`, `0035`, and `0037`; the direct Feature prerequisite
  edge from `0023-10` additionally re-closes Feature `0026`. Feature `0018` is
  affected both by its contained Tasks and by its prerequisite on `0025-10`.

## Evidence disposition for all 54 markers

### Whole-population result

No marker satisfies the complete retention test: reachable task-bound product
or test REF, criterion-appropriate validation, truthful claim provenance,
satisfied prerequisites, and every required approval, signature, specialist
authority, and independent review. Therefore the exception set is empty.

The 12 incident deltas were independently checked with zero-context `TODO.md`
diffs: marker additions/deletions were respectively `4/4`, `3/3`, `7/7`,
`2/2`, `3/3`, `4/4`, `7/7`, `5/5`, `4/4`, `5/5`, `7/7`, and `3/3`, with
zero other `TODO.md` line changes. The normalized repository doctor reports no
visible authoritative REF for each of the 54 Tasks and no Acceptance for each.

### `0023-09` side-branch nuance

`0023-09` is the only reviewed marker for which the repository contains a
task-bound substantive product elsewhere: commit
`d2e9bbd26f168c9cb34c75b7ca6b480bc78c8572` adds the SWE.6 specification, and
R2 review commit `b0b0b9dac606c0881172f1876dc462fdcc0d7e6f` passes its content and
bookkeeping review. Neither commit is an ancestor of reviewed tip
`9875ede2c6ae9bbdfbde8422b05809b747948646` or inventory baseline
`4ad2a5ffe22ca733659ff0d07c9fa348065680fb`. The recorded final R2 verdict at
`000baeba43028af729a7bdf934f6e62fcf794205` is **BLOCKED** on integration
hygiene and expressly grants no Task Acceptance, successor work, release, or
external effect. The Task contract also requires approval, and no reachable
approval or Acceptance is present. Thus `0023-09` does not remain `[x]` in this
correction; its separately reviewed candidate may be integrated only through
its own fresh exact-baseline authority and then establish a new truthful
terminal state.

Other historical mentions of the 54 IDs are decision/backlog references,
subtask work, incident commits, or prose summaries; they do not bind a complete
product/test/authority package to the exact Task on the reviewed lineage.

## Mandatory controls and recovery

1. Land a conforming `decision-record@v1` before marker mutation. It must use at
   least `cross-item-blast-radius`, name the exact 54 Tasks, the 50 successor
   Task-start gates, Feature nodes `0018`/`0026`, checkpoints `0037-34.02` and
   `0037-40`, affected publication/release/external-effect gates, all nine
   Feature-closure gates, alternatives, consequences, activation, rollback,
   and this review participation.
2. Pin current `main`, expected `TODO.md` digest, exact 54 old/new lines, and
   absence of intervening Acceptance/checkpoint/contract changes. Any drift
   requires renewed impact analysis; do not mechanically apply this plan.
3. Change no Task text, prerequisite, REF, claim, Acceptance record, checkpoint
   attribute, summary, or incident history in the marker transaction. Do not
   represent `[ ]` as proof that underlying code is absent; it means the
   authoritative completion claim is not established.
4. Project Lead re-plans the corrected chains before successor dispatch. Each
   Task returns to `[p]` only under a real new/resumed claim; `[x]` requires its
   ordinary committed evidence and real REF. Specialist approvals, signatures,
   release/risk decisions, ECU evidence, and independent audits remain separate
   gates and are never inferred from this review.
5. Rollback of the correction, if the transaction itself is shown wrong, is a
   separately authorized append-only marker restoration bound to exact evidence
   and current graph state. Do not rewrite or delete incident/review history.

## Verbatim briefing and context boundary

```text
Capability class: privileged. Item: mass-marker-evidence-reconciliation-architect-review-data-20260830. Worktree: /Users/tobias.anton/devel/autodocs/.worktrees/mass-marker-evidence-reconciliation-enterprise-20260830 at exact tip 9875ede2c. Allowed paths exhaustive: docs/campaign-evidence/mass-marker-evidence-gap-20260830/architect-scope-review-data.md and architect-review-claim-data.md. Assume distinct Architect persona. Independently review the exact 54-marker plan: name affected successor gates; decide smallest safe correction scope; identify any marker supported by real task-bound product/test REF plus required authority/independence. Record dispatcher identity, distinct persona, verbatim briefing, supplied/withheld context. Commit only allowed files and return REF. Must not mutate TODO/DONE, accept work, cross checkpoint, move Feature, integrate, clean root, rewrite history, or infer release/risk authority. This is scope review only.
```

Supplied context was the exact branch/worktree/tip, exhaustive two-file scope,
committed inventory/plan, incident and companion commit identities,
paused-state/Project Lead references, current repository governance, and all
reachable local Git refs used for the bounded ancestry check. Withheld or
unavailable context includes uncommitted or external product/test evidence,
credentials, private materials, external ECU execution/assessment evidence,
signatures, approvals, release decisions, and every authority not present in
the committed record. No network or external source was used. Absence from this
review is not a claim that an underlying capability can never exist; it is a
finding that the reviewed authoritative completion projection lacks the
required bound evidence.
