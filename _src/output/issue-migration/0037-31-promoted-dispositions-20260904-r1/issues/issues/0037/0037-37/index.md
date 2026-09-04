---
schema_version: "1.0"
id: "0037-37"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-01"
  - "0037-02"
  - "0037-03"
  - "0037-04"
  - "0037-05"
  - "0037-06"
  - "0037-41"
  - "0037-45"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2091"
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

PREREQ: 0037-37:0037-01, 0037-37:0037-02, 0037-37:0037-03, 0037-37:0037-04, 0037-37:0037-05, 0037-37:0037-06, 0037-37:0037-41, 0037-37:0037-45 Assemble and semantically audit the complete pre-implementation architecture baseline. REF: 927da0690a964249f7ca0b83719601b849be801f

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0037-37-Commit)`). Abgenommene Baseline `927da0690a964249f7ca0b83719601b849be801f`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. Manifest mit 17 Contract-Digests, alle 17 selbst neu berechnet und exakt bestätigt.
  - **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-37-20260816-1443.md`, `owner_token: agent:perplexity:0037-37:0037-37-20260816-1443`, request ID `0037-37-20260816-1443`, `base_commit: pending-discovery`. All prerequisite architecture tasks are terminal.
  - **Bookkeeping repair (2026-08-21, Seven, autonomous backlog repair per `AGENTS.md`):** The substantive deliverable was already committed at `927da0690a964249f7ca0b83719601b849be801f` ("docs: assemble issue store architecture review package", 2026-08-16) — all 11 files the Definition of Done names exist and are unchanged since. The claim's own runner history explicitly records why the marker was never flipped: "no commit or TODO bookkeeping mutation was performed" after the implementation request. Independently re-verified before closing: all 17 contract digests in `docs/pipeline/issue-store-review-package.json` recompute correctly against their named paths at the package's `base_commit`; `docs/pipeline/issue-store-findings.md` records one `CLOSED-LOCAL` pair plus `BLOCKING-EXTERNAL-001` naming `0037-49` — exactly the DoD's allowed terminal state ("all audit findings are closed or explicitly blocking"), and the Task's own text forbids marking `[u]` for this reason. `0037-49` (downstream, `[d]`) already independently documents and owns that same external blocker; it is not a reason to leave this Task open. Discovered while investigating Feature `0038`'s `0038-16.01`, which lists this Task as a prerequisite.

## Acceptance criteria

- **AC-001** Create `docs/pipeline/issue-store-architecture.md`, `docs/pipeline/issue-store-review-package.json`, and `docs/pipeline/issue-store-findings.md`
- **AC-002** verify and incorporate every package-local contract/artifact manifest produced by prerequisite architecture Tasks—including `docs/pipeline/issue-item-v1-package.json` from `0037-02`—and enumerate exact contract/schema/policy/fixture/producer paths and SHA-256 digests without requiring prerequisites to modify this downstream package
- **AC-003** split the backlog again before approval whenever one implementation item spans more than four independently writable production modules, more than eight producer call sites, more than one ownership/write scope, or cannot be validated by one focused bounded test command
- **AC-004** name exact Python/`ruamel.yaml`/Node/Graphviz versions, tracked fonts, locale/timezone/environment, SVG normalization, every public key fingerprint/principal/role (never private key material), public projection and localized-payload fields, i18n failure policy, claim limitations, agent instruction/authority epochs, stale-client policy, runner request/action/resource/credential profiles and proof that no implementation Task assumes privileged execution, approval/cutover ref topology and bootstrap trust root, graph stages, DAG writers, migration comparison rules, fixed test seeds/budgets/rule-coverage thresholds, residual risks, and all implementation Task mappings. Commit `issues/_policy/audit-profiles.json` and a review-ready `issues/_policy/feature-0037-execution-profile.json` skeleton with mandatory commands/actions, fixed high-risk cases, deterministic seed/sampling algorithm, minimum strata/counts, runner resource bounds, and failure thresholds. Run an executability audit proving every implementation item has bounded inputs, outputs, failure behavior, tests, start gates, and no unresolved “optional”, “if approved”, or agent-selected architecture

## Definition of Done

The versioned review package is internally consistent and all audit findings are closed or explicitly blocking; `issues/_policy/authorities.json`, `issues/_policy/allowed_signers`, `issues/_policy/audit-profiles.json`, `issues/_policy/translation-review-profile.json`, `issues/_schema/issue-approval-v1.schema.json`, `docs/pipeline/issue-approval.md`, and a stdlib-only `_src/tools/verify_issue_approval_bootstrap.py` are review-ready. The bootstrap procedure reads policy from the exact package commit, verifies the approval-ref commit/record/digests with `git verify-commit`, and requires repository-owner fingerprint confirmation through a recorded independent channel before trusting that first policy. Do not mark `[u]`: this Task is agentic preparation.
