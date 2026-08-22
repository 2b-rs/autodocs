# Independent re-review claim — Task 0044-16

- reviewer: `Data-Geordi-20260822T213740Z`
- persona: Geordi
- role: Integrator
- capability_class: `privileged`
- execution_authority: direct Git and tests; never `run.sh`
- assignment: exact Task `0044-16` re-review only
- dispatcher: Data
- review_branch: `review-0044-16-data-geordi-20260822T213740Z`
- review_worktree: `.review-worktrees/0044-16-data-geordi-20260822T213740Z`
- review_base: `ea0646721da70f9eae5f37a6f4b6881f47466b40`
- candidate_branch: `0044-16`
- candidate_tip: `e3561d47b4e2e0ddc4ebbf2a5af1bd8f813ab13a`
- substantive_correction: `42e80f6e7412616999f42a865e3eefe8c985c85a`
- prior_rejected_review: `a141a493817f57ecf076180ccd2854f20207d0a4`
- prior_finding: `F-0044-16-GEORDI-01`
- status: `accepted`

## Independence and boundaries

The reviewer is distinct from dispatcher Data and implementer
`Harry-Kira-20260822T184500Z`; the reviewer did not author the candidate or its
validation. This assignment authorizes review evidence and, only for an
accepted verdict, a separate `TODO.md` acceptance-bookkeeping commit. It does
not authorize candidate fixes, Feature or `main` integration, ref movement,
`DONE.md`, push, or runner use.

## Write scope

- `docs/campaign-evidence/review-0044-16-20260822-data-geordi-r2/report.md`
- `TODO-Data-Geordi-0044-16-rereview-20260822T213740Z.md`
- only if accepted: `TODO.md`, Task `0044-16` acceptance record only, in a
  separate path-isolated commit

## Review focus

Preserve the prior rejection append-only and test the correction independently:
all non-persistent findings must omit the three optional age/re-sample keys,
while persistent `FOREIGN_STAGED_TREE` must populate all three. Reconfirm one
shared re-sample, blocking semantics, root/stale findings, all-worktree scope,
hard root preflight, exit `2`, and timing evidence.

## Startup preflight

The hard root preflight passed at `ea0646721da70f9eae5f37a6f4b6881f47466b40`.
The live hygiene check passed with 129 registered worktrees, zero findings, in
117.81 seconds wall. An earlier scan at the prior `main` tip was discarded after
`main` advanced cleanly during that scan.

## Verdict and validation

Verdict `accepted` for exact candidate
`e3561d47b4e2e0ddc4ebbf2a5af1bd8f813ab13a`. The independent negative control
proved the rejected candidate leaks all three null keys across all four
non-persistent codes and the corrected candidate omits them all; persistent
`FOREIGN_STAGED_TREE` retains all populated metadata and exits `1`. Focused 6/6,
missing-repository exit `2`, root/stale fixtures, one shared delay, full-scope
enumeration, automation safety, process-doc comparison, and live 130-worktree
scan passed. Live wall time was 133.76 seconds and is retained as an operational
observation.

Review report:
`docs/campaign-evidence/review-0044-16-20260822-data-geordi-r2/report.md`.
The evidence commit containing this claim/report is the Review REF used by the
separate acceptance bookkeeping commit.
