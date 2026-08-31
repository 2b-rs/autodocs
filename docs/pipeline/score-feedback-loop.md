# S-Core Feedback Loop Process Contract

## Product Target
The management-approved product target is the next incarnation of the official 2b-rs.github site: from its index, users can reach BOTH (a) the existing AUTOSAR Adaptive documentation and (b) a first pretty-printed S-Core documentation tree; both are generated from the latest authoritative database snapshot and translated into every configured project language. There is NO requirement to use or reuse an S-Core component library for this project or publication.

## Architecture & Separation of Concerns
- **Git/GitHub**: Durable authority.
- **Supervisor**: Detects typed external events and makes priority-gated PL offers.
- **Project Lead**: Awarded PL chooses assignment/handoff policy.
- **Runner**: Performs deterministic typed transitions.
- **DHTML vs Static Relationship**: DHTML is a read-side/live projection only. It may fetch/inject record JSON, show proposal/curator/publication state, and provide context-bound live agent chat modeled on the agent-inbox Supervisor HUD. It must not mutate canonical records. Full-tree deterministic regeneration remains the durable release/publication baseline, offline/static fallback, link-validation surface, and digest-coherent snapshot. Rule to record verbatim: “DHTML shows what is happening now; static HTML proves what was published.”
- **Full Static Regeneration**: Publication authority.
- **HUD Evidence/Protocol Concepts**: `agent-inbox/supervisor-gui.py`, `supervisor.py`, `roster-gui.js`, and `README.md` provide reusable interaction/protocol concepts (SSE, assignment cards, streamed conversation, client_id/turn_id causality, frozen context, structured handoff, acknowledgement/retry, provenance, structured decisions), but not a packaged S-Core component library. Initial recommendation: reuse protocol and interaction design in a bounded S-Core-specific UI; do not make generic GUI-library extraction a prerequisite. Possible later extraction remains optional.

## Two-Cycle Model
1. Browser feedback -> durable GitHub request -> trusted ingestion -> committed queue item -> AI assignment -> AI-generated proposed record/comment version -> proposal committed/pushed to GitHub.
2. Curator sees exact proposal -> durable GitHub decision -> decision ingestion -> accepted proposal applied transactionally -> database version committed -> live projection refreshed -> complete static tree regenerated/validated/published.

Every proposal and decision is bound to exact record/proposal/source versions; stale decisions cannot apply.

## Project-Lead Scheduling Policy
Whenever new curation or review input arrives, the Supervisor creates a normal priority-gated offer to Project Leads using established atomic award rules. The awarded Project Lead decides the response:
- Hand over to another PL handling the same concern.
- Create a dependent typed-runner assignment.
- Hand the assignment to a runner directly for trivial/specified transitions.

*Do not introduce a Publisher role now. Project Lead is the operative orchestration role for now. The runner executes typed recipes and never chooses product workflow or assignment policy.*

## Recipes
Recipes are executed by the runner. The runner does not select assignments or decide products. Direct Supervisor assignment is reserved for fully mechanical event-to-recipe mappings; interpretation is performed by the awarded PL.
Recipes include: feedback ingestion, AI proposal/regeneration, and apply/regenerate/validate/publish.

## Exact Payload Fields
Browser never writes canonical fields directly.
`record_id`, `published_version`, `source_release`, `current_record`, `proposals`, `feedback`, `conversation_refs`, `curator_decisions`, `workflow_state`, `publication_state` (containing `database_commit`/`static_publication_commit`/`digest`).

## Idempotence Contracts
Retries return/resume the same result; never duplicate proposals, decisions, or publication.
- `feedback:<github-repository>:<issue-or-comment-id>:<record-id>`
- `proposal:<queue-item-id>:<baseline-record-version>:<recipe-version>`
- `decision:<proposal-id>:<curator-decision-revision>`
- `apply:<proposal-id>:<accepted-decision-id>`
- `publish:<database-commit>:<generator-version>`
- `chat:<conversation-id>:<client-id>:<turn-id>`

## Event Handlers
Every terminal recipe result must emit a durable event with an unambiguous next handler:
- ingestion complete -> proposal scheduling
- proposal committed -> curator notification
- accepted decision -> apply/publication scheduling
- publication complete -> workflow closure
