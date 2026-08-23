# Core Pipeline & Engineering Rules (ASPICE Baseline)

## 1. Traceability & Identifier Discipline
- Every engineering work product MUST be identifiable and traceably linked:
  * Requirements: `REQ-<feature>-<id>`
  * Architecture & Decisions: `DEC-<feature>-<id>`
  * Tasks: `TASK-<feature>-<id>` or `<feature>-<step>`
  * Commits & Merges: Reference requirement/task ID (`REF: <id>`, `PREREQ: <id>`).
- Bidirectional traceability must exist from customer/user requirement down to code, unit test, review, and verification evidence.

## 2. Worktree & Branching Isolation
- All implementation and verification work MUST happen in item-owned isolated worktrees and branches (`feature/<id>` or `<feature>-<step>`).
- Direct commits to `main` without review and preflight verification are prohibited.
- Merges to `main` must be fast-forward only (`git merge --ff-only`) with a clean working tree.

## 3. Four-Eyes Principle (Independence of Roles)
- Author and Reviewer/Integrator MUST be distinct agents/identities.
- Self-acceptance is strictly prohibited unless an explicit, recorded, bounded waiver exists.
- Privilege is not independence: having write access does not grant review authority over own code.

## 4. Evidence-Based Verification
- Every assertion ("tests pass", "verified", "ready") requires concrete, reproducible evidence:
  * File paths and exact line numbers (`file:line`)
  * Commit hashes (`REF: <commit-sha>`)
  * Test execution command, exit code, and actual output summary.
- Green command output is evidence of execution, not proof of complete requirement satisfaction.

## 5. Scope & Boundary Protection
- Stick strictly to the assigned Task scope and declared write paths.
- Do not refactor unrelated modules, rename public interfaces without architectural decision (`DEC`), or introduce hidden dependencies.
- Secrets, credentials, and user data must never be committed.

## 6. Memory Governance
- Use partitioned working memories:
  * Agent memory: `.memory/agents/{agent}.md` (personal habitus)
  * Role memory: `.memory/roles/{role}.md` (role practices)
  * Capability memory: `.memory/capability-sets/{cap_set}.md` (permissions)
  * Feature memory: `docs/features/{feature}/MEMORY.md` (active feature work, deleted strictly upon Acceptance).
- All memory entries must have an ISO-8601 UTC timestamp and author signature.
