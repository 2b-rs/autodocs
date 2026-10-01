# Campaign Evidence Summary: 0037-46.02 (Runner-Queue Activation & Rollback)

- **Feature/Task**: `0037-46.02` (Queue aktivieren, Legacy-Singleton stilllegen)
- **Branch**: `0037-46.02`
- **Base Commit**: `8a9898837e3f4ff5e6f6ed5c5683133381a3d910`
- **Working Tree**: `/tmp/runner-0037-46.02`
- **Date**: 2026-08-23
- **Executing Agent**: `q` (sandboxed runtime)
- **Supervising Agent**: `kathryn`

## 1. Execution Log Summary & Artifact Integrity

All qualification runs were executed via the legacy runner loop in `/tmp/runner-0037-46.02` under parameterless strict guardrails ensuring `HEAD == EXPECTED_BASE` and zero working tree mutations (`CHANGED 0`).

| Request ID | Phase / Purpose | Exit Code | Verdict | HEAD Checked | Proof File | SHA-256 Digest |
|---|---|---|---|---|---|---|
| `req-0037-46.02-health-1` | Runner host baseline health check | `0` | PASS | `8a9898837` | `status.porcelain` | `9fc3889cdde7f5d3a2bf29d313722831b2fb57b3c5cdefa0e132e1717782299e` |
| `req-0037-46.02-rollback-1` | 3-gate rollback restoration proof | `0` | PASS | `8a9898837` | `prove_rollback.json` | `d0ebad745d8bba07917c6e4ddc9e12d20ba7ff766a24cc0eff28a8fcbe133fce` |
| `req-0037-46.02-commit-1` | Rollback gates integration commit verification | `0` | PASS | `8a9898837` | `prove_health.json`<br>`prove_post_switch.json`<br>`prove_exclusive_mutation.json` | `ead807fe564c03310527e4c6cb6e1f1a744a0eb35dab3d27540197e2a4e310ea`<br>`f6bea51c3522e1030149679286a1edabbd745cbc7cf80c65e817fc143a829364`<br>`0454172e18b885ca76571f97d31bcfdcc4d1227b9ec34ebc1e68d27769b50778` |
| `req-0037-46.02-roundtrip-1` | Request/result dispatch roundtrip | `0` | PASS | `8a9898837` | `roundtrip_verdict.json` | `69fabf5b25149ddbfe2a73dfb746e31fe95d9ea0bdbe796ed13d7316cb41d2a3` |
| `req-0037-46.02-concurrency-2` | Concurrent disjoint agent execution & scope isolation | `0` | PASS | `8a9898837` | `concurrency_proof.json` | `a1f948f2fa15c32490df1bbf412e84c98f869150162548cb918392576b5e0ee0` |
| `req-0037-46.02-recovery-1` | Crash recovery, lease reclaim & mutation isolation | `0` | PASS | `8a9898837` | `recovery_proof.json` | `f1dfddbae988b2804b0f8a6cc70682779a2559c06acb4243486c59c222314697` |

## 2. Detailed Qualification Highlights

### A. Concurrency & Scope Isolation (`concurrency-2`)
- **Agents**: `fixture-alpha` and `fixture-beta`.
- **Disjoint Scopes**: `_src/spec/alpha.json` vs `_src/spec/beta.json`.
- **Concurrency Mechanism**: Synchronized simultaneously across worker threads using `threading.Barrier(2)`.
- **Timing Evidence**:
  - `beta` arrived at barrier `2026-08-23T08:26:24.727405+00:00`, started `2026-08-23T08:26:24.727490+00:00`, finished `2026-08-23T08:26:24.742517+00:00`.
  - `alpha` arrived at barrier `2026-08-23T08:26:24.727349+00:00`, started `2026-08-23T08:26:24.727517+00:00`, finished `2026-08-23T08:26:24.742480+00:00`.
  - Direct execution overlap: strictly concurrent execution (~15ms duration concurrently executed).
  - Both requests succeeded independently with unique result digests.

### B. Crash Recovery & Mutation Isolation (`recovery-1`)
- **Stale Lease Reclamation**: Proved that expired leases (simulating a crashed worker) are automatically reclaimed upon startup/execution.
- **Governance Scope Guard**: Attempted unprivileged write to governance files (`AGENTS.md`) was rejected with finding `RD-GOVERNANCE-SCOPE`.
- **Scope Collision Guard**: Overlapping write scopes on `_src/tools/foo.py` between concurrent requests were detected and rejected with `RD-SCOPE-COLLISION`.

### C. 3-Gate Rollback Mechanism (`rollback-1` / `commit-1`)
- Implemented and verified in `_src/tools/runner_protocol_rollback.py` and unit tests (`Ran 48 tests ... OK`).
- Restores `agent-workflow.json` bytes and prior epoch cleanly upon any activation or verification failure.
