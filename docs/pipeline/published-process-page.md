# Published Process Description — Page Structure (0002-03)

Source of truth for the design of the published, curator/agent-facing process
description (Feature 0002). This document fixes the page structure agreed for
`0002-04` onward; it does not itself create the page model.

Related decisions already made (see `TODO.md`):

- **0002-01** — audience is both curators/maintainers and AI agents. The page
  documents the *pipeline*, not agent operating instructions. Agent
  instruction files (e.g. `AGENTS.md`-style directives) are referenced as a
  pipeline artifact class, never authored/duplicated here.
- **0002-02** — the page is a **localized page family** (i18n'ed via the
  normal `_src/sources/pages/` → `i18n_translate.py extract/merge` →
  `generate.py` pipeline), not a single static `nolang` page.

## Non-goals

- This page is not a replacement for `_src/SPEC_BUILD_PROCESS.md` or
  `docs/pipeline/processes.md` (the campaign/phase lifecycle deep-dive stays
  there as internal maintainer documentation). The published page is a
  reader-facing map of the pipeline with links out to that detail and to
  representative generated artifacts.
- This page is not the place to embed report *data* — it links to
  `extraction-reports.html`, `traceability.html`, `open-reviews.html`, etc.,
  rather than duplicating their content.

## Section structure

1. **Overview** — one paragraph: source of truth (`spec/records/`), and the
   one-line pipeline shape: extraction → curation/review → i18n →
   diagrams → HTML generation → validation → reports → traceability.
2. **Source of truth** — what lives in `spec/records/` and `spec/*.json`
   catalogs (e.g. `namespaces.json`) is authoritative; everything under
   generated HTML trees, `output/`, and per-language trees is a disposable
   build product. Explicitly lists which directories are sources vs.
   generated vs. cache-only work product (feeds `0002-05`).
3. **Pipeline artifact classes** — a short table/list of artifact *kinds*
   that flow through the pipeline, each with a one-line description and a
   link to where it lives / is curated:
   - Spec records (`spec/records/**/*.json`)
   - Review/curation flags (`spec/review-queue/`, `spec/curation-queue/`)
   - Agent operating-instruction files (e.g. `AGENTS.md`) — per **0002-01**,
     listed here as an artifact class with a link to the file and to any
     open curation-queue entries about it, content not reproduced.
   - Translation batches / i18n segments
   - Diagrams (source SVG/graph + translated variants)
   - Generated HTML page models (`_src/sources/pages/**.json`)
   - Reports (extraction, traceability, open-reviews, build reports)
   - `run.sh` archive pairs (script + log) — linked in detail from `0002-06`
4. **i18n: extraction → translation → merge** — how source pages/records
   become localized output, fallback-to-German behavior for untranslated
   segments (per **0002-02**'s TODO note), and where batch/reject counts are
   reported (feeds `0002-07`).
5. **Diagram translation** — how SVG/graph diagrams are kept in sync with
   localized text.
6. **HTML generation** — `generate.py`'s role turning page models into the
   published tree, per language.
7. **Validation** — `validate.py`'s checks (links, orphans, i18n coverage,
   namespace consistency, schema gates) and what a clean run vs. a failing
   run means for publishability (feeds `0002-08`).
8. **Reports & traceability** — links to `extraction-reports.html`,
   `traceability.html`, `open-reviews.html`, and the combined build report
   once **0001-08** exists; explains how `run.sh` archives
   (`output/run-archive/run-<timestamp>-n<seq>.{sh,log}`) let any published
   artifact be traced back to its exact execution (feeds `0002-06`).
9. **Failure handling** — how to read rejects, fallback counts, stale
   diagrams, and validate errors without silently patching outputs (feeds
   `0002-08`).
10. **Further reading** — links to `_src/WARTUNG.md`, `docs/pipeline/*.md`,
    once available (feeds `0002-09`).

## Page model placement

- New page model: `_src/sources/pages/process.json` (canonical/German source,
  like `index.json`), `file: "process.html"`.
- Participates in `i18n_translate.py extract`/`merge` and per-language
  `generate.py` output like any other content page (per **0002-02**); no
  `nolang` flag on the page as a whole. Individual `nolang`-flagged blocks
  (e.g. embedded live report widgets, if any) remain possible per existing
  convention (see `index.json`'s `tr-todo-graph`/extraction-quality blocks).
- Linked from site navigation/index per **0002-04**; suggested nav label
  "Prozess" (de) / "Process" (en), placed alongside the existing
  Qualität-&-Traceability aside on `index.html`.

## Sequencing note for remaining tasks

This structure is the shared contract for `0002-04`–`0002-10`; each of those
tasks implements exactly one numbered section (or navigation/coverage
concern) above and should not redefine the section list.
