# Provenance-Envelope Integration Summary for Producer Families (0037-26.01..0037-26.06)

## 1. Executive Summary & Scope
- **Task ID**: `0037-26` (Subtasks `0037-26.01` through `0037-26.06`)
- **Governing Architecture**: `DEC-0037-017` & `DEC-0037-019` (Common Provenance Envelope `@v1`)
- **Feature Baseline**: `autodocs-provenance-integration`

---

## 2. Integrated Producer Family Adaptations

### 2.1 Scrape & Extraction Reports (0037-26.01)
- Extended scraper extraction reports with immutable input artifact sets (`pdf_sha256`, `config_commit`), common run UUID, trigger issue/criterion tokens, and stable finding identifiers (`FND-SCRP-*`). Disagreements produce linked findings.

### 2.2 Campaign Snapshots & Manifests (0037-26.02)
- Upgraded `_src/spec/campaigns/*.json` writers to produce deterministic content manifests (`campaign-manifest@v1`). Replaced mtime-dependent hashing with content-sorted artifact sets.

### 2.3 Raw Evidence & Record Version Writers (0037-26.03)
- Attached full provenance envelope to raw extraction records (`score_extraction_adapter.py`), preserving source commit, tool version, and issue trigger. Prohibited synthetic relabeling without explicit non-production disposition.

### 2.4 Database Rebuild & Migration Writers (0037-26.04)
- Added deterministic tree digest calculation to snapshot rebuilds, version migrations, and rollback relations. Ensures identical input sets yield identical semantic artifact hashes.

### 2.5 Curation Items, Queues & Decisions (0037-26.05)
- Extended curation queue items (`_src/spec/curation-queue/`) and lifecycle decision records with author tokens, finding references, applied changes, and supersession links.

### 2.6 Validation & Build Reports (0037-26.06)
- Upgraded build reports and validation digests to enforce shared `run_id` across pipeline stages, stable finding reporting, and strict multi-stage manifest consistency without mtime fallback.

---

## 3. Test & Trace Verification
- Unit & integration suites pass with 100% clean exit codes.
- Deterministic reverse-trace and backward-disposition validated against negative and edge-case fixtures.
