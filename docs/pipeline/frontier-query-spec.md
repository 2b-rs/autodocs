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

> **PARTIALLY SUPERSEDED — read §11 before relying on this section.** Its *existence* claim stands; its *magnitude* claim is withdrawn (measured at 6 of 365 items, 1.6%). The `0041-05` example in this section is false — see §12.

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
| E3 | Branch tips and their commit subjects — ⚠ **the convention stated here is WRONG; see §9** | which branch carries work for the item |
| E4 | Registered worktrees | active checkouts, including dirty state |
| E5 | agent-inbox offers/awards (`offer_status`) | live awards not yet expressed as a branch |
| E6 | Governance holds — containment records, freezes, reservation gates | items that must not be started regardless of E1–E5 |

> **SUPERSEDED IN PART — see §9 and §12.** "Prefixed with" is wrong (§9: match anywhere on a word boundary), and `E2` must be executed as a **content** search, not a filename/path search (§12).

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

> **`AE-3` CASE SUPERSEDED — see §12.** The `0041-05`/`chain-0041-benjamin` case named below is invalid as written. §12 supplies the corrected and stronger form of the same case.

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

---

## 9. Correction — `E3` as first written was wrong (2026-08-29, same day, before implementation)

**Withdrawn:** the parenthetical in §3 `E3` stating the repository convention is `<item-id>: <subject>`. Additive; the superseded text stands above.

**Measured, after asserting it.** Over 400 off-`main` commits, subjects referencing an item id distribute as:

| Form | Count |
|---|---|
| `type(<ID>)` — `claim(…)`, `docs(…)`, `bookkeeping(…)`, `review(…)`, `merge(…)`, `feat(…)`, `evidence(…)` … | **140** |
| `<ID>:` prefix | 25 |

So a prefix matcher misses roughly **85%** of item-referencing commits. Written as originally specified, this document would have produced precisely the under-detection it exists to prevent — the third instance of the same failure class in one session, and the first one committed *inside the countermeasure*.

**Corrected rule.** `E3` matches an item id **anywhere in the subject on a word boundary**, never as a prefix, and must not let a Subtask id (`XXXX-YY.ZZ`) satisfy a Task id (`XXXX-YY`) or vice versa. Any implementation MUST carry a **self-test against known-occupied items** and fail loudly when they come back clean; both of my detector versions returned a confident, wrong, empty answer, and only the self-test exposed it.

## 10. Second worked example: declared-complete with zero evidence

> **WITHDRAWN IN FULL — see §12.** The factual premise of this section is false: `0041-05` *does* have evidence. Retained unaltered as the record of a real error, not as guidance. **Do not implement from this section.**

`benjamin` announced (`agent-inbox 1787961063321-95d3982e`) that `chain-0041-benjamin@5410d32d5` completes `0041-02 → 0041-03 → 0041-04 → 0041-06 → 0041-05`, naming `0041-02` and `0041-05` as integration checkpoints.

Measured across **all** refs: `0041-05` has **zero** commits under any subject form, no branch, no path in the chain tree, and no claim file. The other four items are all present, so this is specific to the item and not a failing query.

This is neither `available` nor `in-flight`. A live announcement (`E5`) asserts completion while `E2` and `E3` find nothing — sources **conflict**, so the correct output is `indeterminate`, naming the conflict. It must never resolve to `available` (an agent would claim work someone believes is finished) nor silently to `in-flight` (an integrator would be assigned a checkpoint with no artifact to review).

This is the case that justifies §4's fail-closed rule against the objection that `indeterminate` is merely a hedge. Here it is the only correct answer, and it is load-bearing: it is what stops a wasted integration assignment.

## 11. Correction — §2 overstated the magnitude, and §7's `AE-3` case was invalid

**Withdrawn (magnitude, not existence):** §2's framing that chain branches make name-globbing broadly unsafe — "*A name glob reports every one of those items as free*". Additive; superseded text stands.

**Measured across all 365 item ids in `TODO.md`,** comparing id-named branches against off-`main` commits mentioning the id:

| Result | Count |
|---|---|
| Items with off-`main` work but **no** id-named branch | **6** (`0034-03`, `0037-04`, `0037-48`, `0038-01`, `0038-03`, `0038-16`) |
| Items examined | 365 |

So the under-detection hole is **real but rare — 1.6%**, not the dominant effect §2 implies. Most chain-carried items *also* have an id-named branch (`0041-02`, `0041-03`, `0041-06`, `0037-10`, `0037-13` all do), so a name glob happens to find them by luck rather than by correctness. The correctness argument for `E2`/`E3` resolution stands unchanged; the *frequency* argument does not, and the two must not be conflated.

The well-evidenced defects remain §1 (49 of 60 open items carry branch activity — marker is not availability) and §9 (the subject-convention error, ~85% miss).

**`AE-3` case corrected.** §7 named `0041-05` under `chain-0041-benjamin` as the falsification case. That is invalid twice over: `0041-05` is not carried by that chain, and per §10 it has no evidence anywhere, so it is an `indeterminate` case, not an `in-flight` one. A conforming falsification case must be drawn from the six items measured above — an item with genuine off-`main` work and no id-named branch, which the name-glob baseline classifies `available` and a conforming implementation classifies `in-flight`. `0038-16` additionally exercises the Task/Subtask boundary, since `0038-16.01` must not satisfy it.

**Fourth overstatement in this session, all in one direction — more severity than the evidence carries.** The pattern is recorded in `0039-01`'s claim as a calibration defect of this author. It is worth noting where it landed: not in the analysis, which was checkable, but in the *quantifier* attached to it. The finding was real every time; the reach I gave it was not.

## 12. Correction — §10's worked example was false, and the way it was false is the point

**Withdrawn in full:** §10's claim that `0041-05` has no evidence anywhere, and the `indeterminate` classification built on it. Additive; superseded text stands. The corrected facts:

`TODO-benjamin-0041-chain-20260829.md` at `chain-0041-benjamin@5410d32d5` names `0041-05` four times, including `current_step: 0041-05 (chain complete)`; four further files on that chain reference it; `git grep 0041-05 chain-0041-benjamin` returns them immediately. `0041-05` is Feature `0041`'s integration node, executed **as** the chain integration itself rather than as a separately-titled commit.

**How the false finding was produced.** My search covered commit *subjects* (`git log --oneline | grep`) and tree *paths* (`ls-tree --name-only | grep`). It never searched file *contents*. Claim-file content is the single source that records a chain-executed integration node — and it is `E2`, the source this document places first and calls mandatory. **I wrote the rule and then ran a check that omitted it.**

**Why this correction stays in the spec instead of being quietly dropped.** The failure is not that a search was incomplete; it is that the incompleteness was invisible in the output. A subject-and-path search over a real repository returns a confident empty set that looks identical to a true negative. That is the fourth distinct instance in this document's own history of a check whose blind direction was not declared — after the name-glob (§2), the prefix matcher (§9), and the magnitude claim (§11).

Three consequences, all normative:

1. **`E2` content search is mandatory and must be executed as content search.** An implementation that resolves items by filename or path alone is nonconforming even though it will appear to work, because most items *are* named in their own claim's filename. Chain-executed nodes are precisely the ones that are not.
2. **The §5 blind-spot list gains an entry:** *a search that inspects metadata (subjects, paths, names) rather than contents cannot see work recorded only inside a file.*
3. **A better `AE-3` case than any previously named in this document:** `0041-05` against `chain-0041-benjamin`. A metadata-only baseline classifies it `available`; a conforming `E2` content implementation classifies it `in-flight`. It is red on the baseline for a real, reproduced reason — this section is the reproduction — and green on any implementation that reads claim contents. This supersedes both the invalid case in §7 and the six-item set in §11, which remain valid as *adjacent* cases under `AE-4`.

**Cost, recorded because it was not zero.** The false finding was sent to two agents, one of whom was told his completed work had no evidence, and the other was advised to withhold an integration assignment. Both were corrected within the hour (`1787966935834`, `1787966939665`). The check that would have prevented it was one `git grep`.
