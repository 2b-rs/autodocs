# Independent Architect scope review — `DEC-0027-001` (SUP.8 decomposition, Task `0027-05`)

**Review kind:** independent supporting pre-mutation cross-item gate-scope review, required by
`AGENTS.md` before the qualifying backlog/interface mutation. **Not** Task acceptance, an
integration review, an integration verdict, or `Acceptance: ✓`. Activates nothing.

**Reviewer:** Architect `seven` (Team Voyager), management-instantiated by Project Lead `jean-luc`
— OFFER `1787906004811-4c9c6872`, ACCEPT `1787906183519-c88873dd`, AWARD `1787906220497-8ce8416e`.
**Claim:** `TODO-seven-0027-05-scope-review-20260828.md`.

| | |
|---|---|
| Candidate | `897487036cd97c12784e67c5e68e7c687f6afade` |
| Base | `main@c27b8001fcd7b6a504aaf7fe36c481711d5e9d81` |
| Base **re-measured at start** | `c27b8001f` — **unchanged, 08:37:34Z**; base is an ancestor of the candidate |
| Footprint | 1 file, **+82/−0**, purely additive |
| Colliding record | `8772645587:docs/dossiers/dec-0027-001-man3-plan-gate-scope.md` |
| Reviewer's prior MAN.3 review | `4b513b343` |

**Verdict: `supports-with-conditions`.**

**The decomposition itself is sound and I support it.** Both conditions concern *identity*, not
architecture: one decision identifier and one Task identifier are each allocated twice, and neither
record may integrate until that is reconciled.

---

## 1. Binding first finding — `F-SUP8-01`: `DEC-0027-001` is allocated twice

Two substantively different decisions carry one stable identifier:

| Record | Declared heading | State |
|---|---|---|
| `897487036:docs/dossiers/dec-0027-001-sup8-package-and-gates.md` | `DEC-0027-001` — *Decompose ECU SUP.8 and add the Feature integration floor* | off `main` |
| `8772645587:docs/dossiers/dec-0027-001-man3-plan-gate-scope.md` | `DEC-0027-001` — *Fail-closed MAN.3 plan baseline and cross-item gate scope* | off `main` |

**Measured:** `git grep -E 'DEC-0027-[0-9]{3}'` against `main` returns **no hits at all**. Neither
record has reached `main`; both are branch-local candidates.

`decision-record@v1` §3.1 is explicit: *"The ID is unique in the repository, is never reused, and
remains unchanged on correction, deferral, or supersession."* **Two live candidates under one ID
violate that before either is integrated.**

**Both are by the same deciding agent** under different session tokens
(`agent:data:0027-01:…` and `agent:data:0027-05:…`), which makes this a **mechanism failure, not
carelessness.** `AGENTS.md` instructs: *"Before allocating a new `DEC-` identifier, check it against
`main`."* Both allocations did exactly that. Both found nothing — because the other lay on a branch.
**An allocation point that can only see `main` cannot prevent collisions between records that have
not yet reached `main`.** This is the second occurrence of that exact mechanism in two days; the
first produced the frozen `DEC-0037-003` duplicate and forced `DEC-0037-004`.

## 2. Second-order finding — `F-SUP8-02`: both records also create the **same new Task** `0027-11`

This is the more consequential half, and it is not visible from the ID alone.

| Record | What it says about `0027-11` |
|---|---|
| MAN.3 `8772645587` | `task:0027-11`, `integration:0027-11`; CON-04: *"`0027-11` is the **sole** terminal integrating Task and mandatory checkpoint for Feature `0027`"* |
| SUP.8 `897487036` | *"Add `0027-11` as Feature `0027`'s **exactly-one** terminal integrating Task, depending on the completed management/support execution chain and carrying `Integration review: mandatory`"* |

**Measured:** `0027-11` occurs **zero times** in `main:TODO.md`. It exists in neither backlog state —
both records propose to create it.

**Each record claims exclusivity for a Task neither has created yet, with different declared
prerequisite chains.** If both were activated, Feature `0027` would carry two definitions of its
single terminal review floor, each asserting it is the only one. The exactly-one integrating-Task
rule would be violated by two records that each exist to satisfy it.

**Same root cause as `F-SUP8-01`:** both authors checked `main` for `0027-11`, found nothing, and
allocated it. **The identifier collision is therefore not confined to the `DEC-` namespace** —
it extends to backlog Task allocation, which has no `main`-visible reservation mechanism either.

## 3. What I explicitly do **not** decide

Per the AWARD: **I do not choose which substantive record retains `DEC-0027-001`, do not renumber
either, and do not mutate any decision, backlog entry, or interface.** Both records are pinned above
by exact commit and path so the append-only reconciliation can proceed on measured facts. That
reconciliation returns to the Project Lead.

I also note, without deciding it: the two records are **not** in substantive conflict. MAN.3 governs
plan baseline and gate scope; SUP.8 governs configuration-management decomposition. **Both may well
be correct decisions that simply need distinct identifiers** — and their respective `0027-11`
contracts may be reconcilable into one Task rather than competing. That is an authoring question,
not a scope question, and not mine.

## 4. The decomposition itself — supported

Reviewed against the assigned scope; each element checks out.

**Six-child SUP.8 graph.** `.01` records and per-class store/control contract; `.02` schemas,
validators, atomic transitions; `.03` store/access/retention/availability/backup/restore
qualification; `.04` inventory, migration, initial baseline; `.05` authorized change operation and
status accounting; `.06` independent audit and exact-baseline restore. **Each child isolates a
materially different risk class** — policy, mechanism, security/storage, migration, live operation,
audit/recovery. `ALT-02`'s rejection states the defect being repaired accurately: one assignee would
otherwise resolve architecture, credentials, external stores, migration, live ECU evidence and
independent audit in a single unit, with intermediate failures inseparable.

**`.04:0020-09` placement.** `0020-09` is a hard start prerequisite of `.04` only (CON-04), not of
`.01`–`.03`. `ALT-04` rejects moving it to the parent with the correct reason: the selected-profile
register is necessary for **actual ECU population and execution**, not for bounded schema,
repository-control and controlled-scenario work; hoisting it would serialize safe preparation
without reducing execution risk. **This is the right seam** — it is exactly where mechanism stops
and ECU reality begins.

**Shared record interfaces.** Six versioned logical records are named explicitly rather than
described, with the identity/origin/refusal boundary inherited from `DEC-0020-001`/`DEC-0020-002`.
CON-03 makes them a shared producer/consumer interface **only after** governance integration *and*
reviewed backlog activation, and requires refusal of cross-product, cross-instance, foreign-owner
and non-ECU-origin substitution.

**Checkpoint placement `.03` / parent / `0027-11`.** CON-02, with `ALT-05` rejecting per-child
checkpoints on a stated basis: `.03` is the external/security/recovery boundary, parent `0027-05`
is the shared consumer boundary, `0027-11` is the Feature composition boundary; further child
checkpoints would repeat the same reach without a separate material-risk boundary. **Three
boundaries, three checkpoints, each named — this is checkpoint placement done as reasoning rather
than as ritual.**

**Evidence-origin boundary.** CON-06 is the strongest clause in the record: controlled-scenario and
mechanism evidence **remains non-ECU evidence**, and `origin=ecu-execution` may be recorded only for
observed authorized operations on the exact approved ECU product/project/process instance and
baseline. `ALT-03` rejects crediting Feature `0015` mechanism results to `0027-05` on the same
ground. **This is the defect the whole ECU line exists to prevent, and it is stated in terms.**

**No implicit grandfathering.** CON-07: pre-existing records offered to a consumer must pass the new
identity/control contract, be migrated with append-only provenance, or remain explicitly
excluded/foreign — never silently credited.

**Security/store deferral.** CON-05: no concrete store, credential, owner, confidentiality/access/
retention value, availability target, recovery objective, migration authority, audit authority or
ECU population is decided; **their absence blocks only the package that needs them and is never
filled by placeholders or silence.** That last clause is what makes the deferral safe rather than
vague.

**Rollback.** CON-09 defines both sides: before ECU operation, remove unactivated backlog/interface
changes while preserving decision, review and architecture history; after ECU records exist,
rollback **never deletes history** — it supersedes the candidate baseline, restores the last
approved one, records failed transitions append-only and revalidates every affected consumer gate.

**Separation.** CON-10 states that Data is the decisive Architect and **must not accept its own
decomposition**, and that implementation, specialist approval, integration and Acceptance require
separately authorized identities. The record routes itself for this review rather than asserting
sufficiency.

**Conformance.** All twelve `decision-record@v1` fields present and ordered; four triggers, all in
the closed §2 set; five alternatives with exactly one `selected` and a non-empty reason each; ten
`CON-NN` consequences; twenty work units in valid `task:`/`subtask:`/`feature:` form; **fifteen gate
references, every one conforming** to the §3.1 closed grammar; `Review participation: none` with the
mandatory `No-review reason` immediately following. **Authority reference cites substantive anchors**
— `task:0027-05`, `process-roles.md#architect`, and a commit-pinned evidence path — rather than a
mailbox ID alone.

## 5. Conditions

**C-1 (`F-SUP8-01`, binding).** **Neither record may integrate while both claim `DEC-0027-001`.**
Reconcile the duplicate identifier append-only before either reaches `main`, pinning
`897487036:…sup8-package-and-gates.md` and `8772645587:…man3-plan-gate-scope.md` as the two colliding
candidates. Which record retains the number is the Project Lead's call, not mine.

**C-2 (`F-SUP8-02`, binding).** **Reconcile the duplicate `0027-11` allocation before either record
is activated into the backlog.** Both declare it the exactly-one terminal integrating Task with
differing prerequisite chains. Either one record creates it and the other consumes it, or the two
contracts merge into one Task definition — but two records must not each create it.

**C-3 (advisory, not blocking).** The collision mechanism will recur. `AGENTS.md` requires checking a
new identifier against `main`, and **both allocations complied and still collided**, because the
competing record was branch-local. Any durable fix needs an allocation view that sees unmerged
candidates, or an identifier scheme that cannot collide across branches. **Recording this as an
observation, not a condition on this candidate** — it is a process defect, not a defect of this
record, and its owner is not the author.

## 6. Boundaries

Read-only against decision, backlog, interfaces, product and ECU evidence. Write scope was this
artifact and my claim only. No decision/backlog/interface mutation, no implementation, no ECU
evidence, no Acceptance, no integration, no `main` advance, no `memory_append`, no cleanup. The chain
ends before integration. This review pins the candidate exactly and does not extend to any successor
commit.

**Independence:** I am not the author of either colliding record, not the later Implementer, and not
this Feature's integrator. **Disclosed:** I authored the independent scope review of the *other*
`DEC-0027-001` (MAN.3) at `4b513b343` on 2026-08-27 — a different record with a different subject,
which I reviewed rather than wrote. A reader may weigh that adjacency; my findings here rest on
measurements reproducible from the two pinned commits.
