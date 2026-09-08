# Preparing structured Management decision requests

**Status:** Normative preparation guidance for the existing
`decision-request@v1` workflow. It clarifies how to formulate and verify a
request; it does not change decision authority, gate reach, the tool schema,
GUI behavior, or the assignment state machine.

**Provenance:** Management instruction in agent-inbox thread
`decision-template-clarity-20260901` (2026-08-31); existing agent-inbox
`decision_request`, `decision_request_from_preparation`, and `decision_status`
contracts at `agent-inbox/main@d4095e64d174f546502b8cf93930084d455b5e35`;
Management decision `DEC-0044-036`.

## 1. Preparation requirements

| ID | Requirement | Binary acceptance intent |
|---|---|---|
| `REQ-DTP-01` | A preparer MUST create one durable request for exactly one decision question. | The question can be answered by selecting exactly one supplied option without answering a second question. |
| `REQ-DTP-02` | The preparer MUST classify the question as binary or multi-option before submission. | Binary has exactly `YES` and `NO`; multi-option has one set of at least two mutually exclusive choices. |
| `REQ-DTP-03` | The prepared title MUST begin with the affected Feature or Task ID and state the recommendation, option count, and expected signature-wave count. | A reader can identify all four values from the title alone. |
| `REQ-DTP-04` | Every option MUST state its observable effects and consequences; exactly one supplied option MUST be recommended with a reason. | No option effect is implicit, and the recommendation names one existing option ID. |
| `REQ-DTP-05` | The preparation MUST distinguish the submitter from the authorized resolver and name the immediate downstream continuation plus any known later decision or review. | No submitter is presented as resolver merely because they created the request; follow-on work is explicit. |
| `REQ-DTP-06` | Before hold reporting or handoff, the preparer MUST verify that the exact created decision ID reports `pending`. After resolution, continuation MUST use that same ID and verify `resolved` plus the selected option. | Both checks are reproducible through `decision_status`; a title, mail, or GUI card is insufficient. |
| `REQ-DTP-07` | The preparer MUST treat mail and GUI views as projections, never as the durable request or resolution authority. | Removing or misrendering a projection cannot change the status asserted by the durable exact-ID lookup. |
| `REQ-DTP-08` | Before creating a request, the preparer MUST define its semantic identity and check durable request state for an existing match. | An unchanged question is reused rather than duplicated, while a materially changed question carries an explicit lifecycle relation. |
| `REQ-DTP-09` | The request service MUST provide an atomic create-or-return operation for semantic identity. | Concurrent equivalent submissions return one durable request ID rather than allocating competing requests. |
| `REQ-DTP-10` | Ambiguous identity matches or conflicting resolutions MUST fail closed. | No continuation, new request, or inferred answer occurs until the durable conflict is reconciled by the authorized resolver. |

These requirements are additive to the existing tool's required evidence,
option, recommendation, assignment-hold, and authority fields. They do not
authorize the preparer to decide, resolve, waive, accept, integrate, or release
anything.

## 1.1 Semantic identity, reuse, and supersession

Before invoking either request-creation operation, record a semantic identity
for the decision. It consists of the exact affected `item`, normalized single
`question`, `deciding_role`, `paused_action`, mutually exclusive option IDs and
their meanings, affected work products and processes, and the material evidence
that makes the authority choice necessary. Presentation-only wording, mail
subjects, GUI grouping, timestamps, and the submitter's identity are not
semantic differences.

The preparer MUST query the durable request registry with `decision_list` and
confirm candidate matches with `decision_status` before creation:

1. An exact semantic match in `pending` state is reused. The preparer cites and
   hands off the existing exact decision ID; creating another request is
   prohibited.
2. An exact semantic match in `resolved` state is already the answer. The
   preparer records that exact ID and selected option and applies the ordinary
   continuation checks; reopening or recreating the question is prohibited.
3. A materially changed question MUST name exactly one predecessor ID and one
   lifecycle relation: `supersedes`, `narrows`, `widens`, or
   `replaces-question`. Its permanent preparation record explains the semantic
   change and why the predecessor's answer no longer decides the new question.
   A new title, submitter, assignment, mail thread, or recommendation alone is
   not a material change.
4. Multiple plausible matches, incompatible predecessor chains, or conflicting
   resolved selections are ambiguous. Stop creation and continuation until the
   authorized resolver reconciles the durable records. Do not select the most
   convenient record or manufacture a supersession.

This client-side check is mandatory but cannot prevent concurrent races. The
request service therefore MUST enforce the same semantic identity at its
transaction boundary with an atomic **create-or-return** operation: return the
existing matching ID or create exactly one new ID. A check-then-create sequence
without this service-boundary guarantee is not a conforming implementation.

## 1.2 Authority distinctions

Decision lifecycle state never creates authority. Apply these boundaries:

- `authority:supervisor`, when present in an authoritative record, identifies
  the Supervisor authority defined by that record. The current user may also
  exercise authority explicitly within their own scope. Neither authority is
  inferred from a sender name, mailbox delivery, GUI control, assignment,
  offer, or task ownership.
- A Supervisor assignment coordinates who prepares or executes work. It does
  not authorize the assignee or Supervisor to choose an option, invent a
  waiver, or supersede a decision unless the exact governing record separately
  grants that decision authority.
- Management-consultation (`mancons`) may triage a request and may record a
  resolution only when an authorized instruction explicitly selects an option
  or the governing record makes exactly one supplied option uniquely
  predetermined. It MUST NOT invent a choice, waiver, supersession, or altered
  question, and uncertainty fails closed to the named deciding role.
- Mail, GUI state, submitter identity, assignment, and offer/award state are
  coordination or projections. None proves authority, a durable request, a
  resolution, Acceptance, or permission to continue.

## 1.3 Management-request eligibility

For an integration or Acceptance dispute, use the delegated escalation ladder
in [`integration-flow-control.md`](integration-flow-control.md) before preparing
a Management request: same-slot actionable rework, then one documented
trilateral technical-resolution round among producer, reviewer, and Coordinator
or Architect. The round records shared facts, positions, attempted options or
corrections, the authority boundary, its outcome, and the exact remaining
question.

Prepare a Management request only if that remaining question is non-delegable:
a product or policy choice, material architecture, authority, material risk,
external effect, public release, or waiver. A `decision-record@v1` trigger
requires a durable record but does not automatically make Management the
resolver. Do not create a generic request for a stale branch, failed hygiene or
tests, an ordinary finding, bounded rework, reviewer selection, capacity, or a
contract correction determinable inside existing authority.

Examples: “Which of these two incompatible product behaviors is authorized?”
may be eligible after the trilateral record proves the contract does not answer
it. “Should the Implementer fix the failing recovery test?” is not eligible; it
returns to same-slot `[p]` rework. “May independence be waived?” is eligible
only as an explicit waiver question and the round itself cannot answer it.

## 2. Model one question

### Binary question

Use a binary request only when the deciding authority must answer one
proposition and there are exactly two exhaustive, mutually exclusive outcomes.

- Option ID `YES` states what becomes permitted, required, changed, or retained.
- Option ID `NO` states what remains prohibited, paused, unchanged, or returned
  for rework.
- Both options state downstream effects and remaining risks. `NO` is not an
  empty default.

A choice among three approaches is not binary. Creating “approve A?”, “approve
B?”, and “approve C?” as three requests permits contradictory combinations and
does not produce one selection.

### Multi-option question

Use one multi-option request when the authority must choose exactly one member
of a set. The set MUST be collectively sufficient for the present decision and
each option MUST exclude every other option for that request.

If two choices could both be selected, they are either separate decision
questions or parts of a single composite option whose combined consequences
must be stated. Do not disguise independent choices as options in one set.

## 3. Title, identities, and signature waves

Use this preparation-title pattern:

```text
<Feature/Task ID> — recommend <option ID> — <N> options — <W> signature waves — <short question>
```

The current tool derives dashboard grouping from `item` and renders the
question. Set `item` to the exact Feature/Task ID. The transport-generated
`DECISION NEEDED` mail prefix is not part of the preparation title and need not
be reproduced in the question.

Record these roles and transitions in the permanent preparation artifact:

- **Submitter:** the Requirements Engineer or other preparer who gathers
  evidence and invokes the request tool.
- **Resolver:** the exact `deciding_role` authorized to select the current
  option. Submission never makes the submitter the resolver.
- **Downstream continuation:** the one immediate action, handler, assignment,
  or gate that may proceed after this request is resolved and every separately
  required authority record exists.
- **More decisions follow:** `NO`, or `YES` followed by each already-known
  question and its intended deciding role. A known later choice is not silently
  bundled into the present question.
- **Expected signature waves:** the number and ordered purpose of distinct
  authority confirmations expected before the downstream result is fully
  authorized. A wave can be the present Management resolution, a later
  Architect scope review, or another separately governed approval. Counting a
  wave predicts the workflow; it neither creates the authority nor proves the
  signature.

`Expected signature waves`, `More decisions follow`, and the preparation title
are preparation metadata, not new `decision_request` tool fields. Keep them in
the permanent preparation artifact and cite that artifact through
`permanent_records`. Do not rely on unknown tool keys being persisted.

## 4. Map the preparation to the enforced request

The existing request call remains authoritative for its own schema:

| Preparation concern | Existing request field or evidence |
|---|---|
| affected Feature/Task | `item` |
| the single question | `question` |
| action paused for this answer | `paused_action` |
| observed evidence | `observed_fact` plus `permanent_records` |
| risk of continuing without the answer | `risk_if_continued` |
| authorized resolver role | `deciding_role` |
| mutually exclusive selection set | `options[]` with stable `id`, `summary`, and `consequences` |
| recommended selection | `recommendation.option_id` and `recommendation.reason` |
| products and processes affected | `affected_work_products` and `affected_processes` |
| ticket that must wait | `assignment_id`, when applicable |
| wave plan, follow-on choices, and immediate continuation | permanent preparation artifact referenced in `permanent_records` |

Use `decision_request_from_preparation` when a prepared JSON or Markdown JSON
artifact is the source. Use `decision_request` for direct structured input.
Ordinary mail, prose saying “DECISION NEEDED”, and a printed template do not
create a request.

## 5. Handoff and resolution checks

After submission:

1. Capture the exact decision ID returned by the successful request call. Do
   not reconstruct it from the item, title, filename, or GUI route.
2. Call `decision_status` with that exact ID.
3. Require `status=pending` before reporting a hold or handing the decision to
   Management. When an `assignment_id` was supplied, separately confirm the
   returned request is linked to that assignment; do not infer the link from a
   mail thread.
4. Handoff names the exact ID, the permanent preparation record, the deciding
   role, and the paused action.
5. After an answer notice, call `decision_status` again with the same ID.
6. Require `status=resolved` and record the returned selected option before
   executing the named continuation.
7. Verify every later signature wave independently. Resolution of the current
   question does not create a later Architect, specialist, Acceptance,
   integration, risk, or release decision.

An unknown ID, unexpected status, mismatched assignment, missing option, or
different resolved ID stops the handoff or continuation until the durable state
is reconciled. It is not repaired by resending mail or creating a second
request for the same unchanged question.

## 6. Scope boundary

This playbook trains preparers and makes false request/handoff claims
observable. It does not change the minimum number of tool options, add tool
fields, choose Management's answer, instantiate an Architect, count a GUI card
as a signature, alter assignment transitions, allocate a `DEC-*` identifier,
or replace the final record requirements in
[`decision-record.md`](decision-record.md).
