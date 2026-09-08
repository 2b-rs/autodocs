# Independent Architect scope review — `DEC-0027-001` MAN.3 plan gate scope

**Review kind:** independent supporting pre-mutation cross-item gate-scope review, as required by
`AGENTS.md`. **Not** Task acceptance, an integration review, an integration verdict, or
`Acceptance: ✓`. It grants no authority and activates nothing.

**Reviewer:** Architect `seven` (Team Voyager), management-instantiated for this review by Project
Lead `jean-luc` — OFFER `1787794283084-d1816a4a`, ACCEPT `1787794381994-3e9cd8de`, AWARD
`1787794424643-51761afa`. **Claim:** `TODO-seven-0027-01-scope-review-20260827.md`.

| | |
|---|---|
| Candidate | `8772645587fd41ae873aeb9c48c061de134d581c` |
| Candidate branch | `gov-0027-01-gate-scope-data-20260827` |
| Baseline offered | `main@2881e6ea7ea286a7e23869f3428b307c9179e4b5` |
| Baseline **re-measured at start** | `main@2881e6ea7ea286a7e23869f3428b307c9179e4b5` — **unchanged, 01:34Z** |
| Record | `docs/dossiers/dec-0027-001-man3-plan-gate-scope.md`, SHA-256 `c21b2d04c57a685e88bdd03e761a209b933fb089090c4f1a418c0d75ad76f495` |

**Verdict: `scope-ready-for-mutation`**, subject to the one condition in §5.

**Independence:** zero prior involvement with Feature `0027` — measured, not asserted (no commit of
mine references it). Disclosed and not a conflict: I reviewed two unrelated records by the same
author today (`DEC-0044-026-C001`, `C002`). Independence turns on *my* authorship, not the author's.

---

## 1. Baseline movement

The AWARD required the pin to be re-measured before start, and a baseline-impact assessment rather
than candidate mutation if `main` had moved. **`main` had not moved**: `2881e6ea7` at 01:34Z,
identical to the offered baseline, with the candidate containing it as an ancestor
(`merge-base --is-ancestor` verified). The diff against that baseline is **purely additive** — 3
files, +390/−1, the single deletion being the replaced `0027-01` marker line. No baseline-impact
assessment is owed.

Recorded because a pin aged in minutes elsewhere today: the Feature `0037` coordinator published a
`main` pin that her own integration invalidated four minutes later. This pin was re-measured for
that reason, not as ceremony.

## 2. `decision-record@v1` conformance — conforming

All twelve fields present and correctly ordered, checked against the closed grammars in §3.1 rather
than by inspection:

| Element | Result |
|---|---|
| Identity `agent:data:0027-01:20260827T011751Z-a33e0189` | agent grammar, four payload components |
| `Recorded at` `2026-08-27T03:18:30+02:00` | valid offset; 01:18:30Z, after the 01:17:51Z claim |
| `Role: Architekt` | in the closed role set |
| `Triggers` | three, **all in the closed set** — including `public-release`, verified to be one of the seven and not an invention |
| `Considered alternatives` | four, exactly one `selected`, each with a non-empty reason |
| `Consequences` | seven, including rollback boundaries and an explicit no-grandfathering clause |
| **`Affected gates`** | **23 entries, every one conforming** — `task-start:`, `integration:` and `feature-closure:` carry work-unit IDs; `validation:` carries paths or stable ids; `release:` carries a stable id |
| `Affected work units` | 25 entries, all `task:`/`feature:` with valid IDs |
| `Review participation: none` + `No-review reason` | the permitted form, and the reason is correct: the decisive author cannot supply his own supporting review |
| `Waiver: none` | present |

**The gate block deserves naming.** Twenty-three gate references with no non-canonical prefix and no
descriptive slug where an `<ID>` is required. I returned `scope-not-ready-for-mutation` on a
different record today for exactly that defect in one entry of six; this record has none in
twenty-three.

## 3. Scope, activation, and separation

**Cross-item blast radius — exact, and argued in both directions.** The record does not merely list
affected units: it carries an explicit **exclusion table with reasons**. Feature `0022` is excluded
because it depends on `0027-05` rather than `0027-01`; kernel/OS/HWE/complete-ECU and the public
documentation pipeline are excluded as outside `software-without-kernel` or wrong evidence origin.
Features `0028`–`0032` are included **for existing closure reach only**, adding no task-start edge.
A scope claim stating what it excludes and why is checkable; one listing only inclusions is not.

**Fail-closed activation boundary — present and self-applied.** Activation requires the exact
baseline to carry an independent supporting review *and* to reach current `main` through separately
assigned privileged integration; product plan mutation still waits on human decisions. Only
canonical gate references are in scope — "no prose alias, wildcard, or implied additional consumer".
**Self-application is explicit**: the first `0027-01` plan baseline receives no bootstrap exemption.
No implicit grandfathering. Rollback is defined on both sides of activation and never rewrites
history.

**Unanswered human decisions — properly separated.** They are `HD-` templates, labelled "prepared
questions, not decisions", with no option pre-selected and routing reserved to the Project Lead for
when a question is the sole next human action. The record neither decides them nor smuggles them
into `Decision` prose.

**`[u]→[p]` — correct, and correctly reasoned.** `CON-01` applies the governing rule: `[u]` is valid
only when a specific human decision is the **sole** next action, and here conforming-record work,
independent review, decision routing, and non-operative candidate preparation all remain agentic.
Under `AGENTS.md` that makes `[p]` right and `[u]` wrong for the governance line.

**Terminal checkpoint `0027-11` — complete.** It carries architecture decisions, planned order with
per-edge justification, acceptance criteria, Definition of Done, test scope derived from
architecture seams, a capability profile including **all five cognitive-demand dimensions** per
`feature-breakdown.md` §8, an advisory range, its branch, and `Integration review: mandatory` with a
named architect rationale that also records the author's own disqualification from reviewing it.
This is the exactly-one terminal integrating Task the process requires.

## 4. Finding — `F-0027-01-SCOPE-01`: the marker collision has no named resolution owner

**Measured across four refs, not inferred:**

| Ref | `0027-01` marker |
|---|---|
| `main@2881e6ea7` | `[ ]` |
| `f8f86837f6` (product preparation) | `[p]` |
| `ffe1b8a851` (product-branch child) | **`[u]`** |
| candidate `8772645587` | **`[p]`** |

The product line moved `[p]` → `[u]`. That is a **deliberate lifecycle transition**, not a default
state, and its holder has a live foreign claim (`agent:tasha:0027-01:20260827T010216Z-5f3a2c91`).

**What the candidate does right:** it preserves that owner token explicitly, records **both** prior
projections and its own reasoning in the `TODO.md` note, and confines the deciding author's
ownership to the governance correction. That is genuinely additive documentation of a single-valued
field, and it is the correct handling of the *token*.

**The gap:** a marker is **single-valued and shared**. Two claims may hold disjoint *write scopes*
over a Task's products, but they cannot hold disjoint ownership of one marker. The record resolves
the divergence in the governance line's favour without the other claim-holder's participation, and
**names nobody to resolve the collision when the product branch integrates**. Whichever lands second
conflicts or silently overrides — and a silent override of a deliberate `[u]` would erase an
escalation signal.

**Deliberately not claimed:** I do **not** find that `[p]` is the wrong value — on the governance
line the reasoning is sound. I do **not** find an authority violation; the token is preserved and no
foreign claim is appropriated. And I do **not** assert that the product line's `[u]` is wrong for
*its* line: its holder may face a product-side human decision that is genuinely her sole next
action, which the record's own `HD-` templates make plausible. **The defect is an unassigned
resolution owner, not a wrong value.**

## 5. Condition for activation

**C-1.** Before the `TODO.md` delta integrates, name who resolves the `0027-01` marker collision
with the holder of the live product claim, and record the outcome — either a coordinated single
value with both owners' participation, or an explicit statement that the governance line's `[p]`
supersedes the product line's `[u]` **and why that does not discard an escalation**. This is a
coordination act, not a scope change; it needs no new decision record and no further scope review
from me.

Everything else in the candidate is ready. The dossier itself may proceed unchanged.

## 6. Boundaries

Read-only against candidate, product, and governance contract. No candidate or `TODO.md` repair, no
authoring outside this record and my claim, no activation, implementation, Acceptance, integration,
`main`/`DONE` movement, push, publication, or external effect. `scope-ready-for-mutation` releases
the pre-mutation scope gate only, for the reach the record enumerates, and is not Acceptance. This
review pins the candidate exactly and does not extend to any successor commit.

## 7. Reviewer defect disclosed — empty first commit

My first commit on this branch, `d7e827545`, contains **both artifacts as zero-byte files**. A
heredoc invoked `/usr/bin/cat`, which does not exist in this environment (`/bin/cat` does); the
shell's `>` redirection had already created and truncated the files before the command failed, so
`git add` and `git commit` succeeded on empty content. The failure was visible in my own output — a
review-file digest of `e3b0c442…b855`, the SHA-256 of the empty string — and was caught by reading
it rather than by any gate.

Recorded rather than quietly amended, and the empty commit is retained in history, because a review
that reports another agent's traceability gap while hiding its own would not deserve to be believed.
