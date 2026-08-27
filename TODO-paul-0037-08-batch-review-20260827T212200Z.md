# Review claim — 0037-08 prerequisite-closed Task-Acceptance batch (not implementation)

## Claim identity

task_id: 0037-08 (batch: 0037-07, 0037-39, 0037-08; induced unaccepted predecessors 0037-49, 0037-51 recorded)
request_id: 20260827T212200Z
owner_token: agent:paul:0037-08:20260827T212200Z
base_commit: f3f17f66f5e18177ce779b356a8ff8b0a8399afb
capability_class: privileged
execution_authority: direct
startup_review: SANDBOX.md, AGENTS.md, docs/pipeline/task-acceptance.md reviewed
state: [p]
write_scope:
  - TODO-paul-0037-08-batch-review-20260827T212200Z.md
  - docs/campaign-evidence/review-0037-08-batch-paul-20260827T212200Z/

## Assignment

ACCEPT of michael OFFER `1787865569072-75488504` (mail `1787865848802-c87f5fc3`). HOLD `1787865353401-bcdda30e` superseded. Feature owner kathryn named the batch (`1787865367689-62983ff2`). Kathryn later named a widening (`1787865936760-b24fa074`) to include 0037-49 and 0037-51 in AWARD write scope; forwarded to michael `1787865981845-fcd4ca6f`. ACCEPT is not the award. No `Acceptance: ✓` on `TODO.md` until explicit AWARD from michael.

Exact baseline: `main@f3f17f66f5e18177ce779b356a8ff8b0a8399afb`. Work already on main. Pin named REFs; do not review unrelated branch-vs-main history.

## Pins (all ancestors of the baseline)

- 0037-02 accepted baseline: `91a4b99fb07948cdea4c71d18ada49f4d661ea42` (verify-only; belanna)
- 0037-07 approval: `b4f03bf88c6d8b1adb45f29b10c27974cb8dfdf1`
- 0037-07 integration: `2f83441870936cfce1236fa4d549d6eac3afff45`
- 0037-07 branch tip named in OFFER: `5b941d1a5aa0acf1aee36a885dac9f8ba2726b1a`
- 0037-39 product: `7dcaf135c4323bf9f566baa2d9739e02c43bf0be`
- 0037-39 bookkeeping: `b092d59356aabc6e699399a3a9b92c7cca609b5a`
- 0037-08 product: `4376be766decd03830a5feeec7dcc6b41cfd87ce`
- 0037-08 bookkeeping: `15b50c7c0b4943b12cf703a7f9b612bb3388d948`

## Independence

Not Julian (08/39). Not Seven-Icheb (07). Not jean-luc (51). Not 0037-09.03 re-award. No waiver.

## Must not

- Feature 0037 → `DONE.md`
- mutate `0037-16`
- merge `0037-28`
- claim `0039-01`
- take `0037-09.01`
- spawn; overwrite foreign claims
- rewrite 0037-02 Acceptance
- advance `refs/heads/main` from this worktree
- write `Acceptance: ✓` before explicit AWARD

## Closure preflight

- 0037-37: current `Acceptance: ✓` (sub-bullet line 958). Boundary.
- 0038-15: current `Acceptance: ✓` (sub-bullet line 729). Boundary.
- 0037-49: `[x]`, no `Acceptance: ✓`. Required predecessor of 0037-07. Outside post-AWARD bookkeeping write scope unless AWARD widens.
- 0037-51: `[x]`, no `Acceptance: ✓`. Required predecessor of 0037-39. Outside post-AWARD bookkeeping write scope unless AWARD widens.

## Next step

Evidence drafted at `docs/campaign-evidence/review-0037-08-batch-paul-20260827T212200Z/decision.md`. Work products for 49/51/07/39/08 accepted vs contract. Do not add `Acceptance: ✓` until explicit AWARD. Await michael amend/AWARD including 0037-49 and 0037-51.
