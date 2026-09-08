# Claim: 0037-30 final legacy quiescence and freeze barrier

- item: `0037-30`
- owner: `data`
- owner_token: `agent:data:0037-30:1788459170204-5a7d114a`
- capability_class: `privileged`
- execution_authority: bounded direct-local cutover preparation and final legacy-frozen selector update
- assignment: implementation `1788459170204-5a7d114a`; same-slot integration rework `1788476723055-16a4829b` / award `1788477149166-e30d4051`
- branch: `0037-30-rework-i30-block-001-data-20260903`
- worktree: `/tmp/autodocs-worktrees/0037-30-rework-i30-block-001-data`
- base: `c170c8f34831f3a28b6d4dab67c02c61e3dad53e`
- write_scope: `agent-workflow.json`, `provenance/migrations/issue-store/0037-30-quiescence-report.json`, `provenance/migrations/issue-store/0037-30-quiescence-report.md`, `TODO-data-0037-30-quiescence-20260903.md`
- integration_reservation: Geordi, through parent assignment `1788476723055-16a4829b`
- state: `implementation_complete`

## Startup reconciliation

- Duplicate 0037-30 ownership was observed in the 2026-09-03T18:13Z roster and stopped mutation.
- Jadzia reported the duplicate Benjamin assignment cancelled; Benjamin re-announced idle at 2026-09-03T18:14:16Z with that disposition.
- The prior `0037-30` worktree is clean at `ae5caa30faf133f6cb1add3fa73ca34800454270` and changes only `TODO-benjamin-0037-30-20260903.md`; it remains preserved and is not merged.
- Resolved former live-session blocker: the 2026-09-03T18:21Z Burnham roster projection remained stale, but authoritative assignment `1788439078629-c2119cbf` is terminal `accepted` and product `09d63be542` is on `main`. It is recorded as a projection discrepancy rather than a live claim.
- Resolved former prerequisite-product blocker: canonical `main@258701d636` now carries `_src/tools/agent_bootstrap.py`, `.github/workflows/issue-policy.yml`, and `_src/tools/issue_recovery.py`, with exact `0037-43`/`0037-42`/`0037-44` receipts listed below. Supervisor released the hold, and the current branch merged that baseline at `c170c8f348` before the four-path mutation.
- The earlier absence report `1788460095583-68f0c20d` remains historical evidence only and no longer describes the current baseline.

## Duplicate assignment receipts

- `1788440467310-f2ef9fe2`: cancelled by receipt `1788440982889-e00742d1`.
- `1788459146574-d2a935f9`: cancelled by receipt `1788459246094-8b6fdefb` as a duplicate of Data's precise award.
- Benjamin reports zero active claims or leases on 0037-30 and re-announced idle at 2026-09-03T18:16:34Z.
- Data's unique live award `1788459170204-5a7d114a` was re-queried as `in_progress`.

## Resume and final reconciliation

- Supervisor released the hold in messages `1788476160970-76224b67` and `1788476339695-9643bf1c`; the assignment service separately resumed the same award.
- Exact receipts `867d12f6ac`, `147dd8f78b`, `5e87ab7b51`, `dcda143c8a`, `e6a9251b1a`, `e54ebbb41b`, and `258701d636` were verified as ancestors of canonical `main@258701d63624c4c04956b938ff5e18d30be077bd` before mutation.
- Current `main` was merged into this preserved branch, producing clean source watermark `c170c8f34831f3a28b6d4dab67c02c61e3dad53e` before the four-path freeze delta.
- Roster reported Burnham busy on award `1788439078629-c2119cbf`, but the authoritative offer query returned terminal state `accepted`; its product `09d63be542` is an ancestor of `main`. Messages `1788476241139-2028b79e` and `1788476241159-a9e8610a` requested correction of the stale projection.
- No issue-store claim files, claim/job/transaction refs, legacy singleton request, queue directory, or Task-ID-bound background process were found. The tracked root is clean. The complete worktree scan found no staged or uncommitted backlog file; two unstaged foreign non-backlog files are preserved in place and identified in the report.
- The report binds the final legacy watermark, all 412 tracked legacy claim files, selector, instruction/policy bundle digests, stale-client results, explicit non-activation boundary, and recovery rule.

## Completion boundary

The carrying commit changes only the four awarded paths, is SSH-signed, and transitions this claim to terminal implementation state. Data does not self-accept or self-integrate. Geordi retains the reserved independent integration slot through the same-slot parent assignment.

## Same-slot rework: I30-BLOCK-001

- Independent signed verdict `532e475a5404a6db34e03ea25c341c6316e7976e` rejected candidate `2099a1cccdf0e91d42191aedab619cbf6ed2ee55`: the canonical 0037-43 gate maps `legacy-frozen` to `docs/pipeline/agent-instructions/current/index.md`, while the candidate bound `legacy/index.md`.
- Atomic award `1788477149166-e30d4051` authorizes an additive four-path repair from canonical `main@258701d63624c4c04956b938ff5e18d30be077bd`; no root/main mutation, writable issue-store activation, import, backlog marker mutation, publication, or ref cleanup is authorized.
- This branch preserves the source watermark and prerequisite receipts, rebinds the selector and signed reports to the canonical current bundle, and returns a new signed candidate for fresh independent review.
- Product/report commit `ccf4807210ceddd6238a178a55f207b32a25e1dd` is SSH-signed and changes the same exact four target-relative paths. The canonical policy gate passes with `evaluated_files_count=4` and zero violations; the rejected `2099a1cccdf` control returns `UNSUPPORTED-BUNDLE-PATH`.
- Bootstrap doctor is `ready`; a pre-freeze client is rejected with `AB017_EXPECTED_EPOCH`; `_src/tests/test_agent_bootstrap.py` passes 17/17 and `_src/tests/test_issue_integration_policy.py` passes 8/8.
- Canonical report payload SHA-256 `6cf2819c93843294eeb9b8873be7a7ca986bc6905b167950d29019054c78603d`, embedded SSH signature, selector digest `49c844c34df6609f4bdec4b618bb5461db4e3848ef7336ca1e7f4a843c122188`, and current-bundle digest `0b49699622bf7c16f1af00736699155e47636f12a9f8d96201964ebaf8f542d1` verify.
