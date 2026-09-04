TODO-perplexity.md — working copy for AGENT PERPLEXITY

Enclosing feature

## Feature: 0034 — Requirement Field Extraction: Wrapped Label Handling

Feature scope (as recorded in TODO.md): defects in requirement-field extraction in `spec_scrape.py` and in benchmark record selection in `_src/tools/spec_extraction_benchmark.py`. Tasks in the feature: 0034-01 (wrapped multi-line label handling), 0034-02 (now closed `[w]`), 0034-03 (completed), 0034-04 (citation-only benchmark selection bug; still open).

Feature status: NOT complete. 0034-01 and 0034-04 remain open, so the feature does NOT move to DONE.md.

Status-model update

- Added a new task state `[w]` to the TODO.md header.
  - Meaning: investigated and closed without code changes because the reported issue is invalid as written, no longer reproducible, superseded, or otherwise not worth fixing.
  - Lifecycle semantics: `[w]` is terminal and is treated like `[x]` for dependency / feature-completion purposes.
  - Required evidence: a `[w]` task must carry a `Reason:` bullet, and the closing disposition commit must add `REF: <hash>`.
- `SANDBOX.md` intentionally left unchanged. It is not wrong; it simply does not define every TODO marker. The authoritative marker definitions live in the TODO.md header.

0034-02 disposition

- [w] **0034-02** — non-reproducible as written; close without code changes.
  - Why: the named motivating example `RS_OSI_00209` already parses correctly in the current repository state. Its real definition occurrence has `⌈` 99 characters after the `[ID]`, which is inside `_record_slice()`'s existing 240-character lookahead. `parse_record()` returns the correct heading and populated `Description`, `Rationale`, `Dependencies`, and `Use Case` fields.
  - Corpus probe result: the five apparent “pre-ID marker” candidates are all citation-only mentions of external `SWS_CORE_*` IDs inside `AUTOSAR_AP_RS_General.pdf`, not local definitions whose anchors are being missed.
  - Conclusion: no reproducible `_record_slice()` definition-anchor bug of the form described by 0034-02 exists on the current codebase.
  - Scope transfer: the real concern surfaced by the probe is citation-only ID handling, which belongs to 0034-04 and is explicitly cross-referenced there.
  - Evidence: `logs/source-reconnaissance/20260815-215209/` and `logs/source-reconnaissance/20260815-215652/`.

0034-04 note

- Added a cross-reference under **0034-04** stating that 0034-02 was investigated and closed `[w]`, and that the citation-only concern belongs to 0034-04 and is absorbed by it.
- 0034-04 remains open. No implementation work has started yet in this bookkeeping step.

Next intended pickup

- **0034-04** is now the natural next task inside Feature 0034, because it owns the real citation-only selection defect surfaced during the 0034-02 investigation.

Merge-back discrepancy check (required by SANDBOX.md)

- Re-compared Feature 0034 before editing task state. No sibling task removed, no material feature-description drift, no new prerequisites added. NO BLOCKER.

Progress log

- 2026-08-15: 0034-03 completed and committed as `7b2b572ab18ecab29e7e6fd9704b9b85e7b806ab`; REF later corrected by `723b485d675ea57a104f05dd10ed84af75548b05`.
- 2026-08-15: 0034-02 pickup bookkeeping committed as `991c11a4810ed91f3fca00dac5501f0ec0451f12`.
- 2026-08-15: Reconnaissance established that 0034-02 does not reproduce as written and that the real concern is citation-only ID handling.
- 2026-08-15: Prepared bookkeeping to introduce `[w]`, close 0034-02 as wontfix with a required `Reason:`, and cross-reference/absorb the concern into 0034-04; commit pending.
