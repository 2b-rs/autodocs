---
schema_version: "1.0"
id: "0006-15"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006-02"
  - "0006-03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:195"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-15:0006-02, 0006-15:0006-03 — define the ID naming schemes needed for cross-release traceability of curated decisions, evidence snippets, and AI-derived artifacts — REF: 8792b642 — hash algorithm (SHA-256/hash8) and UUIDv7 generation pinned and implemented in `_src/tools/version_id.py`; documented in `docs/pipeline/version-id-scheme.md`. Minting code exists but is not yet wired into review_flags.py/curation_flags.py write paths (0006-16/0006-17 scope).

## Scope

- Motivating scenario (2026-08-13): a curator decides on a requirement's value; a later AUTOSAR release changes that same requirement; the system must be able to find every AI-generated artifact (comment/amendment/hypothesis/synthesis) whose evidence depended on the now-superseded decision or requirement version, and every requirement that changed, without deleting any prior decision, curation, evidence snippet, synthesis, or specification version — all of which must remain retrievable under a stable, unique ID.
  - Versioning grain for AUTOSAR AP: requirement level.
  - Define and document at least these ID families, layered on the canonical identity from **0006-02**:
    - canonical requirement identity: `project/kind/id` (release-independent, e.g. `AUTOSAR/AP/record/SWS_UCM_00348`)
    - requirement version: `<canonical-id>@rel:<release>#<content-hash8>` — one immutable content snapshot per release
    - curation decision: `curation:<uuid7>` — immutable once decided, only ever superseded, never mutated or deleted
    - evidence snippet: `evidence:<uuid7>` — first-pass AI extraction result assigned to one requirement version together with its reason
    - AI-generated artifact / synthesis: `artifact:<uuid7>` — second-pass description/amendment/hypothesis, including later resyntheses
    - supersession edge: explicit `supersedes:<old-version-id>-><new-version-id>` link, not inferred from timestamps
  - Specify ID generation rules (UUIDv7 for decisions/evidence/artifacts to stay sortable-by-time across concurrent queue/browser/AI write paths per **0006-06**; content-hash truncation length and hash algorithm for requirement versions) and where each ID family is minted (which tool/script).

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
