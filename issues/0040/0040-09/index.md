---
schema_version: "1.0"
id: "0040-09"
level: "task"
parent: "0040"
state: "open"
visibility: "internal"
prerequisites:
  - "0040-01"
  - "0040-02"
  - "0040-03"
  - "0040-04"
  - "0040-05"
  - "0040-06"
  - "0040-07"
  - "0040-08"
  - "0040-10"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:579"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0040-09:0040-10, 0040-09:0040-01, 0040-09:0040-02, 0040-09:0040-03, 0040-09:0040-04, 0040-09:0040-05, 0040-09:0040-06, 0040-09:0040-07, 0040-09:0040-08 Integrate the whole Feature, review it as a coherent process change, and record the integration verdict. REF: `201017db524a1740919d02bbfcde217d46ee589c`.

## Scope

- **Claim (2026-08-18):** Aggregate integration via `TODO-zed-0040-09-20260818T180401Z-760531d011eb.md`; owner_token `agent:zed:0040-09:20260818T180401Z-760531d011eb`; branch `0040-09`; isolated worktree `.worktrees/0040-09`. User-involved aggregate review is required before acceptance or Feature closure.
  - **Implementation completion (2026-08-18):** The integration package dispositions all 20 stable requirements, reconciles the stale `0040-01` contract, retains both historical authority defects, maps `DEC-0040-10-001` truthfully as legacy/incomplete, and records the `0040-05` non-material drift analysis. An initial unrecorded attempt to change foreign contracts was caught by independent review and rolled back; current-user decision `DEC-0040-006` and a distinct non-privileged Architect review then preceded the final partitioned bindings to `0037-17.02`, `0037-17.03`, `0037-10.04`, and still-reserved `0039-01`. Final independent aggregate review passed with no Feature-local blocker/high/medium finding. Requirement/decision/contract checks, focused link test, REF ancestry, editor diagnostics, `git diff --check`, and the unchanged-byte automation-safety baseline passed. The global doctor remains non-passing with 383 findings, including only the four expected predecessor claims in Feature scope; `_src/validate.py` remains non-passing on 12 unrelated missing retained-log links. No global pass is claimed. Implementation closes at `[x]`; aggregate Acceptance, claim reconciliation, upward integration, and Feature closure await the current user's pinned-baseline review and the unresolved `0040:0039-01` management choice.
  - **Independent review (2026-08-19):** `0040-05` retains its current user-authorized acceptance, including exact matching non-`TODO.md` manifest bytes and the documented non-material `TODO.md` drift. Independent review of the pinned aggregate candidate is `inconclusive`: `DEC-0040-005` records an agent as `Management`, while the normative role model reserves Management to the current user or a registered authority. The earlier `0040-05` acceptance does not silently correct that historical authority record. Evidence: `docs/pipeline/approvals/0040-09-integration-review-20260819.md` (review REF `9008da6ee9f81e12bb305d04b1d40f5db704f43d`).
  - **Integration verdict:** [u] — pending user approval
    - **Verdict by:** `agent:worf-integrator-kehleyr:0040-09:20260819T000300Z-c63f10`
    - **Authority reference:** current-user assignment of Task `0040-09` on 2026-08-19
    - **Recorded at:** `2026-08-19T00:03:00Z`
    - **Rejected/blocked tasks:** `0040-09`
    - **Reason:** Current user or registered Management authority must append an explicit ratification or rejection of the substantive scope decision `DEC-0040-005`, preserving its false historical agent-as-Management entry. This review cannot invent that decision. `DEC-0040-001` lacks a duration but was not used for self-acceptance; no duration is inferred. Feature closure remains independently blocked by `0040:0039-01` (`[u]`).
    - **Integration branch:** `0040-09` review-evidence tip `9008da6ee9f81e12bb305d04b1d40f5db704f43d`
  - **Integration verdict:** [u] — re-review remains pending Management authority
    - **Verdict by:** `agent:worf-kurn-20260819t000700z:0040-09:20260819T000700Z-7ac7f6`
    - **Authority reference:** exact current-user assignment for Feature `0040`, `0040-05`, and `0040-09`, retained verbatim in `TODO-worf-kurn-0040-09-20260819T000700Z-7ac7f6.md`
    - **Recorded at:** `2026-08-19T22:04:06Z`
    - **Rejected/blocked tasks:** `0040-09`
    - **Reason:** The former `0040:0039-01` closure prerequisite is now satisfied by the accepted `0039-01` integration at `0039` tip `cdeb9a1324370ed1de7a22af527600d1e78e522b`. Acceptance remains prohibited because `DEC-0040-005` still records an agent as `Management` without an append-only ratification or rejection by the current user/registered Management authority, and `DEC-0040-001` still lacks the finite waiver duration required by current authority. Fresh review evidence also records an unrelated current automation-safety unit-test failure and a bounded direct-scan timeout; no fresh full safety pass is claimed. This integrator cannot invent any of those authority decisions.
    - **Integration branch:** `0040-integration-Kurn-20260819T000700Z` review-evidence tip `1e4aae66db67cff574a6ec3dafa2614ac7d1c2c8`
  - **Integration verdict resolution (2026-08-20):** Both `[u]` verdicts above are resolved and retained unchanged as history. Their blocking reasons no longer hold: Management ratified `DEC-0040-005` in `DEC-0040-007`, supplied the `DEC-0040-001` waiver endpoint in `DEC-0040-008` (verbatim authority: `docs/dossiers/0040-management-closure-provenance.md`), and the `0040:0039-01` closure gate is satisfied by the accepted `0039-01` integration. The automation-safety limitation recorded by the second verdict is resolved by a fresh full live scan on the exact new baseline: 105 files, 71 findings, 35 disposed critical, zero unresolved critical, zero policy errors. Resolved by `agent:picard:0040-closure:20260820T080227Z` under the current user's 2026-08-20 assignment; no agent cleared its own verdict.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `agent:picard:0040-closure:20260820T080227Z`
    - **Authority reference:** `current-user assignment, 2026-08-20, exact aggregate integration review of Feature 0040 / checkpoint 0040-09; TODO-picard-0040-09-review-20260820T080227Z.md`
    - **Accepted at:** `2026-08-20T08:02:27Z`
    - **Contract SHA-256:** `aa7133d14d0c39a4198951cbdf2f85d4c4dd583dee2b5d6fc06cc2dc1642bd85`
    - **Work-product manifest SHA-256:** `258b6c3e8cba2143287dca795ad5d91fd03a15bbe2b05a02f2c422c73ac0df02`
    - **Prerequisite-acceptance SHA-256:** `1d4567e3eb4e1785adeb105cf3e929c75e4bac48e6e2997fb55076b704cc232d`
    - **Review REF:** `3726a11111dc7340ce9ac008c6209b2ed6dfb773`
    - **Open minor finding:** `F-0040-09-004` — pre-existing automation-safety unit-test failure on `_src/tools/runner_transaction.py`, proven unattributable to this candidate by merge-base reproduction; owner Feature `0038`. Deferral does not contradict any `0040` criterion.
  - **Integration review: mandatory.** **Rationale (architect):** this is the Feature's mandatory integrating task and its review floor, as required by the `TODO.md` header. It is the only point at which the role model, the briefings, the decision record, the traceability tool, the amended breakdown process, the standard references and the effectiveness proof are examined as **one** process rather than eight documents — and that is exactly the level at which the `T1` defect was invisible.
  - **Note on independence:** under `DEC-0040-001` the Feature owner may perform this integration. Where the integrator would be reviewing its own decisive authorship, the review must say so plainly and name what a later independent reviewer should re-examine first.

### Corrective target-policy re-integration (2026-08-20)

The original closure, acceptance, rejected main-integration review, and all
Management decisions above remain immutable historical evidence. The candidate
was then reopened solely to reconcile it with target `main` policy. The completed
corrective Task `0040-11` has substantive REF
`74dbdac90b421128352bfc8afc7bb4b580a4c054`; it merged target `main`
`c0a274e66fd36516e748a0d309bcd35fa5b7e561` at
`c560fbc2fdc5bf39811a545894560f648364f49a` and corrected the current normative
role model to English and the three capability classes.

A new independent privileged review accepted exact candidate
`8f6d42b48fa24fbd07d1e165131cdf663cfdc9bb`: review evidence commit
`eca92b81d4ee98bb2e2225a7816bcbe9f4c1141a`,
[`0040-feature-main-integration-review-worf-martok-20260820T121500Z.md`](docs/pipeline/approvals/0040-feature-main-integration-review-worf-martok-20260820T121500Z.md).
It re-verified target-policy provenance, English/current three-class authority,
checkpoint history, focused validation, and the actual `0040:0039-01` closure
prerequisite. The task's stale `[u]` projection in the legacy `TODO.md` was not
used as decisive: its current accepted record is reachable on canonical Feature
branch `0039` at `cdeb9a1324370ed1de7a22af527600d1e78e522b`. As a Feature closure
gate rather than a merge edge, it need not be an ancestor of `0040` or `main`.

The reviewed Feature descendant was non-force merged onto the pinned target at
`cf91c8698aa23b80e80f98051b3ee667b8b84c20`. This corrective closure creates no
new `Acceptance: ✓` record and does not rewrite historical acceptance; the fresh
review satisfies the independent-review condition of `0040-11`. The carried
terminal repair and review claims were reconciled only after their information was
captured in the corrective implementation and review records:

| Removed claim | SHA-256 | Retained authority/evidence |
| --- | --- | --- |
| `TODO-worf-k-ehleyr-0040-repair-20260820T001000Z-5c2bc79f.md` | `b86ccfb1b00b9c54b4d7e69e79160c6fead8bc8eacd24e9cce6ce6e9b864655f` | `0040-11` history and `docs/dossiers/0040-main-integration-repair-20260820T001000Z.md` |
| `TODO-worf-integrator-martok-0040-integration-20260820T121500Z.md` | `0b84cb0428b415c8e67eaebf584c9109cc043c0adfa7a1b0227d8ece24252359` | accepted review record above |

No Feature `0019` work, external publication, remote, SSH configuration, or
`run.sh` action was performed by this re-integration.

## Acceptance criteria

- **AC-001** The integrator merges the required work, verifies that no authority document contradicts another, that every requirement ID from the baseline has a disposition (implemented, deliberately deferred with reason, or rejected with reason), and that the bounded authority waiver `DEC-0040-001` and its compensating control are visible and were honoured — specifically, that every acceptance this Feature's owner granted to its own work is marked as such and names `DEC-0040-001`. It confirms that no Task introduced a new blocking gate without a recorded `RQ-DEC-05` decision. It records findings and `Acceptance: ✓` at this checkpoint and at `0040-05`

## Definition of Done

Committed with real `REF`; both mandatory checkpoints carry a current passing review or an explicit `[u]` integration verdict; the predecessor claim files are reconciled and removed; the Feature moves to `DONE.md` only when `0040:0039-01` is also satisfied.
