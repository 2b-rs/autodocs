# Pipeline documentation

This directory contains the documentation of the project’s operating and
maintenance processes. Each statement is linked to an authoritative source and,
where possible, to the associated implementation or evidence.

## Contents

- [`core-rules.md`](./core-rules.md) — core pipeline and engineering rules (ASPICE baseline, IDs, isolation, 4-eyes principle)
- [`roles/`](./roles/) — role-specific Standard Operating Procedures (SOPs) for modular process execution
- [`roles.md`](./roles.md) — **product-domain** roles (human, AI,
  tool/validator), distinct from [`process-roles.md`](./process-roles.md)
- [`process-roles.md`](./process-roles.md) — process roles, capability-class
  mapping, and separation controls TK-1/TK-2
- [`decision-record.md`](./decision-record.md) — normative
  `decision-record@v1` Markdown contract, mandatory triggers, waivers, and
  append-only corrections
- [`processes.md`](./processes.md) — campaign process phases (0–6)
- [`campaigns.md`](./campaigns.md) — campaign types used in this repository
- [`actions.md`](./actions.md) — individual actions (ingest review, ingest
  evidence, generate source, validate, publish, archive)
- [`tools.md`](./tools.md) — catalog of project tools and their contracts
- [`reports.md`](./reports.md) — report types, locations, and retention rules
- [`build-ledger.md`](./build-ledger.md) — schema and append-only contract of
  the tracked build ledger `docs/evidence/build-ledger.jsonl` (`DEC-0043-001`)
- [`agent-execution.md`](./agent-execution.md) — capability classes and the
  sandboxed runner contract
- [`agent-workflow.md`](./agent-workflow.md) — authority discovery,
  bootstrap, stale-client, and cutover contract
- [`branch-workflow.md`](./branch-workflow.md) — branch topology, Task/Feature
  integration, claim carriage, and integration verdicts
- [`task-acceptance.md`](./task-acceptance.md) — privileged Task acceptance
  and Feature closure
- [`legacy-handoff-manifest.md`](./legacy-handoff-manifest.md) — pre-activation
  hand-over of every surviving legacy execution primitive to the `0037-46.01`
  typed-action registry or an explicit `0037-46.02` retirement trigger
- [`automation-safety.md`](./automation-safety.md) — automation-safety policy
  and findings workflow
- [`environment-doctor.md`](./environment-doctor.md) — environment and
  capability diagnosis
- [`issue-store.md`](./issue-store.md) — planned issue-store canonical paths,
  source/derived boundary, and privacy model
- [`issue-lifecycle.md`](./issue-lifecycle.md) — planned issue lifecycle,
  claims, closure, and migration behavior
- [`issue-derived-artifacts.md`](./issue-derived-artifacts.md) — planned
  regeneration DAG and source/derived matrix

The documentation reflects the legacy-authority workflow until the explicitly
approved Feature `0037` cutover. `TODO.md`, `DONE.md`, and active
`TODO-<agent-id>.md` claim files remain authoritative until that cutover.
