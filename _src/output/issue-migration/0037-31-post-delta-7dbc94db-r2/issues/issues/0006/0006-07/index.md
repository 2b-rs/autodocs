---
schema_version: "1.0"
id: "0006-07"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:161"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

design a feedback loop from curator decision back into extraction/scrape/database logic

## Scope

- Current strength: `curation_flags.py` already assumes the output of a curation request is not just "data overwrite" but sometimes a code change or new residual rule.
  - Missing piece: a generalized, documented mechanism that can express whether a decision should update a DB value, create a migration, change parser logic, add an allowlist/exception, or spawn a new benchmark/fixture.
  - Add decision outcome classes and post-decision hooks so feedback scales beyond the extraction-report residual list. -- DONE 2026-08-13: added `_src/tools/decision_outcome.py` with `OUTCOME_CLASSES` (db_value_update, migration, parser_change, allowlist_exception, new_fixture, no_action) and an in-process `register_hook()`/`run_hooks()` post-decision hook registry (hook exceptions never block completing a decision). Threaded optional, backward-compatible `outcome_class`/`outcome_detail` kwargs through `curation_flags.complete_flag()`, defaulting to `no_action` so every existing caller keeps working unchanged. Added `_src/tests/test_decision_outcome.py`. Documented in `docs/pipeline/decision-outcome.md`. Does not implement any concrete hook (e.g. auto-writing a migration) or touch review_flags.py/RESIDUAL itself -- this is the generalized mechanism the task's wording ("design") asked for, same scoping pattern as 0006-05/0006-06. REF: 72ef6f6b

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
