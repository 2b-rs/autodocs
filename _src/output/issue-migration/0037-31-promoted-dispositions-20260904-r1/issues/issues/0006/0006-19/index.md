---
schema_version: "1.0"
id: "0006-19"
level: "task"
parent: "0006"
state: "open"
visibility: "internal"
prerequisites:
  - "0006-18"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:223"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-19:0006-18 — add invalidation state and confidence history orthogonal to the existing curation-item lifecycle — REF: 11ff87d4 — RESOLVED (user decision 2026-08-13): additive formula (base by origin/item_kind + confirms bonus + signed feedback deltas up to +/-0.15/item), 0.05 dismissal floor; dismissal blocks revisit-eligibility but confidence changes from other causes (feedback/confirmation/cascade_invalidation) DO enqueue an AI revisit; implemented in `_src/tools/confidence.py`, documented in `docs/pipeline/confidence-model.md`.

## Scope

- Current gap: the lifecycle states (discovered -> queued -> claimed -> proposed -> accepted/rejected -> applied -> published -> superseded, per **0006-06**) have no state representing "still retrievable, but based on superseded facts / comments / model settings."
  - Model invalidation as a flag/status set by cascade (from **0006-18**'s graph), not a curator-driven lifecycle transition; ensure invalidated artifacts remain retrievable and are never deleted, only marked.
  - Add append-only `confidence_history[]` for AI-generated knowledge so prior confidence values remain retained and re-calculable even after the underlying requirement version, curated decision, user comment, source set, or model/settings become superseded.
  - Define how human comments, curator confirmations/rejections, and AI-inferred vs. hard-fact vs. curated-fact provenance increase or decrease confidence.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
