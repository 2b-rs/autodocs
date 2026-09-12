---
item: 0020-10
task: 0020-10
owner: obrien
owner_token: agent:obrien:0020-10:1789246845218-408fcf7c
team: Team DeepSpace9
role: Integrator
capability_class: privileged
execution_authority: atomic priority award 1789246845218-408fcf7c / wake 1789246857626-fc3eb5bd
branch: 0020-10-obrien-20260912
worktree: /Users/tobias.anton/devel/autodocs
target_baseline: main@d339223f2
status: in_progress
state: in_progress
write_scope:
  - docs/dossiers/0020-terminal-integration-package.md
  - docs/dossiers/0020-terminal-integration-manifest.json
  - TODO-obrien-0020-10-integration-20260912.md
  - TODO.md
---

## Contract & Preflight Checklist

- **Task 0020-10:** Assemble and validate the terminal Feature 0020 integration package without changing the completed child products.
- **Scope & Manifesting:**
  - Manifest created: `docs/dossiers/0020-terminal-integration-manifest.json`.
  - Package report created: `docs/dossiers/0020-terminal-integration-package.md`.
  - Reconciles ECU scope (0020-01), evidence boundary (0020-02), responsibility matrix (0020-03), applicability matrix (0020-04), conditional applicability (0020-05), CS/FS applicability (0020-06), Level-1 worksheets (0020-07), evidence catalogue (0020-08), and execution register (0020-09).
- **Validation Evidence:**
  - JSON validation: `python3 -m json.tool docs/dossiers/0020-terminal-integration-manifest.json` -> PASS (valid JSON).
  - SHA-256 verification of child products -> PASS (all 9 digests verified).
  - `git diff --check` -> PASS.
