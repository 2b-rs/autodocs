# Architect pre-mutation scope review — `DEC-0044-028`

## Review identity and binding

- **Review kind:** independent pre-mutation cross-item gate-scope review
- **Verdict:** `scope-supported-with-conditions`
- **Reviewed at:** `2026-08-26T14:48:00Z`
- **Reviewer:** `agent:data:0044-028:responsibility-allocation-20260826T144109Z`
- **Role / capability:** Management-instantiated Architect; `privileged`
- **Assignment:** Project Lead `jean-luc`,
  `agent-inbox:1787755235010-2b87af70`, supplemented by the Acceptance boundary
  in `agent-inbox:1787755266031-c9f5098a`
- **Audit source:** `agent-inbox:1787755203069-7965daf0`
- **Exact baseline:** `main`
  `f423128b4e25def12b28b359d56ea9c5392ab550`
- **Exact reviewed candidate:**
  `docs/dossiers/dec-0044-028-responsibility-allocation.md`, SHA-256
  `087bea706118ad43fd3812a0023633550063fa439577499a2da455b0d8303bd5`
- **Independence:** Data prepared the Management decision record and reviews
  its declared reach, but is explicitly not the policy Implementer, Acceptance
  reviewer, or Integrator. The required pre-mutation separation is Architect
  versus Implementer; a distinct Implementer follows only after this decision
  and review are reachable from `main`.

This review tests reach, affected units and gates, authority boundaries, and
the smallest consistent mutation. It is not Task Acceptance, an integration
review, an integration verdict, a claim on any affected Task, or permission to
advance `main`.

## Sources inspected

- `AGENTS.md`: claim ownership, deterministic selection, dispatcher briefing,
  cross-item pre-mutation review, Acceptance assignment, Integrator and
  Project-Lead boundaries.
- `SANDBOX.md`: capability-class and execution-authority boundary.
- `TODO.md:425`, `TODO.md:445-465`: Feature `0039` reservation and start gates,
  Seven's selection, Harry's ownership, and downstream pilot reservation.
- `docs/pipeline/process-roles.md:35-129`, `162-239`: capability versus role,
  Management wording, authority mapping, TK-1/TK-2, and pre-mutation review.
- `docs/pipeline/feature-breakdown.md:9-104`: Architect ownership of the work
  graph and capability-profile derivation.
- `docs/pipeline/capability-matching.md:14-34`, `45-108`: eligibility,
  orchestrator selection, non-authority notice, and privileged-act constraints.
- `docs/pipeline/task-acceptance.md`: exact Acceptance assignment and authority
  boundary, including the section reviewed by Kathryn and relayed in the
  supplemental assignment.
- `docs/dossiers/README.md:5`, `docs/studies/README.md:5`, and
  `docs/dossiers/process-improvement-studies-provenance.txt:43`: current mirrors
  and immutable source provenance for Feature `0039` reservation history.
- `docs/pipeline/decision-record.md`: canonical trigger, work-unit/gate grammar,
  field order, review participation, and append-only requirements.

## Findings

### F-01 — The correction qualifies for pre-mutation review

The declared rules can block the start of `0039-01`, `0039-02`, `0039-03`, and
`0039-05`, and can affect Feature `0039` integration and closure. They also
define repository-wide responsibility allocation. This is actual declared
cross-unit behavior, not merely a shared-path change, so
`cross-item-blast-radius` applies.

The candidate correctly names the repository, Feature `0039`, the four Tasks,
Feature `0044`, and all intended governance projections. Its gate identifiers
use only canonical concrete forms: four `task-start` gates,
`integration:0039`, and `feature-closure:0039`. It invents no generic
assignment or validation gate slug.

### F-02 — Responsibility, eligibility, ownership, and authority remain separate

The candidate's selected alternative is supported. A capability profile says
who is eligible; a Project-Lead instruction or agreement allocates ordinary
responsibility; an immutable owner token proves a live claim; and a separately
authorized act establishes Acceptance, integration, release, waiver, or other
privileged authority. None substitutes for another.

The decision explicitly preserves the binding boundary requested in the
supplemental assignment: a Project Lead may allocate ordinary work but does not
thereby become a `registered acceptance authority`. Acceptance still requires
exact assignment by the current user or an expressly registered Acceptance
authority. Integration, Feature closure, release, specialist approval, and
external authority remain separately assigned.

### F-03 — Existing concrete user selections are preserved

The candidate does not silently cancel Seven's recorded `0039-01` selection.
It permits only an explicit authoritative handoff or superseding decision to
replace a stronger specific instruction. This is the correct interaction
between the general allocation rule and append-only user provenance.

The stale `TODO.md:450` assertion that a user selection is still the sole next
action may be corrected additively because `TODO.md:449` already records that
selection as fulfilled. The correction must not erase the source instruction
or represent Seven's assignment as absent.

### F-04 — The privilege gate must be narrowed, not discarded

Harry's `0039-02` process-owner designation already settles ordinary
responsibility. The exact implementation capability must be re-derived from
the work contract. Content definition may remain with a sufficiently capable
nonprivileged owner, while approval, registry/tool promotion, Acceptance,
integration, and closure stay with separately assigned privileged identities.

Likewise, `0039-03` retains its real prerequisite on approved `0039-02` output
and all tool-promotion safety boundaries. `0039-05` retains its schema,
acceptance-promotion, and cutover authority gates. The implementation may
remove only the current-user/privileged-**owner** requirement from ordinary
responsibility; it may not convert privileged acts into ordinary work.

### F-05 — No further Management choice is required for ordinary allocation

Within this selected design, no Management decision is needed merely to name a
concrete Project Lead or sufficiently capable ordinary owner for work not
already controlled by a stronger specific instruction. Management or another
registered authority remains required where existing governance already
requires it: waivers, `[u]` resolution, process changes outside this exact
decision, materially different architecture, risk/security/release acceptance,
external credentials/configuration, specialist approval, and any explicit
supersession of Seven's selection.

## Smallest supported implementation scope

The first policy mutation is supported only when performed atomically by an
Implementer distinct from Data and limited to the projections below:

1. `docs/pipeline/process-roles.md` — canonical responsibility-allocation versus
   authority distinction; revise the over-broad statement that Management
   assigns all roles without weakening Management-only decisions.
2. `AGENTS.md` — align ordinary selection/dispatch language and preserve exact
   claim, Acceptance, Integrator, independence, and authority requirements.
3. `docs/pipeline/capability-matching.md` — keep the matcher as eligibility
   evidence and allow the responsible Project Lead/dispatcher to choose among
   eligible recipients without treating the result as authority.
4. `TODO.md` — additively reconcile Feature `0039` reservation projections at
   lines corresponding to the baseline's `425`, `445-465`; preserve real
   prerequisites and privileged-act gates, Seven's selection, and Harry's
   ownership.
5. `docs/dossiers/README.md` and `docs/studies/README.md` — align current
   projections while retaining
   `docs/dossiers/process-improvement-studies-provenance.txt` unchanged as the
   historical source.

No validator is required merely to make the prose correction conforming. If an
Implementer proposes a new or widened repository gate, validator, schema, or
additional path, that is outside this reviewed candidate and requires renewed
scope analysis before mutation. `SANDBOX.md`, `PRIVILEGED.md`,
`docs/pipeline/task-acceptance.md`, and
`docs/pipeline/feature-breakdown.md` need no change under the smallest supported
correction unless the Implementer demonstrates a concrete contradiction; any
such expansion must return to Architect review.

## Binding implementation and review conditions

1. `DEC-0044-028` and this exact supporting review must first be reachable from
   `main`; neither branch-only artifact authorizes policy mutation.
2. The Implementer is distinct from Data and uses an item-owned worktree with a
   declared path-exact claim. Data performs no implementation.
3. The correction is atomic across every projection that changes. A partial
   state that enables Project-Lead allocation but leaves ordinary ownership
   privilege-gated, or removes privilege language from actual privileged acts,
   is not supported.
4. Existing active claims and exact named assignments are not appropriated.
   Reassignment requires a recorded handoff or stronger superseding authority.
5. Focused validation must prove the responsibility/authority distinction,
   Seven/Harry preservation, no stale unsatisfied reservation text, valid links,
   and exact changed-path scope. Any new machine gate requires a new or amended
   `decision-record@v1` and supporting Architect review before its first
   mutation.
6. Acceptance, checkpoint review, integration, Feature closure, release, and
   `main` movement remain separately assigned privileged work. The Project Lead
   coordinates but does not inherit those authorities from this decision.
7. A later independent privileged reviewer or Integrator evaluates the exact
   implementation candidate. This scope verdict creates no `Acceptance: ✓`.

## Verdict

`scope-supported-with-conditions` for the exact decision candidate SHA-256
`087bea706118ad43fd3812a0023633550063fa439577499a2da455b0d8303bd5` and the
smallest six-path policy correction listed above. The verdict fails closed on a
changed decision digest, additional path, new gate, silent supersession of a
named user selection, conflation of Project-Lead allocation with registered
Acceptance authority, or any weakening of separately assigned privileged acts.

## Addendum R1 — identity correction and exact rebind

- **Recorded at:** `2026-08-26T14:52:00Z`
- **Trigger:** Independent STOP finding
  `agent-inbox:1787755616970-fa5798ce` and correction assignment
  `agent-inbox:1787755651657-f758eefb`
- **Correction reviewed:** `DEC-0044-028-C001`
- **Historical candidate retained:** The original review binding to SHA-256
  `087bea706118ad43fd3812a0023633550063fa439577499a2da455b0d8303bd5`
  remains visible and is not rewritten.
- **Corrected decision-file SHA-256:**
  `77d34a7e77d361e26c56dc3d7194095280de200dbacd912c606b2a2890100659`
- **Corrected effective `Deciding identity` block SHA-256:**
  `37ed6095f0556b7462c0c5b9e3d6d4b0a89af7413725b9ae55642c8f6637fc1f`
- **Effective identity:** `authority:repository-owner`
- **Correction-event role:** `Architekt`
- **Rebound verdict:** `scope-supported-with-conditions`

`DEC-0044-028-C001` changes exactly one top-level field from descriptive
Management prose to the repository owner's registered stable identity. Its
`Previous effective block SHA-256`
`7990d83b2cc9772c177cfe26d0aadaa2ec8433a5555a838b37705f30c919cce9`
reproduces the original scalar field bytes, including their terminating LF.
The replacement-block digest above reproduces the effective corrected scalar
field under the correction-event transport rules.

The correction changes no decision content, alternative, consequence,
affected unit, gate, review condition, reservation, Project-Lead boundary, or
Acceptance/integration/release authority. All findings, the smallest supported
implementation scope, and conditions 1–7 remain effective unchanged. This
addendum binds them to corrected decision-file SHA-256
`77d34a7e77d361e26c56dc3d7194095280de200dbacd912c606b2a2890100659`.
Any further change to the effective decision or correction sequence requires a
new append-only rebind before policy mutation.

## Clean unpublished-candidate reconstruction provenance

This file and the bound DEC were rebuilt from exact `main`
`f423128b4e25def12b28b359d56ea9c5392ab550` because the prior candidates never
reached `main` and therefore were not published records under
`docs/pipeline/decision-record.md` section 5. The discarded candidate sequence
remains reachable as audit evidence:

- `8712ebf9d39771ca6761fe5cac6b6ba649840ca1` — original candidate; independent
  identity STOP `agent-inbox:1787755616970-fa5798ce`.
- `8c13456c58e09d54e57c29786c1eff6354e7aebc` — candidate with invalid C001
  correction-event role; verified STOP and C002 instruction
  `agent-inbox:1787755997495-5ff56a8c`.
- `bfa3149ede790e4df1353204a3431930e0b79deb` — candidate with a no-op C002 that
  could not target C001 metadata; verified STOP 3 and clean-rebuild instruction
  `agent-inbox:1787756242460-fedfa1a9`.
- `7b52b3db5c5bab8706b4b89333c1c47e5c4ec7f1` — clean direct-base candidate
  stopped before renewed review because PART-01 still rendered `Role: Architect`;
  independent pre-review finding and rebuild instruction
  `agent-inbox:1787757237536-52386e2a`.

The clean candidate contains one correction event only. PART-01 and C001 both
use exact `Role: Architekt`; C001 otherwise preserves the identity correction
reviewed in R1. No invalid C001 or no-op C002 is part of the final product. The historical
commits are cited but are not ancestors of this fresh candidate.
