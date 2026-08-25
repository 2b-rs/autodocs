# Architect coordination record — Feature `0038` terminal integration restoration

item: 0038-terminal-integration-architecture
owner: data
owner_token: agent:data:0038-terminal-integration:20260825T192007Z-6d7f42a9
status: [p]
capability_class: privileged
process_role: Architect
authority_reference: `DEC-0038-005` on `main@96e7a8b71a75773fd2f7193245792243e704a574`
branch: gov-0038-terminal-integration-data-20260825-r2
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0038-terminal-integration-data-20260825-r2
base: 96e7a8b71a75773fd2f7193245792243e704a574
write_scope: `TODO.md`; `docs/campaign-evidence/0038-35/architect-terminal-integration-contract.md`; this record

## Purpose and separation

Translate the repository owner's `DEC-0038-005` selection into exactly one
terminal integrating Task for Feature `0038`. This Architect package defines
scope, prerequisites, review batches, evidence, ordering, capability profiles,
and closure boundaries only.

Data does not implement `0038-35`, review or accept any Task, issue an
integration verdict, move Feature `0038` to `DONE.md`, advance `main`, or alter
the historical partial-integration approval and R-6 record. The Task
Implementer, fresh structured reviewers, and terminal Integrator are distinct
identities under the contract evidence.

## Startup evidence

- The first pre-authority worktree remained clean and unmodified.
- `DEC-0038-005` was integrated ff-only and independently remeasured as exact
  `main@96e7a8b71a75773fd2f7193245792243e704a574` before this r2 worktree was
  created.
- The decision is the unique `DEC-0038-005` heading on this baseline and grants
  architecture/decomposition authority only.
- Existing `docs/pipeline/approvals/0038-main-integration-20260821T000000Z.md`
  and its R-6 no-closure finding remain append-only history.

## Next action

Commit the smallest Task/scope candidate, validate IDs, prerequisite endpoints,
cycles, exact-one terminal integrating Task, whitespace, and historical-file
non-modification, then hand the exact candidate to a separately assigned
privileged Integrator. Do not implement or close `0038-35` in this claim.
