# Drafted decision record for `0038-34` (DRAFT — NOT A RECORDED DECISION)

- **Author of the draft:** `Tom-Sisko-20260825T091500Z`, Implementierer, unprivileged
- **Status:** **draft prepared for Architect review.** This file is not a recorded
  decision and does not satisfy the cross-item gate-scope review exception.
- **Identifier caveat:** `DEC-0038-004` is the next free identifier as of `main`
  `bd768cb3ce571491d332e9ea26029f8f0e4aedf9` (`DEC-0038-001`, `-002`, `-003` are taken).
  `AGENTS.md` requires the allocation point to be `main`; a parallel line may claim it.
  **Whoever records this must re-check the identifier against `main` at recording time.**
- **Intended destination on recording:** `docs/dossiers/dec-adversarial-completion-evidence.md`
  (new dossier), on a branch cut from `main`, per `DEC-0044-012`.
- **Open field:** `Review participation` cannot be completed by this session. The Architect
  scope review does not yet exist; the `PART-01` block below is marked as a placeholder and
  **must be completed by the reviewing Architect, not by the implementer.** Per
  `decision-record@v1` §4, an implementer must not infer or invent it.

---

### `DEC-0038-004` — Adversarial completion evidence for counting, identity, serialisation and gate-behaviour changes

- **Record format:** `decision-record@v1`
- **Recorded at:** `<to be set by the recording authority, ISO-8601 with timezone>`
- **Deciding identity:** `<to be set by the recording authority>`
- **Role:** `Architekt`
- **Authority reference:** `TODO.md#0038-34` — Architect checkpoint decision of
  2026-08-24 by Architect `seven`, confirming `Integration review: mandatory` and
  restating that a `decision-record@v1` plus an independent Architect scope review are
  required before any requirement text is written.
- **Subject:** Whether to add a bounded, mandatory completion-evidence requirement —
  a red-first negative case, at least two named adjacent cases, and a property test for
  set invariants — to `AGENTS.md`'s completion section and the `TODO.md` header contract,
  applying to changes that touch counting, identity, serialisation or gate behaviour; and
  the exact reach of that requirement.
- **Decision:** Add the requirement, bounded to those four change kinds, in the form
  drafted at `docs/campaign-evidence/0038-34-analysis/draft-requirement-text.md`, together
  with the exclusion statement drafted at
  `docs/campaign-evidence/0038-34-analysis/scope-exclusions.md`, which is recorded in
  `docs/pipeline/task-acceptance.md`. The requirement is framed as *derive the negative
  cases from the contract claim the change makes and write them down before the fix* — not
  as a general instruction to be adversarial. Document-contract conformance defects and
  stale-baseline drift are explicitly outside its reach. No existing acceptance,
  checkpoint, independence or integration requirement is weakened; the change is purely
  additive.
- **Technical justification:** Four independent reviews on 2026-08-22 rejected work whose
  own tests were green, and in each case the defect was real. Verification of those four
  records against their primary sources
  (`docs/campaign-evidence/0038-34-analysis/review-record-analysis.md`) confirms the
  phenomenon for the two code cases but corrects the causal account in the originating
  Task text. The discriminating variable is not implementer-versus-reviewer: in
  `0038-31` and `0044-16` the reviewer's verbatim briefing named the dangerous error
  direction before the review began, and in `0038-33` — the case that passed technical
  review with no nonconformity — `DEC-0038-002` had named the four cases that must go red
  before implementation started. Where the question was named in advance it was answered,
  regardless of who answered it. The requirement therefore mandates the naming, which is
  checkable, rather than an attitude, which is not. Both code defects lay in the
  *concealing* direction — a finding silently dropped, and a consumer unable to
  distinguish absent from zero — which is the direction a confirmatory test never visits.
  The property-test element is justified as a *closing* mechanism: `0038-31`'s defect was
  found by reading the union code and reproducing it hermetically, and was closed by
  10,000 generated cases after ten hand-written tests had provably run out at the
  line-collision case. The bound to four change kinds is deliberate: a requirement that
  applies to every Task is satisfied ritually and stops discriminating, which is the
  failure mode the checkpoint attribute already had to be protected from.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Add the bounded three-part requirement to `AGENTS.md` and the `TODO.md`
    header, with an explicit exclusion statement in `docs/pipeline/task-acceptance.md`.
    - **Disposition:** `selected`
    - **Reason:** Places the obligation where implementers actually read it and the
      exclusions where reviewers do. Bounded to four change kinds with a stated reason,
      so it discriminates. Each of the three elements is independently evidenced by a
      real 2026-08-22 review record, and each is objectively checkable by a reviewer
      without re-deriving the implementer's work.
  - **ALT-02:** Record the requirement only in a dossier or decision record, leaving
    `AGENTS.md` and the header contract unchanged.
    - **Disposition:** `rejected`
    - **Reason:** The originating Task's acceptance criterion (4) rejects it explicitly,
      and the evidence supports that: the mechanism that worked in `0038-33` worked
      because the required cases were placed in a document binding on the implementer
      before implementation. A dossier nobody is required to read reproduces the current
      state, in which the requirement exists only when a dispatcher happens to name it in
      a briefing.
  - **ALT-03:** Require adversarial evidence for every Task, unbounded.
    - **Disposition:** `rejected`
    - **Reason:** Unfalsifiable and self-defeating. A universal requirement is satisfied
      ritually; and the `0044-04` defect class (missing document field, schema
      nonconformity, non-deterministic capability profile, post-pin drift) cannot produce
      a red-first case at all, so the universal form would force manufactured evidence for
      document-shaped work.
  - **ALT-04:** Instead of an implementer obligation, require every reviewer briefing to
    name the dangerous error direction.
    - **Disposition:** `deferred`
    - **Reason:** This is the mechanism the evidence most directly demonstrates — it is
      what actually happened in `0038-31` and `0044-16` — and it is a genuine candidate.
      It is deferred rather than rejected because it places the obligation on dispatchers
      rather than implementers and so has a different, larger blast radius across the
      dispatch protocol; it is complementary to ALT-01 rather than exclusive, and should
      be considered as its own work unit. Recorded here so the option is not lost.
- **Consequences:**
  - **CON-01:** Every future implementer of a counting, identity, serialisation or
    gate-behaviour change carries an additional, non-trivial evidence obligation, and
    integration reviewers gain an explicit ground for rejection when it is absent.
  - **CON-02:** Cost. Deriving negative cases before the fix and reporting property-test
    case counts adds work to exactly the change kinds that are already the most delicate.
    This cost is accepted deliberately, against four same-day defects that would otherwise
    have shipped.
  - **CON-03:** Boundary-judgement risk. "Touches counting, identity, serialisation or
    gate behaviour" requires judgement at the margin. Mitigated by the rule that scope
    follows the change's *claim*, not its file, and by the worked example.
  - **CON-04:** Ritual-compliance risk remains and is not eliminated. An implementer can
    name two adjacent cases that are trivially safe. Mitigated only partially, by
    requiring the case to be named rather than the category, and by the reviewer's
    retained obligation to read the change; explicitly recorded as a residual risk.
  - **CON-05:** The `0038-34` Task text itself contains four statements the source-record
    verification does not support and which should be corrected under this decision:
    the confirmatory/refutational causal claim, the inclusion of `0044-04` in the evidence
    base, the implication that property testing found the `0038-31` defect, and the
    description of `0038-33` as having passed review (its recorded verdict is
    `inconclusive`, on an authority boundary, with no technical nonconformity).
  - **CON-06:** Rollback boundary. The change is additive text in three documents and
    carries no migration or external effect; reverting it restores the prior contract
    exactly, though completion evidence already produced under it remains valid.
- **Affected work units:**
  - `task:0038-34`
  - `path:AGENTS.md`
  - `path:TODO.md`
  - `path:docs/pipeline/task-acceptance.md`
  - `repository:autodocs`
- **Affected gates:**
  - `integration:0038-34`
  - `validation:docs/pipeline/task-acceptance.md`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `<Architect session token — to be supplied by the reviewing Architect>`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `<supports | opposes | no-position — to be supplied by the reviewer>`
    - **Note:** `<to be supplied by the reviewer>`
- **Waiver:** `none`

---

## Conformance notes for the recording authority

1. The three bracketed placeholders (`Recorded at`, `Deciding identity`, and the whole
   `PART-01` block) are **deliberately unfilled**. `decision-record@v1` §3.1 forbids
   placeholders such as `TBD` in a *published* record; this file is explicitly a draft and
   is not published as a record. The record becomes conforming only when the Architect
   supplies its own participation block and the recording authority supplies identity and
   timestamp. The implementer must not fill these in.
2. `Review participation: none` would also be format-conforming, with a mandatory
   `No-review reason` — but it is **not available here**, because the cross-item gate-scope
   review exception independently requires an Architect scope review distinct from the
   implementer. The record cannot be honestly recorded with `none`.
3. Two triggers are listed; `decision-record@v1` §2 makes them alternative, so either
   alone would suffice. Both are stated because both are true.
4. `ALT-04` is `deferred`, which §3.2 permits for non-selected alternatives.
