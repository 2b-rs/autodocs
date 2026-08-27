# Claim: Subtask 0037-26.05

owner_token: agent:worf-0037-26-05:0037-26.05:20260827T124500Z-c7e4a91b
agent: worf-0037-26-05
persona: unprivileged Programmer (≠ gabriel dispatcher)
capability_class: unprivileged
execution_authority: direct git/test execution in own worktree; no runner; no Acceptance/main/DONE
task: 0037-26.05
feature: 0037
branch: 0037-26.05
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0037-26.05
base_pin: 2064704457f98c66fb6f77ad3c263415864fe2ff (0037-19 [x] remasured 2026-08-27; R2 candidate base caveat — 0037-16 chain not on main)
merged_prereq_tips:
  - 0037-17 package tip ancestor of 0037-19 (REF 7be6c50137bf726b291d1485c8fa7f588cc54046)
  - 0037-19 2064704457f98c66fb6f77ad3c263415864fe2ff
state: [x]
startup_review: 0037-19 [x] on branch 0037-19 / worktree /Users/tobias.anton/devel/.worktrees/0037-19; 0037-17 [x]; Task 0037-26 parent branch does not exist — Subtask cut from 0037-19 per dispatcher start pin. No sibling 26/27 merge. Requester identity is not approval.

## Task text (verbatim)

- [ ] **0037-26.05** PREREQ: 0037-26.05:0037-17, 0037-26.05:0037-19 Extend curation items, queues, decisions, and findings with the common provenance envelope.
  - **Acceptance criteria:** Link stable finding, source report/evidence/version, issue/criterion/run/campaign, claim/queue transitions, curator decision/authority, applied change, invalidation/supersession, and published result without treating requester identity as approval.
  - **Definition of Done:** Lifecycle integration tests trace open→claim→decision→apply/publish and reject unauthorized, stale, duplicate, fabricated, or orphaned transitions.

## Write scope

- `_src/tools/curation_provenance.py`
- `_src/tests/test_curation_provenance.py`
- this claim file
- `TODO.md` 0037-26.05 block only (this branch)

## Must not

Acceptance; main; DONE; 0037-16 STOP lift; sibling 26/27; 16/19/20/38/42 product; shared root; memory_append; push.

## Progress

- Implementation complete at REF `6edd1f709b26676fd90ed99cc68fc41705453297`.
- Validation: `python3 -m unittest _src.tests.test_curation_provenance` 9/9 OK.
