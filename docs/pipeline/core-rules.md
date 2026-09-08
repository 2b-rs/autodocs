# Core Pipeline & Engineering Rules (ASPICE Baseline)

## 1. Traceability & Identifier Discipline
- Every engineering work product MUST be identifiable and traceably linked:
  * Requirements: `REQ-<feature>-<id>`
  * Architecture & Decisions: `DEC-<feature>-<id>`
  * Tasks: `TASK-<feature>-<id>` or `<feature>-<step>`
  * Commits & Merges: Reference requirement/task ID (`REQ`/`Task-ID`, `PREREQ: <id>`). After `atomic-checkin-contract@v1` activation, implementation completion uses trailers `Task-ID` and `Base-Ref` rather than an implementation-header git `REF`. Acceptance still records a review `REF` on the separate Acceptance bookkeeping commit.
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
- On first use of a newly applied native profile, read only that agent's
  partitioned agent, role, and capability memories. On ordinary resume, use the
  conversation context and reread only when shared memory may have changed.
- Use partitioned working memories:
  * Agent memory: `logs/agent-memory/agents/{agent}.md` (personal habitus)
  * Role memory: `logs/agent-memory/roles/{role}.md` (role practices)
  * Capability memory: `logs/agent-memory/capability-sets/{cap_set}.md` (permissions)
  * Feature memory: `docs/features/{feature}/MEMORY.md` (active feature work, deleted strictly upon Acceptance).
- Missing files mean empty memory and are created only on the first useful
  append. Shared memory writes must use the generated profile's locked helper;
  direct read-modify-write is prohibited.
- Append only verified, durable, reusable facts with an ISO-8601 UTC timestamp,
  author signature, and stable reference. Do not store transcripts, mailbox
  bodies, task progress, secrets, personal data, or normative facts duplicated
  elsewhere.
- Memory writes are held by `DEC-0044-029` until its activation gate passes. While
  the hold is in force, do not call `memory_append` or `memory_store.py append` in
  any scope; record durable facts in the active item claim, preserve existing
  `logs/agent-memory/**` divergence, and self-report any accidental call with its
  exact path, status, and digest.
- Every memory write requires an explicit active item-owned linked worktree. There
  is no default write target: an omitted or empty workspace, the shared/primary
  checkout, a standalone clone, a symlink resolving to the repository root, and an
  unresolved or non-Git path are each rejected before any lock, directory,
  temporary file, or memory file is created.
- All scopes write inside that proved worktree. Shared agent/role/capability
  entries reach the common baseline only through the ordinary branch commit and
  integration lifecycle -- never by writing the shared root checkout. Feature
  memory remains bound to its active feature worktree.
- Reads follow the same base: reading from a linked worktree returns the committed
  common baseline plus that branch's own entries. Reading one feature memory
  requires that feature's worktree.
- The tool is the enforcement boundary. Profile wording is required guidance but
  cannot authorize or rescue a rejected target, and a successful path check is
  never task ownership, write-scope expansion, Acceptance, integration, release,
  waiver, or specialist authority.
