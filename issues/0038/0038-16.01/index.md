---
schema_version: "1.0"
id: "0038-16.01"
level: "subtask"
parent: "0038-16"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-37"
  - "0038-05"
  - "0038-07"
  - "0038-13"
  - "0038-14"
  - "0038-15"
  - "0038-19"
  - "0038-20"
  - "0038-21"
  - "0038-23"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1932"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0038-16.01:0038-05, 0038-16.01:0038-07, 0038-16.01:0038-13, 0038-16.01:0038-14, 0038-16.01:0038-15, 0038-16.01:0038-19, 0038-16.01:0038-20, 0038-16.01:0038-21, 0038-16.01:0038-23, 0038-16.01:0037-37 Produce the versioned pre-activation handoff manifest consumed by the Feature `0037` queue implementation.

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `seven-azan (0038-16.01-Commit)`). Abgenommene Baseline `2c447983b7bf46bf942a494c2b36225bbbbdc2cc`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. 34/34 test_legacy_handoff_manifest.py, 26/26 test_chore_tool_inventory.py, Manifest-Checker PASS mit exakt übereinstimmenden Zahlen (72 Primitive, 65 Mappings/74 Action-IDs, 7 Retirement-Trigger, 0 unmapped, 0 mehrfach-autoritativ); base_commit-Bindung an 0037-37s Review-Package selbst nachgerechnet und identisch bestätigt; py_compile sauber; automation_safety PASS 0 Funde.
  - **Implementation completion (2026-08-21, `agent:seven-azan:0038-16.01:20260821T000000Z`, capability_class `unprivileged`, dispatched by privileged agent Seven):** REF `2c447983b7bf46bf942a494c2b36225bbbbdc2cc` on branch `0038-16.01` (based off `main` at `7b2e2ce99`; every prerequisite branch — `0038-05-closure`, `0038-07`, `0038-11`, `0038-12`, `0038-13`, `0038-14`, `0038-14-repair`, `0038-15`, `0038-19`, `0038-20`, `0038-21`, `0038-22`, `0038-23`, `0038-27` — plus `0037-37`'s REF `927da0690` verified as already ancestors of `main`, so the base-and-merge rule was satisfied with an empty merge set and no `DEC-0044-007` absorption was needed). Deliverables: `docs/pipeline/legacy-handoff-manifest-v1.json` (`legacy-handoff-manifest@v1`, 72 primitives over all nine required categories, binding the `0037-37` review package's producer REF, file digest, `base_commit` `e3a176aeb` and all 17 contract digests verbatim), `docs/pipeline/legacy-handoff-manifest.md`, the read-only stdlib-only checker `_src/tools/legacy_handoff_manifest.py`, `_src/tests/test_legacy_handoff_manifest.py`, plus catalog/index registration in `docs/pipeline/tools.md` and `docs/pipeline/README.md`. Zero-unmapped is enforced against the *living* `## Skript-Ausführungs-Infrastruktur` mechanism table of `tools.md` (rule `LHM074`, the `0038-14` living-enumeration pattern) and by exactly-one-disposition (`LHM056`); zero-multiply-authoritative by uniqueness over `authority_key` (`LHM048`) and over typed action/contract IDs (`LHM061`). 65 typed-action mappings own 74 unique IDs for `0037-46.01`; 7 retirement triggers are addressed to `0037-46.02`. The `0038-19` section-10 forward-mapping IDs are carried over verbatim so no second authority is created. **Validation:** `legacy_handoff_manifest.py --check` PASS/0 findings; `test_legacy_handoff_manifest` 34/34 OK (incl. fault injection for digest drift, dropped contract, missing/double disposition, duplicate authority key, duplicate typed action, dangling `superseded_by`, unmapped mechanism, claimed activation/authority change, pre-existing `.runner/` root, unsorted primitives); `test_chore_tool_inventory` 26/26 OK; `chore_tool_inventory.py --check` PASS; `automation_safety.py` PASS on the new tool and repository-wide (`policy_errors` 0, `unresolved_critical` 0); `process_doc_doctor.py` 0 errors; all 17 bound contract digests recompute. **Not done, deliberately:** no queue activated, no authority changed, no `Acceptance: ✓` created, `DONE.md`/`0038-16`/`0038-16.02` untouched, branch left at rest (not merged). **Carried open items, recorded not resolved:** the `0038-27`/`0038-22` TK-2 confirmation of the `automation_safety_policy.json` `owner_task: 0038-16` re-point is recorded under manifest primitive `validation.automation-safety`; `BLOCKING-EXTERNAL-001` (owned by `0037-49`) under `approval.external-readiness-blocker`. No backlog repair was required. Claim `TODO-seven-azan-0038-16.01-20260821T000000Z.md` is committed on the branch and carries the full provenance record.

## Acceptance criteria

- **AC-001** Bind the exact `0037-37` review-package digest and map every surviving legacy action, schema, result, scope, evidence, recovery, context, validation, and approval-readiness primitive to a specific `0037-46.01` typed action/contract or an explicit `0037-46.02` retirement trigger
- **AC-002** identify ownership, compatibility, test fixtures, and removal conditions without activating the queue or changing authority

## Definition of Done

A deterministic machine/human-readable manifest validates with zero unmapped or multiply authoritative primitives, names every required queue consumer and legacy retirement point, preserves the active singleton, and is ready for direct consumption by `0037-46.01`.
