---
schema_version: "1.0"
id: "0045-06"
level: "task"
parent: "0045"
state: "closed"
visibility: "internal"
prerequisites:
  - "1788"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:684"
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

(F/P0; exactly one terminal parent) Integrate the

## Scope

canonical per-repository candidates and record the authorized cross-repository
  source/publication proof without using one assignment to write both
  repositories.
  Claim: `DONE-obrien-0045-06-20260901.md`; owner_token:
  `agent:obrien:0045-06:1788269285465-a61aff7c`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788269285465-a61aff7c` (Offer `1788269285465-a61aff7c` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T13:29:00Z`
  - **Task record:**
    `task_id: "0045-06"; feature_id: "0045"; role: integrator`
  - **Integration review:** mandatory. **Rationale (provisional; Architect
    confirmation is an acceptance requirement of `0045-00`):** this is the
    Feature's only terminal join and it gates/records evidence for canonical
    integration and an external public release. This requirements record does not claim
    Architect authority; the approved shared baseline must bind the current
    Architect checkpoint decision before implementation starts.
  - **Architecture decisions and sources:** Terminal aggregation for
    `REQ-0045-02`, `REQ-0045-07`, `REQ-0045-08`, `REQ-0045-09`,
    `REQ-0045-11`, `REQ-0045-12`, and `REQ-0045-16`. Publication output never
    becomes source-history `main`. The parent consumes immutable agent-inbox
    recipe and autodocs apply/generation candidates plus canonical integration
    receipts; it does not rewrite their product files.
  - **Prerequisites:** `0045-06.01` produces the agent-inbox
    apply/publish-contract candidate; `0045-06.02` produces the autodocs
    transactional apply/generation/publication candidate; `0045-01` supplies
    the publication baseline; `0045-05` the Curator decision; `0033-16.01` the
    Feature 0033 terminal integration/review floor. All are hard terminal-join
    edges. `0033-16` alone is insufficient.
  - **Planned order:** `position: 11; order: [0045-00, 0045-01, 0045-02, 0045-03.01, 0045-03.02, 0045-03, 0045-04, 0045-05, 0045-06.01, 0045-06.02, 0045-06]`. This is the only
    terminal node and no Feature 0045 node may succeed it.
  - **Test scope:** `kind: end_to_end`, derived from cross-repository canonical
    ancestry, authority, restart, release, and digest risks. Evidence: verify
    each candidate is an ancestor of its repository's canonical source main;
    rerun the focused Subtask suites; retain an authorized two-round-trip report
    proving feedback→proposal and decision→publication, exact database commit,
    configured languages, digest manifest, publication receipt,
    stale/duplicate/conflict, retryable/terminal failure, and recovery.
  - **Capability profile:** `capability_class=privileged; rights=["read both canonical repositories and exact accepted decision", "write one declared autodocs terminal-evidence path", "run integration/release validation", "integrate or publish only under separately verified exact authority"]; data=["canonical agent-inbox receipt", "canonical autodocs receipt", "accepted decision authority proof", "database/publication digest ledger", "authorized publication target handle"]; tools=["Git", "integration hygiene checker", "pytest", "autodocs validator", "publication script"]; execution_needs=direct; cognitive_demand=critical; independence="Integrator/release authority must be current and independent of proposal author and Curator; implementers may not self-accept, self-integrate, or self-release"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=critical ("two canonical repositories and publication target"); reasoning_depth=critical ("ancestry, authority, retry, and release state"); context_volume=high ("all predecessor receipts/digests"); ambiguity=medium ("target fixed by exact release authority"); verification_hardness=critical ("false proof or wrong public release is difficult to reverse")`. Peak `critical` determines the class.
  - **Branch:** `parent: "0045"; name: "0045-06"; create: "pre-provision from parent in the autodocs repository; merge every done-but-unintegrated autodocs prerequisite; do not create from a stale checkout"`.
  - **Exhaustive write scope (autodocs repository):**
    `docs/campaign-evidence/0045-06/terminal-integration.md` (new). Generated
    publication output is limited to the separately authorized publication
    branch/repository; the parent has no agent-inbox write scope.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0045-02/07/08/09/11/12/16, per-repository 0045-06.01/.02 candidates, publication 0045-01, Curator decision 0045-05, and 0033-16.01 floor", checked_at: "2026-08-31T20:01:01Z", recorded_by: "agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17" }`
  - **Review rationale:** mandatory independent Feature integration/release
    review over both canonical receipts and the external publication proof.
    common-dir identities, candidate commits, main-before/main-after and
    ancestor proofs, exact authority, two-cycle evidence, database/publication
    receipts, digest manifest, and recovery proof; source integration and
    external publication were performed only by separately authorized roles.

    accepted-decision→apply/publication typed-recipe producer and immutable
    handoff schema.
    Claim: `agent-inbox:DONE-quark-0045-06.01-20260901.md`; owner_token:
    `agent:quark:0045-06.01:1788268005826-89ca343d`.
    - **Acceptance:** ✓
      - **Disposition:** `completed`
      - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
      - **Authority reference:** `agent-inbox:jadzia→obrien:1788268477907-a2f9dcc9` (Offer `1788268477907-a2f9dcc9` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
      - **Accepted at:** `2026-09-01T13:16:00Z`
    - **Task record:**
      `task_id: "0045-06.01"; feature_id: "0045"; role: implementer`
    - **Architecture decisions and sources:** Implement the recipe-producer side
      of `REQ-0045-04`, `REQ-0045-05`, `REQ-0045-07`, `REQ-0045-08`,
      `REQ-0045-10`, `REQ-0045-11`, `REQ-0045-12`, and `REQ-0045-16` under
      the approved selector binding. The recipe runs only after the arrival
      offer and awarded Project Lead branch selection, performs full decision
      trust/binding validation, and emits a typed command/result contract; it
      grants no Curator, integration, or release authority.
    - **Prerequisites:** `0045-05` produces the durable Curator-decision arrival
      envelope and immutable autodocs contract;
      `0045-02` produces the selector-compatible offer/assignment contract.
      Both are hard start gates.
    - **Planned order:** `position: 9; order: [0045-00, 0045-01, 0045-02, 0045-03.01, 0045-03.02, 0045-03, 0045-04, 0045-05, 0045-06.01, 0045-06.02, 0045-06]`. It produces the
      immutable handoff consumed by `0045-06.02`.
    - **Test scope:** `kind: integration`, derived from arrival-before-offer,
      accepted-decision, award, selector, apply/publish idempotence, restart,
      and failure risks.
      Evidence: `pytest -q test_apply_publish_recipe.py` with unauthorized,
      unawarded, rejected, revision-requested, stale, same-key replay, conflict,
      partial result, retry ancestry, selector mismatch, and restart fixtures.
    - **Capability profile:** `capability_class=unprivileged; rights=["read agent-inbox assignment and durable decision contracts", "write declared agent-inbox recipe/schema/test paths", "run local fixture tests", "commit candidate without database or external publication effects"]; data=["accepted-decision fixtures", "approved selector binding", "assignment fixtures", "idempotence/retry ledger fixtures"]; tools=["Git", "Python", "pytest", "agent-inbox assignment Runner test harness"]; execution_needs=direct; cognitive_demand=critical; independence="recipe implementer is not Curator, Integrator, or release authority and cannot execute real database/publication effects"`.
    - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=high ("decision, assignment, apply and publication handoff"); reasoning_depth=critical ("authority and partial-effect state"); context_volume=medium ("bounded schemas/fixtures"); ambiguity=low ("selector and decision contracts are pinned"); verification_hardness=critical ("false command can target canonical data or public release")`. Peak `critical` determines the class.
    - **Branch:** `parent: "agent-inbox:0045-04 exact candidate ref"; name: "0045-06.01"; create: "create in the agent-inbox repository from the pinned 0045-04 candidate (and therefore 0045-03.01/0045-02 ancestry); consume the autodocs 0045-05 decision contract only by immutable ref/digest"`.
    - **Exhaustive write scope (agent-inbox repository):**
      `recipes/apply_publish.py` (new),
      `schemas/apply-publish-contract-v1.json` (new), and
      `test_apply_publish_recipe.py` (new).
    - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: "agent-inbox/main@071c1cb1365ec90a9c4f70748275e615b9df475d", basis: "REQ-0045-04/05/07/08/10/11/12/16, ancestral 0045-02 and 0045-03.01 agent-inbox candidates, and the immutable autodocs 0045-05 decision contract", checked_at: "2026-08-31T20:52:11Z", recorded_by: "agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17" }`
    - **Review rationale:** independent authority/idempotence review prevents a
      logical recipe from becoming an implicit release grant.
      agent-inbox; immutable candidate/ref and schema digest are handed to
      `0045-06.02`; no real database or publication effect occurred.

    transactionally apply the accepted proposal, regenerate/validate the
    complete multilingual site, and prepare the publication candidate.
    Claim: `DONE-quark-0045-06.02-20260901.md`; owner_token:
    `agent:quark:0045-06.02:1788268764515-a10c6abf`.
    - **Acceptance:** ✓
      - **Disposition:** `completed`
      - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
      - **Authority reference:** `agent-inbox:jadzia→obrien:1788269022686-16455a38` (Offer `1788269022686-16455a38` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
      - **Accepted at:** `2026-09-01T13:26:00Z`
    - **Task record:**
      `task_id: "0045-06.02"; feature_id: "0045"; role: implementer`
    - **Architecture decisions and sources:** Implement the autodocs consumer
      side of `REQ-0045-02`, `REQ-0045-07`, `REQ-0045-09`,
      `REQ-0045-11`, and `REQ-0045-12` through existing
      `score_curation.py` apply/publish, `curation_flags.py` completion,
      generator/validator, and `publish_public_site.sh` boundaries. It prepares
      a candidate and receipt; the terminal parent owns canonical
      integration/release proof.
    - **Prerequisites:** `0045-06.01` produces the immutable authorized handoff;
      `0045-01` the publication baseline; `0045-05` the Curator decision;
      `0033-16.01` the Feature 0033 terminal integration/review floor. All are
      hard start gates.
    - **Planned order:** `position: 10; order: [0045-00, 0045-01, 0045-02, 0045-03.01, 0045-03.02, 0045-03, 0045-04, 0045-05, 0045-06.01, 0045-06.02, 0045-06]`. It precedes the
      terminal parent and performs no canonical integration by itself.
    - **Test scope:** `kind: end_to_end`, derived from transactional database,
      full-tree generation, validation, digest, publication-candidate, retry,
      and recovery risks. Evidence:
      `pytest -q _src/tests/test_apply_publish_contract.py _src/tests/test_score_curation.py _src/tests/test_generate_parallel_languages.py _src/tests/test_validate_parallel_links.py _src/tests/test_publish_scripts.py`
      plus a retained fixture report for current/stale decision, rollback,
      partial generation, digest mismatch, all configured languages,
      same-key replay/conflict, retry, and terminal failure.
    - **Capability profile:** `capability_class=privileged; rights=["read immutable handoff and predecessor candidates", "write declared autodocs contract/database/generation/validation/test paths", "run local transactional and publication-fixture tests", "commit candidate without canonical integration or external release"]; data=["accepted decision and authority proof", "authoritative database", "configured languages", "publication-target fixture", "handoff and retry ledger"]; tools=["Git", "Python", "pytest", "autodocs curation/generator/validator", "publication script in fixture mode"]; execution_needs=direct; cognitive_demand=critical; independence="implementer cannot self-accept, integrate canonical main, or perform external release; terminal Integrator/release authority remains distinct"`.
    - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=critical ("database, generator, languages, validation, publication candidate"); reasoning_depth=critical ("transaction, rollback, and partial-effect recovery"); context_volume=high ("records, decision, site, and digest ledger"); ambiguity=medium ("accepted record set is decision-bound"); verification_hardness=critical ("canonical data corruption or false publication proof")`. Peak `critical` determines the class.
    - **Branch:** `parent: "0045-06"; name: "0045-06.02"; create: "pre-provision from parent in the autodocs repository; merge done prerequisite candidates; do not create from a stale checkout"`.
    - **Exhaustive write scope (autodocs repository):**
      `_src/tools/apply_publish_contract.py` (new),
      `_src/tools/score_curation.py`, `_src/tools/curation_flags.py`,
      `_src/spec/records/**`, `_src/data/curation-items.json`,
      `_src/generate.py`, `_src/validate.py`,
      `_src/tools/publish_public_site.sh`,
      `_src/tests/test_apply_publish_contract.py` (new),
      `_src/tests/test_score_curation.py`,
      `_src/tests/test_generate_parallel_languages.py`,
      `_src/tests/test_validate_parallel_links.py`, and
      `_src/tests/test_publish_scripts.py`.
    - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0045-02/07/09/11/12, immutable 0045-06.01 handoff, publication 0045-01, Curator decision 0045-05, and 0033-16.01 floor", checked_at: "2026-08-31T20:01:01Z", recorded_by: "agent:beverly:score-feedback-loop-requirements-20260831:1788205915982-a0f32d17" }`
    - **Review rationale:** independent transactional/data/publication-candidate
      review before the terminal Integrator can cross canonical or external
      boundaries.
      generator/validator/script changes, tests, fixture receipts, digest
      manifest, and recovery proof are committed in autodocs; immutable
      candidate/ref is handed to terminal parent `0045-06`.

## Acceptance criteria

- **AC-001** A conforming accepted current handoff is applied transactionally and committed on the candidate branch
- **AC-002** rollback is complete on failure
- **AC-003** live state and full AUTOSAR plus S-Core output derive from that exact database commit in every configured language
- **AC-004** validation and digest manifest agree
- **AC-005** the typed result is complete
- **AC-006** no external publication or canonical integration is claimed

## Definition of Done

Contract consumer, database candidate,
