# Integration claim — `0017-01` MAN.5 option-A governance R3

item: 0017-01-option-a-governance-integration-r3
task_id: 0017-01
feature_id: 0017
owner: geordi
owner_token: agent:geordi:0017-01:1787991796558-92629d4b
assignment_id: 1787991796558-92629d4b
status: [x]
coordination_state: integration_ready
capability_class: privileged
execution_authority: direct local execution and exact-boundary governance integration
branch: integrate-0017-01-option-a-geordi-r3-20260829
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/integrate-0017-01-option-a-geordi-r3-20260829
base_commit: 425b55efbe2a7764dc4ad9d729eb8309ceefa99b

## Exact contract and scope

- Atomic award: `1787991796558-92629d4b`.
- Source candidate: `0975aae06d218ea9d5290b7f30b9b77a7c30f376`.
- Target: `main@425b55efbe2a7764dc4ad9d729eb8309ceefa99b`.
- Incoming source paths are exactly:
  - `docs/dossiers/dec-0017-001-man5-risk-strategy.md`
  - `docs/dossiers/0017-01-man5-risk-strategy-scope-review.md`
  - `TODO-data-0017-01-man5-scope-review-20260829.md`
- R3-owned paths are exactly this claim and
  `docs/dossiers/0017-01-man5-risk-strategy-integration-r3.md`.

No strategy mutation, backlog/marker/Acceptance/Feature-reference mutation,
activation bookkeeping, risk/release/specialist decision, external effect,
credential, Memory write, push, cleanup, or Feature closure is authorized.

## Startup verification

- `main` and root `HEAD` matched the exact target before the worktree was made.
- The source commit's target-relative incoming delta is exactly the three named
  files. It was applied as `037ffd288` without conflict.
- Prior blocked attempts `ac6e5a0aa7f157eb6eb27ad093a6b5c47c2429ee`
  and `2763a9a59711521f073913156618fe8c1564729c` remain preserved and are not
  ancestors of this R3 branch.
- `decision-1787972295293-da9db52e` is resolved as Management option A.
- `DEC-0017-001` was absent from the exact target before integration.
- Architect Data is distinct from Implementer Tasha and Project Lead Jean-Luc.
- The strategy remains non-operative: this integration records only the
  decision, scope review, their source claim, and the R3 integration evidence.

## Validation and handoff

- Independent decision-record structure and option-A semantic review: PASS.
- C-01 through C-09 and the non-operative authority boundary: PASS.
- Exact five-path audit, placeholder scan, and `git diff --check`: PASS.
- `process_doc_doctor.py --root . --json`: PASS (`ok: true`); its one DOC001
  error is an unchanged pre-existing finding in
  `docs/dossiers/0044-03-gate-scope-proposal.md`, outside this candidate.

Final action is exact-candidate hygiene plus the immediate root
preflight/equality/fast-forward/postflight sequence. Any drift or non-zero gate
blocks the merge without repair.
