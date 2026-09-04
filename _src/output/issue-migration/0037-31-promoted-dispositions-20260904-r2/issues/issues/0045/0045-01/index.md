---
schema_version: "1.0"
id: "0045-01"
level: "task"
parent: "0045"
state: "open"
visibility: "internal"
prerequisites:
  - "1788"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:360"
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

(A/P0; fan-out A) Implement the navigable multilingual

## Scope

AUTOSAR Adaptive plus S-Core publication baseline.
  Claim: `DONE-lore-0045-01-1788255929330-d8ef0b05.md`; owner_token:
  `agent:lore:0045-01:1788255929330-d8ef0b05`.
  REF: `d3eb4e29a60b529933b0b0b6afe47fbcfc4e4561`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788261995744-e39a6e85` (Offer `1788261995744-e39a6e85` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T10:16:30Z`
    - **Contract SHA-256:** `9cbe87dfc33b7495b341c2c310468e82ef4e87dc7532d8ff5a329d5ecfec8614`
    - **Work-product manifest SHA-256:** `29fa2a0ebda68dfbf18c991c28c8bc983c27da259d287e07662c1998f828a2a9`
    - **Prerequisite-acceptance SHA-256:** `d6ebaa0f4d2045bc338f50675e1900356e5c811ceaf4458f4d2045bc338f506`
    - **Review REF:** `b053ddbc5a9b21f284e59c705796ebe30c459a3c`
  - **Task record:**
    `task_id: "0045-01"; feature_id: "0045"; role: implementer`
  - **Architecture decisions and sources:** Implement `REQ-0045-01`,
    `REQ-0045-02`, `REQ-0045-03`, and `REQ-0045-09` using the existing
    generator/index/site/view/export boundaries. `0019-13` is repository
    evidence for the two S-Core link-defect classes; it is incorporated in the
    next publication candidate without altering historic digests.
  - **Prerequisites:** `0045-00` is a hard start gate because this task consumes
    the approved shared interface baseline; `0019-13` is a hard producer edge
    because its link repairs must be present in the generated S-Core tree.
  - **Planned order:** `position: 2; order: [0045-00, 0045-01, 0045-02, 0045-03.01, 0045-03.02, 0045-03, 0045-04, 0045-05, 0045-06.01, 0045-06.02, 0045-06]`.
    It may execute in parallel with `0045-02` after `0045-00`; its immutable
    candidate is joined only at `0045-06`.
  - **Test scope:** `kind: end_to_end`, derived from navigation, multilingual,
    no-JS, link-integrity, and snapshot/digest risks. Evidence:
    `pytest -q _src/tests/test_generate_parallel_languages.py _src/tests/test_prepare_score_curation_export.py _src/tests/test_score_curation_views.py _src/tests/test_validate_parallel_links.py`
    plus a retained generation/validation report naming database snapshot,
    configured languages, index links, and output digests.
  - **Capability profile:** `capability_class=unprivileged; rights=["read repository and prerequisite candidates", "write declared autodocs paths", "run local generation and tests", "commit item candidate"]; data=["approved interface baseline", "authoritative database snapshot", "site language configuration", "0019-13 candidate"]; tools=["Git", "Python", "pytest", "autodocs generator/validator"]; execution_needs=direct; cognitive_demand=high; independence="implementer cannot accept, integrate, publish, or certify release"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=high ("index, generator, languages, views, export"); reasoning_depth=medium ("existing boundaries with link repair"); context_volume=high ("full-tree multilingual output"); ambiguity=low ("approved baseline and product target are explicit"); verification_hardness=high ("complete navigation/digest/no-JS proof")`. Peak `high` determines the class.
  - **Branch:** `parent: "0045"; name: "0045-01"; create: "pre-provision from parent; do not create from a stale checkout"`.
  - **Exhaustive write scope (autodocs repository):**
    `_src/generate.py`, `_src/sources/pages/index.json`, `_src/site.json`,
    `_src/tools/score_curation_views.py`,
    `_src/tools/prepare_score_curation_export.py`,
    `_src/tests/test_generate_parallel_languages.py`,
    `_src/tests/test_prepare_score_curation_export.py`,
    `_src/tests/test_score_curation_views.py`, and
    `_src/tests/test_validate_parallel_links.py`.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0045-01/02/03/09, approved shared baseline, and existing generator/index/site contracts", checked_at: "2026-08-31T20:01:01Z", recorded_by: "agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17" }`
  - **Review rationale:** generated publication inputs require independent
    completeness and link-integrity review before terminal integration.
    committed on the task branch; the stated end-to-end suite passes; no
    publication target or source-history `main` is advanced.

## Acceptance criteria

- **AC-001** The root index reaches both trees
- **AC-002** both derive from the same latest authoritative snapshot in every configured language
- **AC-003** the two `0019-13` link classes are fixed
- **AC-004** output works without JavaScript
- **AC-005** and database, language, output, and digest evidence is retained

## Definition of Done

Scoped source/tests and the retained report are
