# A4 worked examples

These examples are evidence of record shape only; neither authorizes a real
suspension.

## Successful shape: QA inside, Security outside

```yaml
schema: risk-integration/v1
application_id: A4-2026-08-22-001
supersedes: null
integration: feature-0044/task-0044-02 -> feature-0044
case: A4
target_branch: refs/heads/feature-0044
source_branch: refs/heads/0044-02
policy_baseline: sha256:BASELINE
reason: "Replacement and target-policy pull-in still leave incompatible policy clauses."
authority_refs: [DEC-0044-018, scope-review:69403bc42]
panel_membership: {qa: inside, security: outside}
participants:
  - {session: sess-integrator-1, role: Integrator, privileged: true, independent: true}
  - {session: sess-qa-2, role: QA-Manager, privileged: true, independent: true}
  - {session: sess-architect-3, role: Architect, privileged: true, independent: true}
consultations:
  qa: {location: panel, requested_at: 2026-08-22T10:00:00Z, response_at: 2026-08-22T10:01:00Z, response: approve, evidence: ev-qa-panel}
  security: {location: outside, consulter: sess-security-4, requested_at: 2026-08-22T10:00:00Z, response_at: 2026-08-22T10:03:00Z, response: approve, evidence: ev-security-explicit}
votes: [{session: sess-integrator-1, response: approve}, {session: sess-qa-2, response: approve}, {session: sess-architect-3, response: approve}]
vetoes: {qa: none, security: none}
scope: {clauses: [policy/A, policy/B], permitted_action: "merge this source into this target", exclusions: [release, credentials, services]}
start: 2026-08-22T10:05:00Z
end: 2026-08-22T10:20:00Z
restoration: {condition: "merge decision recorded and policy restored", action: "restore target baseline", evidence: [before:BASELINE, after:RESTORED]}
state: closed
```

QA's panel vote is the unanimity gate; Security's separate explicit response is
still mandatory. The record cannot be accepted if either consultation is absent.

## Successful shape: both specialists outside

The same schema uses `panel_membership: {qa: outside, security: outside}` and five
distinct session IDs. The three panel votes must all be `approve`, followed by two
explicit `approve`/`none` veto dispositions with timestamps. Neither specialist's
silence is a no-veto response.

## Fail-closed shape

```yaml
schema: risk-integration/v1
application_id: A4-2026-08-22-002
supersedes: A4-2026-08-22-001
panel_membership: {qa: outside, security: outside}
votes: [approve, approve, approve]
consultations: {qa: {response: approve}, security: {response: missing}}
vetoes: {qa: none, security: unknown}
state: failed
failure: {code: missing-response, action: "record [u] integration verdict and escalate to user"}
```

Although the panel was unanimous, the missing Security response makes this
application invalid. It cannot become active, and a retry must create another ID.
