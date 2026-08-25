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

## 2. Population — 20 Tasks, deterministic

Rule from the Task contract: exactly the first 20 Task-level items (`XXXX-YY`;
Features and Subtasks excluded) whose **authoritative** implementation disposition
first becomes `[x]`/`[w]` after activation, ordered by terminal-transition event,
Task ID as tie-breaker.

Baseline commit at/before activation: `83086add0` — 367 Task-level items, of which
138 already terminal and therefore excluded.

| # | Task | Event | # | Task | Event |
|---|---|---|---|---|---|
| 1 | `0040-03` | `d5a65d3a7` 08-20T08:05:14Z | 11 | `0038-25` | `d53e570fa` |
| 2 | `0040-05` | `d5a65d3a7` | 12 | `0038-17` | `ba087fc8b` |
| 3 | `0040-08` | `d5a65d3a7` | 13 | `0037-37` | `bad253b23` |
| 4 | `0040-09` | `d5a65d3a7` | 14 | `0041-01` | `caa7cda9a` |
| 5 | `0040-10` | `d5a65d3a7` | 15 | `0043-01` | `d4741e906` |
| 6 | `0040-11` | `8f6d42b48` | 16 | `0044-01` | `9716738fa` |
| 7 | `0038-20` | `b4ea895cb` | 17 | `0038-28` | `d175e4e28` |
| 8 | `0038-24` | `5f7d1ef17` | 18 | `0043-02` | `946e5e4ab` |
| 9 | `0038-05` | `6e411eedf` | 19 | `0037-49` | `aaa74b8e6` |
| 10 | `0038-23` | `053ffb601` | 20 | `0037-07` | `2f8344187` 08-21T22:54:37Z |

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

## 4. Primary count 2 — escalations (DRAFT, limitations visible)

**Result as computed: 9 of 20 Tasks** — `0040-05`, `0040-08`, `0040-09`,
`0040-10`, `0038-20`, `0037-37`, `0044-01`, `0037-49`, `0037-07`.

Method: escalation markers (`BLOCKER`, `escalat*`, `Eskalation`, `[u]`,
`Managemententscheidung`, `management decision required`, `user decision`) in each
Task's authoritative block on `main` (`TODO.md` + `DONE.md`).

**This is reported as *"Tasks whose authoritative block contains an escalation
marker"*, which is what was computed — not as "escalations".** Its limitations are
part of the result, not a footnote:

- **Lexical, not structural.** It counts a marker's presence, not a conforming
  escalation record. Reporting it as "escalations" would be a proxy behind a
  target's name — the same defect this Task catalogues elsewhere.
- **Block delimitation.** Blocks end at the next Task-level marker, so a note filed
  under a neighbouring item is attributed to the wrong Task.
- **Quotation blindness.** A `[u]` inside quoted prose is indistinguishable from a
  live marker.

A structural count against a conforming escalation record shape is owed before this
figure may be called final.

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
