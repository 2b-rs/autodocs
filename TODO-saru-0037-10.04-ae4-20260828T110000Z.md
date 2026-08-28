# Claim 0037-10.04 AE-4 follow-up (tests only)

- owner_token: agent:saru-0037-10.04-ae4-20260828:0037-10.04-ae4:20260828T110000Z
- capability_class: unprivileged
- execution_authority: unprivileged Programmer (persona Saru). Host git author is `gabriel` / `gabriel@discovery.starfleet.network` (Cursor user identity); persona is Saru, not dispatcher gabriel.
- mailbox: saru-0037-10.04-ae4-20260828
- item: 0037-10.04 AE-4 follow-up (AE-4 not waived)
- branch: 0037-10.04-ae4-saru-20260828
- worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0037-10.04-ae4-saru-20260828
- dispatch_pin_main: 8948a602320c7c0781ed9a578a42b664dfd2eff4 (remeasured equal before cut; no silent-retarget)
- award: briefing AWARD via offer 1787914589074-51c7e982 (offer_reply ACCEPT refused: this mailbox is not a named candidate; work proceeded on explicit parent briefing)
- tokens_not_reused:
  - agent:gabriel-burnham-20260825t092000z:0037-10.04:20260825T092000Z
  - agent:gabriel-nhan-20260825t091000z:0037-10.04:20260825T091000Z
- write_scope: `_src/tests/test_issuectl.py`, `_src/tests/fixtures/0037-10.04/claim.json`, this claim
- not_in_scope: `_src/tools/issuectl.py` (do not edit unless a test cannot be written), landing, `Acceptance: ✓`, Feature 0037 DONE.md, 0037-16 STOP, 0019/0041/0044/0047/0022/0027, spawn implementer, memory_append, logs/agent-memory/**
- issuectl_py_edited: no

## Product contract

Belanna review `b29d30964` INCONCLUSIVE. Product `0450b53cc` / REF `7382aea9` ancestor of main. 10.01 `18b478c3b` on main. Tests against current main.

AE-1 applies to `cmd_list`. AE-4 named cases:

1. owner list-query unfiltered and filter-match/filter-miss with `claim.json` fixture (`--query owner`)
2. `unclear` negative (well-formed item excluded)
3. `prerequisite` negative (item without prereqs excluded)

Do not waive AE-4. AE-5 not triggered. Do not overwrite Burnham REF on the 10.04 TODO heading.

## Progress

- 2026-08-28T11:00:00Z worktree cut from pin; tests next.
