---
schema_version: "1.0"
id: "0050-09"
level: "task"
parent: "0050"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:249"
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

(P0) Close the `0050-07` QA coverage gaps: implement the missing mixed-provider, privacy/negative-authorization, and abuse/quota cases against the integrated 0050 candidates.

## Scope

- **Task record:** `task_id: "0050-09"; feature_id: "0050"; role: implementer`.
  - **Architecture decisions and sources:** `DEC-0050-001`; the `REQ-0050-*` dimensions left unobserved by `0050-07`; QA report `docs/campaign-evidence/0050-07/qa-report.md` findings `Q-01`, `Q-02`, `Q-03`; Management `decision-1788296208431-408cb2cb` option `opt1`, which authorised exactly this task rather than waiving the gaps.
  - **Prerequisites:** `0050-07`; its closure includes `0050-00..06`.
  - **Planned order:** `position: 9`.
  - **Test scope:** `kind: property+integration`; the three unobserved dimensions only — (`Q-01`) a member exhausting provider quota mid-drain, mixed-provider teams draining concurrently, and provider-neutral generation/admission behaviour; (`Q-02`) negative authorization and privacy cases, including a paused or anonymous actor attempting a privileged transition, and redaction/retention interaction with drain receipts; (`Q-03`) abuse and quota boundaries, including repeated pause/resume flooding and reclamation-request abuse.
  - **Capability profile:** `capability_class=privileged; execution_needs=direct; cognitive_demand=high; rights=["edit declared agent-inbox test paths", "run isolated validation", "commit candidate"]; independence="test author must not be the 0050-07 QA author"`.
  - **Cognitive evidence:** `estimator=0044-06@v1; scope_breadth=medium; reasoning_depth=high; context_volume=high; ambiguity=low; verification_hardness=critical`; the hard part is provoking quota exhaustion and pause/accept races deterministically, not writing assertions.
  - **Branch/worktree:** `parent: agent-inbox:0050; name: 0050-09; worktree: /Users/tobias.anton/devel/agent-inbox/.worktrees/0050-09`. Implementation and tests live in **agent-inbox**, where the 0050 candidates are integrated; `autodocs` carries evidence only.
  - **Exhaustive write scope (agent-inbox):** `test_team_pause_phaseout.py`, or a new `test_team_pause_provider_privacy_abuse.py` if the author prefers a separate module, plus the exact item claim. **No production module is in scope.**
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: "agent-inbox/main", basis: "0050-01..06 integrated at agent-inbox main 91f59a6; this adds coverage only", checked_by: "seven", checked_at: "2026-09-01" }`.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** coverage-only node that changes no production behaviour and activates no gate; `0050-08` remains the Feature's review floor and consumes this node's result. Recorded by Architect `seven`, 2026-09-01, under Management `decision-1788296208431-408cb2cb` `opt1`.
  - **Scope boundary — read before "fixing" anything:** if a new case exposes a real defect in `0050-01`..`0050-06`, that defect is **reported as a finding, not repaired here**. This node adds evidence; repairing production behaviour belongs to the node that owns it and needs its own award. A green suite obtained by weakening a case is a failure of this task, not a completion of it.
  - **Independence:** the author must not be `seven`, who wrote the `0050-07` QA that identified these gaps and authored this decomposition. Marking one's own findings covered is self-verification.

## Acceptance criteria

- **AC-001** Each of `Q-01`, `Q-02`, `Q-03` has at least one executed case with an observed result and a named neighbouring case
- **AC-002** provider exhaustion mid-drain, a negative-authorization/privacy denial, and an abuse/quota boundary are each demonstrably exercised rather than asserted in prose
- **AC-003** `AE-3` red-on-broken evidence is produced by fault injection for at least one invariant per finding
- **AC-004** the existing 18 cases still pass at exit 0

## Definition of Done

Coverage committed in `agent-inbox` with checked exit statuses and a short evidence note mapping each new case to `Q-01`/`Q-02`/`Q-03`; any defect discovered is recorded as a finding against its owning node; `0050-07`'s report is not edited — it stands as the record of what was missing when it was measured.
