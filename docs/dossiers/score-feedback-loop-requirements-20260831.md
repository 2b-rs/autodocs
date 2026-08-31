# S-Core Feedback Loop Requirements Dossier

## 1. Source Trace & Exact Requirements
This dossier captures the requirements for the operational website loop connecting browser feedback, GitHub queue, AI proposal, Curator decision, and static publication, integrating existing AUTOSAR and new S-Core tree.

Requirements:
- Project Lead orchestration of priority-gated Supervisor offers (no Publisher role for now).
- Two-cycle model:
  1. Feedback -> GitHub request -> Ingestion -> Queue item -> AI assignment -> Proposal -> GitHub push.
  2. Curator view -> Durable decision -> Ingestion -> Apply -> DB commit -> Refresh -> Regenerate/Publish.
- Runner recipes (Feedback ingestion, AI proposal, Apply/Regenerate/Publish) execute deterministic typed transitions without workflow authority.
- DHTML provides a read-side/live projection only. Full-tree deterministic static regeneration provides the durable release baseline.
- Initial recommendation: reusable interaction concepts from `agent-inbox` are applied into a bounded S-Core-specific UI without requiring generic GUI extraction.
- Strict idempotence contracts on all actions.

## 2. Overlap & Gap Analysis
- **0019 (S-Core Import)**: `0019-13` links repair must be incorporated into the publication baseline task (`0045-01`).
- **0033 (Website Review Request Contract)**: 
  - `0033-07` is a producer for `0045-03` (feedback ingestion relies on the atomic review-request queue write).
  - `0033-07.01` is a producer for `0045-05` (Curator decision UI relies on role-enforced claim/propose/accept transitions).
  - `0033-16` is a producer for `0045-06` (terminal integration incorporates the pre-release audit).
- **0035 (Review-Request Dialog)**: The UI overlap for the curator interaction and submission storage is explicitly mapped to the `0045-05` Curator decision UI task.
- **0021 (Review Flags)**: The historical 0021 guidance remains valid for manual operation. `docs/pipeline/website-review-flag.md` is updated with a proposed/pending (non-operative until 0045-00) target-state link to the new automated process.

## 3. Open Assumptions
- The live interaction (HUD) can reuse `agent-inbox` protocol concepts natively without deep architectural changes to the existing S-Core models (recommendation).
- Curator decisions are dependably tracked via GitHub issues/comments and mapped 1:1 with queue items.

## 4. Proposed Task Mapping
P0: `0045-00` (Decision record / Architect scope review)
A/P0: `0045-01` (Publication baseline)
B/P0: `0045-02` (Scheduling contract)
C/P0: `0045-03` (Feedback ingestion recipe)
D/P1: `0045-04` (AI proposal recipe)
E/P1: `0045-05` (Curator decision UI)
F/P0: `0045-06` (Terminal integration)

## 5. Gate-Scope & Operative Pipeline Mutation
**Important:** The Supervisor→PL offer policy changes cross-item gates for future curation/review work. 
Therefore, this pipeline design remains **explicitly proposed and non-operative** until a `decision-record@v1` is prepared and a distinct management-instantiated Architect scope review is obtained. Task `0045-00` establishes this gate as a strict prerequisite before any operative mutation occurs.
