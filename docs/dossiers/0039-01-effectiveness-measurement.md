# `0039-01` — TK-2 effectiveness measurement

> **STATUS: DRAFT. NOT A FINAL RESULT.**
> This document reports what has been measured so far and what has not. It draws
> **no final process or pilot conclusion**, and it is not evidence that
> `RQ-EFF-01` is satisfied. Release to continue in draft: jean-luc
> (`1787678966455-cd5bdd62`). A final conclusion and the Task's `[x]` remain
> locked until the independent disposition / gate resolution described in §7.

Author: Architect `seven`, claim `TODO-seven-0039-01-20260824T091500Z.md`,
owner token `agent:seven:0039-01:20260824T091500Z`.

## 1. Activation reference

The population is anchored to the **recorded authority-activation reference** for
the `0040-05` TK-2 rule:

| Field | Value |
|---|---|
| Decision | `DEC-0040-007` |
| Recorded at | `2026-08-20T08:02:27Z` |
| Authority reference | `docs/dossiers/0040-management-closure-provenance.md#dec-0040-007` |
| Binding statement | CON-01: the cross-item gate-scope rule holds valid Management authority **from that instant** |

`DEC-0040-005` is deliberately **not** used as the activation reference. It is the
preserved instance of an agent asserting Management authority it did not hold;
`DEC-0040-007` is the ratification that supplied the missing authority.

## 1a. CORRECTION `F-SEVEN-0039-01-SELF-002` — the first population was derived with a defective traversal

**The population table published in the previous draft revision (`df537b263`) was wrong and is superseded here.** The correction is additive; the superseded membership is retained in the manifest's `corrections` block.

**Defect:** the derivation walked `git log --reverse main -- TODO.md DONE.md` **without `--first-parent`**. That interleaves side-branch commits into what was then read as main's timeline — 399 commits total against 270 on the first-parent line — and reading file state at a side-branch commit reports *that branch's* state as a point in main's history.

**How it surfaced:** while deriving the §7.1 context findings, the structural marker-transition reconstruction reported that nine unrelated Tasks reverted from `[x]` at commit `550a6f50a` — a claim commit for `0037-08`, an entirely different Task. A claim commit cannot revert nine foreign Tasks; the implausible result was the symptom. `550a6f50a` is verifiably **not** on main's first-parent line.

**Effect on the result:**

| | Previous (defective) | Corrected (`--first-parent`) |
|---|---|---|
| Membership | included `0040-11` | includes `0044-14` instead |
| Ordering | side-branch timestamps interleaved | main-line transition order |
| Attributed TK-2 count | 3 of 20 | **3 of 20 — unchanged** |

The attributed Tasks are the same three (`0040-05`, `0040-09`, `0044-01`); `0044-14`, newly in the population, carries no attributed record. **The count is unchanged, but it was unchanged by luck, not by construction** — a different member could have carried a record, and the published population would still have been wrong.

**This is the reach axis in my own measurement:** the traversal computed "state at some ancestor of main" while the result asserted "state of main over time". Same defect class this Task catalogues; third time it has caught its own author. The tool now uses `--first-parent`, with the reason recorded at the source line; the 11-test suite remains green.

**Consequence for §4:** the escalation draft and the §7.1 context findings computed on the defective traversal were withdrawn and have since been **re-derived** on the corrected population; see §4 and §4a. The superseded figures are not restored.

## 2. Population — 20 Tasks, deterministic

Rule from the Task contract: exactly the first 20 Task-level items (`XXXX-YY`;
Features and Subtasks excluded) whose **authoritative** implementation disposition
first becomes `[x]`/`[w]` after activation, ordered by terminal-transition event,
Task ID as tie-breaker.

Baseline commit at/before activation: `83086add0` — 138 Task-level items already terminal and therefore excluded. Traversal: `git log --reverse --first-parent main -- TODO.md DONE.md` (see the correction in §1a).

| # | Task | Event commit | Event time (UTC) |
|---|---|---|---|
| 1 | `0038-05` | `6e47ec274` | 2026-08-20 19:31:42 |
| 2 | `0038-20` | `6b4f2a00e` | 2026-08-20 20:14:34 |
| 3 | `0038-24` | `bd2d64808` | 2026-08-20 20:15:58 |
| 4 | `0038-23` | `053ffb601` | 2026-08-20 20:16:24 |
| 5 | `0038-25` | `d53e570fa` | 2026-08-20 21:11:42 |
| 6 | `0038-17` | `ba087fc8b` | 2026-08-20 21:20:19 |
| 7 | `0040-03` | `c5c478a6c` | 2026-08-20 23:10:23 |
| 8 | `0040-05` | `c5c478a6c` | 2026-08-20 23:10:23 |
| 9 | `0040-08` | `c5c478a6c` | 2026-08-20 23:10:23 |
| 10 | `0040-09` | `c5c478a6c` | 2026-08-20 23:10:23 |
| 11 | `0040-10` | `c5c478a6c` | 2026-08-20 23:10:23 |
| 12 | `0037-37` | `bad253b23` | 2026-08-20 23:44:16 |
| 13 | `0044-01` | `eeb759a51` | 2026-08-21 08:58:55 |
| 14 | `0041-01` | `7b2e2ce99` | 2026-08-21 12:22:35 |
| 15 | `0043-01` | `7b2e2ce99` | 2026-08-21 12:22:35 |
| 16 | `0038-28` | `4827ddef4` | 2026-08-21 14:07:25 |
| 17 | `0043-02` | `4c0c7f041` | 2026-08-21 14:07:26 |
| 18 | `0037-49` | `f5cc5bbb4` | 2026-08-21 19:50:18 |
| 19 | `0037-07` | `b13257241` | 2026-08-21 23:12:52 |
| 20 | `0044-14` | `7e12f877d` | 2026-08-22 10:11:13 |

**20 qualifying Tasks exist, so the contract's `not-yet-mature` branch does not
apply.** Manifest with source event commits and the environment qualifier:
`docs/pipeline/evidence/0039-01/effectiveness-population-manifest.json`. Derivation
tool: `_src/tools/derive_tk2_measurement_population.py`, tests
`_src/tests/test_derive_tk2_measurement_population.py` (11/11 green).

**Robustness against branch/`main` divergence:** 73 of 122 item branches carry
markers diverging from `main` (kathryn, 2026-08-25). This does not affect the
population: the contract binds it to the **authoritative** disposition and
`AGENTS.md` makes `main` authoritative, so a branch-side `[x]` is not yet an
authoritative transition. A branch landing later transitions later — after this
window's tail — and cannot retroactively enter the first 20.

## 3. Primary count 1 — conforming TK-2 decision records

**Result: 3 of 20 Tasks**, five records.

| Task | Attributed records |
|---|---|
| `0040-05` | `DEC-0040-005` |
| `0040-09` | `DEC-0040-006` |
| `0044-01` | `DEC-0044-005`, `DEC-0044-006`, `DEC-0044-007` |

Attribution rule: a `decision-record@v1` block whose **own** Subject / Affected /
Scope / Triggers / Authority fields name the Task. Parser coverage: **51 of 54**
distinct `DEC-` identifiers parsed as record blocks, 19 conforming. The three that
cannot be parsed are enumerated rather than left implicit — `DEC-0038-003`,
`DEC-MARKER-001`, `DEC-ROLE-001` — and the residual gap was closed by inspection:
`DEC-ROLE-001` occurs in context with `0037-49` and `0044-01`, but it is a *role*
decision quoted in recorder-identity lines ("Projektleiter records, does not
decide"), not a record attributed to a Task. No attribution added. **The count is
therefore the measured value of this method, not a lower bound.**

**Rejected method, recorded so it is not re-derived as new:** a file co-occurrence
measure yields 14/20 and is **invalid** — it measures shared file residence, not
attribution (`0037-07` alone "hits" 26 records through an index page). Same
inflation direction as the `0038-31` double-count incident.

## 4. Primary count 2 — escalation-marked Tasks (DRAFT, re-derived)

**Re-derived on the corrected first-parent population (`F-SEVEN-0039-01-SELF-002`). The previously withdrawn figure is superseded, not restored: it happened to be the same number, 9, but it was computed over a population containing `0040-11` instead of `0044-14`.**

**Result: 9 of 20** — `0038-20`, `0040-05`, `0040-08`, `0040-09`, `0040-10`, `0037-37`, `0044-01`, `0037-49`, `0037-07`.

Method: escalation markers (`BLOCKER`, `escalat*`, `Eskalation`, `[u]`, `Managemententscheidung`, `management decision required`, `user decision`) in each Task's authoritative block on current `main` (`TODO.md` + `DONE.md`).

**Reported as *"Tasks whose authoritative block contains an escalation marker"*, which is what was computed — not as "escalations".** Limitations are part of the result:

- **Lexical, not structural.** Marker presence, not a conforming escalation record.
- **Block delimitation.** Blocks end at the next Task-level marker, so a note filed under a neighbouring item is attributed to the wrong Task.
- **Quotation blindness.** A `[u]` in quoted prose is indistinguishable from a live marker.

A structural count against a conforming escalation-record shape is still owed before this may be called final.

## 4a. Context findings — `[u]` authority waits and marker reversals (DRAFT, structural)

Re-derived from the corrected first-parent traversal; method: marker-transition reconstruction per population Task across main's bookkeeping history. **Structural, not lexical** — it reads marker state changes, not prose.

**`[u]` authority-wait episodes: 1 of 20 Tasks.**

| Task | Entered `[u]` | Left | Duration | Outcome |
|---|---|---|---|---|
| `0037-49` | 2026-08-20 23:47Z | 2026-08-21 19:50Z | **20.0 h** | `[x]` |

One authority wait in the whole population, resolved to implementation completion after twenty hours. No open-ended `[u]` remains among the twenty.

**Terminal→non-terminal reversals: 2 of 20 Tasks — and neither is a scope reversal.**

| Task | Transition | Commit |
|---|---|---|
| `0038-28` | `[x]` → `[ ]` | `4b95d99db` |
| `0043-02` | `[x]` → `[ ]` | `4b95d99db` |

Both occur at the **same commit**, `4b95d99db` — the already-documented data-loss incident in which a stale-root-checkout commit deleted 4,869 lines from three already-terminal items, repaired by `27930dc9c`. **These are not scope reversals; they are the known incident, and the derivation reproduces it exactly.** That the corrected traversal returns precisely the one documented event and nothing else is the strongest available check that the correction in §1a worked: the defective traversal reported 18 of 20 Tasks reverting, including nine at an unrelated claim commit.

**Genuine scope reversals in the population: none observed.**

**Still owed for §7.1:** missed-trigger findings — Tasks whose declared behaviour met the cross-item predicate but which carry no attributed TK-2 record. That requires judging each Task's declared reach, which is not a lexical operation and is therefore not attempted here as a count.

## 5. Mandated conclusion

Both primary counts are **non-zero** (3 attributed TK-2 records; 9 escalation-marked
Tasks). The contract's rule — *"If both primary counts are zero, the conclusion is
`withdraw`, not `expand`"* — therefore yields: **NOT `withdraw`.**

The contract's own qualifier applies in full: **a non-zero count is adoption
evidence only and is not by itself proof that `RQ-EFF-01` is fulfilled.**

## 6. `RQ-EFF-01` disposition

**`RQ-EFF-01` remains DEFERRED.** This measurement demonstrates that the rule was
adopted in some measure after its activation. It does **not** demonstrate that the
rule is effective, and no capability claim is made here. Nothing in this document
should be cited as effectiveness evidence.

## 7. What is still owed before this can be final

1. Contextual findings the contract requires and this draft does not yet contain:
   missed-trigger findings, later scope reversals, and `[u]` authority-wait duration
   and outcome.
2. A structural escalation count replacing the lexical draft in §4.
3. Resolution of the `AUTO010` gate question. Three `unresolved_critical` findings
   stand against this Task's own test fixture. `Wesley` independently diagnosed them
   as **checker false positives** (the durable JSONL state exists; the checker does
   not bind `handle.write` to `self.journal_path`), and `Data` confirmed
   **`cross-item-blast-radius`** for the alias/dataflow fix. That fix requires a new
   `decision-record@v1` on current `main` plus a management-instantiated Architect
   review **distinct from the implementer** — which cannot be the author of this
   document, who implemented both the measured tool and the fixture.
4. Independent acceptance of `0039-01` itself, which its author does not perform.

## 8. Environment

Every figure above was produced in the environment recorded in the manifest's
`environment` block (interpreter, platform, worktree, branch commit, `main` commit,
timestamp). Absence of that block invalidates the numbers as evidence; it is
included deliberately, following the rule derived from this Task's own defect
catalogue.
