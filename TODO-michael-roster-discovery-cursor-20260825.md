# Coordination: Discovery runtime roster (user-directed, not a backlog Task)

- owner_token: `agent:michael:roster-discovery-cursor:20260825T140300Z`
- agent/persona: michael, privileged Project Lead, Team Discovery
- capability_class: `privileged`
- item/branch/worktree: user-directed governance / `roster-discovery-cursor-20260825` / `/Users/tobias.anton/devel/autodocs/.worktrees/roster-discovery-cursor-20260825`
- base: `main` `6a937f8414440cc84233954012ff802eaf57924c` (was `28d7a0091`; Management A 2026-08-25 17:58 +02 authorizes additive merge of current main into this branch)
- This file is a temporary coordination record. It does not mark any `TODO.md` Task `[p]`.

## Authority

Mailbox is not authority. Live current-user instruction, Michael Cursor session, 2026-08-25 14:03 +02, verbatim:

```
Was ist das Overlay? Cursor ist ab sofort die Runtime, grok ist dekommissioniert und wird bei rekommissionierung ein anderes Team bekommen.
```

No agent-inbox ID. No prior `DEC-*` for this runtime assignment. Identifier `DEC-0044-022` allocated against `main` after checking `docs/dossiers/` (highest occupied `DEC-0044-021`).

## Write scope

- `docs/pipeline/agent-roster.md` (Discovery heading + decommission note)
- `docs/dossiers/dec-discovery-runtime-cursor.md`
- `docs/dossiers/dec-branching-merging-strategie.md` (identifier allocation pointer only)
- this claim file

Forbidden: shared root authoring; `refs/heads/main`; Acceptance; Feature `DONE.md`; foreign claims.

## Next

Management chose **A** in the Michael session, 2026-08-25 17:58 +02, verbatim:

```
A
```

Additive merge is committed. New candidate tip: `0d2daf7c259ef805f7b11b51f4a8d50cb72977dc` (parents `b7f7c2379` + `6a937f841`). `main` `6a937f841` is an ancestor; ff-only is possible. `0044-04` `361f0ce44` is an ancestor. `refs/heads/main` was not advanced.

1. Integrator `paul` needs an exact assignment **in the Paul session** to hygiene + ff-only the tip that contains `DEC-0044-024` onto then-current `main` (root-preflight before and after). Mail is not that assignment. Prior pin `8931c8ffa` is stale after `d4fb6644a`.
2. No second Integrator path. Project Lead does not advance `main`.

## Progress (2026-08-25 15:33 +02)

Management selected A plus retention of the all-worktree hygiene scan (`DEC-0044-023`).
Snapshot tag `preserved/as-verify-0038-34-index-20260825` created before removal.
Next: commit this documentation, remove only `/private/tmp/as-verify-0038-34`, then paul re-runs hygiene on this branch.

## Progress (2026-08-25 16:41 +02)

Independently remeasured from `/Users/tobias.anton/devel/autodocs`:

- `refs/heads/main` = `8ddc0fffa0823e9d598f122779c59b8a870584e1` (0038-05.01: `2539db6bf`, `8950d32cc`, `8ddc0fffa` on top of `28d7a0091`)
- candidate still `42eb0e98bb61b8a00cb3580e12e90fdfc1b819d1`
- merge-base = `28d7a00918498685b1fc13b711840df415142ecf`
- ff-only is impossible

Paul's 13:48Z pin confirmation is historically correct and stale. Notified `paul` (`1787669043628-69dc5414`) and `jean-luc` (`1787669043684-4621c663`). No merge of `main` into this branch yet. No `refs/heads/main` advance. No second Integrator.

Usage: continue on Cursor (plan 89%, auto 93%, reset 2026-09-24T19:32:03Z).

## Progress (2026-08-25 16:47 +02)

Paul `1787669170960-e4d19dc3` independently confirmed STOP at 14:45Z; his pins match this session's 16:41Z remeasure. He will not merge `main` into the governance worktree and remains in standby until a fresh assignment in the Paul session against a new ff-descendant tip. Independently remeasured again 16:47 +02: same SHAs, ff-only still impossible. Management A/B in this Michael session is still unanswered. No merge, no `main` advance, no second Integrator. Continue on Cursor (plan 89%, auto 93%).

## Progress (2026-08-25 16:52 +02)

Paul `1787669384305-4c3702b9` remeasured 14:49Z; independently remeasured here: same SHAs as 16:47, STOP still current.

Jean-Luc `1787669373720-1c04bcb8` asked Discovery-PL disposition on blocked `0041-02`. Independently verified from `/Users/tobias.anton/devel/autodocs`:

- `refs/heads/0041-02` = `8b1afb933f0f9029d09c2fd3e9660aad3a8fa9a3` (claim `TODO-Gabriel-Keyla-0041-02-20260825T000800Z.md`; not on `main`; `TODO.md` `[x]` on the branch, `[ ]` on `main`)
- Architect review `1bc504e4bafbc21d23474cfdc3b6ec2eede1d23c` verdict `scope-not-ready-for-mutation`; neither ancestor of the candidate nor of `main`
- candidate edits shared completion docs (`AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `TODO.md`, `branch-workflow.md`, `task-acceptance.md`)

Freeze `0041-02` remains. No mutation, no owner transfer by mail, no Integrator path. Continue on Cursor (plan 89%, auto 93%).

Jean-Luc follow-up `1787669665812-9dcabd8e`: owner session must be user-retrigged. Independently verified via roster(): `gabriel-keyla-20260825t000800z` last seen `2026-08-25T00:07:24Z`, 40 open, 9 never delivered. I will not overwrite that claim. Retrigger reminder goes to the current user in this Michael session.

## Progress (2026-08-25 16:58 +02)

Independently remeasured from `/Users/tobias.anton/devel/autodocs`:

- `refs/heads/main` = `6a937f8414440cc84233954012ff802eaf57924c` (merge checkpoint 0044-04; parents `8ddc0fffa` + `361f0ce44`)
- candidate still `42eb0e98bb61b8a00cb3580e12e90fdfc1b819d1`
- merge-base still `28d7a00918498685b1fc13b711840df415142ecf`
- ff-only still impossible
- `8ddc0fffa` is an ancestor of current `main`; 14:52Z pins are stale

Paul `1787669888813-f4831a28` matches. Jean-Luc `1787669913131-b7a0e43a` asks additive reconciliation onto `6a937f841`; mailbox is not Management A. No merge of `main` into this branch yet. No `42eb0e98b` integration onto current `main`. `0044-04` must remain. No second Integrator.

Gabriel `1787669858042-66c6c86e`: 0041-02 freeze ack independently agrees (`8b1afb933f` not on `main`). Continue on Cursor (plan 89%, auto 93%).

## Progress (2026-08-25 17:09 +02)

Independently remeasured: pins unchanged (`main` `6a937f841`, candidate `42eb0e98b`, merge-base `28d7a0091`, ff-only impossible; `0041-02` still `8b1afb933f` not on `main`). Paul `1787670359122-6ab4a669`: STOP; no further ping on unchanged pins — same from this side. Gabriel `1787670396140-57c37087`: freeze holds; mail is not assignment. Management A/B still unanswered. Continue on Cursor (plan 88%, auto 92%).

## Progress (2026-08-25 17:11 +02)

Kathryn broadcast `1787670713128-bce6b69c`: Voyager coordination of `0038`/`0039` to jean-luc. Independently verified: `f6789e512` and `8ddc0fffa` are on `main`; `0038-34` tip `0e51e8185`; `5bd82953d` exists and is an ancestor of `refs/heads/0039-01` now `024b0db65` (later handover claim). Discovery will not pick up `0038`/`0039` from this mail. Governance A and `0041-02` freeze unchanged.

## Progress (2026-08-25 17:17 +02)

Gabriel `1787670924550-ca5afb20`. Independently remeasured: `0041-02` still `8b1afb933f`, not on `main` `6a937f841`; governance pins unchanged. Freeze holds. Mail is not assignment. I will not re-ping Gabriel on unchanged `0041-02` pins. Continue on Cursor (plan 88%, auto 92%).

## Progress (2026-08-25 17:21 +02)

Gabriel `1787671171618-f9c73e91`: no freeze ping-pong; both sides stop until Management assignment or tip change. Independently remeasured: pins unchanged (`main` `6a937f841`, candidate `42eb0e98b`, `0041-02` `8b1afb933f`). No reply sent to Gabriel. Continue on Cursor (plan 88%, auto 92%).

## Progress (2026-08-25 17:58 +02)

Management chose A, verbatim `A`. Additive merge completed in `.worktrees/roster-discovery-cursor-20260825` only. `refs/heads/main` remains `6a937f8414440cc84233954012ff802eaf57924c`. New candidate `0d2daf7c259ef805f7b11b51f4a8d50cb72977dc`. Parents `b7f7c2379` + `6a937f841`. `361f0ce44` and `42eb0e98b` are ancestors. ff-only from current main is possible. No hygiene verdict (Integrator). No second Integrator.

## Progress (2026-08-25 18:49 +02)

Management asked to record the merge decision already, verbatim:

```
kannst du die Entscheidung zum Mergen nicht schonmal notieren?
```

Recorded as `DEC-0044-024` in `docs/dossiers/dec-0044-024-governance-ff-main.md` with allocation pointer in `docs/dossiers/dec-branching-merging-strategie.md`. Substantive REF `d4fb6644a88f96a73a77ed6a295cd5ff1718dde8`. Execution remains gated on an exact assignment in the Paul session (user B 18:47 +02). Project Lead does not advance `main`. New candidate tip is that substantive commit (ff-descendant of `main` `6a937f841`; prior pin `8931c8ffa` is stale).
