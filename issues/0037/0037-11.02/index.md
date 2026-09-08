---
schema_version: "1.0"
id: "0037-11.02"
level: "subtask"
parent: "0037-11"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-05"
  - "0037-08"
  - "0037-09"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2310"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0037-11.02:0037-05, 0037-11.02:0037-08, 0037-11.02:0037-09 Implement `issues/_views/catalog.json` and `issues/_views/dependency-graph.json`. **Claim:** `TODO-Gabriel-Joann-0037-11.02-20260825T082200Z.md` (`agent:gabriel-joann-20260825t082200z:0037-11.02:20260825T082200Z`). **REF:** `bdffd04e8f6221490b5fb773673804936bbf330d`. **Claim:** `TODO-Gabriel-Joann-0037-11.02-20260825T081500Z.md` (`agent:gabriel-joann-20260825t081500z:0037-11.02:20260825T081500Z`).

## Scope

- **Validation:** `python -m unittest _src.tests.test_issue_views -v` — 17 tests OK (9 original + 8 AE-4/AE-5 follow-up; independently reconfirmed against then-current `main` before this stamp).
  - **Acceptance: ✓** (2026-08-28T09:29Z, Integrator `belanna`, independent of Implementer `Gabriel-Joann`, AE-4+AE-5 follow-up persona `Tilly`/git-author `gabriel`, and lander `paul`). Product REF `bdffd04e8f6221490b5fb773673804936bbf330d`, landed product `22e6f466c`, AE follow-up landed `3dd4e2335`; first-review Review-REF `65321285a` (verdict INCONCLUSIVE, AWARD `1787904358530-20191990`, named AE-4 gaps: `_archive_status` disposition literals, `_reject_browser_keys` raise path; AE-5 absent); delta re-verify Review-REF `761835510` (verdict ACCEPTED, AWARD `1787906912805-c0f7a0d7`, 17/17 independently rerun, both AE-4 gaps closed, AE-5 property test present); land AWARD `1787908094238-07b8d598`; this stamp AWARD `1787909258361-f29e14b9` (RETRY, superseding STOP'd `1787909114335-05296072`/`1787909184673-6df227a0`). No checkpoint crossed (`0037-11.02` unflagged). No upward Feature integration performed.

## Acceptance criteria

- **AC-001** Catalog contains normalized items with source locators/hashes
- **AC-002** graph projection contains already-classified nodes/edges, lifecycle/archive status, Feature-closure versus start-gate edges, stable internal item URLs, and explicit malformed/missing endpoints. Both include schema/tool/config/source digests plus a content-derived generation ID and deterministic ordering
- **AC-003** they contain no inferred browser-only semantics

## Definition of Done

JSON Schema/golden tests prove byte determinism, full source reconciliation, all state/edge classes, missing-endpoint visibility, and stale/manual-edit detection.
