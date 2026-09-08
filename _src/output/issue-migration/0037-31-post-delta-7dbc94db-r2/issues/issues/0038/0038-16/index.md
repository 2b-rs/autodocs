---
schema_version: "1.0"
id: "0038-16"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1927"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

Complete the pre-activation handoff and post-activation rollout/retirement package. REF: `f3522aaaa80d851f3ba28744b08956a52eb63275`.

## Scope

- **DEC-0037-002 disposition:** Superseded as an aggregate: retain accepted `0038-16.01` as historical handoff evidence; retire `.02` and the obsolete activation/retirement dependency.

## Acceptance criteria

- **AC-001** The handoff manifest and rollout evidence agree on every retained action, schema, result, scope, evidence, recovery, guidance, and retirement primitive
- **AC-002** neither phase creates a second queue, issue store, or authority

## Definition of Done

Both Subtasks are terminal; the historical incident suite and two concurrent disjoint sandboxed-agent fixtures pass; zero undispositioned critical chore findings remain; no user/privileged execution is required; and the package retains the before/after safety, time, retry, context, and evidence-volume comparison.
