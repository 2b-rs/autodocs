# `0038-34` — verification of the diagnosis against the four real review records

- **Author:** `Tom-Sisko-20260825T091500Z`, Implementierer, unprivileged
- **Date:** 2026-08-25
- **Base:** `main` at `bd768cb3ce571491d332e9ea26029f8f0e4aedf9`
- **Assignment:** the node's own Definition of Done — *"Analysis first, then the rule.
  Before writing any requirement text, verify the diagnosis against the actual review
  records rather than against this summary. … If the evidence does not support the
  confirmatory/refutational split … say so and correct this Task instead of implementing
  a rule built on a wrong reading."*

## 0. Sources actually read

Each record was read from its own review branch, not from the node's summary:

| Case | Source (`git show <ref>:<path>`) |
|---|---|
| `0038-31` round 1 | `review-0038-31-kolos-20260822T153500Z:docs/campaign-evidence/review-0038-31-20260822/report.md` |
| `0044-16` | `review-0044-16-data-geordi-20260822T205520Z:docs/campaign-evidence/review-0044-16-20260822-data-geordi/report.md` |
| `0044-04` round 1 | `review-0044-04-harry-bellana-20260822T201200Z:docs/campaign-evidence/review-0044-04-20260822-harry-bellana/report.md` |
| `0038-33` | `review-0038-33-data-geordi-20260822T203512Z:docs/campaign-evidence/review-0038-33-20260822-data-geordi/report.md` |

Two of these (`review-0038-31-20260822-data-geordi`, `review-0044-16-…-r2`) also exist on
`main` under `docs/campaign-evidence/`; the round-1 records that produced the rejections
live only on their review branches.

## 1. Verdict on the node's diagnosis

The node states:

> **Diagnosis:** implementer tests are **confirmatory** — they demonstrate that the fix
> works. Reviewer tests are **refutational** — they look for what the fix broke. All four
> defects were *neighbours* of the change: one field over, one count over, one role over.

**Partly confirmed, materially corrected.** The observation that the defects sat next to
the change is right for two of the four cases and the phenomenon is real. But the
*causal* claim — that the split runs along the implementer/reviewer role boundary — is
**not what the records show**, and one of the four cases does not belong in the evidence
base for a test-evidence rule at all.

Per §5 of the dispatch briefing, where the evidence does not fit the offered binary I say
so rather than forcing it. There are two such places.

---

## 2. X1 — "neither confirmatory-vs-refutational, but: was the dangerous direction named as a question in advance?"

The records show the discovery mechanism in each case. It is not the reviewer's role.

### 2.1 `0038-31` round 1 — the question was in the briefing, verbatim

The reviewer (`Kathryn-Kolos-20260822T153500Z`) found a real finding-loss regression. But
§7 of that report reproduces the dispatcher's briefing verbatim, and it contains:

> **Die gefährliche Fehlerrichtung:** Kann der neue Schlüssel einen echten Befund
> verschlucken? … Lauf die Tests, aber verlass dich nicht nur auf sie — **lies den
> Vereinigungscode selbst.**

The dangerous error direction was *named by the dispatcher before the review started*.
The reviewer's own §6 disclosure is careful about this: it records that the specific
defect in §2 "war im Briefing nicht benannt" — the defect was not named, but **the
direction to look in was**. That is exactly the difference between a briefing that leaks
the answer and one that supplies the question.

Two further details matter for the rule being drafted:

- **The mechanism of discovery was code reading plus a hermetic `/tmp` reproduction, not
  a test.** The report's §2 sets out the mechanism (`kept.extend(occurrences[len(kept):])`
  padding positionally, then the line-keyed `_dedupe` collapsing the pair) and then
  reproduces it in a throwaway Git repo.
- **The 10,000 property cases came in the re-review and *closed* the defect; they did not
  find it.** The node's summary — "the re-review closed it only with 10,000 property
  cases" — is accurate, but it must not be read as evidence that property testing is the
  *finding* mechanism. It is the *closing* mechanism. A rule that requires property tests
  should be justified on that basis, not on a discovery claim the record does not support.

The implementer's ten tests genuinely missed the case, and the report says precisely why:
`test_worktree_only_finding_is_not_hidden_by_a_clean_index` checked the insertion position
*after* the existing occurrence, where the line numbers do not collide. That is a
confirmatory test in the node's sense. So far the node is right.

### 2.2 `0044-16` — the question was in the briefing, as an explicit check item

The reviewer (`Data-Geordi-20260822T205520Z`) found that `index_age_seconds`,
`index_mtime_utc` and `resample_delay_seconds` serialise as `null` on every non-persistent
finding. The verbatim briefing in that report contains, as its own sentence:

> Verify `index_age_seconds`, `index_mtime_utc`, `resample_delay_seconds` appear only for
> persistent findings.

Again the reviewer was pointed at the exact contract claim and asked to check its negative
side; again the mechanism was a fixture reproduction (the report prints the offending JSON
for a `MAIN_WORKTREE_DIRTY` finding). The defect is a genuine neighbour — "one field over",
via the shared `Finding` dataclass and a blanket `asdict()`.

### 2.3 `0038-33` — the counter-example, and it proves X1 rather than the node's diagnosis

The node calls `0038-33` "the informative one" because the implementer produced four
independently red cases. The record confirms the facts, and its §5 shows the reviewer
independently re-ran each of the five focused tests **as its own one-test process**, then
went further than the candidate did — invoking `assert_runner_transaction_control` without
the `assertRaises` wrapper, and mutating real source text and rescanning it with the real
`automation_safety.scan_text`.

But the node draws the wrong lesson from it. The implementer was not spontaneously
adversarial. **`DEC-0038-002` named the four red cases for him** — a sixth finding, a moved
one, a renamed symbol, a byte-changed evidence hash — as a binding constraint written by
someone else *before* implementation. The node itself says so ("named four cases that must
go red") and then attributes the result to a difference in the kind of testing rather than
to the naming.

This is the load-bearing correction. The transferable mechanism is not "implementers should
be refutational" — an instruction of that shape is unfalsifiable and will be satisfied
ritually, which the node's own *Deliberately bounded* paragraph already identifies as the
failure mode to avoid. The transferable mechanism is: **the negative cases were written
down, derived from the contract claim, before the fix was written.** Whoever then executes
them — implementer or reviewer — finds the defect.

### 2.4 One factual correction to the node

The node says `0038-33` "passed its technical review at the first attempt". Technically
accurate — the record finds no candidate critical, major, minor or authority-scope
nonconformity. But the **recorded verdict is `inconclusive`, not `accepted`**, and for a
reason unrelated to the work: the prerequisite-closure rule expanded the target into a
30-item bottom-up batch with 29 unaccepted ancestors, which that assignment did not
authorise. The node's phrasing should be corrected, because a future reader checking the
record will not find an acceptance there.

---

## 3. X2 — `0044-04` cannot support this rule, and belongs in the exclusion statement

This is the second place where the evidence does not fit the offered binary.

The node lists `0044-04` rounds 1 and 2 alongside two code defects and characterises all
four as neighbours, "one role over". The round-1 record lists four material defects:

1. binding Architect scope-review condition **A-09 not fulfilled** — `RQ-IP-02` is absent
   from the Task's `Requirements covered` field;
2. the retained pilot calls malformed prospective placeholders A1 records, though the
   normative schema permits only `fits|does-not-fit` and requires `checked_at` and
   `recorded_by`;
3. the `0043-06` capability profile is **not deterministic** — it combines
   `sandboxed-grunt` with "execution none or direct validator as assigned";
4. **current-state drift**: after the candidate was pinned, branch `0043-06` was created
   and completed without the promised branch-time A1 record, so the prospective pilot
   point can no longer be completed as written.

None of these is test-shaped.

- (1) is a **missing field in a document**, found by enumerating the binding conditions
  from the authority record and checking the candidate against each. The briefing said so:
  "Prüfschwerpunkte: alle 15 bindenden Bedingungen, sechs Vor-Mutations-Bedingungen".
  That is a conformance checklist, not a refutational test.
- (2) and (3) are **schema and determinism conformance** of prose artefacts. A red-first
  case is not available: there is no executable contract to make fail.
- (4) is not a property of the artefact at all. It is a property of **the world having
  moved after the candidate was pinned**. No test of any kind — red-first, adjacent, or
  property-based — can catch it, because the artefact did not change; reality did. It is
  found only by re-measuring current state against a pinned baseline.

Round 2's defect (an A1 record attributing `recorded_by = Architect` to a session holding
implementation-only authority) is the closest to "one role over", but it too is a document
attribution error caught by authority checking, not by a neighbour case.

**Consequence for the rule.** Citing `0044-04` as evidence for an adversarial *test*
evidence requirement overstates the rule's reach and invites exactly the ritual compliance
the node warns against: an implementer facing a document-shaped task will be asked for a
red-first case that does not exist, and will manufacture one. `0044-04` should be moved out
of the rule's evidence base and into its **scope-exclusion statement**, where it is
genuinely valuable: it is the clearest available demonstration of a defect class this rule
does not and cannot cover. The Definition of Done already requires such a statement.

---

## 4. What survives, and what the rule should therefore require

Confirmed by the records and safe to build on:

- **The neighbour phenomenon is real** for the two code cases (`0038-31`, `0044-16`) and
  both defects would have shipped. The node's acceptance criterion (2) — name at least two
  adjacent cases and their result — is well supported.
- **The dangerous-error-direction framing is real and is the operative one.** In both code
  cases the defect lay in the *concealing* direction: a finding disappearing (`0038-31`),
  a consumer unable to distinguish absent from zero (`0044-16`). Both are contract claims
  whose negative side was checkable and had not been checked.
- **Property testing is justified as a closing mechanism** for set invariants: `0038-31`'s
  defect was a multiplicity/collision case in a deduplication union, which is precisely
  where hand-enumerated cases run out. Acceptance criterion (3) stands, on that
  justification rather than on a discovery claim.
- **Red-first with real command and output** is supported by `0038-33`, where the reviewer
  could re-run each named case as its own process and observe it fail. Acceptance
  criterion (1) stands.

Corrected, and to be carried into the requirement text:

- The requirement must be framed as **"derive the negative cases from the contract claim
  and write them down before the fix"**, not as "be adversarial". The former is checkable
  and was the actual mechanism in three of four cases; the latter is not checkable.
- Where a decision record or scope review already names the cases that must go red, the
  completion evidence **cites them** rather than inventing a parallel set — `DEC-0038-002`
  is the model.
- The rule is bounded to the four named change kinds and explicitly excludes the
  document-conformance and baseline-drift classes that `0044-04` exemplifies.

## 5. Proposed amendments to the `0038-34` node text

Offered for the Architect's consideration; **not applied by this session**, since the node
text sits in `TODO.md` and this pass is gated.

1. Replace the diagnosis sentence with the X1 formulation: the split is not
   implementer-vs-reviewer but *named-question-vs-unnamed*, evidenced by the two verbatim
   briefings and by `DEC-0038-002`.
2. Move `0044-04` from the evidence list to a new "what this does not cover" note, with
   its four defects as the worked negative example.
3. Correct "the re-review closed it only with 10,000 property cases" to make explicit that
   code reading found the defect and the property test closed it.
4. Correct "passed its technical review at the first attempt" to note the recorded verdict
   is `inconclusive` on an authority/package boundary, with no technical nonconformity.
