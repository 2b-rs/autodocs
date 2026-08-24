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
- status: implementation complete; validated; committed
- substantive_ref: `3f9aa330f0085dba87e5701dafbcc51c667c835e`

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

## Re-review correction round

- rejected re-review: `a3d6e1e8817910676b647d90c82d79d7c2c08bbc`
  (final review tip `1728db9d4b3f65fa4765584264137eb26ceff820`)
- controlling Runner amendment: `5d5996d07d8e8be71a99722a12e3afcb1d57919a`
  (actual amendment tip `b38c3202d0d40812733204d4386388ff73234599`)
- Runner correction: A.4 repurposed as shared role/job-control contract and
  intermediate mandatory checkpoint; search grammar consolidated into A.3;
  all enumerated background consumers now require current Acceptance of A.4
- migration correction: N.1–N.3 now write collision-free `src/import/**`
  package roots and start behind E.T; `_src/import/**` is absent
- executability correction: all 77 overlay rows now carry a unique package-ID
  command/result, collision-free write/evidence manifest, named recovery target,
  bounded CPU/memory/time/test/cognitive/uncertainty/risk estimate, and
  deterministic branch/merge target
- prior gate and exact trace corrections retained
- validation: `git diff --check`; 16 Features; 77 unique packages and validation
  contracts; 16 terminals; A.4 intermediate checkpoint; 24 Q IDs; no stale
  `_src/import`, generic overlay templates, `sg`, runner queue or `Cap:` literal
- re_review_correction_ref: `7aeedacd6405b63023d89cefb9bf149cc349978c`
- status: re-review findings corrected, validated and committed

## Second re-review correction round

- rejected second re-review:
  `6b8a81ff1171127a95b44795bd4d1852df4ffe7b` (final review tip
  `73f2008a1540140ebd4e5148bdd0f7ee444d9db0`), candidate
  `5651bff97596dde165ae09555b7374ea086f3988`
- A.4 manifest now owns the named operational-role/background-job contracts,
  schemas and fixtures; public types, error behavior, compatibility and recovery
  are normative and consumer edges bind exact contract digests
- all 77 packages own their validation harness under their own test root; the
  unowned global validator dependency is removed
- all 16 terminals own their validation harness, fixtures, contract and write
  manifest inside their normative manifest
- all 77 branch targets use the exact allocated item-ID branch and exact parent
  item branch; Task→Feature and Subtask→Task topology is explicit and extra
  prefixes/aliases are rejected
- malformed `+##` overlay heading corrected
- F-N migration, A.4 lifecycle/checkpoint/consumer gates and exact trace/gate
  sections retained
- validation: `git diff --check`; 77 unique package-owned harnesses; 16 terminal
  owned contract/harness manifests; 77 exact item-ID/parent branch bindings;
  zero unowned global-validator, `feature/` branch-prefix, malformed heading or
  `_src/import` occurrence; A.4 shared outputs/types present
- status: second re-review findings corrected and validated; commit pending
