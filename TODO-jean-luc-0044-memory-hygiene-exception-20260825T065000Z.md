# Coordination claim — DEC-0044-021

- owner_token: `agent:jean-luc:0044-memory-hygiene-exception:20260825T065000Z`
- role: Project Lead, Team Enterprise
- capability_class: `privileged`
- execution_authority: current-user directive, 2026-08-25: `logs/agent-memory` is ephemeral shared learning state; issue attribution in the commit message is sufficient; define a hygiene-checker exception.
- branch: `gov-0044-memory-hygiene-exception-jean-luc-20260825`
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/gov-0044-memory-hygiene-exception-jean-luc-20260825`
- base: `main@f1631200b22e53ac13b410662048dec2ba47ddd0`
- status: `[p]` DEC-0044-020 candidate rejected by Architect at `b3dc4a736e341cab713efa190ef3b3a424342724`; corrected DEC-0044-021 candidate prepared; cross-item gate mutation remains stopped pending distinct Architect re-review.
- write scope: this claim and `docs/dossiers/dec-branching-merging-strategie.md` only.
- prohibited: checker/code/test mutation, Acceptance, integration verdict, main advance, publication, push, or cleanup of the existing root deviation.
- affected gates: repository-wide pre-integration hygiene `MAIN_WORKTREE_DIRTY` and the complementary hard root preflight.
- next step: distinct management-instantiated Architect reviews exact decision candidate and supplies binding implementation constraints; implementation is then dispatched separately.
