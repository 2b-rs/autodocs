# Management and Architect decision packet — 0033-02 through 0033-04 recovery

**Status:** Decision preparation only. No decision, Architect appointment, approval, Acceptance, or implementation authority is claimed here.

**Evidence baseline:** `main@af5cf982c8c6dfe8446f120c2695985a5aa3052f`

**Permanent inventory:** `docs/campaign-evidence/0033-recovery/0033-02-04-inventory.md`

## 1. Decision required

Management must decide whether and how the recoverable 0033-02/03/04 candidate suite should be reintroduced into the current Feature 0033 plan. A distinct Management-instantiated Architect must then bind the selected scope, affected work units, prerequisites, checkpoint placement, and the boundary between proposal evidence and operative governance before any product or gate mutation.

The decision is required because the old branches contain useful, test-backed candidate work but also:

- modify binding `docs/pipeline/` paths while labelling themselves unapproved;
- declare gates and contracts that affect numerous later work units;
- diverge materially from current `main` and current `TODO.md`;
- carry no current authoritative Task lifecycle or Acceptance state;
- and, in 0033-04, inherit a separate `0039-05.01`/Acceptance-policy chain that is not UX-owned.

## 2. Machine-linkable evidence

| Scope | References |
|---|---|
| Recovery baseline | `af5cf982c8c6dfe8446f120c2695985a5aa3052f` |
| Recovery claim | `f25b9487b35f735618ec94fbfd101398d3ac64f1` |
| 0033-02 | tip `ee3dfe99c0966a6605328271008a146eb746fa8b`; substantive `ac4b2579a52f4e6acc94873de6964e0aab059663` |
| 0033-03 | tip `0edf6ce5323ea0eb56535b76dbc627777f1074dc`; prerequisite merge `53a5c68d9c28c7177080f49056fc52d8be27d564`; substantive `7c21351cfa9a189d90fa71ec464bd485aa755acf` |
| 0033-04 | tip `46bef8cbcb76e812c3c6aa2bdfc55ea52f76d3bf`; prerequisite merges `5af29c12beef055c18d9b00673d373149b57defe` and `98d2a3f60d09177124a3c9fa2016ad2fb1984b33`; substantive `d0eca203e381d0adbde382ce446c8f1e74e45ed8` |
| Extra shared-contract ancestor | `0033-03.01@0fe384069df760191e07023e01d4a59e5a802f38`, later acceptance-bearing tip `960d53295c6ad27170d49c442867f132f76b3095` |
| Foreign policy ancestry | `0039-05.01@25aa69c4ca` through merge `012be8cf0d` inside `0fe384069d..960d53295c` |
| Coordination authority | AWARD `agent-inbox:1787959173731-a7980aed`; scope `agent-inbox:1787959339773-a1b03432` |

## 3. Options

### Option A — reconstruct selected candidates on the current baseline (recommended)

Keep the old branches immutable as evidence. After Management selects the policy axes below and a distinct Architect records the exact cross-item scope, create new bounded Task work from current `main`. Recover reviewed content by deliberate reconstruction, not history merge:

1. retain candidate/dossier material as non-operative evidence until approved;
2. reconcile process/privacy choices first;
3. reconcile schema/identity/trust choices against the selected process;
4. reconcile UX/storage/no-JS choices against both;
5. approve the exact combined suite through the current authorized gate;
6. only then update binding pipeline documents and downstream implementation contracts through their current branches/checkpoints.

**Benefits:** preserves useful analysis, fixtures, vectors, and scenario maps; respects current governance placement; avoids importing obsolete TODO/bookkeeping and foreign 0039 history; makes proposal-to-operative transition explicit.

**Risks/costs:** requires current-baseline reconciliation and fresh validation; old test results are evidence but not proof against current code; every selected policy needs explicit authority and traceability.

**Compensating controls:** exact source-ref matrix; path-by-path provenance; no bulk merge/cherry-pick; candidate/operative status lint; current-main diff review; independent Architect scope review; separate implementation and acceptance reviewers; current prerequisite/checkpoint graph validation.

### Option B — adopt the old branches substantially as written

Attempt to carry the historical candidates and their Task histories into current Feature 0033.

**Benefits:** least re-authoring; retains original commit topology and tests.

**Risks:** very high. It would import obsolete `TODO.md` semantics and claims, overwrite or conflict with materially changed pipeline governance, make unapproved content appear binding, and risk importing `0033-03.01` plus unrelated `0039-05.01`/Acceptance-policy ancestry through 0033-04. It also bypasses current worktree/governance and cross-item gate procedures.

**Disposition:** not recommended. It should be unavailable unless Management explicitly authorizes an exceptional, path-filtered migration with a distinct Architect review and independent integration plan; even then it should reconstruct trees rather than merge the historical branch tips.

### Option C — retire the historical suite and redesign from current requirements

Retain the old refs solely as negative/history evidence and restart 0033-02/03/04 without reusing their candidate content.

**Benefits:** cleanest current-baseline design; no inherited governance/history ambiguity.

**Risks:** discards substantial useful work: exhaustive process decisions, canonical identity vectors, schema fixtures, migration cases, accessibility/no-JS scenarios, and prior defect reconciliation. Re-derivation may recreate already-solved contradictions.

**Disposition:** viable only if Management rejects the underlying candidate architecture or determines it cannot be reconciled safely. Otherwise Option A is smaller and more intent-preserving.

## 4. Management selections required before Architect binding

The smallest decision surface is the following set of axes; Management may adopt the historical recommendations, change them, or return them for additional preparation:

1. **Canonical process and invariants:** request-versus-decision separation; rejected/no-apply; authority identities; lifecycle and publication boundary.
2. **Eligibility and recurrence:** eligible page/record/status inventory; legacy/null-version handling; duplicate/concern/recurrence and race semantics.
3. **Identity and trust:** v2 event/concern/package/envelope model; GitHub API/webhook/combined profiles; actor mismatch; self-declared intake.
4. **Privacy and records:** projections, retention clocks, holds, backups, GitHub/controller limits, migration/quarantine/redaction, residual history.
5. **Security and abuse:** URL/fetch policy, quotas/windows/capacity, moderator/quarantine/release/escalation authority, telemetry minimization.
6. **UX and transport:** eligible contexts, shared local collection migration, exact-byte confirmation, receipt/result channel, retry/edit identity, no-JS flow, accessibility/mobile contract.
7. **Recovery strategy:** select Option A, B, or C and authorize the Architect to produce the binding current-baseline decomposition.

These correspond to the historical `PROC-0033-02-01`–`PROC-0033-02-17` suite. The historical values are recommendations, not current policy.

## 5. Required Architect output after Management selection

The assigned Architect should produce one current-baseline scope record that:

- names every affected Task and external consumer, including all units enumerated in the inventory;
- states which historical candidate bytes are evidence, which are reconstructed proposals, and which become operative only after approval;
- resolves the current prerequisite drift, especially the historical `0033-04:0033-03.01` edge and the role of `0033-04.01`;
- identifies exactly one Feature integration task and any additional mandatory checkpoints with rationale;
- separates 0033 recovery from `0039-05.01` and historical Acceptance-policy provenance;
- defines path ownership for governance on `main` versus ordinary products on item branches;
- maps each policy decision to implementation and validation owners;
- preserves independent Acceptance and integration review;
- includes rollback/recovery steps and a current-main validation matrix.

The Architect review is a pre-mutation scope review. It is not approval of the product suite, Task Acceptance, or an integration verdict.

## 6. Stop boundary

Until Management selects an option and the distinct Architect scope record is integrated through its authorized route:

- do not mutate `TODO.md`, `docs/pipeline/`, Task products, or source branches;
- do not merge or cherry-pick `0033-02`, `0033-03`, or `0033-04`;
- do not infer Acceptance or checkpoint authority from historical 0033-04 ancestry;
- do not enter `0033-04.01`, `0033-05`, or later implementation work from this packet;
- do not allocate a decision identifier from this recovery branch.

