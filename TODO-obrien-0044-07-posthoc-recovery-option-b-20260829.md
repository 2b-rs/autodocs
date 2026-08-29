---
item: 0044-07-posthoc-recovery-option-b
task: 0044-07-posthoc-recovery-option-b
owner: obrien
owner_token: agent:obrien:0044-07-posthoc-recovery-option-b:20260829
capability_class: privileged
write_scope:
  - docs/pipeline/branch-workflow.md
  - TODO-jadzia-0011-03-chain-20260829.md
  - TODO-jadzia-0011-04-chain-20260829.md
  - docs/dossiers/0044-07-posthoc-recovery-option-b.md
  - docs/campaign-evidence/0044-07/posthoc-recovery-option-b-obrien-20260829.md
  - TODO-obrien-0044-07-posthoc-recovery-option-b-20260829.md
---

## Contract
Execute 0044-07 post-hoc recovery Option B under decision-1788015759354-013fa663 and decision-1788011983733-189cac2b (rework iteration 1 offer 1788043981549-534fe085):
- Reconstruct preserved snapshot commits and tags for cleared Jadzia root claim edits (`preserved/root-jadzia-claim-edits-20260829-obrien`), cleared zero-byte sparse checkout artifacts (`preserved/staged-0044-07-zero-byte-artifacts-20260829-obrien`), and unbranched Jadzia 0011 claim states (`preserved/root-jadzia-0011-claim-edits-20260829-obrien`).
- Update preserved-snapshot registry in `docs/pipeline/branch-workflow.md`.
- Append-only revert 34341f89 changes on `TODO-jadzia-0011-03-chain-20260829.md` and `TODO-jadzia-0011-04-chain-20260829.md`.
- Update dossier and campaign evidence.
- Verify hygiene, document doctor, diff check, and execute ff-only merge to main.

- **state**: Terminal (Recovery completed and verified, handed over to Jean-Luc)
