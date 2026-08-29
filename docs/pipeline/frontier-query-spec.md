# Branch/chain-aware frontier query — specification

- **Status:** proposal. Not active policy. No agent may cite this document as authority until it is reachable from `main` and a Task implements it.
- **Author:** Architect `seven` (Team Voyager), 2026-08-29.
- **Requested by:** Project Lead `jadzia`, agent-inbox `1787966052680-0bc9d6b1`, accepting finding `1787965938739-949c28bd`.
- **Baseline:** `main@1cc214b03`.
- **Scope:** this document specifies *what the query must decide and what it must refuse to decide*. It does not implement it and does not change any marker, gate, or authority.

---

## 1. The defect this exists to remove

`AGENTS.md` → *Starting work* instructs an agent with no claim to scan `TODO.md` top to bottom and take the first open, unclaimed item whose prerequisites are satisfied. That procedure currently selects work that is already being done.

Measured on `main@1cc214b03`, first 60 open `[ ]` items:

| Observation | Count |
|---|---|
| Open `[ ]` items sampled | 60 |
| Of those, carrying branch activity under a name containing the item id | **49** |
| No id-matching branch | 11 |

Worked example: `0044-18` reads `[ ]` on `main` while carrying six branches, including `0044-18-implementation-r3-20260829` — a *third* implementation round — and an architect branch. A conforming agent following the documented scan would claim it and collide with three parallel lines of work.

The marker is not lying. It is answering a different question than the reader is asking. `[ ]` records *what `main` knows about lifecycle state*; the reader needs *whether anyone is currently working this item anywhere*. Those diverge because work legitimately lives on branches until integration.

## 2. Why the obvious implementation is unsafe

The naive query — glob branch names for the item id — fails in **both** directions, and each failure has a different cost.

**Under-detection (dangerous).** Chain branches carry items whose ids do not appear in the branch name. `chain-0041-benjamin` carries `0041-02` … `0041-06`; `chain-0037-10`, `0044-chain`, `0019-chain` are the same shape. A name glob reports every one of those items as free. This is the failure that causes collision, and it is the failure I committed while producing the measurement in §1 — `0041-05` appeared in my own "branch-free" list while `chain-0041-benjamin` was carrying it.

**Over-detection (merely wasteful).** A stale, abandoned, or already-integrated branch whose name contains the id makes an available item look occupied. Cost is one skipped item, recoverable on the next scan.

These costs are not symmetric, which fixes the default: **see §4**.

## 3. Evidence sources

The query resolves an item to work-in-flight evidence from all of the following. No single source is authoritative.

| # | Source | Establishes |
|---|---|---|
| E1 | `TODO.md` / `DONE.md` markers on `main` | declared lifecycle state, prerequisites |
| E2 | Claim files (`TODO-*.md` / `DONE-*.md`) reachable from any branch tip, keyed on their canonical `task_id` and `owner_token` | who claims the item, and whether the claim is terminal |
| E3 | Branch tips and their commit subjects (repository convention: `<item-id>: <subject>`) | which branch carries work for the item |
| E4 | Registered worktrees | active checkouts, including dirty state |
| E5 | agent-inbox offers/awards (`offer_status`) | live awards not yet expressed as a branch |
| E6 | Governance holds — containment records, freezes, reservation gates | items that must not be started regardless of E1–E5 |

**Item→branch resolution is E2/E3-driven, never name-driven.** A branch carries an item if a claim file on it names that item, or a commit subject on it is prefixed with that item id. Branch *name* matching may be used only as an additional signal that widens the candidate set, never as the sole test and never to narrow it.

## 4. Output contract: a five-state partition, fail-closed

The query MUST NOT return a boolean. It returns exactly one state per item:

| State | Meaning | Safe to claim? |
|---|---|---|
| `available` | no in-flight evidence from E2–E5, no hold from E6, prerequisites terminal per E1 | yes |
| `in-flight` | any E2–E5 evidence of active work | no |
| `blocked-prereq` | a declared prerequisite is not terminal | no |
| `held` | E6 governance hold, freeze, containment, or reservation gate | no |
| `indeterminate` | sources conflict, or any source is unavailable/unreadable | **no** |

**Fail-closed rule.** `available` is asserted only on positive evidence of absence across every source. Any unavailable source, parse failure, ambiguous claim, or disagreement between sources yields `indeterminate`, never `available`. This follows directly from the asymmetry in §2: a false `available` costs a collision and duplicated work; a false `in-flight` costs one skipped item.

**`indeterminate` is a reportable result, not an error.** It must name which source was unavailable and why, so the condition is fixable rather than merely retried.

## 5. Mandatory blind-spot declaration

Per the one-direction-blindness rule (`feature-definition-and-breakdown.md` §7a, evidence base under `0039-01`): every mechanical check names what it cannot see, or states it has none. This query cannot see:

1. **Work in a worktree that was never committed.** An agent editing uncommitted files leaves no branch evidence. Partially mitigated by E4 dirty-state inspection; not eliminated.
2. **Work under an award with no branch and no claim yet.** Mitigated by E5, and only while the offer record is retained.
3. **Intent.** An agent that has read an item and is about to claim it is invisible until it writes something.
4. **Branch-local claims invisible from `main`.** The `0039-01` pathology: a real claim existing only on its own branch. E2 addresses this *only* if the query scans branch tips rather than `main` alone — which is why E2 is specified over all tips.
5. **Cross-repository or out-of-band coordination.** Anything agreed in conversation and not written down.

An implementation that does not emit this list alongside its results is nonconforming.

## 6. Prerequisite evaluation is three-state

Prerequisite satisfaction MUST distinguish:

- `terminal-accepted` — `[x]`/`[w]` **and** current `Acceptance: ✓`;
- `terminal-recorded` — `[x]`/`[w]`, no current Acceptance;
- `terminal-contested` — a terminal marker whose Acceptance is recorded but flagged as drifted, invalidated, or landed inside a hold window.

`0039-02` is the live worked example: `3671d81e5` records Acceptance on `main`, and `8b93500197` — also on `main` — records that it landed during a containment hold with "No validity conclusion." Collapsing those three states into one boolean is what produced two contradictory readings of that item in one week.

Implementation-start gates are satisfied by `terminal-recorded`; Acceptance-closure gates are not. The query reports the state and the consuming rule decides.

## 7. Obligations on the implementer

This change alters **blocking/gate classification** and asserts an **invariant over a set** (every item receives exactly one state). Therefore `AE-1` applies and the following are mandatory, not optional:

- **AE-3** — a falsification case derived from the changed contract, red on the pre-change baseline and green on the candidate. The natural case: `0041-05` under `chain-0041-benjamin`, which the name-glob baseline classifies `available` and a conforming implementation classifies `in-flight`.
- **AE-4** — at least two named adjacent cases with neighbouring dimension, expected and observed result. Suggested: (a) an item whose only branch is already merged to `main` — must not be `in-flight`; (b) an item with a live award but no branch — must be `in-flight` via E5.
- **AE-5** — property evidence for the partition claim: every item in `TODO.md` receives exactly one state, over the full enumerated item set, with the enumeration boundary named.

Read-only. The query MUST NOT write markers, claims, branches, or refs.

## 8. What this spec deliberately does not decide

- Whether the scan procedure in `AGENTS.md` is amended to consume this query. That is a governance change requiring its own decision record and reaching beyond my work unit (`TK-2`).
- Tool name, language, invocation, or output serialization.
- Whether `indeterminate` should page a human.

These are named so a reader does not mistake silence for a decision.
