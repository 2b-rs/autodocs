TODO-perplexity.md — working copy for AGENT PERPLEXITY

Enclosing feature

## Feature: 0034 — Requirement Field Extraction: Wrapped Label Handling

Feature scope (as recorded in TODO.md): defects in requirement-field extraction in `spec_scrape.py` and in benchmark record selection in `_src/tools/spec_extraction_benchmark.py`. Tasks in the feature: 0034-01 (wrapped multi-line label handling), 0034-02 (`_record_slice()` definition-anchor detection when the opening marker precedes the `[ID]` line), 0034-03 (completed), 0034-04 (exclude citation-only ID mentions from benchmark record selection).

Feature status: NOT complete. 0034-01, 0034-02, 0034-04 remain open, so the feature does NOT move to DONE.md.

Completed task bookkeeping correction

- [x] **0034-03** remains complete, but its `REF` in `TODO.md` required a follow-up correction.
  - Initial closeout commit sequence produced an unavoidable self-reference issue: the implementation commit hash was written into `TODO.md`, then the commit was amended to include that bookkeeping line, which necessarily changed `HEAD`.
  - Corrective action requested by user on 2026-08-15: update the `REF` in `TODO.md` from the orphaned pre-amend object `d596af8a8efbdb006dc2a3e096d33d80a4d0e7b8` to the actual committed object `7b2b572ab18ecab29e7e6fd9704b9b85e7b806ab`, then commit that correction before starting new work.

Next pickup

- [p] **0034-02** intended next pickup after the REF correction commit.
  - Why this task next: self-contained, no prerequisite on unfinished work, and reconnaissance already captured `_record_slice()` plus the persisted evidence that the lookahead misses opening markers emitted immediately before the `[ID]` line.
  - Planned first action: a read-only `run.sh` to capture the exact current `_record_slice()` implementation, enumerate definition-vs-citation occurrences for the failing ID(s), locate existing tests that cover `_record_slice()` / heading fallback behavior, and establish a targeted baseline before editing.

Merge-back discrepancy check (required by SANDBOX.md)

- Re-compared Feature 0034 in `TODO.md` after the 0034-03 closeout. No sibling task removed, no material feature-description drift, no new prerequisites added. NO BLOCKER.

Progress log

- 2026-08-15: 0034-03 completed and committed as `7b2b572ab18ecab29e7e6fd9704b9b85e7b806ab`, but TODO carried the pre-amend implementation hash. User requested explicit correction before continuing.
- 2026-08-15: Corrected `TODO.md` REF in working tree; commit pending.
- 2026-08-15: 0034-02 marked as intended next pickup here; TODO.md update + commit pending.
