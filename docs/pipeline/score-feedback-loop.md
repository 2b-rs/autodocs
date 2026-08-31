# S-Core Feedback Loop Process Contract

> [!WARNING]
> **Proposed / Non-Operative:** This pipeline contract is proposed and non-operative pending the approval of decision-record `DEC-0045-01` and the distinct management-instantiated Architect scope review (Task `0045-00`).

## Prior-Dispatcher Failure & Durable Continuation
The prior dispatcher model failed when responsibility ended without a durable event-driven continuation. Every terminal recipe result must emit a durable event with an unambiguous next handler to guarantee continuous operation:
- **Ingestion complete** -> proposal scheduling
- **Proposal committed** -> curator notification
- **Accepted decision** -> apply/publication scheduling
- **Publication complete** -> workflow closure

## Product Target & Static Fallback Guarantees
The management-approved product target is the next incarnation of the official 2b-rs.github site: from its index, users can reach BOTH (a) the existing AUTOSAR Adaptive documentation and (b) a first pretty-printed S-Core documentation tree; both are generated from the latest authoritative database snapshot and translated into every configured project language. 
There is NO requirement to use or reuse an S-Core component library.
**Static Fallback Guarantees:** DHTML is a read-side/live projection only. Full-tree deterministic static regeneration provides the offline/static fallback, link-validation surface, and digest-coherent snapshot. If JS is disabled or fails, the static HTML must prove what was published.

## Architecture & Separation of Concerns
- **Git/GitHub**: Durable authority.
- **Supervisor**: Detects typed external events and makes priority-gated PL offers.
- **Project Lead**: Awarded PL chooses assignment/handoff policy. Project Lead is the operative orchestration role for now. Do not introduce a Publisher role now.
- **Runner**: Performs deterministic typed transitions via recipes.
- **HUD Evidence/Protocol Concepts**: `agent-inbox/supervisor-gui.py`, `supervisor.py`, `roster-gui.js`, and `README.md` provide reusable interaction/protocol concepts (SSE, assignment cards, streamed conversation, client_id/turn_id causality, frozen context, structured handoff, acknowledgement/retry, provenance, structured decisions). Initial recommendation: reuse protocol and interaction design in a bounded S-Core-specific UI.

## Two-Cycle Model
1. **Feedback -> Proposal:** Browser feedback -> durable GitHub request -> trusted ingestion -> committed queue item -> AI assignment -> AI-generated proposed record/comment version -> proposal committed/pushed to GitHub.
2. **Decision -> Publication:** Curator sees exact proposal -> durable GitHub decision -> decision ingestion -> accepted proposal applied transactionally -> database version committed -> live projection refreshed -> complete static tree regenerated/validated/published.

## Live-State Vocabulary
The following explicit vocabulary defines the visible live-state on the UI and queue items:
- `published`: The currently authorized and deployed baseline.
- `proposal`: An AI-generated pending change awaiting curator review.
- `awaiting_curator`: Explicit state requiring manual curator intervention.
- `stale`: Target record/version no longer matches the current baseline; requires re-proposal or rejection.
- `rejected`: Curator denied the proposal.
- `accepted-not-published`: Curator accepted the proposal but the static publication has not yet completed.

## Runner Recipes Contract
Recipes are executed by the runner. The runner does not select assignments or decide products.
### 1. Feedback Ingestion Recipe
- **Input:** GitHub request + exact record/version (`feedback:<github-repository>:<issue-or-comment-id>:<record-id>`).
- **Responsibility:** Validate trusted envelope, create idempotent committed queue item. No direct factual mutation.
- **Output:** Idempotent committed queue item and event that triggers PL scheduling.
### 2. AI Proposal Recipe
- **Input:** Committed queue item + assignment + pinned record (`proposal:<queue-item-id>:<baseline-record-version>:<recipe-version>`).
- **Responsibility:** Research evidence, generate proposal. Live streamed discussion is non-authoritative until structured handoff/commit. AI cannot apply or decide its own proposal.
- **Output:** Evidence-bearing committed proposal pushed to GitHub.
### 3. Apply/Publish Recipe
- **Input:** Proposal ID + Accepted decision ID (`apply:<proposal-id>:<accepted-decision-id>` / `publish:<database-commit>:<generator-version>`).
- **Responsibility:** Revalidate non-stale accepted decision, transactionally apply DB version, refresh live projection, regenerate full AUTOSAR+S-Core multilingual tree from latest snapshot, validate and publish only to publication branch/repository.
- **Output:** Complete static tree regenerated/validated/published.

## Exact Payload Fields
Browser never writes canonical fields directly.
`record_id`, `published_version`, `source_release`, `current_record`, `proposals`, `feedback`, `conversation_refs`, `curator_decisions`, `workflow_state`, `publication_state` (containing `database_commit`/`static_publication_commit`/`digest`).
