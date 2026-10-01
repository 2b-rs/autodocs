# Independent Architect scope review — Feature `0022` / Task `0022-01`

**Verdict:** `scope-ok-with-conditions`

**Reviewer:** `agent:saru:0022-01-scope-review:20260828T100338Z`, management-instantiated Architect, Team Discovery, `privileged` for this record only. Distinct from `agent:data:0022-01:20260828T095108Z-3e883c05` and from any later Implementer. Privilege is not independence, Acceptance, or Integrator authority.

**Award:** offer `1787911418604-da442b87` (notice `1787911418605-46bc094c`). Mail is not additional authority.

**Exact candidate:** `0022-01@1d4776bb7112ea5bca689d80ac18f32e8d610018`

**Substantive proposal REF:** `0ce489193b5c50090340b327854d3c6dc21626cd`

**Proposal SHA-256:** `126774f75bac69f1c5dcc8784bfb4de61c1b55542a57e9d8afc2950b23177080` (`docs/dossiers/0022-feature-breakdown-proposal.md`, remeasured)

**Brief SHA-256:** `ba59f8314d80ccf4dfbbba62484a1d63c903c3b9f91c58379a70d3f3e02ad3bc` (`docs/campaign-evidence/0022-01/independent-scope-review-brief.md`, remeasured)

**Claim-first REF:** `752f1ee11c7098a518ceb9c0c0cd1c60521dadf5`

This is a pre-mutation scope review. It is not Task Acceptance, integration review/verdict, implementation, Feature closure, DEC allocation, or authority to advance `main`.

---

## 1. Remeasured pins

| Input | Result |
| --- | --- |
| Current `main` | `4e247b3ee34f0d8baec54e012db6591b0a41c8a0`. Merge-base with the candidate is `542d9fa31fd6916571e2a7602c8179eeda9e0d6d` (the proposal's pinned TODO `main`). Candidate is not an ancestor of current `main`. |
| Main-only delta vs that pin | Three commits, all `0037-10.04` (`issuectl` query surfaces + `[x]` bookkeeping). `TODO.md` Feature `0022` / `0023-11` / `0024-02` / `0028`–`0032` sentences are unchanged. **Not material** to SYS interface reach. |
| Task `0022-01` on current `main` | `[ ]`, PREREQ `0020-09`. No architecture-hold `[u]`. |
| Task `0022-01` on candidate | `[u]` architecture-preparation hold pointing at this review. Proposal REF `0ce489193` named. |
| `DEC-0020-001` / `DEC-0020-002` / `0020-02` review | On the **candidate** line: `docs/dossiers/dec-0020-02-evidence-boundary-enforcement.md` blob `da4242a865aede7fa567c0a37ffc740b4ce24d7f`; supporting review blob `1717e89262c557fda6fd5a86094d59f33a8a7351`. Those two paths are **absent from current `main`**. `decision-record.md`, `feature-breakdown.md`, and `AGENTS.md` blobs match between candidate and current `main`. |
| `0020-03` / `0020-04` / `0020-09` | Candidate carries merged `0020-09@032fcb6cc` / register blob `74e19d1e5f2936dd26087cab7b524ebbdb0238b1`. Current `main` still has `0020-09` `[ ]` and no register file. Expected for this branch; later `DEC-0022-*` allocation on `main` must not pretend `0020-09`/`DEC-0020-002` are already on that tip. |
| `0023-11`, `0024-02`, `0028`–`0032` | Remeasured from current `main` and the candidate `TODO.md` (same consumer sentences aside from line-number shift). See Q2. |

Independence, baseline identity, and Data authorship of the proposal are unambiguous. Review proceeds (not `scope-inconclusive`).

---

## 2. Answers to the seven questions

### Q1 — Does `PD-0022-01-GATE-01` require a new `decision-record@v1`?

**Yes.** `DEC-0020-002` already decides refuse-at-use/freeze for named Feature `0020`/`0025` consumers, forbids a default `_src/validate.py` gate, and forbids extra start-prerequisites onto `0022`–`0032`. It does **not** decide the SYS interface-row schema, `not-decided` vs activation semantics, `0023-11` use-time acceptance, the `0022-01`/`0022-02.*`/`0022-03` graph, or checkpoint placement. No other existing record on the candidate covers that whole subject. The proposal correctly refuses to mint `DEC-0022-*` here.

### Q2 — Are `0023-11`, `0028`–`0032`, Feature `0022` closure, and `0024-02` correctly classified?

**Mostly yes, with binding classifications:**

| Unit / gate | Classification | Evidence |
| --- | --- | --- |
| `task:0023-11` | **Direct use-time** consumer of SYS.2/SYS.3 allocated inputs. **Not** a current start-prerequisite of `0022-01`, and must not become `task-start:0023-11` via this decision. Current PREREQ is `0020-09`, `0027-05` only. | `TODO.md` `0023-11` text |
| `task:0029-01`, `0030-01`, `0031-01`, `0032-01` | **Direct** affected units: they already name `0022-01` as a start prerequisite. Activation of internal SYS.2–SYS.5 remains conditional on profile. | current `TODO.md` |
| `task:0028-01` | **Conditional future SYS.1 activation**, not a current `0022-01` start edge. Current PREREQ is only `0020-08`. Listing `task-start:0028-01` as an affected *future* activation gate is acceptable; treating it as an existing 0022 start contract is not. | current `TODO.md` |
| `feature:0022` closure / `task:0022-03` | **Direct.** The Feature currently has no terminal integrating Task (`F-0022-ARCH-01`). | backlog: only `0022-01` and `0022-02` |
| `task:0024-02` | **Downstream** selected-profile / release consumer of validation or approved external/shared acceptance (SYS.5/VAL interface), **not** `task-start:0024-02`. Current PREREQs are `0020-09`, `0024-01`, `0027-02`–`0027-08`. Do not add `0022-01` as a start predecessor. Name the affected gate as use/release selected-profile edge, matching `DEC-0020-002`'s refuse-at-use pattern. | current `TODO.md`; answers `F-0022-ARCH-03` |

### Q3 — Does `not-decided` correctly permit a definition row while failing activation/use?

**Yes.** Matches `0020-03` unnamed parties and `F-0022-ARCH-04`. A definition record may store `not-decided`; any consumer activation or evidence gate that requires a named performer/acceptance authority must fail closed. No agent may fill OEM/customer/supplier/assessed-unit roles from silence.

### Q4 — Does the proposal avoid the broad start/validation gate rejected by `DEC-0020-002`?

**Yes**, if the Q2 classifications are kept. ALT-04 correctly rejects adding `0029`/`0030` as unconditional predecessors of `0023-11`. Candidate-root-only validator and explicit ban on `_src/validate.py` match CON-02/CON-03 of `DEC-0020-002` and the `0020-02` scope review (no new start-gates onto `0022`–`0032` from *that* decision; this new decision may still add *use-time* SYS interface refusal without a repository-wide suite).

### Q5 — Is `0022-01` an appropriate intermediate mandatory checkpoint, with `0022-03` the exactly-one terminal integrating Task?

**Yes, with conditions.** `0022-03` is the required Feature floor. `0022-01` as an intermediate checkpoint is justified as the shared interface baseline consumed by multiple later units. Unflagged `0022-02.01`/`.02`/parent behind those two checkpoints matches the “not every child” rule. **Binding:** the `0022-01` checkpoint must not be converted into new `task-start` edges on `0023-11` or `0024-02`.

### Q6 — Is the `0022-02` split bounded, complete, and free of duplicate ownership?

**Yes.** `.01` schemas/contract, `.02` candidate-root validator, parent aggregation-only with findings returned to child owners. Write scopes are disjoint. The split covers the current `0022-02` sentence without a second owner of the same product. **Binding:** parent must not edit child products except through returned findings; `.02` must not register a default shared validator.

### Q7 — Are recovery, no-grandfathering, self-application, A1/A2, and later acceptance/integration boundaries complete?

**Yes as architecture, incomplete as mechanical A1 fields.** §7 states activation order, no grandfathering, self-application (no retroactive Feature-branch certification), rollback before/after activation, and that Acceptance/Integrator remain separately assigned. A2 is correctly defined as canonical blast-radius, not ordinary delay. **Condition:** before operative backlog mutation, record the `feature-breakdown.md` A1 field shape (`checked_at`, `recorded_by`, `basis`) on the breakdown that is actually activated; citing “A1 evidence” in prose is not that field.

---

## 3. Binding conditions (for later `DEC-0022-*` / backlog activation)

1. **C-GATE-CLASS:** Encode Q2 classifications in the decision's affected-units/gates list. `0024-02` is downstream use/release, not `task-start:0024-02`. `0023-11` is use-time, not `task-start:0023-11`. `0028-01` is future SYS.1 activation, not a current `0022-01` start edge.
2. **C-NO-BROAD-START:** Do not add SYS Tasks or `0022-01` as unconditional start predecessors of `0023-11` or `0024-02`.
3. **C-NO-SHARED-VALIDATOR:** `0022-02.02` remains candidate-root-only; no `_src/validate.py` or default shared-suite registration without a new TK-2 decision.
4. **C-DEC-ON-MAIN:** Allocate `DEC-0022-*` against then-current `main`. Do not mint the identifier on `0022-01`. Cite `DEC-0020-002` only from a pin that will be reachable on the implementation/governance baseline; current `main@4e247b3ee` does not contain that dossier path.
5. **C-A1-FIELD:** Add the mechanical A1 record before operative Task-graph mutation.
6. **C-CHECKPOINT-REACH:** `0022-01` Integration review: mandatory reviews the interface contract; it does not by itself start or block `0023-11`.
7. **C-NOT-DECIDED:** Keep `not-decided` non-passing at every activation/use/evidence gate.

Green tests, if any later appear, still do not establish reach or authority.

---

## 4. Stable findings (non-blocking; already named by the proposal or classified here)

- `F-0022-ARCH-01` — missing terminal integrating Task: **supported**; `0022-03` is the floor.
- `F-0022-ARCH-02` — `0022-02` split: **supported**.
- `F-0022-ARCH-03` — `0024-02` class: **resolved as downstream** (Q2).
- `F-0022-ARCH-04` — unnamed performer/authority: **supported**; fail closed at use.

No `scope-needs-revision` finding on the proposed architecture if the conditions above travel with the DEC.

---

## 5. What this review does not do

No `DEC-0022-*` allocation, no `TODO.md` operative mutation, no implementation, no Acceptance, no checkpoint/integration verdict, no `main` movement, no `memory_append`. Chain ends at this record. Project Lead routes any Management decision and later Implementer assignment.
