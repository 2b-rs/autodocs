# Task 0039-05: Machine-Enforced Task and Feature Acceptance Policy

## Summary

Task `0039-05` provides machine-enforced validation for the privileged Task Acceptance and Feature Closure conventions defined in `docs/pipeline/task-acceptance.md`.

## Deliverables

1. **`_src/tools/task_acceptance_policy.py`**:
   - `expand_batch(tasks, assigned, accepted)`: Deterministic, topologically sorted expansion of induced prerequisite-closed review batches from leaves to target checkpoints. Detects cycles, missing endpoints, and unassigned predecessor checkpoints fail-closed.
   - `validate_feature_acceptance(feature_tasks, terminal_integrating_task)`: Ensures complete reachability and graph coverage from all feature tasks to the terminal integrating task prior to closure.

2. **Fixtures & Tests (`_src/tests/fixtures/task_acceptance_policy/cases.json`, `_src/tests/test_task_acceptance_policy.py`)**:
   - Verifies graph expansion against linear, branching, accepted-boundary, wontfix, unassigned-checkpoint, missing-endpoint, and cycle cases.
   - Verifies required semantic case inventory (blocking findings, unauthorized reviews, later-defect successors, missing feature edges, historical invalidations, duplicate acceptances, and feature closures).

3. **Catalog Entry (`docs/pipeline/tools.md`)**:
   - Cataloged `task_acceptance_policy.py`.

## Validation

All unit tests pass (4/4 in `test_task_acceptance_policy.py`), fully compatible with `legacy_task_doctor.py` and `legacy_task_editor.py`.
