# 0043-07 publication run (FRESH RUN) — stage 00: pre-run state

Agent: Tom-Vasquez-20260824T084000Z   Recorded: 2026-08-24T07:24:54Z
Worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0043-07   Branch: 0043-07   HEAD: 0348dfdefcc9e118df9b8e4e3918ed5e90863ab8
New cohort run ref: manual-20260824T072259Z-d6eece5d

This is a **restart**, named explicitly. See F-TOM-VASQUEZ-001 in
TODO-Tom-Vasquez-0043-07-20260824T084000Z.md for why the previous cohort
manual-20260824T022631Z-6c6f72ee (aborted validate stage, ~6h gap) was not
continued. Tom-Rivera's committed stage evidence (00-03) is kept verbatim as
the historical record of the interrupted attempt; this run's evidence uses the
10-* numbering so the two trails cannot be confused.

## Ledger before the run (tracked, append-only)
```
git status --porcelain -- docs/evidence/build-ledger.jsonl  ->  (empty below means clean)
line count: 1
sha256: eb43c604ebc2b968a8e9872c3760c6107799b4075e56da718a9d3c6087a44be7
```

Identical to the sha256 Tom-Rivera recorded before his attempt
(eb43c604ebc2b968a8e9872c3760c6107799b4075e56da718a9d3c6087a44be7): the aborted
sessions left **no partial entry**. Had one existed it would have been reported
to belanna as a finding, never cleaned up.

## Orphaned raw subreports of the aborted attempt (git-ignored per DEC-0043-001)
```
html_generate-1787538538.json                 html_generate   manual-20260824T022631Z-6c6f72ee  finished=2026-08-24T02:28:58Z exit=0
i18n_diagrams-1787538454.json                 i18n_diagrams   manual-20260824T022631Z-6c6f72ee  finished=2026-08-24T02:27:34Z exit=0
i18n_merge-1787538401.json                    i18n_merge      manual-20260824T022631Z-6c6f72ee  finished=2026-08-24T02:26:41Z exit=1
```

Disposition: removed before this run so that exactly one cohort exists locally
and this run's ledger entry cannot be attributed to a torn one. Their identifying
fields are transcribed above, so removing the git-ignored scratch loses nothing.
The cohort was incomplete (no validate subreport), so it was never a publication
candidate under 0043-04's _eligible_publication_cohorts().

## Note carried into the run — F-TOM-VASQUEZ-002 (pre-existing, out of scope)

The i18n_merge subreport of the aborted attempt records exit_code=1 with 107
error findings of category 'merge-reject' ('<id>: unbekannte Segment-ID'),
although the shell exit status was 0. i18n_translate.py sets the subreport's
exit_code to 1 whenever any segment is rejected (_src/i18n_translate.py:257).
These 107 stale entries live in the tracked English translation work files and
have nothing to do with Feature 0043. They are expected to recur in this run and
will drive combine's overall_success to false. Repairing them means editing
translation source data, which is outside this Task's write scope. Flagged for
belanna rather than worked around.

## Working tree before the run
```
?? docs/campaign-evidence/0043-07-publication-run/04-validate-before-combine.txt
?? docs/campaign-evidence/0043-07-publication-run/10-pre-run-state.md
(empty = clean)
```
