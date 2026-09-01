# 0041-03 — Acceptance-owned commit-reference transition (candidate)

**Status:** non-operative candidate for Task `0041-03`. Does not activate
consumers. `0041-06` owns synchronous assembly onto `main`.

**Bound contract:** `atomic-checkin-contract@v1`  
**Contract path:** `docs/dossiers/0041-02-atomic-checkin-contract.md`  
**Contract SHA-256:** `3cc470954cae2809ff4ef719fd87ef203dd2eb9585995f1e818bd86cb65f40a9`  
**Manifest SHA-256:** `fe132eafc1bdd709357b81670704d2363afdb1deeebe9adda7d276e75dd770f8`  
**0041-02 implementation REF (historical, still operative on main):** `8d4ec720ebdf91289ef8bd7ebcbd693527393056`  
**Candidate branch:** `0041-03-rederive-ash` from `main@9a2f29ec91`  
**Stale unused tip:** `refs/heads/0041-03` `a11b3dd51f` (not an ancestor of current main)

## Decision applied

Implementation `[x]`/`[w]` no longer requires a self-referential git `REF` or a
second implementation-bookkeeping commit. The carrying commit trailers
`Task-ID` and `Base-Ref` identify the Task and pre-substantive parent.
Acceptance retains a separate evidence commit and a path-isolated
`Acceptance: ✓` bookkeeping commit that pin:

- carrying commit and tree
- independent review-decision commit
- baseline, prerequisite closure, manifests, and digests
- review `REF` (required on the Acceptance record; optional only when a
  separately authorized waiver names the missing object)

`SANDBOX.md` and `PRIVILEGED.md` are aligned in this candidate, not deferred to
compatibility-only notes.

## Wording matrix

| ID | Path | Old obligation | New obligation | Neighbor |
| --- | --- | --- | --- | --- |
| M1 | `TODO.md` `[w]`/`[x]` bullets | disposition/substantive `REF` | trailers; no implementation `REF` | M2 header gate sentence |
| M2 | `TODO.md` `[x]`/`[w]` gate sentence | commit `REF` | `Task-ID`/`Base-Ref`; review `REF` only on Acceptance | M1; Acceptance header bullet unchanged (D) |
| M3 | `AGENTS.md` parent-package completion | `real REF` | deliverable/validation/evidence | M4 |
| M4 | `AGENTS.md` `[x]`/`[w]` meaning | real `REF` | carrying commit + trailers | M5 |
| M5 | `AGENTS.md` completion step 4–7 | hash-then-bookkeeping | single carrying tree | SANDBOX twin |
| M6 | `SANDBOX.md` runner completion | two-commit REF inject | carrying tree; historical bootstrap note | M5 |
| M7 | `PRIVILEGED.md` commits | hash then bookkeeping | carrying commit + trailers | M5 |
| M8 | `task-acceptance.md` package item 2 | substantive and bookkeeping commits | carrying commit; Acceptance pins review later | M9 |
| M9 | `task-acceptance.md` rendering | Review REF only | carrying + review-decision + review REF | RQ-REF-03 |
| M10 | `core-rules.md` commit identifiers | `REF: <id>` as commit/req mix | trailers for git identity; REQ ids remain | ASPICE traceability |

## Historical compatibility

Pre-activation `[x]`/`[w]` records that already name a git `REF` remain valid
under the contemporaneous contract (`atomic-checkin-contract@v1` §8). This
candidate does not rewrite them. Fixtures under
`docs/pipeline/fixtures/0041-03/` show old phrases that must stay green on
`main` and red on this candidate.

## Handoff to `0041-06`

Do not merge this branch to `main` except as part of the synchronous cutover.
Expected consumers: authority files in this tree plus doctors/editors listed in
`atomic-cutover-manifest@v1`.
