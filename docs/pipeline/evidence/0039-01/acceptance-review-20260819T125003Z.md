# Independent acceptance review — `0039-04 → 0039-01`

- **Reviewer:** Linus Riker `20260819T125003Z`, independently assigned privileged Acceptance reviewer.
- **Authority reference:** Current-user prompt of 2026-08-19, preserved verbatim below.
- **Review baseline:** branch `0039-01`, `0aef8c78ea2c94c68a10ebd6701792683817fbc6`.
- **Candidate commits:** `0039-04` substantive `924eeaf59e22297258f38bb0e9e25eca52dd666b`; `0039-01` substantive `451a05cad307e0ce8cac312e411e096aa4e81bee` and bookkeeping `0aef8c78ea2c94c68a10ebd6701792683817fbc6`.
- **Authority epoch:** legacy `TODO.md`/`DONE.md`/claims, before authorized Feature `0037` cutover.

## Batch and baseline

The exact graph is `0039-01 → 0039-04`; `0039-04` has no declared predecessor. Neither had a reachable current acceptance record, so the complete non-accepted batch is ordered `0039-04`, then `0039-01`. No unaccepted item was treated as an acceptance boundary.

| Task | Contract SHA-256 | Work-product manifest SHA-256 | Prerequisite-acceptance SHA-256 |
|---|---|---|---|
| `0039-04` | `f72a93f3a0f88ec03fd4e857d8c4c20944219819d8d7853717bf9e165f750eaa` | `0c8392ae2ce8524777a8aa83551e9f6cc9d96f2e133c63297451bc4678b0131e` | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` (`[]`) |
| `0039-01` | `c081e5c81e5f73b0ab3d0068270374a0f8bbae152ffae5bb34268e154d0d9396` | `d323785c1dfd572746ebea26946d52ef1caf30fb09285dcc4d7477afdfcf48ce` | pending `0039-04` promotion |

Each manifest digest is SHA-256 over sorted changed paths in its substantive commit, encoded as `path + NUL + blob SHA + LF`.

## Inspection and validation

### `0039-04` — accepted

The original work-product baseline was inspected against its Task contract. It contains the normative acceptance process, adapted authority documents, DOCX/PDF dossier, study index, and verbatim prompt provenance. The `task-acceptance.md` baseline provides independent privileged assignment, bottom-up closure, accepted/rejected/inconclusive outcomes, invalidation, authority separation, records, migration/cutover, metrics, and Automotive SPICE boundary. The authoritative instructions prohibit grunt promotion and require a privileged review before `DONE.md` movement.

Focused revalidation passed:

- `git diff --check 924eeaf…^ 924eeaf…`;
- DOCX ZIP integrity and `word/document.xml` presence;
- PDF header/EOF integrity;
- dossier and provenance SHA-256 values match the study index;
- source provenance receipt exists with the full original user prompt.

**Decision:** `accepted` for the exact `924eeaf…` work-product baseline. Later checkpoint-policy evolution is outside this review’s bound baseline and creates no retrospective self-authorization.

### `0039-01` — rejected

Focused candidate validation passed: four unit tests, validator PASS on the committed manifest, Python compilation, `git diff --check`, baseline reachability, and clean candidate worktree. The process/templates/rules/migration and two pilots are English and preserve the stated authority boundary.

**Major finding `AR-0039-01-001`: study reconciliation is absent.** The Task explicitly requires reconciliation of `docs/dossiers/feature-definition-process-study.docx` against current and post-`0037` authority. None of the candidate process documents, evidence manifest, pilots, or implementation claim cites the study or records a recommendation-by-recommendation disposition, conflict, or authority mapping. A generic process cannot prove that required reconciliation happened.

**Required correction:** add a durable, English reconciliation record that identifies the study by immutable digest, maps each relevant recommendation to an adopted/modified/rejected/superseded disposition and exact authority/process artifact, and identifies post-`0037` ownership. Update the evidence manifest and focused validator/tests so a missing reconciliation record fails. Re-run pilot coverage checks against that record.

**Decision:** `rejected`; no `Acceptance: ✓` may be added for `0039-01`. The Task returns to `[p]` for bounded corrective work. The rejection is implementation-actionable and does not require a user decision.

## Scope and authority conclusion

No external action, product/architecture approval, specialist-risk acceptance, Feature integration, or `DONE.md` move was performed. No existing Acceptance record was modified.

## User-prompt provenance

> Be concise. Write all documentation in English. You are **Linus Riker 20260819T125003Z**, an independent privileged Acceptance reviewer. The current user explicitly directed all Feature 0039 tasks to proceed via named Riker subagents, including required independent review gates. Review mandatory Task `0039-01` on branch/worktree `0039-01` after implementation/bookkeeping commits `451a05cad307e0ce8cac312e411e096aa4e81bee` and `0aef8c78e`. Compute exact expanded predecessor batch under immutable policy; do not silently absorb an unaccepted predecessor checkpoint. Verify exact baseline, claims, provenance, study reconciliation, templates, validator, migration plan, both pilots, authority scope and English documentation; rerun focused validation. If conforming, evidence commit then immutable Acceptance bookkeeping bottom-up and finalize reviewer claim. Do not modify existing Acceptance or unrelated work. Return concise verdicts/commits/tests; escalate only hard blockers.
