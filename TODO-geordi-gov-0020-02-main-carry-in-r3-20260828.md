# Integration claim — `DEC-0020-002` governance carry-in R3

- **item_id:** `gov-0020-02-main-carry-in-r3`
- **owner_token:** `agent:geordi:gov-0020-02-main-carry-in-r3:1787916093967-82946dd2`
- **state / status:** `[p]` / `[p]`
- **capability_class / role:** `privileged` / independent Integrator
- **execution_authority:** exact two-blob assembly, independent integration review, required hygiene/preflights, and conditional governed root merge only
- **planned_duration:** 30 minutes
- **branch:** `integrate-gov-0020-02-geordi-r3-20260828`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/integrate-gov-0020-02-geordi-r3-20260828`
- **target baseline:** `main@e38a688c56f01fd3d8ab825593ee899ea0c7b4f2`
- **source review:** `c90b7b677ff57bae9e05a31bce7531930674210d`
- **exact blobs:** `docs/dossiers/dec-0020-02-evidence-boundary-enforcement.md@da4242a865aede7fa567c0a37ffc740b4ce24d7f`; `docs/dossiers/0020-02-gate-scope-review.md@1717e89262c557fda6fd5a86094d59f33a8a7351`
- **authority:** atomic AWARD `agent-inbox:1787916093967-82946dd2` from Project Lead `jean-luc`; recovery receipt `agent-inbox:1787915902389-e7cb4037`
- **preserved predecessor evidence:** R2 PASS `1bac6b6ab48f0f3f2b7619cd717001b41d4275e0`; R2 BLOCKED verdict `152196a92c5dd3cb2fd3906f4791a5b067004810`
- **write scope:** the two exact blobs and this fresh R3 claim; conditional governed root merge after PASS
- **prohibitions:** no TODO/product authoring, Acceptance, checkpoint verdict, other paths, cleanup, push/publication, external effect, or scope widening

## Integration contract

Prior R2 evidence remains append-only. Carry only the awarded two blobs; re-pin on main advance; stop on any collision, drift, unexpected path, or nonzero gate. No root action before a passing exact candidate hygiene and immediate root preflight.

## Independent R3 review

- **Pin and identity — PASS.** Current `main` re-measured exactly at `e38a688c56f01fd3d8ab825593ee899ea0c7b4f2`; both awarded paths were absent and the assembled tree has exactly one `DEC-0020-002` header.
- **Exact scope — PASS.** Carry `f37b5f13c36339a110371b664ab257dc4ab109e3` preserves the awarded decision and review blobs byte-for-byte; the R3 delta is only those two paths and this claim.
- **Decision/review consistency — PASS.** The decision and independent Architect review agree on refusal at named use/freeze consumers only, retain `docs/ASPICE` as informative, and forbid default shared validation or new start gates. No enforcement/product mutation is carried.
- **Provenance and documentation — PASS.** `check_policy_provenance.py` reports source-origin with the valid review-origin trailer and no finding. `git diff --check` passed. `process_doc_doctor.py` exited `0`, `ok: true`; its pre-existing broken `0044-03` link is outside the carried paths.
- **VERDICT: REVIEW PASS; READY FOR EXACT-CANDIDATE HYGIENE AND GOVERNED ROOT INTEGRATION.**
