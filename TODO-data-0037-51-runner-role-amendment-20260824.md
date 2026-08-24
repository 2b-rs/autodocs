# Architect amendment claim — 0037-51 Runner role

- **Item:** `0037-51-runner-role-amendment-20260824`
- **Owner:** `data` (Architect, Team Enterprise)
- **owner_token:** `agent:data:0037-51-runner-role-amendment:20260824T102013Z`
- **Capability class:** `privileged`
- **Process role:** Architect; preparation and scope review only
- **Authority reference:** direct-user clarification recorded at `fa8d575f723b9905050c77df935cc7b55a8ebaa2` in `TODO-jean-luc-0037-51-20260824T072000Z.md`
- **Assignment source:** Project Lead `jean-luc`, mailbox thread `0037-51`, messages `1787566669522-d2e024d9` and `1787566813425-92cf5fd2`
- **Prior review baseline:** `9f4d3f6ee04389a77dc296ed21a85f918d75739d`
- **Branch:** `review-0037-51-runner-role-amendment-data-20260824`
- **Worktree:** `.review-worktrees/0037-51-runner-role-amendment-data-20260824`

## Assignment and boundary

Append an Architect clarification and impact review to `DEC-0037-002` and the
existing `0037-51` scope review. The direct user retired `sandboxed-grunt`
requirements and their special intermediates, but explicitly retained Runner as
a Dispatcher-selected role for Task-ID-bound long-running background jobs, job
control, and interfaces to other agents. Distinguish that role from the retired
singleton/queue/typed-action transport and report whether the prior verdict
remains valid.

This is not implementation, Task acceptance, an integration review, an
`Acceptance: ✓` action, checkpoint crossing, Feature closure, or external job
execution. The review changes no operative gate; it prepares the authority and
bounds that a distinct decomposition Architect/Implementer must later apply.

## Exact write scope

- `docs/dossiers/dec-0037-future-direct-execution.md`
- `docs/dossiers/0037-51-de-sandboxing-scope-review.md`
- `TODO-data-0037-51-runner-role-amendment-20260824.md`

Prohibited: `TODO.md`, `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`,
`agent-workflow.json`, `docs/pipeline/**`, runner code/configuration, selectors,
other claims, Acceptance records, integration refs, `main`, `DONE.md`, external
services, background jobs, pushes, and publication.

## Startup evidence and assumptions

- The assigned worktree did not yet exist; this session provisioned it from the
  exact prior review tip after verifying the durable authority REF.
- The shared-root hard preflight is not clean: the profile-mandated
  `memory_append` changed only `logs/agent-memory/roles/Architect.md`. The
  mandatory hygiene tool therefore reported `MAIN_WORKTREE_DIRTY` across 157
  worktrees. This review performs no integration or root cleanup; the eventual
  integrator must stop until that independently authorized root condition is
  resolved and the hygiene check passes.
- The user clarification is treated as a correction of the Architect's
  over-broad recording, not as permission to restore sandboxed execution or the
  retired runner transport.
- `Runner` is an operational role, not an execution capability class or an
  authority grant. In the future direct-execution model it maps normally to
  `unprivileged`; any Architect, Integrator, specialist, release, credential, or
  external-system authority remains separately assigned.

## Progress

- Read the prior decision and exhaustive scope review at `9f4d3f6ee`.
- Read the current Runner, Programmer, and Tester role surfaces and the affected
  Feature `0037` Task contracts.
- Derived an append-only correction set and delta review preserving the original
  transport-removal verdict while adding the Runner job-control interface,
  affected nodes, prerequisite rewiring, checkpoint rationale, activation,
  self-application, rollback, non-grandfathering, validation, and estimates.
- Appended six `decision-record-correction@v1` events, one per changed top-level
  field. Each event's previous-effective-block SHA-256 was independently
  recomputed from `9f4d3f6ee`; event IDs `C001`–`C006`, target labels,
  replacement fences, and the single-selected-alternative rule validate.
- Verified all 59 affected Task/Subtask references and all five affected role
  document paths against the pinned baseline.
- Simulated the amended normative prerequisite delta over 361 Task/Subtask
  nodes and 794 resulting edges: all endpoints exist and Kahn topological
  validation reports no cycle. The simulation adds ten reviewed edges and
  removes the superseded `0037-21:0038-16` edge.
- `process_doc_doctor.py --json` is byte-for-byte finding-equivalent to the
  `9f4d3f6ee` baseline: exit `0`, 120 documents, one existing error and 30 total
  findings, zero new and zero resolved. The existing error is the unrelated
  broken relative link in `docs/dossiers/0044-03-gate-scope-proposal.md`.
- `git diff --check` passes. The changed-path guard contains exactly the two
  assigned tracked dossiers plus this assigned untracked claim before commit.

## Next action

Review the final scoped diff, commit only the three assigned paths, report the
final REF to `jean-luc`, then acknowledge both assignment messages. No
integration is permitted while the recorded shared-root hygiene finding remains.
