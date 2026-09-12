---
schema_version: "1.0"
id: "0037-17.02"
level: "subtask"
parent: "0037-17"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-17.01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2265"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
  - id: "AC-005"
    status: "active"
---

## Goal

PREREQ: 0037-17.02:0037-17.01 Implement deterministic provenance graph and reverse indexes under `provenance/_views/`. **Claim:** `TODO-Gabriel-Stamets-0037-17.02-20260825T083300Z.md` (`owner_token: agent:gabriel-stamets-20260825t083300z:0037-17.02:20260825T083300Z`). **REF:** `71189ce1141743f71ff2c94a11bd264ef6e890bf`.

## Scope

- **Requirements covered (reciprocal downstream binding):** `RQ-TRACE-01`, the structural mapping part of `RQ-TRACE-02`, and the index-visible finding part of `RQ-TRACE-04` from `docs/dossiers/re-intake-evidence-traceability-and-roles.md`.
  - **Acceptance: ✓** (2026-08-28, Integrator `belanna`, independent of Implementer `Gabriel-Stamets`, AE-4+AE-5 follow-up implementer `Odo`/`gabriel`, and lander `paul`). Product REF `71189ce1141743f71ff2c94a11bd264ef6e890bf`, landed `8aed115637`; first-review Review-REF `2a44cb7a7` (verdict INCONCLUSIVE, AE-4+AE-5 gaps named); AE follow-up landed `1525852d7` (original `28eb2ba9b`); delta re-verify Review-REF `185e3d73f` (verdict ACCEPTED, AE-4 three codes and AE-5 64-graph closed, Stamets product confirmed byte-identical); AWARD `1787889833273-ac7f03a2`. No checkpoint crossed (`0037-17.02` unflagged). No upward Feature integration performed.

## Acceptance criteria

- **AC-001** Rebuild from immutable sources only
- **AC-002** expose event/node/edge tables plus issue→criteria/runs/artifacts/findings and artifact→producer/issue/campaign/input mappings
- **AC-003** preserve cycles as data while preventing traversal loops
- **AC-004** embed source/schema/tool hashes and reject stale or hand-edited indexes. The graph exposes issue/criterion→evidence and evidence→issue/criterion mappings derived from validated immutable provenance sources. A closed item's evidence identifiers and digests remain represented after later unrelated Task activity and after deletion and regeneration of the derived indexes. Dangling or unresolvable endpoints are emitted as structured findings naming the exact endpoint, identifier, and path where available
- **AC-005** authorized redaction is represented distinctly and is not misreported as a broken endpoint. This Subtask consumes immutable sources owned by `0037-17.01` and does not become a second source writer

## Definition of Done

Golden indexes are byte-stable across input enumeration order, reconcile all source IDs/edges/counts, detect dangling/redacted endpoints, and rebuild cleanly after deletion. A hermetic regression fixture records and closes an item's evidence baseline, adds later unrelated Task activity, deletes only the disposable derived indexes, rebuilds them, and proves that the original evidence IDs, digests, and forward/reverse mappings are unchanged. Golden tests cover a valid bidirectional mapping and dangling, missing, and redacted endpoints without duplicating the shared validation semantics of `0037-09.03`.
