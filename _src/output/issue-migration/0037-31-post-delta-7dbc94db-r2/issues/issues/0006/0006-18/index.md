---
schema_version: "1.0"
id: "0006-18"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006-15"
  - "0006-16"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:216"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-18:0006-15, 0006-18:0006-16 — model evidence/dependency links as a first-class, queryable graph rather than free text — REF: 048ffef1 — RESOLVED (user decision 2026-08-13): dismissal halts future propagation only, never severs existing edges (Option B); implemented in `_src/tools/dependency_graph.py`, documented in `docs/pipeline/dependency-graph.md`.

## Scope

- Current gap: the `evidence` field in the unified curation-item schema (**0006-03**) is descriptive text, not a queryable edge.
  - Introduce first-class node kinds for `requirement-version`, `curation-decision`, `evidence-snippet`, `artifact/synthesis`, and `human-comment`, with typed edges that distinguish at least: `derived_from`, `quotes`, `supersedes`, `revisits`, `comments_on`, `dismisses`, and `confirms`.
  - Support `artifact -> artifact` edges explicitly: AI may resynthesize its own prior text together with newly changed facts or comments, so synthesis-depends-on-synthesis is a real, potentially unbounded scenario.
  - Implement invalidation/revisit discovery as a graph traversal to fixed point (visited-set / cycle-safe), not a fixed hop count; termination comes from exhausting reachable dependents or hitting curator-dismissed nodes.
  - Define whether dismissal merely stops future propagation or also severs existing downstream dependency edges for audit purposes; document the chosen semantics.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
