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
state: [p]
next_step: read the current decision/re-derivation sources completely, inventory every live consumer from current-main bytes, then author and validate the non-operative contract and manifest

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

## Next step

Complete the required source review and current-main consumer inventory before the first product mutation.
