# Risk integration (case A4)

This procedure is the canonical record and state machine for a risk integration. It
implements the bounded authority envelope ratified for `DEC-0044-018`. It authorizes
no particular suspension, acceptance, release, credential, service mutation, or
residual-risk decision. A4 is reached only after policy replacement and target-policy
pull-in have failed (see [`branch-workflow.md`](branch-workflow.md)).

## States and transitions

`candidate -> consulted -> voted -> veto-checked -> active -> restored -> closed`
is the only successful path. `candidate -> failed` is mandatory for any missing,
invalid, late, vetoed, non-unanimous, or unproved step. `active -> expired -> failed`
and `active -> restoration-failed -> failed` are fail-closed transitions. A retry is
a new `application_id` linked by `supersedes`; it never edits or reopens a record.
Failure is recorded as the existing `[u]` integration verdict and escalated to the
user; it is not an Acceptance path.

The three decision sessions are privileged, independent sessions and must vote
unanimously. Panel membership is not fixed: QA-Manager and Security-Manager may sit
inside the three, but both must always be consulted and their vetoes apply from
outside the panel as well. If a specialist is outside the panel, a recorded explicit
response is required; silence, absence, abstention, or substitution is not assent.
An inside-panel specialist's veto is represented by unanimity, and remains final for
the application. An outside veto is checked after panel unanimity and is likewise
final. Any veto fails the application.

## Mechanically checkable record

Every field below is required unless marked optional. Values are immutable after
creation; append a new application for corrections or retries.

| Field | Required value/validation |
|---|---|
| `schema`, `application_id`, `supersedes` | `risk-integration/v1`; globally unique ID; `supersedes` is null or a prior failed/expired ID |
| `integration`, `case`, `target_branch`, `source_branch`, `policy_baseline` | exact integration identity; `case=A4`; full refs/IDs and baseline digest |
| `reason`, `authority_refs` | non-empty reason; `DEC-0044-018`, scope-review REF, and applicable TK-2 decision refs |
| `participants` | exactly three panel entries: immutable session ID, role, privileged capability, independence statement, and session start |
| `panel_membership` | explicit QA/Security `inside` or `outside`; no inferred role or silent substitution |
| `consultations.qa`, `consultations.security` | each has consulter/session ID, location (`panel`/`outside`), requested and response timestamps, exact explicit response (`approve`/`veto`/`reject`), and evidence ref |
| `votes` | one explicit vote per panel participant, timestamped and bound to application; all `approve` for success |
| `vetoes` | QA and Security dispositions, timestamps, evidence; `none` is explicit, never inferred from silence |
| `scope` | exact policy clauses/files/branches and permitted action; exclusions stated; no open-ended or silent substitution |
| `reason`, `start`, `end`/`duration` | reason plus finite ISO-8601 start and end or finite duration; end must be computable |
| `restoration` | exact condition, responsible action, before/after baseline digests, timestamp, and evidence ref |
| `state`, `failure` | state from the transition list; failure code/evidence for every failed path |
| `created_by`, `created_at`, `record_digest` | immutable author/session, ISO-8601 timestamp, digest over canonical record |

Validity requires all IDs and refs to resolve, sessions to be distinct and
independent, consultations to precede the vote decision, explicit responses from
both specialists, unanimous panel approval, no veto, finite scope/duration, and
restoration evidence matching the recorded baseline. Expiry, missing evidence,
invalid independence, non-unanimity, or failed restoration is invalid even if work
was performed; dependent integration remains blocked under `[u]`.

## Relationship to acceptance and integration

The integrator records the A4 application and its evidence but cannot clear an
existing `[u]` verdict by this record. Acceptance reviewers cannot use it as
`Acceptance: ✓`; the application is only an input to the separately assigned
integration/acceptance process. Root/ref movement and controlled-service actions
remain governed by `SANDBOX.md`, `branch-workflow.md`, and `DEC-CAP-003`.
