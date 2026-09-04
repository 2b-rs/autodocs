---
schema_version: "1.0"
id: "0037-17"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-17.01"
  - "0037-17.02"
  - "0037-17.03"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2252"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-17:0037-17.01, 0037-17:0037-17.02, 0037-17:0037-17.03 Complete immutable provenance storage, indexing, and query support. **Claim:** `TODO-dax-0037-17-parent-20260828T060352Z.md` (`owner_token: agent:dax-0037-17-parent-20260828:0037-17:20260828T060352Z`). **REF:** `b41a5cedddedf17e62951d4bb0d2def8f1d33743`. **Implementation completion (2026-08-28, Dax, unprivileged Programmer):** Package-level verification against `main@7d6d71475796d3afdacff585d25059e2059e73b3`; no product edit. `uv run python _src/tests/test_provenance_store.py` 23/23 PASS; `test_provenance_views.py` 15/15 PASS; `test_provenance_query.py` 12/12 PASS; `py_compile` PASS. Evidence `docs/campaign-evidence/0037-17-parent-dax-20260828T060352Z/package-verify.md`. No Acceptance claimed.

## Scope

- **Acceptance: ✓** (2026-08-28, Integrator `belanna`, independent of Implementer `Dax`, git-author leak `gabriel`, and lander `paul`). Product REF `b41a5cedddedf17e62951d4bb0d2def8f1d33743`, landed `b42db62287c203112ded6c326fa165a7f4ee7131`; first-review Review-REF `76393ac26` (verdict ACCEPTED: genuine package verification, not aggregation-only; 50/50 tests independently rerun; zero product edit independently confirmed via blob-identity comparison; AE-7 applies to this bookkeeping/verification increment without waiving the children's own current Acceptance); land AWARD `1787898440670-71db94cd`; cherry-pick AWARD `1787901179486-40ad176b` (supersedes STOP'd ff-only AWARD `1787899600202-777db475`, cherry-picked from stamp `155aa3748` after `main` advanced past it via unrelated `DEC-0044-029` R3). No checkpoint crossed (`0037-17` parent unflagged). No upward Feature integration performed.

## Acceptance criteria

- **AC-001** Storage remains authoritative/immutable, indexes remain disposable, and every reverse result is derivable from one validated forward event rather than duplicated links

## Definition of Done

All three Subtasks pass shared causal-chain fixtures and no writer can mutate an existing event/artifact-set identity.
