---
schema_version: "1.0"
id: "0038-07"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0038-04"
  - "0038-06"
  - "0038-10"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1691"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0038-07:0038-04, 0038-07:0038-06, 0038-07:0038-10 Generate bounded Task context and resume capsules. REF: ee18a1e87e4ea4125803408c7a9b6ff7511427af

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-07-Commit)`). Abgenommene Baseline `ee18a1e87e4ea4125803408c7a9b6ff7511427af`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. 21/21 eigene Tests am eigenen REF.
  - **Completion evidence (2026-08-20):** Committed the read-only `_src/tools/task_context_capsule.py`, composing `legacy_task_doctor.py` (0038-04), `legacy_scope_planner.py`'s DAG graph-walking helpers (0038-06), and the immutable per-attempt result/current-pointer primitives from `runner_transaction.py` (0038-10, merged from branch `0038-10` tip `539ea06bb04f244a6df95793bdbf1bf41ef8c17b`) into one bounded `task-context-capsule@v1` document (default 8192-byte compact-JSON budget, priority-ordered truncation, provably terminating next-action shrink floor) plus a `docs/pipeline/task-context-capsule.md` guide and a `docs/pipeline/tools.md` catalog entry. 21/21 focused tests passed (`python3 -m unittest _src.tests.test_task_context_capsule`), including hermetic fixtures reproducing the named `0037-48` premature-publication-reporting resume (verbatim recorded "Next step" text from `TODO-perplexity-0037-48-a7f3c1e29b04.md`) and an evidence-grounded, explicitly-documented reconstruction of the `0036-06` context-overflow resume (the original claim predates claim retention and was deleted at Feature closure). `python3 -m py_compile` and `python3 _src/tools/automation_safety.py --json` both passed with zero findings. See `TODO-seven-azan-0038-07-20260820T023122Z.md` for the complete claim, branch/merge, scope, and validation record.

### Campaign C — Make validation and environments trustworthy

## Acceptance criteria

- **AC-001** Compile only selected Task/Feature constraints, prerequisite states, claim identity, authority/policy digests, pending request/result, explicit/derived scope, material findings, completed phases, retained evidence references, and exact next action into machine JSON plus a short human summary. Full logs/prompts remain referenced by path/digest
- **AC-002** immutable ownership survives context/tool-budget boundaries

## Definition of Done

Fixtures resume `0037-48` after premature publication reporting and `0036-06` after context overflow without repeating completed work, changing owner, dropping blockers, or exceeding a fixed context-size budget.
