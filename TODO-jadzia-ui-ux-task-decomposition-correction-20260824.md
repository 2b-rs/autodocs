# Claim — UI/UX task-decomposition correction

- item_id: `ui-ux-task-decomposition-correction-20260824`
- owner: Architect `jadzia`, Team DeepSpace9
- owner_token: `agent:jadzia:ui-ux-task-decomposition-correction-20260824:20260824T143000CEST`
- capability_class: `privileged`
- execution_authority: direct Shell/Git within isolated item worktree; Architect correction only
- branch: `ui-ux-task-decomposition-correction-jadzia-20260824`
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/ui-ux-task-decomposition-correction-jadzia-20260824`
- base: `76d227ed73b48b0e48d66e585d0c5e0a13de1868`
- review: `1907ddc344ed775543da9aa6de3bd7be9ea4f752`
- management_runner_authority: `0037-51@fa8d575f723b9905050c77df935cc7b55a8ebaa2`
- data_runner_amendment_check: no newer durable REF than `9f4d3f6ee04389a77dc296ed21a85f918d75739d`; direct authority above is sufficient
- write_scope: `docs/design/ui-ux-task-decomposition.md`; this claim
- prohibited: backlog/governance/requirements/review mutation, ID allocation, Acceptance, checkpoint crossing, integration, main advance, Feature closure
- status: implementation complete; validated; pending commit

## Correction disposition

1. Retired sandboxed-grunt/runner-queue execution assumptions; retained Runner only as Dispatcher-selected Task-ID-bound long-job control/interface role.
2. Moved future UI writes to `src/**` and made E.T reachability/freeze mechanically normative.
3. Encoded acceptance, release and start gates as explicit graph edges with decision-record and distinct-Architect scope-review requirements.
4. Added a complete 77-row package-contract overlay for validation, evidence, recovery, resources, estimates and branch targets.
5. Added exact RQ ownership including RQ-012/013 and exact 119-view implementation/terminal ownership rules.

No Acceptance or integration decision is made by this claim.

## Validation

- `git diff --check`: pass
- structural counts: 16 Feature sections, 77 package bullets, 16 terminal
  bullets, 77 contract-overlay rows: pass
- retired execution scan (`Cap:`, `sg`, runner queue, downstream `_src/ui`,
  `_src/tools`, `_src/research`): zero stale occurrences
- exact trace rules: canonical RQ expansion covers 001..032; Q mapping covers
  Q-01..Q-24; view partitions expand to 119 IDs with one implementation owner
  and one terminal verifier by construction
- changed scope: only the decomposition and this claim
