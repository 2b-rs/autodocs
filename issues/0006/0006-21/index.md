---
schema_version: "1.0"
id: "0006-21"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006-18"
  - "0006-19"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:235"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-21:0006-18, 0006-21:0006-19 — define the structure of synthesized knowledge units so fact type, evidence, and confidence remain inspectable and re-runnable — TODO: typed-claim object model sketched 2026-08-13 (claim ID, type, evidence refs, confidence, history, dismissal flag), not yet turned into a concrete field-by-field schema or fixture

## Scope

- A synthesized description must not be a single opaque blob. Define a typed-claim object model where each claim/section can distinguish at least: hard fact, curated fact, user comment, and AI-inferred knowledge.
  - For each claim, store: stable claim ID, parent artifact/synthesis ID, claim type, textual content, evidence/dependency refs, current confidence, append-only `confidence_history[]`, invalidation status, and whether curator action has dismissed it from future synthesis runs.
  - Ensure the model can represent AI revisiting its own prior text: later syntheses may cite/reuse/supersede earlier synthesis claims without losing the original text or confidence trail. -- DONE 2026-08-13: turned the sketched typed-claim object model into a concrete `typed-claim@v1` schema in `_src/tools/typed_claim.py` with explicit fields for claim_id, parent_artifact_id, claim_type (`hard_fact` / `curated_fact` / `user_comment` / `ai_inferred`), content, evidence_refs, dependency_refs, current_confidence, append-only confidence_history, structured invalidation, dismissed_from_future_synthesis, and bidirectional supersession links between older/newer claims. Added constructor/validator/update helpers plus `_src/tests/test_typed_claim.py` (10 tests). Documented with worked examples in `docs/pipeline/typed-claim-schema.md`. Deliberately schema-first only: no storage or renderer wiring yet; broader cross-doc spread remains 0006-22. REF: 8cdaf6ca

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
