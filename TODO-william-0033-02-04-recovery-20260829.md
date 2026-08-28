# Dispatcher coordination claim — 0033-02 through 0033-04 recovery preparation

- **owner_token:** `agent:william:0033-02-04-recovery:1787959173731-a7980aed`
- **state:** `[p]`
- **capability_class:** `unprivileged`
- **role:** Dispatcher, Team Enterprise
- **authority:** Atomic AWARD `1787959173731-a7980aed`; exact scope clarification `agent-inbox:1787959339773-a1b03432`
- **branch/worktree:** `0033-02-04-recovery-enterprise-20260829` / `.worktrees/0033-02-04-recovery-enterprise-20260829`
- **base:** `main@af5cf982c8c6dfe8446f120c2695985a5aa3052f`
- **startup_review:** exact main pin verified; branch and worktree were absent; source branches are read-only evidence; competing Lore and Gabriel claim paths verified absent.
- **write scope:** this claim; `docs/campaign-evidence/0033-recovery/0033-02-04-inventory.md`; `docs/dossiers/0033-02-04-recovery-decision-packet.md`. The Lore and Gabriel claim paths named by the scope clarification must remain absent.
- **execution scope:** direct read-only Git/source inspection and path-limited commits in this item-owned worktree only.
- **external resources:** none.
- **must not:** mutate Task/product/governance/TODO state; merge or cherry-pick sources; allocate a decision; claim Architect or reviewer authority; perform review, Acceptance, checkpoint integration, main/ref advance, Feature/DONE movement, cleanup, publication, credential use, or external effects; enter `0033-04.01`, `0033-05`, or later work.

## Ordered recovery state

- Read-only source pins: `0033-02@ee3dfe99c` (substantive `ac4b2579a`); `0033-03@0edf6ce53` (substantive `7c21351cf`, prerequisite merge `53a5c68d9`); `0033-04@46bef8cbc` (substantive `d0eca203e`, historical merges `5af29c12` and `98d2a3f60`).
- First action: inventory `0033-02` exact commits, Task-owned paths, current-main divergence, Acceptance/checkpoint state, and hidden policy/authority choices.
- Mandatory wait after `0033-02`: classify cross-item gate reach and proposal-versus-operative status before inspecting `0033-03` as a continuation candidate.
- Continue to `0033-03` only if source ownership is unambiguous; continue to `0033-04` only after separating its additional `0033-03.01`/`0039` ancestry from Task-owned content.
- Terminal deliverables: permanent recovery inventory and a Management/Architect decision packet naming affected work units/gates, options, risks, smallest intent-preserving recommendation, and machine-linkable refs. Return the candidate to Jean-Luc; no recovery merge is part of this chain.
- Stop conditions: main drift; contested ownership; unavailable evidence; cross-item scope not fully enumerable; source ambiguity; or any need to write outside the authorized paths.
