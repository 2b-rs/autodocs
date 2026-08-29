# `0041-02` non-activating Architect supersession review — Integrator evidence

## Exact authority and boundary

- **Integrator award:** `1787977931427-cd2293a6`, item `0041-02-supersession-review-integration`, process “Privileged governance integration”.
- **Allowed paths:** this evidence, `docs/dossiers/0041-02-blackout-supersession-scope-review.md`, and `TODO-geordi-0041-02-supersession-integration-20260829.md` only.
- **Baseline:** `main@472bab05668d01052991b0fec3e41434a0fa0b4d`.
- **Excluded:** Task Acceptance; implementation or authority-document activation; `8b1afb933f`; `0041-03`, `0041-04`, and `0041-06`; Feature closure; any `TODO.md` change.

## Independent review of the offered candidate

The offered review tip is `review-0041-blackout-supersession-20260829@7fd003ba9ba5c44287a99be2b93dbb287fff8363`. Its substantive commit is `a81eacd58724f24311628888c5773362e7b6759a`; `7fd003ba9` directly follows it and changes only `TODO-architect-0041-blackout-supersession-20260829.md`, which is outside this award. The integration candidate therefore replays only the reviewed substantive content, preserving source attribution with `git cherry-pick -x a81eacd58` as `8ba8521b02c3e9c4674347a5731676365f331131`.

`7fd003ba9` diverges from current `main`; its common ancestry is the review pin `ef7aa528d154a9be8754ee6c6bef84f21056247b`. Current-main movement after the review's observed `5b06f31d` is `472bab056`, which changes six Jadzia handover claims only. It leaves Feature `0041` in `TODO.md` and `docs/dossiers/dec-0041-006-atomic-implementation-checkin.md` byte-identical to the review pin.

On current `main`, the decision record SHA-256 is `3bd3a24445219def41e867f2fddadc5698e64a54ee7ed5b0b97eda4747470e18`, matching the review's cited pin. Its corrections `DEC-0041-006-C001` through `C005` enumerate all three former omissions—`_src/tools/legacy_task_editor.py`, `docs/pipeline/core-rules.md`, and `_src/tools/check_integration_hygiene.py`—in decision, technical justification, consequences, affected work units, and gates. CON-05 retains the old two-commit / implementation-`REF` contract until the one reviewed cutover; CON-06 requires manual current-main re-derivation and forbids stale lineage reuse.

## Verdict

**Accepted for this exact non-activating landing only.** The Architect review's consumer-finding verdict `supersedes` is supported for the named three-consumer omission. Its limiting verdict is retained unchanged: full `0041-02` activation remains blocked, `8b1afb933f0f9029d09c2fd3e9660aad3a8fa9a3` is not merged or made an ancestor, and successors remain unstarted. Bounded non-activating re-derivation is the only stated permitted follow-up.

This is neither Task Acceptance nor an implementation/integration checkpoint verdict for `0041-02`; it lands the separately authored Architect review and exact Integrator provenance only.

## Pre-integration validation

- `git diff --check main...a81eacd58` — passed.
- `git diff --check HEAD~1..HEAD` for replay `8ba8521b` — passed.
- Candidate path delta — exactly `docs/dossiers/0041-02-blackout-supersession-scope-review.md` before this evidence/claim commit.
- `git merge-base --is-ancestor 8b1afb933f HEAD` — expected non-zero; historical activation candidate remains excluded.
- Machine integration hygiene and root pre/postflight results are appended only after they are actually executed.
