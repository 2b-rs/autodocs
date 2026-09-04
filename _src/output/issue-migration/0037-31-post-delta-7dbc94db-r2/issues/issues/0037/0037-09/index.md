---
schema_version: "1.0"
id: "0037-09"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-09.01"
  - "0037-09.02"
  - "0037-09.03"
  - "0037-09.04"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2228"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-09:0037-09.01, 0037-09:0037-09.02, 0037-09:0037-09.03, 0037-09:0037-09.04 Complete strict issue, lifecycle, provenance/privacy, and derived-artifact validation. **Claim:** `TODO-tuvok-0037-09-parent-20260828T031800Z.md` (`agent:tuvok-0037-09-parent-20260828:0037-09:20260828T031800Z`). **REF:** `80628b80213d557dda80a1c053a6a23ceebec696`. **Implementation completion (2026-08-28, Tuvok, unprivileged Programmer):** Package-level verification against `main@9cd0075225c6cf6d06faeef2ee432123c923a1b9`; no product edit. `uv run python _src/tests/test_issue_validate.py` 58/58 PASS; AE-5 5/5 PASS; scoped automation-safety PASS. Evidence `docs/campaign-evidence/0037-09-parent-tuvok-20260828T0318Z/package-verify.md`. **Acceptance: ✓** (2026-08-28, Integrator `belanna`, independent of Implementer `tuvok-0037-09-parent-20260828` and lander `paul`). Product REF `80628b80213d557dda80a1c053a6a23ceebec696`; first-review Review-REF `cbb1026307422b0f02759c29eb13efdf9c7252a4` (verdict ACCEPTED, including the `validate.py` `check_issue_store` wiring independently confirmed by actual execution, not source inspection alone); first-review AWARD `1787881010063-2adb04b0`; lander `paul` AWARD `1787881912860-e6ce6b7f`. No checkpoint crossed or upward integration performed.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** All validators share `_src/tools/issue_validate.py` diagnostics/config, are side-effect free, accept explicit authoritative/candidate/staged roots, and cover every rule ID in the architecture review package without one validator silently weakening another

## Definition of Done

All four Subtasks pass the fixed rule-coverage/test profile and `_src/validate.py` invokes the complete suite; tracked CI is not claimed unless separately introduced.
