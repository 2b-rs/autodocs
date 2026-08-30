# Coordination claim — Task 0041-04 direct item-scoped publication

task_id: 0041-04
feature_id: 0041
process: Feature 0041 direct item-scoped publication implementation
owner: tasha
owner_token: agent:tasha:0041-04:1788079889737-376a6f6e
request_id: 1788079889737-376a6f6e
assignment_id: 1788079889737-376a6f6e
status: [p]
state: [p]
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
