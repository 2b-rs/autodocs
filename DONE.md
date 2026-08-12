# DONE — Completed Features

Completed *Features* moved here from `TODO.md` once all of their *Tasks* are
marked `[x]`. Each entry keeps its original task text and completion
evidence; a completion date and `REF:` (git hash) are added at move time.

## Feature: Performance

Completed: 2026-08-12 15:27 CEST — REF: 1723c02b

- [x] benchmark, optimize and parallelize generate.py, validate.py, and lib_docmodel.py — 2026-08-12: `generate.py` parallelizes the German page workload using `ProcessPoolExecutor`, explicit macOS `fork` context, batched `map(..., chunksize=...)`, and `WORKERS=min(12, cpu_count)`; small targeted builds stay sequential to avoid pool overhead. `validate.py` parallelizes both German `check_build()` page validation and the dominant language-tree workload across all independent languages. `lib_docmodel.py` remains the pure worker-level renderer; no shared cache was added because separate processes cannot benefit from one and most records are read once per page. Verified by run.sh #253/#254: generate.py dropped from 11.14s to 1.49s for 424 pages (7.5x), with byte-identical output (`generate.py --check`: Abweichungen 0); validate.py dropped from 44.07s to 12.98s (3.4x), with user+sys CPU 33.55s exceeding 12.98s wall time, confirming Python-level multi-core execution. Validation findings remain unchanged: 3811 namespace-less records, tracked separately below.
- [x] optimize and parallelize extraction_report.py (single ProcessPoolExecutor pass over PDFs for all 4 categories, ThreadPoolExecutor for pdftoppm screenshots, WORKERS=min(12, cpu_count) per AGENTS.md job-level parallelism guidance) — 2026-08-12, verified via run.sh (#250) exit 0, 355 deviations reproduced identically to the pre-optimization baseline
- [x] fix run.sh incident from 2026-08-12: extraction_report.py build only writes page-model JSON, never publishes HTML; run.sh must always chain `build && python3 _src/generate.py`. Also made record_version() versions-neutral for unchanged republish runs to avoid duplicate versions (v0012/v0013 dedup incident). Docs updated: _src/WARTUNG.md ("Extraktions-Berichte: Bauen vs. Publizieren") and docs/pipeline/reports.md.

## Feature: Document Coverage

Completed: 2026-08-12 15:31 CEST — REF: 83a2c2da

- [x] investigate possible missing AUTOSAR Safety RS document — resolved 2026-08-12: the authoritative source is `AUTOSAR_FO_RS_Safety.pdf` (Foundation branch, requirements document). Earlier assumption that `AUTOSAR_FO_EXP_SafetyOverview.pdf` defines the `RS_SAF_*` records was wrong; that EXP document only references Safety requirements inline. `rs-saf` is now registered in `RS_DOCS` (`spec_scrape.py`) against `AUTOSAR_FO_RS_Safety`; the PDF still needs to be downloaded into `AUTOSAR/FOUNDATION/` and then re-run through `spec_scrape.py`. Also flagged: `AUTOSAR_AP_RS_HWTestManager`, `AUTOSAR_AP_SWS_OperatingSystemInterface`, `AUTOSAR_FO_PRS_IntrusionDetectionSystem`, `AUTOSAR_FO_PRS_TimeSyncOverEthernetProtocol` are cached but not yet registered in `DOCS`/`RS_DOCS`; also `RS_SOMEIP` has orphaned traceability records with no registered source document yet — needs the same treatment.


## Feature: Review & Feedback / Level 1 — Make Review Need Visible

Completed: 2026-08-12 15:31 CEST — REF: 83a2c2da


- [x] Open review need is visible at the top of the page as a notice
- [x] Notice states the number of affected API elements
- [x] Notice links via intra-page link directly to the
