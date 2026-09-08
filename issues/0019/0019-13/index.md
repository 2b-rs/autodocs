---
schema_version: "1.0"
id: "0019-13"
level: "task"
parent: "0019"
state: "open"
visibility: "internal"
prerequisites:
  - "0019-10"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3031"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0019-13:0019-10 Repair the two broken relative-link classes shipped in the digest-bound S-Core v0.6.0 curation export and prevent unresolved local links in later subtree releases. **Claim reconciliation (2026-08-24):** The `Harry-Miles-20260823T022500Z` implementation claim was released as orphaned and work-product-free: no claim artifact, implementation branch, worktree, or commit exists. The older `backlog-0019-13-harry-20260822T132000Z` line remains backlog-authoring provenance only. The Task is unclaimed and retains its full implementation scope; no approved digest tree, special publication, Acceptance, checkpoint, integration, `main`, `DONE.md`, push, or Runner action was changed by this reconciliation.

## Scope

- **Management direction (2026-08-22, recorded by Projektleiter `kathryn`):** Repair this at the **next opportunity**, and do **not** run a publication just for it. Verbatim: „Bei nächster Gelegenheit die toten Links reparieren, kein extra Publish-Vorgang dafür." Consequence for whoever picks this up: fix the renderer/exporter so later subtree releases carry resolvable targets, and let the repaired output **ride along with the next publication that happens anyway**. Do not schedule a dedicated release; do not touch the already published, digest-bound tree `7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283` retroactively — a silent correction there would invalidate both the exclusion check and the approval that named that digest. The currently published dead links are an accepted, recorded defect until a later release supersedes them.
  - **QA finding (2026-08-22):** An independent full scan of the approved 2,248-file preview with tree SHA-256 `7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283` resolved all 20,190 local `href`/`src` occurrences and found exactly 2,240 missing-target occurrences: `participate.html` links once to `../../../curation-report.html`, and each of the 2,239 `records/*.html` pages loads `../../../../review_request.js`. No further dead local links were found in that tree. The release authorization records these as known non-blocking defects of the already-approved publication; do not alter that immutable tree or retroactively change its digest/evidence.
  - **Root cause:** `_src/tools/score_curation_views.py` renders paths for an assumed embedding beneath the complete website root, while `_src/tools/prepare_score_curation_export.py` creates an independently publishable strict subtree without packaging those two targets and explicitly allowlists both unresolved escape paths in `ensure_link_scope()`.

## Acceptance criteria

- **AC-001** Define the supported final publication topology and make every generated local `href` and `src` resolve in that assembled tree. The participation link reaches the intended curation report or a deliberately local replacement
- **AC-002** every record page loads a packaged/reachable `review_request.js` without escaping to a missing target. The strict export validator resolves targets against the exact assembled publication root and fails closed for missing files, path escapes, or a removed target
- **AC-003** unresolved-link allowlists must not mask either defect class. Whole-population tests cover all 2,239 record pages and `participate.html`, and negative fixtures prove both missing-target classes fail

## Definition of Done

A newly generated later-release candidate preserves all unvalidated markers, identities, provenance, status/count/manifest guarantees, and publication boundaries; its complete local-link scan reports zero missing targets; repeat generation is byte-identical; focused and whole-population tests pass; new digests and validation evidence are committed. Repair and re-release use a new reviewed candidate and never mutate or relabel the already-approved digest-bound tree.
