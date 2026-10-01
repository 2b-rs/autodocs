# Task 0043-07 — Disposition of every `RQ-BR-*` requirement

- **Agent:** `Tom-Adeyemi-20260824T133000Z` (Dispatcher `tom`, unprivileged)
- **Recorded:** 2026-08-24T16:30Z
- **Branch:** `0043-07`
- **Cohort under test:** `manual-20260824T072259Z-d6eece5d`
- **Evidence base:** `docs/campaign-evidence/0043-07-publication-run/` stages 10–20,
  ledger `docs/evidence/build-ledger.jsonl` (2 lines)

The `0043-07` acceptance criterion requires that **every `RQ-BR-*` requirement has a
disposition**. Seven requirements are covered by the six predecessor Tasks. Each disposition
below is stated against evidence produced by *this* end-to-end run wherever the run can
exercise it, not merely against the predecessor's own completion note.

**These dispositions are an implementer's evidence-backed assessment. They are not acceptance.**
Acceptance of `0043-07` and of the Feature is `belanna`'s at the mandatory integration
checkpoint.

---

## RQ-BR-01 — full build history rendered on `build-reports.html` (Task `0043-03`)

**Disposition: SATISFIED, and exercised for the first time with a real multi-row history.**

`0043-03` was accepted on a ledger that contained exactly **one** entry (the backfilled
historic run). Its acceptance criterion — "complete ledger as a build list, newest first" —
could not, at that time, actually distinguish a list from a single-run rendering. This run
supplied the missing second entry and the requirement now stands on a genuine list:

- `build-reports.html` contains `manual-20260824T072259Z-d6eece5d` (3 occurrences) —
  stage 19.
- The new run appears **without any manual editing**: the page was produced by
  `build_report.py publish` + `generate.py` only (stages 18, 19); no HTML was hand-edited,
  as `CLAUDE.md`'s golden rule requires.
- Rendering is ledger-driven: the page model's binding fields are byte-equal to the newest
  ledger entry (stage 19 table).

**Notable, and reported rather than assumed:** the `F-BELANNA-0043-03-01` fix (never link a
`combined_report_ref` that points into git-ignored `output/`) had likewise only ever been
tested against one ledger row. With two rows, `build-reports.html` contains **0**
`href="output/build-reports..."` occurrences and full `validate.py` reports all internal
links valid (stage 20). The fix generalizes.

## RQ-BR-02 — run correlation, every run sets `RUN_ARCHIVE_REF` (Task `0043-01`)

**Disposition: SATISFIED.**

All four producers of this cohort carry one shared, non-null ref, and `combine` correlated
them without starvation:

- ledger entry `run_archive_ref = "manual-20260824T072259Z-d6eece5d"` (non-null, and
  distinguishably `manual-`-prefixed per `0043-01`'s fallback design, because this build ran
  outside the runner);
- `counts_by_stage` carries all **four** required stages — `i18n_merge`, `i18n_diagrams`,
  `html_generate`, `validate` — i.e. the cohort was complete, which is exactly the condition
  `combine` starved on before `0043-01`.

## RQ-BR-03 — tracked append-only build ledger (Task `0043-02`, implements `DEC-0043-001`)

**Disposition: SATISFIED, with the append-only and idempotence properties proven live.**

This run produced the **first real (non-backfilled) ledger entry** in the project's history.
Measured, not assumed:

- 1 → 2 lines at `combine` (stage 16);
- line 1 **byte-identical** before and after, verified by diff, not inspection — entries are
  not rewritten;
- `backfilled: false` on the new entry, distinguishing it from the historic one;
- the entry carries every field the requirement names: `recorded_at`, `run_archive_ref`,
  `repo_commit` (`7a0cce8d2`), `exit_code`, per-stage counters, `findings_count`,
  `combined_report_digest`;
- **idempotence proven twice**: `publish` (stage 18) and a re-run of `combine` (stage 16a)
  each left the ledger byte-identical, both reporting "ein Eintrag je Lauf". A run cannot be
  double-recorded.
- The `DEC-0043-001` boundary holds: raw combined reports stayed under git-ignored
  `output/`, pinned into the ledger only by digest.

## RQ-BR-04 — report staleness mechanically impossible to miss (Task `0043-04`)

**Disposition: SATISFIED, and this is the strongest evidence in the Task.**

Both closed-list firing conditions from bound `B-02` are now proven **live** rather than
hermetically, plus the clearing case — see stage 20's three-way demonstration:

| stage | exit | state |
|---|---|---|
| 15 | 1 | condition **(b)** `unrecorded-publication-run` **fires** — complete cohort, no ledger entry |
| 17 | 1 | condition **(a)** `stale-build-report` **fires** — ledger newer than the page binding |
| 20 | 0 | both satisfied — gate **clears** |

The three states are mutually exclusive and each arose from the tree's real state:
appending the ledger entry ended (b) and created (a); binding the page ended (a).

**`F-TOM-BAXTER-003`, the Auflage `0043-04`'s acceptance placed on this Task, is
discharged** by stage 15. Condition (a)'s live proof (stage 17) was not required by the
Auflage and is delivered additionally.

**The second Auflage** — the task-foreign `process.html` deadlink — is also resolved, but
**not by repair**: the target `TODO-perplexity-0037-37-20260816-1443.md` is still absent and
untracked; `process.html` simply no longer references it (0 occurrences) after regeneration
from current sources. Stated explicitly so a green `validate` is never mistaken for the
missing file having returned.

The third firing condition `malformed-build-ledger`, admitted into scope at `0043-04`'s
review, was **not** exercised by this run: no malformed entry occurred and none was
manufactured. Its coverage remains `0043-04`'s hermetic tests (`test_report_freshness`
19/19). Named here as a known limit rather than left for the reviewer to notice.

## RQ-BR-05 / RQ-BR-06 — uniform report-page header, visible freshness, S-Core campaign (Task `0043-05`)

**Disposition: SATISFIED for this run's scope; carried forward unchanged, with one limit
restated.**

- The `0043-05` header survives regeneration: `build-reports.html` was rebuilt twice in this
  run (stages 18/19) through the generators and full `validate.py` is green (stage 20) with
  all internal links and anchors valid across `de` + 10 language trees.
- Visible freshness is now genuinely *fresh* rather than merely *present*: the page's
  provenance binds this run, timestamped 2026-08-24T11:29:43Z, replacing the frozen
  2026-08-21 binding that stage 17 caught.
- **Restated limit, not newly discovered:** `Harry-Neelix`'s completion note records that
  `0019-06` (S-Core campaign evidence) is *visible* but **not linked**, for want of a
  same-tree HTML target, and that all five pages are deliberately `nolang`. This run neither
  changed nor improved that, and it is outside `0043-07`'s scope. Repeated here because a
  reviewer checking `RQ-BR-06` ("S-Core campaign reachable from the report landscape")
  should see the qualification at the point of disposition.

## RQ-BR-07 — ASPICE evidence map (Task `0043-06`)

**Disposition: SATISFIED, documentation-only; unaffected by this run and deliberately not
extended.**

`docs/pipeline/aspice-report-evidence-map.md` exists, is linked from
`docs/pipeline/README.md`, and makes no capability-level claim (the `0011-03`/`0019-10`
wording constraint). This run touched no `docs/pipeline/` file.

**One honest observation handed to the reviewer, deliberately not acted on:** the map states
as a known gap that raw combined reports and run-archive logs remain git-ignored by design
under `DEC-0043-001` and are therefore not themselves configuration-managed. This run is a
concrete instance — `combined_report_ref` `output/build-reports/combined-1787570983.json` is
pinned in the permanent ledger by SHA-256 but the file itself is not tracked and is not
recoverable from the repository. That is the documented, intended `DEC-0043-001` boundary
working as decided, **not** a defect found here, and changing it would be a decision above
this Task's authority. Recorded so the reviewer sees the trade-off exercised in the real
data rather than only described in prose.

---

## Summary

| requirement | task | disposition |
|---|---|---|
| `RQ-BR-01` | `0043-03` | satisfied — first real multi-row history |
| `RQ-BR-02` | `0043-01` | satisfied — 4/4 stages, one shared non-null ref |
| `RQ-BR-03` | `0043-02` | satisfied — first real entry; append-only + idempotence proven live |
| `RQ-BR-04` | `0043-04` | satisfied — both firing conditions **and** the clearing case proven live; `F-TOM-BAXTER-003` discharged |
| `RQ-BR-05` | `0043-05` | satisfied — header survives regeneration; freshness now real |
| `RQ-BR-06` | `0043-05` | satisfied with restated limit — `0019-06` visible, not linked |
| `RQ-BR-07` | `0043-06` | satisfied — documentation unaffected; `DEC-0043-001` trade-off observed live |

**Known limits actively surfaced:** the `malformed-build-ledger` firing condition is not
live-exercised; `0019-06` remains unlinked; git-ignored combined reports are pinned by digest
but not recoverable; the run's own `overall_success` is `false` for 107 task-foreign
translation-merge rejections (`F-TOM-ADEYEMI-001`); and this session recorded two
measurement defects of its own (`F-TOM-ADEYEMI-002`, stages 16a and 19).
