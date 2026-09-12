---
schema_version: "1.0"
id: "0037-17.01"
level: "subtask"
parent: "0037-17"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-04"
  - "0037-07"
  - "0037-09"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2257"
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
---

## Goal

PREREQ: 0037-17.01:0037-04, 0037-17.01:0037-07, 0037-17.01:0037-09 Implement atomic event, run, finding, and artifact-set writers/readers at the approved `provenance/` paths. **Claim:** `TODO-Gabriel-Culber-0037-17.01-20260825T081500Z.md` (`owner_token: agent:gabriel-culber-20260825t081500z:0037-17.01:20260825T081500Z`). **REF:** `995c025b1bc4de575473dab95256db0ab61f8b17`.

## Scope

- **Successor recheck (2026-08-22, Seven-Icheb, per `AGENTS.md` "Completing implementation work" step 5):** `0037-07` closed `[x]` this pass. Of this Task's three prerequisites, `0037-04` `[x]` and `0037-07` `[x]` are now terminal, but `0037-09` is still `[ ]` (open, with its own four unresolved Subtask prerequisites `0037-09.01`-`.04`). `0037-17.01` is therefore **not yet globally eligible** — recheck again once `0037-09` closes.
  - **Start (2026-08-25, Gabriel-Culber):** Feature `0037` pin `063b9c04eb68e770ef7b2f9b7d7ea3aeff5c984a` already has `0037-09` `[x]` (parent package consistency). `0037-07`/`0037-09` are ancestors; named ref `0037-04` is absent and its contracts are in-tree. Implementation start is unlocked on this baseline.
  - **Implementation completion (2026-08-25, Gabriel-Culber, unprivileged Programmer):** `_src/tools/provenance_store.py` exclusive-create writers/readers; `_src/tests/test_provenance_store.py` 13/13 PASS. Validation: `python3 _src/tests/test_provenance_store.py` OK; `py_compile` OK; `git diff --check` OK. No Acceptance, checkpoint, main, DONE, or push.
  - **Acceptance: ✓** (2026-08-28, Integrator `belanna`, independent of Implementer `Gabriel-Culber`, AE-4 follow-up implementer `Neelix`/`gabriel`, and lander `paul`). Product REF `995c025b1bc4de575473dab95256db0ab61f8b17`; first-review Review-REF `73d8b9dd` (verdict INCONCLUSIVE, AE-4 ten-code gap named); AE-4 follow-up landed `6af31a201` (original `bafc61ff1`); delta re-verify Review-REF `523c84635` (verdict ACCEPTED, ten codes closed, Culber product confirmed byte-identical); AWARD `1787888962319-a5a1b319`. No checkpoint crossed (`0037-17.01` unflagged). No upward Feature integration performed.

## Acceptance criteria

- **AC-001** Create one validated JSON file with exclusive-create semantics
- **AC-002** canonicalize/digest artifact sets
- **AC-003** require typed endpoints, source/tool/config commits, run/campaign/issue/criterion context, privacy/evidence class, trigger/cause, and path+digest for mutable files
- **AC-004** reject duplicate/colliding IDs, dangling refs, fabricated historical context, and overwrite attempts

## Definition of Done

API tests cover concurrent creation, replay idempotence, collision, crash before rename, file/tree digest changes, redaction, legacy-confidence adapters, and no partial file after injected failure.
