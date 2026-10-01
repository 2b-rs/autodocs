# Capability matching (`0044-05`)

**Status:** Pilot governance record for Task `0044-05` (Feature `0044`, `RQ-CB-01..03`,
Management decision `DEC-0044-004`, architecture baseline `DEC-0044-025`). Machine-readable
authority is the three closed schemas below; this page is their human-readable rendering,
activation boundary, and operational contract. Where this page and a schema disagree, the
schema wins.

**Checker/matcher:** `python3 _src/tools/capability_match.py --profile <profile.json>
--descriptor <descriptor.json> [--descriptor <path> ...] [--agent-id <exact-id>] [--json]` —
deterministic, stdlib-only, reads only the given files, no network/credentials/Git/wall-clock
state.

## What this document is, and what it is not

It defines a deterministic, no-AI matcher: an Architect writes a machine-readable Task
requirement profile; the matcher compares it against one or more agent capability
descriptors and returns every capable descriptor with explainable, stably ordered
rejections. The orchestrator — not the Architect, not the matcher — chooses among eligible
agents.

Reading or running the matcher:

- activates no repository-wide dispatch enforcement,
- grants no authority, assignment, ownership, independence, Acceptance, waiver, specialist
  approval, or release permission,
- credits no historic dispatch retroactively ("no grandfathering" — see below),
- and does not widen a subagent's write scope, capability class, or process role beyond
  what the dispatcher's briefing states under `AGENTS.md`'s "Dispatching a subagent"
  four mandatory fields.

**Exact non-activation wording (binding, must appear verbatim here and in `AGENTS.md`):**

> This pilot requirement becomes operative only when this governance commit and the bound `0044-05.02` product are both reachable from `main`; it does not activate repository-wide dispatch enforcement, grant authority, or credit historic dispatches.

## Legacy schema distinction

`issues/_schema/agent-capability-v1.schema.json` (the legacy two-class runner descriptor,
accepted under `0037-45`) is **preserved unchanged, byte-for-byte**. The matcher does not
read, migrate, or supersede it. `agent-capability-descriptor@v1` below is a **new, distinct**
schema owned by `0044-05`; a legacy `agent-capability@v1` document given to the matcher is
rejected as an unsupported schema (exit `2`), not silently accepted or upgraded. Any future
migration of the legacy schema is a separate, explicit Task.

## No-grandfathering

Broad activation of capability-matched dispatch requires an explicit `0044-08` decision and
its own evidence. No dispatch performed before that decision is retroactively credited,
validated, or assumed compliant merely because a matching profile/descriptor pair could in
principle have been constructed for it after the fact.

## Contracts

### Task requirement profile (`task-requirement-profile@v1`)

Closed object (`additionalProperties: false`). Required fields: `schema`, `profile_id`,
`task_id` (`^[0-9]{4}-[0-9]{2}(\.[0-9]{2})?$`), `process_role`, `capability_class`
(`sandboxed-grunt`/`unprivileged`/`privileged`), `execution_needs`
(`none`/`runner`/`direct`), `required_rights`, `required_data_handles`, `required_tools`
(unique sorted arrays), `token_budget_class`, `context_budget_class`
(`small`/`medium`/`large`/`very-large`), `cognitive_demand`
(`low`/`medium`/`high`/`critical`), `required_assurances`, `sources` (requirement/decision/
architecture/evidence/assumption bindings), `test_scope`, and `resource_bounds`.

Cross-field rules enforced by the schema/matcher: `sandboxed-grunt` permits `execution_needs`
`runner` or `none`, never `direct`; `unprivileged`/`privileged` permit `direct` or `none`,
never `runner`; an `Integrator` role requires `privileged` plus `acceptance.review` and
`integration.checkpoint` where applicable; any profile requiring `acceptance.review`,
`integration.checkpoint`, or `feature.close` requires `privileged`.

### Agent capability descriptor (`agent-capability-descriptor@v1`)

Closed snapshot object, deliberately distinct from legacy `agent-capability@v1`. Required
fields: `schema`, `descriptor_id`, `agent_id`, `process_roles`, `capability_class`,
`execution_routes`, `rights`, `data_handles`, `tools`, `token_budget_class`,
`context_budget_class`, `cognitive_classes_served`, `assurances`, `capacity_status`
(`available`/`unavailable`/`unknown` — the latter two always reject), `snapshot_reference`.
No secrets, raw credential paths, or model marketing names. `sandboxed-grunt` never has
`direct`; `unprivileged`/`privileged` never have `runner`.

### Match result (`capability-match-result@v1`)

`schema`, `matcher_version`, `profile_id`, `profile_sha256`, sorted `descriptor_sha256`
bindings, `status` (`single-eligible`/`multiple-eligible`/`none-eligible`/`invalid-input`),
sorted `eligible_agent_ids`, sorted `rejections` (each with `agent_id`, `descriptor_id`, all
applicable stable reason codes in fixed order), and a constant `non_authority_notice`
restating the non-authority boundary above.

## Eligibility and stable rejection codes

A descriptor is eligible only when capacity is `available`, its `process_roles` includes the
required role, its capability class is compatible (`privileged` required → only `privileged`
actual; `unprivileged` required → `unprivileged` or `privileged`; `sandboxed-grunt`+`runner`
required → only `sandboxed-grunt` with `runner`; `sandboxed-grunt`+`none` required → any class
with `none`), its `execution_routes` includes the required `execution_needs`, every required
right/data-handle/tool/assurance is present, its token/context budget rank meets or exceeds
the requirement, and the required `cognitive_demand` is explicitly in
`cognitive_classes_served`. Extra descriptor capabilities never widen the Task contract or
suppress a rejection — privileged class cannot satisfy a runner route, and a right string
cannot override a class or role conflict.

Rejection reasons are emitted in this fixed order, one entry per applicable failure:
`CAPACITY_UNAVAILABLE`, `CAPACITY_UNKNOWN`, `PROCESS_ROLE_MISSING`,
`CAPABILITY_CLASS_INCOMPATIBLE`, `EXECUTION_ROUTE_MISSING`, `RIGHT_MISSING`,
`DATA_HANDLE_MISSING`, `TOOL_MISSING`, `TOKEN_BUDGET_INSUFFICIENT`,
`CONTEXT_BUDGET_INSUFFICIENT`, `COGNITIVE_CLASS_UNSERVED`, `ASSURANCE_MISSING`,
`AUTHORITY_CONSTRAINT_FAILED`. Invalid input uses separate `INPUT_*`/`SCHEMA_*` codes and
never produces an eligibility claim.

## CLI, exit codes, and failure behavior

```text
python3 _src/tools/capability_match.py \
  --profile <task-requirement-profile.json> \
  --descriptor <agent-capability-descriptor.json> [--descriptor <path> ...] \
  [--agent-id <exact-id>] [--json]
```

- Batch mode exit `0`: at least one eligible descriptor (including `multiple-eligible`).
- Batch mode exit `1`: valid inputs, no eligible descriptor.
- Self-check (`--agent-id`) exit `0`: the named agent is eligible; exit `1`: present but
  rejected.
- Exit `2`: malformed/unsupported schema (including a legacy `agent-capability@v1` input),
  duplicate JSON key, duplicate `descriptor_id`/`agent_id`, non-canonical array order,
  requested agent absent, I/O failure, or internal failure. **Exit `2` is never a non-match**
  — a caller must not treat it as "no eligible agent."
- Human output is at most ten summary lines; `--json` is canonical UTF-8 JSON, sorted keys,
  compact separators, exactly one trailing LF.

## Failure and recovery

- Invalid or inconclusive matching **never** falls back to AI-based selection. It returns
  exit `2` or a `none-eligible` result, and the existing authority route (the dispatcher,
  under `AGENTS.md`) decides whether the profile or descriptor must be corrected.
- A descriptor's capacity dropping after dispatch does not rewrite history: record a new
  descriptor snapshot/result and route through Task `0044-06`'s overwhelmed-agent path.
- Before `0044-08`, rollback is deletion/reversion of this pilot's briefing wiring on a
  reviewed governance candidate; schema versions, match results, and findings are retained,
  never deleted.
- Schema supersession is strictly additive: this pilot never rewrites or deletes legacy
  `agent-capability@v1` or prior result evidence.

## Tool registration

See [`tools.md`](tools.md) for the tracked-tool table entry.

## Provenance

Architecture baseline: `docs/campaign-evidence/0044-05/capability-matcher-architecture.md`
(`0044-05.01`, Architect `data`). Product: `_src/tools/capability_match.py`,
`_src/tests/test_capability_match.py`, and the three schemas under `issues/_schema/`
(`0044-05.02`, Implementer `gabriel`). This adoption page and its `AGENTS.md` counterpart:
`0044-05.03`, Implementer `belanna`, distinct from Architect `data` and from the separately
assigned Integrator who reviews the complete parent `0044-05` package before any `main`
advance.
