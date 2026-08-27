# Historical Acceptance validity/impact — `0039-04` then `0039-01`

**Reviewer:** `paul` (privileged; assignment `1787758630130-34f2f515`)
**Pinned assignment baseline:** `9ccd99b25ccadffa951b0f184e174dd4fa2b8621`
**Review branch:** `review-0039-04-01-acceptance-line-paul-20260826T154500Z`
**Outcomes below are impact/validity decisions, not new `Acceptance: ✓` credit and not Acceptance of Seven's current work.**

Contract bytes use the same rule as `docs/pipeline/task-acceptance.md` / the 0038-33/34 serialization: UTF-8 exact complete Task block from `TODO.md`, header through the byte before the next same-level Task header, rstrip, one terminating LF. Inputs: `digests/contract-*.utf8`.

Current-main policy notice used (jean-luc `1787758485464-bb202fa1`): `docs/pipeline/feature-breakdown.md` product `942a648fd7e0623a76027aeb0c4c2aa8cf2683d9` is reachable from this pin; Task `0044-06` is `[x]` without `Acceptance: ✓` and that does not block ordinary successor implementation.

---

## Bottom-up order

`0039-01` PREREQ `0039-04`. Decide `0039-04` first.

Transitive prerequisites of `0039-04` on the pin: none. Empty prerequisite-acceptance set is consistent with published SHA-256 `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` (SHA-256 of `[]`).

---

## Verdict A — `0039-04` historical acceptance is **not current**

**Disposition of this impact review:** `not-current` (historical record remains append-only on branches `0039` / `0039-01`; it supplies **no** current `Acceptance: ✓` credit on `main`).

### What the historical record is

At `dfd4bf2717df48700b10adc6f16a65425656b731` (`acceptance(0039-04): record independent acceptance`, author `tobias.anton`, 2026-08-19):

- `**Acceptance:** ✓`
- Disposition `completed`
- Accepted by `Linus Riker 20260819T125003Z` at `2026-08-19T13:04:19Z`
- Contract SHA-256 `f72a93f3a0f88ec03fd4e857d8c4c20944219819d8d7853717bf9e165f750eaa`
- Work-product manifest SHA-256 `0c8392ae2ce8524777a8aa83551e9f6cc9d96f2e133c63297451bc4678b0131e`
- Prerequisite-acceptance SHA-256 `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`
- Review REF `c5aa797054c745df54fbcd6c8d40cfff58377e33`

That commit is reachable from branches `0039`, `0039-01`, `0039-02`, `0039-03`. It is **not** an ancestor of assignment pin `9ccd99b` or of live `main` `714fbdd40`. Independently: `git merge-base --is-ancestor dfd4bf271 9ccd99b` exits 1.

On the pin, `TODO.md` for `0039-04` is `[x]` with implementation completion text that still says the Task awaits independent privileged acceptance and that **no** `Acceptance: ✓` credit is recorded. Main never carried the bookkeeping commit.

### Contract vs work products

Independently recomputed: the `0039-04` Task block **without** the later `Acceptance: ✓` stanza at `dfd4bf271` hashes to `f72a93f3a0f88ec03fd4e857d8c4c20944219819d8d7853717bf9e165f750eaa` (matches the published contract digest). The same digest is the full Task block at pin `9ccd99b` (2783 bytes; `digests/contract-0039-04-pin-9ccd99b25cca.utf8`). The **TODO.md Task contract on current main matches the historically accepted contract.**

Work-product bytes bound by `0039-04` DoD (normative process in pipeline/agent instructions) **do not** match the acceptance-commit tree:

| Path | SHA-256 at `dfd4bf271` (16 hex) | SHA-256 at `9ccd99b` (16 hex) |
|---|---|---|
| `docs/pipeline/task-acceptance.md` | `f333c4ec09b89a67…` (22410 bytes) | `e340b2b1ec7579b7…` (29511 bytes) |
| `AGENTS.md` | `e725504476a1d2a5…` (29355 bytes) | `4cca9f28316563f0…` (66223 bytes) |
| `SANDBOX.md` | `06b9eb6f7e2b1483…` (23046 bytes) | `4871c705af9f77bf…` (26826 bytes) |
| `PRIVILEGED.md` | `53c5484b36111885…` (unchanged) | `53c5484b36111885…` |

`task-acceptance.md` §Invalidation: acceptance is invalidated (not deleted) on accepted work-product byte or semantic interface change, and on relevant policy/authority epoch change. An unrelated `HEAD` advance alone does not invalidate. Here the process documents that **are** the `0039-04` work products changed on `main` after the stranded acceptance tree.

### Why this is not inconclusive

Reachability, pin `TODO.md` (no `✓`), and work-product drift are independently measured. Missing evidence that would have been needed to **re-accept** current-main `0039-04` (fresh work-product manifest, independent validation rerun of the 2026-08-17 suite against `9ccd99b`) is **out of this assignment**; this assignment is historical validity/impact, not a new Acceptance of current-main `0039-04`.

### Next lifecycle step (`0039-04`)

Do not treat branch-only `✓` as current credit on `main`. Do not rewrite or delete `dfd4bf271`. When Feature `0039` is integrated, carry the historical record append-only. Current-main `0039-04` still needs a **separately assigned** independent privileged Acceptance of the **current** work-product baseline if Feature closure or a prerequisite-closed Acceptance batch requires current `✓`. This session does not perform that Acceptance.

---

## Verdict B — `0039-01` historical acceptance is **not current** and requires **additive supersession** pending Seven's delta

**Disposition of this impact review:** `not-current` / **additive invalidation-or-supersession required** relative to the current contract. Historical `✓` remains append-only on branch `0039-01`. This is **not** Acceptance of `778c8db6e5` and **not** a `TODO.md` bookkeeping mutation on `main`.

### Named line ending vs actual acceptance commits

Assignment named `130e8f8dc154cde50fa05c7f9ef1e9572088ad17` (`bookkeeping(0039-01): record REC-20 corrective completion`). Independently: at that commit `0039-01` is `[x]` after Shannon's `AR-0039-01-002` repair, and the text **explicitly asserts no `Acceptance: ✓` credit**. So `130e8f8dc` is the implementation-complete line **before** acceptance bookkeeping, not the acceptance commit itself.

Actual acceptance on that line (ancestors of Seven's tip; **not** ancestors of `9ccd99b`):

- `afce1a779a747a29fc6958d076fde15c9ca3fadb` — `acceptance(0039-01): record independent acceptance` (Niklaus Riker; Review REF first published as invalid expansion of `5c7589379`)
- `f268f5610d18b09da15bb1edcd12a78664126529` — `acceptance(0039-01): correct review reference` to reachable `5c75893795ab7d8a7edd1a8583c26f627ace3662`

Corrected record at `f268f5610`: Disposition `completed`; Accepted by `Niklaus Riker 20260819T125003Z` at `2026-08-19T14:30:54Z`; published Contract SHA-256 `b47a84f71b6a40425668c5136e5f542aa1f221b3cc338f8f16fa7caa3518ae1e`; work-product manifest `6379020bb096b4c941157f65ac039f063bc7b5fa590fe7f68ac2ec863230eaf8`; prerequisite-acceptance `ae1da059b8b15d11e1e9c6fd9851211d95f8ba6c59eaa3ca2f1c156cd40df132`; Review REF `5c75893795ab7d8a7edd1a8583c26f627ace3662`.

`git merge-base --is-ancestor f268f5610 9ccd99b` exits 1. On pin `9ccd99b`, `0039-01` is `[ ]` with the 2026-08-23 Seven reservation and the later RQ-EFF-01 / `docs/dossiers/0039-01-effectiveness-measurement.md` DoD. No `Acceptance: ✓` on main.

### Contract drift (material)

Independently hashed Task blocks (canonical rule):

| Tree | 0039-01 contract SHA-256 | Bytes |
|---|---|---|
| `130e8f8dc` / pre-`✓` at `afce1a779a` | `ff486e39af821d31f8ce6a0b4a5609f405e336bcaf01fd1de0a787ae8617109d` | 5429 |
| Pin `9ccd99b` | `cc5b9ba9c7b402b268b6b338f72c7e07e0b02def27856cdfaade5869bb12511d` | 4181 |
| Seven tip `778c8db6e5` | `386a93462bc15f01267dccf868b907f00b01eed0a7005caa055d746d06f7ce91` | 5413 |

Published accepted digest `b47a84f71…` **did not recompute** from `130e8f8dc` or from the pre-`✓` slice of `f268f5610` under this serialization. That is a **serialization gap** for the published 0039-01 contract field, not a reason to treat pin/Seven text as equal to the 2026-08-19 `[x]` body: pin and Seven hashes both differ from `ff486e39…`.

Material additions present on pin and on Seven's `[p]` header, absent from the 2026-08-19 implementation-complete DoD: deferred `RQ-EFF-01` 20-Task measurement; required dossier `docs/dossiers/0039-01-effectiveness-measurement.md`; reservation naming `seven`. Seven's own commit `778c8db6e5` records that the Task was already accepted on 2026-08-19 before the contract was expanded, and that later additions superseded contract SHA-256 `b47a84f71…`. Independently confirmed as a claim about drift; this review does **not** adopt Seven's dispositions of individual deliverables.

`task-acceptance.md`: normative Task / criterion / DoD change invalidates current acceptance. The current contract is not the accepted contract.

Prerequisite-closed impact: historical `0039-01` `✓` depended on then-current `0039-04` `✓`. `0039-04` `✓` is not current on `main` (Verdict A). Even if `0039-01` `✓` had landed, it could not remain current on `main` while its required predecessor lacks current `✓` (`task-acceptance.md` §2).

### Next lifecycle step (`0039-01`)

1. Treat `f268f5610` `✓` as **historical, not current**.
2. **Additive** invalidation/supersession belongs on the `0039-01` integration/acceptance path when authorized — not as a rewrite of `f268f5610`, and not as this session marking `0039-01` accepted.
3. Seven remains the reserved implementer of the **current** contract; this review does not inspect or accept `778c8db6e5` work products.
4. After Seven's delta is `[x]`/`[w]` on an authorized baseline, a **separately assigned** independent privileged reviewer (not Seven, not this impact-only assignment unless re-assigned) performs fresh Acceptance of that baseline. `0039-04` current-main Acceptance (if still missing) remains in the same prerequisite-closed batch.

---

## Independence and competence

Reviewer `paul` is not Linus/Niklaus/Ken/Edsger/Margaret/Shannon Riker, not `seven`, not the `zed` 0039-04 implementer. No waiver. Competence for this assignment is reading Git reachability, `TODO.md` contracts, and `task-acceptance.md` invalidation rules; no specialist architecture/security decision is required to decide current-vs-historical credit.

## What was not done (bounds)

- No mutation of `refs/heads/0039-01` or Seven's worktree.
- No `Acceptance: ✓` added or removed on `TODO.md`.
- No `main` advance, no Feature `0039` `DONE.md` move.
- No re-run of 2026-08-17/19 test suites as a substitute for a new Acceptance.
- Live `main` `714fbdd40` 0044-028 landing recorded only as unrelated post-assignment tip drift.

## Next lifecycle step (batch)

Report this candidate to `jean-luc`. Privileged integrator/PL decides whether to (a) leave main markers as they are (already no `✓`), (b) authorize a later additive invalidation note when `0039` merges, and (c) assign a **new** Acceptance reviewer for current-main `0039-04` and, after Seven completes, current `0039-01`. This candidate is not that Acceptance.
