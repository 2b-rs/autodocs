# Unified Curation and Review Workflow Model (Feature 0006)

Status: Normative workflow contract (Feature 0006-14).
Authoritative for all curation, review, and flag-for-review lifecycle transitions.

---

## 1. Context & Purpose

The Unified Curation and Review Workflow Model (Feature 0006) establishes a single, consistent lifecycle for all human-in-the-loop decisions across the repository. It unifies previously distinct processes for:
- Review flags (Feature 0003, 0021, 0035)
- Extraction and curation hypotheses (Feature 0005)
- General defect and anomaly reporting

This contract defines the authoritative states, transitions, required artifacts, and roles that govern the curation workflow to prevent uncoordinated implementation divergence.

---

## 2. Core Entities

1. **Curation Item (`curation_item.py`)**: The normalized, first-class object representing a pending decision. Unifies disparate queues (e.g., `review-queue`, `curation-queue`) into a single model.
2. **Hypothesis (`hypothesis-store.md`)**: An AI-proposed extraction, artifact, or curation candidate requiring human validation, identified by a stable UUIDv7.
3. **Decision/Outcome (`curator-decision-protocol.md`)**: The terminal human judgment (e.g., `accept`, `reject`) bounding a Curation Item or Hypothesis.
4. **Version ID (`version-id-scheme.md`)**: SHA-256/UUIDv7 based stable identifier pinning decisions to exact requirement text and context.

---

## 3. Workflow State Machine

The unified lifecycle normalizes all curation and review activities into the following strict state transitions:

- **`discovered`**: A flag, hypothesis, or anomaly is generated (by AI, tools, or users) but not yet committed to the actionable queue.
- **`queued`**: The item is logged in the canonical inventory and awaits human triage or assignment.
- **`claimed`**: A curator or reviewer assigns the item for active evaluation.
- **`proposed`**: (Optional) A candidate solution or structured correction is drafted and awaits final verification.
- **`applied` / `rejected` (Terminal)**: The final decision is reached. A valid decision package (e.g., `review-package@v1`) is ingested, the target record is updated, and the item leaves the active queue.

*Exception Path*: Direct curator decisions in the UI (via `review.js`) may fast-path from `discovered` directly to `applied` or `rejected`, bypassing intermediate queues, provided the cryptographic text hash and authorization are validated upon ingestion.

---

## 4. Required Contractual Obligations

- **No Stateless Updates**: Every state transition must be recorded durably with a timestamp, actor identity, and rational context.
- **Cryptographic Binding**: All terminal decisions must include the `text_hash` of the requirement at review time. If the underlying requirement text has drifted, the ingestion must reject the package.
- **Centralized Ingestion**: Browser clients and external scripts cannot mutate repository files directly. All packages must pass through the canonical ingestion path (e.g., `_src/tools/review_ingest.py` or equivalent tools defined in `tools.md`) to apply changes.
- **Lossless Normalization**: Subsystems managing distinct queues (e.g., `SWS_LOG`, `review-queue`) must use the canonical `curation_item` adapters to ensure universal read compatibility.

---

## 5. Subsystem Integration

All existing tools and subsystems MUST align with this unified contract:
- `curation_report.py`: Aggregates the unified state model into human-readable tables.
- `review.js` / Client Panels: Emits `review-package@v1` adhering to the outcome structures defined here.
- Hypothesis generation tools: Mint UUIDv7 identifiers and conform to the `open` -> `accepted`/`rejected` lifecycle.
