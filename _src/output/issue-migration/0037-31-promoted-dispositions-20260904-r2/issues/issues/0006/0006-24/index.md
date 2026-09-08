---
schema_version: "1.0"
id: "0006-24"
level: "task"
parent: "0006"
state: "open"
visibility: "internal"
prerequisites:
  - "0006-18"
  - "0006-19"
  - "0006-20"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:253"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-24:0006-18, 0006-24:0006-19, 0006-24:0006-20 — support a "delta view" of everything changed, superseded, or invalidated since a given release or date

## Scope

- Motivating scenario (2026-08-13): a user needs a report of exactly what changed since R25-11 (or since a given date) — which requirement versions were superseded, which curated decisions became stale, and which AI artifacts were invalidated or flagged for revisit as a result.
  - Define a query that takes a baseline release/date and returns: new requirement versions created since then, decisions/evidence/artifacts marked `invalidated` as a consequence (traced via the **0006-18** dependency graph), and any revisit tasks enqueued by **0006-20**'s trigger job in that window.
  - This is closely related to but distinct from **0006-20**'s per-trigger cascade report: **0006-20** reports the immediate blast radius of one trigger event; **0006-24** aggregates across an arbitrary time/release window for ad-hoc review, so implement it as a query over the stored cascade results rather than a second cascade mechanism.
  - Note overlap with **0001**'s build-report work: the per-trigger report from **0006-20** is a natural input to a delta view, so align schemas rather than defining a second, incompatible "what changed" report format. -- DONE 2026-08-13: added `_src/tools/delta_view.py` with `delta_view(release=None, date=None)`, a pure aggregation query over 0006-18/19/20's existing stores -- ZERO new cascade logic, per the task's explicit instruction. Returns changed_requirements (new versions since baseline), invalidated_nodes, revisit_tasks_enqueued/revisit_tasks -- field names deliberately schema-aligned with 0006-20's summarize_reports() output, per the task's explicit alignment instruction. A release baseline resolves to the earliest recorded_at timestamp that release was ever recorded (documented assumption, since invalidation/revisit timestamps are wall-clock, not release-tagged); an unknown release returns an empty delta rather than erroring. Added `_src/tests/test_delta_view.py` (9 tests). Documented in `docs/pipeline/delta-view.md`. Does not build a CLI/HTML render, same deferral as 0006-23 pending 0006-14. REF: 400cef88

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
