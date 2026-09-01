# PAM-informed Campaign Evidence Contract — Eclipse S-CORE Database Import

Source: derived from `_src/SPEC_BUILD_PROCESS.md` (campaign/status model) and
`docs/pipeline/score-identity-scheme.md` (0009-01/0009-04), extended here to
fix the local campaign-evidence obligations for Feature 0019 ("Eclipse S-CORE
Database Import").

This is **not an Automotive SPICE Level-1 assessment definition**. PAM 4.0
rates Level 1 for a named process, and its base practices are process-specific.
The six practices below are project-defined controls intended to preserve
useful documentation-campaign evidence. Under `DEC-0011-001`, an artifact may
be associated only as **candidate evidence** for a named documentation-process
outcome category, and only with its exact documentation product, project,
process instance, origin, baseline, limitations, validity, and contrary
evidence. Association does not establish outcome achievement, a process
attribute rating, or a capability level. Feature `0020-02` classifies this
evidence as `documentation-execution`; it is not objective execution evidence
for a future ECU process instance.

## Scope

Applies to the ingestion of Eclipse S-CORE release snapshots, starting with
the v0.6.0 campaign defined by Feature `0019`, into the specification database
under the `ECLIPSE/S-CORE` project namespace defined in
`score-identity-scheme.md`.

## Local process-performance practices mapped onto this pipeline

| Local practice | Concrete requirement for this feature | Work product |
|---|---|---|
| LP1 — Define campaign scope | Every S-CORE import is a named, scoped **campaign** with an explicit release label, repository set, and record-kind scope (module/component/design-doc/process-doc) | `_src/spec/campaigns/<id>.json` manifest |
| LP2 — Fix source inputs and dependencies | Manifest fixes release tag/branch, resolved commit SHA per repository, and PDF-cache-equivalent (source snapshot hash) *before* extraction starts | Campaign manifest, `source_commit`/`source_ref` fields per `score-identity-scheme.md` |
| LP3 — Define the technical approach | Extraction backend(s), `kind` taxonomy, and canonical-ID derivation rule are fixed in advance, not decided ad hoc during a run | `score-identity-scheme.md`; scraper source (`score_scrape.py`) |
| LP4 — Perform the import and produce records | Scraper run emits one record per unit with canonical ID, version ID (`@rel:<release>#<hash8>`), and provenance metadata; nothing is hand-edited outside `legacy`/manual-override rules | `_src/spec/records/ECLIPSE_S-CORE/**/*.json` |
| LP5 — Check consistency and structure | Automated structural validation (dangling refs, orphaned modules, malformed sphinx-needs IDs) runs on every import before records are eligible for `valid/*` | `validate_score.py` output / campaign report |
| LP6 — Review, confirm, and communicate results | Import results are summarized (counts by kind/status) and made visible in the curation/review report, not only in commit messages | `curation-report.html` entry, campaign close commit |

## Candidate named-process associations

These associations are trace categories, not achieved outcomes or ratings:

| Local control/evidence | Candidate category | Required limitation |
|---|---|---|
| Campaign scope, plan, and status | `MAN.3`-adjacent | Documentation campaign instance only; no ECU project-performance claim |
| Release-pinned source/configuration inventory and versioned records | `SUP.8`-adjacent | Configuration evidence for the documentation campaign only |
| Structural validation, curator review, and finding disposition | `SUP.1`-adjacent | Review evidence is not automatically independent QA or proof of content correctness |
| Persisted problems/exceptions and closure links | `SUP.9`-adjacent | Requires a real problem lifecycle with cause, correction, verification, and closure |
| Controlled change and curation decisions | `SUP.10`-adjacent | Request, decision, and application remain distinct; queue state alone proves nothing |
| Authorized documentation publication package and close report | `SPL.2`-adjacent | Documentation release only; not ECU software or product-release evidence |

No import extraction is relabeled as ECU `SWE.*`, and public S-CORE content is
not treated as the assessed unit's requirements. Only an authorized assessment
of the named process instance may judge outcome achievement or assign
`N`/`P`/`L`/`F`, CL1, or CL2.

## Minimum acceptance bar for campaign-evidence completeness

An S-CORE import campaign has a complete local evidence set only if **all** of
the following hold:

1. A campaign manifest exists, is committed, and fully identifies the input
   (release label, repo list, resolved commit SHAs, extraction tool version).
2. Every emitted record carries a canonical ID, version ID, and non-canonical
   provenance fields per `score-identity-scheme.md` — no anonymous/untraced
   records are permitted into the database.
3. An automated validation pass runs over the emitted record set and its
   pass/fail result (with counts) is persisted, not just printed to a console.
4. A human-readable summary of the import (records by kind, by status,
   validation findings) is committed or published, so the outcome of the
   process step is independently checkable without re-running the tool.
5. The campaign is explicitly closed (status + commit) according to the
   operational lifecycle in `docs/pipeline/processes.md`, so campaign
   boundaries stay auditable.

These conditions do not establish a capability level. ECU CL1 ratings belong
to the authorized named-process assessment under Feature `0025`; ECU CL2
ratings belong to Feature `0018`. The recorded conflict between the dated CL2
survey rule and the `0011-02` method remains outside this contract, so this
campaign neither selects nor relies on a CL2 aggregation threshold. Managed
planning, monitoring/adjustment, resources/competencies, interfaces, and
work-product management are outside Feature `0019`. Statistical quantitative
process analysis/control belongs to PA 4.1/PA 4.2, not CL2.
