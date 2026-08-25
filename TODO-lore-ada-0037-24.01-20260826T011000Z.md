# Claim: Subtask 0037-24.01

- owner_token: `agent:lore-ada-20260826t011000z:0037-24.01:20260826T011000Z`
- agent/persona: Lore-Ada-20260826T011000Z, unprivileged Programmer, Team Enterprise
- dispatcher: Lore (`/root` collaboration dispatch, 2026-08-26T01:10:00Z)
- capability_class: `unprivileged`
- execution_authority: direct local Git/Python in this dedicated item worktree; no runner queue
- item/branch/worktree: `0037-24.01` / `0037-24.01` / `/Users/tobias.anton/devel/autodocs/.worktrees/0037-24.01`
- Feature base: `118aeb64247dff3023c7904586e04cf523a8626a`
- startup_review: independently verified `0037-24.01` open, `0037-02` and `0037-23.01` `[x]`, no active claim/token/branch/worktree collision before creation
- prerequisites: `0037-02` and `0037-23.01` are already reachable from Feature base; exact `0037-23.01` tip `69ed6d7572fe6516867169280e79c3e471e53715` is an ancestor, so no done-but-unintegrated prerequisite merge is required
- exact_write_scope:
  - `_src/i18n_translate.py`
  - `_src/tests/test_issue_title_i18n.py`
  - `_src/tests/fixtures/issue-title-i18n/**`
  - `_src/i18n/{de,en,es,pt,fr,ru,ar,hi,ko,zh,nl}/issues.json`
  - `TODO-lore-ada-0037-24.01-20260826T011000Z.md`
  - `TODO.md` (0037-24.01 marker/claim/progress/REF only)
- external_resources: none; external translation is explicitly outside hermetic regeneration
- assumptions: public title extraction joins the sanitized public projection's allowlisted IDs/hashes to the internal generated catalog's canonical English title; configured output languages derive only from `_src/site.json`
- forbidden: Acceptance; review/integration verdict; mandatory checkpoint crossing; main advance; `DONE.md`; push; root-checkout mutation; any path outside exact scope; Wave 1A owner contact; work on `0037-10.02`, `0037-23.02`, `0037-11`, or held `0037-10.03`
- status: `[x]` implementation complete; product REF `386590183ebd742032b46f8c67274c498a2ddaa6`. Lease ended. No Acceptance.
- next_step: none for this token; privileged integration remains separate

## Task

Extend `_src/i18n_translate.py` extraction/split/merge/status for public issue titles stored in `_src/i18n/<lang>/issues.json`.

- **Acceptance criteria:** Key by item ID with canonical English `source_locale`, SHA-256 source-title hash, translated title, translator/run metadata, and status; include only `public-summary` titles; invalidate on source hash change; protect IDs/refs/code/placeholders; require canonical language plus every target in `_src/site.json`; reject duplicate/stale/wrong-item records. External human/model translation remains an authoring step, not part of hermetic regeneration.
- **Definition of Done:** Schema, extraction/merge fixtures, split round trip, stale invalidation, all-language completeness report, and protected-token tests pass for English/German, representative LTR, and Arabic RTL.

## Completion evidence

- Product REF: `386590183ebd742032b46f8c67274c498a2ddaa6`.
- Focused plus existing i18n regression validation: `python3 -m unittest _src.tests.test_issue_title_i18n _src.tests.test_i18n_page_content` — 14/14 tests passed.
- Compilation: `python3 -m py_compile _src/i18n_translate.py _src/tests/test_issue_title_i18n.py` — passed.
- Static safety: path-scoped `automation_safety.py` — PASS, zero unresolved critical findings; two pre-existing deletion advisories in the legacy segment pipeline.
- `git diff --check HEAD^ HEAD` — passed.
- Production `issues-status` derives 11 languages from `_src/site.json` and correctly reports incomplete: the current public projection exposes one placeholder item but the generated catalog has no matching canonical title. No translation or title was fabricated.
- Scope audit: all product paths are within the exact dispatch write scope; no Acceptance, checkpoint crossing, main/DONE/push, root mutation, or external translation occurred.
