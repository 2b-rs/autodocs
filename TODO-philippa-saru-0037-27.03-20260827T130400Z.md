# Claim: Subtask 0037-27.03

owner_token: agent:philippa-saru-0037-27.03:0037-27.03:20260827T130400Z
agent: philippa-saru-0037-27.03
capability_class: unprivileged
execution_authority: direct Git/tests in item worktree; no Acceptance, checkpoint, main, DONE.md
task: 0037-27.03
feature: 0037
branch: 0037-27.03
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0037-27.03
state: [x]
substantive_ref: eca14f6f9a87ac38c62c7f4b1404b22f5c60f535
named_expected_ancestor: F-0037-16-R2-01 / cfa4b8f2c (verified ancestor of HEAD after base-and-merge)

## Base-and-merge (measured)

- Cut from Feature `0037` @ `e495e053443726760eae0255fbaf24a216874315`
- Merged `0037-19` @ `2064704457f98c66fb6f77ad3c263415864fe2ff` (fast-forward from Feature tip; Feature+17 already contained)
- Merged `0037-17` @ `78f1e3fd2a74e4dab5a6c8fe150ab69384715157` (Already up to date / no-op)
- Merged `0037-27.01` @ `9c1a1c86f612996cbb975ec289b9a8456d090d90` (contains product `f5c059ba8`)
- HEAD after merges: `9c1a1c86f612996cbb975ec289b9a8456d090d90`
- R2 `cfa4b8f2c` remains ancestor. No rebase onto main.

## Task text (verbatim)

- [ ] **0037-27.03** PREREQ: 0037-27.03:0037-17, 0037-27.03:0037-19, 0037-27.03:0037-27.01 Extend user-guide/process-page authoring and page composition with typed claims and common provenance.
  - **Acceptance criteria:** Link guide/page fragment to exact records/evidence/claims/instructions/policy/config, authoring issue/criterion/run, composition input/output hashes, review decision, and invalidation cause; generated HTML remains derived from `_src/` sources.
  - **Definition of Done:** A guide/page fixture traces every published claim to approved source/decision and input change creates bounded linked regeneration work.

## Write scope

- `_src/tools/page_composition_provenance.py`
- `_src/tests/test_page_composition_provenance.py`
- `_src/tests/fixtures/page_composition/`
- this claim file
- TODO.md **0037-27.03 block only**

## Must not

Acceptance; main; DONE.md; 0037-16; mutate 19/20/38/42; 0037-26.*; mutate 27.01/02/04/05 products; frozen 0037-23.02; memory_append; root `/Users/tobias.anton/devel/autodocs`. Bind writers to existing provenance/_schema via provenance_store; if a gap exists report as a finding, do not invent a local schema fork. Path-grep for schema filenames is not the test — import provenance_store + schema_version is.

## Startup review

- capability_class unprivileged per briefing.
- Import binding: `import provenance_store as ps` and `ps.SCHEMA_VERSION` on every store record.
- Schema gap policy: report finding; do not fork.

## Briefing provenance (verbatim)

You are **philippa-saru-0037-27.03**, unprivileged implementer (NOT dispatcher philippa).

## Four briefing fields
1. capability_class: **unprivileged**. No Acceptance, checkpoint, main, DONE.md.
2. item **0037-27.03**; branch **0037-27.03**; worktree **/Users/tobias.anton/devel/autodocs/.worktrees/0037-27.03**. NEVER write root `/Users/tobias.anton/devel/autodocs`.
3. write scope: user-guide/process-page authoring and page composition with typed claims and common provenance; 27.03-owned tests/fixtures; claim; TODO.md **0037-27.03 block only**. Generated HTML remains derived from `_src/` sources — do not hand-edit generated HTML.
4. must-not: Acceptance; main; DONE; 0037-16; mutate 19/20/38/42; 0037-26.*; mutate 27.01/02/04/05 products; frozen 0037-23.02; memory_append; root. Bind writers to existing provenance/_schema via provenance_store; if a gap exists report as a finding, do not invent a local schema fork. Path-grep for schema filenames is not the test — import provenance_store + schema_version is.

**owner_token:** `agent:philippa-saru-0037-27.03:0037-27.03:20260827T130400Z`
**claim:** `TODO-philippa-saru-0037-27.03-20260827T130400Z.md`

**base-and-merge:** Cut from Feature **0037@e495e053443726760eae0255fbaf24a216874315**, then merge **0037-19@2064704457f98c66fb6f77ad3c263415864fe2ff** and **0037-17@78f1e3fd2a74e4dab5a6c8fe150ab69384715157** and **0037-27.01@9c1a1c86f** (or equivalent tip with product f5c059ba8) before product mutation. If 0037-19 already contains Feature+17, merges may be no-op — still record measured tips. R2 cfa4b8f2c must remain ancestor unless you stop and report checkpoint invalidation. Do not silently rebase to main.

## Contract
Extend user-guide/process-page authoring and page composition with typed claims and common provenance.
AC: Link guide/page fragment to exact records/evidence/claims/instructions/policy/config, authoring issue/criterion/run, composition input/output hashes, review decision, invalidation cause.
DoD: A guide/page fixture traces every published claim to approved source/decision; input change creates bounded linked regeneration work.

Stop at [x]. Report REFs to philippa, kathryn, michael. Keep going.

## Progress

- Worktree created; prereq merges recorded above.
- Deliverables: `page_composition_provenance.py`, fixtures, 9 tests.
- Validation: `python3 _src/tests/test_page_composition_provenance.py -v` OK (9).
- Implementation terminal at `eca14f6f9`. No Acceptance. No push.
