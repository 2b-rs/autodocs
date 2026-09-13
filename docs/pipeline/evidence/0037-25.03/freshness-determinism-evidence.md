# Subtask 0037-25.03: Freshness, Determinism, Manifest, and Unexplained-Diff Validation Evidence

## Overview

Subtask `0037-25.03` validates freshness checking, byte and semantic determinism, manifest generation, and unexplained-diff detection in `_src/tools/issue_regenerate.py`.

## Criteria Verification

- **AC-001 (Digest Recomputation):**
  - Source (`issues/`, `provenance/`), schema, tool, and config artifact digests are recomputed during DAG execution and embedded in the content-addressed run manifests and generated views.

- **AC-002 (Stage Comparators & Determinism):**
  - Staging applies declared deterministic byte and canonical JSON comparators across all pipeline stages (`_stage_validate`, `_stage_internal`, `_stage_public`, `_stage_graphs`, `_stage_pages`, `_stage_html`, `_stage_report`).
  - Repeated clean runs yield identical content-addressed tree manifests (`tree_manifest`).

- **AC-003 (Negative Detection & Mutation Guards):**
  - Fails with `STALE` / error on missing, stale, hand-edited output, undeclared files (`IR1027`), unexplained existing output (`IR1028`), or unauthorized mutation of canonical sources (`IR1026`).

- **AC-004 (External Run Reports):**
  - Run and stage validation reports are returned as distinct structured result payloads (`issue-regeneration-result@v1`) and never written self-referentially into the candidate trees they validate.

## Validation

Verified via full test suite in `_src/tests/test_issue_regenerate.py` (35/35 passing).
