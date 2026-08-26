# Recovery Claim 0037-10.05

- owner_token: agent:william-rowan-20260826t064300z:0037-10.05:20260826T064300Z
- capability_class: unprivileged
- execution_authority: unprivileged Programmer/Implementer, Team Enterprise, dispatched by William T. Riker under Jean-Luc's collision-free dirty-state handoff order
- item: 0037-10.05
- branch: 0037-10.05-recovery-20260826T064200Z
- worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0037-10.05-recovery-20260826T064200Z
- base: ff244c9816e80e5ad308522c1e470e5900804307 (conforming preserved snapshot of Corin's exact three-path WIP; original product base `6e58f95f6d66eadbf02fb23726401ac81554b9af`)
- preserve_ref: preserved/0037-10.05-corin-wip-20260826 -> ff244c9816e80e5ad308522c1e470e5900804307
- inherited_frozen_paths: `TODO-William-Corin-0037-10.05-20260826T035200Z.md` sha256 `f58b20fceaefdc8dfb7e70e85d0f6813df118fc25906b175e50ed92f30380421`; `_src/tools/issuectl.py` sha256 `e722baf2ce0ac46ffe1ef4fad5d35f8787ce2afdaeccee9ab1ce0fcd77ca42d1`; `_src/tests/test_issuectl_closure.py` sha256 `e3bed178595f5264c46b41dd96c74dd80f799d2847dac24e25811f35cd0832b6`
- merged_prereq_tips: prerequisite closure was already present in Corin's pinned base; recovery inherits that committed ancestry and exact WIP without a new prerequisite merge
- startup_review: Corin's original worktree was verified to contain exactly the dispatched three-path dirty state at HEAD `6e58f95f6`; it remains frozen and untouched; recovery branch/worktree names were collision-free; exact 0037-10.05 contract remains `[p]`
- write_scope: `_src/tools/issuectl.py`; `_src/tests/test_issuectl.py`; focused `_src/tests/test_issuectl_*`; Corin and Rowan claim history as additive handoff/progress; exact 0037-10.05 block/bookkeeping in `TODO.md` after a real product REF
- external_resources: none
- assumptions: the preserved bytes are recoverable through the permanent tag; Corin is historical and not live; Rowan is the sole replacement owner; lifecycle and authority semantics remain those of the pinned contract
- prohibitions: no mutation/reset/clean/delete/overwrite/commit in Corin's original worktree; no Acceptance; no checkpoint; no parent 0037-10 closure; no Feature/main/DONE; no 0037-38; no root-checkout mutation; no push; no overlapping owner; no destruction or silent appropriation; no forced premature product commit; no amend

## Progress

- 2026-08-26T06:43:00Z recovery accepted after conforming preservation; replacement claim opened. First post-claim action is the required focused Julian-venv closure test.
- 2026-08-26T07:12:00Z governance-free reconstruction: after the permanent preservation row became independently reachable on `main`, the live recovery line moved append-only to branch `0037-10.05-recovery-product-20260826T064300Z` at clean product base `6e58f95f6d66eadbf02fb23726401ac81554b9af`. Handoff commit `12dec558694ea9ebdd9362fb21eb638052ac9d01` contains only TODO/claim state. Exact preserved `_src/tools/issuectl.py` and `_src/tests/test_issuectl_closure.py` bytes were then restored uncommitted; no `docs/pipeline/branch-workflow.md` delta is carried. The earlier branch/base fields above remain historical receipt data and are superseded only by this additive correction.
