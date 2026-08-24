# Worktree Topology Plan (`WTP@v1`)

**Status:** candidate architecture contract for Feature `0046`; dormant outside the Feature trial.

**Decision basis:** [`DEC-0046-001`](../dossiers/dec-0046-worktree-topology-and-integration-plan.md).

## 1. Purpose and authority boundary

A Worktree Topology Plan is the Architect-owned structural input to Feature execution. It declares the complete set of executable work units, their canonical branches and item-owned worktrees, scope ownership, structural predecessor relations, concurrency/overlap classes, checkpoints, compatibility constraints, lifecycle, and recovery premises before implementation begins.

A WTP is not a claim, lease, task assignment, branch operation, integration plan, Acceptance decision, checkpoint verdict, or authority grant. Existing repository authority remains controlling. The Integrator owns the operational `IP@v1`; this contract defines only the inputs the IP must consume and the conditions under which an IP becomes stale or invalid.

Machine instances conform to [`worktree-topology-plan.schema.json`](worktree-topology-plan.schema.json). [`worktree-topology-plan.template.json`](worktree-topology-plan.template.json) is a valid minimal example, not an activated plan.

## 2. Identity and canonical digest

Every WTP carries:

- `schema_version: worktree-topology-plan@v1`;
- `canonicalization_version: json-sort-utf8-no-floats@v1`;
- `digest_algorithm: sha256`;
- immutable `feature_id`, `baseline_ref`, `topology_revision`, `architect_identity`, `authority_ref`, `created_at`, `status`, and `supersedes`;
- `content_digest`, computed after removing the top-level `content_digest` member, recursively sorting object keys by Unicode code point, preserving array order, encoding strings and structural tokens as compact UTF-8 JSON, prohibiting floating-point values, and hashing the resulting bytes with SHA-256.

Both the reachable Git REF of the committed plan and the reproducible `content_digest` identify a WTP. REF supplies provenance and reachability; digest supplies content identity. Neither substitutes for the other. A consumer rejects an unreproducible digest, unsupported schema/canonicalization/digest version, unreachable REF, or mismatched Feature identity.

## 3. Structural ownership

### 3.1 Nodes

Each executable Task or Subtask has exactly one node with:

- `node_id` and exact `work_unit`;
- `branch`, `base_branch`, and absolute `worktree_path`;
- `owner_role` and one exact capability class from `SANDBOX.md`;
- non-empty `write_scope` and `read_scope` path rules;
- structural `predecessor_constraints` rather than transient runtime tips;
- `concurrency_group`, `phase`, `provisioner`, `lifecycle`, and `recovery_reference`.

The WTP also names the unique node for the worktree checking out `main`. Its lifecycle is `retained`, its write scope is empty, and its use is read-only except for the separately authorized final root merge described by current authority. Planned nodes are not executable until their item claim and applicable start gates exist.

### 3.2 Edges

Each edge names `from`, `to`, one closed kind (`base`, `prerequisite-content`, `claim-carry`, `review`, `integration-target`), a falsifiable condition, and required evidence. Edges describe structural reach; the IP binds their exact runtime tips and execution order.

The graph must be complete for the governed Feature, referentially valid, acyclic for base/prerequisite order, and consistent with Task→Feature and Subtask→Task branch topology. A node/edge subset is invalid even when every named branch exists.

### 3.3 Scope rules

Path rules are repository-relative and typed `exact` or `prefix`. Every writable path has one active owner in a concurrency phase. A shared read scope creates no ownership. A foreign worktree's dirty or staged state is never cleaned, reset, stashed, or appropriated by plan execution.

## 4. Time-aware overlap classes

`overlap_rules` classify every intersecting pair of write scopes:

| Class | Temporal relation | Required behavior |
|---|---|---|
| `concurrent-exclusive` | Nodes may be active simultaneously | Any path intersection blocks activation; split scope or serialize through a new WTP revision. |
| `ordered-predecessor` | Consumer starts after producer is terminal and carried | Intersection is permitted only for named paths, explicit order, predecessor REF evidence, and ownership transfer. |
| `claim-carry` | Upward merge carries append-only claim/provenance records | Only declared append-only claim paths may overlap; foreign owner tokens are immutable. |
| `reconciliation` | A bounded integrator step combines previously separate products | The WTP declares candidate paths and authority boundary; the IP selects a predeclared strategy and records conflict/evidence outputs. |

Unknown classes fail closed. Merely sharing a path does not prove a conflict; omitting the temporal relation does. A relation that changes simultaneity, ownership transfer, allowed paths, or authority requires a new WTP revision.

## 5. Staleness and validity

The WTP declares closed JSON-pointer lists in `staleness_policy`.

### 5.1 Blocking structural change

An IP is `blocking-stale` when any bound WTP structural field changes, including Feature/baseline compatibility, node/work-unit membership, branch/base identity, path ownership, predecessor meaning, overlap class, checkpoint reach, authority/capability boundary, validation profile, recovery premise, activation profile, schema/canonicalization/digest version, or WTP digest. Work stops before the affected step; a new IP revision must bind the superseding WTP.

### 5.2 Refreshable operational drift

Only exact runtime tips, observed ancestry, evidence timestamps, and recomputable hygiene/closure snapshots are potentially `refreshable-stale`. Refresh is permitted only when:

1. the WTP remains current and digest-identical;
2. topology, prerequisite meaning, scope, checkpoint reach, authority, validation, and recovery premises are unchanged;
3. the current IP already declares the selected refresh/reconciliation alternative;
4. the authorized Integrator records an append-only event binding old/new pins, reason, classification, recomputed ancestry/overlap/Acceptance-closure/hygiene results, identity, and evidence digest.

Missing, stale, invalidated, or candidate-mismatched Acceptance is blocking, never silently refreshable.

### 5.3 Invalid plan

A withdrawn WTP, an incompatible supersession, unsupported identity algorithm, unreproducible digest, partial graph, unknown overlap class, duplicate active branch/worktree, or impossible recovery reference is `invalid`. Invalid is not a stale subtype and cannot be refreshed.

## 6. WTP-to-IP interface

The Architect supplies the Integrator:

1. WTP Git REF, canonical digest, schema version, canonicalization version, and digest algorithm;
2. Feature and structural baseline identity/compatibility constraints;
3. normalized complete nodes, edges, scope rules, overlap classes, checkpoints, and recovery premises;
4. closed blocking/refreshable/invalid classifications;
5. required validation profile and activation state;
6. status, supersession compatibility, and immutable Architect/authority identities.

The Integrator-owned IP adds exact source/target tips, ordered predecessor absorption, merge mode, target-before state, checkpoint steps, validation/test profile execution, reconciliation choice, rollback commands, evidence outputs, and final-`main` preconditions. It also computes an immutable Acceptance-closure snapshot containing:

- WTP REF/digest and checkpoint node;
- closure algorithm/version, normalized prerequisite edges, and accepted-boundary stops;
- for each induced node, implementation candidate REF/tree digest, Task contract REF/digest, terminal disposition and claim/provenance REF, Acceptance decision REF/record digest/candidate binding, reviewer/authority reference, invalidation/supersession state, and evidence-manifest REF/digest;
- applicable decision/waiver REFs and the integration target pin;
- normalized member manifest and closure digest.

Timestamps are audit metadata, not closure content identity. The IP must revalidate WTP status/supersession immediately before every consequential integration step.

## 7. Lifecycle, activation, migration, and recovery

WTP status is `candidate`, `trial`, `active`, `superseded`, or `withdrawn`.

- `candidate`: architecture input only; no gate behavior.
- `trial`: Feature `0046` may self-apply it as additional evidence while pre-existing authority remains controlling.
- `active`: available only after the Feature's migration, validation, mandatory checkpoint, QA, and governance-integration conditions pass.
- `superseded`: retained append-only; compatibility is explicit.
- `withdrawn`: invalid for new or continued IP execution.

No existing Feature is grandfathered. Migration assigns one explicit disposition—`migrated`, `compatible-with-bounds`, or `deferred`—with baseline, omissions, risks, owner, and revisit trigger. Rollback stops affected gates, retains the last valid WTP/IP and evidence, restores prior behavior only through separately authorized governance change, and preserves claims, Acceptance, verdicts, and snapshot tags.

## 8. Semantic validator obligations

JSON Schema validates shape; the future deterministic validator additionally proves:

- canonical digest reproducibility and reachable REF identity;
- complete one-node-per-executable-unit coverage;
- unique active branch/worktree ownership and unique `main` node;
- scope ownership plus complete time-aware overlap classification;
- edge endpoints, branch topology, prerequisite completeness, and acyclicity;
- checkpoint set and exactly one terminal Feature integrating Task;
- closed stale/invalid classification and IP binding compatibility;
- explicit activation/migration/recovery fields and no implicit grandfathering;
- refusal of unauthorized or non-final `main` steps.

Green schema or validator output is execution evidence, not Acceptance or authority.

