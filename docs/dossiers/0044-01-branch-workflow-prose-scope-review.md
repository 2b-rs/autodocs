# Task `0044-01` — Architect gate-scope review of the `branch-workflow.md` prose completion

**Status:** Architect scope review under the Cross-item gate-scope review
exception (`AGENTS.md`, "Autonomous backlog repair"). This record opens the
gated `branch-workflow.md` mutation Implementer `seven-rebi` stopped before
(`TODO-seven-rebi-0044-01-20260820T235543Z.md`); it is not Task acceptance, an
integration verdict, or `Acceptance: ✓`.

**Reviewer:** `agent:seven-bellana:0044-01-architect-review:20260821T000000Z`
(Architect persona, capability_class `privileged`), independent of the
Implementer identity `agent:seven-rebi:0044-01:20260820T235543Z`.

## 1. Independent gate-scope judgment

Seven-Rebi's claim identifies two candidate gated deliverables under the
`branch-workflow.md` "Integration policy precedence" section: (2) the draft
`decision-record@v1` for `RQ-IP-03`'s per-integration `TK-2` duty, and (3) the
`branch-workflow.md` prose completion itself (explicit A1–A4 case distinction
plus the `0044-04` cross-reference). I reviewed both independently rather than
adopting her conclusion by default.

**On (2), the `RQ-IP-03` per-integration duty:** her ground 2 is correct and,
on inspection, not really a judgment call — `RQ-IP-03`
(`docs/dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md`
line 74) states the choice is `TK-2`-pflichtig in the customer's own words.
Recording *that a duty exists and its record shape* is squarely
`cross-item-blast-radius` (`integration:0044` and every future `RQ-IP-03`
replacement) and `authority-tailoring-or-waiver` (the replacement option is
itself a bounded exception to strict target-policy precedence). I agree it is
gated and requires an Architect-countersigned record before being treated as
binding, per the exception's rule that a draft by the Implementer alone is
explicitly insufficient.

**On (3), the prose completion:** I independently re-derived this rather than
trusting the summary. I pulled the source table directly:
`docs/dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md`
§2.1 (lines 57–62) already states the full A1–A4 table verbatim, decided by
the customer on 2026-08-20 and anchored by `DEC-0044-001..003`. `RQ-IP-02`
(same file, lines 70–73) already ties A1/A2 prevention to "Prüfung bei
Breakdown/Branch-Anlage" — i.e., to the feature-breakdown/branch-creation
process, which is exactly `0044-04`'s own pre-existing scope ("Write the
feature-breakdown process instruction: ... plus the per-task capability
requirement profile and branch instruction", `TODO.md` line 109). So the
*content* of the A1–A4 labels and the `0044-04` link is not a new
architecture choice by the Implementer or the Architect — it is already fully
decided by Management and by the pre-existing `0044-04` Task definition;
transcribing it is much closer to Negative-2 ("unambiguously determined ...
repair") than to a genuine drafting choice.

However, I disagree with treating that as dispositive on its own. Two things
still push this over the gate, and I concur with Seven-Rebi's bottom-line
conclusion that (3) is gated, for reasons distinct from hers:

- `branch-workflow.md`'s "Integration policy precedence" section is the text
  every future integrator reads to decide which policy governs a merge, for
  every Feature in the repository, and the section is explicitly under
  `Integration review: mandatory` for `0044-01`. Editing it — even to make an
  already-decided rule more explicit and mechanically checkable — is
  `cross-item-blast-radius` under the trigger table's own text ("regardless
  of whether the deciding node is marked as an integration checkpoint").
  Negative-2 requires not only an unambiguous target but also "no normative
  meaning change"; adding four explicit, individually labeled case
  definitions where the current text merges A1/A2 into a single combined
  sentence, and adding a new forward reference to a Task (`0044-04`) whose
  content does not exist yet, is more than a typo/link repair even though the
  underlying decision is settled.
- The Task's own acceptance criteria (`TODO.md` line 93) explicitly requires
  the A1–A4 distinction and the `0044-04` cross-reference "consistently with
  `AGENTS.md` and `task-acceptance.md`" — i.e., the Task itself treats this as
  a normative anchoring step, not incidental prose polish.

**Conclusion:** I agree the gate applies to (2) and (3). Seven-Rebi was not
being overcautious; she correctly identified a case where content is largely
pre-decided but the *anchoring act itself* still meets the closed
`cross-item-blast-radius` predicate. I disagree only with her framing that
this requires new "normative granularity ... not itself dictated verbatim by
the customer" for A1–A4 specifically — the A1–A4 labels *are* dictated
verbatim (§2.1's table); what is not yet dictated is the exact prose
integration and the `0044-04` cross-reference wording, which is enough on its
own to trigger the gate under `material-architecture-or-repository-behavior`
(establishing durable process-rule text) even without leaning on the label
question.

## 2. Decomposition check: does `0044-04` exist?

Checked directly: `TODO.md` line 109 — `0044-04` **exists** as a real,
currently open, unclaimed Task ("Write the feature-breakdown process
instruction: derivation sources for architecture decisions, task
dependencies, and test cases, plus the per-task capability requirement
profile and branch instruction. *(architect-elaboration)*"), with no
prerequisites blocking its start. Seven-Rebi's own hedge ("`0044-04`'s
not-yet-written breakdown instruction") is accurate as a statement that
`0044-04`'s *content* doesn't exist yet, but does not mean `0044-04` is
missing from the backlog. The cross-reference `0044-01` must add is a forward
pointer to a real, already-decomposed Task, not to a placeholder that must
first be created. This is not a decomposition defect requiring repair.

## 3. Disposition

Not a management/`[u]` boundary case: no materially different valid product
architecture is being chosen here (the content is customer-decided; only the
anchoring act needed distinct Architect review), no authority is being
tailored beyond what the exception itself already requires, and no
credential/security/release boundary is touched. This is squarely the
Architect scope-review role the exception describes. I therefore:

1. Countersign a corrected, Architect-authored `DEC-0044-005` below (adapting
   Seven-Rebi's draft — content was sound; only identity/role/review-participation
   needed correction to become authoritative).
2. Record a new `DEC-0044-006` below for the `branch-workflow.md` A1–A4/`0044-04`
   anchoring act itself.
3. Perform the now-unblocked `branch-workflow.md` prose completion myself in
   this same session (Architect, not Implementer, doing the specific gated
   mutation the exception names as an acceptable outcome), leaving
   Seven-Rebi's tool, tests, and claim file otherwise untouched.

### `DEC-0044-005` — Integrator policy-replacement choice is a per-integration `TK-2` record

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-21T00:00:00Z`
- **Deciding identity:** `agent:seven-bellana:0044-01-architect-review:20260821T000000Z`
- **Role:** `Architekt`
- **Authority reference:** `task:0044-01`, elaborating `DEC-0044-001..003`
  (`docs/dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md`,
  `RQ-IP-03`); scope review conducted per the Cross-item gate-scope review
  exception (`AGENTS.md`)
- **Subject:** Which record format and duty apply when an integrator exercises
  the `RQ-IP-03` policy-replacement option (case A3) during a real
  integration.
- **Decision:** Each time an integrator replaces the governing integration
  policy under `RQ-IP-03` (case A3: target policy changed post-branch-out for
  a non-planning-error reason), the integrator MUST, before completing that
  integration, record a `decision-record@v1` naming: the two branches
  integrated, the replaced-from and replaced-to policy versions (commit SHAs
  of the policy path on each), why the replacement version was chosen over
  other valid-since-branch-out versions on either branch, and the affected
  work units/gates (at minimum the integration itself). This duty is
  per-integration, not a one-time process decision; `DEC-0044-005` only
  anchors that the duty exists and its record shape.
- **Technical justification:** `RQ-IP-03` already states the choice is
  `TK-2`-pflichtig; `DEC-0044-001..003` already establish the underlying
  policy-replacement permission. This record makes explicit, in canonical
  `decision-record@v1` vocabulary, which trigger applies and what the
  resulting record must contain, so a future validator or the `0044-08`
  end-to-end proof can check the duty was met rather than re-deriving it from
  prose each time.
- **Triggers:**
  - `cross-item-blast-radius`
  - `authority-tailoring-or-waiver`
- **Considered alternatives:**
  - **ALT-01:** Require a full `decision-record@v1` per replacement, as stated
    above.
    - **Disposition:** `selected`
    - **Reason:** Matches `RQ-IP-03`'s explicit `TK-2` language and keeps
      every policy-governing-merge decision traceable and reviewable.
  - **ALT-02:** Fold the replacement rationale into the ordinary integration-
    review commit message, without a separate decision record.
    - **Disposition:** `rejected`
    - **Reason:** Commit messages are not append-only, structurally
      checkable, or reliably cross-referenced by later validators; `RQ-IP-03`
      names `TK-2` explicitly, which under `decision-record.md` means the
      canonical format, not free text.
- **Consequences:**
  - **CON-01:** Every A3 replacement integration gains one additional
    committed artifact before it can close; bounded, matches existing `TK-2`
    overhead elsewhere.
  - **CON-02:** A validator can be built against a stable record shape
    instead of free text.
- **Affected work units:**
  - `feature:0044`
  - `task:0044-01`
  - `task:0044-02`
- **Affected gates:**
  - `integration:0044` (and, prospectively, every future Feature integration
    exercising `RQ-IP-03`)
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:seven-bellana:0044-01-architect-review:20260821T000000Z`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Content adapted from Implementer's draft after independent
      re-derivation from `RQ-IP-03`'s own text; only identity/role/authority
      fields required correction to become authoritative.
- **Waiver:** `none`

### `DEC-0044-006` — Anchor the A1–A4 case distinction and the `0044-04` prevention-point cross-reference in `branch-workflow.md`

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-21T00:00:00Z`
- **Deciding identity:** `agent:seven-bellana:0044-01-architect-review:20260821T000000Z`
- **Role:** `Architekt`
- **Authority reference:** `task:0044-01`, `RQ-IP-02`
  (`docs/dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md`
  §2.1/§3, table A1–A4); scope review conducted per the Cross-item gate-scope
  review exception (`AGENTS.md`)
- **Subject:** Whether and how to make the `branch-workflow.md` "Integration
  policy precedence" section state the A1–A4 case distinction explicitly and
  name `0044-04` as the mechanical prevention point for cases A1/A2.
- **Decision:** `branch-workflow.md`'s "Integration policy precedence"
  section is amended to explicitly label the four cases (A1–A4) already
  decided in `DEC-0044-001..003`/§2.1's table, replacing the current combined
  A1/A2 sentence with individually labeled case text, and to state that
  `0044-04` (the feature-breakdown process instruction, already an open
  backlog Task) is the prevention point required by `RQ-IP-02` for A1/A2. The
  decision content itself is not new — it transcribes the already-decided
  table and the already-defined scope of `0044-04` — but the anchoring act
  meets `cross-item-blast-radius` (binding text read by every future
  integrator, `Integration review: mandatory` node) and
  `material-architecture-or-repository-behavior` (new durable, individually
  labeled process-rule text where only a combined paraphrase existed before),
  so it required this record and review before mutation.
- **Technical justification:** See §1 of this file for the full independent
  re-derivation. In short: §2.1's table and `RQ-IP-02` already fix the
  content; `0044-04`'s existing Task definition already covers "branch
  instruction" and breakdown-time checks, so no architecture choice is being
  made here — only an anchoring act on a checkpoint-flagged document, which
  the exception's predicate still captures regardless of content novelty.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Add explicit A1–A4 labels and the `0044-04` cross-reference,
    transcribing §2.1's table content near-verbatim.
    - **Disposition:** `selected`
    - **Reason:** Matches the Task's acceptance criteria, matches the
      already-decided table exactly, and gives `check_policy_provenance.py`
      or a future validator a stable, named case vocabulary to check against.
  - **ALT-02:** Leave the current combined A1/A2 paraphrase in place and treat
    the acceptance criterion as satisfied by the existing prose.
    - **Disposition:** `rejected`
    - **Reason:** Does not meet the Task's explicit acceptance criterion
      ("the A1–A4 case distinction"); the current prose does not name
      `0044-04` as the prevention point at all, leaving `RQ-IP-02` only
      partially anchored.
- **Consequences:**
  - **CON-01:** `branch-workflow.md` becomes independently checkable
    case-by-case; a later `0044-04` implementer has an explicit, named
    integration point to satisfy.
  - **CON-02:** No existing gate behavior changes — this is anchoring, not a
    new rule — so no other in-flight Task's contract is altered.
- **Affected work units:**
  - `feature:0044`
  - `task:0044-01`
  - `task:0044-04`
- **Affected gates:**
  - `integration:0044`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:seven-bellana:0044-01-architect-review:20260821T000000Z`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Independently re-derived from the intake dossier and
      `0044-04`'s existing Task text rather than adopting the Implementer's
      framing; confirmed `0044-04` exists as a real, open, unclaimed Task
      (`TODO.md` line 109) before referencing it.
- **Waiver:** `none`

## 4. Implementation opening condition

The Architect (`seven-bellana`) is distinct from the Implementer
(`seven-rebi`) and returned `supports` on both records above. The gate for
deliverable (3), the `branch-workflow.md` prose completion, is therefore
open. I perform that mutation directly in this same review session (see the
substantive commit on branch `0044-01` following this record), rather than
handing it back, since the content is fully determined by the records above
and no further Implementer judgment remains.

This review does not grant Task acceptance, an integration verdict, or
`Acceptance: ✓` for `0044-01`. `0044-01`'s mandatory integration review
remains a separate, later step.
