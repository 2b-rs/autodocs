# 0043-04 — Architect review of report-staleness gate scope

**Reviewer:** `Harry-Seven-20260822T153500Z`, Architect, privileged

**Dispatcher:** `Harry`

**Former implementer:** `Data-Aria-20260821T093000Z`

**Review kind:** independent pre-mutation cross-item gate-scope review, not Task acceptance

**Review baseline:** `main` at `3d8467b097120302d80f5ffccfae06c1e3dd095a`

**Decision state:** exact ID/path requested from `kathryn` through agent-inbox `1787430954327-6b380f26`; not allocated when this review was prepared

## Verdict

The canonical `cross-item-blast-radius` predicate **applies**. This is not based on shared paths or a hypothetical defect. Task `0043-04` expressly requires `validate.py` to emit a staleness finding and makes that check part of the canonical build. In the actual implementation contract, `record_finding(..., severity="error", ...)` appends the message to `problems`; `main()` exits `1` whenever `problems` is non-empty. The declared gate can therefore block validation and downstream integration/closure of work units other than `0043-04`.

I support only the bounded semantics below. No product/gate mutation is authorized until a conforming `decision-record@v1` is integrated on `main`. The existing `Integration review: mandatory` marker is **confirmed**: a false negative recreates the frozen-report incident, while a false positive blocks every canonical validation using this gate.

## Pinned candidate, baseline, and drift

| Ref | Pin | Evidence |
|---|---|---|
| Candidate `0043-04` | `b9bef3f423a05de47f7dbad82324af0ebb4667e9` | exactly two commits after base: claim/discovery `59a546c03` and authorization-hold bookkeeping `b9bef3f42`; no product/gate implementation |
| Candidate base | `38a4d43adcb889e0014f8025d1fdb564eb34c97f` | contains terminal `0043-01`; lacks `build_ledger.py` and `build-ledger.md` |
| Feature `0043` | `23c4c3705e0055ebce5f4d5ad5de81d2d7bec7b1` | includes completed `0043-02`, `0043-03`, `0043-05`, and `0043-06` work, including the ledger and current history renderer |
| Review/main baseline | `3d8467b097120302d80f5ffccfae06c1e3dd095a` | current governance/backlog baseline at review worktree creation |

The candidate is 165 commits behind the pinned Feature tip and 148 behind the pinned main (with two candidate-only claim commits). Feature and main have also diverged (23 Feature-only, 6 main-only commits at discovery). The target `validate.py` object is nevertheless identical in candidate, Feature, and main (`731a3a1ba137f657c2cb62ca13cf459e58bb1709`), proving no staleness gate exists in any of them. The candidate must not be implemented as-is: after authority lands, its claim history must be preserved while it is reconciled under the binding Task-from-Feature base/merge rule with current Feature work and current main governance.

## Actual declared behavior and affected reach

The existing contracts establish:

- `validate.py` is the canonical validation command; any error finding produces exit `1`.
- `build_report.py combine` selects a schema-valid four-stage cohort (`i18n_merge`, `i18n_diagrams`, `html_generate`, `validate`) sharing one non-empty `run_archive_ref`.
- `combine` and `publish` append idempotently to tracked `docs/evidence/build-ledger.jsonl`; append failure raises the command exit to at least `1`.
- The ledger contract names `0043-04` as a consumer, requires malformed-ledger findings to stay visible, and says a run without a ledger entry is a finding.
- `0043-03` renders ledger history, but the page model has no structured publication-provenance field: the run identity appears only inside opaque presentation HTML. Parsing that HTML would not be a stable validation contract.

Affected work units:

1. `task:0043-04`, which owns the new check and canonical sequence.
2. `task:0043-02`, whose ledger schema/consumer boundary the check consumes but must not rewrite.
3. `task:0043-03`, whose page-model producer requires a narrow structured provenance extension so the validator does not parse presentation HTML.
4. `feature:0043`, especially integrating Task `0043-07`, whose acceptance criteria require a green end-to-end run including this check.
5. `repository:autodocs` work units whose declared validation or checkpoint evidence invokes canonical `_src/validate.py`.

Affected gates:

- `validation:_src/validate.py`
- `integration:0043-04`
- `integration:0043-07`
- `feature-closure:0043`

The decision does not itself publish, release, accept, or integrate anything; no external/release gate is claimed merely because the checked artifact is called a publication report.

## Minimum supportable gate semantics

1. **Stable publication identity, not mtime.** `build_report.py` must place a structured provenance object in `_src/sources/pages/build-reports.json` binding the generated page model to one exact ledger entry, at minimum its `combined_report_digest`, `recorded_at`, and `run_archive_ref`. A live publication has a non-null run ref; a null ref is allowed only when it mirrors an entry explicitly marked `backfilled: true`. The validator reads this object; it must not scrape the HTML string or compare filesystem mtimes/wall clocks.
2. **Newest tracked state.** In a clean checkout with no git-ignored raw reports, the page binding must match the newest schema-valid tracked ledger entry, including an exact historic backfill whose run ref is null by contract. Absence of ignored `output/` evidence is not itself stale.
3. **Newest complete live cohort.** When raw subreports exist, only a schema-valid cohort containing all four required stages under one non-empty `run_archive_ref` is eligible. A newer eligible non-diagnostic cohort must have a matching ledger entry, and the page binding must name that same run. A later validation subreport under the same unique ref does not create a new cohort or stale the page by itself.
4. **In-progress cohorts do not block.** Missing stages, identity-less files, and incomplete current runs are not silently promoted into a staleness verdict. Their existing producer/combine checks remain unchanged; this gate waits until a cohort is complete.
5. **Diagnostic runs stay diagnostic.** Existing `--no-ledger` is documented as diagnostic. The producer must mark its combined output structurally as non-publication/ledger-not-required, or isolate it from discovery. The validator must not guess diagnostic intent merely from a missing ledger entry. A normal `combine`/`publish` attempt whose ledger append failed remains an error.
6. **Fail closed on authoritative corruption.** Missing/malformed structured page provenance, a malformed tracked ledger, a complete publication cohort without a ledger entry, or a mismatch between page binding, newest ledger entry, and newest eligible cohort are `severity="error"` findings and therefore exit `1`.
7. **Canonical phase order.** The documented sequence must make the phase boundary explicit: producers including the initial validation subreport; `combine`; `publish`; generation of `build-reports.html`; then final validation. The final validation may write another `validate` subreport under the same run ref but must not invalidate the already published cohort identity.
8. **Hermetic proof.** Focused tests cover the motivating frozen page, aligned clean checkout, newer complete cohort, incomplete cohort, missing/malformed ledger, failed append, explicit diagnostic run, same-ref final validation, and absence of ignored output.

The Task's prerequisite graph should add `0043-02` and `0043-03`: the implementation consumes the former's ledger contract and extends the latter's completed page model. This is an intent-preserving dependency correction, not permission to overwrite either completed work product.

## Explicit prohibitions and boundaries

- No warning/advisory-only finding: it would not make staleness mechanically impossible to miss.
- No scan of every report page or expansion beyond `build-reports` freshness under this Task.
- No mtime/clock heuristic, HTML-text scraping, or selection of a partial/identity-less cohort.
- No false blocker merely because ignored raw reports are absent in a clean checkout.
- No treating `--no-ledger` diagnostics as publication failures without an explicit machine-readable distinction.
- No change to historical ledger entries, append-only guarantees, `DEC-0043-001`, unrelated `validate.py` checks, publication authority, external destinations, or acceptance semantics.
- `validate.py` remains read-only with respect to product state: it must report, never auto-run `combine`, publish, append the ledger, or repair the page.
- No implementation against stale candidate bytes and no wholesale conflict resolution of `TODO.md`; preserve the claim and reconcile exact lines/work products.

## Validation and evidence for this review

- Pre-mutation hygiene: PASS, 116 registered worktrees.
- Candidate/base/Feature/main refs and commit divergence pinned as above.
- Candidate diff from its base: only the Data-Aria claim and `TODO.md` authorization hold; no product code.
- `validate.py` exit path inspected directly: error finding → `problems` → exit `1`.
- Ledger producer/consumer contract, page renderer, page-model bytes, canonical maintenance workflow, ledger tests, and report tests inspected at Feature tip `23c4c3705`.
- Relevant authority files were fully read earlier in this unchanged session; their Git objects are unchanged from the prior full read (`AGENTS.md` `054f62f8…`, `SANDBOX.md` `46645922…`, `decision-record.md` `d62bbedd…`, `process-roles.md` `1b67de54…`). Current `TODO.md`, Feature context, claim/hold, and changed report artifacts were read afresh.

## Mutation status

**Blocked pending Decision record and governance integration.** The independent Architect review supports the bounded scope, but the second precondition is absent until Kathryn allocates the exact Decision identifier/path, Dispatcher Harry expands write scope to that exact path, and a conforming `decision-record@v1` is integrated on `main`. The Task remains `[u]`; no product/gate mutation may begin before then.

The complete dispatch briefing, dispatcher identity, persona-name discrepancy, and context given/not given are retained verbatim in `TODO-Harry-Seven-0043-04-scope-20260822T203500Z.md`.

## Additive governance update — 2026-08-22

Kathryn allocated exact identifier `DEC-0043-003` and exact path `docs/dossiers/dec-0043-report-staleness-gate.md` on `main@69326064dac5bb2aab93f61762d8bc6891d570e6`; Dispatcher Harry then expanded this review's write scope to exactly that path. The conforming draft is committed with this review and implements the bounded verdict above. It also incorporates `DEC-CAP-003` explicitly: neither the decision nor the contemplated product implementation changes any agent-controlling host, Runner, start, health, restart, rollback, or revocation mechanism. The 2026-08-22 task-acceptance clarification is likewise incorporated: this Architect scope decision is not Task acceptance or a checkpoint verdict, and transitive non-accepted prerequisite closure remains a Feature-closure concern rather than an entry gate for the later node-level checkpoint review.

The authorization state changes only after governance integration: until `DEC-0043-003` is present on `main`, Task `0043-04` remains blocked from product/gate mutation. This additive update does not perform acceptance, integration, publication, Feature closure, or implementation.
