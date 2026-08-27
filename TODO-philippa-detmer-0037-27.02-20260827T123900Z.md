# Claim `0037-27.02`

- owner_token: `agent:philippa-detmer-0037-27.02:0037-27.02:20260827T123900Z`
- agent_id: philippa-detmer-0037-27.02
- capability_class: unprivileged
- execution_authority: direct tools; no runner; no Acceptance; no checkpoint; no main; no DONE.md
- item: 0037-27.02
- branch: 0037-27.02
- worktree: `/Users/tobias.anton/devel/autodocs/.worktrees/0037-27.02`
- base: `0037-19` @ `2064704457f98c66fb6f77ad3c263415864fe2ff` (R2 ancestor `cfa4b8f2c` confirmed)
- merged_prereq_tips: `0037-17` already ancestor of `0037-19` (`78f1e3fd2a74e4dab5a6c8fe150ab69384715157`); no extra merge
- write_scope: `_src/tools/diagram_provenance.py`; `_src/render_diagrams.py`; `_src/i18n_diagrams.py`; `_src/tests/test_diagram_provenance.py`; `_src/tests/fixtures/diagram_provenance/`; this claim; `TODO.md` 0037-27.02 block only
- startup_review: R2 baseline valid; 0037-17 in 0037-19; 0037-27.01 not a start prereq

## Task (verbatim)

Extend diagram source and rendered SVG workflows with manifests and common provenance.

Acceptance criteria: Record source model/labels/theme/tool/config, issue/criterion/run, rendered artifact digest, language, invalidation/regeneration relation, and source-to-SVG members; do not inject uncontrolled provenance into SVG markup.

Definition of Done: Source/label/theme changes mark exact SVGs stale, regeneration links replacements, and queries trace canonical and translated diagrams bidirectionally.

## Progress

- 2026-08-27: claimed; implemented diagram-provenance@v1 workflow + renderer hooks (env-gated, no SVG injection).
- 2026-08-27: implementation complete `[x]`. Product REF `9c4b59780da477aa714b4cbcf168e4df48843d64`. Tests 10/10. AE evidence PASS.
- 2026-08-27: additive schema-bind follow-up (do not amend `9c4b59780`): writers validate against the five `provenance/_schema` files via `validate_against_bound_schema` (0037-26.01@45ef86d54 pattern). Extra-field reject `DP-SCHEMA-DEVIATION`.
