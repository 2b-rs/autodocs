---
schema_version: "1.0"
id: "0034-01"
level: "task"
parent: "0034"
state: "open"
visibility: "internal"
prerequisites:
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2592"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

Fix `spec_scrape.py` requirement-field parsing so field labels that the PDF wraps across two physical lines (e.g. `Supporting` / `Material:`) are recognized as labels instead of being appended to the preceding field's value. REF: `f3bc0f30e`.

## Scope

- **Discovery (2026-08-15, found while working 0007-01):** Field parsing in `_src/tools/spec_scrape.py` iterates the requirement chunk line by line and tests each line against `LABEL_RE` (`^(label)\s*:?\s*(.*)$`); any non-matching line is appended to the current field buffer. AUTOSAR RS PDFs routinely render the two-word label `Supporting Material:` as `Supporting` on one line and `Material:` on the next, so neither line matches, both tokens are swallowed into the previous field, and the actual `Supporting Material` value (frequently just an en dash) is lost entirely.
  - **Blast radius:** 146 of the 191 still-unreviewed records in `_src/tests/fixtures/spec_extraction/benchmark-draft.json` exhibit the corruption — trailing `Supporting Material` bleeding into `Use Case` (121), `Dependencies` (22), and `AppliesTo` (3). This is an extractor defect, so it affects any consumer of scraped requirement props, not only the benchmark fixture. Confirmed by hand against source PDFs for `RS_AP_00111` (General p.10), `RS_OSI_00100` (OperatingSystemInterface p.10), `RS_PHM_00101` (PlatformHealthManagement p.10), `RS_SHWA_00001` (SafeHardwareAcceleration p.7), and `RS_SM_00001` (StateManagement p.8).
  - **Note:** `_src/tools/spec_extraction_benchmark.py` is NOT the culprit; it copies `record["props"]` verbatim into `expected.fields`. Fix belongs in the scraper.
  - **Live reproduction (2026-08-15):** Confirmed still present in current `spec_scrape.py`. Calling `parse_record()` on freshly extracted PDF text yields `props` keys `['Description','Rationale','Dependencies','Use Case']` with **no** `Supporting Material` key at all, and the label text trapped at the tail of `Use Case` — e.g. `RS_SM_00001` → Use Case `'Provide interface to influence State Managements internal states. Supporting Material'`, and `RS_AP_00120` → Use Case `'– --- Page 15 --- General Requirements specific to Adaptive Platform Supporting Material: '`. The latter also shows page-break furniture (page marker + running header) being absorbed, so the fix should strip page markers/running headers during field accumulation as well. A repro is therefore cheap: parse any RS document text and assert a `Supporting Material` key exists.
  - **Resolution (2026-08-17):** `_normalize_wrapped_labels()` rejoins any multi-word `LABELS` entry that extraction split across lines, applied at the top of `normalize_layout()` so all backends see the joined form; it rewrites only matches that actually span a newline, so single-line prose is untouched. `_label_pattern()` makes `LABEL_RE`, `HEADING_LABEL_RE`, and `NORM_RE` whitespace-tolerant within a label, ordered longest-first so no label is shadowed by a shorter prefix of itself. `NOISE_RES` gains `--- Page N ---` markers and the running headers `Requirements on <X>` / `General Requirements specific to Adaptive Platform`, covering criterion 2 and the page-furniture absorption flagged from 0034-03. Five regression tests added (suite 45 -> 50): wrapped `Supporting`/`Material:` with and without colon, the second multi-word label `Forwarding header file`, a negative case where three values legitimately end in "Material", and page-marker/running-header stripping.
  - **Changed expectation (criterion 4, justification):** `_clean_value()` now preserves a value that is exactly an en/em dash or hyphen; `TAIL_RE` previously stripped it to `""`, making a field the document explicitly marked "not applicable" indistinguishable from a field that was never extracted. One existing assertion changed accordingly from `Rationale == ""` to `Rationale == "–"`. The document states the dash; the old empty string was part of the defect.
  - **Validation (2026-08-17):** End-to-end `parse_record()` against the real cached R25-11 corpus for all six records named above — `RS_SM_00001`, `RS_AP_00120`, `RS_AP_00111`, `RS_SHWA_00001`, `RS_OSI_00100`, `RS_PHM_00101` — now returns a `Supporting Material` key for every one. Both recorded live reproductions are resolved: `RS_SM_00001` Use Case is now `'Provide interface to influence State Managements internal states'` with Supporting Material `'–'`, and `RS_AP_00120` Use Case is now `'–'` with Supporting Material carrying its real value (was `'– --- Page 15 --- General Requirements specific to Adaptive Platform Supporting Material: '`). Scraper/extraction suites pass: fields 50, scrape_upstream 10, spec_upstream 6, benchmark 5, campaign 11. Full-suite comparison against a stashed baseline shows `test_automation_safety` (AUTO010 in `_src/tools/runner_transaction.py`) and `test_legacy_task_editor` failing identically with and without the change — pre-existing and unrelated; no suite regressed. Evidence: `logs/validate-db-contents/20260817-225700/`.
  - **Downstream regeneration note (DoD):** `_src/tests/fixtures/spec_extraction/benchmark-draft.json` is stale — 146 of its 191 unreviewed records carry the corruption this fixes — as are any campaign outputs derived from those props. Regeneration remains blocked on input exactly as the caveat above states: the campaign `raw/` inputs are absent, so the extraction campaign must be re-run, not merely the benchmark builder. Not performed here. No generated HTML is affected; the scraper feeds fixtures and campaign data, not the published tree.
  - **Check-in note (2026-08-17):** Code and tests were authored under claim `TODO-perplexity-0034-01-20260816-195100.md` (`agent:perplexity:0034-01:20260816-195100`) but left uncommitted with the marker unadvanced. A later session validated them and checked them in on explicit user direction, without appropriating or altering that claim's `owner_token`; the claim file is retained and carries an appended reconciliation record. Acceptance remains a separate privileged review and has not been granted.

## Acceptance criteria

- **AC-001** Multi-line labels from `LABELS` are joined and matched before value accumulation, without misclassifying prose that merely begins with a label word
- **AC-002** a regression test covers the wrapped `Supporting`/`Material:` case plus at least one wrapped-label case for a different multi-word label and one negative case where a value legitimately ends with the word `Material`
- **AC-003** existing `test_spec_scrape_fields.py` expectations still pass or are updated with recorded justification

## Definition of Done

Fix and tests committed with `REF`; a short note records which downstream artifacts (benchmark draft, any campaign outputs) must be regenerated. Blocked-on-input caveat: the campaign `raw/` inputs (`*.pypdf.json` / `*.builtin.json`) that fed the current benchmark draft are no longer present in the tree, so regenerating the fixture requires re-running the extraction campaign, not merely re-running the benchmark builder.
