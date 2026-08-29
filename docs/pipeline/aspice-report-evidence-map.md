# ASPICE Evidence Map — Report Landscape and Build Ledger

Status: documentation Task `0043-06`, requirement `RQ-BR-07`. Written after the
report-landscape overhaul (`0043-05`) and the build-ledger schema (`0043-02`,
`DEC-0043-001`).

**This is not an Automotive SPICE assessment and makes no capability-level
claim.** `DEC-0011-001`, Feature `0020`'s origin boundary, and the authorized
Feature `0025`/`0018` assessment paths require a sharp separation: naming a
candidate process-outcome category for an artifact is not asserting that the
outcome is achieved, at any level, for any process instance. `0011-03`
reconciles the wording; it does not perform the future assessment. This map
exists so an authorized assessor can see exactly what exists and what is
missing without treating the inventory itself as a rating.

## How to read this table

For each report page / artifact: the **candidate** process-outcome category it
is closest to (using the same PAM-informed, project-defined framing as
[`aspice-level1-score-import.md`](aspice-level1-score-import.md), not a rated
PAM assessment), what it evidences, what an assessor should actually be shown,
and the honest gap — what is *not* covered, including evidence that is
git-ignored by design and therefore not configuration-managed.

An association is admissible only when the exact documentation product,
project, process instance, origin, baseline, limitations, validity, and
contrary evidence are supplied. Missing context means “not associated,” not an
invitation to infer it. The closed candidate set is `MAN.3`, `SUP.8`, `SUP.1`,
`SUP.9`, `SUP.10`, and `SPL.2` adjacent; no row assigns achievement or a
rating.

| Artifact | Candidate category | What it evidences | What to show an assessor | Known gap |
|---|---|---|---|---|
| `docs/evidence/build-ledger.jsonl` | **SUP.8**-adjacent (Configuration Management) — baselines | One append-only, schema-validated entry per publication run: outcome, counts, findings-by-severity, and a cryptographic digest (`combined_report_digest`) plus reference (`combined_report_ref`) binding the entry to its full machine report. Append-only-ness is itself machine-verified (`build_ledger.py verify --baseline=HEAD`), not merely asserted. | The ledger file itself (`git log` shows its own history is append-only in practice, not just by policy); a `verify --baseline=HEAD` run against the commit under assessment; [`build-ledger.md`](build-ledger.md) for the schema and consumer contract. | The entries the ledger references (`output/build-reports/*.json`, `output/run-archive/*.sh`/`.log`) are **git-ignored by design** (`DEC-0043-001`) — they are fixed by digest and referenced by path, not configuration-managed themselves. A baseline audit that needs the raw combined report, not just its digest and summary, needs the operator's local `output/` tree or an external archive; neither is guaranteed to still exist. The first ledger entry (`backfilled: true`) has `run_archive_ref: null` and `repo_commit: null` — it is honestly a reconstructed historical marker, not a live-captured run, and `verify` flags any *later* entry claiming the same. |
| `build-reports.html` (`_src/tools/build_report.py`) | **MAN.3**-adjacent (Project Monitoring) — status reporting | Aggregated status of the most recent publication runs: per-run outcome, the exact runner reference (`run_archive_ref`) tying a report to its archived script/log pair, and a full validation-findings table. `0043-03` renders the ledger history newest-first on the same page, so current status and trend are both visible without cross-referencing files. | The live page plus the ledger it renders from; the `run_archive_ref` links, where they resolve, as the audit trail back to an actual executed run. | The page shows *reported* status, not independent re-execution; it cannot itself prove a run's `exit_code` matched what actually happened, only that the ledger and the report agree. Historical machine reports it links to inherit the same git-ignored-raw-evidence gap as the ledger row above. |
| `curation-report.html` (`_src/tools/curation_report.py`) | **SUP.1**-adjacent (Quality Assurance) — review/curation records | Every curation/review item across both queues, in every terminal state (`accepted`, `rejected`, `proposed`, `superseded`) as well as open — nothing is filtered from the display. Each decided item carries `decision_basis` (rationale, evidence, counter-evidence per [`curation-item-schema.md`](curation-item-schema.md)) and an append-only `history[]` of prior state transitions. Website-originated review requests additionally show requester identity/trust and transport, without that provenance conferring authority over the outcome — the curator's decision remains the sole basis for the resulting state ([`website-review-flag.md`](website-review-flag.md), non-bypass rules 2/3). | The live page; for a specific decision, the underlying `curation-item@v1` record's `decision_basis`, `evidence`, `counter_evidence`, and `history`. | This is evidence that a review/curation **process was followed and recorded**, not evidence that the underlying technical content is correct, that QA was independent, or that `SUP.1` was achieved. No independent second reviewer is required or recorded by the schema itself; whether that is acceptable is a separately tracked process-role question. |
| `open-reviews.html` (`_src/tools/open_reviews_report.py`) | **MAN.3**-adjacent (Project Monitoring) — open-item tracking | A pure "what is currently open" view derived from the same curation-item data as `curation-report.html`, without terminal-state history diluting it. Useful as the single place to check outstanding review load. | The live page as a snapshot; combined with `curation-report.html`'s history for anything that needs "how did this item get resolved," since this page intentionally does not carry that. | Purely derivative of the curation-report data — it is not an independent evidence source and carries the same "process followed, not content validated" limit as that row. |
| `traceability.html` (`_src/tools/traceability_report.py`) | **SUP.1**-adjacent (Quality Assurance) — consistency/traceability checking | Bidirectional consistency between each record's declared upstream and the Chapter-6 traceability tables extracted from source documents (`upstream_not_traced` / `traced_not_upstream`), sourced from a `spec_scrape.py crosscheck` run and its log. Found record IDs are linked to their documentation page where a same-tree HTML target exists. | The live page; the `crosscheck --json` run and log it was built from, for the date shown on the page. | German-only by design (`nolang`), so it is not part of the translated-language consistency surface. The page is point-in-time consistency evidence, not proof of independent QA, continuous enforcement, content correctness, or `SUP.1` achievement. |
| `extraction-reports.html` (`_src/tools/extraction_report.py`) | **SUP.9**-adjacent (Problem Resolution Management) — extraction defect/fix evidence | Full list of extraction deviations grouped by the four defect classes fixed on 2026-08-11, each with the fixing commit; curation requests the automated extraction could not resolve, feeding `curation_ingest.py`. Published versions are preserved by default (`DEC-0043-002`): a version, once published, is not silently regenerated or overwritten by a later run, so a historical report continues to reflect the extraction logic that actually produced it at the time. | The live page and, for a specific historical claim, the preserved versioned report page (`extraction-report-v%04d.html`) rather than only the current one. | A row is candidate `SUP.9` evidence only when a real problem lifecycle, cause, correction, verification, and closure are present. Preservation alone does not prove those elements or outcome achievement. |

## What this map deliberately does not do

- It does not assign a PAM capability level to any process, for the same
  reason [`aspice-level1-score-import.md`](aspice-level1-score-import.md)
  does not: base practices are process-specific and rating them is an
  assessment activity, not a documentation activity.
- It does not claim independence between the people/agents producing the
  underlying work and those recording its verification evidence — the
  `process-roles.md` gap cited in the `curation-report.html` row is a known,
  separately tracked limitation, not something resolved by writing this map.
- It does not cover every report type cataloged in
  [`reports.md`](reports.md) — only the five report pages `0043-05` overhauled
  plus the build ledger `0043-02` introduced, per this Task's scope. Other
  report types (scrape-phase reports, the extraction campaign/benchmark
  reports, the AI-workflow status view) are documented there but are outside
  this map.

## Related documents

- [`aspice-level1-score-import.md`](aspice-level1-score-import.md) — the
  precedent for this document's framing and disclaimers, for the S-Core import
  campaign specifically.
- [`build-ledger.md`](build-ledger.md) — the build ledger's schema, append-only
  guarantee, and consumer contract.
- [`build-report-schema.md`](build-report-schema.md) — the per-run report
  envelope the ledger and `build-reports.html` are built from.
- [`reports.md`](reports.md) — the full catalog of report types in this
  repository, of which this map covers a named subset.
- [`curation-item-schema.md`](curation-item-schema.md) — the schema backing
  `curation-report.html` and `open-reviews.html`.
- [`process-roles.md`](process-roles.md) — records the SWE.4/SWE.6/SYS.5
  independent-qualification gap referenced above.
