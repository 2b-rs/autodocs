# Claim — independent scope re-review R2, `DEC-0044-027`

- **owner_token:** `agent:seven:0044-12-scope-review-r2:20260826T140000Z-ff45c2ff`
- **capability_class:** `privileged`
- **role:** Architect, management-instantiated for this review only
- **assignment:** `jean-luc` `agent-inbox:1787751762460-6a7ad4b6`, re-pin `1787752344498-1d3842e6`; candidate notified by `saru` `1787752307989-3728a846`
- **branch/worktree:** `review-0044-12-scope-seven-r2-20260826` / `.worktrees/review-0044-12-scope-seven-r2-20260826`, cut from **current `main`** `059f7e326` as I committed in R1
- **candidate under review:** `2cf41dc908e1f34af699153179b85238418cf918`, record `docs/dossiers/dec-0044-027-policy-provenance-recording.md`, SHA-256 `74f083fe…27ae`, blob `8aa43f6c5d226a306a738b4f98eb58a5dd39fb74`
- **write scope:** `docs/dossiers/0044-12-gate-scope-review-r2.md` and this claim. Nothing else.
- **must not:** implement; edit any `DEC-`, policy, tool, or `TODO` marker; accept; integrate; advance `main`; move anything to `DONE.md`; push.
- **verdict:** `scope-ready-for-mutation`, subject to gates G1–G3.
- **R1 artifact:** `review-0044-12-scope-seven-20260826` @ `5ff5aae54` — **unchanged**, per jean-luc's hold, throughout.

## Measured, not inherited

Saru's cover mail asserted all six conditions closed and told me to test rather than inherit. I re-read the six conditions verbatim from `5ff5aae54` **before** opening the candidate, then measured each separately. Both digests and the blob ID reproduced; `DEC-0044-008` verified untouched by empty diff; all six CON-02 paths verified to exist.

- **C1 met in substance** (all twelve fields; `Review participation: none` + `No-review reason` is the permitted form, and its reason — that my authoring would collapse the distinctness this re-review needs — is correct). Placement on `main` becomes gate G1 rather than a finding, because the recording Architect is forbidden from integrating.
- **C2 met** — six enumerated paths, closing R1's F-2.
- **C3 met** — CON-04, dated 2026-08-21.
- **C4 met**, with G3: rollback correctly forbids the partial revert that leaves prose requiring trailers while the tool still passes them; but nothing requires the activation commit's identity to be recorded once it exists.
- **C5 met, and strongest.** The load-bearing detail I checked because it is where this could have failed: `DEC-0041-006` CON-05 keeps the `0041` rule non-operative until its own cutover, so a composition rule demanding Family B *now* would pre-activate `0041` through `0044-12`. It does not — Saru scoped the Family B predicate to **post-cutover** commits, so no overlap can arise before that cutover. Also verified `DEC-0041-006` carries no trailer-exclusivity clause, so the families can coexist. Open `0041` dependency named exactly (CON-07), not absorbed.
- **C6 met** as a recorded constraint on a future assignment, which is the most a record can do.

## Finding and consistency note

**F-R2-01:** `integration:repository-main` is not conforming — `integration:` takes a work-unit `<ID>`. Surplus and reach-neutral (`integration:0044-12`/`0044-08` already carry it), fixed in the candidate rather than by a correction event, since a record never on `main` is not published.

Consistency with my `DEC-0044-026-C001` verdict earlier today (`scope-not-ready` for the same grammatical class) is argued explicitly in §3 rather than left to be noticed: there the bad entry was the object of the correction event, changed reach onto another unit's start, and had an unused narrower option. None of the three holds here. Same rule, same reading of `<ID>`, different severity because the facts differ.

## Disconfirmed hypothesis, recorded

I expected `_src/tools/test_check_policy_provenance.py` to be a wrong path, since suites here normally live in `_src/tests/`. It exists exactly where CON-02 names it. Recorded because a reviewer's refuted suspicion is evidence too, and suppressing it would make the review look more prescient than it was.
