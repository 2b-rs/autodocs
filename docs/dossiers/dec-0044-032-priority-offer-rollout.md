# `DEC-0044-032` — Priority-gated Assignment lifecycle as future start authority for new multi-Dispatcher rounds

This is a pre-mutation `decision-record@v1` for Task `0044-18`. It records the
**future** gate that, after a later separately authorized implementation assignment
and activation commit, requires every **new** multi-Dispatcher work round to use
the agent-inbox 1.16.2 Assignment lifecycle. Management
`decision-1787959369327-8349792b` rejects an as-written rollout; this record
does **not** implement, activate, accept, integrate, or close Feature `0044`.

**Authority for the substance:** current-user Management instruction of
2026-08-28 recorded in Task `0044-18` on `main`, plus Management appointment of
Architect Saru (`agent-inbox:1787959942820-df9ff687` /
`decision-1787959369327-8349792b`) and the atomic award
`agent-inbox:1787960044585-a1424e0a`. Mailbox is not that authority.

**Identifier allocation:** `DEC-0044-032`, checked against branch cut `main`
`6ec2314f58382a54c40a71f59c96ac7eeb08db7c` and remeasured `main` tips through
`de6340fe7` (`DEC-0044-001` … `DEC-0044-031` present; `DEC-0044-032` absent).

**External baseline (award update):** `external:agent-inbox` `main`
`f081d27645ab97bd48f92b5274d82eea4f202864`, `SERVER_VERSION = "1.16.2"`.
This supersedes the Task-text pin `2983630f7` / server v1.11.0 for any later
`0044-18` implementation assignment. Geordi preparation input
`f5b181e8f0371401692e38224ab484082d37ea25` is read-only context, not this
record's product.

---

### `DEC-0044-032` — Priority-gated Assignment lifecycle gate for new multi-Dispatcher rounds

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-29T02:30:00+02:00`
- **Deciding identity:** `agent:saru:0044-18-scope-review:20260828T235500Z`
- **Role:** `Architekt`
- **Authority reference:** `task:0044-18`; Management appointment `agent-inbox:1787959942820-df9ff687`; `decision-1787959369327-8349792b`; atomic award `agent-inbox:1787960044585-a1424e0a`; resume `agent-inbox:1787961207759-31332e96`; review input `agent-inbox:1787962832255-9de602cb`; `docs/pipeline/decision-record.md`; prerequisite `task:0044-04` `[x]` `e1127ac2f`
- **Subject:** Exact pre-mutation reach of the future `0044-18` gate: after a later exact-baseline implementation assignment and activation, every new multi-Dispatcher work round must use the complete current agent-inbox Assignment lifecycle at `main@f081d276` / server 1.16.2 as the sole start-authority signal; which units and gates that future activation would affect; and that this record authorizes no rollout mutation now.
- **Decision:** Record the complete 1.16.2 Assignment lifecycle as the future start-authority contract for **new** multi-Dispatcher rounds, and do **not** authorize rollout mutation in this commit. After a later Integrator-gated activation, a coordinator creating a new item/chain round MUST create exactly one live `offer` round per item/chain. Equal candidates share a numeric priority. Only the active **lowest-numbered** tier is delivered (`offer_inbox`). Only that tier may `offer_reply`. The first successful `accept` is the serialized atomic `AWARDED` result and the **sole** start authority. `send`, a frontier entry, free-form `OFFER` mail, another Dispatcher's activity, and `roster` counts are planning context, never an award. Fail-closed: before creating a new round, prove coordinator and candidates expose the 1.16.2 tools (`offer`, `offer_inbox`, `offer_reply`, `offer_status`, `offer_control`, `assignment_transition`); if not, refresh/restart the affected runtime and report the unavailable mechanism rather than emulating an award with `send`. Existing already-open legacy rounds finish under their pinned briefing. Independent chains MAY run as separate parallel rounds. Several Project Leads or Dispatchers are concurrent capacity; an award assigns only its item/chain; `delegate` is temporary coverage only. The future autodocs projection MUST describe the complete `assignment-state-machine@v1` at `f081d276` (states `submitted`, `offered`, `offer_paused`, `awarded`, `in_progress`, `on_hold`, `review`, `rework`, `accepted`, `cancelled`, `withdrawn`, `unfilled`, `failed`). Geordi's semantic five-step preparation at `f5b181e8f` is accepted as describing that machine. Invented gate IDs `assignment-offer:<chain>` / `assignment-start:<chain>` / `assignment-tier-advance:<chain>` / `assignment-completion:<chain>` are **not** `decision-record@v1` gate references; the conforming affected gates of this record apply instead. This record does not mutate `AGENTS.md`, `TODO.md`, role/capability authority, or any implementation surface. A fresh exact-baseline implementation assignment after this record lands is required before those surfaces may change. `Integration review: mandatory` on `0044-18` (Architect `data`, 2026-08-28) is retained. `0044-13` does not start from this record.
- **Technical justification:** Task `0044-18` names a fleet-wide assignment state machine whose defect class is duplicate execution, hidden eligible capacity, or violated prerequisite/checkpoint ordering. That is `cross-item-blast-radius`: the future gate can block or change start of every new multi-Dispatcher round and the Feature `0044` / `0044-08` integration contract. Management rejected as-written rollout, so the mandatory record is a preparation contract, not an activation. The Task text still pins `2983630f7` / v1.11.0; the award updates the external baseline to `f081d276` / 1.16.2, which includes `offer_inbox` and `assignment_transition`. `AGENTS.md` on the branch cut still describes `announce`/`inbox`/`ack`/`send` and does not yet make `offer_reply` accept the sole start authority. Broadening the gate into new start-prerequisites on every Dispatcher-facing Task would convert a use-time round-creation gate into a repository-wide start freeze. `0044-08` already lists `0044-18` as a prerequisite, so Feature integration remains a named affected gate even while rollout is unactivated. Geordi's preparation omits those Feature-level gates and uses nonconforming gate-ID syntax; this record supplies the conforming list without absorbing Geordi's tree.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Append-only `decision-record@v1` that binds the future new-round start-authority to the complete 1.16.2 Assignment lifecycle, names conforming affected units/gates, and withholds rollout mutation until a later exact-baseline implementation assignment.
    - **Disposition:** `selected`
    - **Reason:** Matches Management rejection of as-written rollout, the Architect award, jean-luc exact-scope review input, and the cross-item exception's demand for a named gate before mutation.
  - **ALT-02:** Keep the Task-text external baseline `2983630f7` / server v1.11.0 and project only `offer` / `offer_reply` / `offer_status` / `offer_control`.
    - **Disposition:** `rejected`
    - **Reason:** The award and resume update the baseline to `f081d276` / 1.16.2; the live machine includes `offer_inbox` and `assignment_transition`.
  - **ALT-03:** Permit `send`-emulated first-accept-wins `AWARD`/`WITHDRAWN` as a fallback when offer tools are missing.
    - **Disposition:** `rejected`
    - **Reason:** Task `0044-18` requires fail-closed reporting of the unavailable mechanism; silent emulation is the defect the Task exists to remove.
  - **ALT-04:** Add `0044-18` as an implementation-start prerequisite of every open Dispatcher-facing Task across Features.
    - **Disposition:** `rejected`
    - **Reason:** That would freeze unrelated Features; already-open rounds must finish under pinned briefings.
  - **ALT-05:** Authorize immediate mutation of `AGENTS.md` and related surfaces from this record, or treat Geordi's preparation commit as the decision product.
    - **Disposition:** `rejected`
    - **Reason:** Management rejected as-written rollout; absorbing an Implementer tree would collapse independence and skip the exception.
- **Consequences:**
  - **CON-01:** Until a later exact-baseline implementation assignment and activation commit, current autodocs coordination (`announce`/`inbox`/`ack`/`send`) remains operative for new rounds. This record does not activate the gate.
  - **CON-02:** This Architect commit mutates only the awarded paths `TODO-saru-0044-18-architect-20260829.md`, `docs/dossiers/dec-0044-032-priority-offer-rollout.md`, and `docs/dossiers/dec-0044-032-priority-offer-rollout-scope-review.md`. Future implementation surfaces are not authorized here and must be named by that later assignment.
  - **CON-03:** Binding future start-authority after activation: one live `offer` per item/chain; lowest-numbered active tier only; first `offer_reply` accept is atomic `AWARDED` and the sole start; `offer_status` inspects without coordination mail; `offer_control` recovers expired deadlines; `assignment_transition` carries awarded work through `in_progress` / `on_hold` / `review` / `accepted` / `rework` as `assignment-state-machine.json` at `f081d276` specifies. README wording at that pin that says "highest tier" is not the autodocs projection; lowest-numbered governs.
  - **CON-04:** Fail-closed per runtime at new-round creation. Missing 1.16.2 tools are reported, not emulated. `decision_request` remains the Management decision path and is not a substitute award.
  - **CON-05:** Non-retroactivity: already-open legacy rounds finish under their pinned briefing. New rounds after a later activation commit use the priority tools.
  - **CON-06:** Role and capability-class authority are unchanged. `delegate` does not retire a peer or transfer the process role.
  - **CON-07:** Geordi proposed gate labels `assignment-*:<chain>` are semantic aliases only. They MUST be projected in later records and tests using the conforming affected-gates list below, not as additional `decision-record@v1` gate kinds.
  - **CON-08:** The Implementer of any later rollout is distinct from `agent:saru:0044-18-scope-review:20260828T235500Z` and from the later Integrator. This record does not assign that Implementer, does not mark `0044-18` `[p]`, does not write `Acceptance: ✓`, and does not move Feature `0044` to `DONE.md`. Discovery does not take `0044` implementation.
  - **CON-09:** `0044-18` retains Architect `data`'s `Integration review: mandatory` flag. Feature integrating Task `0044-08` remains the Feature review floor and lists `0044-18` as a prerequisite. `0044-13` does not start from this record. This branch does not absorb `715cd717d` / later `0044-13` merges.
  - **CON-10:** Governance landing of this record onto `main` requires a separate privileged Integrator. This Architect worktree does not advance `refs/heads/main`.
- **Affected work units:**
  - `repository:autodocs`
  - `feature:0044`
  - `task:0044-18`
  - `task:0044-08`
  - `task:0044-04`
  - `external:agent-inbox`
  - `path:docs/dossiers/dec-0044-032-priority-offer-rollout.md`
  - `path:docs/dossiers/dec-0044-032-priority-offer-rollout-scope-review.md`
  - `path:TODO-saru-0044-18-architect-20260829.md`
- **Affected gates:**
  - `task-start:0044-18`
  - `external:new-multi-dispatcher-round`
  - `integration:0044-18`
  - `integration:0044-08`
  - `feature-closure:0044`
  - `external:agent-inbox-assignment-lifecycle-1.16.2`
- **Review participation:** `none`
- **No-review reason:** Management assigned this Architect both the `decision-record@v1` and the supporting independent scope-review as one award, with identity distinct from the Geordi Implementer and later Integrator. A second Architect instance was not assigned. The supporting review is `docs/dossiers/dec-0044-032-priority-offer-rollout-scope-review.md` by this same identity; it is not Task Acceptance and not an integration verdict.
- **Waiver:** `none`
