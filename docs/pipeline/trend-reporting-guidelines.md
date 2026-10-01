# Trend Reporting & Collection Architecture (Feature 0017-06)

## Purpose
This document establishes the architecture for the trustworthy, correlated collection of project metrics and the generation of trend reports (MAN.6). It defines rules to prevent incomparable processes or missing phases from inflating success metrics.

## 1. Trustworthy Collection
- **Automated Ingestion:** All metrics (e.g., test pass rates, defect density, code coverage, review cycle times) must be extracted automatically from the Immutable Evidence Repository (Feature 0015-06).
- **Correlation:** Metrics must be tied to a specific Release Baseline or Campaign ID. Time-series data must correlate across these IDs to prevent comparing "apples to oranges" (e.g., comparing a partial unit-test run to a full integration-test suite).

## 2. Completeness & Data-Quality Flags
- **Completeness Gates:** A data point is only considered valid if all prerequisite lifecycle stages (requirements, design, tests, reviews) are marked as complete for that baseline.
- **Data-Quality Flags:** If a baseline is missing a stage (e.g., performance tests were skipped) or if an evidence bundle is incomplete, the trend reporting engine must append a `<DataQualityWarning>` flag to that metric.
- **Strict Mode:** By default, incomplete data points must not be aggregated into success metrics (e.g., an incomplete QA run does not count toward a 100% pass rate). They must be highlighted as "Insufficient Data".

## 3. Trend Reporting
- **Dashboards:** Trend reports should visualize at least:
  - Defect arrival and closure rates.
  - Test coverage trends across baselines.
  - Traceability gap trends over time.
- **Immutability:** The generated trend report for a specific period or baseline must be archived as an immutable artifact in the configuration management system (SUP.8).
