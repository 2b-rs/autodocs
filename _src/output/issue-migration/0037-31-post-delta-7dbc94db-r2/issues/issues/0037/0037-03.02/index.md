---
schema_version: "1.0"
id: "0037-03.02"
level: "subtask"
parent: "0037-03"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2032"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0037-03.02:0037-02 Define the cross-worktree/cross-clone claim and recovery protocol in `docs/pipeline/issue-lifecycle.md`. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-03.02`). Abgenommene Baseline `536c824f095f1563b9c565378afecabb4ff07bf1`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). issue-claim-v1.schema.json vorhanden.

## Scope

- **Closure (2026-08-16):** Claim/recovery lifecycle contract, `issue-claim@v1` schema, and six race fixtures committed in `536c824f095f1563b9c565378afecabb4ff07bf1`. Validation passed: claim schema and six race fixtures passed syntax/semantic checks.

## Acceptance criteria

- **AC-001** `issues/_schema/issue-claim-v1.schema.json` requires item, owner identity, worktree/clone ID, base commit, claimed write scopes, issued/expiry times, lease nonce, and CAS-ref digest. Same-clone acquisition uses atomic `git update-ref refs/autodocs/claims/<item-id>`
- **AC-002** independent clones serialize by promptly integrating `claim.json` to a protected branch. Integration rejects stale bases, duplicate/overlapping active scopes, and unmerged competing claims. Expiry blocks new work until explicit release or authority-approved takeover
- **AC-003** takeover never deletes history. Document fetch/recheck, renewal, handoff, crash recovery, unavailable-remote behavior, and the limitation that no repository-only mechanism guarantees pre-merge exclusivity across disconnected clones

## Definition of Done

Review-ready schema, state table, compare-and-swap pseudocode, merge-time rules, and race fixtures cover two worktrees, two clones, expiry, takeover, stale base, overlapping scopes, and failed integration.
