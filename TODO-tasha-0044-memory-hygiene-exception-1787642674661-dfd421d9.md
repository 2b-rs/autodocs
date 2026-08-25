# Coordination claim — DEC-0044-021 hygiene implementation

item: 0044-memory-hygiene-exception
owner: tasha
owner_token: agent:tasha:0044-memory-hygiene-exception:1787642674661-dfd421d9
status: [x]
capability_class: unprivileged
execution_authority: direct local execution in this item-owned worktree only
branch: 0044-memory-hygiene-exception-tasha-1787642674661-dfd421d9
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0044-memory-hygiene-exception-tasha-1787642674661-dfd421d9
base_commit: 15dd2f4bf7e56703e6de6abc87951e3e3affa33c
substantive_ref: 9f905ceeb349b903574215b395334415ffe04abd

## Assignment and authority

- Corrected Programmer assignment: agent-inbox message `1787642674661-dfd421d9`; the earlier incorrect `privileged` capability label is withdrawn and grants no authority.
- Governing decision: `DEC-0044-021` at `29d37e7496bf485acf9d6cc7f1a696f27962c951`.
- Supporting independent Architect scope review: `90b1298890ecb72a82951e461396bcba63fcb60a`.
- Both are ancestors of the assigned exact base and were verified before mutation.

## Exact write scope

- `TODO-tasha-0044-memory-hygiene-exception-1787642674661-dfd421d9.md`
- `_src/tools/check_integration_hygiene.py`
- `_src/tools/test_check_integration_hygiene.py`
- the smallest shared executable helper under `_src/tools/` required for one classifier implementation
- `AGENTS.md`
- `docs/pipeline/branch-workflow.md`
- `docs/pipeline/tools.md`
- `docs/pipeline/process-roles.md`
- `docs/pipeline/roles/project-lead.md`
- `docs/pipeline/roles/integrator.md`
- `docs/pipeline/role_artifact_matrix.csv`
- only minimal directly required tests or documentation within the assigned scope

No root checkout path, foreign claim, or `0019-13` product path is writable under this claim.

## Required behavior

- Use one NUL-safe executable classifier for the checker, machine-runnable hard root preflight, candidate-overlap guard, and immediate post-merge verification.
- Recognize only the exact case-sensitive child prefix `logs/agent-memory/` with at least one child component.
- Except only a non-empty set of exclusively unstaged tracked Memory paths. Empty state is clean, not an exception. Staged Memory, mixed Memory/non-Memory, other hygiene findings, unavailable/indeterminate state, and exit `2` remain blocking.
- Before merge, intersect the candidate changed-path set with the currently allowed dirty Memory paths and block every overlap, including equal bytes.
- Replace the raw prose-only `git diff --quiet` root recipe with the shared machine command. Do not parse newline-delimited Git path output.
- Preserve Project Lead as coordinator only; the expressly assigned privileged Integrator owns hygiene execution, verdict, post-merge verification, and the authorized `main` merge.

## Negative and recovery evidence

Hermetic tests cover exclusive Memory divergence, empty state, the directory itself, prefix lookalikes, case variation, newline-bearing paths, mixed divergence, staged Memory, equal/different overlap, other findings, exit `2`, post-merge classification, and role/document consistency. Validation includes focused and relevant full tests, `py_compile`, automation safety, `git diff --check`, and process-document validation.

## Boundaries and simultaneous-claim justification

This implementation claim is disjoint from owned Task `0019-13`, which remains stopped before product mutation pending integration of its separate reviewed governance record. This claim touches only the listed hygiene implementation/governance projection paths; `0019-13` touches S-Core renderer/exporter/test/evidence paths. Holding both claims is explicit and does not combine their authority, evidence, or completion.

Tasha does not perform Acceptance, integration review, checkpoint crossing, root cleanup/write, `main` advance, `git update-ref`, push, publication, waiver, risk acceptance, or release. Geordi reviews and integrates separately under a fresh exact assignment.

## Next step

Implementation is complete and committed. Route the exact substantive ref and
bookkeeping tip to Geordi for the separately assigned review/integration; this
claim grants no Acceptance or integration authority.

## Completion evidence

- Added the shared byte-path classifier in `_src/tools/integration_hygiene_policy.py`
  and applied it to the checker, hard root preflight, candidate-overlap guard,
  tests, and operative role/process documentation.
- Focused tests: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
  test_check_integration_hygiene -v` — PASS, 17/17.
- Syntax: `python3 -m py_compile check_integration_hygiene.py
  integration_hygiene_policy.py test_check_integration_hygiene.py` — PASS.
- Focused automation-safety scan of the three implementation/test files — PASS;
  3 files scanned, 0 findings, 0 policy errors, 0 unresolved critical findings.
- `git diff --check` — PASS.
- `process_doc_doctor --strict` — candidate 29 findings with the same single
  pre-existing `DOC001` error as main (main baseline: 32 findings); no new error.
- Live full-worktree scan from the item worktree with `--candidate-ref HEAD
  --json` — exit 0, `ok: true`, no findings; observed root
  `main@668dd3d5cf1a9f8081b8de5e15301a0031f46c11` clean.
- Live hard root preflight against the canonical root with `--root-preflight
  --candidate-ref HEAD --json` — exit 0, `ok: true`, no findings at the same
  clean main tip.
