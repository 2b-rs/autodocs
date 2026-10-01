# Eclipse S-CORE v0.6.0 — Phase-6 curator readiness package

**Task:** `0019-08`
**Candidate baseline:** Feature branch `0019` commit `b1ff3b205e928210900091a63894ecf45626bc40`
**Accepted readiness-package snapshot:** SHA-256 `368c7a2234286d621b73749541afcf023ca9f07966bd15b0e5a11838ed605700` from commit `40aaa877447087647d608e94b3d8d75ce91c27b9`
**Decision state:** `CONDITIONALLY ACCEPTED — USER-AUTHORIZED, DIGEST-BOUND`
**Publication state:** `BOUNDED` — no generated-tree command, remote publication, or SSH action was run by this task.

The readiness-package snapshot above was preparatory evidence. The append-only
curator decision below binds the authenticated user's authorization to that
exact snapshot. It is a curator publication gate only; it is not Task
`Acceptance: ✓`, an integration approval, a remote mutation, or Feature
closure.

## Exact review inputs

| Input | Exact identity |
| --- | --- |
| Source BOM | `_src/spec/campaigns/eclipse-score-v0.6.0.json`; file SHA-256 `00ae06246b513250ee19aa74fb1285ac0050a774f56a52fc75ac6aaecc73facb` |
| Source snapshot | inventory SHA-256 `1f3595a67d8bd3ee6463144d01e5f9889609dd888e064c578c05fca098cf596f`; 787 artifacts |
| Pinned source commits | `score@v0.6.0` `db1f5bb87ad7f41b40b6aca4b96a889d8798735e`; `process_description@v1.6.0` `04e9cd30bc657033a764dbb75f07e03e4ccbbc12` |
| Import profile | `_src/spec/import-profiles/eclipse-score-v0.6.0.json`; SHA-256 `20388a20422fb7ace1f3bf88c67dd9d16c733c95d7e6f6eb4c21e73cf4c9e2fd` |
| Exact corpus reproduction | import date `2026-08-19`; raw SHA-256 `6a95acf9b7aadbd39c94d7067bbaecc0466019638221d427b743ed0381a1d86a`; corpus SHA-256 `b2898d9c666ac86235875e3230c902908be44a2208c4085a0ec584b8a6e73692` |
| Persisted validation report | `_src/spec/campaigns/reports/eclipse-score-v0.6.0.validation.json`; SHA-256 `586158d6386c5858bf45a55c507b861814c1ec3aa0bdd4a368b9fa1eedca30f7` |
| Persisted human report | `_src/spec/campaigns/reports/eclipse-score-v0.6.0.validation.md`; SHA-256 `96073d040858245e7c44ba4c4c4c03f22ede7e9ac7f2b17c428140c6f74dd85e` |
| Queue reproduction | one `queued` item, SHA-256 `494662e83e3d4a1e0f97909437d5e09c2965413b500a047a8946ee711b486df7`, generated only in a disposable local snapshot |

The regenerated JSON and Markdown validation reports are byte-identical to the
persisted reports. The report binds exactly to the reproduced corpus digest.

## Phase-6 reconciliation

| Class | Count / result |
| --- | --- |
| Validation report | PASS; 0 findings, 0 errors, 0 warnings |
| Canonical records | 2,239: module 1; component 1; design-doc 966; process-doc 1,271 |
| Record status | 2,239 `invalid/to-be-confirmed` |
| Exception candidates | 1 `identity-collision` |
| Reproduced queue snapshot | 1 `queued` item |
| Tracked S-Core queue items at candidate baseline | 0 |
| Low-confidence `valid/ai-decided` records | 0 |
| Hypothesis records | 0 |
| Source exclusions | 2: `tooling` and `docs-as-code`, documented as build/render dependencies outside the four in-scope record classes |

The exception is
`score-normalization-exception:dcf6dbf31474ff96` for
`ECLIPSE/S-CORE/process-doc/feat__feature_name`. Its reproducible queue item is
`score-curation:8331ec449f11734de83f`, with the release-pinned source locator:

```text
https://github.com/eclipse-score/process_description/blob/04e9cd30bc657033a764dbb75f07e03e4ccbbc12/process/process_areas/architecture_design/architecture_concept.rst#L428-L454
```

The normalized corpus is intentionally pre-publication:
`canonical_corpus_written=false`, `queue_written=false`, and
`publication_permitted=false`. The disposable queue snapshot proves the
`0019-07` governed transition and is not a tracked queue mutation or a content
decision.

## Validation performed

Against the rebased candidate, the following completed successfully:

```text
score_campaign_manifest.py --require-complete
score_source_snapshot.py --verify
score_extraction_adapter.py
score_normalization.py --import-date 2026-08-19
validate_score.py (reproduced reports compared byte-for-byte)
score_curation.py (disposable, validation-bound queue snapshot)
python3 -m unittest ...score_campaign_manifest ...score_source_snapshot
  ...score_import_profile ...score_extraction_adapter ...score_normalization
  ...test_validate_score ...test_score_curation ...test_curation_item_lifecycle
  ...test_curation_item_versioning
```

The integrated test suite passed: **62 tests, 0 failures**. `git diff --check`
passed. No network, `run.sh`, record-store mutation, tracked queue mutation,
generated-tree build, remote publication, or `DONE.md` action occurred.

## Required authenticated curator record

The curator must review the exact inputs above and append a decision containing:

```text
Outcome: accept | reject | explicitly bounded conditional-accept
Authenticated curator identity and authentication evidence:
Timestamp (ISO-8601 with timezone):
Rationale and every reviewed class:
Candidate feature commit and source snapshot/corpus/report/queue digests:
Permitted record/version publication scope (or explicit none):
Excluded/unresolved items, limitations, and residual risk:
Required post-generation checks and re-run/expiry trigger:
Conditional-acceptance bounds and remediation owner, if used:
```

A scoped evidence search at `b1ff3b205e928210900091a63894ecf45626bc40`
found only normative references and explicit statements that prior work made no
curator decision; no authenticated curator decision record is reachable.

## Authenticated curator decision

- **Decision ID:** `CUR-0019-08-20260820`
- **Outcome:** explicitly bounded conditional acceptance
- **Curator / authentication evidence:** the current authenticated user, acting
  as curator authority, explicitly accepted the exact digest-bound Phase-6
  package in the user prompt retained verbatim in
  `TODO-worf-curator-readiness-mogh-0019-08-20260819T001000Z.md`.
- **Timestamp:** `2026-08-20T00:00:00Z`
- **Decision rationale and reviewed classes:** acceptance binds the exact source
  BOM/snapshot, reproduced corpus, persisted validation reports, and disposable
  queue snapshot listed above. The reviewed reconciliation is: 2,239 structural
  records with zero validation findings; all 2,239 remain
  `invalid/to-be-confirmed`; one `identity-collision` candidate is represented
  by one disposable `queued` curation item; zero low-confidence
  `valid/ai-decided` records; zero hypotheses; and two documented source
  exclusions (`tooling`, `docs-as-code`).
- **Exact inputs:** source snapshot inventory SHA-256
  `1f3595a67d8bd3ee6463144d01e5f9889609dd888e064c578c05fca098cf596f`;
  corpus SHA-256 `b2898d9c666ac86235875e3230c902908be44a2208c4085a0ec584b8a6e73692`;
  validation JSON SHA-256
  `586158d6386c5858bf45a55c507b861814c1ec3aa0bdd4a368b9fa1eedca30f7`;
  validation Markdown SHA-256
  `96073d040858245e7c44ba4c4c4c03f22ede7e9ac7f2b17c428140c6f74dd85e`; and
  the accepted queue snapshot SHA-256
  `494662e83e3d4a1e0f97909437d5e09c2965413b500a047a8946ee711b486df7`
  (one `queued` item, created `2026-08-20T00:13:00Z`).
- **Permitted publication scope:** `0019-09` may generate S-Core
  curation/review views containing aggregate counts, the two exclusions, and
  the identified unresolved collision/queue case. No ECLIPSE/S-CORE canonical
  record or version is authorized for factual publication: all 2,239 records
  are `invalid/to-be-confirmed`. The user's separate authorization to use the
  GitHub SSH key for later website publication does not authorize this task to
  alter SSH configuration, push, or publish.
- **Limitations and residual risk:** the decision neither changes record status
  nor decides the collision candidate. The disposable queue snapshot is
  validation evidence, not a tracked queue mutation. It does not authorize a
  content decision, Task acceptance, integration, Feature closure, or any
  publication beyond the bounded curation/review view scope.
- **Required post-generation checks:** `0019-09` must rerun the digest-bound
  validation pipeline; reconcile generated aggregate and per-kind/status counts
  against this report and queue snapshot; prove that no invalid/unresolved
  record is rendered as fact; retain canonical/version identity and provenance
  for the identified unresolved case; and pass language-tree, DOM, link, and
  client-rendered checks. Any source, corpus, report, queue, or generator-input
  digest drift expires this decision and requires a new curator decision before
  publication.

This completes the Phase-6 curator gate for `0019-08`. It does not add
`Acceptance: ✓`; a later independent acceptance/integration action remains
separate.
