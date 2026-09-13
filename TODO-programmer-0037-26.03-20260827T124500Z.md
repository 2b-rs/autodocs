# Claim: 0037-26.03

- item: `0037-26.03`
- state: `[x]`
- owner_token: `agent:programmer-0037-26.03:0037-26.03:20260827T124500Z`
- capability_class: `unprivileged`
- execution_authority: direct tools; no runner; no Acceptance; no main; no DONE; no push
- persona: Programmer (distinct from dispatcher gabriel)
- startup_review: 2026-08-27; assigned by dispatcher gabriel
- write_scope:
  - `_src/tools/version_store.py`
  - `_src/tools/evidence_snippet.py`
  - `_src/tools/evidence_version_provenance.py`
  - `_src/tests/test_evidence_version_provenance.py`
  - `TODO-programmer-0037-26.03-20260827T124500Z.md`
  - `TODO.md` (0037-26.03 block only)
- execution_scope: git -C `.worktrees/0037-26.03`; tests under that worktree
- must_not: Acceptance; refs/heads/main; DONE.md; 0037-16 STOP lift; sibling 26/27; 16/19/20/38/42 product; shared root; memory_append; push
- base: `2064704457f98c66fb6f77ad3c263415864fe2ff` (0037-16 R2 / 0037-19 bookkeeping tip, **not** main)
- remasure_0037-19: `[x]` at that commit; REF `c2f198e19`; prereqs 0037-17 and 0037-19 are ancestors (`17in=0`, `19in=0`)
- merged_prereq_tips:
  - `0037-17` already ancestor (`78f1e3fd2`)
  - `0037-19` already ancestor (`2064704457`)
- branch: `0037-26.03`
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-26.03`
- assumptions:
  - Producer family is `_src/tools/version_store.py` + `_src/tools/evidence_snippet.py`.
  - Shared provenance schemas/indexes from 0037-17 are used; no sibling 26/27 product.
  - Synthetic fixtures stay `synthetic`/`development-test`; never relabeled production.
  - Legacy JSONL lines without envelope get explicit unknown/legacy disposition; no invented run/issue backfill.

## Completion

- substantive REF: `8ac92acee0afa2197cc2ee5fd08cb4ebafc76d35`
- validation: `python3 -m unittest _src.tests.test_evidence_version_provenance _src.tests.test_curation_item_versioning` 16/16 OK
- next: none; implementation terminal; Acceptance not in scope

