# Claim supplement — 0027-05 governance collision correction

- **owner_token:** `agent:data:0027-05:20260828T081812Z-2afa2a68`
- **state:** `[x]`
- **capability_class:** `privileged`
- **role:** management-instantiated Architect; correction author only
- **authority:** `agent-inbox:1787906519329-e38ca275`, deterministic Project Lead direction after independent review `e4d6b34757950962040628d8c1e3974bf05dd91e`
- **base:** `main@c27b8001fcd7b6a504aaf7fe36c481711d5e9d81`
- **branch/worktree:** `gov-0027-05-dec-0027-002-data-20260828` / `/Users/tobias.anton/devel/autodocs/.worktrees/gov-0027-05-dec-0027-002-data-20260828`
- **write scope:** this claim; `docs/dossiers/dec-0027-002-sup8-package-and-gates.md`; `docs/campaign-evidence/0027-05/dec-0027-002-review-impact.md`
- **must not:** integrate the abandoned duplicate dossier, mutate backlog/interfaces, implement, produce ECU evidence, perform Acceptance/integration, advance `main`, clean foreign state, or write Memory

## Correction contract

Retain the earlier MAN.3 allocation as `DEC-0027-001`. Reissue the later SUP.8
decision as collision-free `DEC-0027-002`, preserving the abandoned
`897487036:docs/dossiers/dec-0027-001-sup8-package-and-gates.md` identity only
as append-only provenance. Treat `0027-11` as the single terminal Feature
integration Task already allocated by MAN.3; SUP.8 contributes prerequisites,
checkpoint constraints, and consumer requirements to that one reconciled
contract and does not allocate a second Task.

No gate is activated by this correction. The exact candidate returns for
scope-review currency assessment and separately assigned governance integration.

## Completion evidence

- Claim-first REF: `a1b17ec2d5a6d1eb7db0d9a3c229cb39b6a1fcab`.
- Substantive REF: `499ed11b970a682a8e18def16908a679746b30ad`.
- Corrected record is `DEC-0027-002`; current `main` and all pre-existing refs
  had no `dec-0027-002-sup8-package-and-gates.md` allocation before this commit.
- The abandoned duplicate dossier path is absent from the candidate tree.
- `git diff --check`: pass.
- `process_doc_doctor.py --json`: `ok=true`; one unrelated pre-existing
  `DOC001` error and 34 total findings remain.
- **handoff:** exact candidate returns to Project Lead for review-currency
  assessment and separately assigned governance integration. No backlog or
  interface mutation is authorized by this completion.
