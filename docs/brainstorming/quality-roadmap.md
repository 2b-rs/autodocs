# Quality Roadmap

This file pulls together the brainstorming from `SPEC_QUALITY_ROADMAP.md`.

## Core insight

The repository currently has **three quality checks**, and they are not peer
reports but a **causal chain**:

1. `extraction_report.py` checks scraper logic directly against known
   PDF-misparse bug classes.
2. `traceability_report.py` / `crosscheck` checks DB records against PDF text
   field-by-field.
3. `trace-check` checks two scraper-derived views of the same PDFs against
   each other: chapter-6 `satisfied_by` parsing vs. inline RS-ID scanning.

The important consequence is that a large `trace-check` finding set should not
be treated as "hundreds of manual review items" first. It should first be
root-caused into extraction defects vs. genuine document asymmetries.

## Proposed roadmap

### Step 1 — Provenance-aware triage

Extend `check_traceability_consistency()` findings with provenance on both
sides of a contradiction:
- which extraction path produced the value,
- which PDF page it came from,
- the raw matched snippet.

Goal: let a human or follow-up tool classify a finding as parser bug in path
A, parser bug in path B, or genuine document asymmetry.

### Step 2 — Cluster before presenting

Group findings by shared signature (same missing-record pattern, same
document, same regex boundary, etc.), similar to the category model already
used in `extraction_report.py`.

Goal: turn many individual rows into a small set of root-cause clusters.

### Step 3 — Keep distinct reports, but unify the record view

Do **not** collapse `extraction_report`, `traceability_report`, and
`trace-check` into one mega-report. They answer different questions.

Instead, add a shared per-record evidence/review view that all three reports
can link to.

### Step 4 — Build a per-record review surface

The proposed "sophisticated view for spec records" would show, in one place:
- rendered PDF screenshot region,
- current structured record JSON,
- each extraction path's independent findings,
- conflicts between paths,
- provenance/diff/verdict when paths disagree.

This is framed as the missing prerequisite for meaningful review.

### Step 5 — Reuse existing review workflow

Rather than inventing another review system, reuse the existing
`review.js` + GitHub-issue + ingest pattern:
- accept side A,
- accept side B,
- mark as benign asymmetry,
- flag as new bug.

Decisions should feed back into review metadata and future suppressions /
allowlists.

## Themes worth preserving

- **Root cause beats row count.** Large report totals are misleading if many
  rows share one underlying parser defect.
- **Provenance is review acceleration.** If a contradiction already carries
  page, snippet, and producing function, the reviewer no longer has to reopen
  the PDF for ordinary cases.
- **Views stay specialized.** The answer is better linkage, not fewer pages.
- **Workflow reuse matters.** The repository already has review mechanics;
  new quality-review loops should build on them.

## What is still brainstorming vs. implemented

| Idea | Status |
|---|---|
| Provenance-enriched `trace-check` findings | Partly implemented recently in the working tree direction, but still a roadmap item in this memo |
| Root-cause clustering for `trace-check` | Brainstorming / not a standalone finished report flow yet |
| Per-record review page | Brainstorming only |
| Reusing review workflow widgets and ingest logic | Plausible and aligned with existing tools, but not yet a complete end-to-end product |
