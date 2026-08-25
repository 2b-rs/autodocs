# Claim: Subtask 0037-23.01

- owner_token: `agent:gabriel-privacy:0037-23.01:20260825T115400Z`
- agent/persona: Gabriel-Privacy, unprivileged Programmer, Team Discovery
- dispatcher: gabriel; jean-luc `1787658776430-349a559b`
- capability_class: `unprivileged`
- execution_authority: direct local Shell/Git in this dedicated item worktree; no runner queue
- item/branch/worktree: `0037-23.01` / `0037-23.01` / `/Users/tobias.anton/devel/autodocs/.worktrees/0037-23.01`
- Feature base: `722aaa2149c78cf705db411a4142c67d92bb1c3d`
- prerequisites: `0037-01`, `0037-12`, `0037-17.03` already `[x]` on Feature tip; no extra merge
- exact_write_scope:
  - `_src/tools/privacy_projector.py`
  - `_src/tests/test_privacy_projector.py`
  - `_src/data/issue-graph-public.json`
  - `TODO-gabriel-privacy-0037-23.01-20260825T115400Z.md`
  - `TODO.md` (0037-23.01 Task block only)
- forbidden: Acceptance; checkpoint merge; Feature DONE.md; main; push; root recovery/cleanup; live repository TODO.md/DONE.md as product; 10.02/10.03; parent 0037-11
- status: `[p]`; **claim materialization only**. No product mutation before this claim commit REF is reported.
- next_step: wait for start-gate / then implement locale-neutral privacy projector.

## Task

Implement the locale-neutral privacy projector for `_src/data/issue-graph-public.json`.

- **Acceptance criteria:** Include only items explicitly marked `public-summary` and only approved ID/level/title-key/title-source-hash/coarse-state/public-summary/public prerequisites/link fields, with no translated title; exclude claims, identities, private paths, detailed findings/decisions/evidence, security/unreleased items, and all incident edges to omitted nodes. Emit an aggregate restricted count without identifiers; fail closed on unknown fields/classes, dangling public edges, missing privacy decisions, or leaked restricted fixture tokens; record input/output artifact sets and policy digest.
- **Definition of Done:** Allowlist and adversarial leak tests, schema validation, deterministic output, reverse privacy checks, and mutation tests prove the public artifact cannot reveal omitted IDs or fields.
