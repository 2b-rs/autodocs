---
schema_version: "1.0"
id: "0038-10"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-45"
  - "0038-01"
  - "0038-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1710"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0038-10:0038-01, 0038-10:0038-02, 0038-10:0037-45 Standardize immutable per-attempt results and an atomic mutable current pointer. REF: `d712bbb95a8f9bfea5b546919561bad442a45fdb`. Prior implementation REF (retained): `4231f93b24cbd9aa056305ffa5a147ac316c783c`. Binding pins: product `d712bbb95a8f9bfea5b546919561bad442a45fdb`; takeover `634e4804e91e65ecfeb865f72c0a47ab7f472c21`; confirm `fbc207b1b321a67d10f5b6ab0d421d31d13a26c7`; independent review `e93afa347c225fd023e4b1e93d8b9a7dc09b1089`. `9c3b8e412622c9402b6fa21fbf185b2066af962b` is **not** a valid handoff close. `1d800dfa1` is Bryce provenance only. `0f49010c596fda6c00bf677ef85046fbecad261a` is an inspect-runtime adopt, not retroactive authority. Claim remains on the item branch: `TODO-Gabriel-Nilsson-0038-10-repair-20260825T044000Z.md`. Current `owner_token`: `agent:gabriel-sato-20260825t071600z:0038-10-repair:20260825T071600Z`. Prior Nilsson, Bryce, and Linus tokens provenance only. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `Gabriel-Dispatcher-Kette (Bryce/Linus/Sato, Provenienz teils invalide, Produkt-REF unberührt)`). Abgenommene Baseline `d712bbb95a8f9bfea5b546919561bad442a45fdb`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). Reparatur des O_NOFOLLOW-Symlink-Fehlers: zwei deterministisch grüne Läufe (46/46, 0/0) am eigenen REF, adversariale Symlink-Escape-Prüfung bestanden, py_compile/diff-check/automation_safety sauber. Vorherige Ablehnung des alten REF 4231f93b24c in 4fddf329e bleibt unverändert als Provenienz stehen.

## Scope

- **Completion evidence (2026-08-19, retained — not deleted on repair reopen):** `4231f93b24cbd9aa056305ffa5a147ac316c783c` adds immutable no-follow per-attempt results, atomic SHA-256-bound task current pointers, strict recovery/finalization binding and locking, explicit phase/action lifecycle evidence, and 46 hermetic fixtures covering success, failure, timeout, cancellation, crash, retry, tampering, same-request rerun, and pointer boundaries. `PYTHONDONTWRITEBYTECODE=1 python3 _src/tools/test_runner_transaction.py` passed 46 tests in 291.398s; `python3 -m py_compile _src/tools/runner_transaction.py _src/tools/test_runner_transaction.py`, `git diff --check`, and `_src/tools/automation_safety.py --path _src/tools/runner_transaction.py --json` passed (safety verdict PASS; three constrained-cleanup advisories; zero unresolved critical or policy findings). Prior claim `TODO-terra-1-0038-10-20260819T000000Z-6666b30b762f.md` remains on this lineage and is not deleted.
  - **Repair reopen (2026-08-25):** Implementation ownership resumed under the new claim above. Historical `[x]` REF and completion evidence stay in the block. No acceptance, review, or checkpoint mutation this turn.
  - **Repair completion (2026-08-25):** `_open_directory_nofollow` followed only in-tree `O_NOFOLLOW` opens from `/`, so `_current_pointer_status` and `_atomic_write` failed on unresolved macOS temp paths whose prefix is the `/var` -> `/private/var` alias (`Not a directory: 'var'`). Review `4fddf329efdd53ec65d9639e7210d2585bbf37c9` measured 39/46 (5 fail, 2 error) twice at `4231f93b24cbd9aa056305ffa5a147ac316c783c`; the two older tests remain green at 0038-02. Repair follows leading OS prefix aliases whose target stays under the current physical prefix and still refuses escaping directory symlinks. `PYTHONDONTWRITEBYTECODE=1 python3 _src/tools/test_runner_transaction.py` passed 46/46 in 100.264s; `python3 -m py_compile _src/tools/runner_transaction.py` and `git diff --check` passed. No Acceptance/review/checkpoint; old claim/review history retained.
  - **Takeover (2026-08-25T04:50:00Z):** Dispatcher gabriel transferred ownership from Gabriel-Nilsson-20260825T044000Z to Gabriel-Bryce-20260825T045000Z. Nilsson token is provenance only; Bryce token is current ownership. Marker returned to `[p]` until the new owner inspects/adopts the already-committed product after this claim-follow-up commit.
  - **Recorded deviation (not retroactively authorized):** Product mutation happened before takeover. Unstaged `_src/tools/runner_transaction.py` 41+/4− SHA-256 `d018cd46881caf8fbd29cf955a9082dfea3f822ab70424ceb6bc65f4edcddfde` was later committed as `d712bbb95a8f9bfea5b546919561bad442a45fdb` by a second Nilsson-labeled workflow agent that was **not** the original claim session. Bookkeeping `9c3b8e412622c9402b6fa21fbf185b2066af962b`. New owner may inspect/adopt that committed diff only after the claim-follow-up commit. This note documents the deviation; it does not authorize it retroactively.
  - **Adopt (2026-08-25, Gabriel-Bryce-20260825T045000Z):** Independent inspect **ADOPTS** `d712bbb95`. Finding: `_open_directory_nofollow` `O_NOFOLLOW` on every component from `/` breaks unresolved macOS `/var`→`/private/var` temp paths used by `_current_pointer_status`/`_atomic_write` and the 46 fixtures, while `Transaction` already `Path.resolve()`s. Candidate follows only prefix-staying directory aliases. Independent run: **46/46 OK in 110.438s**; `py_compile` pass; `git diff --check` clean. `9c3b8e412` is not a valid close. Marker stays `[p]`. No product code in this bookkeeping commit.
  - **Takeover (2026-08-25T04:58:00Z):** Dispatcher gabriel transferred ownership from Gabriel-Bryce-20260825T045000Z to Gabriel-Linus-20260825T045800Z. Nilsson and Bryce tokens are provenance only; Linus token is current ownership. `1d800dfa1` is Bryce provenance only. Inspect-runtime violation: `0f49010c` was authored by Gabriel-Bryce-20260825T045000Z-inspect, not the session that wrote `1d800dfa1`; that adopt is not retroactive authority. Quarantine candidate remains `d712bbb95`. Marker stays `[p]`. This bookkeeping commit is claim/TODO only (no product code). Takeover SHA: `634e4804e91e65ecfeb865f72c0a47ab7f472c21`.
  - **Confirm (2026-08-25, Gabriel-Linus-20260825T045800Z):** Independent inspect **CONFIRMS** `d712bbb95`. Finding: `_open_directory_nofollow` `O_NOFOLLOW` on every component from `/` breaks unresolved macOS `/var`→`/private/var` temp paths used by `_current_pointer_status`/`_atomic_write` and the 46 fixtures, while `Transaction` already `Path.resolve()`s. Candidate follows only prefix-staying directory aliases. Independent run: **46/46 OK in 106.359s**; `py_compile` pass; `git diff --check` clean. No new defect. `9c3b8e412` is not a valid close. Marker stays `[p]`. No product code in this bookkeeping commit.
  - **Takeover (2026-08-25T07:16:00Z):** Dispatcher gabriel transferred ownership from Gabriel-Linus-20260825T045800Z to Gabriel-Sato-20260825T071600Z. Nilsson, Bryce, and Linus tokens are provenance only; Sato token is current ownership. Privilege is not merge or acceptance authority. Binding pins preserved: product `d712bbb95`; takeover `634e4804e`; confirm `fbc207b1b`; independent review `e93afa347`.
  - **Repair close (2026-08-25, Gabriel-Sato-20260825T071600Z):** Implementation terminal `[x]` REF `d712bbb95a8f9bfea5b546919561bad442a45fdb` binding the pins above. One path-limited bookkeeping commit (claim + this block). No product change. No Acceptance. No merge. No Feature close. `9c3b8e412` is not a valid close. Validation this session: `git diff --check` / `git status` only.

### Campaign D — Make artifacts and evidence compact, fresh, and recoverable

## Acceptance criteria

- **AC-001** Every attempt writes `result.json` with Task/request/base/authority, per-phase RC/status/duration, aggregate verdict, exact actions, structured findings, path counts/digests, commits, cleanup/recovery state, and evidence references before an atomic `current.json` pointer changes. A retained script or free-text `run-current.log` is never interpreted as pending/completed state
- **AC-002** partial attempts use explicit lifecycle markers

## Definition of Done

Success, failure, timeout, cancellation, crash, retry, tamper, and pointer-update fixtures are deterministic; an empty archive or overwritten current log cannot erase the last immutable attempt result.
