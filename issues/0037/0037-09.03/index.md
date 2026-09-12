---
schema_version: "1.0"
id: "0037-09.03"
level: "subtask"
parent: "0037-09"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-04"
  - "0037-08"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2244"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-09.03:0037-04, 0037-09.03:0037-08 Implement typed-reference, provenance graph, artifact/run/finding, evidence-class, and privacy/public-projection validation. **Claim:** `TODO-Gabriel-Reno-0037-09.03-20260825T050700Z.md` (`agent:gabriel-reno-20260825t050700z:0037-09.03:20260825T050700Z`). **Implementation completion (2026-08-25, Gabriel-Reno, unprivileged Programmer):** REF `b72aefbcfc2b3e5002cf5762876de9b520951e2b`. Provenance checks IV0923–IV0934 in `_src/tools/issue_validate.py`; 27 negative fixtures plus adversarial leak token under `_src/tests/fixtures/0037-09.03/`. Validation: `test_issue_validate` 17/17 PASS; `py_compile` PASS; `git diff --check` PASS; automation_safety reports 0 findings on `issue_validate.py`. **Acceptance: ✓** (2026-08-27, Integrator `paul`, unabhängig von Implementierer `Gabriel-Reno` / `agent:gabriel-reno-20260825t050700z:0037-09.03:20260825T050700Z`). Abgenommene Baseline `b72aefbcfc2b3e5002cf5762876de9b520951e2b` / `016a21f484e83b4d9486e242ea0165f59ba19bdb`; Review-REF `9e86bd66886822a61d0efd08e65d102b91dcd96b`; evidence `7cc356a90756fc052dc570b708893ef2769eda73`; C merge `6b4f8bab94042246ca2a352210f0bda43bba9017`; re-verify receipt `be5ea3d6db0b8f39b525bb874f3f40172cb0bb88`; AWARD `1787870279374-3300fdfe`. No checkpoint crossed or upward integration performed.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Detect invalid/dangling/reversed/cardinality-violating edges, ID/digest collisions, fabricated context, mutable path without digest, synthetic-as-production evidence, restricted-field/endpoint leakage, redaction mismatch, and stale or incomplete reverse indexes

## Definition of Done

One negative fixture per typed relation/classification/privacy rule and adversarial leak tokens pass fixed traversal/resource budgets.
