# MAN.6 Measurement Specification (0017-05)

**Status:** Normative
**Version:** 1.0.0
**Reference:** Feature 0017-05 (Prerequisite `0017-04`)

This document specifies the concrete operational definitions, collection methods, and usage parameters for the metrics identified in `docs/pipeline/man6-measurement-metrics.md`.

## 1. Quality & Outcome Metrics

### 1.1 M-QUAL-01: Review Closure Rate
- **Definition**: The percentage of pull requests, commits, and formal architectural decisions (`DEC-*`) that reach closure with an explicit `Acceptance: ✓` marker.
- **Unit**: Percentage (0-100%).
- **Source**: `git log` commit messages and `TODO.md` history.
- **Owner**: QA / Integrator.
- **Collection Method**: Automated scrape of `main` branch commit messages and `TODO.md` claims looking for `Acceptance: ✓`.
- **Baseline**: 0%.
- **Target/Threshold**: Target = 100%. Threshold = 100% (No unreviewed code is allowed in `main`).
- **Cadence**: Per Integration run.
- **Analysis/Presentation**: Tabular report generated per campaign milestone.
- **Retention**: Retained in Git history permanently.
- **Decision Use**: Used as a hard gate for SPL.2 Release Readiness.

### 1.2 M-QUAL-02: Test Pass Rate
- **Definition**: The ratio of passing unit/integration tests to total executed tests per CI run.
- **Unit**: Percentage (0-100%).
- **Source**: `pytest` XML reports or equivalent test runner output.
- **Owner**: Integrator.
- **Collection Method**: Automated parser of test runner outputs.
- **Baseline**: N/A (Dynamic per test suite size).
- **Target/Threshold**: Target = 100%. Threshold = 100%.
- **Cadence**: Every commit to any branch.
- **Analysis/Presentation**: Test dashboard / Markdown summary injected into PRs.
- **Retention**: Latest per branch; permanently for `main`.
- **Decision Use**: Merge gate to `main`.

### 1.3 M-QUAL-03: Fallback/Reject Count
- **Definition**: Number of times an item is sent back to `REWORK` due to failing the Four-Eyes review.
- **Unit**: Integer count.
- **Source**: Mailbox thread states (Agent-inbox) and `TODO.md` status changes.
- **Owner**: Project Lead.
- **Collection Method**: Scrape `agent-inbox` logs for `REWORK` decisions.
- **Baseline**: 0.
- **Target/Threshold**: Target < 3 per item. Threshold > 5 triggers root-cause analysis.
- **Cadence**: Weekly.
- **Analysis/Presentation**: Scatter plot of rework counts vs. item complexity.
- **Retention**: Archive logs per campaign.
- **Decision Use**: Identify competency gaps or ambiguous requirements.

## 2. Effort & Schedule Predictability

### 2.1 M-SCH-01: Effort Variance
- **Definition**: Deviation between estimated effort and actual elapsed time.
- **Unit**: Percentage variance.
- **Source**: Estimated vs. actual time recorded in `TODO.md` (or inferred by `in_progress` to `DONE` timestamps).
- **Owner**: Project Lead.
- **Collection Method**: Automated parsing of `TODO.md` state transitions.
- **Baseline**: 0%.
- **Target/Threshold**: +/- 20% variance acceptable.
- **Cadence**: End of sprint/campaign.
- **Analysis/Presentation**: Burndown/burnup velocity charts.
- **Retention**: End of project lifecycle.
- **Decision Use**: Adjusting future sprint capacities.

## 3. Resource & Infrastructure Health

### 3.1 M-RES-01: Provider Quota Usage
- **Definition**: Consumption of LLM API tokens.
- **Unit**: Tokens (Input/Output).
- **Source**: Provider API dashboards.
- **Owner**: Tooling Administrator.
- **Collection Method**: Daily export from API platform.
- **Baseline**: 0.
- **Target/Threshold**: 80% of daily hard limit.
- **Cadence**: Daily.
- **Analysis/Presentation**: Line chart tracking cumulative daily usage.
- **Retention**: 90 days.
- **Decision Use**: Triggers pause on non-critical background jobs if threshold is breached.

## 4. Traceability & Coverage

### 4.1 M-TRC-01: Requirement Coverage
- **Definition**: Percentage of SWE.1 requirements linked to SWE.2 architectural elements and SWE.6 tests.
- **Unit**: Percentage (0-100%).
- **Source**: Traceability matrix generated from `req-*.md` and `dec-*.md` linkages.
- **Owner**: Requirements Engineer / Architect.
- **Collection Method**: Automated trace script (`trace_matrix.py`).
- **Baseline**: 0%.
- **Target/Threshold**: 100%.
- **Cadence**: Nightly.
- **Analysis/Presentation**: Matrix artifact `docs/pipeline/traceability-matrix.md`.
- **Retention**: Persistent in `main`.
- **Decision Use**: Identifies orphan requirements before QA testing.

## 5. Defect & Change Management

### 5.1 M-DEF-02: Defect Aging
- **Definition**: Average time from SUP.9 issue opening to validated closure.
- **Unit**: Days.
- **Source**: Issue tracker or `TODO.md` defect items.
- **Owner**: Integrator.
- **Collection Method**: Script tracking timestamp of `OPEN` vs `DONE` state for defect tags.
- **Baseline**: 0 days.
- **Target/Threshold**: Target < 5 days. Threshold > 14 days triggers escalation.
- **Cadence**: Weekly.
- **Analysis/Presentation**: Histogram of defect ages.
- **Retention**: Retained in defect logs.
- **Decision Use**: Escalation of stale blocking defects.

## 6. Release & Delivery Health

### 6.1 M-REL-01: Known Issues Ratio
- **Definition**: Count of open/accepted limitations packaged into the SPL.2 release manifest.
- **Unit**: Integer count.
- **Source**: Release Notes / `spl2-release-manifest.md`.
- **Owner**: Release Manager.
- **Collection Method**: Manual count extraction during release prep.
- **Baseline**: 0.
- **Target/Threshold**: Target = 0. Threshold > 5 requires customer waiver.
- **Cadence**: Per Release Candidate.
- **Analysis/Presentation**: Table in Release Notes.
- **Retention**: Permanent per release baseline.
- **Decision Use**: Go/No-Go decision for release authorization.
