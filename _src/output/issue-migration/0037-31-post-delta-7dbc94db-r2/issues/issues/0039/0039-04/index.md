---
schema_version: "1.0"
id: "0039-04"
level: "task"
parent: "0039"
state: "closed"
visibility: "internal"
prerequisites:
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1549"
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
  - id: "AC-006"
    status: "active"
---

## Goal

Define and introduce the privileged Task-acceptance and Feature-closure convention, with a DOCX/PDF dossier and adapted process/agent instructions.

## Scope

- **Claim (2026-08-17):** The current user selected this work and retained this session's explicit privileged designation. Claimed via `TODO-zed-0039-04-20260817-131714-a3facd2d095e.md`, owner_token: agent:zed:0039-04:20260817-131714-a3facd2d095e, base_commit `7df56ab6686b2b5bc45efc1d99455e4e838530ab`.
  - **REF:** `924eeaf59e22297258f38bb0e9e25eca52dd666b`
  - REF: `924eeaf59e22297258f38bb0e9e25eca52dd666b`
  - **REF format note (2026-08-30, Project Lead `kathryn`):** Same hash as above, not a new claim. Added under Management decision `decision-1788065728470-280206f4` because the legacy doctor's authoritative-task detector requires the plain two-space-indent dash form and does not match the bold markdown form used above it, at `_src/tools/legacy_task_doctor.py` around line 845, which had produced a missing-reference finding despite the value being present and correct.
  - **Implementation completion (2026-08-17):** Focused acceptance-package, backlog graph, instruction-consistency, link, digest, DOCX/XML, PDF/content-equivalence, diagnostics, and `git diff --check` validation passed. The legacy doctor still reports 357 pre-existing findings globally and none for `0039-04`/`0039-05`. The bounded `python3 _src/validate.py` run produced no output and timed out after 180 seconds, so no full-project validation pass is claimed. This Task awaits a separately assigned, normally independent privileged acceptance review; no `Acceptance: ✓` credit is recorded.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `agent:geordi:0039-04:review2-20260830` (Geordi La Forge, privileged independent reviewer)
    - **Authority reference:** atomic award `1788070198728-35c6be82`
    - **Accepted at:** `2026-08-30T06:14:27Z`
    - **Exact reviewed candidate:** `0a195615f043eb1e8b3501dd13446315be65aca4`
    - **Contract SHA-256:** `4fa3380935cb2cdaafbafa98f937f718425e8bcbaaff934d50117de26157d027`
    - **Work-product manifest SHA-256:** `141441171b0ccc439a66e40f57b1424a2a47f2ccb331502893a00d9653e80cc3`
    - **Prerequisite-acceptance SHA-256:** `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` (empty closure)
    - **Review REF:** `fa5dba719a030da735f15252105278dcdd93048b`
    - **Terminal root claim:** `DONE-zed-0039-04-20260817-131714-a3facd2d095e.md` (byte-identical rename of the historical TODO claim named above)

## Acceptance criteria

- **AC-001** Define canonical accepted state `accepted` rendered as `✓`
- **AC-002** distinguish implementation/disposition completion from acceptance
- **AC-003** prohibit sandboxed/grunt acceptance promotion
- **AC-004** require an independently assigned privileged reviewer to inspect the exact Task contract, work products, validation/evidence, material findings, and transitive non-accepted prerequisite closure
- **AC-005** define bottom-up acceptance, accepted dispositions, rejection/inconclusive outcomes, invalidation, high-risk acceptance-before-start gates, Feature aggregate review, authority boundaries, migration/cutover, records, metrics, and machine-enforcement needs. Produce a DOCX/PDF dossier covering affected documents/processes, daily operation, benefits/risks, and careful Automotive SPICE relationships
- **AC-006** adapt current agentic and pipeline instructions without appropriating foreign tool claims

## Definition of Done

The dossier and normative process are committed; `TODO.md`, `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, and applicable pipeline lifecycle guidance agree that only a currently authorized privileged reviewer may promote exact reviewed work to accepted and that a Feature cannot move to `DONE.md` until every active Task/Subtask has an accepted disposition plus aggregate closure acceptance. Formats, links, marker semantics, authority boundaries, prerequisite behavior, migration implications, and retained provenance validate. Machine enforcement that conflicts with active foreign scopes is represented as explicit downstream work. This implementation closes at `[x]` and awaits independent privileged acceptance rather than self-acceptance.
