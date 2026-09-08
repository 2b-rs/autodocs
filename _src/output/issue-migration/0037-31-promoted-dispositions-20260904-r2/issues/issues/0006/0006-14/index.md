---
schema_version: "1.0"
id: "0006-14"
level: "task"
parent: "0006"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:189"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

document the feature as a repo-level workflow contract before implementation spreads further

## Scope

- Update `docs/pipeline/{data-model,roles,actions,processes,reports,tools}.md` and `_src/SPEC_BUILD_PROCESS.md` so the unified curation model is the documented source of truth, not just emergent queue code.
  - Explicitly record what remains human-only, what AI may propose, and what tools may apply automatically. -- DONE 2026-08-13: added a consistently-worded 'unified curation/review model' cross-reference section to each of docs/pipeline/{data-model,roles,actions,processes,reports,tools}.md and to _src/SPEC_BUILD_PROCESS.md, pointing to curation-item-schema.md/workflow-lifecycle.md/workflow-validation.md as the canonical model instead of duplicating them. roles.md and SPEC_BUILD_PROCESS.md explicitly record the human-only / AI-may-propose / tool-automatic split (including why review_flags.py's proposed->applied shortcut does not skip a human step). REF: c37d2d4b

### Cross-release traceability and invalidation

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
