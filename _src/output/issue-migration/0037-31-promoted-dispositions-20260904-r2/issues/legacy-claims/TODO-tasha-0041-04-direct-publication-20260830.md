# Coordination claim — Task 0041-04 direct item-scoped publication

task_id: 0041-04
feature_id: 0041
process: Feature 0041 direct item-scoped publication implementation
owner: tasha
owner_token: agent:tasha:0041-04:1788079889737-376a6f6e
request_id: 1788079889737-376a6f6e
assignment_id: 1788079889737-376a6f6e
status: [x]
state: [x]
capability_class: unprivileged
execution_authority: direct local execution in this item-owned worktree and disposable local repositories only
startup_review: ["AGENTS.md", "SANDBOX.md", "docs/pipeline/roles/security-engineer.md", "docs/pipeline/core-rules.md", "TODO.md", "docs/dossiers/dec-0041-007-atomic-cutover-task-graph.md"]
branch: 0041-04-enterprise-implementer-20260830
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0041-04-enterprise-implementer-20260830
base_commit: 838904e70ff307cce3175ddd8fbc7a1527d276f8

## Atomic award and exact boundary

- Atomic award `1788079889737-376a6f6e`, due `2026-08-30T11:51:55Z`, assigns
  Tasha as unprivileged Implementer for the fresh current-lineage `0041-04`
  product.
- Exact write scope is `_src/tools/publish_item_branch.py`,
  `_src/tools/test_publish_item_branch.py`,
  `docs/pipeline/item-branch-publication.md`, and this claim.
- The offer-status projection also lists pre-authorized candidate claim paths
  for Odo and Chakotay/Torres. The execution wake permits only the winner's
  claim; those foreign paths are excluded from this claim and will not be
  mutated.
- Prohibited: historical `0041-04` implementation input; Acceptance;
  checkpoint or Feature/main integration; Feature closure; external
  publication; credentials; protected refs; Task `0041-05`; root cleanup;
  Management, release, waiver, or risk authority.

## Contract and plan

- Implement the current `TODO.md` `0041-04` contract and `DEC-0041-007`
  direct-execution path. Accepted `0037-51` and completed `0041-01` are
  prerequisites; their products are read-only inputs.
- Provide a stdlib Python interface with explicit repository, assigned item,
  source, target, remote, and expected-old inputs. Fail closed before push on
  noncanonical or protected targets, assignment mismatch, dirty/relevant-state
  ambiguity, stale/CAS-lost state, ambiguous remotes, non-fast-forward updates,
  and source/target identity mismatch. Never discover credentials or infer
  authority.
- Preserve canonical worktree bytes, support dry-run, and emit deterministic
  JSON outcome and recovery evidence. Test only against disposable local
  repositories, including success, every refusal, CAS race,
  interruption/retry, and idempotent already-published behavior.
- Run the focused suite, automation-safety validation, compilation, and
  `git diff --check`; retain exact evidence and commit product/test/document
  refs. No real remote push or protected-ref mutation is authorized.

## Next action

Pin prerequisite and architecture evidence, write red-first hermetic tests,
implement the smallest fail-closed publisher and registered documentation,
validate, and transition the exact candidate to review without self-acceptance.

## Review-ready product and evidence — 2026-08-30

- Product REF `610b0dae880aa80e0217fad810326e0a38681d9e`
  contains only the three authorized product/test/documentation paths. The
  prior claim-first REF is `748fcf80995857223941f0b2859f4344f32afd25`.
- Red-first baseline: `python3 -m unittest
  _src.tools.test_publish_item_branch` failed before implementation with
  `ModuleNotFoundError: No module named 'publish_item_branch'`.
- Exact committed-product validation:
  - `python3 -m unittest -v _src.tools.test_publish_item_branch`: 17/17 PASS
    in 49.947 seconds. Disposable local repositories cover success,
    absent-target creation, dry-run, protected/noncanonical/mismatched refs,
    missing/ambiguous remotes, malformed/stale expected objects, dirty state,
    non-fast-forward history, local and remote CAS races,
    interruption/retry, push rejection, idempotence, and canonical-worktree
    preservation.
  - `python3 -m py_compile _src/tools/publish_item_branch.py
    _src/tools/test_publish_item_branch.py`: PASS.
  - `python3 _src/tools/automation_safety.py --path
    _src/tools/publish_item_branch.py --json`: PASS; zero findings, zero
    unresolved criticals, and zero policy errors.
  - `git diff --check HEAD^ HEAD`: PASS; worktree clean at the product REF.
  - `python3 _src/tools/process_doc_doctor.py --json`: `ok: true`; no finding
    attributable to `docs/pipeline/item-branch-publication.md`. The global
    result retains two errors and 34 findings already outside this award.
- No network URL, external remote, credential, protected ref, project ref,
  canonical root, Acceptance, checkpoint, integration, release, or `0041-05`
  action was used or mutated. All publication tests used disposable local
  repositories under temporary directories.
- The atomic award excludes `TODO.md`; its authoritative `0041-04` marker
  therefore remains `[ ]`. This claim records the completed review candidate
  but does not invent Task bookkeeping, Acceptance, or integration authority.

## Handoff

Route product REF `610b0dae880aa80e0217fad810326e0a38681d9e` plus this
claim-only evidence commit to independent review. The coordinator/integrator
must separately pin current target state and use their own exact authority for
any Task bookkeeping or integration. Tasha does not self-review or publish the
candidate.
