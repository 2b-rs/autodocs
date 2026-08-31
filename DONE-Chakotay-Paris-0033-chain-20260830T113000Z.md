# Claim — Chakotay-Paris-20260830T113000Z

**owner_token:** `agent:chakotay-paris:0033-chain:20260830T113000Z`
**capability_class:** `unprivileged`
**execution_authority:** direct Git/test execution in own worktree, no runner queue
**item_id:** chain `0033-02` → `0033-03` → `0033-04` (STOP before `0033-04.01`)
**branch:** `chain-0033-chakotay`
**worktree:** `/Users/tobias.anton/devel/.worktrees/chain-0033-chakotay`
**base pin:** `main@3736170586e85047ab68691f0596689610688d9c`
**dispatcher:** `chakotay` (Dispatcher), atomically-awarded priority offer `1787970210735-b3950909`

## Assignment summary

Author fresh **Class R** ("reconstructed proposal") deliverables for Tasks `0033-02`,
`0033-03`, `0033-04` per the Architect scope review
`docs/dossiers/0033-02-04-architect-scope-review.md` (Architect `seven`,
`scope-ok-with-conditions`, blocked on §0.4 — verified resolved at this base pin, see
below) and Management decision `DEC-0033-002`
(`docs/dossiers/dec-0033-002-recovery-strategy.md`, Option A).

## Startup verification performed

- Verified `main` tip `3736170586` carries the marker repair (`fce918a6a`,
  "backlog-repair(0033): revert 23 false-positive [x] markers") and the checkpoint
  placement (`1bc5ca6f8`, "0033: place Feature integration checkpoints per architect
  scope review §4.2"). Confirmed by direct `grep` of `TODO.md` at this pin: `0033-02`,
  `0033-03`, `0033-04`, `0033-04.01` are all `[ ]`, and `0033-04.01` carries
  `**Integration review: mandatory.**` with the architect rationale. **§0.4 precondition
  is satisfied at this base pin** — this chain is startable.
- Read `docs/dossiers/0033-02-04-architect-scope-review.md` in full (§0–§11).
- Read `docs/dossiers/dec-0033-002-recovery-strategy.md` (`DEC-0033-002`) in full.
- Read exact current `TODO.md` text for `0033-02` (line 1727), `0033-03` (line 1733),
  `0033-04` (line 1739), `0033-04.01` (line 1745).
- Read Class E substantive commits for informative context, cited by SHA, never merged:
  `ac4b2579a5` (0033-02 candidate), `7c21351cfa` (0033-03 candidate), `d0eca203e3`
  (0033-04 candidate). Confirmed all remain reachable (`git cat-file -e`).

## Class discipline (per this briefing and scope review §2)

- **Class E** (historical, immutable, cited by SHA, never merged/cherry-picked): the five
  packet tips `ee3dfe99c096`, `0edf6ce5323e`, `46bef8cbcb76`, `0fe384069df7`,
  `960d53295c6a`, and their substantive commits `ac4b2579a5`, `7c21351cfa`, `d0eca203e3`.
- **Class R** (this chain's entire output): fresh content under `docs/dossiers/0033-*`,
  `docs/campaign-evidence/0033-recovery/**`, `_src/tests/**` and
  `_src/tests/fixtures/review_request_v2/**`. Every commit states class per path.
- **Never written by this chain:** anything under `docs/pipeline/**`, `AGENTS.md`,
  `SANDBOX.md`, `PRIVILEGED.md`, `CLAUDE.md`, `DONE.md`, `docs/pipeline/{branch-workflow,
  process-roles,task-acceptance}.md`, `TODO.md` header contract, any `DEC-*` record.
  `TODO.md` item-marker/bookkeeping edits confined to the `0033-02`/`0033-03`/`0033-04`
  item blocks only.
- **Never merged/cherry-picked:** `0033-02-blackout-recovery`, `0033-03-blackout-recovery`,
  `0033-04-blackout-recovery`, any historical `0033-*` branch, or any `0039-05.01`/
  Acceptance-policy ancestry.
- **Not in scope:** `0033-04.01` itself (the approval gate) — this chain stops before it.

## Write scope (exact)

- `docs/dossiers/0033-*`
- `docs/campaign-evidence/0033-recovery/**`
- `_src/tests/**`, `_src/tests/fixtures/review_request_v2/**`
- this claim file
- `0033-02`/`0033-03`/`0033-04` bookkeeping blocks in `TODO.md` (marker/REF only)

## Assumptions

- "Review-ready" deliverable = a Class R dossier stating the full policy/schema/UX
  contract content itself (not a stub pointing at unwritten `docs/pipeline/` files),
  since Class O placement is `0033-04.01`'s exclusive act and cannot happen in this
  chain. The dossier is written as the candidate text that `0033-04.01` would approve
  and a later Task would then land verbatim into `docs/pipeline/`.
- Informed by Class E content (`ac4b2579a5`, `7c21351cfa`, `d0eca203e3`) for topic
  coverage and defect list, but authored as fresh prose/structure, not copied.

## Progress log

- 2026-08-30T11:30Z — worktree/branch provisioned off pinned base; scope-review and
  decision record read in full; task texts read; Class E citations confirmed reachable;
  claim committed as first micro-commit.
