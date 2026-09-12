---
schema_version: "1.0"
id: "0044-05"
level: "task"
parent: "0044"
state: "open"
visibility: "internal"
prerequisites:
  - "0044-04"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1123"
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

PREREQ: 0044-05:0044-04 Define machine-readable schemas for task requirement profiles and agent capability descriptors, plus a deterministic no-AI matcher. *(architect-elaboration)* Claim: `TODO-data-0044-05-20260825T165207Z-4f9c2a71.md` (owner token `agent:data:0044-05:20260825T165207Z-4f9c2a71`; Architect separation/TK-2 preparation; no matcher implementation or acceptance authority).

## Scope

- **Requirements covered:** `RQ-CB-01` … `RQ-CB-03`; implements `DEC-0044-004`.
  - **Package completion (2026-08-25, Implementer `belanna`, distinct from Architect `data`; separate assignment from `0044-05.03`, agent-inbox `1787682099937-e59a8bb8`):** All three children (`.01`/`.02`/`.03`) terminal. Schema/tool/docs consistency, legacy-schema byte-identity, self-application evidence (new committed digest-bound profile/descriptor/result, `single-eligible`, exit 0), absence of broad activation/historic credit, and complete finding dispositions (`automation_safety` PASS 0 findings) all independently verified. REF: `f5d75092d`. Full report: `docs/campaign-evidence/0044-05/self-application/parent-completion-report.md`. **No `Acceptance: ✓`.** Mandatory integration checkpoint below stands unchanged, for the separately assigned privileged Integrator.
  - **Integration review:** **mandatory.** **Rationale (architect):** the matcher decides which agent may receive which authority-relevant work; a false positive here routes work past the capability-class boundary.
  - **[u] Integration verdict — BLOCKED (2026-08-25T20:43:31+02:00):** Verdict author `geordi` (Geordi La Forge, privileged Team Enterprise Integrator); authority `agent-inbox:jean-luc→geordi:1787682425261-41defefd`; exact rejected implementation/integration baseline `1aeaed098eb28f4c56e5ec07de56e3b0334ffcf3`; rejected item `0044-05`, finding `F-0044-05-GEORDI-001`. Reason: the published closed JSON Schemas contradict the approved matcher contract and their own committed/emitted instances — `test_scope` and `resource_bounds` forbid every field used by the self-application profile, documented nested member shapes are not schema-bound, and invalid-input results emit an `error` property forbidden by `capability-match-result@v1`. Rejected review evidence REF `5208d4b31677792a9f9685085fa7053071f55938`, report `docs/campaign-evidence/0044-05/checkpoint-review-geordi-20260825.md`. Parent implementation marker remains `[x]`; no `Acceptance: ✓`, checkpoint crossing, or `main` advance occurred. A later correction does not self-clear or supersede this verdict: it remains until an authorized user decision and separately assigned independent re-review record the disposition.
  - **Package completion, corrected round (2026-08-25T20:50Z, Implementer `belanna`, same separate assignment):** Reconciled corrected schemas (`e637660978`/`6b8ff993d`, fixing `F-0044-05-GEORDI-001`) and the `[u]` verdict lineage (`5208d4b31`/`016bbcc94`) into this candidate via two `--no-ff` merges; rejection evidence and the verdict above left unmodified. Independently re-validated the committed self-application instances **against the published JSON Schemas themselves** (not just the matcher's own private validation) using a new stdlib-only structural validator, `docs/campaign-evidence/0044-05/self-application/validate_against_schema.py`, sanity-checked by reproducing Geordi's exact finding against the pre-fix schemas before trusting it against the corrected ones: profile, descriptor, and result instances all **VALID**; a new genuine invalid-input result (real legacy-descriptor rejection, exit 2) also **VALID** against the corrected result schema and **INVALID** (forbidden `error`) against the old one, matching finding #3 exactly. 19/19 tests, `automation_safety` PASS 0 findings, legacy digest unchanged, no activation wiring, non-activation sentence still byte-identical, full ancestry reconfirmed, `git diff --check` clean. REF: `2731d8a11`. Full record: `docs/campaign-evidence/0044-05/self-application/parent-completion-correction-20260825T2043Z.md`. **Does not clear the `[u]` verdict above** — that remains for an authorized user decision and a separately assigned independent re-review. No `Acceptance: ✓`.
  - **[u] Integration re-review verdict — REMAINS BLOCKED (2026-08-25T21:13:03+02:00):** Verdict author `geordi` (Geordi La Forge, privileged Team Enterprise Integrator); authority `agent-inbox:jean-luc→geordi:1787685001155-e6cde308`, relaying the current user's Alternative A authorization for a fresh independent re-review and conditional supersession only if accepted; exact corrected rejected baseline `b9d402d643a08f9a6b5466e7ba96c6b774f44e52`; rejected item `0044-05`, finding `F-0044-05-GEORDI-002`. Reason: the published profile and descriptor schemas accept authority-invalid cross-field combinations that the normative matcher rejects — including `sandboxed-grunt` with direct execution, `privileged` with runner routing, and a non-prefix cognitive-class sequence — although the approved architecture sections 5–7 require the schemas to enforce the same capability-class, route, role, and cognitive-prefix constraints. Fresh rejected review evidence REF `b4956fa26d2e60f6d1bd0a2eb16ca91e0e31bafa`, report `docs/campaign-evidence/0044-05/checkpoint-rereview-geordi-20260825.md`. The prior verdict at `016bbcc94ecc469bc7bb817ceacbf0acde52dc35` remains current: its user-authorization condition was met, but the separate acceptance condition was not. Parent implementation remains `[x]`; no `Acceptance: ✓`, verdict supersession, hygiene gate, checkpoint crossing, or `main` advance occurred. A later correction does not self-clear this verdict; disposition still requires an authorized decision and a new separately assigned independent review.
  - **Corrective implementation (2026-08-25, Implementer `gabriel`, unprivileged; distinct from Architect `data` and Integrator `geordi`):** Claim `TODO-gabriel-0044-05-geordi-002-20260825T191700Z.md` (`owner_token: agent:gabriel:0044-05-geordi-002:20260825T191700Z`). Branch/worktree `0044-05-geordi-002` from exact blocked-review tip `6940900f67`. Product REF `5bd9d880ff89b81fce04cc5f893a07010638d52d` encodes profile/descriptor `allOf`/`if`/`then` cross-field constraints and schema/matcher agreement tests for F-0044-05-GEORDI-002. Validation: 21 tests OK; path-scoped `automation_safety` PASS; legacy digest unchanged. Does not edit verdict text, review reports, matcher, or result schema, and does not claim to clear the `[u]` records. No `Acceptance: ✓`.
  - **Integration verdict supersession — CLEARED (2026-08-25T21:27:23+02:00):** Superseding Integrator `geordi`; authority `agent-inbox:jean-luc→geordi:1787685806304-66071b55`, applying the repository owner's Alternative-A authorization already recorded in `agent-inbox:jean-luc→geordi:1787685001155-e6cde308`. Fresh independent accepted review REF `9fa61ec991f463792048d7ffe68ff9988577d584`, report `docs/campaign-evidence/0044-05/checkpoint-rereview-geordi-20260825-r2.md`, exact reviewed baseline `74d3a6fb90b79f5dac9fb26d22f78223f268617e`. `F-0044-05-GEORDI-001` and `F-0044-05-GEORDI-002` are closed; both prior `[u]` verdicts and rejected reviews remain append-only history and are superseded for this corrected baseline only. This record grants no Feature closure or broad activation.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `geordi` (Geordi La Forge, privileged Team Enterprise Integrator)
    - **Authority reference:** `agent-inbox:jean-luc→geordi:1787685806304-66071b55` plus recorded repository-owner conditional authorization `1787685001155-e6cde308`
    - **Accepted at:** `2026-08-25T21:27:23+02:00`
    - **Contract SHA-256:** `b52e21551d3d81ea690300727c6cf5a5e5dadc57ad1287354e783ba3a176262f`
    - **Work-product manifest SHA-256:** `b61c8151374d89f275efa804ec116c1cc0ec8a07dc7dda3f936b897475928cee`
    - **Prerequisite-acceptance SHA-256:** `eee2be5dbd8c9f2b57048e5144e56ee2329163f685ddcec70139ba9a0f257dcc`
    - **Review REF:** `9fa61ec991f463792048d7ffe68ff9988577d584`
    - **Review evidence SHA-256:** `dbc3ea26833b27e73466c7aca80eae16eabcdae772b91c1252f2c583e07386a3` (`docs/campaign-evidence/0044-05/checkpoint-rereview-geordi-20260825-r2.md`)

    - **Decision/source baseline:** `DEC-0044-025`; `RQ-CB-01` … `RQ-CB-03`; accepted `0044-04`; legacy `agent-capability@v1` remains unchanged.
    - **Deliverables:** `docs/campaign-evidence/0044-05/capability-matcher-architecture.md`, repaired prerequisite graph, exact schemas/matcher/result/CLI/rejection/test/resource/recovery contracts, and recorded Architect gate-scope support.
    - **Capability profile:** `privileged`; Architect; direct Git/text validation; cognitive `high`; token 12k–24k; context `large`; no network, credentials, secrets, or external effects.
    - **Integration review:** not mandatory. **No-checkpoint justification (architect):** defines a reviewed contract and performs no executable gate or external effect; parent `0044-05` is the immediate mandatory checkpoint.
    - **Implementation evidence:** `DEC-0044-025` is on `main@174b10078`; architecture and exact child contracts committed at `9854d2f18`; graph audit found 358 IDs, 758 prerequisite edges, zero missing endpoints, and zero cycles; `git diff --check` passed.
    - **Acceptance:** ✓
      - **Disposition:** `completed`
      - **Accepted by:** `geordi` (Geordi La Forge, privileged Team Enterprise Integrator)
      - **Authority reference:** `agent-inbox:jean-luc→geordi:1787685806304-66071b55`
      - **Accepted at:** `2026-08-25T21:27:23+02:00`
      - **Contract SHA-256:** `d06930d250143ad7c424bb58a1e3dd61685dfe052d7d6e6bc47174354bed4cfc`
      - **Work-product manifest SHA-256:** `8a0060f1a4aae22129a9abdc4e73682c2218050bc314d2b73eff80889fd19776`
      - **Prerequisite-acceptance SHA-256:** `02f19b138b8e9ae0d063d23cc8d5ce191ae37bc6151f7d4439fb12759ef616ad`
      - **Review REF:** `9fa61ec991f463792048d7ffe68ff9988577d584`
      - **Review evidence SHA-256:** `dbc3ea26833b27e73466c7aca80eae16eabcdae772b91c1252f2c583e07386a3`

    - **Write scope:** `issues/_schema/task-requirement-profile-v1.schema.json`; `issues/_schema/agent-capability-descriptor-v1.schema.json`; `issues/_schema/capability-match-result-v1.schema.json`; `_src/tools/capability_match.py`; `_src/tests/test_capability_match.py`; `_src/tests/fixtures/capability-match/`; own claim/bookkeeping only.
    - **Capability profile:** `unprivileged`; Implementer; direct Python/Git; cognitive `high`; token 16k–32k; context `large`; CPU 1, memory ≤1 GiB, focused suite ≤20 minutes; no network or credentials.
    - **Prohibitions:** No governance paths, legacy-schema mutation, activation, agent selection, Acceptance, integration review, or `main` advance.
    - **Integration review:** not mandatory. **No-checkpoint justification (architect):** executable remains unactivated and the parent mandatory checkpoint immediately reviews it together with adoption.
    - **Acceptance:** ✓
      - **Disposition:** `completed`
      - **Accepted by:** `geordi` (Geordi La Forge, privileged Team Enterprise Integrator)
      - **Authority reference:** `agent-inbox:jean-luc→geordi:1787685806304-66071b55`
      - **Accepted at:** `2026-08-25T21:27:23+02:00`
      - **Contract SHA-256:** `5b155fdc3033940b3a32308a6f193c814950a9bef2c180ec4e5575b5da3301bb`
      - **Work-product manifest SHA-256:** `b350aa31d37b1099ee95a7c6e9544378f306953269c0487d0152f1b81601647b`
      - **Prerequisite-acceptance SHA-256:** `fac220dc170584ff05bf9f5c14c658ef60a60dd4aff99f4e9dcd620ea6ca44ed`
      - **Review REF:** `9fa61ec991f463792048d7ffe68ff9988577d584`
      - **Review evidence SHA-256:** `dbc3ea26833b27e73466c7aca80eae16eabcdae772b91c1252f2c583e07386a3`

    - **Write scope:** `AGENTS.md`; `docs/pipeline/capability-matching.md`; `docs/pipeline/tools.md`; `docs/pipeline/README.md`; own governance coordination record only, on a branch cut from then-current `main`.
    - **Candidate topology:** Observe exact current `main` SHA `M` and exact assigned parent `0044-05` tip `P`; `P` must contain `.02` bookkeeping `79f279ffcbdacf3d275048ffbd0df70e966e9429` and Architect clarification `a222f7b32` by ancestry. Create the item-owned governance branch/worktree at `M`; merge `--no-ff P` as second parent before governance edits. This explicitly carries `.01`/`.02` product, claims, and the topology contract so tool and documentation can land atomically. Stop and obtain refreshed pins if either SHA differs; never merge documentation alone or silently widen the declared product scope.
    - **Required non-activation text:** “This pilot requirement becomes operative only when this governance commit and the bound `0044-05.02` product are both reachable from `main`; it does not activate repository-wide dispatch enforcement, grant authority, or credit historic dispatches.” The sentence appears in `AGENTS.md` and `docs/pipeline/capability-matching.md`.
    - **Capability profile:** `privileged`; Implementer only; direct Git/text validation; cognitive `medium-high`; token 10k–20k; context `medium`; CPU under 5 minutes; no network, secrets, external effects, Acceptance, or integration authority.
    - **Integration review:** not mandatory. **No-checkpoint justification (architect):** wires the tested mechanism only for the bounded pilot; parent `0044-05` reviews package composition before any broader activation.
    - **Acceptance:** ✓
      - **Disposition:** `completed`
      - **Accepted by:** `geordi` (Geordi La Forge, privileged Team Enterprise Integrator)
      - **Authority reference:** `agent-inbox:jean-luc→geordi:1787685806304-66071b55`
      - **Accepted at:** `2026-08-25T21:27:23+02:00`
      - **Contract SHA-256:** `dd5d51d12ed9b27694460c2560a0b5c1502533f7e0e2e4c55475cb15b38b9aea`
      - **Work-product manifest SHA-256:** `4377f9033db7b779ba0cea7b83fb1e4024b7fe56fb12e119f6c86d00b8628f72`
      - **Prerequisite-acceptance SHA-256:** `93b257c21798f3d9079b8e6288eb5a11d2969c14f79ddb3c6d8435862c0b600e`
      - **Review REF:** `9fa61ec991f463792048d7ffe68ff9988577d584`
      - **Review evidence SHA-256:** `dbc3ea26833b27e73466c7aca80eae16eabcdae772b91c1252f2c583e07386a3`

  - **Parent package completion:** After `.01`, `.02`, and `.03` are terminal, an implementation session distinct from the `.01` Architect verifies schema/tool/docs consistency, unchanged legacy bytes, current self-application evidence, absence of broad activation, and complete finding dispositions. Parent `0044-05` then retains its mandatory checkpoint; `0044-08` remains the sole terminal integrating Task.

## Acceptance criteria

- **AC-001** Pilot briefing input references the profile and result while preserving all existing mandatory dispatch fields and authority checks
- **AC-002** CLI, failure, recovery, non-authority boundary, legacy distinction, and no-grandfathering are documented
- **AC-003** no repository-wide dispatch gate is activated

## Definition of Done

Governance edits remain path-limited beyond the explicitly declared parent-history merge; validation proves product `2c563040563b350f26e6c85b0dccb8c211fdbdef`, all three schemas, tests, and exact non-activation text are present on the candidate; matcher tests and `git diff --check` pass. The candidate is handed to a separately assigned privileged Integrator for the complete parent `0044-05` mandatory checkpoint; broad activation remains exclusively `0044-08` after end-to-end evidence and user decisions.
