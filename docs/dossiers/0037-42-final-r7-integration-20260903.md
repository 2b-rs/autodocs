# 0037-42 final R7 independent review

- Assignment: `1788472433977-e0bf2b4c`
- Reviewer/Integrator: `geordi` (privileged, independent of implementer `worf`)
- Baseline: `main@867d12f6ac95301a6fa1aaf53649f778feb7c353`
- Candidate: `7008a2926c158a15ef1af0b991e11dca1e03e272`
- Verdict: **REJECTED — I42-BLOCK-003**
- Root integration: **not attempted**

## Static gates

- Candidate parent is the exact assigned baseline; ancestry check passed.
- Candidate principal SSH signature verified against `allowed_signers`.
- Candidate changes exactly the four awarded implementer paths: Worf's claim and completion records, `_src/tools/agent_bootstrap_boundary.py`, and `_src/tests/test_agent_bootstrap_boundary.py`.
- The repair added protocol presence/support checks and basic client name/version presence checks.

## Independent probes

The rejected predecessor `f55039ae5e` reproduced red: missing and bogus protocol CLI invocations returned zero, while `{}` and a bogus client/protocol tuple were accepted.

The repair improved protocol behavior:

| Probe | Observed |
|---|---|
| CLI missing `--protocol-version` | exit 2 |
| unsupported protocol, human mode | exit 1 |
| unsupported protocol, JSON mode | exit 1 with `status: rejected` |
| empty client name | rejected (`MISSING-CLIENT-NAME`) |

The assigned client-version and compatibility-tuple boundary remains fail-open:

| Client version / protocol | Observed |
|---|---|
| `bogus` / `2025-06-18` | accepted |
| `1` / `2025-06-18` | accepted |
| `999.0.0` / `2025-06-18` | accepted |
| `0.1.0` / `2024-11-05` | accepted |

`validate_client_bootstrap` only rejects an absent version or the literal `0.0.0`; it neither parses the version nor defines/enforces supported client-version ranges or client/protocol compatibility tuples. The six new tests likewise contain no malformed-version, unsupported-version, or incompatible-tuple assertion. The CLI exposes protocol negotiation only, so it cannot demonstrate human/JSON rejection for client tuple failures.

## Required rework

Define the supported client-version contract and its compatibility relation to protocol versions, reject malformed/unsupported versions and incompatible tuples with stable diagnostics, expose the client handshake through a testable human/JSON CLI boundary (or bind an already-authoritative interface), and add negative tests for each case. The focused and full suites must then be rerun substantively.

Because this acceptance-gate finding is decisive, review stopped before the full suite, integration hygiene, root preflight, or merge. `main` remained at the assigned baseline throughout.
