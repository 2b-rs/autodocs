---
schema_version: "1.0"
id: "0038-27"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-14"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1855"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0038-27:0038-14 Reconcile the automation-safety dispositions orphaned by `0038-14`'s closure and finish their underlying classification/retirement work. REF: `2d6493caf`.

## Scope

- **Context:** `0038-14`'s classification scope covered 27 of 107 tracked chore tools with real fault-injection evidence; `_src/tools/bootstrap_ssh_known_hosts.sh`, the six `_src/i18n/work/**` one-off write scripts, and `_src/tools/sync_to_devel.sh` all carried `automation_safety_policy.json` dispositions pinned to `0038-14` and are re-pointed here by the repair note above. `sync_to_devel.sh` differs from the other eight: `0038-14`'s own fault-injection evidence already proved lock exclusivity, all three pre-rsync guards, retry-is-a-no-op, and delete-propagation, so **no code change is required** for it — this Task's only job for that one entry is to give it its final, correctly owned disposition.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect `Seven-B'Ellana`, 2026-08-20):** none of these nine findings touch credentials, a push, or a force-push — `bootstrap_ssh_known_hosts.sh` only ever writes public host-key verification data and already fingerprint-checks and removes on mismatch; the i18n writers are local one-off translation scripts; `sync_to_devel.sh` needs no code change at all. Risk is bounded and objectively checkable by the automation-safety scan named in the Definition of Done; re-examined whenever Feature `0038` next reaches its integrating task. **Trigger correction (2026-08-21, architect `Seven-B'Ellana`):** Feature `0038` has no integrating task and, under the partial-integration decision of this date, will not acquire one; that made this re-examination trigger unreachable and turned a bounded risk acceptance into an unfalsifiable one. The trigger is redirected to the closure of Task `0038-28`, a real open Task on the same file surface. Original wording retained above, append-only.
  - **Implementation completion (2026-08-20, `agent:seven-piri:0038-27:20260820T000000Z`, dispatched by privileged agent Seven):** `_src/tools/bootstrap_ssh_known_hosts.sh` — replaced the AND-list `mkdir && chmod` with two explicit `cmd || exit 1` checked steps, and hardened the host-key append to verify the fingerprint *before* any write instead of append-then-rollback (both findings now gone at the source; both disposition entries removed). The six one-off i18n write scripts — confirmed via `git grep` that nothing else references them, confirmed genuinely one-off (hard-coded foreign absolute paths, fixed historical translation-batch content), retired by deletion per `0038-14`'s own Definition of Done; their disposition entries removed, and the now-stale entries for these six paths were also reconciled out of `0038-14`'s own generated `_src/tools/chore_tool_inventory_data.json` so `_src/tests/test_chore_tool_inventory.py` keeps passing. `_src/tools/sync_to_devel.sh` — no code change: re-verified byte-identical to `0038-14`'s fault-injection proof commit `92ab55f49e19025b543fedce8627c9f7fac64815` and that the finding's `evidence_sha256` still matches; disposition `kind` changed to `narrow-suppression` and `owner_task`/`expires_after_task` re-pointed from `0038-27` to `0038-16` — determinable without a human decision because the disposition schema requires a live owner Task and `0038-16`'s own Definition of Done already gates on "zero undispositioned critical chore findings remain," making it the correct durable custodian rather than re-orphaning this entry the instant `0038-27` closes (the identical defect class this Task exists to fix). **TK-2 note:** this re-point has reach beyond `0038-27`'s own work unit; no second instance was available to co-decide, so it is flagged for confirmation when `0038-16` or Feature `0038`'s integrating task is worked. Validation: full-repository `python3 _src/tools/automation_safety.py --json` shows none of these nine dispositions in `unresolved_critical` or `policy_errors` (remaining 13 unresolved-critical / 4 stale-policy findings are pre-existing and out of scope — `run-loop.sh` owned by `0040-10`, `provision_tmp_worktree.sh` owned by `0038-22`, `provision_worker_clone.sh` unowned — matching `0038-14-repair`'s own prediction); `python3 -m unittest _src.tests.test_chore_tool_inventory` 26/26 pass; `python3 -m unittest _src.tests.test_automation_safety` 120/121 pass (the one failure, on `_src/tools/runner_transaction.py`, confirmed pre-existing via `git stash` and out of this Task's write scope). Evidence and claim: `TODO-seven-piri-0038-27-20260820T000000Z.md`, branch `0038-27` (based off `0038-14-repair` at `1fb185a36`), left at rest, not merged into `0038-14-repair`/`0038`/`main` by this session. No acceptance credit claimed.

## Acceptance criteria

- **AC-001** For `_src/tools/bootstrap_ssh_known_hosts.sh` (`AUTO001` line 10, `AUTO008` line 22): replace the AND-list trust-store setup (`mkdir -p ... && chmod 700 ...`) with explicit checked steps
- **AC-002** confirm and record that the existing verify-then-possibly-remove host-key append already satisfies the fail-closed intent, or harden it if it does not. For the six one-off i18n write scripts (`_src/i18n/work/hi/batch_13.write.sh`, `batch_14.write.sh`, `batch_15.write.sh`, `_src/i18n/work/zh/write_batch_01_heredocs.sh`, `write_batch_02_heredocs.sh`, `write_batch_03_heredocs.sh`): retire each (delete, since `0038-14`'s own Definition of Done calls these "one-off scripts") or, if a script is still needed, give it tests/docs and an explicit retention reason per that same Definition of Done. For `_src/tools/sync_to_devel.sh` (`AUTO001` line 16): re-verify `0038-14`'s fault-injection proof still holds against current source and record a final disposition
- **AC-003** no code change is expected

## Definition of Done

Committed with real `REF`; `python3 _src/tools/automation_safety.py --json` reports zero unresolved critical findings and zero policy errors for these nine dispositions; each of the nine has an explicit final resolution (retired, code-fixed, or re-verified-and-dispositioned) recorded in this Task's completion evidence.
