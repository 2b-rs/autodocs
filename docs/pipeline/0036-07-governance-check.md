# 0036-07 Governance & Security Boundary Check: Review Processes & Pipeline Generation

## Scope & Objective

This governance review verifies that all normative documentation, user-facing guides, interactive client components, and page-generation workflows delivered under **Feature 0036** strictly adhere to the security, integrity, and lifecycle invariants established in **Feature 0021** (and consolidated in **Feature 0033** and **Feature 0035**).

Specifically, this check evaluates:
1. **Curator Decision (`review-package@v1`) vs. Flag-for-Review Request (`review-request-package@v1`) Distinction**: Plain-language and normative clarity that review requests are requests only and cannot mutate record statuses directly.
2. **Client Mutation Boundary**: Absolute non-bypass invariant that neither browser client scripts (`review.js`, `review_request.js`) nor uncurated submissions directly modify local database files, status flags, or specification content.
3. **AI Authorization Boundaries**: Explicit documentation that AI agents and generative processes are bounded pipeline tools that cannot unilaterally approve normative documents, change safety classifications, or publish unauthorized HTML outside the reviewed pipeline.

---

## 1. Boundary & Lifecycle Invariant Audits

### 1.1 Curator Decision Protocol (`review-package@v1` / `review.js`)
- **Normative Document**: `docs/pipeline/curator-decision-protocol.md` (Task 0036-01, `f3c26670`)
- **User Guide & Diagram**: `_src/sources/pages/process.html` (Task 0036-04, `51482d09`)
- **Verification**:
  - The protocol explicitly states that decision packages collected in `review.js` represent human curator assessments stored client-side in `localStorage` until export/submission.
  - The workflow requires authorized ingestion and Git-tracked issue processing before any status change takes effect in the canonical API documentation.
  - The generated sequence diagram (`#curator-decision-protocol`) explicitly shows that browser actions submit decisions to a GitHub issue queue, where maintainers incorporate changes via the automated build pipeline.

### 1.2 Flag-for-Review Request Protocol (`review-request-package@v1` / `review_request.js`)
- **Normative Document**: `docs/pipeline/review-request-ux.md` & `docs/pipeline/curator-decision-protocol.md` (Task 0036-02, `8c3c155a`)
- **User Guide & Diagram**: `_src/sources/pages/process.html` (Task 0036-04, `51482d09`)
- **Client Implementation**: `review_request.js` (Task 0036-05, `31479053`)
- **Verification**:
  - In `review_request.js`, the dialog header and context card explicitly declare:
    > *"This creates a review request only. The record is not changed immediately."*
  - The sequence diagram (`#flag-for-review-protocol`) clearly models the life cycle:
    `User Flag -> Queue/Issue Submission -> Maintainer Evaluation -> Pipeline Ingestion -> Site Regeneration`.
  - At no point in the UI or documentation is it suggested that submitting a review request changes the requirement status or closes a curation finding.

### 1.3 Process Page Generation Architecture (`_src/sources/pages/`)
- **Normative Document**: `docs/pipeline/process-page-generation.md` (Task 0036-03, `9d3511ea`)
- **Verification**:
  - Document defines the strict layering: `Spec-DB -> AI Curation/Composition -> Source Templates -> i18n -> Generated HTML`.
  - Explicitly documents that AI generation operates strictly as an drafting/assistance stage producing canonical German source templates under `_src/sources/pages/`.
  - All generated HTML pages are build artifacts produced by `_src/generate.py` and validated by `_src/validate.py`.
  - Normative documents in `docs/pipeline/` remain under Git version control and require reviewer/maintainer approval for modification.

---

## 2. Findings Matrix

| Component / Document | Verified Invariant | Status | Evidence |
|:---------------------|:-------------------|:-------|:---------|
| `docs/pipeline/curator-decision-protocol.md` | Clear separation between curator decision and review request | PASS | Section 2.1 & 3.2 |
| `docs/pipeline/process-page-generation.md` | AI bounded to template draft assistance; pipeline controls HTML generation | PASS | Section 4 & 5 |
| `_src/sources/pages/process.html` | Explanations and diagrams state records are immutable from client | PASS | Sections `#curator-decision-protocol` & `#flag-for-review-protocol` |
| `review_request.js` | Dialog displays explicit non-immediate mutation disclaimer and process link | PASS | Context card & trust warning markup |
| `review.js` | Package export/submission does not perform local database mutation | PASS | Drawer action handlers |

---

## 3. Conclusion & Certification

All documentation, source diagrams, and client-side interfaces created or updated under Feature 0036 fully satisfy the governance, security, and record-immutability constraints of Feature 0021. The boundary between client-side requests and server/pipeline-side record mutations is preserved with complete clarity.
