# Coordination claim — `0037-46.02` corrective governance

- `owner_token: agent:jean-luc:0037-46.02-governance:20260823T134915Z`
- `capability_class: privileged`
- `execution_authority: direct-local-execution`
- `process_role: Project Lead`
- `assignment: current user selected Variant A on 2026-08-23, authorizing the Data failover design to be recorded and its five corrective packages to be coordinated`
- `branch: 0037-46.02-governance-jean-luc-20260823T134915Z`
- `worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0037-46.02-governance-jean-luc-20260823T134915Z`
- `base: main@0c766950390557e32143732d2fb6026b8aea211b`
- `startup_review: root tracked tree and index clean; HEAD equals refs/heads/main; inbox clear; no DEC-0037 identifier present on main immediately before allocation`
- `write_scope:`
  - `docs/dossiers/dec-0037-runner-failover-gate.md`
  - `TODO.md` (`0037-46.02` corrective state and `.01`--`.05` packages only)
  - `TODO-jean-luc-0037-46.02-governance-20260823T134915Z.md`
- `architecture_evidence: arch-0037-46.02-remediation-data-20260823T130400Z@a2e9802026466d220f26af3ec78291e901979010; proposal content commit 164890ec3c9ccc670fd502ea8c351269be955683`
- `integration_review_evidence: review-0037-46.02-geordi-20260823@b57fa240859bac7a3ba3362680db1541c88ccb8c; rejected candidate 0d2088a6778820b83329fafe248f21b97d904654`
- `external_resources: none for this governance package`
- `must_not: implement the failover; deploy or mutate /tmp/runner-0037-46.02; accept work; clear Geordi's rejected verdict; cross the 0037-46.02 checkpoint; move Feature 0037 to DONE.md; push; touch the root checkout except the separately authorized final main merge`

## Purpose and next step

Record the Management selection as conforming `decision-record@v1`, reopen the rejected parent for corrective work without erasing its implementation history, add the five bounded packages from Datas proposal, validate governance/backlog structure, and integrate the governance branch to `main` only after the mandatory hygiene and root preflight pass.
