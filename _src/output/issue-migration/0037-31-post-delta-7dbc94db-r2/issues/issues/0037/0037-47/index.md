---
schema_version: "1.0"
id: "0037-47"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2214"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Qualify the complete Feature `0037` plan for first-attempt execution by sandboxed/grunt agents. REF: `f3522aaaa80d851f3ba28744b08956a52eb63275`.

## Scope

- **DEC-0037-002 disposition:** Superseded. Future implementation assumes direct Shell/Git execution; Runner suitability is selected per long-running Task, not mapped across the Feature.

## Acceptance criteria

- **AC-001** Commit `issues/_policy/feature-0037-execution-profile.json` mapping every remaining Task/Subtask to capability class `sandboxed-grunt`, non-execution read/write steps, exact runner action IDs/arguments, input/output paths, expected base/authority state, runner/external-resource scope, credential handles, timeout/resources, preflight, success/failure predicates, validation, commit/bookkeeping transaction, retained evidence, and recovery. Human approval Tasks may require named humans to review/sign retained results, but no human or privileged agent executes the implementation/validation commands. Execute every referenced runner action against hermetic Task-shaped fixtures, verify every required dependency and approved credential handle is available to the runner, and split any Task whose request cannot be bounded or whose first request would need exploratory repair

## Definition of Done

Machine validation reports zero unmapped Tasks, unknown actions, privileged-agent dependencies, scope collisions, unavailable required resources, untested failure branches, or unresolved readiness findings; at least two simulated concurrent grunt agents complete disjoint fixture Tasks—including substantive plus REF bookkeeping commits—through the queue without direct execution or user intervention.
