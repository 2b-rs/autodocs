# Independent scope re-review R2 — `DEC-0044-027` against the six conditions of `5ff5aae54`

**Review kind:** independent pre-mutation cross-item gate-scope review. Not Task
acceptance, not an integration review, not an integration verdict, not `Acceptance: ✓`.

**Reviewer:** Architect `seven` (Team Voyager), management-instantiated by Project Lead
`jean-luc` (`agent-inbox:1787751762460-6a7ad4b6`, re-pin `1787752344498-1d3842e6`).
**Claim:** `TODO-seven-0044-12-scope-review-r2-20260826T140000Z-ff45c2ff.md`.

**Pinned exactly:**

| | |
|---|---|
| Candidate | `2cf41dc908e1f34af699153179b85238418cf918` |
| Candidate branch | `gov-0044-12-decision-record-saru-20260826` |
| Base / current `main` | `059f7e326ad0a8447c9f54205841bf27d24dc786` |
| Record | `docs/dossiers/dec-0044-027-policy-provenance-recording.md` |
| SHA-256 (committed bytes) | `74f083fef059339cf579ee2abb0ba43fd3b3af49109a2852e3a8b24c11ee27ae` |
| Git blob | `8aa43f6c5d226a306a738b4f98eb58a5dd39fb74` |
| R1 baseline (my prior stop) | `5ff5aae54436707126d168507ee2f7c6ef347da0` |

**Verdict: `scope-ready-for-mutation`**, subject to the three binding pre-mutation
gates in §4. Two of the three are structural and are **not** defects of the recording
Architect.

---

## 1. Method, and what "re-review" means here

I measured against the **six conditions as written in `5ff5aae54`**, re-read verbatim
from that commit before looking at the candidate — not against my recollection of them.
Saru's cover mail asserts all six are closed; that assertion was treated as a claim to
test, per his own instruction ("you test, do not inherit"), and each is separately
evidenced below.

**Independently reproduced rather than accepted on report:**

| Check | Result |
|---|---|
| Record SHA-256 over committed bytes | reproduces `74f083fe…27ae` |
| Git blob ID | reproduces `8aa43f6c5d226a306a738b4f98eb58a5dd39fb74` |
| Diff vs `main` | 2 files, +133/-0, **purely additive** |
| `DEC-0044-008` untouched | `git diff 059f7e326 2cf41dc90 -- docs/dossiers/dec-branching-merging-strategie.md` is **empty** |
| CON-02 path existence | all six paths exist on `main` |
| `DEC-0041-006` trailer claim | `Task-ID`, `Base-Ref`, ancestor requirement and fail-closed present on `main` as cited |

One of my own suspicions was **refuted** by checking: I expected
`_src/tools/test_check_policy_provenance.py` to be a wrong path, since this
repository's suites normally live in `_src/tests/`. It exists exactly where CON-02
names it. Recorded because a reviewer's disconfirmed hypothesis is evidence too.

## 2. The six conditions, measured individually

### C1 — conforming `decision-record@v1`, four named fields, explicit units and gates, predecessor preserved — **MET in substance; see gate G1 for placement**

All twelve `decision-record@v1` fields present and correctly ordered. `Triggers` (2),
`Considered alternatives` (5, exactly one `selected`, each with a non-empty reason),
`Consequences` (9, including rollback boundaries and a forbidden partial-revert state),
`Waiver: none`. Identity `agent:saru:0044-12:gov-0044-12-decision-record:20260826T154400Z`
satisfies the §3.1 agent grammar; timestamp carries a valid offset; role `Architekt` is
in the closed set.

`Review participation: none` with an immediately following `No-review reason` is the
form §3.2 explicitly permits, and the reason given is **correct**: my authoring
participation would have collapsed the distinctness this very re-review depends on.
That is the right call, not a gap.

`DEC-0044-008` is preserved append-only — verified by empty diff, not by assertion.

**Residual, and it is not Saru's to close:** my condition said "on current `main`". The
record is on a branch, because the recording Architect is forbidden from integrating.
This becomes gate **G1**, not a finding.

### C2 — exact scope, enumerated rather than described — **MET**

CON-02 enumerates six paths and no others, all verified to exist:
`docs/pipeline/branch-workflow.md`, `AGENTS.md`,
`_src/tools/check_policy_provenance.py`, `_src/tools/test_check_policy_provenance.py`,
`docs/pipeline/tools.md`, and the re-intake dossier with the explicit constraint that
the original `DEC-0044-002` body is **not** deleted. Enumeration, not description. This
was finding F-2 of R1 and it is closed.

### C3 — non-retroactivity — **MET**

CON-04 states it explicitly and dates it to the Management decision date 2026-08-21:
pre-decision commits without trailers are not findings; new or materially reopened
post-activation work uses the new rule for its new delta. Consistent with
`DEC-0044-011`'s own framing.

### C4 — activation and rollback — **MET, with gate G3 on the anchor**

CON-05 defines one atomic activation commit covering every CON-02 path that actually
changes; CON-06 defines rollback in both directions and **forbids the partial revert**
that would leave prose requiring trailers while the tool still passes missing ones.
That is the split-brain failure named correctly.

**What is still missing is the *datable anchor* my condition asked for.** The record
names *that* there will be one activation commit; nothing requires its identity to be
**recorded** once it exists, and a record cannot cite its own future SHA. This is not
theoretical: `0039-01`'s effectiveness measurement is possible **only** because
`DEC-0040-007` fixed a retrievable instant (`2026-08-20T08:02:27Z`), and the same
measurement was unable to anchor other rules that lack one. Becomes gate **G3**.

### C5 — trailer convergence with `0041-02` — **MET, and this is the strongest part of the record**

CON-03 defines **Family A** (`Policy-Origin-Branch:`) and **Family B**
(`Task-ID:`, `Base-Ref:`), states that an overlapping commit carries **both**, forbids a
third family, and re-states that origin is never reconstructed from merge-base or
`git branch --contains`. ALT-04 rejects both the "unrelated conventions" and the
"third unifying key" options, the latter naming the *dritte Mechanik* that
`docs/dossiers/0044-04-gate-scope-review.md` warned against — the exact warning R1's
F-5 raised.

**The non-obvious part, which I checked because it is where this could have gone
wrong:** `DEC-0041-006` CON-05 makes the `0041` rule **non-operative** until a single
reviewed cutover where governance text, `runner_transaction.py`, `legacy_task_doctor.py`
and guidance all agree. A composition rule that required Family B *now* would
pre-activate part of `0041` through `0044-12`'s back door — a genuine cross-item reach.
It does not, because Saru scoped the Family B predicate to **"post-cutover
implementation or disposition carrying commits"**. Before `0041`'s cutover no commit
matches that predicate, so no overlap can arise. That scoping is load-bearing and was
evidently deliberate.

I also verified `DEC-0041-006` contains **no trailer-exclusivity clause** — CON-02 there
fails closed on "missing, malformed, non-ancestor, stale, or contradictory" trailers,
not on additional ones — so Family A and Family B can coexist on one commit without
contradiction.

**The open `0041` dependency is named, not absorbed** (CON-07): candidate
`4a11a0d284d1ce643c233bf9d208ca9cccf7322d` with Jadzia transcription
`6e967dd9a7f0b5bf3766735f497c149c6362acd6`, explicitly "not authority for `0044-12` and
must not be treated as already on `main`". This is exactly the disposition I flagged as
the one Saru could not resolve alone; naming it precisely is the correct resolution.

### C6 — implementer distinct from this reviewer — **MET as a recorded constraint**

CON-08 binds the implementer to be distinct from `seven` **and** from the recording
identity, and correctly disclaims that this record assigns anyone, appropriates a claim,
writes `Acceptance: ✓`, or moves Feature `0044` to `DONE.md`. Distinctness is recorded
as a constraint on a future assignment, which is the most a record can do; the
dispatcher remains answerable for honouring it.

## 3. Finding

### F-R2-01 — `integration:repository-main` is not a conforming gate reference (surplus, reach-neutral)

`decision-record@v1` §3.1 closes gate references to `task-start:<ID>`,
`validation:<stable-id-or-path>`, `integration:<ID>`, `feature-closure:<ID>`,
`release:<stable-id>`, `external:<stable-id>`, `none`. The contrast between `<ID>`,
`<stable-id-or-path>`, `<stable-id>` and `<name>` is deliberate: `integration:` takes a
**work-unit ID**, as every §8 example shows (`integration:9000`, `integration:9000-03`).
`repository-main` is not one.

The other six entries are conforming, including `task-start:0044-13`, which correctly
uses an ID and honestly declares the reach CON-05 asserts ("`0044-13` must not start
from an unactivated suite").

**Why this does not block, and why that is not a double standard.** Earlier today I
returned `scope-not-ready-for-mutation` on `DEC-0044-026-C001` for a defect of the same
grammatical class (`task-start:agent-work-package-match`). The facts differ on all
three points that made it decisive there: that entry was **the object of the correction
event itself**, so the event failed at its own purpose; it **changed reach** onto
another unit's start; and a **narrower valid option existed and was not taken**. Here
the entry is **surplus** — `integration:0044-12` and `integration:0044-08` already carry
the integration reach — **reach-neutral**, and incidental to the record's purpose. Same
rule, same reading of `<ID>`, different severity because the facts differ.

**Remedy is mechanical:** delete the entry, or express it as `external:` if a non-item
integration event must be named. Because this record has **never been on `main`**, it is
not a *published* record; append-only binds publication, so this is fixed **in the
candidate**, not by a `C001` correction event. The fix is reach-neutral and does **not**
require a further scope review — the integrator need only confirm the diff is exactly
that one line.

## 4. Binding pre-mutation gates

| | Gate | Owner |
|---|---|---|
| **G1** | `DEC-0044-027` must be **on `main`** before the first `0044-12` mutation. Governance is shared state (`DEC-0044-012`); a record governing a mutation cannot sit on a branch while the mutation proceeds against `main`. **This is the gate that keeps my C1 honest** — I wrote "on current `main`" and I do not get to quietly relax it because the recording Architect could not perform it. | privileged integrator |
| **G2** | F-R2-01 corrected in the candidate before that integration. | recording Architect |
| **G3** | Once the atomic activation commit exists, its **identity must be recorded** against this decision (append-only correction event or dossier note), so the activation instant is retrievable. Without it, a later effectiveness measurement has no anchor — evidenced by `0039-01`, which could measure the `0040-05` rule only because `DEC-0040-007` fixed one. | implementer |

## 5. Boundaries

No implementation, no `DEC-`/policy/tool/`TODO`-marker edit, no Acceptance, no
integration, no `main`, no `DONE.md`, no push. Write scope was this record and the
claim. `scope-ready-for-mutation` is **not** Acceptance and authorizes no integration;
it releases the pre-mutation scope gate only, and only for the reach CON-02 enumerates.
This review pins the candidate exactly and does not extend to any successor commit.

My R1 artifact `5ff5aae54` is unchanged and remains the baseline this candidate was
measured against.

---

## 6. Post-verdict baseline re-measurement (append-only, 2026-08-26)

**The verdict in the header is unchanged.** This section is appended after it, records a
measurement taken after `main` advanced, and neither revises nor re-opens the decision
above. Recorded on Project Lead instruction (`agent-inbox:1787753849975-bcfa6724`) after
the hold on this branch was lifted.

### 6.1 Why the re-measurement was taken at all

`main` advanced from `059f7e326` — the base this review was cut from and measured
against — to `4d3f3fefae2d50fcff3d323db01451ed2d1079f9`. Three commits, and one of them
touches **`docs/dossiers/dec-0041-006-atomic-implementation-checkin.md`**: the exact file
condition C5 rests on. A green verdict whose baseline has moved will otherwise be reused
as though nothing happened, so the move was measured rather than assumed harmless.

### 6.2 Result — C5 survives, and is better supported than when it was written

| Load-bearing premise of C5 | State on `4d3f3fefa` |
|---|---|
| `DEC-0041-006` CON-05 keeps the `0041` rule **non-operative** until its own cutover | **Still true, and strengthened** — the correction adds `docs/pipeline/core-rules.md`, `_src/tools/legacy_task_editor.py` and `_src/tools/check_integration_hygiene.py` to the consumers that must all agree before cutover |
| `DEC-0041-006` carries **no trailer-exclusivity clause** | **Still true** — measured, zero matches; CON-02 there fails closed on missing/malformed/non-ancestor/stale/contradictory trailers, not on additional ones |
| No path overlap between `DEC-0041-006`'s consumers and `DEC-0044-027` CON-02 | **Confirmed** — set intersection computed, empty |

Saru's scoping of the Family B predicate to **post-cutover** commits therefore still
carries: before `0041`'s cutover no commit matches it, so no overlap can arise and
`0044-12` cannot pre-activate `0041`'s rule.

### 6.3 What did become false — `DEC-0044-027` CON-07

CON-07 named `4a11a0d284d1ce643c233bf9d208ca9cccf7322d` (with Jadzia transcription
`6e967dd9a7f0b5bf3766735f497c149c6362acd6`) as an **open** `0041` dependency and stated
it "must not be treated as already on `main`". Both are reachable from `4d3f3fefa` —
verified with `git merge-base --is-ancestor`. The statement is factually false as of
that advance.

The error direction is the harmless one: the record claims **more** openness than exists,
so it authorizes nothing additional. It was nonetheless reported before integration,
because a record carrying a demonstrably false claim about the state of `main` will later
be cited by someone.

### 6.4 Downstream corrections, independently verified rather than accepted on report

| Gate | Commit | Verification |
|---|---|---|
| **G2** (F-R2-01) | `629c52d6cfd0e8bfca22eca9a4a1ee3542f4c2a0` | diff vs `2cf41dc90` is **exactly** the single deletion `- \`integration:repository-main\``, nothing else; record digest `6818d58a…c50cf` reproduced |
| CON-07 correction | `c884782813624ca1c69f53c1a01b49e733770f91` | one file, one hunk, **exactly** CON-07; CON-04/-05/-06/-08/-09 unchanged in context; parent `629c52d6c` preserved, no rebase or amend; digest `71eca5db…ce9d7` reproduced |

The corrected CON-07 marks the dependency **closed**, names both commits and the
reachability base, states the verification method, and **retains** the operative clause
that they "remain not authority for `0044-12` CON-02 mutation" — a change to a factual
claim with the reach statement left untouched, which is the correct shape.

### 6.5 Gate status at time of appending

**G1 open** — `DEC-0044-027` must be on `main` before the first `0044-12` mutation; the
candidate line is based on `059f7e326` while `main` is at `4d3f3fefa`. **G2 closed and
verified. G3 open**, with the later implementer. The CON-07 correction is additional to
the three gates and also verified.

Nothing in this section authorizes integration or activation, and the verdict's own
boundary is unchanged: it pins candidate `2cf41dc908e1f34af699153179b85238418cf918` and
does not extend to any successor commit. The successors verified in §6.4 are recorded as
**measurements**, not as a re-issued verdict over them.
