# 0043-07 publication run — stage 00: pre-run state

Agent: Tom-Rivera-20260824T042500Z   Recorded: 2026-08-24T02:26:18Z
Worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0043-07   Branch: 0043-07   HEAD: 82ac886cf6c15cbde020051041127576d9f11d03

## Ledger before the run (tracked, append-only)
```
git status --porcelain -- docs/evidence/build-ledger.jsonl  ->  (empty below means clean)
line count:        1
sha256: eb43c604ebc2b968a8e9872c3760c6107799b4075e56da718a9d3c6087a44be7
```

## Working tree before the run
```
?? docs/campaign-evidence/0043-07-publication-run/
(empty = clean)
```

## Foreign leftover cohort from the aborted Tom-Sabine-20260824T013000Z run

git-ignored raw output under output/build-reports/ per DEC-0043-001. Her run
reached a COMPLETE four-stage cohort under ref manual-20260824T013644Z-16b903fd
but never ran 'combine', so it never became a ledger entry.

```
total 80
-rw-r--r--  1 tobias.anton  staff    474 Aug 24 03:43 html_generate-1787535801.json
-rw-r--r--  1 tobias.anton  staff    510 Aug 24 03:48 html_generate-1787536120.json
-rw-r--r--  1 tobias.anton  staff    491 Aug 24 03:38 i18n_diagrams-1787535507.json
-rw-r--r--  1 tobias.anton  staff  17076 Aug 24 03:36 i18n_merge-1787535405.json
-rw-r--r--  1 tobias.anton  staff    805 Aug 24 03:36 validate-1787535379.json
-rw-r--r--  1 tobias.anton  staff    752 Aug 24 03:48 validate-1787536084.json

html_generate-1787535801.json                  html_generate  manual-20260824T013644Z-16b903fd
html_generate-1787536120.json                  html_generate  manual-20260824T013644Z-16b903fd
i18n_diagrams-1787535507.json                  i18n_diagrams  manual-20260824T013644Z-16b903fd
i18n_merge-1787535405.json                     i18n_merge     manual-20260824T013644Z-16b903fd
validate-1787535379.json                       validate       None
validate-1787536084.json                       validate       manual-20260824T013644Z-16b903fd
```

Disposition: removed before my run so that exactly one cohort exists and my
ledger entry cannot be attributed to a foreign, half-finished run. This is
git-ignored regenerable scratch belonging to a dead session, not evidence.
