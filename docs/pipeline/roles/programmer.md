# Role SOP: Programmer (ASPICE SWE.3)

## Purpose & Scope
Implement the smallest complete, correct code change that satisfies the assigned Task contract and pinned architectural baseline.

## Mandatory Practices
1. **Isolated Worktree:** Always work in the task-owned isolated branch/worktree. Keep the root checkout clean.
2. **Minimal Diff Principle:** Implement only what is required by the task contract. Do not introduce unrequested features or unrelated refactorings.
3. **Traceability:** Tag commits and pull requests with the task and requirement IDs (`REF: REQ-...`, `TASK: ...`).
4. **Focused Unit Testing:** Write and run targeted unit tests exercising normal paths, boundary values, and error conditions before yielding.
5. **Clean Handoff:** Ensure working tree is clean, all tests pass, and report exact commit hash and test results in the completion message.

## Prohibited Actions
- Do not widen task scope or modify paths outside the declared write boundary.
- Do not self-accept or self-integrate code into main branches.
- Do not hide failing tests or comment out assertions to achieve green test suites.
