# S-Core Feedback Loop Requirements Dossier

## 1. Source Trace & Exact Requirements
This dossier captures the requirements for the operational website loop connecting browser feedback, GitHub queue, AI proposal, Curator decision, and static publication, integrating existing AUTOSAR and new S-Core tree.

Requirements:
- Project Lead orchestration of priority-gated Supervisor offers (no Publisher role).
- Two-cycle model:
  1. Feedback -> GitHub request -> Ingestion -> Queue item -> AI assignment -> Proposal -> GitHub push.
  2. Curator view -> Durable decision -> Ingestion -> Apply -> DB commit -> Refresh -> Regenerate/Publish.
- Runner recipes (Feedback ingestion, AI proposal, Apply/Regenerate/Publish) execute deterministic typed transitions without workflow authority.
- DHTML provides a read-side/live projection only. Full-tree deterministic static regeneration provides the durable release baseline.
- Reusable interaction concepts from `agent-inbox` are applied into a bounded S-Core-specific UI without requiring generic GUI extraction.
- Strict idempotence contracts on all actions.

## 2. Overlap & Gap Analysis
- **0019 (S-Core Import)**: `0019-13` links repair must be incorporated into the final publication task (`0045-06`).
- **0033 (Website Review Request Contract)**: Overlaps significantly with feedback ingestion (`0033-07`), Curator UI (`0033-07.01`), and end-to-end integration (`0033-16`). Feature 0045 nodes integrate these 0033 tasks explicitly as prerequisites.
- **0035 (Review-Request Dialog)**: Relates to the submission/transport. Covered under the DHTML read-side and trusted feedback ingestion contract (`0045-03`).
- **0021 (Review Flags)**: The original manual-only implication is superseded. `docs/pipeline/website-review-flag.md` is updated to link the new automated process.

## 3. Open Assumptions
- The live interaction (HUD) can reuse `agent-inbox` protocol concepts natively without deep architectural changes to the existing S-Core models.
- Curator decisions are dependably tracked via GitHub issues/comments and mapped 1:1 with queue items.

## 4. Proposed Task Mapping
A/P0: `0045-01` (Publication baseline)
B/P0: `0045-02` (Scheduling contract)
C/P0: `0045-03` (Feedback ingestion recipe)
D/P1: `0045-04` (AI proposal recipe)
E/P1: `0045-05` (Curator decision UI)
F/P0: `0045-06` (Terminal integration)

## 5. A1 Target-Policy Integrability
The pipeline and target tasks align with current `main` branch policy. 
**Gate-Scope Flag**: Task `0045-05` requires an independent UI/UX and security review before integration, triggering a cross-item gate-scope decision prior to qualifying mutation.
