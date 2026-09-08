# Maintained Risk Register & Tracking Baseline (0017-02)

## 1. Document Control & Register Metadata
- **Register ID**: `REG-RSK-20260829-01`
- **Feature / Task**: `0017-02` (PREREQ: `0017-01`)
- **Governing Strategy**: [`docs/pipeline/man5-risk-management-strategy.md`](file:///Users/tobias.anton/devel/agent-inbox/docs/pipeline/man5-risk-management-strategy.md)
- **Status**: `ACTIVE / MAINTAINED`
- **Next Review Gate**: `G-DEV / Sprint Review`
- **Assigned Custodian**: `jadzia` (Risk Manager / Project Lead)

---

## 2. Active Risk Register Matrix

| Risk ID | Category | Risk Description | Initial $L$ (1-5) | Initial $I$ (1-5) | Initial RPN | Treatment Strategy | Mitigation Action & Tracking Ref | Residual $L$ | Residual $I$ | Residual RPN | Current Status | Owner |
|---|---|---|:---:|:---:|:---:|---|---|:---:|:---:|:---:|---|---|
| `RSK-TECH-001` | TECH | Real-time cyclic task scheduling jitter exceeds 50µs bound under peak CPU load. | 3 | 4 | **12** (Med) | Mitigate | Enforce static task priority preemption and eliminate dynamic memory allocations (`REQ-STK-001`, `REQ-STK-005`). Verified in `test_cyclic_timing`. | 1 | 4 | **4** (Low) | MITIGATED | `kira` (Architect) |
| `RSK-PROC-002` | PROC | Concurrent agent worktree collisions and non-fast-forward merge races on `main`. | 4 | 4 | **16** (High) | Mitigate | Mandate isolated branch-local worktrees per task (`0011-04`, `REQ-STK-007`) and enforce `git merge --ff-only` preflight verification in CI. | 1 | 3 | **3** (Low) | CONTROLLED | `benjamin` (Dispatcher) |
| `RSK-PROC-003` | PROC | Shared agent-memory corruption or unauthorized append operations during memory governance transition. | 4 | 4 | **16** (High) | Mitigate | Enforce `DEC-0044-029` append hold and lock memory helper `memory_store.py` to validate active item worktree before write. | 1 | 3 | **3** (Low) | CONTROLLED | `tuvok` (Security) |
| `RSK-RES-004` | RES | Provider API rate limits and token exhaustion stalling multi-agent workflow delivery. | 3 | 4 | **12** (Med) | Transfer / Mitigate | Implement automated token-budget tracking (`profile_generator.py`) and quota load-shedding to healthy peer runtimes (`DEC-0044-010`). | 2 | 2 | **4** (Low) | ACTIVE | `jadzia` (Lead) |
| `RSK-SAFE-005` | SAFE | Missing bidirectional traceability between stakeholder requirements and unit test evidence. | 3 | 5 | **15** (High) | Mitigate | Establish automated preflight traceability verification matrix (`REQ-STK-006`, `docs/pipeline/stakeholder-requirements-baseline.md`). | 1 | 4 | **4** (Low) | MITIGATED | `jake` (QA-Manager) |
| `RSK-SAFE-006` | SAFE | Fault Tolerant Time Interval (FTTI > 100ms) exceeded during hardware sensor plausibility failure. | 2 | 5 | **10** (Med) | Mitigate | Implement hardware watchdog timer and dedicated safe-state transition routine within 50ms (`REQ-STK-002`). | 1 | 5 | **5** (Low) | CONTROLLED | `odo` (Security) |

---

## 3. Risk Treatment Detail & Action Plans

### RSK-PROC-002: Worktree Collision & Concurrency Control
- **Risk Event**: Simultaneous writes to the same local branch causing dirty tree state and merge conflict lockouts.
- **Preventive Controls**:
  1. Priority-offer dispatching ensures exactly one agent owns an item token.
  2. Each task creates and operates within `.worktrees/<feature-step>`.
  3. Preflight scripts verify clean worktree and fast-forward capability before integration.
- **Monitoring Metric**: Number of failed fast-forward merge attempts per release cycle (Target: 0).

### RSK-PROC-003: Shared Memory Governance Integrity
- **Risk Event**: Unverified profile updates mutating common memory baseline without integration review.
- **Preventive Controls**:
  1. Strict enforcement of `DEC-0044-029` hold.
  2. `memory_store.py` rejects write attempts if worktree parameter does not resolve to an item-owned directory.
  3. Shared memory baseline is only updated via standard branch merge lifecycle.
- **Monitoring Metric**: Audit count of unauthorized direct memory appends (Target: 0).

---

## 4. Maintenance & Review Cadence
- **Weekly Review**: Risk register inspected weekly by QA Manager (`jake`) and Risk Custodian (`jadzia`).
- **Trigger-Based Review**: Initiated immediately upon:
  * Discovery of a new Critical/High risk ($	ext{RPN} \ge 15$).
  * Unhandled CI preflight test failure or integration abort.
  * Quota threshold breach notice.

---

## 5. Governance Sign-Off & Baseline Audit

| Role | Signatory Agent | Verdict | Timestamp | Signature Hash / Ref |
|---|---|---|---|---|
| **Risk Manager / Project Lead** | `jadzia` | APPROVED | 2026-08-29T21:07:00Z | `jadzia:0017-02:risk-reg-signoff:approved` |
| **Security & Safety Engineer** | `odo` | APPROVED | 2026-08-29T21:07:10Z | `odo:0017-02:risk-audit:approved` |
| **QA-Manager** | `jake` | APPROVED | 2026-08-29T21:07:20Z | `jake:0017-02:qa-reg-verify:approved` |
