# S-Core Feedback Loop Process Contract

> [!WARNING]
> **Proposed / non-operative.** This contract does not activate a gate or
> scheduling policy. Task `0045-00` must first produce a resolved Management
> decision request, a supporting review by a distinct management-instantiated
> Architect, and one approved shared Feature/interface baseline. No `DEC-*`
> identifier or decision-record path is preallocated here.

## Product target and truth boundary

The official 2b-rs.github index shall reach both the existing AUTOSAR Adaptive
documentation and a first pretty-printed S-Core tree. Both are generated from
the latest authoritative database snapshot in every language configured by
`_src/site.json`. An S-Core component library is neither required nor implied.

**DHTML shows what is happening now; static HTML proves what was published.**
DHTML is a read-side projection of live workflow state. It is not the durable
release baseline. Deterministic full-tree generation, validation, publication
commit, and digest manifest establish the static baseline, including a
JavaScript-disabled path.

## Authority and component boundaries

- **Git/GitHub** supplies durable request, proposal, decision, commit, and
  publication provenance.
- **Supervisor** detects a trusted typed event and opens a priority-gated
  Project Lead offer. It does not choose the product disposition or contractor.
- **Awarded Project Lead** makes the explicit scheduling decision: hand off to
  a Project Lead already handling a materially similar item; create a dependent
  typed-runner assignment; or hand the same item to a runner when the action is
  trivial. The chosen branch and its durable reason are part of the result.
- **Runner recipe** validates and executes a typed awarded transition. It
  cannot assign work, select a decision branch, accept a proposal, grant
  authority, integrate, or authorize publication.
- **AI contractor** may research and propose. Streamed conversation is
  non-authoritative until a structured handoff/proposal is committed.
- **Curator** alone may accept, reject, or request revision of the proposal.
  Acceptance does not itself grant integration or release authority.
- **Integrator/release operator** independently verifies and crosses the
  applicable integration and publication gates.

The agent-inbox `supervisor-gui.py`, `supervisor.py`, `roster-gui.js`, and
`README.md` are evidence for SSE, assignment-card, causal-chat,
acknowledgement/retry, provenance, structured-handoff, and decision concepts.
They do **not** form a packaged reusable HUD or component library. Feature 0045
uses those findings to specify a bounded S-Core-specific Curator surface.

## Runner interface decision and repository boundary

“Typed Runner-role recipe” is a required application contract, not evidence
that a recipe registry already exists. Current repository evidence is:

- autodocs `agent-workflow.json` declares
  `runner_protocol=runner-request@v1` and
  `authority_epoch=legacy-writable`;
- `SANDBOX.md` makes the selector machine authority;
- `_src/tools/runner_dispatch.py` and `_src/runner/actions-v1.json` are absent;
  and
- `0037-46.01`/`0037-46.02` are historical/superseded, not current registry
  producers.

Task `0045-00` must resolve whether the proposed recipes bind to
`runner-request@v1`, the current agent-inbox assignment Runner through an
adapter, or another approved interface. Task `0045-02` must prove the resolved
choice compatible with the authoritative selector before a downstream
implementation path is bound. No downstream task may invent registry files or
infer execution authority from the word “recipe.”

One assignment has one branch/worktree and one repository write boundary.
Cross-repository parents therefore consume immutable, versioned handoffs:

- `feedback-recipe-contract@v1` and
  `feedback-ingestion-result@v1` bind the agent-inbox producer to the autodocs
  ingestion consumer; and
- `apply-publish-contract@v1` and `publication-result@v1` bind the agent-inbox
  recipe producer to the autodocs apply/generate/publish consumer.

Each handoff contains schema/version, producer repository and commit, consumer
baseline, normalized input digest, idempotence key, result/status, durable
receipt, and retry ancestry. Parent tasks verify both canonical repository
receipts and record their digests; they do not use one assignment to write
both repositories.

## Event-driven continuation

Every recipe result is durable and names either the next event/handler or a
terminal failure disposition:

1. trusted feedback ingestion complete → priority-gated proposal scheduling;
2. proposal committed and pushed → Curator notification/decision intake;
3. accepted, non-stale decision ingested → priority-gated apply/publication
   scheduling;
4. publication result committed → workflow closure or durable retry/failure.

No dispatcher may stop at “submitted” or an in-memory callback. The next step
must be reconstructible from the durable result after restart.

## Two cycles and Project Lead decision branches

### Cycle 1 — feedback to proposal

1. Browser feedback creates a durable GitHub issue/comment envelope bound to
   the exact published record/version.
2. Trusted ingestion validates transport, target, schema, staleness, and
   duplication; it commits one queue item without changing factual data.
3. Supervisor emits a priority-gated Project Lead offer.
4. The awarded Project Lead records one of the three scheduling branches above.
5. An awarded AI contractor/runner produces an evidence-bearing proposal and
   structured handoff, then pushes the proposal version to GitHub.
6. The result notifies the Curator and preserves causal chat/proposal links.

### Cycle 2 — Curator decision to publication

1. The Curator sees the exact published baseline, proposal, pretty-printed
   diff, evidence, provenance, and live conversation state.
2. The Curator writes a durable accept, reject, or request-revision decision.
3. Trusted ingestion validates authority, binding, revision, and staleness.
4. Rejection closes without factual mutation; request-revision returns through
   a priority-gated proposal offer; acceptance opens a priority-gated
   apply/publication offer.
5. The awarded Project Lead again records handoff, dependent recipe, or trivial
   same-item runner execution.
6. An authorized apply/publication execution revalidates the decision,
   transactionally mutates the database, commits the database version,
   refreshes the live projection, regenerates and validates every configured
   language, and publishes only to the authorized publication target.

## Typed records

### Feedback ingestion result

Required fields: trusted envelope reference, GitHub repository, issue/comment
ID, record ID, submitted and current record versions, queue-item ID/version,
deduplication disposition, idempotence key, durable commit/reference, next
event, and typed error/retry data. It never contains an applied factual change.

### Proposal result

Required fields: queue-item and assignment IDs, pinned baseline version/hash,
recipe version, proposal ID/version, evidence references, structured handoff,
conversation references, Git commit/push reference, idempotence key, next
event, and typed error/retry data. An AI-authored proposal has no Curator or
apply authority.

### Curator decision contract

Required fields: proposal ID/version, pinned baseline record version/hash,
Curator identity and verified authority evidence, decision revision,
`accepted | rejected | revision_requested` disposition, rationale, evidence
references, timestamp, stale-check result, idempotence key, durable GitHub
reference, and next event. A later revision is a new monotonic decision
revision; it does not overwrite history.

### Publication result contract

Required fields: proposal ID, accepted-decision ID/revision, database commit,
generator version, publication target and static publication commit, digest
manifest, configured-language set, generation and link-validation results,
workflow state, publication state, idempotence keys, retry ancestry, durable
receipt, and next event or terminal failure. `published` is reported only when
the database commit, generated tree, validation, publication commit, and digest
manifest all agree.

## Deterministic typed recipes

The recipe names below are logical interfaces. Their concrete dispatch binding
is an output of `0045-00`/`0045-02`, not a presumed current registry.

| Recipe | Validates and performs | Must not decide |
| --- | --- | --- |
| `feedback_ingestion` | Trusted GitHub envelope → idempotent committed queue item and scheduling event. | Record truth, assignee, or product disposition. |
| `ai_proposal` | Awarded queue item + pinned baseline → evidence-bearing proposal, causal chat handoff, GitHub commit/push, Curator event. | Its own acceptance, apply, or publication. |
| `apply_publish` | Accepted non-stale decision → transactional database apply/commit, live refresh, full multilingual regeneration, validation, publication receipt. | Curator disposition, integration verdict, release authorization, or target policy. |

## Exact idempotence keys

- `feedback:<github-repository>:<issue-or-comment-id>:<record-id>`
- `proposal:<queue-item-id>:<baseline-record-version>:<recipe-version>`
- `decision:<proposal-id>:<curator-decision-revision>`
- `apply:<proposal-id>:<accepted-decision-id>`
- `publish:<database-commit>:<generator-version>`
- `chat:<conversation-id>:<client-id>:<turn-id>`

For every key:

- same key and byte-equivalent normalized input returns the recorded result;
- same key with different normalized input is a conflict and performs no
  effect;
- an in-progress replay resumes only after proving the last durable boundary;
- retryable failure records error class, attempt, ancestry, safe resume point,
  and next handler;
- terminal failure records an actionable disposition, leaves later workflow
  state unadvanced, and does not claim publication;
- retries never replace or erase earlier requests, decisions, commits, or
  receipts.

## Visible state vocabulary

`proposal`, `awaiting_curator`, `stale`, `rejected`,
`revision_requested`, `accepted-not-published`, `applying`,
`publication_failed`, and `published` are distinct. The UI shall show the
authoritative reference, timestamp, and retry/failure state behind each label;
absence of a live update never rewrites the last proven static publication.

## Existing-feature boundaries

- Feature `0021` remains the historical manual/non-bypass contract.
- Feature `0035` remains requester/submission-dialog UX; `0033-13` carries its
  regressions. Feature 0045 does not redefine that ownership.
- Feature `0033` supplies trusted intake, queue, authenticated lifecycle,
  browser packaging, truthful receipt/failure, accessibility/no-JS, and
  integration-floor contracts consumed by Tasks `0045-03`, `0045-05`, and
  `0045-06`.
