# Feature 0033 recovery inventory — Tasks 0033-02 through 0033-04

**Status:** Read-only recovery inventory. It does not adopt, merge, approve, accept, or activate any source content.

**Recovery baseline:** `main@af5cf982c8c6dfe8446f120c2695985a5aa3052f`

**Coordination:** atomic AWARD `agent-inbox:1787959173731-a7980aed`; exact scope `agent-inbox:1787959339773-a1b03432`; claim-first REF `f25b9487b35f735618ec94fbfd101398d3ac64f1`.

## 1. Executive finding

All three historical Task products remain recoverable as exact Git objects, and their Task-owned content can be separated from prerequisite and policy ancestry. None of the three exact source tips is an ancestor of the recovery baseline, and the recovery baseline is not an ancestor of any source tip. Current `main` therefore contains no authoritative adoption of those branches.

The documents repeatedly label themselves review-ready, unapproved candidates and reserve activation to `0033-04.01`. Their proposal-versus-operative status is therefore explicit. However, much of the candidate is written directly under `docs/pipeline/`, which current governance treats as binding shared state. Landing those bytes now would make cross-item process, trust, privacy, lifecycle, and implementation gates operative despite their own unapproved labels. No source merge or cherry-pick is safe without a current decision record and distinct Architect scope review.

## 2. Source topology and ownership

### 2.1 Task 0033-02 — process candidate

| Item | Exact reference |
|---|---|
| Source tip | `0033-02@ee3dfe99c0966a6605328271008a146eb746fa8b` |
| Substantive product | `ac4b2579a52f4e6acc94873de6964e0aab059663` |
| Source base / merge base with recovery baseline | `993ceffbcea4fa8f0cca16de07ac91cf88fae619` |
| Final bookkeeping | `ee3dfe99c0966a6605328271008a146eb746fa8b` |
| Source lifecycle | `[x]` at source tip; no `Acceptance: ✓`; no `Integration review: mandatory` attribute on the Task block |
| Current-main lifecycle | `[ ]`; no `Acceptance: ✓`; no checkpoint attribute on the Task block |

Task-owned substantive paths are the Zed claim, `TODO.md` bookkeeping, two dossiers, and eight pipeline documents:

- `TODO-zed-0033-02-20260819T062827Z-9382adfb03ce.md`
- `TODO.md`
- `docs/dossiers/0033-02-process-reconciliation.md`
- `docs/dossiers/0033-02-prompt-provenance.md`
- `docs/pipeline/actions.md`
- `docs/pipeline/curation-item-schema.md`
- `docs/pipeline/flag-for-review-protocol.md`
- `docs/pipeline/reports.md`
- `docs/pipeline/roles.md`
- `docs/pipeline/status-model.md`
- `docs/pipeline/website-review-flag.md`
- `docs/pipeline/workflow-lifecycle.md`

`ac4b2579a` calls the result an explicitly unapproved process candidate. It reserves seventeen choices, `PROC-0033-02-01` through `PROC-0033-02-17`, for the combined approval gate. The candidate nevertheless declares non-bypass behavior for request/decision separation, lifecycle, actor authority, rejection/no-apply, eligibility, duplicate detection, moderation, projections, retention, GitHub controller limits, and publication.

Named affected work units in the 0033-02 artifacts are: `0033-01`, `0033-02`, `0033-03`, `0033-04`, `0033-04.01`, `0033-05`, `0033-06`, `0033-07`, `0033-07.01`, `0033-07.02`, `0033-07.03`, `0033-07.04`, `0033-08`, `0033-11`, `0033-14`, and `0033-15.01`.

**Classification:** proposal, not operative at its historical source tip; qualifying cross-item gate scope if affirmatively adopted now.

### 2.2 Task 0033-03 — package, identity, and envelope candidate

| Item | Exact reference |
|---|---|
| Source tip | `0033-03@0edf6ce5323ea0eb56535b76dbc627777f1074dc` |
| Prerequisite merge | `53a5c68d9c28c7177080f49056fc52d8be27d564` carrying exact `0033-02@ee3dfe99c` |
| Substantive product | `7c21351cfa9a189d90fa71ec464bd485aa755acf` |
| Final bookkeeping | `0edf6ce5323ea0eb56535b76dbc627777f1074dc` |
| Source lifecycle | `[x]`; no `Acceptance: ✓`; no checkpoint attribute on the Task block |
| Current-main lifecycle | `[ ]`; no `Acceptance: ✓`; no checkpoint attribute on the Task block |

The prerequisite history is cleanly isolated in merge `53a5c68d9`. The 0033-03-owned substantive delta at `7c21351cf` contains:

- `TODO-zed-0033-03-20260819T065436Z-d9be66d964ba.md` and `TODO.md` bookkeeping;
- seven canonical/compatibility/valid/invalid fixture files under `_src/tests/fixtures/review_request_v2/`;
- `_src/tests/test_review_request_package_v2_contract.py`;
- `docs/dossiers/0033-03-prompt-provenance.md`;
- `docs/dossiers/0033-03-schema-reconciliation.md`;
- `docs/pipeline/review-request-package-schema.md`;
- `docs/pipeline/review-request-package-v2.schema.json`.

The candidate separates UUIDv7 event identity, deterministic concern identity, package digest, and transport/persistence identity; defines closed v2 package and envelope families; provides canonical vectors and compatibility dispositions; and leaves all GitHub trust profiles disabled. It expressly reserves profile activation, legacy classes, anonymous/self-declared intake, recurrence/duplicate policy, URL/fetch policy, actor mismatch, projections, retention, abuse controls, browser storage/PAT handling, and residual risk to `0033-04.01` and the `PROC-0033-02-*` suite.

Named affected work units in the 0033-03-owned artifacts are: `0033-01`, `0033-02`, `0033-03`, `0033-03.01`, `0033-04.01`, `0033-05`, `0033-06`, `0033-07`, `0033-07.02`, `0033-07.03`, `0033-08`, `0033-10`, and `0033-11`.

**Classification:** source ownership unambiguous; proposal and executable contract evidence, not an enabled trust/runtime profile; qualifying cross-item gate scope if adopted as binding schema or implementation prerequisite.

### 2.3 Task 0033-04 — UX candidate and foreign ancestry separation

| Item | Exact reference |
|---|---|
| Source tip | `0033-04@46bef8cbcb76e812c3c6aa2bdfc55ea52f76d3bf` |
| First prerequisite merge | `5af29c12beef055c18d9b00673d373149b57defe`, carrying `0033-03.01@0fe384069d` including 0033-02/03 history |
| Initial Task claim | `86b9aaa57ea86ef0b95860d62743871e446f9fc2` |
| Final prerequisite/acceptance merge | `98d2a3f60d09177124a3c9fa2016ad2fb1984b33`, carrying `0033-03.01@960d53295c` |
| Substantive product | `d0eca203e381d0adbde382ce446c8f1e74e45ed8` |
| Final bookkeeping | `46bef8cbcb76e812c3c6aa2bdfc55ea52f76d3bf` |
| Source lifecycle | `[x]`; no `Acceptance: ✓` for 0033-04; no checkpoint attribute on the Task block |
| Current-main lifecycle | `[ ]`; no `Acceptance: ✓`; no checkpoint attribute; current main no longer lists `0033-03.01` as an explicit prerequisite of 0033-04 |

The UX-owned product at `d0eca203e` is limited to the Donald and Grace claims, `TODO.md` bookkeeping, one focused test, two dossiers, and `docs/pipeline/review-request-ux.md`. The earlier Zed claim was created at `86b9aaa57e` and is also 0033-04 coordination history.

The delta `0fe384069d..960d53295c` brought in by `98d2a3f60` is not UX-owned. It consists of:

- accepted `0039-05.01` policy history and its `0039-04`/`0039-05.01` acceptance records;
- `0033-01` through `0033-03.01` acceptance review/bookkeeping;
- changes to `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `DONE.md`, `TODO.md`, and `docs/pipeline/{branch-workflow,process-roles,task-acceptance}.md`;
- acceptance-policy fixtures/tests and associated dossiers/claims.

That ancestry must be evaluated, if at all, through its own `0039` and Acceptance provenance. It must not be recovered, credited, or modified as part of 0033-04 UX recovery.

The UX candidate is expressly unapproved. It defines eligible contexts, byte-bound confirmation, local collection migration, truthful transport/ingestion states, accessibility/mobile behavior, no-JavaScript intake, and fourteen future scenario IDs. Named affected units include `0033-02`, `0033-03`, `0033-03.01`, `0033-04`, `0033-04.01`, `0033-05.01`, `0033-06`, `0033-10`, `0033-10.01`, `0033-11`, `0033-11.01`, `0033-13`, and `0042-02.01`.

**Classification:** UX-owned content is separable; the inherited `0033-03.01`/`0039`/Acceptance policy history is not UX-owned; the UX contract remains a proposal until authorized, but adoption changes downstream implementation and public-intake contracts.

## 3. Current-main divergence

At the recovery baseline, all three Tasks are reopened as `[ ]`. The historical claims, dossiers, v2 fixtures/tests/schema, and UX scenario/test artifacts are absent. The overlapping pipeline documents have materially diverged on current `main`. Direct branch merge or cherry-pick would therefore mix old `TODO.md` semantics, obsolete governance placement, and unrelated inherited histories with the current authority baseline.

The old source Tasks also predate the current rule that governance artifacts, including everything under `docs/pipeline/`, are shared main-state changes requiring their own governed integration route. Their historical location is evidence, not present authority to land them.

## 4. Gate reach and hidden authority choices

The combined suite can block or change other work through these declared gates:

1. `0033-04.01` approval of the exact combined process/schema/privacy/UX suite;
2. downstream implementation-start dependencies for strict validation, trusted ingestion, queue/lifecycle authority, privacy/retention, abuse control, browser/storage, accessibility, end-to-end validation, guidance, and release;
3. the non-bypass request/decision, rejected/no-apply, actor-authority, live-target, schema/trust, projection, retention, moderation, and publication rules;
4. binding shared vocabulary and schemas under `docs/pipeline/`;
5. the historically merged but separately owned `0033-03.01` and `0039-05.01` Acceptance-policy chain.

The policy and authority choices are not hidden in the prose after inspection: the 0033-02 candidate enumerates them as `PROC-0033-02-01`–`17`, and the 0033-03/04 candidates refer back to that suite. What was hidden at the branch-integration level is that placing unapproved candidates in binding pipeline paths would make them look operative, and that `0033-04` carries unrelated 0039/Acceptance governance ancestry.

## 5. Recovery constraints

- Preserve all exact source refs as read-only evidence.
- Do not merge or cherry-pick any source branch into current Feature/main history.
- Do not infer current Acceptance from the records inherited by `0033-04`; the exact 0033-02/03 tips had none, and 0033-04 itself has none.
- Do not credit `0039-05.01` or Acceptance-policy history to UX recovery.
- Before any operative gate mutation, require a conforming decision record and supporting scope review by a Management-instantiated Architect distinct from the future Implementer.
- Reconstruct only selected, reviewed content against current `main`, with candidate evidence separated from binding governance until authorized.

