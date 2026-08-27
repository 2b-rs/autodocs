# `0038-34` — drafted requirement text (DRAFT, NOT APPLIED)

- **Author:** `Tom-Sisko-20260825T091500Z`, Implementierer, unprivileged
- **Status:** **draft proposal.** Not policy. Not applied to `AGENTS.md` or `TODO.md`.
- **Gate:** applying this text is the mutation gated by the cross-item gate-scope review
  exception. It requires a recorded `decision-record@v1` (drafted as
  `draft-DEC-0038-004.md`) and an independent Architect scope review, neither of which
  exists yet.

The text below is derived from the corrected diagnosis in `review-record-analysis.md`.
The central change against the node's own phrasing: the requirement is stated as
**"derive the negative cases from the contract claim and write them down before the fix"**,
which is checkable, rather than "be adversarial", which is not.

---

## A. Proposed insert — `AGENTS.md`, § *Completing implementation work*

To be inserted as a new subsection after step 4 (the `[x]`/`REF` bookkeeping step), since
that is where completion evidence is described.

> ### Adversarial completion evidence for four change kinds
>
> A change that touches **counting, identity, serialisation, or gate behaviour** carries a
> heightened evidence requirement. These four kinds share a property: their defects sit
> next to the change rather than in it — one field over, one count over, one occurrence
> over — and a test that demonstrates the fix working will not reach them.
>
> Before writing the fix, derive the negative cases from the **contract claim the change
> makes** and write them down. Where a decision record, Architect scope review, or Task
> text already names the cases that must go red, cite those rather than inventing a
> parallel set. The completion evidence then shows:
>
> 1. **A red-first case.** At least one case that fails **before** the fix and passes
>    after, with the real command and its real output in the evidence — not a claim that
>    it was observed. If the change is a fix, this is the defect itself; if the change is
>    new behaviour, it is the behaviour's absence.
> 2. **At least two named adjacent cases.** State which neighbouring cases were
>    deliberately checked and what each result was. Name the case, not the category.
>    **A case that turned out fine is a pass; naming none is not.** The obligation is to
>    have looked and to say where.
> 3. **A property test where an invariant over a set is asserted.** Deduplication,
>    merging, closure and ordering changes assert something about every member of a set,
>    and hand-enumerated cases run out exactly at the collision and multiplicity cases
>    that matter. Where the change makes such an assertion, a property-based test is
>    required and **its case count is reported**.
>
> Ask specifically what the **concealing** failure direction would look like — a finding
> that disappears, a count that is silently low, a consumer that cannot distinguish absent
> from zero. That direction is worse than the inflation or noise a fix usually targets,
> and it is the direction a confirmatory test never visits.
>
> This requirement is deliberately bounded. It applies to the four named change kinds and
> is not a general instruction to be adversarial everywhere; see
> [`docs/pipeline/task-acceptance.md`](docs/pipeline/task-acceptance.md) for what it does
> not cover. A requirement that applies everywhere is satisfied ritually and stops
> meaning anything.
>
> An integration reviewer may reject completion evidence that omits a required element,
> and does so without re-deriving the missing case itself. Producing the evidence is the
> implementer's work; this does not transfer to the reviewer.

## B. Proposed insert — `TODO.md` header contract

To be inserted in the header where completion/`[x]` semantics are defined, kept short
because the header is a reference and not a tutorial.

> **Adversarial completion evidence.** When a Task touches **counting, identity,
> serialisation or gate behaviour**, `[x]` additionally requires: (1) a **red-first** case
> shown failing before the fix and passing after, with the real command and output;
> (2) **at least two named adjacent cases** with their results — naming a case that turned
> out fine is a pass, naming none is not; (3) where the change asserts an **invariant over
> a set** (deduplication, merging, closure, ordering), a **property-based test with its
> case count reported**. Derive these from the contract claim the change makes, and write
> them down before the fix; where a decision record or scope review already names the
> cases that must go red, cite those. This applies to those four change kinds only — see
> `AGENTS.md` → *Adversarial completion evidence for four change kinds*, and the scope
> exclusions in `docs/pipeline/task-acceptance.md`. It weakens no existing acceptance,
> checkpoint or integration requirement.

## C. Notes on drafting choices

1. **"Derive from the contract claim … before the fix" replaces "be adversarial".**
   Justified in `review-record-analysis.md` §2: in three of four cited cases the defect
   was found because the question had been named in advance, in a briefing or in
   `DEC-0038-002`. Naming, not role, is the transferable mechanism.
2. **The property-test requirement is justified as a *closing* mechanism, not a finding
   mechanism.** `0038-31`'s defect was found by code reading; the 10,000 property cases
   closed it. The draft does not claim otherwise.
3. **"Name the case, not the category"** is included because the obvious ritual-compliance
   failure for criterion (2) is to write "checked adjacent serialisation behaviour" and
   stop.
4. **The concealing-direction paragraph** is the single most transferable sentence in the
   evidence base: both code defects (`0038-31`, `0044-16`) were concealing-direction
   defects, and both reviewer briefings had pointed at that direction explicitly.
5. **No existing requirement is weakened.** The draft adds an obligation on the implementer
   and an explicit permission for the reviewer to reject on its absence. It does not touch
   checkpoint placement, acceptance authority, independence, or the prerequisite-closure
   rule.
6. **Placement of the exclusion statement.** The full exclusions belong in
   `docs/pipeline/task-acceptance.md`, because a reviewer is the party who needs to know
   when *not* to demand the evidence. `AGENTS.md` and the header both link to it. That
   third file is a proposed addition to the eventual write scope and is drafted separately
   in `scope-exclusions.md`.
