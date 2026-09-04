# Integration claim — DEC-0037-008

- **owner_token:** `agent:geordi:0037-cutover-dec-0037-008-integration:1788441501278-0c2f6f6e`
- **assignment:** atomic award `1788441501278-0c2f6f6e`
- **capability / role:** `privileged` / independent Integrator
- **state:** `[x]`
- **worktree:** `/tmp/autodocs-worktrees/0037-cutover-dec-0037-008-geordi`
- **branch:** `integrate-dec-0037-008-geordi-20260903`
- **target baseline:** `main@1dbbc9cb6379dd41d72f811df06300574d53a8cf`
- **implementation candidate:** `09d63be542ca341d47e33f69cadc99aa5a0f7ed5`
- **fresh aggregate before claim:** `cc854792e82f1ee21481c700d35ff91a9e1e1144`
- **write scope:** the two `DEC-0037-008` dossier files and this claim only
- **execution scope:** independent review, candidate hygiene, guarded root merge, and canonical integration receipt; no push
- **external resources:** none

## Review and progress

- Candidate commit changes exactly the two authorized dossier files and is based on `db0a66f92e0630738844b8087b9907d564d9f6e3`.
- Fresh no-ff aggregate changes exactly the two authorized product paths without conflict; `git diff --check` passes.
- Both pinned findings blobs and SHA-256 digests match `51be4db07c26bf48aa1eb00ff8cdbcea8fc81b45`; independently counted finding families total 910 and 911 exactly as recorded.
- Decision-record envelope and companion Architect `SUPPORT` artifact were reviewed. The reviewer identity is distinct from Task `0037-29`'s Implementer; the artifact claims no Acceptance or integration authority.
- Candidate hygiene stopped with exit `2`: registered available worktree `/private/tmp/dec-0037-008-saru-20260903` has no common-dir index at `.git/worktrees/dec-0037-008-saru-20260903/index`. Foreign cleanup is not authorized.
- **Incident:** the initial compound command ran `git worktree add ... && git merge ...` with the root checkout as its shell working directory. Creating the worktree did not change the shell working directory, so after checkout completed the second command accidentally merged candidate `09d63be542ca341d47e33f69cadc99aa5a0f7ed5` in the root checkout. Root merge `7c9e228c4c1215eeaf4f2aaeb50672a518267ab7` was created at `2026-09-03T15:20:23+02:00`, from `78b5a8c9e191682c587676b368cc58e00d8b60a7`, without the mandatory candidate hygiene PASS or immediate root preflight. It is an ancestor of current `main@323275c7d05c5bbed88852c3e7fe8483ad005aae`; this claim commit is not. No rollback, cleanup, Acceptance, or validity is inferred.

## Boundary

No `TODO.md`/`DONE.md` mutation, Task Acceptance, `0037` marker change,
importer/runtime change, external effect, Feature closure, waiver, push, or ref
deletion is authorized. A non-zero hygiene result is a stop.

## Forward Qualification & Incident Recovery

- **Recovery Authority:** Management resolution `decision-1788441923781-ff7846f7` selecting Option `forward_qualification` (Record: `logs/agent-inbox/decision-requests/decision-1788441923781-ff7846f7.json`).
- **Assignment:** Award `1788442040784-2c0677c7` to independent Integrator `obrien` (Miles O'Brien, Team DeepSpace9).
- **Terminal State:** `[x]` — Forward qualification complete. Original un-gated pre-merge evidence is not retroactively claimed as passed; forward qualification evidence is permanently recorded in `docs/dossiers/dec-0037-008-integration-incident-qualification.md`.
