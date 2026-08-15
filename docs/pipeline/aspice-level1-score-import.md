# PAM-informed Campaign Evidence Contract — Eclipse S-CORE Database Import

Source: derived from `_src/SPEC_BUILD_PROCESS.md` (campaign/status model) and
`docs/pipeline/score-identity-scheme.md` (0009-01/0009-04), extended here to
fix the local campaign-evidence obligations for Feature 0019 ("Eclipse S-CORE
Database Import").

This is **not an Automotive SPICE Level-1 assessment definition**. PAM 4.0
rates Level 1 for a named process, and its base practices are process-specific.
The six practices below are project-defined controls intended to preserve
useful documentation-campaign evidence. Feature `0011-03` may map that
evidence to approved named documentation-process outcomes, while Feature
`0020-02` must classify it as `documentation-execution`. It is not objective
execution evidence for a future ECU process instance and cannot support ECU
capability wording.

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

These conditions do not establish a capability level. ECU CL1 requires a
validated `PA 1.1 = L` or `F` result for each named process under Feature
`0025`; ECU CL2 additionally requires `PA 1.1 = F` and `PA 2.1`/`PA 2.2` at
`L` or `F` under Feature `0018`. Managed planning, monitoring/adjustment,
resources/competencies, interfaces, and work-product management are outside
Feature 0019. CL2 monitoring may be qualitative and/or quantitative;
statistical quantitative process analysis/control belongs to PA 4.1/PA 4.2,
not CL2.
