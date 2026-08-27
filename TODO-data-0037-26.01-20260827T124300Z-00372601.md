# Claim `0037-26.01`

- item: `0037-26.01`
- owner_token: `agent:data:0037-26.01:20260827T124300Z-00372601`
- request_id: `20260827T124300Z-00372601`
- persona: `data` (unprivileged Programmer; distinct from dispatcher `gabriel`)
- capability_class: `unprivileged`
- execution_authority: unprivileged Programmer — direct execution; no Acceptance, no Integration review, no Feature→main/`DONE.md`
- branch: `0037-26.01`
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-26.01`
- start_base: `2064704457f98c66fb6f77ad3c263415864fe2ff` (0037-19 product REF `c2f198e19`)
- independently_remeasured_0037-19: `[x]` on that tip with **REF:** `c2f198e19` (worktree `git show 2064704457:TODO.md`)
- 0037-17 ancestor: `78f1e3fd2` is ancestor of start_base (`merge-base --is-ancestor` exit 0)
- merged_prereq_tips: none (0037-17 and 0037-19 already ancestors of start_base)
- write_scope: scrape/extraction report producers (`_src/tools/spec_scrape.py`, `_src/tools/extraction_report.py`, `_src/tools/score_scrape.py`, new `_src/tools/scrape_extraction_provenance.py`), focused tests under `_src/tests/test_scrape_extraction_provenance.py`, this claim file, `TODO.md` 0037-26.01 block only
- 0037-37 inventory (family at merged base, `chore_tool_inventory_data.json` + Task text): `spec_scrape.py` (PDF/backend scrape reports: `phase_crosscheck`, `write_traceability_records`, `check_traceability_consistency`), `extraction_report.py` (extraction-deviation report assemble/build), `score_scrape.py` (text/repo scrape JSON report). Not this family: `spec_extraction_campaign.py` (0037-26.02), record-version writers (0037-26.03), curation (0037-26.05), build reports (0037-26.06), 0037-27.*
- must_not: Acceptance; Integration review; merge to main; DONE.md; lift 0037-16 STOP; take 0037-16/19/20/38/42 product; 0037-27.* or sibling 0037-26.* files; Feature ownership; 0019/0041/0044/0047; foreign `[p]`; root checkout; memory_append; push
- caveat: tip sits on 0037-16 R2 candidate not main; rejected checkpoint requires rebase
- startup_review: assigned item; 0037-19 still `[x]` on start_base; implementation start prereqs 0037-17 and 0037-19 terminal on this tip; Mail ACCEPT is not ownership
- product_ref: `943e852eb596a998f5d9c659427ba5379452af3e`
- next_step: none — implementation `[x]`; Acceptance is a separate privileged review

## Progress

- 2026-08-27T12:43:00Z worktree created at `.worktrees/0037-26.01` from `2064704457`. Claim SHA `b660ea5ef2415dbd03f7894d5dc9e529e0548f90`. WT `/Users/tobias.anton/devel/autodocs/.worktrees/0037-26.01`.
- Product REF `943e852eb596a998f5d9c659427ba5379452af3e`. Validation: `python3 _src/tests/test_scrape_extraction_provenance.py` 8/8 OK; py_compile of family producers OK.
