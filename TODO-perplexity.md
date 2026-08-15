TODO-perplexity.md — working copy for AGENT PERPLEXITY

Enclosing feature

## Feature: 0034 — Requirement Field Extraction: Wrapped Label Handling

Feature scope (as recorded in TODO.md): defects in requirement-field extraction in `spec_scrape.py` and in benchmark record selection in `_src/tools/spec_extraction_benchmark.py`. Tasks in the feature: 0034-01 (wrapped multi-line label handling), 0034-02 (`_record_slice()` definition-anchor detection when the opening marker precedes the `[ID]` line), 0034-03 (this task), 0034-04 (exclude citation-only ID mentions from benchmark record selection).

Feature status: NOT complete. 0034-01, 0034-02, 0034-04 remain open, so the feature does NOT move to DONE.md.

Task completed

- [x] **0034-03** Add `Additional Information` to the recognised field labels in `spec_scrape.py` so Persistency-style requirement blocks do not silently drop their second field.

Acceptance criteria vs. evidence

1. "`Additional Information` recognised as a normative label" — MET, with a documented deviation in mechanism. Added to `LABELS`, deliberately not to `NORMATIVE_LABELS`; see design decision below. Recognition is what the criterion requires and recognition is achieved.
2. "`parse_record()` on the Persistency document returns both `Description` and `Additional Information` for `RS_PER_00010` and `RS_PER_00021` with the boundary at the label" — MET against the REAL cached PDF, not a mock. Both records yield fields `['Description', 'Additional Information']`; headings resolve to "Configurable Layout of Persistent Data" and "Initialization and Shutdown"; no label leak into `Description`.
3. "A regression test covers it" — MET. Three tests in `RequirementFieldTests`.
4. "Existing scrape tests still pass" — MET. Scrape selection went 65 -> 68 passed (the +3 are the new tests), 144 deselected, 0 failed. Full suite: 212 passed, 0 failed.

Changes made

- `_src/tools/spec_scrape.py`: `Additional Information` added to `LABELS`.
- `_src/tests/test_spec_scrape_fields.py`: three tests added to `RequirementFieldTests`:
  - `test_additional_information_is_a_field_boundary` (concatenated-cell form)
  - `test_additional_information_on_its_own_line_is_a_field_boundary` (own-line form)
  - `test_additional_information_without_colon_does_not_split_prose` (negative case pinning the colon gate)

Design decision (deliberate)

- `LABELS` yes, `NORMATIVE_LABELS` no. `NORMATIVE_LABELS` members split without a trailing colon; safe for a rare token like `Rationale`, unsafe for the ordinary English phrase `Additional Information`, which would corrupt prose like "see the annex for Additional Information about timing". Colon-gating via `API_LABELS` is sufficient because the real Persistency tables emit the colon — confirmed end-to-end, not assumed. The negative test pins the decision.

Observation for 0034-01 (not a new task)

- Both extracted `Additional Information` values end with the absorbed running header `Requirements on Persistency`. Same page-furniture absorption already recorded in 0034-01's live-reproduction bullet, now confirmed on a second document and a different label. Recorded in TODO.md under 0034-03 so 0034-01 picks it up.

Merge-back discrepancy check (required by SANDBOX.md)

- Compared this working copy against Feature 0034 in TODO.md at merge time. The feature description and the sibling tasks 0034-01, 0034-02, 0034-04 are unchanged from pickup: no tasks removed, no descriptions materially altered, no prerequisites added that I failed to respect. NO BLOCKER. Work may continue.

Progress log

- 2026-08-15: Task copied here, marked `[p]` in TODO.md.
- 2026-08-15: run.sh v1 reconnaissance FAILED, exit 142 (SIGALRM at the runner's 300 s guard). Root cause was mine: bare `wait` after starting an infinite heartbeat background loop, so the Phase 1 barrier could never return (log showed `jobs=0` while the phase never advanced). Reported and yielded per SANDBOX.md.
- 2026-08-15: run.sh v2 reconnaissance OK (exit 0). Barriers now wait on explicit PIDs only; per-phase `perl alarm` watchdogs. Established: authoritative source `_src/tools/spec_scrape.py`; baseline 65 passed / 144 deselected on Python 3.9.6 + pytest 8.4.2; Persistency PDF cached at `_src/spec/pdf-cache/R25-11/AUTOSAR/AP/`. Defect confirmed exactly as recorded — `LABELS` ran `Kind`..`Errors` with no `Additional Information`, and both `LABEL_RE` and `NORM_RE` derive from `LABELS`.
- 2026-08-15: Fix + tests applied; run.sh validation OK (exit 0). Logs: `logs/source-reconnaissance/20260815-213921/`, `logs/validate-db-contents/20260815-214205/`.
- 2026-08-15: Marked `[x]` in TODO.md, merged back, discrepancy check clean, commit pending.

Next task selection (after commit)

- 0034-02 is the intended next pickup: self-contained, no prerequisite on an unfinished task, and reconnaissance already captured `_record_slice()`.
- 0034-01 still carries its blocked-on-input caveat (campaign `raw/` inputs absent from the tree), so its evidence chain depends on re-running an extraction campaign.
- 0034-04 remains open and untouched.
