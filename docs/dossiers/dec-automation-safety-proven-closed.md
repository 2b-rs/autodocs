# Decision record for proven-closed disposition kind

### `DEC-AUTOMATION-SAFETY-PROVEN-CLOSED` — Authorize a durable `proven-closed` disposition kind for terminal tasks

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-27T21:08:23Z`
- **Deciding identity:** `agent:jadzia:automation-safety-proven-closed:20260827`
- **Role:** `Architekt`
- **Authority reference:** Management decision `agent-inbox:1787854883138-45083376` (item 4 = "A+B"); OFFER/AWARD `agent-inbox:1787864903627-53ee454d`
- **Subject:** Introduction of a durable `proven-closed` disposition kind to `_src/tools/automation_safety_policy.json` to safely handle validated findings on terminal owner tasks (e.g., the 33 `owner_task: 0038-16` findings).
- **Decision:** Authorize the addition of a new disposition kind `proven-closed` to the automation safety schema. This disposition kind explicitly marks findings on terminal tasks as validated false positives or explicitly acceptable because the task is confirmed closed and the state is proven. It will allow `automation_safety.py` to accept terminal `owner_task` values when the disposition is `proven-closed` instead of unconditionally rejecting them at line 2815. This DEC only authorizes the schema change and the disposition class; it does not implement the change or modify the 33 existing `owner_task: 0038-16` entries.
- **Technical justification:** The automation safety checker (`automation_safety.py:2815`) unconditionally rejects any terminal `owner_task`, but there are 33 confirmed terminal `[w]` owner tasks in `DONE.md:793` that have legitimate dispositions. This is the 3rd recurrence of this class of false positives. Management decision `1787854883138-45083376` (item 4 = "A+B") instructed to fix the 33 entries and implement `proven-closed`. A distinct `proven-closed` kind cleanly separates open operational dispositions from durably closed, validated historical findings without violating the safety invariant that active tasks must not use terminal tasks as owners.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Implement a new `proven-closed` disposition kind to handle terminal tasks.
    - **Disposition:** `selected`
    - **Reason:** Cleanly differentiates between active dispositions and historically validated findings, satisfying the management decision and resolving the false positive recurrence.
  - **ALT-02:** Remove the terminal `owner_task` check completely.
    - **Disposition:** `rejected`
    - **Reason:** This would weaken the safety invariant and allow active operations to hide behind closed tasks improperly.
  - **ALT-03:** Rewrite history to change the `owner_task` of the 33 findings to an active task.
    - **Disposition:** `rejected`
    - **Reason:** Falsifies provenance and operational history.
- **Consequences:**
  - **CON-01:** The schema for automation safety dispositions must be updated to accept `proven-closed`.
  - **CON-02:** The automation safety checker must be modified to allow terminal `owner_task` values ONLY when the disposition kind is `proven-closed`.
  - **CON-03:** The 33 existing `owner_task: 0038-16` findings can be migrated to this new disposition under separate implementation.
  - **CON-04:** This DEC record only authorizes the governance change; product implementation must be performed separately after this DEC is merged.
- **Affected work units:**
  - `task:0038-16`
  - `task:0039-01`
  - `repository:autodocs`
- **Affected gates:**
  - `validation:automation-safety`
- **Review participation:** `none`
- **No-review reason:** Awaiting independent review by Saru as arranged by Project Lead Kathryn.
- **Waiver:** `none`
