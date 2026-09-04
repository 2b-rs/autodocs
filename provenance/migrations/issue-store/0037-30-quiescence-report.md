# Task 0037-30 legacy quiescence and freeze barrier

Status: implementation-complete candidate; independently review before integration.

The final committed legacy source watermark is `c170c8f34831f3a28b6d4dab67c02c61e3dad53e` (tree `e36bc00daf0e9612ee2426c0314b0fa6cc02fcc9`), derived from canonical `main@258701d63624c4c04956b938ff5e18d30be077bd` plus this claim's preserved history. Every required `0037-43`, `0037-42`, and `0037-44` product and receipt named in the JSON report is an ancestor of that canonical baseline.

## Reconciliation verdict

- The only live autodocs repository claim at the freeze boundary is Data's exact `0037-30` award, `1788459170204-5a7d114a`; its carrying commit makes the claim terminal.
- Burnham's roster entry is a stale projection. The authoritative offer state for `1788439078629-c2119cbf` is `accepted`, and its two-path product commit `09d63be542` is on `main`.
- No issue-store claim file, `refs/autodocs/claims/*`, job ref, transaction ref, legacy `run.sh`, `.runner/` queue, or Task-ID-bound background process exists.
- All 412 tracked legacy claim files are retained. Their sorted path-and-content digest is `sha256:9a3473ab76dba99aa4fe08d678d956b1c42ecd32068d3c91df3116e4d31a69ab`.
- The root checkout has no tracked divergence. Two foreign worktrees have preserved unstaged non-backlog state: one generated fixture and one permitted `logs/agent-memory/` file. Neither is staged, overlaps this candidate, or changes `TODO.md`, `DONE.md`, or a claim file.
- Root-only untracked `.worktrees/` and `allowed_signers` paths are recorded but do not alter the committed watermark.

## Atomic freeze

The same candidate changes `agent-workflow.json` from the legacy v1 placeholder selector to digest-valid `agent-workflow-bootstrap@v2`, workflow `2.0.0`, authority epoch `legacy-frozen`, profile `legacy-lists`, phase `frozen`, and direct execution. Its selector digest is `sha256:49c844c34df6609f4bdec4b618bb5461db4e3848ef7336ca1e7f4a843c122188`; the bound canonical current instruction bundle digest is `sha256:0b49699622bf7c16f1af00736699155e47636f12a9f8d96201964ebaf8f542d1`.

This does not activate `issue-store-writable`, any dormant `claim.json`, or any `refs/autodocs/claims/*`. It forbids ordinary pickup and claim mutation until both `0037-40` activation/reference commits lift the freeze. Only the transaction-bound operators for `0037-31`, `0037-34.01`, `0037-32`, `0037-33`, and `0037-34.02` may proceed, without ordinary claims or item writes.

## Stale-client behavior and signature

The bootstrap doctor must accept the exact frozen selector and reject a client expecting the prior `legacy-writable` epoch with stable `AB017_EXPECTED_EPOCH`. The prior placeholder digest is separately retained as evidence and is rejected by `AB013_DIGEST_MISMATCH`.

The same-slot `I30-BLOCK-001` repair is bound to signed rejection `532e475a5404a6db34e03ea25c341c6316e7976e`. The rejected candidate `2099a1cccdf0e91d42191aedab619cbf6ed2ee55` produces `UNSUPPORTED-BUNDLE-PATH`; the repaired carrying commit must make the same canonical integration-policy command pass while preserving stale-epoch rejection and doctor readiness.

The JSON report carries an embedded SSH Ed25519 signature over its canonical payload with the `signature` member omitted, under namespace `autodocs-0037-30-quiescence-v1`. The carrying Git commit is also SSH-signed. Verification of either signature authenticates bytes and identity; it does not replace independent acceptance or the mandatory integration process.

## Recovery

Before integration, withhold or revert only this candidate. After integration, recovery must use the separately authorized frozen-window transaction and must never silently enable legacy or issue-store writes. Do not delete this branch, any preserved ref, or foreign worktree content as recovery.
