---
schema_version: "1.0"
id: "0041-02"
level: "task"
parent: "0041"
state: "open"
visibility: "internal"
prerequisites:
  - "0041-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1332"
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

PREREQ: 0041-02:0041-01 Specify the non-operative atomic-check-in contract and exact synchronous activation manifest. Claim: `TODO-beverly-0041-02-atomic-contract-20260830.md`; owner_token: `agent:beverly:0041-02:1788079620073-b1d511e4`. REF: `8d4ec720ebdf91289ef8bd7ebcbd693527393056`.

## Scope

- **Bookkeeping fix (2026-08-31, `belanna`, marker only, no content/scope change):** Marker was left `[ ]` after the reviewed candidate landed at `main f5763cf21e98066f7e932d50a2b0e9c5802550f9` (checkpoint review PASS, `docs/campaign-evidence/0041-02-checkpoint-belanna-20260830/review.md@94a681be1`). Beverly's own claim explicitly deferred this exact marker to "the separately assigned independent privileged 0041-02 checkpoint reviewer" (that reviewer was me) and named no `TODO.md` write scope of her own. Independently verified before this fix: all four declared deliverables (`docs/dossiers/0041-02-atomic-checkin-contract.md`, `docs/pipeline/fixtures/0041-02/atomic-cutover-manifest.json`, `docs/pipeline/fixtures/0041-02/README.md`, `TODO-beverly-0041-02-atomic-contract-20260830.md`) exist on current `main` and are unchanged since `8d4ec720eb`. This Task is explicitly non-operative (see its own "Architecture graph repair" note below and Acceptance criteria: "No operative consumer changes in this Task") — flipping this marker does not itself activate any authority document; activation remains `0041-06`'s sole synchronous responsibility per `DEC-0041-007`. No Acceptance credit added or implied.
  - **Hold — do not integrate (2026-08-25/26, Discovery Project Lead `michael`; visibility record, not a new checkpoint and not Task ownership):** Re-pinned onto `main` `d401aeb069371934ed349f5b59b9cae5051dbfbc` after the Culber preservation commit landed; the earlier hold candidate `d84a783e266936b3a0d6ae962836da81c7fd3c87` was based on `8a364e000` and is not an ancestor of this tip. Branch `0041-02` tip `8b1afb933f0f9029d09c2fd3e9660aad3a8fa9a3` is `[x]` on that branch only. Authoritative `main` still has this Task `[ ]`. Independent Architect verdict `scope-not-ready-for-mutation` is commit `1bc504e4bafbc21d23474cfdc3b6ec2eede1d23c` on `review-0041-02-scope-data-20260823T160421Z`, report `docs/dossiers/0041-02-gate-scope-review.md`. That review is not an ancestor of this `main` tip or of `8b1afb933f`. `0041-03`/`0041-04`/`0041-06` currently sit on historical `47fb026016`, not on `8b1afb933f` and not on this `main`; do not treat them as start-ready. Do not merge `8b1afb933f`. Lift only when a conforming `decision-record@v1` exists on current `main` and the Architect stop is superseded or explicitly waived by recorded Management authority. Does not overwrite claim `TODO-Gabriel-Keyla-0041-02-20260825T000800Z.md`. Does not change `Integration review: mandatory`.
  - **Architecture graph repair (2026-08-30, `DEC-0041-007`):** Reopened for current-main re-derivation. Historical `[x]` candidates remain append-only evidence and are prohibited implementation inputs. This Task now produces a non-operative shared contract/manifest; it does not activate authority documents or satisfy a successor through stale work.
  - **Requirements covered:** `RQ-CI-01` … `RQ-CI-05`.
  - **Context (finding H):** The two-commit closure is structurally fragile — the second commit depends on the first one's hash, so it can only be written afterwards, and nothing forces it. Four Tasks sit in exactly that state today: `0007-01`, `0037-37`, `0038-02` and `0038-18`. This removes the cause rather than monitoring it.
  - **Integration review:** **mandatory.** **Rationale (architect):** retained as the shared-interface checkpoint. Multiple packages consume this grammar/manifest; an ambiguity would propagate into governance and executable gates before `0041-06` can detect it. This checkpoint reviews a non-operative contract, not activation.
  - **Task contract (`feature-breakdown@v1`):**
    ```yaml
    task_id: "0041-02"
    feature_id: "0041"
    role: implementer
    architecture_decisions:
      - decision: "Produce non-operative atomic-checkin-contract@v1 and atomic-cutover-manifest@v1"
        derives_from:
          requirements: ["RQ-CI-01", "RQ-CI-02", "RQ-CI-03", "RQ-CI-04", "RQ-CI-05", "REQ-0041-02-RD-01", "REQ-0041-02-RD-02", "REQ-0041-02-RD-03", "REQ-0041-02-RD-04", "REQ-0041-02-RD-05", "REQ-0041-02-RD-06"]
          decision_records: ["DEC-0041-006", "DEC-0041-007"]
          existing_architecture: ["docs/dossiers/0041-02-current-main-rederivation.md@861d87b721c9b3dbb57612e1d84234c8575c2c3e"]
          repository_evidence: ["docs/dossiers/0041-02-blackout-supersession-scope-review.md@8ba8521b02c3e9c4674347a5731676365f331131"]
        authority_or_assumption: authority
    prerequisites:
      - task_id: "0041-01"
        derives_from: "completed clone/provisioning interface and original Feature baseline"
    planned_order:
      position: 1
      order: ["0041-02", "0041-03", "0041-06", "0041-05"]
      order_matters_because: "all completion consumers require one reviewed grammar before candidate preparation and synchronous activation"
    write_scope: ["docs/dossiers/0041-02-atomic-checkin-contract.md", "docs/pipeline/fixtures/0041-02/atomic-cutover-manifest.json", "docs/pipeline/fixtures/0041-02/README.md", "TODO-<owner>-0041-02-<request>.md"]
    test_scope:
      derives_from: ["trailer grammar", "consumer completeness", "migration and rollback invariants"]
      kind: integration
      evidence: "schema/duplicate/consumer-manifest validator, fixture cases, digest inventory, git diff --check"
    capability_profile:
      capability_class: unprivileged
      rights: ["read repository and history", "write declared non-operative paths", "commit on item branch"]
      data: ["current-main consumer bytes", "DEC and review refs", "no external data"]
      tools: ["Git", "stdlib Python", "repository validators"]
      execution_needs: direct
      cognitive_demand: high
      independence: "implementer is distinct from Architect Data and checkpoint Integrator; no Acceptance/integration authority"
    cognitive_estimate: {estimator: "cognitive-demand-estimator@v1", scope_breadth: high, reasoning_depth: high, context_volume: high, ambiguity: medium, verification_hardness: high}
    advisory_estimate: {tokens: "30k-55k", tests: "10-20 min", runtime_cpu: "low", planned_duration: "120-210 min", uncertainty: "20-35%", risk: high}
    branch: {parent: "0041", name: "0041-02", create: "pre-provision from current Feature/main governance baseline; never reuse historical 8b1afb933f"}
    ```

## Acceptance criteria

- **AC-001** Produce versioned `atomic-checkin-contract@v1` and `atomic-cutover-manifest@v1`. The contract defines exact single `Task-ID`/full-object-id `Base-Ref` grammar, duplicate/malformed/wrong-item/stale/non-ancestor failures, carrying-tree invariants, claim finalization, `[x]`/`[w]` semantics without self-reference, Acceptance ownership of implementation/review commit identities, historical/reopened-work migration, and error vocabulary. The manifest exhaustively names every normative, editing, transaction, diagnostic, hygiene, test, and matching-guidance consumer
- **AC-002** binds current blob digests and candidate outputs
- **AC-003** declares one activation ref advance, validation order, rollback set, and old-writer absence proof. Provide positive, negative, migration, and rollback examples. No operative consumer changes in this Task

## Definition of Done

Contract, manifest, examples, whole-consumer discovery evidence, and own claim are committed on a fresh current-main branch; schemas/digests validate; every `DEC-0041-006` consequence and Beverly blocker is mapped; the old two-commit rule remains byte-operative; historical candidates are not merged, copied, or represented as current work.
