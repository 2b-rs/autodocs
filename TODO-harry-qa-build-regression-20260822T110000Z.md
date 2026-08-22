# Claim: Harry QA Build/Validate Regression 2026-08-22

owner_token: agent:harry:qa-build-regression-20260822:20260822T110000Z
capability_class: unprivileged
execution_authority: direct Git, Python, virtualenv, dependency installation, build, validation, and tests; never use `run.sh`
dispatcher: kathryn (Projektleiter), agent-inbox thread `qa`, message `1787395406013-18a8f1df`
branch: `qa-build-regression-20260822-harry`
worktree: `.worktrees/qa-harry-build-20260822T110000Z`
base_commit: `478a89e7c2a4052fbd3bff8d81da932d94924896`
comparison_commit: `f9c8050ff2b367be7fe7c4eefe24b83a178f950c`

## Assignment

Run the complete repository build and validation after the 2026-08-22 recovery and subsequent main changes. Compare the current result with an older main baseline so known dead-link findings are not misreported as regressions. Report actual counts and retain evidence.

## Authority boundaries

- QA execution and evidence only; no acceptance, integration checkpoint, `Acceptance: ✓`, main advance, publication, or `DONE.md` change.
- Never mutate the shared root checkout.
- Build/validation mutations occur only in item-owned disposable worktrees.

## Write and execution scope

- Tracked writes: this claim and `docs/campaign-evidence/qa-build-regression-20260822/report.md`.
- Disposable execution: `/private/tmp/autodocs-qa-harry-{current,baseline,venv,logs}-20260822T110000Z`.
- Build-generated changes in disposable worktrees are evidence only and are not integrated.
- External resources: Python package index only if the required packages are not already available from the local package cache; no repository push or other external mutation.

## Startup review

- Root `main` and `HEAD` were both `478a89e7c2a4052fbd3bff8d81da932d94924896` at discovery.
- The shared root contains unrelated untracked files and directories; none are in scope and none will be modified.
- The earlier `TODO-kathryn-harry-20260822T003000Z.md` claim is terminal and has a different immutable owner token; it is not resumed.
- This is a user-directed QA activity rather than an existing backlog Task, so no unrelated `TODO.md` item is marked `[p]`.

## Status

Implementation complete. Both isolated runs generated 428 pages with exit 0. Both validations executed 11 checks and returned exit 1 with the same 13 dead-link findings; their CLI outputs are byte-identical. No regression was found between `f9c8050ff` and `478a89e7c`. The later main tip `388018fdd` differs only in a release-authorization evidence document outside build inputs. Durable summary: `docs/campaign-evidence/qa-build-regression-20260822/report.md`.

Next: commit this claim and report with the user prompt provenance, notify Kathryn, then continue with assigned QA task 2.
