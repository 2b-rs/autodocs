## Human escalation sentinel

A sentinel write is permitted only when the next unresolved action genuinely requires a human decision or authority. It is not a general blocker-reporting mechanism.

Before writing a sentinel, the owning agent MUST prove all of the following:

1. It owns the active claim for the affected item.
2. It has reread the current authority selector, agent instructions, complete
   item, prerequisites, acceptance criteria, and Definition of Done.
3. It has completed or ruled out every safe action within its delegated
   authority, including applicable investigation, retry, recovery, backlog
   repair, parent-package closure, and runner-result reconciliation.
4. No runner request is pending, no published result remains unreconciled, and
   no already-defined request remains merely unpublished.
5. The sole next action requires one of:
   - a choice between materially different valid product or architecture
     outcomes;
   - explicit authorization or risk acceptance;
   - a credential or externally controlled configuration;
   - a human signature, review, or approval;
   - a scope or policy decision outside delegated authority.
6. The claim records the exact question, evidence, options, recommendation,
   consequences, attempted actions, required authority, and the precise work
   unblocked by the answer.
7. The authoritative item has the state required by the current process:
   normally `[u]`, or `[p]` when a defined signed-decision transaction requires
   that state.
8. No open sentinel already represents the same item, question, and authority
   epoch.

The agent MUST NOT escalate for technical difficulty, unfamiliarity, command or test failure, a repairable planning defect, an open parent with executable package work, a determinable dependency deadlock, response/tool-budget exhaustion, a pending runner request, movement to another Feature, or a desire for confirmation.

When every predicate is satisfied, create a new sentinel atomically at `run.sh` using a non-overwriting operation.

Writing the sentinel is the final available action, not a preliminary announcement. The agent must first update the claim and authoritative item, then write the sentinel in the same turn. After writing it, report the exact sentinel path and escalation ID and yield for the named human authority.
