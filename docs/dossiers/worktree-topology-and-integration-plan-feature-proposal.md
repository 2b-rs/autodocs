# Feature proposal — architected worktree topology and integration plan

- **Proposal ID:** `FC-WTIP-20260824` (unallocated planning identifier)
- **Status:** preparation; not an operative process contract
- **Prepared by:** `agent:troy:process-workproducts-worktree-integration-plan-20260824:20260824T172134Z` (QA Manager)
- **Authority basis:** current-user assignment of 2026-08-24, routed by Project Lead Jean-Luc in mailbox `1787592094893-3382b9b6`
- **Incident evidence anchor:** `6d9a9ba116419fc0631412870f9d5914d3fda7c2`
- **Scope boundary:** This document proposes a Feature and two future work products. It does not allocate a Feature/Task/DEC ID, alter any current workflow, approve a topology or merge, or grant authority.

## 1. Observed process gap

**Observation:** Current rules require item-owned worktrees, branch hierarchy, prerequisite merges, hygiene checks, and controlled `main` advancement. The incident anchored at `6d9a9ba116` shows that an implementation branch can still become a convergence point for terminal prerequisites without a single, reviewable plan that names the required checkout topology and the integration/reconciliation sequence.

**Inference:** A programmer-centred guard can detect or reject some unsafe state, but cannot demonstrate that the planned collection of branches and worktrees is complete, non-conflicting, available to its assigned roles, or integrated in a sequence that preserves prerequisites and checkpoint authority. The absence of an Architect-owned topology and an Integrator-owned companion plan raises recovery cost and invites repeated ad-hoc reading of distributed claims, worktree lists, and merge history.

**Severity:** major process-control gap; no claim that `6d9a9ba116` alone proves a defect in its work product.

**Proposed owner:** a newly allocated pipeline Feature, decomposed by an independent Architect; the Integrator owns its operational integration plan.

**Next authority step:** Project Lead allocates a numeric Feature ID and requests a Management-instantiated Architect scope review. Before any future operative gate/policy mutation, the Feature must have a conforming `decision-record@v1` and supporting independent Architect scope review.

## 2. Goal and non-goals

The Feature establishes two versioned, reviewable planning work products:

1. **Worktree Topology Plan (WTP):** Architect-authored during Feature breakdown. It declares the required checkout/worktree topology for bounded work units before implementation starts.
2. **Integration Plan (IP):** Integrator-authored and maintained from the approved topology. It declares branch targets, merge order, prerequisites, checkpoints, reconciliation, validation, and the separately authorized `main` advance.

Non-goals: the plans do not replace claims, `TODO.md`, decision records, task acceptance, integration review, hygiene checks, or root preflight; do not allocate work; do not grant merge/Acceptance authority; and do not make a plan a lease.

## 3. Proposed work-product schemas and templates

### WTP@v1 (Architect work product)

Required immutable header: `feature_id`, `baseline_ref`, `topology_revision`, `architect_identity`, `authority_ref`, `created_at`, `status`, and `supersedes`.

Each **worktree node** requires: `node_id`, `work_unit`, `branch`, `base_branch`, `worktree_path`, `owner_role`, `capability_class`, `write_scope`, `read_scope`, `expected_predecessor_refs`, `concurrency_group`, `provisioner`, `lifecycle` (`planned|active|released|retained`), and `recovery_reference`.

Each **edge** requires: `from`, `to`, `kind` (`base|prerequisite-content|claim-carry|review|integration-target`), `condition`, and `evidence_required`. The WTP must explicitly identify the unique worktree checking out `main` and mark it read-only except for an authorized final advance.

Template invariant: every executable Task/Subtask maps to exactly one active item-owned worktree; no two active nodes claim the same branch; every write scope has an owner; and an unallocated/future node is visibly `planned`, not executable.

### IP@v1 (Integrator work product)

Required immutable header: `feature_id`, `topology_ref` (WTP revision/digest), `baseline_ref`, `plan_revision`, `integrator_identity`, `authority_ref`, `created_at`, `status`, and `supersedes`.

Each **integration step** requires: `step_id`, `source_branch`, `source_tip`, `target_branch`, `target_tip_before`, `merge_mode`, `ordered_predecessors`, `checkpoint`, `required_acceptance_closure`, `integration-test-profile`, `hygiene_required`, `reconciliation_paths`, `conflict procedure`, `rollback/recovery`, `evidence outputs`, and `authority boundary`.

The final `main` step must additionally name: exact root/preflight command, hygiene result, authorized actor, candidate/target refs, merge mode, post-advance verification, and recovery reference. It remains `planned` until the separately required authorization and clean preflight exist.

## 4. Proposed Feature decomposition

| Candidate package | Owner role | Deliverable and acceptance intent |
|---|---|---|
| P1 — requirements and decision preparation | Requirements Engineer + QA finding input | Versioned requirement inventory; `decision-record@v1` proposal; affected gates/work units; no activation. |
| P2 — topology contract | Architect | WTP@v1 schema/template, node/edge invariants, Feature-breakdown amendment, independent scope review. |
| P3 — integration contract | Integrator | IP@v1 schema/template and update protocol; no self-approval of implementation. |
| P4 — deterministic validation | Implementer/Tester | Parser/validator and fixtures for topology/plan consistency, unique branch/worktree ownership, dependency/merge ordering, stale pins, scope overlaps, and prohibited `main` advance. |
| P5 — migration and compatibility | Implementer + QA review | Existing active Features obtain additive, explicitly marked compatibility plans; no implicit grandfathering. |
| P6 — terminal integration | Integrator | One integrating Task, marked `Integration review: mandatory`, proves a representative Feature end-to-end with WTP/IP evidence. |

The Architect chooses actual Task IDs, prerequisite graph, checkpoints, and exact scopes only after numeric Feature allocation. P6 is the Feature's required single integration-review floor.

## 5. Acceptance criteria and Definition of Done

The allocated Feature is implementation-complete only when:

- the Architect's WTP@v1 identifies every executable work unit, branch, worktree, owner role, capability class, scope, predecessor reference, and recovery route;
- the Integrator's IP@v1 binds a specific WTP digest and represents every upward merge, checkpoint, reconciliation, test profile, and final-main preflight as ordered, pinned steps;
- deterministic validation rejects duplicate active branch/worktree ownership, missing nodes/edges, unreachable prerequisite order, stale refs, unauthorised `main` steps, unchecked reconciliation paths, and scope overlap;
- migration evidence distinguishes every existing Feature as migrated, explicitly compatible, or deferred with a named owner/revisit trigger; and
- a representative Feature demonstrates that the two plans reduce ad-hoc re-reading and provide a reproducible recovery path without replacing current acceptance or hygiene controls.

Definition of Done additionally requires scoped tests, documentation, committed validation evidence, a real REF, preserved append-only history, and an independent QA review of the process operation. It excludes self-Acceptance.

## 6. Validation and measures

Proposed validator inputs are WTP/IP fixtures and repository read-only metadata. It must produce stable machine-readable findings and an exact plan digest. Minimum checks:

- WTP node/edge schema and referential integrity;
- one active worktree/branch owner per executable work unit and no incompatible scope overlaps;
- IP topology-digest match; source/target pin existence; topological merge order; all declared prerequisites and checkpoint boundaries present;
- `main` action is represented only as an authorized final step with hygiene/root-preflight evidence fields; and
- migration manifest completeness and no unmarked implicit grandfathering.

QA measures: planned-vs-actual worktree divergence, integration rework count, stale handoffs, repeated discovery reads, blocked-preflight recoveries, and mean recovery time. Baselines must be recorded before activation; claims about improvement require comparable samples.

## 7. Migration, compatibility, and recovery

Existing Features remain governed by their current contracts until their migration status is explicitly recorded. A migration adds plans; it does not rewrite old claims, merge evidence, Acceptance records, or preserved snapshots. A compatibility record must name its Feature baseline, omissions, risks, owner, and revisit trigger. If a plan is malformed or stale, the safe response is to stop the affected integration, retain the last valid plan revision, regenerate from current evidence, and preserve all historical plan/review records.

## 8. Role handoffs and authority controls

1. QA Manager records the gap and audits subsequent operation; it does not validate its own authored operative contract.
2. Requirements Engineer stabilizes the requirement baseline and open decisions.
3. Project Lead allocates the Feature/Task IDs and routes Management decisions.
4. An independent Architect performs the cross-item scope review and authors WTP during breakdown.
5. Implementers provision only the WTP-declared item worktrees and update claims in their scopes.
6. The independent Integrator authors/updates IP and crosses only assigned checkpoints.
7. A privileged authorized actor alone performs the final root-based `main` advance after passing the current hygiene and hard-preflight contracts.

## 9. Routing request

Route `FC-WTIP-20260824` to the Project Lead for numeric Feature allocation and to a Management-instantiated Architect for scope review. The Architect must decide whether the proposed plan validation creates a qualifying cross-item gate and, if so, prepare the required decision record before any activation. Until that point this dossier is preparatory evidence only.
