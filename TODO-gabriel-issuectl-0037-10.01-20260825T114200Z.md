# Claim: Subtask 0037-10.01

- owner_token: `agent:gabriel-issuectl:0037-10.01:20260825T114200Z`
- agent/persona: Gabriel-Issuectl, unprivileged Programmer, Team Discovery
- dispatcher: gabriel (this session); jean-luc `1787658051022-50ec1d09`
- capability_class: `unprivileged`
- execution_authority: direct local Shell/Git in this dedicated item worktree; no runner queue
- item/branch/worktree: `0037-10.01` / `0037-10.01` / `/Users/tobias.anton/devel/autodocs/.worktrees/0037-10.01`
- Feature base: `722aaa2149c78cf705db411a4142c67d92bb1c3d`
- prerequisite branches: `0037-08`, `0037-09`, `0037-17.01` already `[x]` on Feature tip; no extra merge
- exact_write_scope:
  - `_src/tools/issuectl.py`
  - `_src/tests/test_issuectl.py`
  - `TODO-gabriel-issuectl-0037-10.01-20260825T114200Z.md`
  - `TODO.md` (0037-10.01 Task block only)
- forbidden: `0037-10.02`, `0037-10.03`; Worf-released set overlap except this item; live generated repository TODO.md/DONE.md as product; Acceptance; checkpoint merge; Feature DONE.md; main; push; cleanup/recovery of root; parent 0037-11; 0037-23.01
- status: `[p]`; **claim materialization only**. No product mutation before this claim commit REF is known.
- next_step: implement item creation and controlled structural edits in issuectl after claim REF.

## Task

Implement item creation and controlled structural edits.

- **Acceptance criteria:** Create Feature/Task/Subtask paths; edit approved front-matter fields; allocate/withdraw/supersede/move `AC-NNN`; and add/remove prerequisites/relations using expected input digest and atomic temp-file replacement. Validate ID/path/parent, cycles, criterion invariants, claim/write scope, and no-op behavior before promotion; preserve unrelated prose bytes.
- **Definition of Done:** Tests cover each operation, concurrent edit rejection, invalid cycle/parent/move, criterion history, crash rollback, dry-run diff, and byte-stable no-op.
