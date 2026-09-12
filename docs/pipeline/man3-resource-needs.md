# MAN.3 Resource & Competence Needs (0012-03)

**Status:** Normative
**Reference:** Feature `0012-03` (Prerequisite: `0012-02` Integrated Project Plan)

This document specifies the required resources, roles, authorities, competencies, and infrastructure necessary to execute the lifecycle defined in the `virtualized-automotive-ecu` project. It fulfills ASPICE MAN.3 requirements for resource planning and competency determination.

## 1. Human Resource Equivalents (Agent Roster)
Since execution is driven by autonomous LLM agents acting under defined personas, "human resources" translate to agent instances and their associated provider quotas.

### 1.1 Quantities & Availability
- **Active Roster Target**: At least 8 named agent identities operating concurrently (e.g., Julian, Kira, Worf, Jadzia, O'Brien, Odo, Jake, Nog, Quark).
- **Availability Constraint**: Agents are available 24/7, subject only to strict provider API rate limits and token quotas.
- **Provider Quotas**: Minimum of 1M input tokens and 100K output tokens per day across all active runtime providers (e.g., `codex`, `claude`).

### 1.2 Competency Needs & Role Authority
Every agent is mapped to specific competencies based on their designated `role` and `capability_class`.
- **Architect / Technical Lead**: Authorized to make structural decisions (`DEC-*`), define component interfaces, and approve `G-ARCH` gates. Must hold `privileged` capability for repository-wide analysis.
- **Requirements Engineer**: Authorized to negotiate and baseline `REQ-*` and `SWR-*` records. Holds `unprivileged` capability.
- **Integrator / QA**: Authorized to fast-forward merges, verify 4-eyes compliance, and execute the final CI regression suite. Holds `privileged` capability.
- **Developer / Implementer**: Authorized to mutate code within explicitly assigned, item-owned worktrees. Holds `unprivileged` or `sandboxed-grunt` capabilities.

### 1.3 Qualification Actions & Training Plans
- **Qualification Action**: Newly instantiated agents must read the core governance files (`AGENTS.md`, `branch-workflow.md`, `TODO.md` headers) upon session start before executing work.
- **Independence Safeguard**: The system enforces separation of duties. An agent who implements a task (`@author`) cannot mathematically approve its own Acceptance review.

## 2. Tools, Licenses, and Infrastructure
### 2.1 Software Toolchain
- **Version Control**: Git (minimum v2.30) enforcing fast-forward-only merges and cryptographically signed commits.
- **Automation / Orchestration**: Custom `agent-inbox` MCP server for priority offer management, asynchronous mailbox communication, and state locking.
- **Validation**: Python 3.11+ with `pytest` for unit testing and JSON Schema validation for artifact constraints.

### 2.2 Material & Environment Resources
- **Execution Environments**: Ephemeral, isolated local environments (`/tmp/` or designated `devel/` paths) with strict read-only boundaries outside the assigned Git worktree.
- **Data Resources**: Access to the formalized `docs/dossiers/` context and baseline definition schemas.

## 3. Resource Allocation Tracking
Actual assignment of these resources to specific `TODO.md` work packages will be conducted in task `0012-04` and actively operated/evidenced in `0018-02`. During execution, the `agent-inbox` `roster.json` dynamically tracks which agent (resource) is currently `busy` on which `task`, providing real-time allocation visibility.
