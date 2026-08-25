# Architect coordination record — Feature `0038` terminal integration restoration

item: 0038-terminal-integration-architecture
owner: data
task_id: 0038-35
request_id: terminal-integration-20260825T192007Z-6d7f42a9
owner_token: agent:data:0038-35:terminal-integration-20260825T192007Z-6d7f42a9
base_commit: 6037b5febb36609f48580a9a797be618ddc27223
state: [ ]
architect_work_product_status: [x]
capability_class: privileged
process_role: Architect
authority_reference: `DEC-0038-005` on `main@96e7a8b71a75773fd2f7193245792243e704a574`
branch: gov-0038-terminal-integration-data-20260825-r2
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0038-terminal-integration-data-20260825-r2
base: 96e7a8b71a75773fd2f7193245792243e704a574
refreshed_base: 6037b5febb36609f48580a9a797be618ddc27223
write_scope: ["TODO.md", "docs/campaign-evidence/0038-35/architect-terminal-integration-contract.md", "TODO-data-0038-35-terminal-integration-20260825T192007Z-6d7f42a9.md"]

## Intended write scope

- `TODO.md`
- `docs/campaign-evidence/0038-35/architect-terminal-integration-contract.md`
- `TODO-data-0038-35-terminal-integration-20260825T192007Z-6d7f42a9.md`

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
- **Canonical identity correction:** the original noncanonical path
  `TODO-data-0038-terminal-integration-20260825T192007Z-6d7f42a9.md` and token
  `agent:data:0038-terminal-integration:20260825T192007Z-6d7f42a9` are preserved
  in Git history through bookkeeping tip `b19cb6cbb8`; the canonical identity
  retains the existing `terminal-integration-20260825T192007Z-6d7f42a9`
  request component and binds it to authoritative Task `0038-35`.

## Next action

Refreshed substantive candidate
`becef8b419fd10ff8c3110719209317823446283` is a two-parent additive merge of
prior corrected candidate `5503f49fb619a2fd97fbce7e60dddcd63bc77b2e`
and exact current `main@6037b5febb36609f48580a9a797be618ddc27223`.
Against that current `main`, the complete candidate changes exactly three
owned paths: this claim, the architecture contract, and `TODO.md`; the latter
has exactly seven inserted lines and no deletion, so all accepted `0044-05`
records are preserved byte-for-byte.

Canonical `legacy_task_doctor.py --root . --json` reports zero findings for
`0038-35` and zero unknown/duplicate/self/cycle/malformed prerequisite
findings; its 779 unrelated repository findings remain disclosed and out of
scope. Feature `0038` remains 39 unique nodes, with all other 38 named exactly
once by `0038-35`, no missing, extra, or self edge. `DEC-0038-005` remains one
unique heading. The protected partial-integration record retains SHA-256
`d45ade874c9e1a03367b2ffb64c0eb9334f4d09be3d34c0786be97617ee146bd`; the
architecture contract is byte-identical to the prior corrected candidate at
SHA-256
`7cbe8e4a18337b988ef7d39bd7ccf0ed7b37968c8146ac65336b04ba454bdf37`;
`git diff --check` passed. Hand only this refreshed exact candidate to a
separately assigned privileged Integrator. This claim performed no
implementation, Acceptance, integration, closure, or `main` advance.

### Prior corrected candidate (preserved history)

Corrected the independently rejected candidate at substantive REF
`705b249709e8c0f6a5a0f3577c73b46313ff2749`: the only Task-contract change is
the exact `(architect)` authority tag on `0038-35`'s mandatory checkpoint
rationale. Canonical `legacy_task_doctor.py --root . --json` now reports zero
findings for `0038-35` and zero unknown/duplicate/self/cycle/malformed
prerequisite findings; its 766 other repository findings remain disclosed and
out of scope. The Feature population remains 39 unique nodes, and `0038-35`
names the other 38 exactly once with no missing, extra, or self edge.

`DEC-0038-005` remains a unique heading. Main remains
`96e7a8b71a75773fd2f7193245792243e704a574`; the protected partial-integration
record remains byte-identical at SHA-256
`d45ade874c9e1a03367b2ffb64c0eb9334f4d09be3d34c0786be97617ee146bd`, and the
architecture contract remains byte-identical to rejected candidate `2b87ab0ce`
at SHA-256
`7cbe8e4a18337b988ef7d39bd7ccf0ed7b37968c8146ac65336b04ba454bdf37`.
`git diff --check` passed. Hand the corrected candidate to a separately
assigned privileged Integrator; this claim performed no implementation,
Acceptance, integration, closure, or `main` advance.
