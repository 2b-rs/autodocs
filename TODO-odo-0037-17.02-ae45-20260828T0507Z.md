# Claim: 0037-17.02 AE-4 + AE-5 follow-up (additive tests)

- **owner_token:** `agent:odo-0037-17.02-ae45-20260828:0037-17.02-ae45:20260828T0507Z`
- **mailbox:** `odo-0037-17.02-ae45-20260828`
- **persona:** Odo, unprivileged Programmer
- **capability_class:** unprivileged
- **execution_authority:** item-owned worktree; direct Git/tests; no land; no Acceptance
- **git author leak:** host `user.name`/`user.email` is `gabriel` / `gabriel@discovery.starfleet.network`. Persona is Odo; commits are authored by the Cursor user (same leak class as 17.01 AE-4). Do not treat git author as mailbox identity.
- **item:** 0037-17.02 AE-4+AE-5 follow-up (not a second product implementer)
- **branch:** `0037-17.02-ae45-odo-20260828`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/0037-17.02-ae45-odo-20260828`
- **base:** remesured `refs/heads/main` immediately before cut = `b5cbea435fa057cc6db383f05399953a00f78ed2` (matches dispatch pin). Did **not** cut from TODO REF `71189ce11`.
- **write scope:** `_src/tests/test_provenance_views.py`, this claim. `provenance_views.py` only if a committed failing test proves a product bug.
- **must not:** land; Acceptance; advance main; touch `test_provenance_store.py` / `provenance_store.py`; batch with 17.01 AE-4; merge 11.02 / `bdffd04e8` / `a4d9e8ac` / `063b9c04eb`; lift 0037-16 STOP; take 0037-28; Feature DONE.md; reuse Stamets/Culber tokens.
- **Stamets product:** do not overwrite TODO REF `71189ce11` / landed `8aed11563`. This claim is follow-up + note only.

## Trigger

Belanna review `2a44cb7a72897de1a26ff67034bb240eb4318862` INCONCLUSIVE (AWARD 1787886294922-2c7eb575). AE-4 gaps: PV-CORRUPT (malformed + non-object), PV-UNRESOLVABLE-ENDPOINT (empty-uri + non-dict), PV-RECONCILE failure (count + identity). AE-5: exhaustive 64 directed-edge subsets on 3 nodes for `detect_cycles`.

## Status

Implementation `[x]` on this follow-up branch (does not restamp TODO.md 17.02 REF).

- **product/REF:** `28eb2ba9ba4c19e4fba449ddcba4febe9837ebac`
- **`provenance_views.py` edited:** no
- **validation:** `python3 -m unittest _src.tests.test_provenance_views -v` (worktree cwd) → **15/15 OK** in 1.509s (8 prior + 6 AE-4 + 1 AE-5). AE-5 executed **64** graphs (`AE5_ENUMERATED_GRAPH_COUNT`), 0 Kahn-oracle mismatches; `walk_without_loops` unique-node for every start on each graph.
- **base vs then-current main:** left-right after product commit recorded in bookkeeping commit.
- **handover_to:** jadzia
- **handover_at:** 2026-08-29T12:14:00Z
- **handover:** Terminal state reached. Review and integration required. Handoff to Integrator (Jadzia) via `jadzia`.
