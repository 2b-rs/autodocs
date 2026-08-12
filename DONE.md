# DONE — Completed Features

Completed *Features* moved here from `TODO.md` once all of their *Tasks* are
marked `[x]`. Each entry keeps its original task text and completion
evidence; a completion date and `REF:` (git hash) are added at move time.

## Feature: Performance

Completed: 2026-08-12 15:27 CEST — REF: 1723c02b

- [x] benchmark, optimize and parallelize generate.py, validate.py, and lib_docmodel.py — 2026-08-12: `generate.py` parallelizes the German page workload using `ProcessPoolExecutor`, explicit macOS `fork` context, batched `map(..., chunksize=...)`, and `WORKERS=min(12, cpu_count)`; small targeted builds stay sequential to avoid pool overhead. `validate.py` parallelizes both German `check_build()` page validation and the dominant language-tree workload across all independent languages. `lib_docmodel.py` remains the pure worker-level renderer; no shared cache was added because separate processes cannot benefit from one and most records are read once per page. Verified by run.sh #253/#254: generate.py dropped from 11.14s to 1.49s for 424 pages (7.5x), with byte-identical output (`generate.py --check`: Abweichungen 0); validate.py dropped from 44.07s to 12.98s (3.4x), with user+sys CPU 33.55s exceeding 12.98s wall time, confirming Python-level multi-core execution. Validation findings remain unchanged: 3811 namespace-less records, tracked separately below.
- [x] optimize and parallelize extraction_report.py (single ProcessPoolExecutor pass over PDFs for all 4 categories, ThreadPoolExecutor for pdftoppm screenshots, WORKERS=min(12, cpu_count) per AGENTS.md job-level parallelism guidance) — 2026-08-12, verified via run.sh (#250) exit 0, 355 deviations reproduced identically to the pre-optimization baseline
- [x] fix run.sh incident from 2026-08-12: extraction_report.py build only writes page-model JSON, never publishes HTML; run.sh must always chain `build && python3 _src/generate.py`. Also made record_version() versions-neutral for unchanged republish runs to avoid duplicate versions (v0012/v0013 dedup incident). Docs updated: _src/WARTUNG.md ("Extraktions-Berichte: Bauen vs. Publizieren") and docs/pipeline/reports.md.
