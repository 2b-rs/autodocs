# Architect Scope Review: 0037-30 Legacy-Frozen Cross-Item Write Gate (`DEC-0037-030`)

- **Review Format:** Architect Scope Review (`docs/pipeline/decision-record.md`, `docs/pipeline/core-rules.md`)
- **Reviewer:** `worf` (instantiated by Management as privileged Architect; distinct from implementer `data` and integrator `geordi`)
- **Review Date:** 2026-09-04T01:36:00+02:00
- **Governing Management Decision:** `decision-0037-30-legacy-frozen-write-gate-20260903` (Option: `enforce_scoped_freeze`)
- **Counterexample Ref:** `ce31c50f14cce6bf643a2bfbbbfa600c98fb2312` on `d88f73e8b`
- **Current Baseline:** `main@780b54e4f3be37985d392e7785f69616b1a16842`
- **Scope Verdict:** **SUPPORTING** (Narrow fail-closed gate scope bounded to legacy-frozen ordinary backlog mutations while allowing cutover transaction evidence)

---

## 1. Context and Problem Statement
During independent integration review R2 for Task `0037-30` (Ref: `ce31c50f14`), an adversarial probe demonstrated that under `authority_epoch: "legacy-frozen"`, `_src/tools/issue_integration_policy.py` exited `0` (`passed`) when new root legacy claims (`TODO-*.md`) or backlog mutations were introduced. The policy gate previously restricted prohibited claim and generated-view checks strictly to `authority_profile == "issue-store"`.

Management decision `decision-0037-30-legacy-frozen-write-gate-20260903` resolved this by adopting option `enforce_scoped_freeze`: enforce a strict fail-closed integration boundary against ordinary legacy backlog mutations while `write_phase == "frozen"`, without deadlocking legitimate Feature 0037 cutover transaction evidence or metadata updates.

---

## 2. Exact Bounded Gate Scope & Path Dissection

### A. Denied Path and Operation Classes under `legacy-frozen` (`write_phase: "frozen"`)
1. **Ordinary Backlog Claim Files**:
   - Any new or modified root legacy claim matching `^TODO-[A-Za-z0-9._-]+\.md$` (outside `provenance/` and outside authorized cutover task claims for `0037-30`..`0037-40`).
2. **Direct Edits to Backlog Lists**:
   - Any modification to `TODO.md` or `DONE.md` by ordinary Feature tasks.
3. **Uncoordinated Role Signatures & Stale Profile Claims**:
   - Any change attempting to write to legacy tasks without an active transaction ID or cutover assignment.

### B. Explicitly Allowed Path and Operation Classes
1. **Cutover Evidence & Carrying Dossiers**:
   - `docs/dossiers/0037-30-*.md` through `docs/dossiers/0037-40-*.md` (reconciliation, freeze evidence, migration reports, audit dossiers).
2. **Cutover Task Claims & Completion Records**:
   - Task claims bound to authorized cutover tasks: `TODO-*-0037-3[0-9]-*.md`, `DONE-*-0037-3[0-9]-*.md`, `TODO-*-0037-40-*.md`, `DONE-*-0037-40-*.md`.
3. **Canonical Selector & Policy Metadata**:
   - Updates to `agent-workflow.json`, `.github/workflows/issue-policy.yml`, and `_src/tools/issue_integration_policy.py` necessary to transition through cutover phases.
4. **Issue Migration Output / Transaction Ledger**:
   - `_src/output/issue-migration/*`, `issues/*` (candidate generation and validation artifacts).

---

## 3. Affected Work Units & Gates
- **Affected Work Units**:
  - `task:0037-30` (Legacy reconcile & quiescence barrier)
  - `task:0037-31` (Migration candidate generation)
  - `task:0037-32` (Independent pre-cutover audit)
  - `task:0037-33` (Release decision)
  - `task:0037-34` (Authority switch preparation and execution)
  - `task:0037-40` (Cutover reference & activation commits)
- **Affected Gates**:
  - `validation:_src/tools/issue_integration_policy.py`
  - `integration:0037-30`
  - `integration:0037-31`

---

## 4. Stability, Diagnostics, and Falsification Probes

- **Diagnostic Codes**:
  - `POLICY-FROZEN-LEGACY-CLAIM-PROHIBITED`: Rejection when an ordinary `TODO-*.md` claim is introduced under `write_phase: "frozen"`.
  - `POLICY-FROZEN-BACKLOG-EDIT-PROHIBITED`: Rejection when direct edits to `TODO.md` / `DONE.md` occur under `write_phase: "frozen"`.

- **Adversarial Red/Green Probe Requirements**:
  * **Red on `d88f73e8b`**: Adding `TODO-stale-client-after-freeze.md` against `d88f73e8b` previously exited `0` (passed).
  * **Green on scoped candidate**: Adding `TODO-stale-client-after-freeze.md` under `legacy-frozen` must exit `1` with `POLICY-FROZEN-LEGACY-CLAIM-PROHIBITED`.
  * **Happy Path on scoped candidate**: Permitted cutover evidence `docs/dossiers/0037-30-*.md` and `DONE-data-0037-30-*.md` must exit `0` (passed).

---

## 5. Architectural Non-Deadlock & Continuity Proof
- **No Split-Brain Writes**: Prohibiting ordinary `TODO-*.md` claims in `legacy-frozen` prevents pre-cutover workers from taking new legacy work or mutating backlog state while migration candidate generation runs.
- **No Evidence Deadlock**: By explicitly allowing `docs/dossiers/0037-*` and cutover task claims `TODO-*-0037-*` / `DONE-*-0037-*`, integrators and transaction operators (`0037-31`..`0037-40`) retain unblocked ability to record signed review dossiers, integration receipts, and transition artifacts.

---

## 6. Formal Decision Record Attachment

### `DEC-0037-030` — Legacy-Frozen Cross-Item Integration Write Gate

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-09-04T01:36:00+02:00`
- **Deciding identity:** `agent:worf:0037-30:1788478459781-5d0f3d7a`
- **Role:** `Architekt`
- **Authority reference:** `decision-0037-30-legacy-frozen-write-gate-20260903`
- **Subject:** Enforce fail-closed integration gate against ordinary legacy backlog and claim mutations under `write_phase == "frozen"`.
- **Decision:** Adopt option `enforce_scoped_freeze`. Scope `_src/tools/issue_integration_policy.py` to reject ordinary legacy claims and backlog mutations under `legacy-frozen` while allowing Feature 0037 cutover evidence, claims, and metadata.
- **Technical justification:** Eliminates the fail-open gap identified in counterexample `ce31c50f14` and secures the pre-cutover quiescence barrier without deadlocking cutover transaction execution.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Full freeze rejecting all repository writes including dossiers and cutover claims.
    - **Disposition:** `rejected`
    - **Reason:** Deadlocks cutover progression because `0037-31`..`0037-40` require writing migration reports and integration receipts.
  - **ALT-02:** Unscoped freeze allowing all writes until `issue-store` cutover.
    - **Disposition:** `rejected`
    - **Reason:** Re-creates the `ce31c50f14` defect where ordinary workers could modify legacy backlog after freeze.
  - **ALT-03:** Scoped freeze rejecting ordinary legacy mutations while permitting cutover evidence and transaction claims.
    - **Disposition:** `selected`
    - **Reason:** Completely closes the freeze bypass while allowing cutover completion.
- **Consequences:**
  - **CON-01:** Ordinary agent pickup and legacy claims are blocked at the integration gate under `legacy-frozen`.
  - **CON-02:** Cutover transaction evidence and dossiers pass cleanly.
- **Affected work units:**
  - `task:0037-30`
  - `task:0037-31`
  - `task:0037-32`
  - `task:0037-34`
  - `task:0037-40`
- **Affected gates:**
  - `validation:_src/tools/issue_integration_policy.py`
  - `integration:0037-30`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `authority:management:supervisor`
    - **Role:** `Management`
    - **Participation:** `consulted`
    - **Position:** `supports`
    - **Note:** Mandated under decision-0037-30-legacy-frozen-write-gate-20260903.
- **Waiver:** `none`
