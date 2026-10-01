# 0044-13 containment result R2

Verified at `2026-08-28T21:30:49Z` under `DEC-0044-031` after the source activation and sanitized supervisor restart. This is containment evidence only; it is not implementation, review, Acceptance, or Feature integration for Task `0044-13`.

## Neutralized activation

- Active generator source: `agent-inbox/main@f081d27645ab97bd48f92b5274d82eea4f202864`.
- Focused source validation before activation: `python3 -m unittest test_supervisor.GitIdentityTests` passed `9/9` in `12.094s`; `python3 -m py_compile supervisor.py test_supervisor.py` and `git diff --check` passed.
- Active supervisor: PID `82065`, start `2026-08-28T21:28:08Z`, profile generation `1ed89f10-c7be-4562-baae-99dc8a92fe1d` loaded at `2026-08-28T21:28:09Z` with reason `restart`.
- Fresh Jean-Luc process environment: `GIT_CONFIG_COUNT=7`; exactly `GIT_CONFIG_KEY_0..6` and `GIT_CONFIG_VALUE_0..6`; no higher key/value variables; `GIT_CONFIG_GLOBAL` points to the generated Jean-Luc config and `GIT_CONFIG_NOSYSTEM=1`.
- `git config --show-origin --get-all core.hooksPath` returned no value.
- Generated Git configurations: `50`; files containing `hooksPath`: `0`; SHA-256 of the sorted per-file digest listing: `a8ab66d05d5ce9532045e2636d2ef09669aeaa0ef66e397cf0ee3014959eb709`.

## Preserved evidence and repository pins

- Live hook remains present and unchanged at SHA-256 `a4393fc5aeb2986bb191c6c6aac34e844869bb67ff604e0225b9e35efb4ff9aa`.
- Retained transaction log remains unchanged at `11` lines and SHA-256 `e2224059c60364191b830476b35b720eb7ef034256288c132e6e6183f1883a5a`.
- Pre-neutralization archive remains unchanged at SHA-256 `5df39837e671e826aff34c954852a4027ca41729a065c378f4bf5a4702a5a0ec`; archive extraction independently reproduced the pinned hook and log digests before activation.
- `autodocs/main` remains `7892e40db1f5d208a85c0e13fd90288969b32d3f`.
- Comparing all `675` refs with the archived pre-neutralization snapshot yields exactly one changed ref: item-owned `refs/heads/0044-13-containment-execution-r2-jean-luc-20260828`, from snapshot base `7892e40db1f5d208a85c0e13fd90288969b32d3f` to the containment evidence chain. Every other ref, including `refs/heads/main`, is byte-identical to the snapshot mapping.

## Disposition

Both supervisor-generated activation sources are absent for fresh processes; the retained hook bytes are unreachable through those sources and remain preserved. The fleet hold remains in force until the expressly assigned Integrator independently verifies this evidence and the exact candidate, integrates the containment record if fit, and reports the release checkpoint result.
