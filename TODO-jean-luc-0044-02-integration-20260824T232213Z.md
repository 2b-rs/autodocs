# Integration claim — Task 0044-02

- `owner_token`: `agent:jean-luc:0044-02-integration:20260824T232213Z`
- `item`: `0044-02`
- `role`: Project Lead / governance integrator
- `capability_class`: `privileged`
- `authority`: current user, 2026-08-25 — “ok. Aus dem Fehler lernen und weitermachen”; governance-main route in `AGENTS.md`
- `target_branch`: `main`
- `integration_branch`: `integrate-0044-02-jean-luc-20260825`
- `worktree`: `.worktrees/integrate-0044-02-jean-luc-20260825`
- `base_commit`: `b3fa32a6a2e5a87753971b67710517130d1f6379`
- `source_branch`: `0044-02`
- `source_tip`: `ec7b3cad3d57d7e1ee14c81808e24e42f1c376bc`
- `status`: integration preparation

## Contract

Integrate the already implementation-complete risk-integration procedure and its
bookkeeping onto current `main`. The Task carries an Architect no-checkpoint
justification, so no mandatory integration checkpoint is crossed. This activity
does not create Task Acceptance, change an Integration-review attribute, close
Feature `0044`, move `DONE.md`, push, or authorize an external effect.

The source implementation claim is
`TODO-william-ezra-20260823T192000Z-0044-02-20260823T192000Z.md`. Its bounded
candidate records substantive REF
`c9f0968e9765fa2eab765d85dab6c376cf314a99`; source-tip bookkeeping is
`ec7b3cad3d57d7e1ee14c81808e24e42f1c376bc`.

## Integration controls

- Run the root hard preflight and mandatory all-worktree hygiene check before
  source integration and again before advancing `main`.
- Use a real `--no-ff` merge for the foreign source branch and preserve current
  `main` changes during any line-wise reconciliation, especially `TODO.md`.
- Validate exact changed paths, `git diff --check`, the documentation checker,
  Task marker/REF consistency, source-tip ancestry, and a clean integration
  worktree before the root fast-forward.
