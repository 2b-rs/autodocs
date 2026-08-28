# 0044-13 retained-main post-hoc audit

Audit performed on 2026-08-28/29 by Geordi in the expressly assigned privileged
Integrator role under Management option A (`decision-1787953120979-d603985f`,
message `1787954030389-49e2d37a`, offer `1787954209187-be92ace7`). This is a
bounded containment audit. It is not Task `0044-13` implementation, Acceptance,
Feature integration, or fleet-release authority.

## Verdict

`VALIDATED_POST_HOC` — the retained containment state at
`main@4fd50a81408fda30d7657ff57a87bbdd6ccd9b54` is internally consistent with
the preserved evidence and passed both current hygiene gates. The original
pre-landing preflight cannot be recreated after the landing and is therefore
not claimed, inferred, or retroactively converted into a pass. The fleet HARD
STOP remains in force until separately released by its authority.

## Retained-main delta

The audit worktree and `refs/heads/main` both resolved to the exact assigned SHA
before audit mutation. The range
`02166e2a1e829f0e5dd59ff6fbdff59864665ab6..4fd50a81408fda30d7657ff57a87bbdd6ccd9b54`
contains exactly these four linear commits:

1. `4493cf5b62c0e2e00bc3a6a644a7f1b788920fa1` — final pre-neutralization evidence.
2. `6ffe721ae9e9d239127c8a40456ef06ea4ada17e` — supervisor-activation checkpoint.
3. `f85d0eb5e44dd1a3480aced245b7c9c500742f91` — generated-profile regeneration.
4. `4fd50a81408fda30d7657ff57a87bbdd6ccd9b54` — sanitized-restart result.

The range changes exactly four paths:

- `TODO-jean-luc-0044-13-containment-20260828T194500Z-01a049e4.md`
- `docs/campaign-evidence/0044-13/containment-evidence-20260828/containment-result-r2.md`
- `docs/campaign-evidence/0044-13/containment-evidence-20260828/pre-neutralization-files-r2.tar`
- `docs/campaign-evidence/0044-13/containment-evidence-20260828/pre-neutralization-inventory-r2.md`

Those path bytes equal the previously inspected containment candidate
`082030e6c89948036cf3d4b9a9c450d83454d7cd`. No extra retained path was found.

## Independent live-state checks

- Active `agent-inbox/main` resolved to
  `f081d27645ab97bd48f92b5274d82eea4f202864`.
- The running supervisor process was PID `82065`, executing
  `/Users/tobias.anton/devel/agent-inbox/supervisor.py restart --gui ...`.
- The fresh Geordi environment had `GIT_CONFIG_COUNT=7`, exactly
  `GIT_CONFIG_KEY_0..6` and `GIT_CONFIG_VALUE_0..6`, no higher numbered entries,
  `GIT_CONFIG_NOSYSTEM=1`, and the generated global profile path.
- `git config --show-origin --get-all core.hooksPath` returned no value.
- Generated profiles: `50`; profiles containing `hooksPath`: `0`; SHA-256 of the
  sorted per-file digest listing:
  `a8ab66d05d5ce9532045e2636d2ef09669aeaa0ef66e397cf0ee3014959eb709`.
- Preserved live hook SHA-256:
  `a4393fc5aeb2986bb191c6c6aac34e844869bb67ff604e0225b9e35efb4ff9aa`.
- Retained transaction log: `11` lines; SHA-256:
  `e2224059c60364191b830476b35b720eb7ef034256288c132e6e6183f1883a5a`.
- Pending transaction regular-file count: `0`.
- Preserved archive SHA-256:
  `5df39837e671e826aff34c954852a4027ca41729a065c378f4bf5a4702a5a0ec`.

The source merge `f081d276` changes exactly `supervisor.py` and
`test_supervisor.py` relative to its second parent, the then-current baseline
`3d4f75f2f9a299e06eb9b967286597d157ec87b6`. The containment claim's phrase
"first parent/current baseline" is a parent-number wording error: its first
parent is the prepared containment line `027b43f5...`; the two-path assertion is
true against the second parent/current baseline. This audit preserves that
distinction rather than silently repeating the incorrect parent label.

## Current-state hygiene

Before this audit's claim/evidence commits, both required read-only checks ran
against the retained `main` state and returned exit `0`:

- Candidate-aware hygiene:
  `python3 _src/tools/check_integration_hygiene.py --repo /Users/tobias.anton/devel/autodocs/.worktrees/0044-13-posthoc-audit-geordi-20260828 --candidate-ref 4fd50a81408fda30d7657ff57a87bbdd6ccd9b54`
  — `PASS`, `290` registered worktrees.
- Root preflight:
  `python3 _src/tools/check_integration_hygiene.py --repo /Users/tobias.anton/devel/autodocs --root-preflight`
  — `PASS`, `290` registered worktrees.

These results establish the observable current hygiene baseline. They do not
reconstruct the state immediately before the already-retained landing. That
historical preflight is permanently non-recreatable because refs, indexes,
worktrees, processes, and filesystem state have advanced; current success is
not evidence that the missing contemporaneous gate ran or would have passed.

## Disposition

The current retained containment baseline is fit as a post-hoc audited state.
No hook, generated profile, log, pending transaction, supervisor process,
foreign worktree, TODO/DONE marker, or `main` ref was mutated by this audit.
Any fleet release or later `0044-13` implementation/Acceptance requires its own
express authority and checkpoint.
