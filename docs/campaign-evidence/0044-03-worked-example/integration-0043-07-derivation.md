# Worked example — derived integration-test obligation for checkpoint `0043-07`

**What this is:** the rule of
[`docs/pipeline/integration-test-obligation.md`](../../pipeline/integration-test-obligation.md)
applied to a **real pending integration**: Task `0043-07` ("Integrate the
Feature and prove one publication run end to end", `Integration review:
mandatory`, the Feature-`0043` review floor). Produced by Task `0044-03`
(`agent:seven:0044-03:20260823T143745Z`, 2026-08-23) as its required worked
example and retained as evidence.

**What this is not:** it changes nothing in Feature `0043`, claims no `0043`
item, accepts nothing, and is not the execution record. Per `DEC-0044-019`
the **execution** of this derived set is performed by `0043-07`'s integrator
against the then-current integrated candidate; that execution record is the
broad-activation qualification which `0044-08` confirms. Where this derivation
and the actual candidate state diverge at execution time, the integrator
re-derives the affected rows and records the delta — the matrix below is the
demonstration of *how* the derivation works, pinned to the state visible on
2026-08-23.

## Derivation inputs (source of each obligation)

- **Feature goal / trigger defect:** composition failure — "every part worked,
  the chain did not" (frozen `build-reports.html`; `RUN_ARCHIVE_REF` never
  set; fail-closed `combine` starving). The architect's checkpoint rationale
  explicitly makes *the chain itself* the review object.
- **Integrated items and their declared interfaces:**
  - `0043-01`: `RUN_ARCHIVE_REF` environment contract (runner path in
    `runner-host/run-loop.sh`, manual path via `build_report.py mint-ref`,
    documented in `_src/WARTUNG.md`, `docs/pipeline/build-report-schema.md`).
  - `0043-02`: tracked append-only ledger `docs/evidence/build-ledger.jsonl`;
    writer `_src/tools/build_ledger.py`; contract
    `docs/pipeline/build-ledger.md`; invariants: `O_APPEND` writes, idempotence
    per `run_archive_ref`, `verify --baseline` byte-prefix property.
  - `0043-03`: `build-reports.html` rendered from the ledger via the page
    model `_src/sources/pages/build-reports.json`; newest-first history list.
  - `0043-04` (pending, gate decided by `DEC-0043-003`): one
    `severity="error"` freshness check in canonical `_src/validate.py`,
    binding page-model provenance to the newest valid tracked ledger entry;
    complete-cohort eligibility; diagnostic `--no-ledger` exclusion.
  - `0043-05`: uniform report-page headers through the page-model generators;
    i18n segment extraction for new user-visible text.
  - `0043-06`: `docs/pipeline/aspice-report-evidence-map.md` (documentation;
    honesty constraints are its acceptance criteria).
- **Task contract of the checkpoint node:** one real publication run end to
  end; `validate.py` green including the staleness check; every `RQ-BR-*`
  requirement dispositioned; evidence retained.

## Derivation matrix

| # | Category | Applicable? | Derived obligation (test + oracle) |
|---|---|---|---|
| 1 | Architecture risks / changed seams | **Yes** — the seam *is* the deliverable: producers → `combine` → ledger → page model → renderer → validator | **E2E-1:** On the integrated candidate tree, execute one real publication run: `generate.py`, `validate.py`, `i18n_translate.py merge`, `i18n_diagrams.py`, then `build_report.py combine` and `publish`, then page regeneration, then final validation. **Oracle:** all four required stage subreports share one non-null `run_archive_ref`; `combine` succeeds (no starvation); exactly one new ledger entry appears; regenerated `build-reports.html` lists the run in the history; final `validate.py` exits green including the `0043-04` staleness check. This is the Task's own acceptance criterion executed as the seam test. |
| 2 | Interfaces / schemas / contracts | **Yes** — three declared contracts cross the seam | **INT-1:** run `_src/tools/build_ledger.py verify --baseline=<merge-base>` on the candidate: the committed ledger must be a byte-exact prefix of the working copy (schema + append-only contract). **INT-2:** rerun the focused suites on the candidate tree, not the item branches: `_src/tests/test_build_ledger.py`, `_src/tools/test_build_report.py`, and the `0043-04`/`0043-05` focused tests. **Oracle:** all pass on the exact integrated tree. **INT-3:** confirm the page-model provenance binding matches `docs/pipeline/build-report-schema.md` as extended by `0043-04` (fields `combined_report_digest`, `recorded_at`, `run_archive_ref` per `DEC-0043-003`). |
| 3 | Invariants / state transitions | **Yes** — append-only and idempotence invariants are load-bearing | **INV-1:** after E2E-1, run `publish` a second time under the same `run_archive_ref`. **Oracle:** no second ledger entry (idempotence). **INV-2:** diff the ledger against the merge base. **Oracle:** existing entries byte-identical, exactly the new entry appended (no rewrite). **INV-3:** regenerate the five report pages twice. **Oracle:** deterministic output (`generate.py --check` style, 0 deviations), proving the headers come from generators, not hand edits. |
| 4 | Negative / failure / recovery modes | **Yes** — the motivating defect was a silent negative-case failure | **NEG-1:** rerun the `0043-04` hermetic frozen-page fixture on the candidate. **Oracle:** the staleness finding fires (severity error, `validate.py` exit 1). **NEG-2:** hermetic missing-ledger-entry case fires; incomplete-cohort case does **not** fire; clean-checkout/no-`output/` case does **not** fire (false-positive guards of `DEC-0043-003` CON-05). These run as the committed focused tests plus one direct fixture invocation typed into the evidence. |
| 5 | External effects | **Yes, as exclusion** — real publication to the public deploy repo (`2b-rs/autodocs`) is out of checkpoint scope | **EXT-1:** no real push is part of this checkpoint. The publication run of E2E-1 is local; any publisher-path check uses the existing hermetic scratch-remote tests. **Recorded exclusion:** public deployment remains governed by its own controls (`0038` publisher gates); residual risk noted in the evidence rather than silently omitted. |

Non-applicable rows: none — every category yielded either an obligation or a
recorded exclusion (row 5), which is the honest disposition the rule requires.

## Evidence plan (section-5 minimum, instantiated)

The `0043-07` integrator's record must name: checkpoint `0043-07` and the
`0043` → `main` boundary; the exact candidate tree (Feature-branch tip after
merging `0043-01..06`, with parent hashes) and target `main` tip; the run's
`run_archive_ref` and fixture identities; Python/tool versions material to
`generate.py`/`validate.py` (e.g. the `lxml` scratch-venv caveat recorded by
`0043-02`); every command with exit status; the oracles above with actual
results; SHA-256 digests for the combined report and any git-ignored log the
verdict rests on; the EXT-1 exclusion with residual risk; and replay
instructions. Commit the record with the review findings on the integration
branch.

## No-automation dispositions

- All obligations above are automatable with existing project tooling; no
  manual-fallback row remains.
- If at execution time an environment gap makes a row unexecutable (e.g.
  `lxml` unavailable for full `validate.py`), the integrator follows
  section 6 of the rule: bounded manual/alternative procedure with recorded
  limits if it can establish the criterion — otherwise the checkpoint fails
  and the existing `[u]` integration verdict is recorded. No silent pass.
