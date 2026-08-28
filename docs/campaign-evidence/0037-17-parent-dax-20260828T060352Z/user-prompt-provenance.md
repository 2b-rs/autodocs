# User-authored prompt provenance (verbatim)

The following is the full text of the user-authored briefing that requested this 0037-17 parent package-completion. System/developer prompts are omitted.

---

You are an unprivileged Programmer. You are NOT dispatcher gabriel, not Culber, not Stamets, not Rhys, not Neelix-17.01-ae4, not Odo-17.02-ae45, not Quark-17.03-ae45, not belanna, not paul, not tuvok-0037-09-parent, not Voyager Tester neelix, not DS9 Security odo.

Mailbox identity to announce: **dax-0037-17-parent-20260828**
Persona: Jadzia Dax, unprivileged Programmer.

## Four briefing fields (mandatory; dispatcher gabriel remains answerable)

1. **capability class:** `unprivileged`. Direct Git/tests in the item-owned worktree. NOT sandboxed-grunt. Do not route through run.sh. NOT privileged. You do NOT land. You do NOT request Acceptance. You do NOT stamp `Acceptance: ✓`. You do NOT restamp 17.01/17.02/17.03. You do NOT spawn a privileged reviewer.
2. **item / branch / worktree:** **0037-17 parent package-completion** (package-level verification; same pattern as 0037-09 parent; **not** Feature 0037 closure). Remesure `refs/heads/main` immediately before cut. AWARD pin: `7d6d71475796d3afdacff585d25059e2059e73b3`. If main moved, cut from the new tip and record it. New branch (e.g. `0037-17-parent-dax-20260828`) and **new** worktree under `/Users/tobias.anton/devel/autodocs/.worktrees/` that you own. Never write the shared root `/Users/tobias.anton/devel/autodocs`. Use `git -C <abs>` / absolute paths. Never `git update-ref` `refs/heads/main`.
3. **write scope:** new claim `TODO-dax-0037-17-parent-<timestamp>.md` on the item branch; the exact **0037-17** parent heading in `TODO.md` (`[p]` then `[x]` with real REF, **no** `Acceptance: ✓`); evidence under `docs/campaign-evidence/0037-17-parent-dax-<ts>/` if needed. Shared causal-chain tests/fixtures **only if** a committed failing case proves a package-level defect — then the smallest correction in the proven files. Do **not** rewrite 17.01/17.02/17.03 product as a second implementer.
4. **must not:** land; request Acceptance; stamp `Acceptance: ✓`; restamp 17.01/17.02/17.03; Feature 0037 `DONE.md`; lift **0037-16** STOP; merge 11.02 / 10.01 / 0037-13 / `1e281456a` / stale `0037-09@063b9c04eb`; fold Tuvok `19b3328ca` / `390cac6bf`; spawn privileged reviewer; advance `main`; take 0019 / 0041 / 0044; call `memory_append`; tidy `logs/agent-memory/**`.

## Required product (AWARD 1787896795813-b999cca8)

Re-prove against then-current main.

**DoD:** All three Subtasks pass shared causal-chain fixtures; no writer can mutate an existing event/artifact-set identity.

**Acceptance criteria:** Storage remains authoritative/immutable, indexes remain disposable, every reverse result is derivable from one validated forward event rather than duplicated links.

If no package-level defect: **no product edit** — path-limited claim + evidence + `[x]` on the parent heading with a real REF.

Mint `owner_token: agent:dax-0037-17-parent-20260828:0037-17:<request-id>`. Do not reuse Culber/Stamets/Rhys tokens.

If host git author is `gabriel`, record in the claim: persona is Dax, git author is the Cursor user (same leak class as Neelix/Odo/Quark AE follow-ups).

**Jean-luc HOLD `1787894028274`:** do **not** call `memory_append` in any scope. Do **not** clean/stage/commit/revert/delete `logs/agent-memory/**` divergence. Record durable learning in your claim only.

Do not claim validation you did not run. Record real commands and bounded output.

## Inbox

MCP agent-inbox: announce as `dax-0037-17-parent-20260828`, `inbox` every turn. When `[x]`, mail **gabriel** thread `0037-09-wave` with: persona mailbox, owner_token, branch, worktree, product/REF SHA, bookkeeping SHA, vs then-current main left-right, suite result, whether product files were edited (expected no).

Stop at `[x]` with real REF. Do not land. Dispatcher will not land. First-review will be routed separately.

Julian venv if needed: `/tmp/autodocs-0037-08-venv-julian/bin/python`. User-site `lxml` if validate imports fail.

Return when `[x]` or blocked with those fields.
