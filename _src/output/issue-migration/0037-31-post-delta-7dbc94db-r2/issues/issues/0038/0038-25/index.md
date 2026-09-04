---
schema_version: "1.0"
id: "0038-25"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0038-18"
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1642"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0038-25:0038-18 Make the `verify-and-commit-v1` profile fail closed when bookkeeping is omitted. REF: `2f9c82af5aaeeaef8654bea56accefd04983fb5c`. Claim: `TODO-terra-1-0038-25-20260819T000000Z.md`; owner_token: `agent:terra-1:0038-25:20260819T000000Z`.

## Scope

- **Merge note (0041, 2026-08-21):** Branch `0041`'s `DEC-0041-005` supersession gate on this Task was overtaken by `main`'s independent closure (REF `2f9c82af5`) before this merge; the gate never blocked anything real and is retained here only as provenance.
  - **Defect (2026-08-18, found while auditing `0038-18`):** `_src/tools/runner_transaction.py:522` requires a substantive `commit` object for **both** profiles, but `:524` requires a `bookkeeping` object **only** for `close-task-v1`. Finalization at `:1774` likewise demands a bookkeeping commit only `if has_bookkeeping`. A manifest that simply omits the `bookkeeping` key therefore produces a green `verify-and-commit-v1` transaction that publishes the deliverable and never advances the marker — exactly the outcome observed on `0038-18`, whose own closure used the profile whose guard it had just weakened.
  - **Acceptance criteria (working-tree synchronization):** After a successful transaction the working tree matches the published commit for every declared output path, or the transaction fails and says so. The `0038-18` publication advanced `main` while leaving the working tree at the previous state, which is a silent revert hazard for the next writer.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** the Task tightens an existing guard and adds tests; it grants no new capability and removes none. Its effect is objectively checkable by the negative fixture, and it is re-examined whenever `0038` reaches its integrating task. **Trigger correction (2026-08-21, architect `Seven-B'Ellana`):** Feature `0038` has no integrating task and, under the partial-integration decision of this date, will not acquire one; that made this re-examination trigger unreachable and turned a bounded risk acceptance into an unfalsifiable one. The trigger is redirected to the closure of Task `0038-28`, a real open Task on the same file surface. Original wording retained above, append-only.

## Acceptance criteria

- **AC-001** Extend `_src/tools/runner_transaction.py` and its schema to support a scoped validation profile (`verify-and-commit-v1` or modular action registration) that can execute declared unit test modules (e.g. `python -m unittest _src/tools/test_runner_transaction.py`) without invoking unrelated site generators (`_src/generate.py`)
- **AC-002** ensure candidate isolation, path-limited substantive and REF bookkeeping commits, and report collection function identically to `close-task-v1`. Document the profile in `docs/pipeline/runner-transaction.md` with test coverage in `_src/tools/test_runner_transaction.py`

## Definition of Done

Focused hermetic tests verify manifest validation, action execution, candidate isolation, and commit behavior for the new profile; syntax, unit tests, and path-limited commits succeed through the runner.
