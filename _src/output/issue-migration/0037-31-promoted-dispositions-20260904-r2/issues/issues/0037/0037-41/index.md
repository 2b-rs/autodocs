---
schema_version: "1.0"
id: "0037-41"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-01"
  - "0037-03"
  - "0037-06.03"
  - "0037-45"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2086"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

PREREQ: 0037-41:0037-01, 0037-41:0037-03, 0037-41:0037-06.03, 0037-41:0037-45 Define the versioned agent-bootstrap, authority-discovery, stale-client, and instruction-cutover contract. REF: 12f1fb2b3574fe1172b42f2cbb05316b370756df **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-41`). Abgenommene Baseline `12f1fb2b3574fe1172b42f2cbb05316b370756df`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). agent-workflow.md + Schema + agent-workflow.json, gültiges JSON mit erwarteten Schlüsseln.

## Scope

- **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-41-20260816-1439.md`, `owner_token: agent:perplexity:0037-41:0037-41-20260816-1439`, request ID `0037-41-20260816-1439`, `base_commit: pending-discovery`. Prerequisites `0037-01`, `0037-03`, `0037-06.03`, and `0037-45` are terminal.

## Acceptance criteria

- **AC-001** Create `docs/pipeline/agent-workflow.md` and `issues/_schema/agent-workflow-bootstrap-v1.schema.json`
- **AC-002** classify `SANDBOX.md`, `AGENTS.md`, and `PRIVILEGED.md` as canonical human bootstrap policy and root `agent-workflow.json` as canonical machine selector with schema/contract version, agent capability class, approved runner protocol/endpoint version, authority epoch/profile (`legacy-lists` or `issue-store`), write phase (`legacy-writable`, `legacy-frozen`, `issue-store-frozen`, `issue-store-writable`, or `legacy-restored`), allowed capabilities, transaction ID, authoritative backlog paths, claim/edit/validate/close commands, minimum tool version, process links, source-policy digests, and cutover/rollback commit. Define first-read/doctor behavior without YAML or network, policy precedence, pre-cutover legacy operation, clean-restart requirement, mandatory session/claim quiescence, epoch bump at cutover/rollback/activation, per-command expected-epoch fencing immediately before every mutating compare-and-swap/write, stale cached-instruction/version/epoch handling, protected-integration rejection of direct generated-view or `TODO-<agent-id>.md` writes, atomic instruction/authority switch, rollback, and emergency diagnostics. Define and test a policy-semantic continuity matrix mapping the legacy rules for owned-work resumption, parent-package closure, autonomous intent-preserving backlog repair, `[u]` boundaries, append-only collaboration/tooling suggestions, reusable `_src/tools/` proposals, one-use runner requests, prohibition of runner escalation/notification, and throttled-grunt request economy onto the issue-store commands and records
- **AC-003** changing storage authority must not silently remove these behaviors. Explicitly reconcile current contradictions such as user-operated `run.sh`/tool prohibitions versus available local tools
- **AC-004** no instruction may require a human to execute an agent's script unless that operating mode is currently approved

## Definition of Done

Review-ready schema, state/precedence table, legacy/current/future instruction bundles, and positive/negative fixtures cover fresh agents, stale pre-cutover sessions, unsupported tool versions, missing/corrupt selector, direct legacy writes after cutover, partial instruction switch, rollback, and conflicting `SANDBOX.md`/`AGENTS.md`/pipeline guidance; every failure tells the agent to stop mutation, re-read named files, and run one exact recovery command.
