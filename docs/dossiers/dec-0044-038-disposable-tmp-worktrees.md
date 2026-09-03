### DEC-0044-038 — Repository governance for disposable agent worktrees

- **Record format:** `decision-record@v1`
- **Recorded at:** 2026-09-03
- **Deciding identity:** Current user, represented by user prompts
- **Role:** Management
- **Authority reference:** Current user instructions explicitly mandating that agents must stop filling project/devel storage with worktrees and use /tmp instead.
- **Subject:** Repository governance for disposable agent worktrees
- **Decision:** Agents must stop filling project/devel storage with worktrees; all new agent-created worktrees belong under /tmp, are disposable, and agents must expect automatic disappearance. Worktrees are execution caches, never survival/provenance authority; useful work must be committed to Git refs. Disappearance or unavailable registration alone cannot block start/validation/integration/publication/closure. Stale registrations are normal reap cases. Hygiene still blocks dirty/index divergence in available worktrees, dirty tracked root, candidate overlap, indeterminate reachable Git/ref state, or missing required committed evidence. Existing non-/tmp worktrees are legacy and need not be recreated/migrated. Never delete branch/tag/ref merely with a worktree.
- **Technical justification:** Worktrees are transient execution contexts that frequently clutter persistent project storage. By relocating them to /tmp, the system delegates lifecycle management to the OS, preserving persistent storage. The requirement that useful work must be committed to Git refs ensures that no critical state is lost when a worktree is reaped. Treating worktrees as execution caches simplifies crash recovery and prevents worktree metadata from being a blocking dependency for normative pipeline steps.
- **Triggers:**
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  1. **Selected — /tmp disposable worktrees as execution caches.** Moves all new worktrees to /tmp, explicitly decouples pipeline state from worktree survival, and relies entirely on Git refs for provenance and state.
  2. **Rejected — Persistent bounded worktrees.** Would require complex lifecycle management and garbage collection logic by the agents, violating the directive to stop filling project storage.
- **Consequences:** All tools and agents that create worktrees must target /tmp. Pipeline validation steps must not treat missing worktrees as blocking errors for task progression; they must evaluate Git refs. Dirty tracked roots or uncommitted divergence within an available worktree remain blocking hygiene violations. No retroactive migration of existing worktrees is required. Branches, tags, and refs remain the sole persistent artifacts and must not be deleted as a side-effect of worktree cleanup.
- **Affected work units:**
  - `repository:autodocs`
  - `feature:0044`
- **Affected gates:**
  - `task-start`
  - `integration`
- **Review participation:** none
- **No-review reason:** This record was authored directly by the management-instantiated Architect. Independent scope review is attached.
- **Waiver:** none
