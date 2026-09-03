# 0037-42 final R9 independent review

- Assignment: `1788473992724-44b807cd`
- Reviewer/Integrator: `geordi` (privileged; independent of implementer `worf`)
- Baseline: `main@867d12f6ac95301a6fa1aaf53649f778feb7c353`
- Rejected carrying candidate: `5d0af9431e4b91e5a76fde882d566741514044d3`
- Exact repair candidate: `147dd8f78b28a6dd33a7c96faaeb063f57b23eaa`
- Signed rejection: `9ee684a14264958fa6d1e5c022a262df4a842f6a`
- Binding: `temporary_local_no_push`

## Static and provenance checks

- The repair candidate is a direct child of the exact assigned baseline and its Worf SSH signature verifies.
- Its aggregate diff contains exactly the five awarded implementation paths: Worf's claim and completion records, the boundary tool and test, and the R7 dossier.
- `git diff --check` exits `0`.
- The R7 dossier at `docs/dossiers/0037-42-final-r7-integration-20260903.md` is exact blob `073d6ffb6141b785a7fcdc8d43fcd83c1f449025`, byte-identical to signed reviewer ref `337ef9254cb17835edc65ed70fce72c616e0f58f`. The implementer-authored replacement from rejected R8 is absent.
- The prior R8 rejection commit has a valid Geordi SSH signature.

## Independent red/green probes

Historical red behavior was reproduced on the rejected candidates:

- `I42-BLOCK-001`: the documented strict doctor `--repo` interface is rejected as unrecognized by candidate `63c6b52cff`.
- `I42-BLOCK-002`: candidate `f55039ae5e` silently accepts missing and bogus protocols with exit `0`; its CLI has no client-handshake boundary.
- `I42-BLOCK-003`: candidate `7008a2926c` exposes protocol negotiation only; every `--client-json` tuple probe fails at argument parsing instead of validating the client contract.

The exact repair candidate independently passes the complete boundary matrix:

| Probe | Human/JSON result |
|---|---|
| Missing protocol or client input | exit `1`, stable `MISSING-ARGUMENTS` rejection |
| Unsupported protocol | exit `1`, stable `UNSUPPORTED-PROTOCOL-VERSION` rejection |
| Missing/empty client identity | exit `1`, stable `MISSING-CLIENT-NAME` rejection |
| `bogus` or short `1` client version | exit `1`, stable `INVALID-CLIENT-VERSION` rejection |
| Unsupported major `999` on current protocol | exit `1`, stable `INCOMPATIBLE-CLIENT-PROTOCOL-TUPLE` rejection |
| Client major `1` on legacy protocol | exit `1`, stable `INCOMPATIBLE-CLIENT-PROTOCOL-TUPLE` rejection |
| Major `1` on current or maintenance protocol | exit `0`, accepted |
| Major `0` on legacy protocol | exit `0`, accepted with deprecation guidance |

The canonical strict doctor remains compatible and unchanged: the exact documented interface executes, reports the repository's existing legacy selector as `stale-or-invalid`, and exits `2` with ordered `AB012`, `AB013`, and `AB021` findings. This is the expected fail-closed result for the unactivated placeholder selector; the repair does not alter selector state or activate a workflow.

## Suites and review verdict

- `python3 -m pytest -q _src/tests/test_agent_bootstrap*.py`: `23 passed`, exit `0`.
- `python3 test.py`: `Ran 100 tests`, `OK`, exit `0`.
- Exact repair-candidate hygiene: PASS across `146` registered worktrees.

## Verdict: PASS

The exact signed repair candidate closes `I42-BLOCK-004` while preserving the complete reviewer-authored R7 record. It also substantively closes the earlier fail-open protocol/client findings without modifying the canonical strict doctor or selector state.

This PASS authorizes only the assigned guarded local integration sequence. It is not Task Acceptance, push, publication, remote configuration, selector activation, Feature closure, or authority to delete or rewrite refs. Root integration and its receipt remain pending.
