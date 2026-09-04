# Claim: 0037-10.01 AE-4+AE-5 follow-up (tests only)

- owner_token: `agent:airiam-0037-10.01-ae45-20260828:0037-10.01-ae45:20260828T115500Z`
- mailbox: `airiam-0037-10.01-ae45-20260828`
- agent/persona: Airiam, unprivileged Programmer (not dispatcher gabriel)
- git author on this host: `gabriel <gabriel@discovery.starfleet.network>` — persona is Airiam; do not treat git author as mailbox identity
- dispatcher: gabriel; AWARD offer `1787917459879-0fa7e42b`
- capability_class: `unprivileged`
- execution_authority: direct Git/tests in item-owned worktree; no `run.sh`; not privileged
- item/branch/worktree: `0037-10.01-ae45` / `0037-10.01-ae45-airiam-20260828` / `/Users/tobias.anton/devel/autodocs/.worktrees/0037-10.01-ae45-airiam-20260828`
- AWARD pin / cut: `0e0650e664bae7519db7ed1a26656059c073a65b` (remeasured equal to `refs/heads/main` immediately before cut)
- exact_write_scope:
  - `_src/tests/test_issuectl.py`
  - `TODO-airiam-0037-10.01-ae45-20260828T115500Z.md`
- forbidden: `_src/tools/issuectl.py` (stop if tests cannot be written without it); land; `Acceptance: ✓`; Feature 0037 `DONE.md`; 0037-16 STOP; 0019 / 0039-01 / 0041 / 0044 / 0047 / 0022 / 0027; spawn implementer; `memory_append`; `logs/agent-memory/**`; reuse `agent:gabriel-issuectl:0037-10.01:20260825T114200Z`; overwrite 10.01 TODO heading REF
- status: `[x]` implementation complete (follow-up claim only). No Acceptance. Do not land.
- product_SHA: `7a55d62ae632a07402928d841dc3279fa9138e53`
- 10.01 heading REF left unchanged: `007234d85b53b4fc5e7d57e817b24095ff3e5259`
- issuectl.py blob after commits must remain `b8a3e77a082e59fee0203c52be453d24b985e013`

## Task

Close first-review `d2f3138b2` INCONCLUSIVE AE-4/AE-5 gaps with tests only.

## Product

- AE-4: `test_prereq_self_target_ic1108_distinct_from_two_node_cycle` (self-check IC1108 vs cycle IC1108)
- AE-4: `test_criterion_move_missing_destination_ic1114_distinct_from_same_id` (dest-missing vs source==dest)
- AE-4: `test_criterion_move_crash_on_second_os_replace_rolls_back` (second `os.replace` of criterion-move)
- AE-5: `DetectCyclePropertyTests.test_detect_cycle_property_named_and_enumerated`
  - invariant/oracle: `detect_cycle(G) is None` iff Kahn classifies G as DAG; cyclic reports contain a repeated vertex
  - domain: named 3-node cycle, 6-node longer-chain cycle, 12-node deep acyclic chain; plus k-cycles and Hamiltonian paths on N∈{3,4,5}; plus 40 successor-or-none graphs per N, seed `20260828+N`
  - executed case count: **132**

## Validation

- `python3 _src/tests/test_issuectl.py -v` — 23 tests OK (julian venv missing; system python3)
- `python3 -m py_compile _src/tools/issuectl.py _src/tests/test_issuectl.py` — PASS
- `automation_safety.py --path _src/tests/test_issuectl.py`: verdict FAIL; AUTO010 at lines 196 (pre-existing list-filter claim fixture) and 945 (`test_move_success_and_claim_scope`, previously recorded ~872). New AE-4/AE-5 tests did not add AUTO010. No policy disposition added. Tests not weakened.

## User prompt (verbatim)

You are an unprivileged Programmer. You are NOT dispatcher gabriel, not gabriel-issuectl, not Burnham, not Nhan, not Joann, not Tilly, not Saru, not belanna, not paul.

Mailbox identity to announce: **airiam-0037-10.01-ae45-20260828**
Persona: Airiam, unprivileged Programmer.

## Four briefing fields (mandatory; dispatcher gabriel remains answerable)

1. **capability class:** `unprivileged`. Direct Git/tests in the item-owned worktree. NOT sandboxed-grunt. Do not route through run.sh. NOT privileged. You do NOT land. You do NOT request Acceptance. You do NOT stamp `Acceptance: ✓`. You do NOT waive AE-4 or AE-5.
2. **item / branch / worktree:** **0037-10.01 AE-4+AE-5 follow-up** (tests only). Remesure `refs/heads/main` immediately before cut. AWARD pin this spawn: `0e0650e664bae7519db7ed1a26656059c073a65b` (michael OFFER cited `91cd74d2e`; that tip moved; cut from then-current main, **do not silent-retarget to another item**). **If main moved again vs this pin, STOP and report.** New branch (e.g. `0037-10.01-ae45-airiam-20260828`) and **new** worktree under `/Users/tobias.anton/devel/autodocs/.worktrees/` that you own. Never write the shared root `/Users/tobias.anton/devel/autodocs`. Use `git -C <abs>` / absolute paths. Never `git update-ref` `refs/heads/main`.
3. **write scope:** tests + new claim only. Prefer `_src/tests/test_issuectl.py`. Do **not** edit `_src/tools/issuectl.py` unless a test cannot be written — if so STOP and report. Confirm after commits that `issuectl.py` blob is still `b8a3e77a082e59fee0203c52be453d24b985e013` or STOP.
4. **must not:** land; stamp `Acceptance: ✓`; Feature 0037 `DONE.md`; lift **0037-16** STOP; take 0019 / 0039-01 / 0041 / 0044 / 0047 / 0022 / 0027; spawn another implementer; call `memory_append`; tidy `logs/agent-memory/**`; reuse `agent:gabriel-issuectl:0037-10.01:20260825T114200Z`.

## Required product (AWARD offer 1787917459879-0fa7e42b)

First-review `d2f3138b2` INCONCLUSIVE (not rejected). Evidence: `git show d2f3138b2:docs/campaign-evidence/review-0037-10.01-belanna-20260828T1015Z/review.md`. 10.01 still `[x]` REF `007234d85` (that SHA may not be an ancestor of main — do not cut from it). No `Acceptance: ✓`.

AE-1 applies (create/edits, identity, gates, `detect_cycle`).

**AE-4:**
1. `cmd_prereq` self-check IC1108 (`target==id`) untested vs cycle IC1108; criterion-move dest-missing IC1114 untested vs source==dest IC1114.
2. multi-file crash-rollback on second `os.replace` during criterion-move untested.

**AE-5:** `detect_cycle` has one 2-node case; add property evidence: 3+-node cycle, longer-chain cycle, deep acyclic no false-positive. Name invariant/oracle, domain/boundary, **executed case count**.

AUTO010 on `test_move_success_and_claim_scope` is recorded; do not add a policy disposition; do not weaken tests; if new tests trip AUTO010, record it.

Mint `owner_token: agent:airiam-0037-10.01-ae45-20260828:0037-10.01-ae45:<request-id>`.

If host git author is `gabriel`, record persona Airiam vs git author.

Do not overwrite the 10.01 TODO heading REF. Follow-up claim only.

## Inbox

Announce as `airiam-0037-10.01-ae45-20260828`. When `[x]`, mail **gabriel** thread `0037-09-wave` with mailbox, token, branch, worktree, product SHA, bookkeeping SHA, vs-main left-right, suite, whether `issuectl.py` edited (expected no). Keep mail under 1000 chars.

Stop at `[x]`. Do not land.

Julian venv if present: `/tmp/autodocs-0037-08-venv-julian/bin/python`.

Return when `[x]` or blocked with those fields.
