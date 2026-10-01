# Independent scope review — `DEC-0044-026-C002` (r2 candidate)

**Review kind:** independent pre-mutation cross-item gate-scope review. Not Task
acceptance, not an integration review, not an integration verdict, not `Acceptance: ✓`.

**Reviewer:** Architect `seven` (Team Voyager), assigned by Project Lead `jean-luc`
(`agent-inbox:1787753428493-7bf887ab`). **Claim:** `TODO-seven-0044-026-c002-review-20260826T141500Z-e0ae3187.md`.
**Predecessor review:** `4ad4389fc` (`scope-not-ready-for-mutation`), unchanged.

| | |
|---|---|
| Candidate | `b9fc1f7b9f1a2ea4bfa54bec5041e10b6911e238` |
| Branch | `gov-0044-026-gate-grammar-c002-data-20260826-r2` |
| Parents | `4d3f3fefa` (current `main`), `671a1ac7e` (prior C002) |
| Dossier digest | `711e2614ab302cb1eb6b193d07858514ccbc72c02246936f5db0e6286948274b` |

**Verdict: `scope-ready-for-mutation`.** All four conditions of `4ad4389fc` are met.

---

## 1. Independently reproduced, not accepted on report

| Check | Result |
|---|---|
| Dossier digest | reproduces `711e2614…74b` |
| **C001 `Previous effective` digest** | `6ab313136b533f698b578ef143cfe32040518e4274b8f525df2ac17b34553c39` — **I computed this value before the candidate existed** and published it to the Project Lead; Data computed it independently; the committed event carries it. Three derivations, one value. |
| C002 effective-block digest | reproduces `49292d34…046` |
| C001 byte-identical to `95f3b168` | **true** — 1274 bytes, both sides |
| First-parent diff vs `main` | 2 files, +186/-0, purely additive |
| Event placement | `C001` (line 59) → `C002` (line 81) → re-pin note (line 103); C002 immediately follows C001 as §5 requires |
| Exactly one top-level field | `Affected gates` only |

**A measurement error of mine, recorded because it nearly became a finding.** My first
C001 comparison reported *differs*. It did not: my extraction ran each block to the
*next* `####` heading, and those headings differ between the two files, so I compared
two different spans. Re-measured with an explicit block boundary: byte-identical. Had I
published the first result, I would have raised a false finding against a correct
candidate — the direction axis, in the instrument rather than the subject, for the
fourth time today.

## 2. The four conditions of `4ad4389fc`

### Condition 1 — F-1, the nonconforming payload — **MET**

The third entry is now `validation:agent-work-package-match`. `validation:` takes
`<stable-id-or-path>` under §3.1, so the slug is admissible where it was not under
`task-start:<ID>`. **All six effective gate entries now conform:** four `validation:`
with stable identifiers, `integration:0044-08` and `feature-closure:0044` with real
work-unit IDs.

### Condition 2 — F-2, the reach onto another unit's start — **MET**

**No `task-start:` gate remains in effect.** The only surviving occurrences are
historical: inside C001's superseded replacement block, and quoted in C002's own
correction reason. That is append-only working correctly, not a residue.

The narrowing is the one I identified as available and unused, and it resolves F-1 and
F-2 together rather than patching each. It restores consistency with the base record's
Decision text ("may inform scheduling but must not independently grant …") and CON-06
("`0044-05` matching eligibility … remain unchanged during this phase").

### Condition 3 — F-3, the framing of the correction reason — **MET, and precisely**

C002 states that it "selects the **narrowest reading supported by the decision's
declared content**" — the exact test I substituted for the unsupportable "semantic
equivalence" claim — and enumerates what is *not* changed: matching eligibility,
assignment, execution authority, lifecycle state, Task start. It also names the defect
in C001 plainly rather than obscuring it.

**On C001's own now-superseded reason,** which still asserts a mapping "without adding,
removing, widening, narrowing, or activating a gate": that claim is known to be wrong
and is deliberately left standing as history. This is correct. C001 is the artifact my
negative review judged; preserving it keeps that verdict checkable against what it
actually judged, and C002 both supersedes it and explains why. A reader following the
chain reaches the truth. C001's reason must not be cited as current, and the chain makes
that unambiguous.

### Condition 4 — the further append-only event with the recomputed digest — **MET**

`DEC-0044-026-C002`, ID contiguous after `C001`, one field changed, and the
`Previous effective block SHA-256` computed over **C001's replacement bytes** per §5
rule 5 — not over the original `main` block. This was the specific confusion I flagged
in advance; it did not occur.

## 3. F-4 from the predecessor review — does the existing `0044-06` scope review carry the corrected record?

**Yes, unchanged.** Its verdict excludes "any vocabulary change, automatic scheduling
enforcement, new lifecycle state, or claim that `RQ-CB-06` is customer-confirmed". The
corrected record introduces none: the vocabulary is untouched, no gate blocks a start,
no lifecycle state is created, and `RQ-CB-06` remains interpretation-bound to `0044-08`.
This was the only outstanding element of F-4 and it is now satisfied.

## 4. No new findings

I looked for a reason to withhold and did not find one. The candidate is additive,
preserves the rejected artifact, changes exactly the field and the entry it was
instructed to change, and carries three digests that reproduce independently.

## 5. Boundaries

No implementation, no `DEC-`/policy/tool/`TODO`-marker edit, no Acceptance, no
integration, no `main`, no `DONE.md`, no push. `scope-ready-for-mutation` is **not**
Acceptance and authorizes no integration or activation; it releases the pre-mutation
scope gate only. This review pins the candidate exactly and does not extend to any
successor commit.
