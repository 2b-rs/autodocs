# MAN.3 Resource Allocations & Tracking (0012-04)

**Status:** Normative
**Reference:** Feature `0012-04` (Prerequisite: `0012-03`)

This document fulfills ASPICE MAN.3 requirements for explicitly assigning resources, confirming availability and competence, communicating authority, and defining the retention and escalation of actual resource use during the managed execution of the `virtualized-automotive-ecu` project.

## 1. Resource Allocations by Role and Process Phase

The project execution spans four core campaigns (A, B, C, D) defined in `man3-project-management-plan.md`. The named "human" resources (LLM agents) are assigned to these phases based on their assessed competence (`man3-resource-needs.md`).

### 1.1 Process Phase Allocations

| Role / Capability | Process Group | Assigned Agent(s) | Primary Responsibilities & Authority |
|---|---|---|---|
| **Project Lead** | MAN.3, MAN.5 | Jadzia, Benjamin | Project planning, risk escalation, milestone approval, and cross-functional coordination. |
| **Requirements Engineer** | SWE.1 | Julian | Derivation of software requirements, baseline maintenance, traceability matrices. |
| **Architect** | SWE.2 | Odo | Structural definition, interface design, hardware-software mapping, `DEC-*` record approvals. |
| **Developer / Implementer** | SWE.3, SWE.4 | Worf, Nog, Jake | Detailed design, unit construction, static analysis, unit test coverage implementation. |
| **QA / Integrator** | SWE.5, SWE.6, SUP.8 | O'Brien, Kira | Integration test execution, PR merges, baseline management, configuration audits. |
| **Compliance Officer** | SUP.1, MAN.6 | Quark | Metric collection validation, process compliance checks, non-conformance logging. |

*Note: Any agent assigned a task must possess the minimum configured capability (e.g., `privileged` vs. `unprivileged`) for their respective domain.*

## 2. Communication of Responsibilities and Authority

- **Role Assignment:** A defined role is communicated to the agent context natively via the `agents.json` persona block (e.g., `"role": "Requirements Engineer"`).
- **Execution Authority:** The `agent-inbox` dynamically tracks authority. The `TODO.md` artifact assignment acts as the formal, isolated work package authorization (e.g., `@julian`).

## 3. Allocation and Utilization Tracking

During execution (Feature `0018`), actual resource use MUST be retained and evidenced exactly as it occurred:

1. **State Tracking**: `agent-inbox` maintains a `roster.json` file providing a real-time point-in-time view of which agent is `busy` on which specific task ID, along with start timestamps.
2. **Effort Logging**: The completion of a task (`TODO.md` moved to `DONE.md`) creates an immutable artifact linking the assigned agent to the git commit hash (`REF:`).
3. **Usage Archiving**: System execution logs (`.system_generated/tasks/`) store the explicit tool call volumes, which translates directly to LLM token consumption records.

## 4. Escalation Paths for Resource Shortages

In the event of a resource constraint or bottleneck, the following escalation procedures MUST be executed:

### 4.1 Token Quota Exhaustion (API Rate Limits)
- **Detection**: Tooling administrator receives HTTP 429 warnings from the provider platform.
- **Escalation**:
  1. Temporary suspension of asynchronous background validation sweeps.
  2. Prioritization constraint: Mailbox assigns `priority` tasks only (blocking path to Milestone).
  3. If exhaustion persists > 4 hours, Project Lead adjusts the baseline milestone schedule via a formal MAN.3 plan revision.

### 4.2 Agent Bottlenecks (e.g., Integrator Overload)
- **Detection**: `roster.json` indicates an Integrator agent has > 5 `ready for review` tasks queued in its mailbox.
- **Escalation**:
  1. The Project Lead is authorized to temporarily grant `privileged` reviewer capability to an alternate, non-authoring agent from the Developer pool to clear the integration queue.
  2. The separation of duties constraint (`author != reviewer`) MUST remain mathematically enforced during this temporary reallocation.

### 4.3 Competence / Capability Gaps
- **Detection**: An agent repeatedly fails Four-Eyes reviews (Fallback Count threshold breached) or attempts unprivileged operations on privileged boundaries.
- **Escalation**: The task is formally marked `BLOCKED` in `TODO.md` and returned to the coordinator for reassignment to an agent with the proven capability class.
