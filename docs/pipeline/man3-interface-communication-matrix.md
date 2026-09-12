# MAN.3 Interface & Communication Matrix (0012-05)

**Status:** Normative
**Reference:** Feature `0012-05` (Prerequisites: `0011-04`, `0012-02`)

This document defines the formal interfaces and communication channels between internal project team members (agents) and external stakeholders (User, Evaluator). It satisfies ASPICE MAN.3 requirements for managing project interfaces and commitments.

## 1. Project Interfaces

### 1.1 Internal Interfaces (Agent-to-Agent)
The core mechanism for internal communication is the **Agent-Inbox Mailbox System**.

| Interface / Party | Responsibility | Communication Channel | Cadence / Trigger | Escalation Path |
|---|---|---|---|---|
| **Implementer ↔ Integrator** | Handoff of completed CI for formal Acceptance Review. | Mailbox (`agent-inbox` thread assignment) | Event-driven (Post-Commit) | If review delayed > 4 hours, re-assign via Coordinator. |
| **Requirements Eng. ↔ Architect** | Negotiation of architectural feasibility against SWE.1 needs. | Mailbox (Decision Requests) | Event-driven (During `DEC-*` creation) | Escalate to Project Lead for priority resolution. |
| **Project Lead ↔ Team** | Task assignments, schedule adjustments, risk broadcast. | Mailbox (Broadcast `to: "all"`) | Event-driven (Milestone/Sprint start) | Supervisor override if system stalls. |

### 1.2 External Interfaces (Agent-to-Stakeholder)
The core mechanism for external communication is the **Artifact Directory (`brain/`) and User Messaging**.

| Interface / Party | Responsibility | Communication Channel | Cadence / Trigger | Escalation Path |
|---|---|---|---|---|
| **Project Lead ↔ User/Supervisor** | Requesting management decisions, reporting milestone completion, securing waivers. | Direct User Message (Transcript) or Persistent Artifact | Event-driven (Milestone Gates, Unresolvable Blockers) | Wait for User Wake-up. |
| **Integrator ↔ External Auditor** | Provision of baseline evidence and qualification test reports. | Markdown Evidence Dossiers (`docs/dossiers/`) | Release Candidate (SPL.2) | Direct notification to Stakeholder via User Message. |

## 2. Communication Commitments and Expectations

### 2.1 Mailbox Discipline
- **Same-Turn Closure**: All agents MUST acknowledge (`ack`) delivered mail only *after* acting on it or durably recording follow-up in the assigned worktree.
- **Caveman Style**: Messages must be terse fragments (e.g., `RESULT <item>. Ref: <commit>. Next: <action>.`). Maximum 1,000 characters and 10 lines. Detail must reside in repository artifacts.
- **No Stale Mail**: No message may be kept as a "reminder".
- **Decision Requests**: A formal `decision_request` requires explicit options, evidence, and deciding role specified.

### 2.2 Response Time SLAs
- **Internal Reviews**: An integrator MUST claim an integration review within 2 working cycles of broadcast.
- **Task Claiming**: Priority offers MUST be accepted or declined immediately using `offer_reply`.

## 3. Communication Records

The following artifacts act as the persistent communication records and audit trails for the project:

1. **`TODO.md`**: Tracks the state transitions and assignment claims of every discrete task.
2. **Commit History (`git log`)**: Immutable chronological log of CI modifications.
3. **`agent-inbox` Delivery Logs**: (Operated by the infrastructure) Tracks when messages were dispatched, read, and acknowledged by agents, proving communication occurred.
4. **`DEC-*` Decisions**: Durable records of architectural and requirement negotiations.
