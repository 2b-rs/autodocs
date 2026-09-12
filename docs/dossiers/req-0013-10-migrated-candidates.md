# Migrated Requirement Candidates (0013-10)

**Status:** Candidate
**Reference:** Feature 0013-10

This document represents the first batch of requirement migrations from scattered repository artifacts into the controlled hierarchy, as defined by the procedures in `req-0013-08` and the inventory from `0013-07`.

## Batch 1: Adversarial Completion Evidence (Process Requirements)

The following requirements were migrated from the `TODO.md` header and `AGENTS.md` (originally introduced by `DEC-0038-004`). They have been classified as formal Quality Assurance / Verification Process Requirements (SUP.1 / SWE.6).

### `REQ-PROC-AE-01` — Applicability of Adversarial Evidence
- **Statement**: The adversarial evidence requirement SHALL apply whenever a substantive change alters counting or cardinality, identity matching, serialization shape, field presence, blocking/gate classification, or asserts an invariant over a set or sequence.
- **Source Link**: `TODO.md` header (`AE-1`) / `AGENTS.md`
- **Supersession History**: Derived directly from legacy inline marker `adversarial-completion-evidence@v1`.
- **Classification**: SUP.1 (Quality Assurance)
- **Status**: `candidate-approved`

### `REQ-PROC-AE-02` — Exact Baseline Identification
- **Statement**: Completion evidence SHALL identify the exact pre-change baseline (commit/branch) and the exact candidate against which it was produced.
- **Source Link**: `TODO.md` header (`AE-2`) / `AGENTS.md`
- **Supersession History**: Derived directly from legacy inline marker `adversarial-completion-evidence@v1`.
- **Classification**: SUP.1 / SUP.8
- **Status**: `candidate-approved`

### `REQ-PROC-AE-03` — Falsification Case
- **Statement**: The evidence SHALL name at least one falsification case derived from the changed contract, demonstrating it failing (red) on the pre-change baseline and passing (green) on the candidate.
- **Source Link**: `TODO.md` header (`AE-3`) / `AGENTS.md`
- **Supersession History**: Derived directly from legacy inline marker `adversarial-completion-evidence@v1`.
- **Classification**: SWE.6 (Qualification Testing)
- **Status**: `candidate-approved`

### `REQ-PROC-AE-04` — Adjacent Boundary Cases
- **Statement**: The evidence SHALL name at least two distinct adjacent contract cases, identifying the neighboring dimension, expected result, observed result, and the reason for adjacency.
- **Source Link**: `TODO.md` header (`AE-4`) / `AGENTS.md`
- **Supersession History**: Derived directly from legacy inline marker `adversarial-completion-evidence@v1`.
- **Classification**: SWE.6 (Qualification Testing)
- **Status**: `candidate-approved`

### `REQ-PROC-AE-05` — Set and Sequence Property Evidence
- **Statement**: When claiming an invariant over a set or sequence, the evidence SHALL include a generative or exhaustive property test naming its invariant/oracle, generation domain, seed/replay input, and executed case count.
- **Source Link**: `TODO.md` header (`AE-5`) / `AGENTS.md`
- **Supersession History**: Derived directly from legacy inline marker `adversarial-completion-evidence@v1`.
- **Classification**: SWE.6 (Qualification Testing)
- **Status**: `candidate-approved`

## Batch 2: Agent Isolation Constraints (Pipeline Tooling)

The following requirements govern the execution isolation of the `agent-inbox` tooling and worktrees.

### `REQ-TOOL-ISO-01` — Worktree Isolation
- **Statement**: Agent processes mutating repository state MUST execute their changes within dedicated, item-owned Git worktrees, isolated from the `main` branch.
- **Source Link**: `branch-workflow.md`, implicit `run.sh` behavior.
- **Supersession History**: Extracted from scattered process documentation.
- **Classification**: SUP.8 (Configuration Management Tooling)
- **Status**: `candidate-approved`

### `REQ-TOOL-ISO-02` — Inbox Message Immutability
- **Statement**: Messages delivered to an agent's inbox SHALL NOT constitute proof of authority, ownership, or acceptance; they are strictly asynchronous coordination signals.
- **Source Link**: `AGENTS.md` (Mailbox discipline).
- **Supersession History**: Extracted from persona prompts and system instructions.
- **Classification**: MAN.3 (Project Management Tooling)
- **Status**: `candidate-approved`

---
*Note: Migration of further batches (e.g., specific JSON schema validation rules into detailed design records) will follow in subsequent iterations under feature `0013`.*
