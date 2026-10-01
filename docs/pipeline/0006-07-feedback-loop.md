# 0006-07 Feedback Loop: Curator Decision to Extraction

> [!NOTE]
> This document specifies the architectural feedback loop from a Curator decision (rejection, revision request, or edit) back into the upstream extraction, scraping, and database logic for the S-Core records.

## 1. Motivation

Currently, when a Curator rejects an AI proposal or requests a revision, the decision is recorded, but the upstream extraction and scraping logic (`score_scrape.py`, `score_extraction_adapter.py`) and the AI contractor do not systematically consume this feedback. Without a feedback loop, the system risks repeating the same extraction mistakes on subsequent runs or similar elements.

## 2. Architectural Boundary

The feedback loop bridges **Cycle 2 (Curator decision)** back to **Cycle 1 (Feedback to proposal)** and the offline extraction/scraping processes.

*   **Extraction/Scrape Logic**: Must consume durable Curator feedback as configuration overrides or context.
*   **AI Contractor**: Must receive previous Curator decisions as explicit context when generating a revised proposal.
*   **Decision Store**: Must provide a queryable interface for feedback bound to specific `record-id`s or extraction patterns.

## 3. Mechanism of the Feedback Loop

### 3.1. Durable Feedback Storage
When a Curator decision of type `rejected` or `revision_requested` is ingested via the `apply_publish` recipe (or a dedicated decision ingestion recipe), the decision rationale and delta are not just emitted as a continuation; they are explicitly committed to a durable **Feedback Store** (e.g., `_src/data/curation-feedback.json` or within the `issue-store`). 

### 3.2. Extraction Adapter Awareness
During periodic scrape runs, `score_scrape.py` and `score_extraction_adapter.py` must query the Feedback Store.
*   **Direct Overrides**: If the curator explicitly corrected a field (e.g., a regex mismatch for an S-Core ID), the adapter must apply this correction automatically to the raw scraped data before creating a queue item.
*   **Pattern Matching**: If a pattern of rejections is detected (e.g., same source document consistently failing), the scraper flags the source for manual adapter update.

### 3.3. AI Contractor Context Injection
When an AI contractor is awarded a proposal task (via `ai_proposal` recipe) resulting from a `proposal-scheduling continuation` (triggered by a Curator's `revision_requested`), the runner recipe must:
1. Fetch the entire Curator decision history for the specific `queue-item-id`.
2. Inject the Curator's rationale and evidence references into the AI's generation context.
3. Validate that the AI's new proposal explicitly addresses the negative constraints from the previous rejection.

## 4. State Machine and Idempotence

The feedback loop relies on the exact idempotence keys established in the S-Core process.
*   `decision:<proposal-id>:<curator-decision-revision>`: This key guarantees that a curator's feedback is processed exactly once into the Feedback Store.
*   When a `revision_requested` decision is processed, the system creates a new queue item or increments the queue item revision: `proposal:<queue-item-id>:<baseline-record-version>:<recipe-version>+1`.

## 5. Implementation Plan

1.  **Schema Extension**: Extend `curator-decision-protocol.md` and related schemas to ensure the rationale is machine-readable and explicitly links to extraction fields.
2.  **Adapter Update**: Modify `score_extraction_adapter.py` to accept an optional `FeedbackStore` dependency.
3.  **Runner Update**: Update the `ai_proposal` recipe in `runner_transaction.py` to bundle Curator feedback into the `task-evidence-pack`.
