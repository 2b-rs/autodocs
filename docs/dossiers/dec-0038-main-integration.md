# Decision record: partial integration of Feature 0038 into `main`

**Format** per `decision-record@v1` (`docs/pipeline/decision-record.md`), append-only.
Own ID series `DEC-0038-0xx`.

---

## `DEC-0038-001` — Integrate Feature 0038 into `main` without closing it

- **Recorded at:** 2026-08-21T00:00:00Z
- **Deciding identity:** `agent:seven:0038-main-integration:20260821`
- **Role:** Integrator
- **Authority reference:** verbatim management order, reproduced under *Provenance* below
- **Review participation:** Architect `Seven-B'Ellana` — **supports** (Round 2, no dissent remaining on any point). QA-Manager `Seven-Kathryn` — **supports**, with one recorded dissent (see *Dissent*).

### Subject

Management ordered Feature branch `0038` merged into `main`. Feature 0038 is
**not terminal**: `0038-16`, `0038-16.01` and `0038-16.02` remain open and are
blocked downstream of Feature 0037's queue cutover. `AGENTS.md` describes
Feature→`main` and the `DONE.md` move as one coupled closure act, so the method
was not self-evident from the order.

### Decision

Integrate, do **not** close. Specifically:

1. **Direction.** Merge `main` **into** `0038` (`--no-ff`, real merge commit with
   two parents), resolve all five conflicts there, then advance `main` by
   **fast-forward only**. Mandated by `DEC-0044-001..003`: the target branch's
   policy governs, and pulling the target's changes into the branch being
   integrated is "the one policy flow that keeps provenance checkable". This
   keeps `main` out of a conflicted state and makes the resolution an ordinary
   reviewable diff rather than a merge-commit interior.
2. **No `DONE.md` move. No `Acceptance: ✓` created, removed or altered.**
   `0038-26`'s existing acceptance is immutable and was verified byte-identical.
3. **`DEC-LEG-001` is NOT claimed.** Feature 0038 falls outside its stated scope
   (see *Technical justification*).
4. **No rebase, no squash, no force-push.**
5. Feature 0038 remains open in `TODO.md` with an integration note recording
   every residual and its owner.

### Technical justification

**Why `DEC-LEG-001` does not apply.** Its scope is a two-part AND: decomposition
predates `98fa57ce1` **and** the Feature carries no node marked
`Integration review: mandatory`. Feature 0038 fails part 2 — `0038-26` is a real
checkpoint. The Architect additionally found the document internally
contradictory at this point (its Feature-level biconditional versus its
node-level carve-out) and took the biconditional as controlling, on the ground
that an agent may not construe a management waiver more widely than its own
scope sentence in the agent's own favour. The QA-Manager found part 1 also
compromised: Feature 0038's decomposition was still being amended on 2026-08-20
(`1fb185a36`), three days *after* the rule existed, so it is a hybrid rather
than a Feature that "could not comply". Both independently concluded: not
claimable. The ambiguity is referred to management as a drafting defect to be
fixed at source, not interpreted by agents on demand.

**Why closure is off the table anyway.** Feature 0038 is not terminal, so it
could not close regardless of the waiver question. `DEC-LEG-001` is therefore
not on the critical path.

**Why merged-but-open is honest rather than novel.** `git merge-base
--is-ancestor 0037 main` is true: Feature 0037's branch is already fully merged
into `main` while Feature 0037 remains wide open — and it is the very merge base
`0038` was branched from. Feature 0033 is the same. Merged-but-open is this
repository's established, load-bearing state. The genuine gap is that
`branch-workflow.md` documents only the coupled closure act; that gap is
recorded as residual R-8.

### Considered alternatives

- **ALT-A — merge without closing.** `selected`. Executable today under existing
  authority, matches existing precedent, needs no new management decision, and
  makes `main`'s `TODO.md` strictly more truthful (it currently misreports 14
  completed Tasks as open).
- **ALT-B — move the blocked `0038-16` chain out of Feature 0038 to make it
  terminal and closeable.** `rejected`. Three independent grounds. (i) Feature
  0038's Definition of Done ends "queue activation has an executed
  handoff/retirement map with no duplicate authority" — delivered by exactly
  that chain and nothing else; removing it forces either a false closure or a
  DoD amendment, and `AGENTS.md` forbids weakening acceptance to make work pass.
  (ii) The ID scheme forces renumbering, which would rewrite the ownership
  provenance of **12** automation-safety dispositions keyed to
  `owner_task: 0038-16` in a bulk edit. (iii) This repository was burned by
  exactly this failure mode four days earlier — `1fb185a36`, "repair
  automation-safety dispositions orphaned by 0038-14's closure". The tell is the
  counterfactual: nobody would propose the move absent closure pressure. That
  makes it restructuring so a gate evaluates differently, which is the
  anti-pattern `DEC-LEG-001`'s own rejected `ALT-03` warns against, regardless
  of mechanism.
- **ALT-C — do not merge; wait for Feature 0037.** `rejected`. Feature 0038's
  closure is strictly downstream of Feature 0037's entire queue cutover —
  potentially the rest of the project. Meanwhile `main` and `0038` have diverged
  47/65 commits and five further Features hold unmerged branches that will hit
  the same conflicts. Delay compounds the risk it seeks to avoid.

### Dissent (recorded)

**QA-Manager `Seven-Kathryn`**, against folding the disposition repair into the
merge commit: a merge commit carrying changes present in neither parent is an
*evil merge* — `git log -p` shows nothing by default and a reviewer cannot
distinguish conflict resolution from a substantive edit smuggled alongside it.
She accepts one bisect-visible broken intermediate (`M`), documented by SHA, as
the cheaper trade. **This dissent was accommodated, not overruled:** the repair
is its own commit `R`, and because `main` advances only at the fast-forward to
`R`, trunk never observes the broken state at all.

She also records a QA finding **against herself**: her Round-1 §3.6 treated the
root checkout as holding one uncommitted state and "understated the danger by an
order of magnitude".

### Consequences

- **CON-01:** 28 terminal Tasks reach trunk; `main`'s `TODO.md` stops
  misreporting them as open.
- **CON-02:** Feature 0038 stays open and visible with every residual owned.
- **CON-03:** `git log --first-parent main` now walks the `0038` line for this
  span — first-parent ordering is inverted relative to trunk convention. Accepted
  knowingly; both parent SHAs are recorded here and in the merge subject.
- **CON-04:** Commit `M` (`c5c478a6c`) does not pass `_src/validate.py`; `git
  bisect` can land on it. `R` (`5c03c63a3`) restores the gate. `main` never
  points at `M` alone.
- **CON-05:** Feature 0038 still cannot close. A future closure requires a new
  recorded management decision (residual R-6).

### Affected work units

Feature 0038 (all Tasks), Feature 0040 (its closure state is preserved, not
altered), Feature 0041 (2 carried dispositions), Task `0038-28` (new).

### Affected gates

`feature-closure:0038` (not crossed), `task-start:0038-16.01`,
`validation:_src/validate.py`, `integration:main`.

### Triggers (per `decision-record.md`)

`cross-item-blast-radius`; `material-architecture-or-repository-behavior`;
`material-risk-decision`.

### Provenance

Verbatim management order that triggered this decision:

> The feature branch must be merged mach to main now. I want you to perform a
> joint review together with the persona of the Architect and the Persona of the
> Project manager. Spawn subagents as necessary, discuss pros and cons, in as
> many rounds as needed to reach consensus. Find the best and cleanest technical
> solution that also exhibits the least risk for future breakages. Document the
> discussion, inform me about the decision and execute it.

The order set the goal. The method recorded above is the agents' decision, not
management's; no option list was presented to management and none of these
choices is attributed to it.

### Addendum: independent-verification requirement waived by management

The QA-Manager persona's Round-2 requirement of a third privileged verifier
(distinct from both Seven and B'Ellana) could not be satisfied: the proposed
verifier `worf-martok-20260820t130000z` has no reachable agent-inbox, and the
user directed proceeding straight to Feature 0037 once 0038 was done. The
current user, as management, is the sole authority that may waive a process
safeguard the agents themselves created; this instruction is recorded as that
waiver.

This does not remove the underlying verification — all 15 checks in the
integration note were independently re-derived by the integrator from first
principles (blob hashes, reachability, programmatic byte-comparison of
disposition fields, reproduction of the one test failure at the merge-base)
rather than asserted. What is waived is specifically the second-attester
requirement, not the verification work itself.
