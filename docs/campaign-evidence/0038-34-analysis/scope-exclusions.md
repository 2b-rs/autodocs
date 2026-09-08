# `0038-34` — what the adversarial-evidence requirement does **not** cover

- **Author:** `Tom-Sisko-20260825T091500Z`
- **Status:** draft. Intended destination: `docs/pipeline/task-acceptance.md`, so that a
  reviewer — the party who must know when *not* to demand this evidence — reads it.
- Required by the node's Definition of Done: *"an explicit statement of what is **not**
  covered."*

A requirement that applies everywhere is satisfied ritually and stops meaning anything.
The exclusions below are therefore normative parts of the rule, not caveats.

## 1. Change kinds outside the four named

The requirement applies to changes touching **counting, identity, serialisation, or gate
behaviour**. It does **not** apply to, among others: documentation and prose edits;
refactoring with no behavioural claim; formatting, translation and asset regeneration;
dependency bumps; new isolated functionality that asserts nothing about existing sets;
backlog and bookkeeping edits. For these, existing completion evidence rules are unchanged
and no red-first case, adjacent case, or property test may be demanded.

**A change is in scope because of what it claims, not because of which file it touches.**
A one-line edit to a comparison operator inside a deduplication key is in scope; a
thousand-line regeneration of HTML output is not.

## 2. Document-contract conformance defects — the `0044-04` class

This is the most important exclusion, and it is drawn from a case the `0038-34` node
currently cites as *supporting* evidence. See `review-record-analysis.md` §3.

`0044-04` round 1 was rejected on four material defects:

1. a binding Architect scope-review condition (A-09) not fulfilled — a requirement ID
   absent from a `Requirements covered` field;
2. prospective placeholders called A1 records although the normative schema permits only
   `fits|does-not-fit` and requires `checked_at` and `recorded_by`;
3. a capability profile that is not deterministic, combining `sandboxed-grunt` with
   "execution none or direct validator as assigned";
4. an A1 record (round 2) attributing `recorded_by = Architect` to a session holding
   implementation-only authority.

**None of these is reachable by this rule.** There is no executable contract to make fail,
so there is no red-first case; "adjacent case" has no meaning for a missing field in a
document; and there is no set for a property test to quantify over. These defects were
found by **enumerating the binding conditions from the authority record and checking the
candidate against each** — a conformance checklist — and by **authority checking**.

Demanding a red-first case for a document-shaped change will produce a manufactured one.
Reviewers must not do it, and implementers must not offer it.

## 3. Stale-baseline and current-state drift

`0044-04` round 1's fourth defect was that **after the candidate was pinned**, branch
`0043-06` was created and completed without the promised branch-time record, so a
prospective pilot point could no longer be completed as written.

This is not a property of the artefact. The artefact did not change; the world did. No test
of any kind — red-first, adjacent, or property-based — can detect it, because every test
runs against the pinned candidate. It is found only by **re-measuring current state against
the pinned baseline at review time**, which the existing acceptance procedure already
requires. This rule adds nothing there and must not be read as covering it.

## 4. Authority, independence and process defects

Role attribution, capability-class determinism, independence of reviewer from implementer,
checkpoint placement, prerequisite-closure completeness, and acceptance-record validity are
governed by `AGENTS.md`, `docs/pipeline/process-roles.md` and
`docs/pipeline/task-acceptance.md`. Conforming adversarial evidence is **not** a substitute
for any of them, and its absence is not an authority finding. A candidate with exemplary
red-first evidence can still be rejected on authority grounds — `0038-33` was in fact
returned `inconclusive` on exactly such a boundary while its technical evidence was found
fully conforming.

## 5. Discovery guarantees

The rule does **not** guarantee that a defect will be found. It guarantees that the
question was asked and the answer recorded. Both code defects in the evidence base were
found by **reading the code** and reproducing hermetically; the property test *closed*
`0038-31`'s defect rather than finding it. Conforming evidence is therefore not a
substitute for a reviewer reading the change, and a reviewer must not treat green
adversarial evidence as licence to skip inspection. That would reproduce, one level up,
precisely the confirmatory-evidence failure this rule exists to address.

## 6. What is not weakened

Nothing in this requirement or its exclusions reduces any existing obligation. Integration
checkpoints, Architect checkpoint authority, reviewer independence, prerequisite-closed
acceptance, the `[u]` integration verdict, provenance, and the hygiene gate are unchanged.
The rule is purely additive: one new obligation on the implementer for four named change
kinds, and one explicit permission for the reviewer to reject on its absence.
