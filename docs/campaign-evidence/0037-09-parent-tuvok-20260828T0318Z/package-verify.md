# 0037-09 parent package verification (Tuvok, 2026-08-28)

Persona: unprivileged Programmer `tuvok-0037-09-parent-20260828` (not gabriel, not Chapel, not Adira 20260825).
owner_token: `agent:tuvok-0037-09-parent-20260828:0037-09:20260828T031800Z`
Baseline: `main@9cd0075225c6cf6d06faeef2ee432123c923a1b9` (remeasured immediately before branch cut).
Branch: `0037-09-parent-tuvok-20260828T0318Z`
Worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-09-tuvok-parent-20260828T0318Z`
Stale `0037-09@063b9c04eb68e770ef7b2f9b7d7ea3aeff5c984a` was not merged.

## Verdict

No package-level source defect. Shared `_src/tools/issue_validate.py` already covers IV0900–IV0908, IV0910–IV0944 (no IV0909), is side-effect-free, and accepts explicit working-tree / candidate / staged-index / authoritative roots. `_src/validate.py` `CHECKS` includes `check_issue_store` with `--issue-source` `{working-tree,staged-index,candidate,off}` plus `--issue-root` / `--issue-authoritative-root` / `--issue-dag` / `--issue-generated-root`. No product edit.

## Commands and results

| Command | Result |
|---|---|
| `uv run python _src/tests/test_issue_validate.py` | 58/58 OK, 25.365s |
| `uv run python _src/tests/test_issue_validate_dag_ae5.py` | 5/5 OK, 0.028s |
| `python3 -m py_compile` on `issue_validate.py`, `validate.py`, both test modules | PASS |
| `uv run python _src/tools/automation_safety.py --json --path _src/tools/issue_validate.py --path _src/validate.py --path _src/tests/test_issue_validate.py --path _src/tests/test_issue_validate_dag_ae5.py` | PASS, 0 findings, 0 policy errors |
| `git diff --check` on those paths | PASS (no product delta) |
| Repo-wide `automation_safety.py --json` | FAIL, 82 findings / 40 policy errors — pre-existing global, not introduced here |

`uv run python` importing `_src/validate.py` failed with `No module named 'lxml'` in the toolchain venv (only `ruamel.yaml` locked). Wiring was instead proven by source inspection of `CHECKS` and `parse_validate_cli`, plus the existing `DerivedArtifactValidateTest.test_validate_py_candidate_and_staged_modes` (reads `validate.py` text; 58-test run includes it). Full HTML-tree `validate.py` was not executed in this venv.

## Rule coverage (architecture IDs on this baseline)

Implemented Diagnostic/Configuration IDs: IV0900–IV0908, IV0910–IV0944.

IV0900–IV0903 are configuration/limit/duplicate/self-edge codes. 09.01 fixtures map several structural cases to parser `IS08xx` IDs (IS0803, IS0804, IS0824, IS0826, IS0829, IS0832, IS0835, IS0836, IS0840) plus IV0904–IV0906; IV0907/IV0908 are asserted in `IssueValidateTest`. 09.02–.04 fixtures plus unit tests cover IV0910–IV0944. Combined suite does not silently drop sibling rules (`test_existing_structural_and_lifecycle_rules_are_unchanged`, `test_existing_structural_lifecycle_and_provenance_rules_hold`).

## Acceptance mapping

- Shared diagnostics/config: one module, one `Diagnostic` type, one CLI.
- Side-effect free: mutation guards in tests; scoped automation-safety PASS.
- Explicit roots: `--root` / `--authoritative-root` / `--source` on `issue_validate.py`; `--issue-*` on `validate.py`.
- No silent weakening: sibling-additive tests still fire IV0904 and IV0911 after later packages.
