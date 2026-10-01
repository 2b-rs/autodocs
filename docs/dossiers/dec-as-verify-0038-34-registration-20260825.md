# Managemententscheidung — tote Worktree-Registrierung entfernen; Hygiene-Gate bleibt

**Autorität:** Management (aktueller User), Beschluss in der Michael-Cursor-Session
2026-08-25 15:33 +02. Wortlaut:

> Ja, toten Eintrag entfernen. Das Vorhandensein sekundärer Worktrees darf
> generell einen checkout ins Repository vom kanonischen Pfad aus blockieren.

**Protokollant:** `agent:michael:roster-discovery-cursor:20260825T140300Z`
(Project Lead Discovery). Protokolliert, trifft die Entscheidung nicht
(`DEC-ROLE-001`). Mailbox is not authority.

**Identifier:** `DEC-0044-023`, geprüft gegen `main` `28d7a00918498685b1fc13b711840df415142ecf`
und Branch `roster-discovery-cursor-20260825` (höchste belegte Nummer `DEC-0044-022`).

---

### `DEC-0044-023` — Remove only the dead `as-verify-0038-34` registration; keep scanning all worktrees

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-25T15:33:00+02:00`
- **Deciding identity:** `authority:current-user:autodocs:2026-08-25`
- **Role:** `Management`
- **Authority reference:** `path:docs/dossiers/entscheidungsvorlage-as-verify-0038-34-20260825.md` (live Management instruction in the Michael Cursor session, 2026-08-25 15:33 +02; no agent-inbox ID)
- **Subject:** Recovery of the missing worktree registration `/private/tmp/as-verify-0038-34`, and whether secondary worktrees may continue to block operations from the canonical repository checkout
- **Decision:** Remove only that dead registration after a `preserved/*` snapshot of its leftover index. Do not prune other worktrees. The existing hygiene rule stays: the presence of secondary worktrees may generally block a checkout or merge that uses the canonical path; `WORKTREE_UNAVAILABLE` and the all-worktree scan remain in force. This is not a waiver of `DEC-0044-010` / `DEC-0044-015` / `DEC-0044-021`.
- **Technical justification:** Git listed `/private/tmp/as-verify-0038-34` as prunable because the directory is gone. That stale pointer made `check_integration_hygiene.py` fail closed (`WORKTREE_UNAVAILABLE`) and stopped the Integrator from merging `DEC-0044-022`. The commit at the missing worktree's HEAD (`9bcf87edb`) is already on branch `0038-34`. Management chose Option A of the 2026-08-25 template and separately stated that secondary worktrees may still block the canonical checkout, so the checker is not narrowed.
- **Triggers:**
  - `cross-item-blast-radius`
  - `irreversible-or-external-effect`
- **Considered alternatives:**
  - **ALT-01:** Snapshot the leftover index as `preserved/as-verify-0038-34-index-20260825`, then `git worktree remove` only `/private/tmp/as-verify-0038-34`; keep the all-worktree hygiene scan.
    - **Disposition:** `selected`
    - **Reason:** Matches the Management instruction; unblocks Integrator merge without weakening the gate or deleting other worktrees.
  - **ALT-02:** Leave the dead registration in place.
    - **Disposition:** `rejected`
    - **Reason:** Management ordered the dead entry removed.
  - **ALT-03:** Recreate the missing directory so the registration looks live.
    - **Disposition:** `rejected`
    - **Reason:** Would likely convert `WORKTREE_UNAVAILABLE` into `INDEX_NOT_HEAD` without recovering a real checkout.
  - **ALT-04:** Stop letting secondary worktrees block the canonical checkout (narrow or drop `WORKTREE_UNAVAILABLE` / the all-worktree scan).
    - **Disposition:** `rejected`
    - **Reason:** Management stated the opposite: secondary worktrees may generally block that checkout. Changing the checker would be a separate gate-scope mutation and is not authorized here.
- **Consequences:**
  - **CON-01:** After snapshot, only the named registration is removed. Other `.worktrees/` and `/tmp` worktrees stay.
  - **CON-02:** Integrator `paul` re-runs hygiene on `roster-discovery-cursor-20260825` and, if it passes, merges to `main`. Project Lead does not advance `main`.
  - **CON-03:** A later missing or dirty secondary worktree can again block canonical-path merges. That is intended.
  - **CON-04:** The preserved tag is the recovery path for the stale index; do not prune or delete that tag without a named user authorization.
- **Affected work units:**
  - `path:.git/worktrees/as-verify-0038-34`
  - `path:docs/pipeline/branch-workflow.md`
  - `repository:autodocs`
- **Affected gates:**
  - `validation:_src/tools/check_integration_hygiene.py`
  - `integration:repository-main`
- **Review participation:** `none`
- **No-review reason:** This is authorized recovery of one already-missing registration plus written retention of the existing hygiene scan. It does not implement, widen, narrow, or rewrite the checker's declared behavior. Option ALT-04 (changing that behavior) is explicitly rejected.
- **Waiver:** `none`
