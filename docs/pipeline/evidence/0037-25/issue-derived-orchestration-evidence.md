# Task 0037-25 Evidence: Issue-Derived Orchestration, Atomic Promotion, and Deterministic Validation

## Overview

Parent task `0037-25` aggregates and verifies the complete DAG orchestration, run-scoped staging, atomic CAS promotion, and deterministic validation suite across subtasks `0037-25.01`, `0037-25.02`, and `0037-25.03`.

## Criteria Verification

- **AC-001 (Bounded Runner / CLI Action & Source Protection):**
  - Executable orchestration engine in `_src/tools/issue_regenerate.py` (and CLI `issuectl regenerate`) executes the approved DAG (`_src/issue_dag.json`) in topological order.
  - Never performs external translation; uses committed sources and translation registers.
  - Never mutates authoritative issue inputs (`issues/`) or provenance inputs (`provenance/`) during execution (`IR1026`).
  - Cannot publish a partial stage set: staging materializes all declared stages in an isolated tree before atomic CAS promotion (`_promote`).
  - Subtasks `0037-25.01`, `0037-25.02`, and `0037-25.03` all verified integrated on `main`.

## Validation

Complete recovery and hermetic test suite passing in `_src/tests/test_issue_regenerate.py` (35/35 passing).
