# 0044-03 pre-mutation gate-scope review

- Reviewer: `Data-Lore-20260822T205800Z`, persona Lore
- Role: privileged Architect; direct Git/tests, no runner
- Dispatcher: `Data`
- Preparer/implementer boundary: `Data-Iris-20260822T150415Z`
- Date: 2026-08-22
- Verdict: `scope-ok-mit-auflagen`
- Decision: `DEC-0044-019`

This is an independent cross-item gate-scope and authority review before policy
mutation. It is not Task acceptance, an integration review, an integration
verdict, or `Acceptance: ✓`. No Feature or checkpoint boundary is crossed here.

## Pinned baseline and sources

| Item | Pin / SHA-256 |
|---|---|
| review baseline `main` | `0d04432d6a4c6ae7f67a7818c6b9ab93266a527d` |
| preparation branch handoff | `fef61dd0c38099c9e334a371fb3f52f29a68becc` |
| proposal commit | `9e65d0ebaa63e55c4c8e1e741e311107d04d5609` |
| proposal bytes | `79be55ece8aca9a1ffefc9f67bda343b71fbcbd82fb0124aa6432f5cad06464e` |
| `AGENTS.md` | `93c3ea9de9bd6587d4a9b728af6a2502a670d589cda9788a9490e5e112e8fa34` |
| `SANDBOX.md` | `ea607b2a06967a97a68037aedc3474d4b2d6f41c1f0b35a8302a1ca88c6dd739` |
| `TODO.md` / Task contract and inventory | `64a736b4d232a88a7006a3513520e24c514c9a96c5a6832d0e2fc0e98766f45e` |
| `decision-record.md` | `dea2c93ad046d67a129d6b30b7715609a49afde26f47e5039cc2c2159cdb66c0` |
| `process-roles.md` | `02007d8f22927ba2740235bd8d0a4772aaa476db2fe4b1591e8505f8389f4096` |
| `task-acceptance.md` | `f333c4ec09b89a670d6a92d33175937eb7a419b4549b356274bdb8805eb7351f` |
| `branch-workflow.md` | `6f875c8341b4cf055cb6167025f86eaf62959439e2566bca61bd92a73fdec0fe` |
| RQ-IP-07 source/intake | `a33c8b6c8bf67314aee24014e5f7f8e97e6cf2228756fb3f26927a5d66dd8bbe` |
| decision dossier before append | `ca42c14b9a801e1c5384bce9521879efe24b45a534f12a7a2240d19eff3265cf` |

I read the complete preparation proposal as context, not authority; the Task
contract, RQ-IP-07 source/intake, decision-record format, process-role,
acceptance and branch-workflow rules; `DEC-0044-017` and its 0044-04 review
pattern; the reservation for `DEC-0044-019`; and the current checkpoint
inventory. The reservation is correctly treated as allocation only.

## Dispatch and independence record

- Dispatching identity: `Data`.
- Reviewer persona: Lore, explicitly distinct from dispatcher Data and from
  preparer/implementer `Data-Iris-20260822T150415Z`.
- Context given: the complete briefing below; candidate branch and exact
  proposal/handoff commits; named governing repository documents; required
  units/gates, activation direction, write scope, and prohibitions.
- Context not given: no private reasoning, expected draft text, preselected
  verdict, acceptance decision, integration authority, or authority to mutate
  policy implementation. Repository evidence was read independently.
- This idle thread previously completed an unrelated `0038-33` review under
  persona Geordi. No prior verdict, context, privilege exercise, or authority
  from that task authorizes or informs this `0044-03` decision. The identity and
  role were re-announced as Lore/Architect before this work.

### Entire follow-up briefing, verbatim

```text
Begin a NEW, separate assignment and explicitly change persona/identity to Data-Lore-20260822T205800Z. Re-announce to agent-inbox because role changes to Architect; do not carry Geordi review authority into this task. This Lore turn is dedicated only to 0044-03 and must not later review 0044-02.

You are Data-Lore-20260822T205800Z. Explicitly assume persona Lore, privileged Architect, independent from implementer/preparer Data-Iris-20260822T150415Z and dispatcher Data. Keep all reports concise and in English. Announce to agent-inbox as `Data-Lore-20260822T205800Z`, role `Architect`, runtime `zed/gpt-5.6-sol`; check inbox at start and before every consequential action. Direct Git/tests only; never runner/run.sh.

Assignment: author the authoritative technical decision record `DEC-0044-019` for Task 0044-03 and perform the independent pre-mutation cross-item gate-scope review. This is not Task acceptance or integration. Reserved identifier DEC-0044-019 is recorded on main; reservation alone is not approval. Preparation branch `0044-03`, proposal commit `9e65d0ebaa63e55c4c8e1e741e311107d04d5609`, claim handoff `fef61dd0c`; read `docs/dossiers/0044-03-gate-scope-proposal.md` completely. Read AGENTS.md, SANDBOX.md, TODO.md, decision-record.md, process roles, task acceptance, branch workflow, RQ-IP-07 source/intake, DEC-0044-017 and 0044-04 scope-review pattern, and current checkpoint inventory.

Do independent analysis; the proposal is context, not a prescribed answer. Decide the binding executable integration-test obligation at mandatory checkpoints: derivation from architecture risks/interfaces/invariants/failure modes/external effects; minimum reproducible evidence; no-automation/manual fallback; fail/[u] path; separation from Acceptance authority. Explicitly assess affected units/gates, including current Feature-0044 checkpoints, task/integration 0044-08, feature closure, repository:autodocs, future `integration:*` and `feature-closure:*`, plus the real 0043-07 worked example. Management direction to test, not merely copy: repository-wide future reach should activate only after the 0043-07 example is actually executed and recorded; until then it binds only Feature-0044 trial nodes. Verify current checkpoint inventory and explain any changed/removed unit instead of silently dropping it.

Create branch `review-0044-03-data-lore-20260822T205800Z` and isolated worktree `/Users/tobias.anton/devel/autodocs/.review-worktrees/0044-03-data-lore-20260822T205800Z` from current main. Mandatory hygiene/root hard preflight before mutation. Exact write scope: append authoritative DEC-0044-019 content only in `docs/dossiers/dec-branching-merging-strategie.md`; new `docs/dossiers/0044-03-gate-scope-review.md`; `TODO-Data-Lore-0044-03-review-20260822T205800Z.md`; and `logs/check-in-provenance/0044-03-Data-Lore-20260822T205800Z.txt`. Do not modify policy implementation files, TODO task markers, Acceptance, Feature/main refs, DONE.md, or external state. Commit decision and review on the review branch; do not merge to main—Project Lead must integrate governance using the authorized worktree procedure.

DEC-0044-013 record requirement: reproduce THIS ENTIRE FOLLOW-UP BRIEFING verbatim in the scope-review record; record dispatching identity Data, reviewer persona Lore, context given and not given, and that the idle thread previously completed unrelated 0038-33 review but no prior verdict/context authorizes this task. Record one scope verdict: scope-ok, scope-ok-mit-auflagen, scope-zu-weit, scope-zu-eng, or unschluessig. If the technical decision cannot be made without Management authority, mark that exact portion unresolved and do not invent approval. Report commits, verdict, affected units/gates, conditions, validation, and integration handoff to Data/Kathryn.
```

## Independent scope analysis

### Predicate and authority

The canonical `cross-item-blast-radius` predicate applies. The rule changes the
evidence contract of other work units and can block their integration and
closure when evidence is missing or fails. This is declared gate behavior, not
a hypothetical bug or a shared-path inference. Architect authority covers the
test architecture and staged scope. It does not cover acceptance, specialist
waivers, or a silent risk acceptance; the existing Integrator `[u]` path is
therefore retained.

### Binding executable obligation

At a mandatory checkpoint the Integrator must execute verification against the
exact integrated candidate. A green branch-local run is insufficient when the
candidate tree differs. The derivation basis is a closed review matrix over:

1. architecture risks and changed integration seams;
2. interfaces, schemas, protocols, and compatibility contracts;
3. invariants and data/state transitions;
4. negative, failure, recovery, and rollback modes; and
5. external effects, exercised through a safe fixture, dry run, or a bounded
   manual procedure where real execution is unsafe.

Each applicable row names an executable test kind and oracle. A row may be
non-applicable only with a concrete reason. This is proportional: it does not
require every test kind at every checkpoint.

Minimum retained evidence is: checkpoint and boundary; exact candidate and
target refs/trees; inputs/fixtures; material environment and tool identities;
command or typed manual procedure; expected and actual result; exit status;
digest-bound logs/artifacts; exclusions, gaps, and residual risk; and replay
instructions. The evidence must let an independent reviewer reproduce or
falsify the result.

When automation is absent, a manual procedure is acceptable only if it is
reproducible and has a falsifiable oracle. Its limits and the automation gap are
recorded. If the criterion cannot safely or credibly be established, the result
is not “not applicable” or pass: the checkpoint fails and the Integrator uses
the existing `[u]` integration verdict/escalation path.

No test exit status grants `Acceptance: ✓`, supplies a missing specialist
decision, waives a criterion, or permits integration by itself. The required
review authority evaluates the evidence separately.

### Staged reach and worked example

The management direction is technically sound with one necessary control: the
activation event must be reviewable, not inferred from the mere existence of a
file. Therefore:

- The rule binds Feature-0044 trial checkpoints immediately after the decision
  and review are integrated to `main`.
- `0043-07` is the real qualification example. Before broad activation it is an
  experimental application of this rule, not repository-wide authority and not
  acceptance of Feature 0043.
- Repository-wide prospective reach for future `integration:*` and
  `feature-closure:*` activates only when `0043-07` has actually executed and
  recorded the required derived evidence and `0044-08` confirms it.
- If the example is absent, generic, irreproducible, or cannot establish a
  criterion, `0044-08` fails/takes `[u]`; broad activation remains dormant.

This prevents a worked-example promise from being mistaken for a completed
qualification while giving `0044-08` one exact activation check.

### Current inventory and proposal delta

Current `TODO.md` marks these Feature-0044 nodes mandatory: `0044-01`,
`0044-04`, `0044-05`, `0044-12`, `0044-13`, `0044-14`, `0044-15`,
`0044-16`, and integrating Task `0044-08`. The proposal listed all except
`0044-16`; that Task was added after the proposal's pinned baseline. It is
included here. No listed checkpoint was silently removed.

`0044-14` and `0044-15` already have accepted historical reviews. This decision
does not retroactively invalidate them. Their records are inputs to `0044-08`;
any new execution or re-review follows the new trial rule. `0044-01` remains a
declared checkpoint even though its long review history predates this decision.

Affected work units are `task:0044-03`, the nine current Feature-0044
checkpoint Tasks above, `feature:0044`, `task:0043-07`, `feature:0043`, the two
implementation policy paths, and `repository:autodocs`. Exact current gates are
listed in `DEC-0044-019`; wildcard future reach is stated in prose because the
`decision-record@v1` gate grammar requires an exact `integration:<ID>` or
`feature-closure:<ID>`, not `*`.

## Verdict and binding conditions

**Verdict: `scope-ok-mit-auflagen`.** No unresolved Management-only technical
choice remains. The following conditions are part of the approval:

1. Integrate `DEC-0044-019` and this review to `main` before any qualifying
   policy mutation for `0044-03`.
2. Bind only Feature-0044 trial checkpoints initially; do not claim
   repository-wide activation from the decision record alone.
3. Use `0043-07` as an actually executed, retained derivation example; a generic
   suite listing is not sufficient.
4. Make `0044-08` the explicit broad-activation confirmation. Failure or
   missing evidence leaves future reach dormant and uses fail/`[u]`.
5. Include `0044-16` in the live inventory. Re-pin and explain any later
   inventory change before implementation rather than silently dropping it.
6. Test the exact integrated candidate and retain the complete reproducibility
   minimum; branch-local green evidence alone is insufficient.
7. Treat manual fallback as bounded evidence, never a waiver or silent pass.
8. Keep test evidence, Task acceptance, specialist authority, integration
   verdicts, and Feature closure as separate decisions.

## Validation and handoff

Before worktree creation, the root hard preflight passed (`HEAD` was current
`main`, tracked worktree and index clean) and
`check_integration_hygiene.py --repo /Users/tobias.anton/devel/autodocs`
returned `PASS` over 123 registered worktrees. Validation after authoring must
confirmed only the four assigned paths changed; `git diff --check` passed; the
`decision-record@v1` fields, IDs, alternatives, exact work-unit/gate reference
grammar, participation, and waiver were checked against the pinned format; the
two briefing copies are byte-identical; and branch/base identity matched the
pinned values. `process_doc_doctor.py` scanned 108 documents with zero errors
and the same 30 advisory findings as `main` (107 documents). No product test is
evidence of scope authority and none can replace this review.

Project Lead must integrate the governance branch using the authorized
worktree/hygiene procedure. Neither this report nor its green validations move
`main`, change Task markers, accept work, or authorize Lore to review `0044-02`.
