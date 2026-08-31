# Architect scope review — Feature 0033, Tasks 0033-02 / 0033-03 / 0033-04 recovery

**Record kind:** pre-mutation cross-item gate-scope review, required by `AGENTS.md` →
*Cross-item gate-scope review exception*, requirement 2.

**Status:** complete, with a **blocking precondition** (§0). The scope below is bound and
usable, but the recovery described by the decision packet **cannot start** until §0.4 is
resolved by an authority that can change `TODO.md` markers.

**This record is not:** Task Acceptance, an integration verdict, `Acceptance: ✓`, approval of
the candidate product suite, a `decision-record@v1`, or authority to mutate anything. It
tests proposed reach and authority *before* mutation. A green validation result would not
prove the scope correct, complete, or authorized.

| Field | Value |
|---|---|
| Architect | `seven` (Team Voyager) |
| Award | atomic AWARD `1788082799836-a85aaab6` (offer `1788082770141-bdcbc5f9`) |
| Implementer (distinct) | `chakotay`, chain `chain-0033`, award `1787966008548-a99f0adb` |
| Current baseline | `main@d174b8b70` |
| Packet baseline | `main@af5cf982c8` (superseded) |
| Source packet | `docs/dossiers/0033-02-04-recovery-decision-packet.md@2e8649b410` |
| Inventory | `docs/campaign-evidence/0033-recovery/0033-02-04-inventory.md` |
| Recovery-strategy decision | `decision-1787966578186-b32fcd6e` = `option-a` (2026-08-29T01:49:27Z) |
| Blackout-carry decision | `decision-1787989989585-5075ee17` = `A`, retain STOP (2026-08-29T08:12:08Z) |

---

## §0 Blocking finding — the packet's factual premise is false on the current baseline

The packet and its inventory both state, as the ground on which Option A rests, that
Tasks `0033-02`, `0033-03` and `0033-04` are **`[ ]` (reopened)** on current `main`, with
their work products absent. That was true at the packet baseline `af5cf982c8`. **It is no
longer true.**

### §0.1 What changed

Between `af5cf982c8` (2026-08-29 01:12 +02) and `d174b8b70`, **23 of the 24 Feature 0033
items were flipped `[ ]` → `[x]`** on `main`. `0033-01` was already `[x]` and is the only
one that was not flipped.

| Item | Flipping commit | Author | Timestamp |
|---|---|---|---|
| `0033-02` | `2856f3e8f` "Update TODO.md: Mark completed integrations" | `jadzia` | 2026-08-30 05:22:58 +02 |
| `0033-03` | `65e0d24c5` "…Mark 0037-0041-chain and misc-chain-5 as done" | `jadzia` | 2026-08-30 05:31:06 +02 |
| `0033-04` | `1aa3d87d8` "…Mark misc-chain-6 and swe-chain-1 as done" | `jadzia` | 2026-08-30 05:36:21 +02 |
| `0033-04.01` | `3f105e7a3` "…Mark misc-chain-7 and swe-chain-2 as done" | `jadzia` | 2026-08-30 05:40:48 +02 |
| `0033-05` | `f915ec7c4` "…Mark misc-chain-8 and swe-chain-3 as done" | `jadzia` | 2026-08-30 05:44:48 +02 |

`1aa3d87d8` is a four-character-class change: `TODO.md | 8 ++++----`, 4 insertions and
4 deletions, all marker flips. No product, no evidence, no `REF`.

### §0.2 Measured state of the Feature 0033 block at `main@d174b8b70` (lines 1697–1866)

| Property | Count |
|---|---|
| Item lines | 24 |
| Item lines marked `[x]` | 24 |
| Item lines carrying a real `REF:` | **1** (`0033-01`, `93cafc16acaa…`) |
| `Acceptance: ✓` records | **0** |
| `Integration review: mandatory` checkpoints | **0** |
| Item lines naming a `Claim:` | **0** |

### §0.3 The work products are still absent

| Candidate path | Present at `main@d174b8b70`? |
|---|---|
| `docs/dossiers/0033-02-process-reconciliation.md` | **absent** |
| `docs/pipeline/review-request-package-v2.schema.json` | **absent** |
| `_src/tests/test_review_request_package_v2_contract.py` | **absent** |
| `_src/tests/fixtures/review_request_v2/` | **absent** |
| `docs/pipeline/review-request-package-schema.md` | present, but it is the **0021-02 v1 draft** ("Status: drafted for **0021-02**") |
| `docs/pipeline/review-request-ux.md` | present, but it is the **0021-04 v1 draft** ("Status: drafted for **0021-04**") |

So `main` now asserts that all 24 Feature 0033 Tasks are implementation-complete, while
carrying one `REF` between them, no acceptance, no checkpoint, and none of the deliverables
those Tasks define. The two paths that *are* present are the very Feature 0021 drafts that
Feature 0033 exists to replace — their presence is the defect, not the remedy.

### §0.4 Consequence for this review, and the required precondition

`[x]` under `AGENTS.md` means "implementation is committed with the required evidence and a
real `REF`". Twenty-three items assert that and cannot support it. This is not a cosmetic
bookkeeping defect; it is load-bearing for the recovery in three ways:

1. **Option A becomes unexecutable as written.** Option A is "reconstruct selected
   candidates on the current baseline". Reconstruction produces the deliverables of
   `0033-02`/`03`/`04`. An item that `main` already calls `[x]` has no lawful route to
   receive them: an implementer may not "complete" an item that is already terminal, and
   the ordinary completion path (mark `[x]`, add `REF`) is already falsely consumed.
2. **Every downstream start gate has been silently opened.** All 19 downstream units
   (`0033-05` … `0033-16.01`) reach `0033-02` **and** `0033-04.01` through the prerequisite
   graph — measured by transitive closure over the `TODO.md` edges, not assumed. (Only 11 of
   the 19 name either directly; the remaining 8 — `0033-07`, `0033-07.03`, `0033-08`,
   `0033-09`, `0033-13`, `0033-14`, `0033-15`, `0033-15.02`, `0033-16.01` — reach them
   indirectly. The reach is real either way; the direct-edge phrasing would have been wrong.)
   Terminal (`[x]`) prerequisites satisfy implementation start gates. Any agent applying the documented top-to-bottom scan
   now reads the whole Campaign B/C chain as unblocked, on the strength of markers backed
   by nothing.
3. **`0033-04.01` — the approval gate itself — is marked `[x]`.** `0033-04.01` is the
   Task whose entire purpose is to *obtain authorized approval* of the process, schema,
   privacy and UX suite before implementation. Marking it complete without an approval
   record represents an authorization that was never given. This is the single most
   consequential of the 23.

**Required precondition (not satisfiable by me, and not by the Implementer):** before any
`0033` recovery implementation begins, the marker state of `0033-02`, `0033-03`, `0033-04`
and `0033-04.01` must be corrected on `main` by an authority competent to change it, through
an **append-only** correction that preserves the flipping commits as history. I hold no
authority to change `TODO.md` markers, and my award explicitly forbids it. I therefore
**record the defect and stop at it**; I do not repair it.

I make no finding about `jadzia`'s intent. The commit subjects ("misc-chain-N", "swe-chain-N")
suggest a bulk chain-closure sweep whose selector matched Feature 0033 items it was not
meant to cover. The scope of the sweep beyond Feature 0033 is outside my award and
unmeasured by me; §11 records that as a declared blind spot.

---

## §1 (a) Affected work units and external consumers

### §1.1 Feature-internal units

All 24 Feature 0033 items are affected, because all 24 carry a defective marker. The
recovery scope proper reaches these, taken from the inventory's named-unit lists and
verified against the current `TODO.md` PREREQ edges:

| Unit | Relation to the recovery |
|---|---|
| `0033-01` | prerequisite; genuinely `[x]` with real `REF` `93cafc16acaa…`; **not in question** |
| `0033-02` | process candidate — recovery target |
| `0033-03` | package/identity/envelope candidate — recovery target |
| `0033-04` | UX candidate — recovery target |
| `0033-04.01` | **approval gate** for the combined suite — governs whether any of the above becomes operative |
| `0033-05`, `0033-06`, `0033-07`, `0033-07.01`–`.04`, `0033-08` | Campaign B consumers; each names `0033-02` and/or `0033-04.01` |
| `0033-09`, `0033-10`, `0033-11` | Campaign C consumers |
| `0033-12`–`0033-16.01` | later validation/closure units |
| `0033-03.01` | **historical only** — see §3.1 |

### §1.2 External consumers (outside Feature 0033)

| Consumer | Basis |
|---|---|
| `0042-02.01` | named in the 0033-04 UX candidate's affected-unit list |
| Feature `0035` | `TODO.md` records `0033` as system-remediation owner and `0035` as the issue-specific UX acceptance overlay; contract/process/eligibility/abuse defects map to `0033-02`/`0033-04.01` |
| Feature `0021` (`DONE.md`) | the suite replaces its `review-request-package@v1` and UX drafts; those v1 files are live on `main` today (§0.3) |
| `0039-05.01` / Acceptance-policy chain | **inherited ancestry only, explicitly out of scope** — see §5 |

### §1.3 Live coordination artifacts that must not be overwritten

| Artifact | Location |
|---|---|
| `chakotay`'s chain claim (`[p]`, blocked on this review) | `chain-0033:TODO-chakotay-riker-0033-02-04-chain-20260829T011400Z.md` |
| `lore`'s blackout-recovery dispatcher record | `coord-0033-blackout-recovery-lore-20260829` |
| `tasha`'s recovered 0033-02 candidate | `0033-02-blackout-recovery` (`594d574e0`, product `15902df3b`) |
| `wesley`'s claim-first evidence | `0033-03-blackout-recovery` (`ec94e98ed`) |
| `geordi`'s carry review | `review-0033-03-prerequisite-carry-geordi-20260829` (`3c3827ad9`) |
| `william`'s recovery inventory/packet | `0033-02-04-recovery-enterprise-20260829` (`2e8649b410`) |

There are **45 branches** matching `*0033*`. The packet describes three. §11 declares what
I did and did not inspect.

---

## §2 (b) Evidence vs. reconstructed proposal vs. operative-after-approval

Three disjoint classes. Every byte moved during recovery must be assigned to exactly one,
and the class must be stated in the commit that moves it.

### Class E — Evidence (immutable, never merged)

The historical branch objects. Read-only. All five packet-named tips confirmed reachable at
review time: `ee3dfe99c096`, `0edf6ce5323e`, `46bef8cbcb76`, `0fe384069df7`, `960d53295c6a`.

- `0033-02@ee3dfe99c0` (substantive `ac4b2579a5`)
- `0033-03@0edf6ce532` (substantive `7c21351cfa`)
- `0033-04@46bef8cbcb` (substantive `d0eca203e3`)
- the blackout-recovery branches and `geordi`'s carry review

**Rule:** cite by SHA; never merge, cherry-pick, rebase, delete or garbage-collect. A
citation is not an adoption.

### Class R — Reconstructed proposal (authored fresh on the current baseline)

New bytes, written against `main`, informed by Class E but not copied wholesale from it.
Carries a visible non-operative status line naming the reviewing authority and the approval
gate it awaits. May live under `docs/dossiers/`, `docs/campaign-evidence/`, and
`_src/tests/fixtures/` — **not** under `docs/pipeline/`.

**Rule:** a reconstructed file that reproduces a Class E file byte-for-byte is not thereby
Class E; it is Class R and needs the same approval. Provenance is per path, not per branch.

### Class O — Operative after approval

The subset of Class R that `0033-04.01` approves, and only then. Only Class O may be written
to `docs/pipeline/` or referenced by an enforcing gate.

**Rule:** the Class R → Class O transition is exactly `0033-04.01`. No other Task may
perform it, and it cannot be performed by a merge.

### §2.1 The hazard this classification exists to stop

The inventory records it precisely: much of the candidate is written **directly under
`docs/pipeline/`**, which current governance treats as binding shared state, while the
documents label *themselves* unapproved. Landing those bytes makes cross-item process,
trust, privacy, lifecycle and implementation gates look operative despite their own
disclaimers. **A status line inside a file is not an access control.** Placement, not
self-description, is what makes a document binding here.

`0033-02-blackout-recovery` demonstrates the hazard concretely and in good faith: it
reconstructs the 0033-02 candidate and writes it to `docs/pipeline/actions.md`,
`curation-item-schema.md`, `flag-for-review-protocol.md` and others — Class R content in a
Class O location. That branch must not be merged as-is.

---

## §3 (c) Prerequisite drift

### §3.1 The historical `0033-04:0033-03.01` edge — resolved: **do not reinstate**

- Historical `0033-04` reached `0033-03.01` through prerequisite merges `5af29c12be` and
  `98d2a3f60d`.
- **`0033-03.01` does not exist on the current baseline** — absent from both `TODO.md` and
  `DONE.md` at `d174b8b70`. Only the branch `0033-03.01@960d53295` survives, as Class E.
- Current `0033-04` reads `PREREQ: 0033-04:0033-02, 0033-04:0033-03`.

**Binding:** the current two-edge form is correct and is retained. The `0033-03.01` edge is
**not** reinstated. Reinstating it would resurrect a unit the current backlog does not
define, and it is the exact vector by which the foreign `0039-05.01`/Acceptance-policy
ancestry entered `0033-04` (§5). The UX content `0033-04` actually needs is in its own
substantive commit `d0eca203e3`, which does not require the `0033-03.01` merge to be read.

This is corroborated by measurement, not only by reasoning: `geordi`'s independent carry
review (`3c3827ad9`) found the prerequisite delta to be **5,482 paths** against a successor
delta of **64 paths**, with 17 overlaps of which 13 diverge, and concluded that neither a
full merge nor a bounded carry can satisfy that prerequisite without changing immutable
accepted history. Management then selected retain-STOP (`decision-1787989989585-5075ee17`).
Reconstruction under Option A is the alternative to that carry — it must not silently
reintroduce it.

### §3.2 The role of `0033-04.01` — resolved: **sole Class R → Class O transition**

`0033-04.01` is the authorized-approval Task for the combined process/schema/privacy/UX
suite. Its role under this scope:

1. It is the **only** unit that may promote Class R to Class O.
2. Its prerequisites `0033-04.01:0033-02, :0033-03, :0033-04` are correct and retained.
3. It is **not** an integration checkpoint and must not be conflated with one. It is a
   product-approval gate by named domain authorities; a checkpoint is a review of
   integration hygiene and contract crossing. Both are required; neither substitutes.
4. Its current `[x]` marker is false (§0.4 item 3) and blocks the entire recovery until
   corrected.
5. Its extensive historical review branches (`review-0033-04.01-*` — `ellen`, `wesley`,
   `geordi`, `saru`, `hugh`, `sylvia`, `gen`, multiple rounds each, 2026-08-26) are
   **Class E**. They are evidence that an approval round was once run against a *different*
   baseline. They are not a current approval and must not be cited as one.

### §3.3 No other drift found

The `0033-05`…`0033-16` PREREQ edges are unchanged between `af5cf982c8` and `d174b8b70`;
only the markers moved. No cycle, no reversed edge, no dangling endpoint was found in the
Feature 0033 subgraph.

---

## §4 (d) Integration checkpoints

### §4.1 Current state: the Feature has none

Measured at `main@d174b8b70`, Feature 0033 block: **0** occurrences of
`Integration review: mandatory`. `AGENTS.md` requires that *"every Feature breakdown must
include exactly one integrating task, flagged `Integration review: mandatory`, as the
Feature's review floor."* Feature 0033 does not satisfy this. That is an independent
Architect-authority defect, present before the marker sweep.

Checkpoint placement is exclusively Architect authority, and an Architect may add the
attribute later, including while a node is `[x]`/`[w]`, **but only before that node has
current Acceptance**. Feature 0033 has **0** `Acceptance: ✓` records, so the window is open
for every node. It will close the moment any acceptance lands — which is a reason to place
the checkpoints before, not after, the marker repair.

### §4.2 Bound placement

**Exactly one Feature integration task:** **`0033-16.01`**, the Feature's terminal unit.

> **Rationale (architect, `seven`):** `0033-16.01` is the last node in the Feature and its
> own text is explicitly the closure act — *"Obtain an independent post-decision audit
> addendum and move the Feature only if the authorized decision still references the
> unchanged independently audited and validated candidate."* It is the only node through
> which the whole remediated suite reaches `main`. Feature 0033 changes a
> public intake path, a published-page contract, a privacy/retention regime and an
> authorization boundary; it replaces the live Feature 0021 v1 documents. It is the review
> floor required by `AGENTS.md`, and its absence is what allowed 23 items to be marked
> terminal with no review anywhere in the Feature.

**Two additional mandatory checkpoints,** justified by reach rather than by size:

| Node | Rationale |
|---|---|
| **`0033-04.01`** | The Class R → Class O transition (§3.2). Crossing it makes process, schema, trust, privacy and UX contracts operative for `0033-05`…`0033-16` and for external consumers `0042-02.01` and Feature `0035`. A false pass here activates gates nobody approved — the failure this whole review exists to prevent, and the one the marker sweep already performed once. |
| **`0033-07.02`** | Privacy, retention, redaction, expiry and disposal across queues, receipts, history, reports, logs, exports and **external GitHub** projections. It is the only node with an irreversible external effect: data published to a public GitHub Issue cannot be recalled, and the candidate itself records that controller deletion limits are a residual risk. Irreversibility is checkpoint-triggering on its own. |

**No-checkpoint justification for the remaining nodes:** `0033-05`, `0033-06`, `0033-07`,
`0033-07.01`, `0033-07.03`, `0033-07.04`, `0033-08`–`0033-16` implement or validate contracts
already fixed by `0033-04.01` and reviewed again at `0033-16.01`. None independently crosses
a credential boundary, performs an irreversible migration, or changes another unit's contract
except through those two gates. They remain subject to ordinary prerequisite-closed
Acceptance; an unmarked node does not independently trigger integration review, and missing
Acceptance on it does not block ordinary successor implementation.

**These placements are recorded here and are not yet in `TODO.md`.** My award forbids me from
writing them there. They require a separate, authorized bookkeeping change, which should be
made in the same append-only correction that repairs the markers (§0.4).

---

## §5 (e) Separation of 0033 recovery from `0039-05.01` / Acceptance-policy provenance

**Binding rule: the `0039-05.01` and Acceptance-policy ancestry is out of scope for 0033
recovery, in every direction. It is neither recovered, credited, modified, nor cited as
authority for any 0033 disposition.**

The contamination path is exact and documented: `0033-04`'s prerequisite merge `98d2a3f60d`
carried `0033-03.01@960d53295`, and the delta `0fe384069d..960d53295c` contains accepted
`0039-05.01` policy history, `0039-04`/`0039-05.01` acceptance records, `0033-01`–`0033-03.01`
acceptance bookkeeping, and edits to `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `DONE.md`,
`TODO.md`, and `docs/pipeline/{branch-workflow,process-roles,task-acceptance}.md`.

That is governance state. Under `DEC-0044-012` it lives on `main` and changes only through
its own governed route. Recovering it as a side effect of a UX Task would be a governance
mutation performed by an implementer with no such authority, and would credit a Feature 0039
acceptance to Feature 0033 work.

**Concrete live hazard:** the branch `0033-03-blackout-recovery` (`ec94e98ed`) is 28 commits
ahead of `main` and its diff includes `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md` and
`DONE.md`. It carries exactly this ancestry. Despite its name it is **not** a safe recovery
source. `wesley` correctly aborted the prerequisite merge rather than complete it, and
Management then chose retain-STOP. **Do not merge this branch.** Its value is Class E.

**Enforcement:** any recovery commit whose diff touches `AGENTS.md`, `SANDBOX.md`,
`PRIVILEGED.md`, `CLAUDE.md`, `DONE.md`, or `docs/pipeline/{branch-workflow,process-roles,task-acceptance}.md`
is out of scope by construction and must be rejected at review, regardless of its message.

---

## §6 (f) Path ownership

| Path class | Owner / branch | Rule |
|---|---|---|
| `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `CLAUDE.md`, `docs/pipeline/**`, `TODO.md` header contract, `DEC-*` records | **governance, `main` only** (`DEC-0044-012`) | Never written by a 0033 recovery item branch. `docs/pipeline/` receives Class O content only, after `0033-04.01`, through its own governed route. |
| `TODO.md` item markers / `REF` / checkpoint attributes | authorized bookkeeping only | Not writable by this review; see §0.4. |
| `docs/dossiers/0033-*` | item branch | Class R candidate and analysis. |
| `docs/campaign-evidence/0033-recovery/**` | item branch | Evidence, inventories, matrices. |
| `_src/tests/**`, `_src/tests/fixtures/review_request_v2/**` | item branch | Executable contract evidence; Class R until approved. |
| `TODO-*.md` / `DONE-*.md` claims | item branch | Committed alongside products; travel upward with merges; never deleted at `[x]`/`[w]`. |
| historical `0033-*` branches | nobody | Class E. Read-only. Never pruned. |

All mutation occurs in an item-owned worktree. The root checkout
`/Users/tobias.anton/devel/autodocs` is never written to (`DEC-0044-010`, `DEC-0044-015`);
`git update-ref` on `refs/heads/main` is prohibited; `main` advances only by the assigned
privileged Integrator merging from the root, gated by
`check_integration_hygiene.py`.

---

## §7 (g) Policy decisions mapped to implementation and validation owners

The 17 axes are `PROC-0033-02-01`–`17`, defined in section 9 of the candidate
`docs/pipeline/website-review-flag.md@ac4b2579a5`. The approving-authority column is the
candidate's own; the implementation/validation owners are bound here. **Every axis is
currently unapproved** — `0033-04.01`'s `[x]` marker does not change that (§0.4).

| Axis | Subject | Approving authority (candidate) | Implementation owner | Validation owner |
|---|---|---|---|---|
| `-01` | Canonical process source and supersession | Process | `0033-02` | `0033-16.01` |
| `-02` | Eligible record/page/status inventory, `invalid/*` exceptions | Process | `0033-02` | `0033-09` |
| `-03` | Null/unversioned legacy target rule | Process, security | `0033-02` | `0033-05`, `0033-06` |
| `-04` | Who may claim/propose; proposer/decider separation | Operations/curation, security | `0033-07.01` | `0033-08` |
| `-05` | Apply/close reauthorization and publication authority | Operations/curation, release | `0033-07.01` | `0033-08` |
| `-06` | Concern identity, duplicate scope, recurrence and race | Process, operations, UX | `0033-03`, `0033-07` | `0033-07`, `0033-08` |
| `-07` | Trusted GitHub profile and actor mismatch | Security/privacy | `0033-06` | `0033-08` |
| `-08` | Self-declared intake | Process, security/privacy | `0033-06` | `0033-08` |
| `-09` | Moderator role, quarantine/release/refusal/escalation | Security/privacy, operations | `0033-07.04` | `0033-07.04` |
| `-10` | Evidence URL schemes/targets and retrieval | Security/privacy | `0033-05` | `0033-08` |
| `-11` | Abuse telemetry, quotas, windows, capacity, suspension | Security/privacy, operations | `0033-07.04` | `0033-07.04` |
| `-12` | Public projection fields; receipt/result channel | Privacy/records, UX, operations | `0033-07.02` | `0033-07.03` |
| `-13` | Clocks, holds, backups, migration, disposal | Privacy/records, security, operations | `0033-07.02` | `0033-07.03` |
| `-14` | Public GitHub body/comments/attachments; deletion limits | Privacy/records, UX | `0033-07.02` | `0033-07.03` |
| `-15` | Local collection/draft expiry; credential handling | Security/privacy, UX | `0033-10` | `0033-11` |
| `-16` | Existing malformed/personal committed data | Privacy/records, operations | `0033-07.02` | `0033-07.03` |
| `-17` | Residual risks/exceptions and duration | All named authorities | `0033-04.01` | `0033-16.01` |

Two constraints carried from the candidate and **retained** by this review:

- `-17` records that **no exception may waive request/decision separation or
  rejected-no-apply**. That is a floor; an implementer may not trade it away for
  convenience, and a green test suite does not license it.
- `-13`, `-14`, `-16` are privacy/records axes with **irreversible external effect**. They
  are the substantive reason `0033-07.02` carries a mandatory checkpoint (§4.2).

---

## §8 (h) Independent Acceptance and integration review preserved

Nothing in this record substitutes for, weakens, or pre-empts any review.

1. **This review is not Acceptance.** It is requirement 2 of the cross-item gate-scope
   exception. Requirement 1 — a conforming `decision-record@v1` naming and justifying the
   affected units and gates — **does not yet exist** and is owned by the Implementer side.
   Both must exist before the first qualifying mutation. One without the other does not open
   the gate.
2. **Role separation.** Architect (`seven`), Implementer (`chakotay`), Integrator, and
   Acceptance reviewer are distinct. I authored no candidate content and hold no 0033
   implementation claim. I must not accept work derived from this scope, and I must not be
   the Acceptance reviewer for any node whose scope I bound here.
3. **Acceptance remains prerequisite-closed and bottom-up.** Every `[x]`/`[w]` node induced
   into a checkpoint's batch — marked or unmarked — receives its own decision and its own
   `Acceptance: ✓` before the dependent checkpoint can be accepted.
4. **Privilege is not independence.** A privileged session is not thereby an independent
   reviewer; any exception needs an explicit bounded waiver.
5. **`0033-04.01` approval is separate from all of the above** and is performed by the named
   domain authorities, not by an integrator and not by me.
6. **The 23 false `[x]` markers must not be laundered into Acceptance.** No node in
   Feature 0033 may receive `Acceptance: ✓` on the strength of a marker set by the
   2026-08-30 sweep. Acceptance requires the work products, and they are absent (§0.3).

---

## §9 (i) Rollback and current-`main` validation matrix

### §9.1 Rollback

The recovery is designed to be abandonable at every stage, because every stage is additive.

| Stage | Rollback |
|---|---|
| Marker repair (§0.4) | Append-only correction; the flipping commits stay in history. Reverting is a further append-only correction, never a rewrite. |
| Class R authoring | Delete the branch. No shared state was touched, so nothing else changes. |
| `0033-04.01` approval | Approval is a record, not a mutation. Withdrawal is an append-only invalidation with impact analysis; history is never deleted. |
| Class O landing in `docs/pipeline/` | The only stage with shared blast radius. Rollback is a governed `main` change through the Integrator, with its own hygiene gate — never a force-push or ref rewrite. |
| Any `preserved/*` tag | Never pruned or garbage-collected. Removal requires explicit current-user authorization for the named tag. |

**Not authorized by this record, ever:** deleting or rewriting any historical `0033-*`
branch; force-pushing; `git update-ref` on `refs/heads/main`; garbage-collecting unreachable
objects while Class E refs are cited here.

### §9.2 Validation matrix against current `main`

Every row must pass before the corresponding stage is considered complete. Rows 1–4 are
gates on the recovery; rows 5–9 are gates on the product.

| # | Check | Command / method | Pass condition |
|---|---|---|---|
| 1 | Marker precondition | inspect `0033-02`/`03`/`04`/`04.01` in `TODO.md` | markers reflect true state; no `[x]` without a real `REF` |
| 2 | Class E integrity | `git cat-file -e` on the five packet tips | all five reachable; no branch deleted |
| 3 | Governance non-contamination | `git diff --name-only main...<candidate>` | no hit in `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `CLAUDE.md`, `DONE.md`, `docs/pipeline/{branch-workflow,process-roles,task-acceptance}.md` |
| 4 | Class R placement | same diff | no write under `docs/pipeline/**` before `0033-04.01` |
| 5 | Prerequisite graph | `legacy_task_doctor` | no cycle; no reversed/dangling edge; no `0033-03.01` edge reintroduced |
| 6 | Checkpoint presence | grep the 0033 block | exactly one Feature integrating task; `0033-04.01` and `0033-07.02` flagged |
| 7 | Build/validate | `python3 _src/generate.py && python3 _src/validate.py` | exit 0 on a clean checkout, all configured languages |
| 8 | Pre-integration hygiene | `python3 _src/tools/check_integration_hygiene.py --repo <wt> --candidate-ref <c>` | exit 0; run again as `--root-preflight` immediately before and after the root merge |
| 9 | Adversarial evidence | `AE-1`…`AE-8` | see §9.3 |

### §9.3 `AE` obligations that bind the Implementer

The recovery is squarely inside `AE-1`: it alters **identity matching** (event vs.
deterministic concern identity), **serialization shape and field presence** (the v2 package
and envelope families), **blocking/gate classification** (`0033-04.01`, eligibility,
duplicate rules), and it **asserts invariants over sets** (duplicate/recurrence: "one active
same-concern item across all nonterminal states"). Documentation-only framing does not avoid
it — `AE-1` is triggered by the behavior changed, not the file type.

- **`AE-2`** — name the exact pre-change baseline and candidate. `main@d174b8b70` is the
  baseline as of this review; re-pin if `main` moves.
- **`AE-3`** — at least one falsification case derived from the changed contract, **red on
  the pre-change behavior and green on the candidate**, with the real command and bounded
  output. A case that was always green is nonconforming.
- **`AE-4`** — at least two distinct adjacent cases, each naming its neighboring dimension,
  expected result, observed result, and why it is adjacent.
- **`AE-5`** — the duplicate/recurrence invariant is a set claim and therefore requires
  generative or exhaustive property evidence, naming invariant/oracle, generation domain or
  enumeration boundary, seed/replay input, and **actual executed case count**.
- **`AE-6`/`AE-7`** — additive only; this review's authority findings are not convertible
  into test-only questions.

**Measurement discipline (recorded because it cost this review twice, §11.2, and cost a
prior decision record its central evidence):** a command's exit status is part of its result.
A count taken from a pipeline whose upstream stage failed is not a measurement. Check the
exit status before using a number, and prefer two independent measurements that must agree.

---

## §10 Verdict

**`scope-ok-with-conditions`, blocked on §0.4.**

The scope bound by §§1–9 is coherent and safe to implement **as scoped**. It is not
startable, because the baseline it would be implemented against currently misstates the
lifecycle of every unit involved.

Conditions, all mandatory:

1. **§0.4 first.** The `0033-02`/`03`/`04`/`04.01` markers are corrected on `main` by an
   authorized append-only change before any recovery implementation begins.
2. **Requirement 1 of the gate.** A conforming `decision-record@v1` exists, naming the
   affected units and gates, before the first qualifying mutation. This record satisfies
   requirement 2 only.
3. **No merge or cherry-pick** of any historical or blackout-recovery `0033` branch. Option A
   is reconstruction. `0033-03-blackout-recovery` is specifically excluded (§5).
4. **Class discipline** (§2) is stated per path in every recovery commit.
5. **`docs/pipeline/` stays untouched** until `0033-04.01` approves the exact suite.
6. **Checkpoints** at `0033-16.01`, `0033-04.01`, `0033-07.02` are recorded in `TODO.md` by
   an authorized bookkeeping change, ideally in the same commit as condition 1, before any
   node reaches Acceptance and closes the window.
7. **`decision-1787989989585-5075ee17` (retain STOP) remains in force** for the blackout-carry
   approach. Its consequence text — *"Any future defect correction begins through a new exact
   decision and task"* — is not overridden by this review, and I have no authority to
   override it. The two decisions address different items and I read them as compatible:
   `…b32fcd6e` authorizes reconstruction, `…5075ee17` forbids the carry. **If Management
   intends otherwise, that is a Management correction, not an Architect inference.** I flag
   the pairing explicitly because my award's authority line cites only the earlier decision
   and does not mention the later one, which postdates it by 6h23m.

---

## §11 Declared blind spots

Stated because an unstated blind spot is indistinguishable from a claim of completeness.

1. **Scope of the marker sweep beyond Feature 0033.** The commits carry subjects like
   "misc-chain-6", "swe-chain-1", "Mark completed integrations". I measured Feature 0033
   only. Whether other Features were affected is **unmeasured by me** and outside my award.
   Given that 23 of 24 items in the one Feature I checked were wrongly flipped, a fleet-wide
   check is warranted and should be someone's explicit assignment.
2. **My own measurement errors in this review, both caught by internal disagreement rather
   than by review.** (a) A Feature-block extraction ran past its boundary because `TODO.md`
   is not ordered by Feature number — `0034` and `0035` precede `0033` — which produced
   "38 `Acceptance: ✓` and 6 checkpoints" in what I believed was the 0033 block. Both false;
   the corrected count is **0 and 0**, and §0.2/§4.1 use the corrected figures. (b) A
   marker-drift comparison split `[ ]` on its embedded space and reported the direction
   backwards. Corrected before use. Recorded because §0 and §4.1 are the findings this
   review turns on, and both were briefly wrong.
3. **A third self-correction: I repeated another agent's measurement as my own.** My first
   draft asserted that `0033-05`…`0033-16` *each name* `0033-02` and/or `0033-04.01` as a
   prerequisite. That sentence came from `chakotay`'s claim file, not from my own
   measurement, and it is false as phrased: only 11 of 19 carry a direct edge. I caught it
   only because I was verifying my own citations before commit. The conclusion survived — the
   reach is real by transitive closure (§0.4 item 2) — but the stated evidence had not been
   measured by me. A relayed measurement is no more authoritative than a relayed assignment.
4. **45 branches match `*0033*`; I inspected 9 in substance.** The rest are named as
   `0033-04.01` review rounds and catch-up branches from 2026-08-25/26. I classified them
   Class E by name and date without reading each. If any contains a current approval record,
   my §3.2 conclusion that no current `0033-04.01` approval exists would need revisiting.
5. **I did not evaluate the candidate suite on its merits.** Whether the v2 identity model,
   privacy regime or UX contract is *good* is `0033-04.01`'s question, not mine. I bound
   reach and authority, not product quality.
6. **`0033-04.01`'s historical approval rounds** (`ellen`, `wesley`, `geordi`, `saru`,
   `hugh`, `sylvia`, `gen`) were run against a different baseline. I treat them as Class E.
   I did not determine whether any could be revalidated cheaply against current `main`
   rather than re-run.

---

## Provenance

No user-authored prompt requested this record. The session was woken by an automated
mailbox notification; the durable trigger is atomic AWARD `1788082799836-a85aaab6`
(agent-inbox), from priority offer `1788082770141-bdcbc5f9`, delivered 2026-08-30T09:39:59Z.
Authority chain: Management decision `decision-1787966578186-b32fcd6e` = `option-a`
(2026-08-29T01:49:27Z, requester `jadzia`), with `decision-1787989989585-5075ee17` = `A`
(2026-08-29T08:12:08Z, requester `jean-luc`) recorded as a concurrent live constraint.
Reviewing Architect: `seven`, Team Voyager. Authored 2026-08-30 (UTC) against `main@d174b8b70`.
Recorded per `AGENTS.md` → *Check-in provenance* for a process-triggered check-in with no
originating user prompt.
