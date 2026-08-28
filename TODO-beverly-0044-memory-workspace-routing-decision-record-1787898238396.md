# Claim: record Management option A as `DEC-0044-029`

item_id: 0044-memory-workspace-routing-decision-record
request_id: 1787898238396
owner_token: agent:beverly:0044-memory-workspace-routing-decision-record:1787898238396
base_commit: 7d6d71475796d3afdacff585d25059e2059e73b3
capability_class: unprivileged
execution_authority: direct
startup_review: AGENTS.md; SANDBOX.md; docs/pipeline/roles/requirements-engineer.md; docs/pipeline/core-rules.md; docs/pipeline/decision-record.md
state: [p]
write_scopes: ["TODO-beverly-0044-memory-workspace-routing-decision-record-1787898238396.md", "docs/dossiers/dec-0044-029-memory-workspace-routing.md"]

## Assignment and provenance

- Project Lead AWARD: `agent-inbox:1787898238396-26164e3d`.
- Management decision authority: `agent-inbox:1787898060256-d1495823`.
- Originating decision request: `agent-inbox:1787894015952-201f6995`.
- Supporting Tuvok evidence reference: `agent-inbox:1787893973173-8df13a51`; mailbox prose will not be copied into the record.
- Exact baseline: `main@7d6d71475796d3afdacff585d25059e2059e73b3`.
- Identifier allocation check: `DEC-0044-029` was absent at the exact baseline immediately before branch creation; `DEC-0044-028` was the highest allocated `DEC-0044-*` identifier.

## Intended write scope

- `TODO-beverly-0044-memory-workspace-routing-decision-record-1787898238396.md`
- `docs/dossiers/dec-0044-029-memory-workspace-routing.md`

## Constraints and assumptions

- Record Management-selected option A exactly: the `memory_append` hold remains; default or shared-root routing must become impossible and fail closed before writes may resume.
- This package records the decision only. It does not implement, activate, review, accept, integrate, or advance `main`.
- Cross-item tool, profile, instruction, or gate mutation remains blocked until a distinct Management-instantiated Architect supplies the required scope review.
- Existing root and `logs/agent-memory/**` divergence is preserved untouched. No `memory_append` or helper append call is permitted.
- Prohibited paths include `AGENTS.md`, `SANDBOX.md`, `TODO.md`, `DONE.md`, `docs/pipeline/**`, tool/profile files, and memory files.

## Progress

- Awarded branch and worktree were created from the exact baseline.
- Claim-first commit is the next required lifecycle step.

## Next step

Commit this claim alone, then author and validate the conforming `decision-record@v1` within the remaining awarded path.
