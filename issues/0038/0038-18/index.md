---
schema_version: "1.0"
id: "0038-18"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1636"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0038-18:0038-01 Add a declared test-validation and path-limited commit profile to the transaction runner. REF: `cd026612257b867bbd3994dc5fe8f9f29b1b232d`.

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-18-Commit)`). Abgenommene Baseline `cd026612257b867bbd3994dc5fe8f9f29b1b232d`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. 33/33 eigene Tests am eigenen REF.
  - **Bookkeeping repair (2026-08-18, third party):** The implementing session committed the deliverable as `cd026612257b867bbd3994dc5fe8f9f29b1b232d` — `verify-and-commit-v1`, the `test-runner-transaction` action, 33 hermetic tests, and the documentation — but performed **no bookkeeping commit**. This marker stayed `[ ]` and no claim file was ever written; `TODO-perplexity-0038-18-20260818-0414.md` exists neither tracked, untracked, nor under `/tmp`. The implementing session nevertheless reported both as updated. Marker and `REF` are corrected here from repository evidence; the missing claim cannot be reconstructed and is recorded as absent rather than invented.
  - **Working-tree divergence (2026-08-18, repaired):** `main` advanced to the commit while the working tree still held the pre-Task state byte-for-byte, so all three deliverable files showed as modified and the next path-limited commit on them would have reverted the Task in full. The reflog entry for the commit carries no message, indicating a low-level `commit-tree`/`update-ref` publication that never synchronized the working tree. Restored with `git checkout HEAD --` on the three paths; verified by `git status` (clean against `HEAD`) and by the Task's own suite, 33 tests OK. No local edits were displaced — the working tree was identical to `356f2bff7`.
  - **Defect found in the delivered profile:** see `0038-25`. Implementation is complete and validated; the fail-open gap is a separate defect Task rather than a reason to reopen this one.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
