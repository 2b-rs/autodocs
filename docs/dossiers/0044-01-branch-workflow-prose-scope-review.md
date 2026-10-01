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

## 5. Third-round scope review — fast-forward absorption blind spot

**Reviewer:** `agent:seven-bellana:0044-01-architect-review:20260821T030000Z`
(Architect persona, `privileged`), a third, focused review distinct from
sections 1–4 above, following Seven-Tom's third independent integration
review (`agent:seven-tom:integrator:0044-01-review:20260821T020000Z`, verdict
recorded beneath Task `0044-01` in `TODO.md`, commit `b62df43a8` on branch
`0044-01-integration-review-seven-tom-20260821T020000Z`, now fast-forwarded
onto `0044-01`).

### 5.1 What Tom found and why it is real

Rounds 1–2 found and Seven-Rebi fixed two genuine false-positive causes in
`_src/tools/check_policy_provenance.py` (detached-HEAD `(no branch)` lines,
and stale/retained branches sitting at an ancestor point on `source`'s own
first-parent line), culminating in a topology-only redesign
(`36d048ce2`/`bc01f6a76`) that classifies a policy-path commit as
`source-origin` purely from **first-parent-chain membership plus non-merge
status**, deliberately ignoring `containing_branches` as a decision input.

Round 3's finding is structural, and I independently confirm it rather than
taking Tom's word alone: `git merge --ff-only` and `git update-ref` advance a
branch tip to a target commit without ever creating a merge commit. The
absorbed commit(s) become part of the receiving branch's own first-parent
chain, with exactly one parent each — topologically indistinguishable from a
commit authored directly there. No git-native, purely local-history signal
(reflogs excepted, and reflogs are local/prunable/not shared, per Tom's own
option (b)) can tell "authored on `source`" apart from "absorbed onto
`source`'s tip via fast-forward" after the fact. Tom's minimal scratch-repo
reproduction (target-tip source branch, then `git merge --ff-only
foreign-branch`, zero merge commits) is not repository-specific; it is a
property of Git itself. I re-read `_first_parent_chain()`/`_parent_count()`
in `_src/tools/check_policy_provenance.py` (current tip `bc01f6a76`) and
confirm the code has no path that could detect this case — it is not an
implementation bug to patch, it is the necessary consequence of using
first-parent-chain topology as the classification signal at all, which is
itself the necessary consequence of `containing_branches`/branch-name
evidence having been proven unreliable in rounds 1–2. There is no fourth
purely-mechanical redesign available that closes this gap; a correct
disposition must be a documented residual limitation, a process control, or
both — not a fifth code patch.

### 5.2 Is this a `[u]`/management decision, or an Architect scope call?

I evaluate this independently against the same authority boundary the
Cross-item gate-scope review exception and `AGENTS.md`'s implementation-
completion section both describe, rather than adopting Tom's `TK-2`-reach
framing as automatically meaning "route to the user."

**What is genuinely `TK-2` (reach beyond this Task) here:** yes — this
finding affects every future integration across the repository that relies
on `check_policy_provenance.py`, not only `0044-01`, so `cross-item-blast-
radius` applies, and any change to `branch-workflow.md`'s merge-authority
prose is `material-architecture-or-repository-behavior` on a document already
flagged `Integration review: mandatory`. A `decision-record@v1` is therefore
mandatory. That is a documentation requirement, not by itself an escalation
requirement — `AGENTS.md`'s "Cross-item gate-scope review exception" and
"Autonomous backlog repair" sections both draw this same distinction
explicitly, and I already exercised exactly this authority twice this
session for `DEC-0044-005`/`DEC-0044-006` on the same document.

**What is not a genuine `[u]`/management call:** neither of Tom's two named
options requires choosing between materially different **product**
architectures the user has not already indicated a preference on, accepting
a **security/release risk on the user's behalf** beyond what `DEC-0044-001..
003`/`DEC-0044-002` already accept, changing externally controlled
configuration, or exposing credentials. Both options operate entirely within
the integration-policy architecture the user already decided on 2026-08-20
(`DEC-0044-001..003`): the target-branch-governs-precedence rule and the
foreign-branch prohibition are unchanged by either option; the only question
is which **enforcement mechanism** closes an already-known-imperfect gap in
the mechanical check the user asked `0044-01` to build. Choosing an
enforcement mechanism for an already-accepted policy, when the alternatives
differ only in strength/cost/complexity and not in what risk is accepted, is
squarely the kind of technical/process-scope call `AGENTS.md` places within
Architect authority ("only escalate ... if it requires accepting a security/
release risk on the user's behalf, or choosing between materially different
product directions the user hasn't already indicated a preference for").

I also weigh the concrete cost of reflexive escalation: this exact
fast-forward mechanism is this session's own routine mechanism for advancing
`main` (Feature `0038` integration, `0037-37`, `0037-49`, `0041-01`,
`0043-01` — all hand-verified, all legitimate), so an uninformed `[u]` here
would stall on a question the Architect role exists precisely to answer from
already-established architecture: not "is fast-forward acceptable," but
"under what condition, if any, must fast-forward give way to an explicit
merge commit so the mechanical check can see the evidence."

**Conclusion:** within Architect authority. I decide below, record it as
`DEC-0044-007`, and do not set `[u]`.

### 5.3 Decision

I select Tom's option (a) — accept the fast-forward blind spot as a
documented residual limitation, paired with a companion process control —
over option (b) for three technical reasons: (1) a reflog-based heuristic is
explicitly non-authoritative (local, prunable, not shared across clones/
worktrees) and would give a false sense of mechanical coverage for exactly
the violation shape the tool exists to catch, which is a worse property than
an honestly documented gap; (2) option (a)'s process control is enforceable
at the point of the operation itself (an agent either uses `--no-ff` for
non-predecessor absorption or it doesn't; this is directly observable in the
resulting commit graph, unlike a reflog entry that decays), and, once
followed, closes the gap **completely** for future policy-path commits,
rather than merely flagging some fraction of them for human review; (3) it
requires no new code and does not touch the classifier `check_policy_
provenance.py` just repaired three times — it changes what git operations are
permitted to reach a Task/Feature branch's first-parent chain in the first
place, which is a process rule, not a fourth attempt at a mechanical fix.

**Scope note on the broader branching/merging strategy:** this finding and
decision are narrowly about closing the mechanical check's blind spot for
policy-path commits under `DEC-0044-002`. I agree with Tom that it connects
to, but do not attempt to resolve, the broader question of this repository's
whole branching/merging (configuration management) strategy that is being
separately routed to project management via Kathryn — that broader question
may reach further (e.g., whether fast-forward should be restricted more
generally, or whether `main`-advancement itself should require a different
mechanism). `DEC-0044-007` is scoped to the `DEC-0044-002` policy-provenance
check only and does not prejudge that separate, broader review.

### `DEC-0044-007` — Accept the fast-forward provenance blind spot as a documented residual limitation, paired with a mandatory non-fast-forward absorption rule

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-21T03:00:00Z`
- **Deciding identity:** `agent:seven-bellana:0044-01-architect-review:20260821T030000Z`
- **Role:** `Architekt`
- **Authority reference:** `task:0044-01`, elaborating `DEC-0044-001..003`
  and `DEC-0044-002` specifically
  (`docs/dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md`);
  scope review conducted per the Cross-item gate-scope review exception
  (`AGENTS.md`); responds to Seven-Tom's third `[u]` integration verdict
  (`TODO.md`, Task `0044-01`, commit `b62df43a8`)
- **Subject:** How `check_policy_provenance.py`'s structural inability to
  distinguish a commit authored on `source` from a foreign commit absorbed
  onto `source`'s tip via fast-forward (`git merge --ff-only`/`git
  update-ref`, no merge commit) is disposed for Task `0044-01`'s acceptance
  criterion and for the repository's branch-workflow process.
- **Decision:** (1) `check_policy_provenance.py`'s classification design is
  **not** changed again to attempt to close this gap — no purely local-
  history signal can do so with certainty, per §5.1. The gap is accepted as a
  documented residual limitation of the mechanical check. (2)
  `docs/pipeline/branch-workflow.md` is amended (see the accompanying
  substantive commit) to add a binding process control: an agent MUST NOT use
  `git merge --ff-only` or `git update-ref` to advance a Task/Feature/Subtask
  branch, or `main`, onto the tip of any branch other than that item's own
  direct predecessor/successor chain or its own prior tip; absorbing content
  from any other branch — including a legitimate `DEC-0044-001` target-policy
  pull-in — MUST use an explicit merge commit (`git merge --no-ff` or
  equivalent) so `check_policy_provenance.py`'s merge-commit-based foreign/
  pull-in classification has topology to inspect. Advancing a branch
  (including `main`) via fast-forward to the tip of that item's own
  already-integrated predecessor/successor chain remains permitted and is not
  "absorption" in this sense — for example fast-forwarding `main` to a
  Feature branch's fully-integrated, already-merge-commit-verified tip is the
  item's own successor state, not foreign content. (3)
  `check_policy_provenance.py`'s module docstring gains a new "fast-forward
  absorption" entry in its "Residual known limitations" section, referencing
  this record; this is direct implementation follow-up work, not a further
  gated architecture decision, and is left to a resumed Implementer session
  (see the Task `0044-01` note accompanying this record for the exact scope).
- **Technical justification:** See §5.1–§5.3 above. Fast-forward absorption
  is topologically unrecoverable from local history alone; a reflog heuristic
  is non-authoritative and would misrepresent coverage. A process control
  that prohibits the git operation which creates the blind spot in the first
  place, for the one case that matters (absorbing genuinely foreign branch
  content), closes the gap completely and requires no further code changes to
  a classifier already independently re-reviewed three times. The
  predecessor/successor-chain and own-prior-tip exceptions preserve this
  session's own already-legitimate, hand-verified `main`-advancement pattern
  (Feature `0038`, `0037-37`, `0037-49`, `0041-01`, `0043-01`) without
  weakening `DEC-0044-002`.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `material-risk-decision`
- **Considered alternatives:**
  - **ALT-01:** Accept the residual limitation, add the non-fast-forward
    absorption process control to `branch-workflow.md` (Tom's option (a)).
    - **Disposition:** `selected`
    - **Reason:** Closes the gap completely and durably for future policy
      commits, is directly observable/enforceable in the commit graph itself,
      requires no further classifier changes, and does not weaken
      `DEC-0044-002`.
  - **ALT-02:** Add a best-effort reflog-based heuristic to flag likely
    fast-forward absorption for human review (Tom's option (b)).
    - **Disposition:** `rejected`
    - **Reason:** Reflogs are local, prunable, and not shared across clones/
      worktrees/CI, so the heuristic would be unreliable exactly where the
      check is most needed (a fresh isolated integration-review worktree, per
      this Task's own repeated review pattern); a partial, non-authoritative
      signal risks being mistaken for real coverage, which is a worse
      property than an honestly documented gap.
  - **ALT-03:** Attempt a fourth classifier redesign to close the gap purely
    mechanically.
    - **Disposition:** `rejected`
    - **Reason:** Per §5.1, no purely local-history signal can distinguish
      the two cases after a fast-forward has occurred; this is not an
      implementation defect but a property of Git itself, so further code
      changes to the classifier cannot succeed where the first three rounds'
      genuine defects could.
  - **ALT-04:** Escalate to the user (`[u]`) as Tom's verdict flagged.
    - **Disposition:** `rejected`
    - **Reason:** Per §5.2, neither remaining option chooses between
      materially different product architectures beyond what `DEC-0044-001..
      003` already decided, nor accepts security/release risk beyond what
      `DEC-0044-002` already accepts; this is an enforcement-mechanism choice
      for an already-accepted policy, within Architect authority.
- **Consequences:**
  - **CON-01:** Future integrators/agents absorbing content from a non-
    predecessor branch onto a Task/Feature branch must use an explicit merge
    commit; ad hoc `--ff-only`/`update-ref` absorption of foreign content is
    now a process violation, independent of and in addition to whatever
    `check_policy_provenance.py` reports.
  - **CON-02:** This session's own `main`-advancement pattern (fast-forward
    to an already-integrated successor tip) remains permitted and requires no
    rework.
  - **CON-03:** `check_policy_provenance.py`'s documented limitations grow by
    one entry; no code behavior changes as a direct result of this record.
  - **CON-04:** The broader repository-wide branching/merging strategy
    question remains open and is not resolved by this record (see the scope
    note in §5.3); a future broader revision could supersede or narrow this
    process control.
- **Affected work units:**
  - `feature:0044`
  - `task:0044-01`
  - `repository:autodocs`
- **Affected gates:**
  - `integration:0044`
  - `integration:main` (every future fast-forward-based integration in this
    repository)
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:seven-tom:integrator:0044-01-review:20260821T020000Z`
    - **Role:** `Integrator`
    - **Participation:** `reviewed`
    - **Position:** `no-position`
    - **Note:** Tom's third `[u]` verdict identified the defect, proved it
      with an independent minimal reproduction, named both disposition
      options considered here, and explicitly deferred the choice between
      them as a `TK-2` decision without recommending one; this record adopts
      option (a) of his own naming.
- **Waiver:** `none`
