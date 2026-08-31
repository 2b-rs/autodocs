# Claim: decision-template clarity and preparer guidance

owner_token: agent:beverly:decision-template-clarity-20260901:1788218125381-26c2d7f5
assignment_id: 1788218125381-26c2d7f5
coordination_kind: user-directed governance-documentation package; no unrelated `TODO.md` Task is claimed
state: [p]
base_commit: 87144c00363b12f39d97633876b9b3f324e0f1f8
branch: decision-template-clarity-20260901
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/decision-template-clarity-20260901
capability_class: unprivileged
execution_authority: direct local execution in the item-owned worktree and exact awarded paths only
startup_review: AGENTS.md; SANDBOX.md; docs/pipeline/roles/requirements-engineer.md; docs/pipeline/core-rules.md; offer and atomic award 1788218125381-26c2d7f5; supervisor interim rule 1788218033829-dbb27fa3; branch/worktree/base/status verification

## Assignment and capability reconciliation

The atomic award assigns Requirements Engineering and Governance Documentation
for decision-request template specification and preparer training. Its briefing
labels the capability class `privileged`, while the current runtime profile and
`docs/pipeline/agent-roster.md` identify Beverly as `unprivileged`. Mail and an
award do not grant privilege, so the lower observed class governs. The awarded
documentation work is executable without privileged authority; this claim does
not authorize Acceptance, integration, decision resolution, `DEC-*` allocation,
publication, `DONE.md`, or advancing `main`.

## Exhaustive write scope

- `docs/pipeline/decision-record.md`
- `docs/pipeline/decision-request-preparation.md`
- `docs/pipeline/README.md`
- `TODO-beverly-decision-template-clarity-20260901-1788218125381-26c2d7f5.md`

## Required result

Clarify one-request-per-question decision modeling; distinguish binary
`YES`/`NO` from one mutually exclusive multi-option set; prohibit one yes/no
request per option; require identity, recommendation, option count,
consequences, signature waves, submitter/resolver, continuation, and follow-on
decision disclosure; require exact pending-state verification before handoff
and exact-ID resolution verification afterwards; and explain that mail/GUI
projection is informational rather than authoritative. Add concise good/bad
examples derived from the `0045-00` incident without personal attribution.

## Boundaries and next step

This is clarification and training only. It must not change decision authority,
gate reach, tool schemas, GUI behavior, or state-machine behavior. Inspect the
current scoped guidance and incident evidence, derive the smallest consistent
documentation change, validate focused links/content plus repository process
doctors and `git diff --check`, then commit the exact awarded paths and report
the candidate SHA for independent review/integration.

## Evidence and validation

- The enforced workflow was checked against agent-inbox
  `main@d4095e64d174f546502b8cf93930084d455b5e35`: its `AGENTS.md`, `README.md`,
  `agent_inbox_mcp.py`, and `test_agent_inbox.py` confirm durable request
  creation, required evidence/options/recommendation, optional assignment hold,
  exact-ID `decision_status`, and the informational dashboard projection.
- `docs/pipeline/decision-request-preparation.md` records seven atomic,
  binary-verifiable requirements (`REQ-DTP-01` through `REQ-DTP-07`), the
  binary/multi-option distinction, title and authority-wave metadata, enforced
  field mapping, pre/post handoff checklist, and unattributed `0045-00`
  good/bad examples.
- `docs/pipeline/decision-record.md` now links unresolved request preparation
  to the final append-only decision record without changing the canonical
  record fields, authority, gate reach, or correction rules. The pipeline index
  links the new playbook.
- `git diff --check`: pass.
- `process_doc_doctor.py --root . --json`: `ok=true`; 248 documents, two
  errors, 37 findings. A clean archive of pinned base
  `87144c00363b12f39d97633876b9b3f324e0f1f8` reports 247 documents and the
  same two errors, 37 findings, and identical finding classes. The candidate
  adds no finding class; the new document is scanned.
- Scope check: the only changed paths are the four paths declared above. The
  candidate changes no tool, GUI, state-machine, backlog, `DEC-*`, Acceptance,
  integration, publication, or `main` state.

## Current step

The documentation candidate and claim evidence are ready for the substantive
path-limited commit. After that commit, finalize this claim with the exact
implementation REF in a separate bookkeeping commit and transition the
assignment to review.
