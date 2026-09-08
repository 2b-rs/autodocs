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

## Closure and handoff

- `status: implementation-complete; coordination claim lease released after main integration`
- `decision_ref: 0ffac017ef05ef14dd6e622f94bc1580d3e4f1f5`
- `backlog_ref: b64076ea1791e9e8679428f35c6dd57f8c9f2f81`
- `identifier_repair: Datas conceptual 0037-46.02.01--.05 labels were a parser-invalid third ID level; intent is preserved as valid Task 0037-50 with Subtasks 0037-50.01--.05`
- `validation:`
  - `python3 _src/tools/process_doc_doctor.py --json`: exit 0, 0 errors; `DEC-0037-001` is referenced by `TODO.md`
  - `python3 _src/tools/legacy_task_doctor.py --json`: no findings for `0037-46.02` or `0037-50*`; repository-wide pre-existing totals improve from 449 errors/611 findings on base to 442 errors/604 findings
  - `git diff --check`: exit 0
  - each of `0037-50`, `.01`, `.02`, `.03`, `.04`, `.05` occurs exactly once as a Task header
- `handoff: after the governance branch is current on main, 0037-50.02 and 0037-50.03 are the first parallel-eligible implementation packages; each requires its own exact claim, item branch/worktree, and implementer distinct from data and geordi`

## Restart-recovery disposition — 2026-08-28

- `terminal: yes`; this coordination scope is complete and its lease remains released.
- `main evidence:` decision REF `0ffac017ef05ef14dd6e622f94bc1580d3e4f1f5` and later superseding execution-model REF `f3522aaaa80d851f3ba28744b08956a52eb63275` are ancestors of current `main@8948a602320c7c0781ed9a578a42b664dfd2eff4`.
- `current disposition:` Task `0037-46.02` is `[w]`; no corrective implementation or integration action remains under this owner token.
- `handoff:` downstream work was re-planned and completed under separate claims; this claim must not be resumed.

## Supervisor restart recovery revalidation — 2026-08-29

- `terminal: yes`; do not resume this governance token.
- `current evidence:` decision REF `0ffac017ef05ef14dd6e622f94bc1580d3e4f1f5` and superseding REF `f3522aaaa80d851f3ba28744b08956a52eb63275` remain ancestors of `main@26f34aa56ce6287424d5bcb9440cd394b47b60ad`; `0037-46.02` remains `[w]`.
- `handoff:` none under this token; every downstream disposition has separate ownership.
