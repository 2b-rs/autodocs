# Claim: Task 0037-27.01

owner_token: agent:philippa-rhys-0037-27.01:0037-27.01:20260827T123900Z
agent: philippa-rhys-0037-27.01
capability_class: unprivileged
execution_authority: direct Git/tests in item worktree; no Acceptance, checkpoint, main, DONE.md
task: 0037-27.01
feature: 0037
branch: 0037-27.01
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0037-27.01
state: [x]
substantive_ref: f5c059ba8bb8cb9dc1ee4a8d7b422fe149a8edd4
base: branch 0037-19 @ 2064704457f98c66fb6f77ad3c263415864fe2ff
named_expected_ancestor: F-0037-16-R2-01 / cfa4b8f2c (verified ancestor of 0037-19)
prereq_0037-17: ancestor 78f1e3fd2 (already merged; no extra merge)
prereq_0037-19: [x] REF c2f198e19
0037-16_remeasure: 0037-16 tip 2d6887a07 is ancestor of 0037-19; R2 remains ancestor of this base. No silent rebase onto main. STOP/tasha 0037-16 untouched.

## Task text (verbatim)

- [ ] **0037-27.01** PREREQ: 0037-27.01:0037-17, 0037-27.01:0037-19 Persist AI workflow runs and typed claims with stable claim IDs and common provenance.
  - **Acceptance criteria:** Pin record/evidence/policy/prompt/model/config/input versions, issue/criterion/campaign/run, outputs and confidence/invalidation/supersession; give typed claims their own ID family and one-file persistence; adapt legacy traces with explicit unknown/legacy confidence and never invented prompts/models/runs.
  - **Definition of Done:** Tests trace a claim through source evidence and AI run, invalidate on each governed input change, preserve prior claims/history, and reject fabricated or bare-ID provenance.

## Write scope

- `_src/tools/ai_workflow_persist.py`
- `_src/tools/typed_claim.py` (claim_id family)
- `_src/tools/version_id.py` (`claim:` prefix)
- `_src/tests/test_ai_workflow_persist.py`
- this claim file
- TODO.md **0037-27.01 block only**

## Must not

Acceptance; main; DONE.md; 0037-16; 0037-19/20/38/42 products; 0037-26.*; 0037-27.02/03/04/05 products; frozen `.worktrees/0037-23.02`; memory_append; root `/Users/tobias.anton/devel/autodocs` writes.

## Briefing provenance (verbatim)

You are **philippa-rhys-0037-27.01**, unprivileged implementer (NOT dispatcher philippa, NOT privileged).

## Four briefing fields
1. capability_class: **unprivileged** (direct Git/tests; NO Acceptance, checkpoint, main, DONE.md).
2. item **0037-27.01**; branch **0037-27.01**; worktree **/Users/tobias.anton/devel/autodocs/.worktrees/0037-27.01** (create). NEVER write shared root `/Users/tobias.anton/devel/autodocs`.
3. write scope: AI workflow-run + typed-claim persistence with stable claim IDs and common provenance; 27.01-owned tests/fixtures; claim file; TODO.md **0037-27.01 block only**.
4. must-not: Acceptance; main; DONE.md; 0037-16 (STOP/tasha); mutate 0037-19/20/38/42 products; 0037-26.*; 0037-27.02/03/04/05 products; frozen `.worktrees/0037-23.02`; memory_append; root writes.

**owner_token:** `agent:philippa-rhys-0037-27.01:0037-27.01:20260827T123900Z`
**claim:** `TODO-philippa-rhys-0037-27.01-20260827T123900Z.md` on branch 0037-27.01
**base:** branch `0037-19` @ `2064704457f98c66fb6f77ad3c263415864fe2ff` (named expected ancestor `cfa4b8f2c` / F-0037-16-R2-01). Merge prereq branch `0037-17` if not already ancestor. Remeasure; if 0037-16 checkpoint later invalidates R2, stop and report — do not silently rebase onto main.
**Prereqs on 0037-19 TODO snapshot:** 0037-17 [x], 0037-19 [x] REF c2f198e19.

## Contract
Persist AI workflow runs and typed claims with stable claim IDs and common provenance.
AC: Pin record/evidence/policy/prompt/model/config/input versions, issue/criterion/campaign/run, outputs and confidence/invalidation/supersession; typed claims own ID family and one-file persistence; adapt legacy traces with explicit unknown/legacy confidence; never invent prompts/models/runs.
DoD: Tests trace a claim through source evidence and AI run, invalidate on each governed input change, preserve prior claims/history, reject fabricated or bare-ID provenance.

Follow AGENTS.md + SANDBOX.md + branch-workflow.md. Commits in the worktree with provenance of this briefing. Stop at [x]. No push. Report REFs to philippa and kathryn.

Keep going until complete or blocked. Return claim path, SHAs, validation.

## Progress

- Worktree created from 0037-19 @ 206470445.
- Deliverables: `ai_workflow_persist.py`, `claim:` ID family, hermetic tests (14) + typed_claim (10).
- Validation: `python3 _src/tests/test_ai_workflow_persist.py -v` OK (14); `python3 _src/tests/test_typed_claim.py` OK (10).
- Implementation terminal at `f5c059ba8`. No Acceptance. No push.
