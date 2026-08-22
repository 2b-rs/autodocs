# QA Build/Validate Regression Check — 2026-08-22

## Verdict

The repository **builds successfully**, but the full validation remains **red** because of 13 dead internal links. The current and comparison runs produced the same 13 findings byte-for-byte, so no validation regression was introduced between the post-recovery baseline and the tested current main state.

## Pinned states and environment

- Tested current state: `478a89e7c2a4052fbd3bff8d81da932d94924896`
- Comparison baseline: `f9c8050ff2b367be7fe7c4eefe24b83a178f950c` (immediately after recovery commit `27930dc9c` and bytecode cleanup)
- Scratch environment: Python 3.9 virtualenv with system-site packages, `lxml 6.1.1`, `pytest 8.4.2`
- Commands, in each isolated disposable worktree: `python _src/generate.py` followed by `python _src/validate.py`
- After the runs, `main` advanced to `388018fdd412c6d6059b41e8d89b37871c8a2a9f`. The sole intervening path is `docs/campaign-evidence/eclipse-score-v0.6.0-closure-candidate/release-authorization-20260822.md`; it is outside the generator/validator inputs, so it does not invalidate this build comparison.

## Results

| Run | Generate | Pages | Generate duration | Validate | Checks | Findings | Validate duration |
|---|---:|---:|---:|---:|---:|---:|---:|
| Current `478a89e7c` | exit 0 | 428 | 116.703 s | exit 1 | 11 | 13 dead links | 242.500 s |
| Baseline `f9c8050ff` | exit 0 | 428 | 33.921 s | exit 1 | 11 | 13 dead links | 299.829 s |

The generated CLI logs are identical (`SHA-256 ca01d4d9244baf65e1ae89840d7d19456884e6e069df1092cb41396853e946f6`). The validation CLI logs are also identical (`SHA-256 35e6b1498fe9dd856f017eb689e94c9fe541c921a151e5a9b0a3cf9a7821b494`).

## Findings present in both states

- Six missing retained log targets linked from `curation-report.html` under `_src/logs/validate-review-request-ui/20260815-154824/`: `phase0-env.log`, `phase1-syntax.log`, and four `phase2-test_review_request_*.log` files.
- The same six missing retained log targets linked from `open-reviews.html`.
- One missing claim target linked from `process.html`: `TODO-perplexity-0037-37-20260816-1443.md`.

These are genuine validation failures and remain open; this report only establishes that they predate the tested current state and were not introduced by the intervening commits.

## Evidence

Full ephemeral run artifacts were retained at `/private/tmp/autodocs-qa-harry-logs-20260822T110000Z` and in each disposable worktree's `output/build-reports/` directory for the duration of this session. Structured report digests:

- Current generate: `d80a80d0d99e433fb82cc45dcf98ee932342067d36539e00716fe37187a2367d`
- Current validate: `2a09a444d870f2043d775d3ff698d84582ce5b159302e36649271ca22ad47960`
- Baseline generate: `1e3911dd5375aa551b864daf0c92c19b274f78b9b7274522c08a5282bbb16804`
- Baseline validate: `e3345356ba739b03f2cfea089db39b8911b926a625a98249037bcf481f6e037d`

