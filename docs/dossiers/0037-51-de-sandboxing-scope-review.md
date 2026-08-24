# Architect scope review — Feature 0037 future direct execution

## Review identity and immutable baseline

- **Review item:** `0037-51`
- **Architect:** `agent:data:0037-51:20260824T083513Z`
- **Role/capability:** Management-instantiated Architect; `privileged`
- **Authority:** `TODO.md`, Task `0037-51`, authority commit `a57582e6cdf60a2d5ba37d1af3ff3be7de3afe77`
- **Baseline:** `main@a57582e6cdf60a2d5ba37d1af3ff3be7de3afe77`
- **Decision candidate:** `DEC-0037-002` in `docs/dossiers/dec-0037-future-direct-execution.md`
- **Branch:** `review-0037-51-scope-data-20260824T083513Z`
- **Worktree:** `.review-worktrees/0037-51-scope-data-20260824T083513Z`
- **Write scope:** this review and the decision candidate only

## Boundary and current status

This is preparation under the cross-item gate-scope exception. It does not edit
`TODO.md`, `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `agent-workflow.json`,
`docs/pipeline/**`, runner code, selectors, production paths, Acceptance records,
integration checkpoints, `main`, or `DONE.md`. The review verdict remains
incomplete until the affected-item matrix, dependency rewiring, activation,
self-application, recovery, rollback, non-grandfathering, validation, and risk
analysis below are complete and checked against the pinned baseline.

## Initial classification rule

An item is a removal candidate only when its required outcome has no future
consumer after all agents gain direct Shell and Git access. An item is retained
when it defines issue-store data, provenance, authority, validation, privacy,
collision protection, deterministic generation, evidence, migration, cutover,
or recovery independent of the runner transport. A mixed item is rewritten so
the invariant remains and the runner envelope, action registry, host deployment,
or sandbox-only fixture is removed. Completed artifacts are never erased; their
future normative role is dispositioned explicitly.

## Preliminary affected groups

- **Remove/defer transport:** `0037-46`, `0037-46.01`, `0037-46.02`,
  `0037-47`, and open `0037-50.02`–`.05`; retire the runner-host activation and
  sandbox first-attempt qualification chain from future planning.
- **Historical only:** completed `0037-48`, `0037-45`, `0037-41`,
  `0037-50.01`, and completed Feature `0038` runner work remain immutable
  provenance; future consumers must not depend on their runner-specific parts.
- **Rewrite mixed contracts:** `0037-39`, `0037-42`, `0037-44`, `0037-21`,
  `0037-25`/`.01`, `0037-30`, `0037-32`, `0037-34.01`, `0037-33`,
  `0037-35.01`, and `0037-36` retain direct-execution validation, stale-client,
  authority, audit, cutover, rollback, and recovery semantics without runner
  actions or sandbox fixtures.
- **Retain core:** issue schema, lifecycle, claim, provenance, graph, privacy,
  deterministic generation, migration, audit, approval, and atomic authority
  switch work remains within Feature `0037` unless the final matrix identifies
  a transport-only criterion.

## Start evidence

`DEC-0037-002` was confirmed free against the pinned `main` baseline before this
branch was created. Repository mutation is confined to the two declared files.
The complete matrix and verdict will be added on this same branch before handoff.
