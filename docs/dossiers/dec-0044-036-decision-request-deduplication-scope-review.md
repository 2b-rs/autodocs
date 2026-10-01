# Review: DEC-0044-036 — Durable Management decision requests have one canonical lifecycle per unchanged question

**Reviewer:** Kira Nerys (Architect)
**Target:** Commit 57add1133f3b5642d357f1311034862f006bfb18
**File:** docs/dossiers/dec-0044-036-decision-request-deduplication.md

## Verdict
**REWORK**

## Findings
1. **decision-record@v1 conformance:** Verified. The record contains all required fields (Record format, Recorded at, Deciding identity, Role, Authority reference, Subject, Decision, Technical justification, Triggers, Considered alternatives, Consequences, Affected work units, Affected gates, Review participation, No-review reason, Waiver).
2. **user/Supervisor versus mancons authority boundary:** **MISSING.** The candidate does not explicitly address or verify the user/Supervisor versus mancons authority boundary. This must be explicitly defined in the decision constraints or consequences.
3. **root-checkout safety incident:** **REWORK REQUIRED.** Review work must occur in an isolated worktree/branch and never temporarily switch the shared root checkout.
4. **pending/resolved exact-ID dedup semantics:** Verified. Addressed via "matching pending request is reused... matching resolved request is the answer and continuation cites its exact ID".
5. **explicit append-only supersession for conflicts:** Verified. Addressed via "explicit append-only supersession... conflicting resolved decisions fail closed".
6. **exact linked-hold resumption:** Verified. The text references "exact-ID reuse lets claims, holds, review evidence, and continuations converge on one status" and addresses "same paused action under multiple pending holds", providing the exact semantic equivalent.
7. **GUI/mail projection non-authority:** Verified. Explicitly states "Presentation fields such as title, prose formatting, sender, timestamp, mailbox message, wake-up, or GUI projection are not identity" and warns consumers not to treat them as authority.
8. **affected cross-item gates:** Verified. Explicitly lists `feature-closure:0044`, `task-start:0046-01`, and `integration:0046-00`.
9. **rollback and non-invention of material choices:** Verified. Explicitly covers rollback semantics (abandonment before implementation, disabling automation after implementation while preserving records without silently choosing among them).
10. **Minimal mutation scope & state machine preservation:** Verified. Record limits itself to the architecture contract only, stating "it does not itself modify a normative process, gate, or implementation".

## Conclusion
The candidate must be reworked to explicitly address the **user/Supervisor versus mancons authority boundary**, and must be properly reviewed in an **isolated worktree** to satisfy the required review constraints and prevent root-checkout modification.

---

# Rereview: DEC-0044-036

**Reviewer:** Kira Nerys (Architect)
**Target:** Commit 1786fcc9f658d88ffb3e8ff6614e3b1968e20880
**Prior Evidence:** cde15625ac

## Verdict
**SUPPORT**

## Findings
1. **authority-boundary finding:** **CLOSED.** The candidate explicitly records the current user as the deciding Management authority and clarifies that the Supervisor coordinates assignments without transferring decision authority. It also specifies that `mancons` performs triage and resolves only explicitly or uniquely determined choices without inventing material choices, waivers, or supersessions.
2. **decision-record@v1 conformance:** Verified.
3. **pending/resolved exact-ID dedup semantics:** Verified.
4. **explicit append-only supersession for conflicts:** Verified.
5. **exact linked-hold resumption:** Verified. The consequences section now explicitly includes "linked-hold resumption by the same exact request ID".
6. **GUI/mail projection non-authority:** Verified.
7. **rollback and non-invention of material choices:** Verified.

## Conclusion
The candidate successfully addresses the missing authority boundary and satisfies all review constraints. Support is granted.
