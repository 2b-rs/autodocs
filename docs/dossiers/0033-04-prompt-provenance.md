# Prompt provenance — Task 0033-04

## 2026-08-19 — current-user instruction

```text
Be concise. Write all documentation in English. You are **Donald Riker 20260819T125003Z**, explicitly privileged corrective implementer. User directed all Feature 0033 tasks through named Riker subagents. Resume Task 0033-04 in `.worktrees/0033-04`, branch `0033-04`; preserve coordinator/Grace claims append-only and create successor claim with explicit handoff. The prior sandboxed attempt stopped only because run.sh was owned by 0042-02.01; do not overwrite it. As privileged, use direct safe Git/test execution without modifying foreign run.sh. Merge accepted prerequisite branch 0033-03.01 tip 960d53295c6ad27170d49c442867f132f76b3095 per workflow before mutation. Implement the full review-ready UX contract only, including executable scenario/test mapping and shared IndexedDB migration constraints. English documentation. No production browser/store/transport/credential/queue/public effect or approval. Commit substantive then `[x]` bookkeeping; no self-acceptance. Escalate only hard blockers; return concise commits/tests.
```

The implementation used direct local Git and focused tests only. It did not
modify root `run.sh`, invoke a browser, contact a network/service, use a
credential, or mutate a store, queue, record, Issue, public host, approval, or
acceptance record.
