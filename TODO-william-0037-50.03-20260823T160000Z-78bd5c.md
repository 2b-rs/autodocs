# Coordination claim — `0037-50.03`

- `owner_token: agent:william:0037-50.03:20260823T160000Z-78bd5c`
- `capability_class: unprivileged`
- `execution_authority: direct-local-execution`
- `process_role: Implementer`
- `assignment: implement the dormant, digest-bound runner-protocol rollback bundle and coordinated executor`
- `branch: 0037-50.03`
- `worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0037-50.03`
- `base: 0037-50@8f6e27ffc7b19b255f93399136378f27ff55289a`
- `startup_review: inbox clear; `TODO.md` at main `9dcbaaee11482f62205e1c0b7a43989477dee5d7` and parent task wording reviewed; `DEC-0037-001` at `0ffac017ef05ef14dd6e622f94bc1580d3e4f1f5` reviewed; branch and worktree were absent before creation; base pin verified exact.`
- `write_scope:`
  - `issues/_policy/runner-protocol-rollback-v1.json`
  - `issues/_schema/runner-protocol-rollback-v1.schema.json`
  - `_src/tools/runner_protocol_rollback.py`
  - `_src/tests/test_runner_protocol_rollback.py`
  - `TODO-william-0037-50.03-20260823T160000Z-78bd5c.md`
  - `TODO.md` (`0037-50.03` bookkeeping only, after substantive REF)
- `external_resources: none`
- `must_not: accept/review; cross any checkpoint; merge upward; mutate Feature/main; deploy or make host/network changes; push; mutate governance or runner admission/retirement wiring; touch .02 paths.`

## Scope and next step

Implement only the dormant executor, its policy and schema, and focused tests. It must restore the service before the selector only after active-claim drain, bind each payload to corrected `46fdd6398` lineage digests, retain verified append-only event/blocked state on every failure class, and leave no production call site.

## Additive release — 2026-08-24

- disposition: **superseded by DEC-0037-002** (integrated on `main` at `7a10f50d76e5620f3b7e3c796093c88037bb54bd`)
- authority: explicit Project Lead `jean-luc` coordination assignment, mailbox `1787586335426-d322bef1`; DEC-0037-002 names `subtask:0037-50.03` and supersedes DEC-0037-001's unimplemented corrective chain for planning.
- preserved starting tip: `0037-50.03@7ef4a317ae467a831cd1bcd8d898075a68699162`.
- release action: no further implementation started. Existing preparation state and this claim's startup evidence remain untouched; only this additive claim record is committed.
- boundaries retained: no acceptance, integration, `main`, `TODO.md`, or `DONE.md` mutation; no production rollback or host action.
