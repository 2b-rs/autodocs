# Claim: `0041-02` atomic check-in contract and activation manifest

task_id: 0041-02
feature_id: 0041
request_id: 1788079620073-b1d511e4
assignment_id: 1788079620073-b1d511e4
owner_token: agent:beverly:0041-02:1788079620073-b1d511e4
base_commit: f5763cf21e98066f7e932d50a2b0e9c5802550f9
capability_class: unprivileged
execution_authority: direct execution in the assigned item-owned worktree; non-operative implementation only
startup_review: AGENTS.md; SANDBOX.md; TODO.md current 0041-02 contract and Feature 0041 graph
state: [ ]
assignment_state: review
work_product_status: [x]
coordination_state: ready_for_review
substantive_ref: 2b7eaa8662f7aa9a5bb66c011fa1d36e793b33ad
next_step: coordinator routes the exact committed candidate to the separately assigned independent privileged 0041-02 checkpoint reviewer; TODO.md remains outside this award

## Assignment and branch

- Atomic award: `1788079620073-b1d511e4` under chain authority `1788079413412-6ee70689`.
- Process: implementation.
- Branch/worktree: `0041-02-atomic-contract-beverly-20260830`; `/Users/tobias.anton/devel/autodocs/.worktrees/0041-02-atomic-contract-beverly-20260830`.
- Exact base: `main@f5763cf21e98066f7e932d50a2b0e9c5802550f9`; worktree clean at startup.
- Direct prerequisite `0041-01` is `[x]`; current `0041-02` is `[ ]` and was explicitly reopened by `DEC-0041-007` for fresh current-main derivation.

## Exhaustive write scope

- `docs/dossiers/0041-02-atomic-checkin-contract.md`
- `docs/pipeline/fixtures/0041-02/atomic-cutover-manifest.json`
- `docs/pipeline/fixtures/0041-02/README.md`
- `TODO-beverly-0041-02-atomic-contract-20260830.md`

No `TODO.md`, authority, operative consumer, tool, test, historical candidate, foreign claim, or other path may be modified.

## Required result and validation

- Produce `atomic-checkin-contract@v1` and exhaustive `atomic-cutover-manifest@v1` from current-main bytes.
- Define exact trailer grammar/error vocabulary, carrying-tree and claim-finalization invariants, `[x]`/`[w]` and Acceptance boundaries, historical/reopened migration, activation validation order, rollback set, old-writer absence proof, and positive/negative/migration/rollback examples.
- Bind current blob digests and candidate outputs; map every `DEC-0041-006` consequence and Beverly blocker; retain whole-consumer discovery evidence.
- Validate schema/digests, manifest completeness, exact scope, and `git diff --check` while proving the operative two-commit rule remains byte-unchanged.

## Prohibitions

No operative consumer or authority change; no reuse, copy, or merge of historical candidates; no Acceptance, checkpoint crossing, integration, `main`/`DONE.md` movement, successor start, external effect, root-checkout mutation, or write outside scope. Lore separately routes the mandatory independent privileged checkpoint review.

## Mailbox resume — 2026-08-30

- Message `1788080367101-843a8ffc` requested resumption of atomic award
  `1788079620073-b1d511e4` from the preserved draft without restart. The award,
  owner token, branch, worktree, base, and exact scope were independently
  reverified before mutation.
- The agent-inbox MCP operations are unavailable in this runtime. This record is
  the durable follow-up for that message; acknowledge it when MCP access is
  restored. The read-only mailbox projection cannot acknowledge or announce.

## Completion evidence and findings

- The candidate defines one exact trailer grammar, carrying-tree and finalized
  claim invariants, stable fail-closed error vocabulary, historical/reopened
  migration, Acceptance separation, synchronous activation, old-writer proof,
  rollback, positive/negative examples, and requirement/decision trace.
- `atomic-cutover-manifest@v1` pins 21 current live consumers across normative,
  editing, transaction, diagnostic, hygiene, test, and guidance categories; it
  also pins three authority inputs and orders 20 activation validations.
- The `0041-06` contract names `_src/tests/test_runner_transaction.py` and
  `_src/tests/test_check_integration_hygiene.py`, but the observed live tests are
  `_src/tools/test_runner_transaction.py` and
  `_src/tools/test_check_integration_hygiene.py`. Both mismatches are explicit
  activation blockers; no scope was silently inferred or widened.
- A draft premise was corrected before commit: the open claim cannot contain the
  exact claim-first commit's own object ID. The contract now requires immutable
  transaction/attempt capture of that `HEAD`, followed by copying the known
  value into the finalized claim in the carrying tree.
- Contract SHA-256:
  `3cc470954cae2809ff4ef719fd87ef203dd2eb9585995f1e818bd86cb65f40a9`.
- Manifest SHA-256:
  `fe132eafc1bdd709357b81670704d2363afdb1deeebe9adda7d276e75dd770f8`.
- README SHA-256:
  `dff0a5b7baa2ae0621ae6c3e9699472641077406b904ae05408ac670fda01383`.
- Strict JSON duplicate-key/schema/digest/completeness validation: PASS; 21
  consumer digests, three authority digests, pinned candidate outputs, two
  declared mismatches, unique validation order, and exact current consumer set.
- Contract semantic coverage: PASS; 12 numbered sections, 21 stable `ATC-*`
  codes, six requirement mappings, and explicit `0041-02`/`03`/`06`/`05`
  boundaries.
- README relative-file validation: PASS. `git diff --check`: PASS.
- `process_doc_doctor.py --root . --json`: exit 0 / `ok: true`; 34 retained
  repository findings, none against this candidate's new paths.
- `legacy_task_doctor.py --root . --json`: repository-wide exit 1 with 1,491
  retained findings. The sole candidate-path finding is the award-mandated
  noncanonical claim filename. The canonical `state: [ ]` remains aligned with
  `TODO.md`; separate `assignment_state: review` and `work_product_status: [x]`
  preserve the review-ready work-product lifecycle without moving the Task.
  No product path receives a Doctor finding.
- Exact source lineage: `main@f5763cf21e98066f7e932d50a2b0e9c5802550f9`
  followed only by claim-first commit `ef5369a99e3ddcead35211de530f977b6b047d34`
  before product mutation. Historical candidate `8b1afb933f` was not merged,
  cherry-picked, rebased, squashed, or copied.
- Substantive candidate REF:
  `2b7eaa8662f7aa9a5bb66c011fa1d36e793b33ad`; exact four-path staged set and
  `git diff --cached --check` passed before commit, and `git show --check` passed
  afterwards.
- No operative consumer, authority document, Task marker, historical record,
  external system, credential, Acceptance, checkpoint, integration ref, or
  Feature state was changed.

## Next step

Coordinator routes the exact committed candidate and its reported substantive
REF to the separately assigned independent privileged `0041-02` checkpoint
reviewer. The reviewer must treat the two declared `0041-06` test-path mismatches
as activation blockers, not as permission to infer scope. `TODO.md` bookkeeping,
Acceptance, checkpoint crossing, integration, and successor start remain outside
this award.
