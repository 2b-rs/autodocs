# Integration Plan (`IP@v1`)

**Status:** candidate Integrator-owned contract for Feature `0046`; dormant and
non-operative until separately activated through the Feature gates.

**Architecture input:** [`WTP@v1`](worktree-topology-plan.md), owned by the
Architect and decided by [`DEC-0046-001`](../dossiers/dec-0046-worktree-topology-and-integration-plan.md).

**Requirements:** `RQ-IP-001..008`, `RQ-OPS-001`, and `RQ-OPS-009` in the
Feature-0046 requirements baseline.

## 1. Purpose and authority boundary

An Integration Plan is an append-only operational work product authored by an
explicitly assigned Integrator. It binds one immutable WTP identity and records
the exact runtime pins, order, checkpoint crossings, prerequisite-closed
Acceptance snapshots, reconciliation choices, validation, evidence, recovery,
and final-`main` preconditions for one integration attempt.

An IP is not a claim, lease, assignment, Acceptance decision, checkpoint
verdict, policy activation, merge execution, or authority grant. A field that
names an actor or command records a required precondition; it cannot supply the
authority it names. Existing repository authority remains cumulative and
controlling.

Machine instances conform to
[`integration-plan.schema.json`](integration-plan.schema.json). The
[`integration-plan.template.json`](integration-plan.template.json) file is a
valid dormant example. The Feature-0046 trial instance is retained at
[`docs/campaign-evidence/0046-trial/integration-plan.json`](../campaign-evidence/0046-trial/integration-plan.json).

## 2. Identity and canonical content

Every IP carries:

- `schema_version: integration-plan@v1`;
- `canonicalization_version: json-sort-utf8-no-floats@v1`;
- `digest_algorithm: sha256`;
- an immutable `plan_id`, `revision`, `feature_id`, `baseline_ref`,
  `integrator_identity`, `authority_ref`, `created_at`, `status`, and
  `supersedes` relation;
- `content_digest`, computed after removing the top-level `content_digest`,
  recursively sorting object keys by Unicode code point, preserving array
  order, serializing compact UTF-8 JSON, rejecting floating-point numbers, and
  hashing the resulting bytes with SHA-256.

The committed IP REF and reproducible digest are both required. REF proves
provenance and reachability; the digest proves content identity. Unsupported
versions, an unreachable REF, a digest mismatch, an edited execution event, or
a broken revision chain fail closed.

Statuses are `dormant`, `ready`, `executing`, `completed`, `blocked`,
`superseded`, and `withdrawn`. This contract does not authorize a transition.
Only `ready` or `executing` plans may contain an enabled consequential step,
and even those require external current authority at the step boundary.

## 3. Immutable WTP binding

`wtp_binding` consumes, without reinterpreting:

1. immutable WTP Git REF and canonical digest;
2. WTP schema, canonicalization, and digest-algorithm versions;
3. Feature and structural baseline compatibility;
4. complete node, edge, scope, overlap, checkpoint, validation, activation,
   status, supersession, and recovery identities;
5. Architect and decision authority identities.

The binding also records artifact digests for the contract, schema, and
template used to interpret the WTP. `consumption` lists every WTP interface
member as either `consumed` or `rejected-blocking`, with a reason and evidence
REF. Omission is invalid.

Before every consequential step, the consumer must re-read the reachable WTP,
reproduce its digest, revalidate status and supersession compatibility, and
compare every structural identity. A withdrawn WTP, incompatible supersession,
unreproducible digest, Feature/baseline mismatch, partial graph, unknown overlap
class, duplicate branch/worktree, or impossible recovery premise makes the IP
`invalid`; execution stops. Invalid is not refreshable.

## 4. Pins, graph consumption, and ordered absorption

`topology_snapshot` records the complete normalized node IDs, edge IDs,
overlap-rule IDs, and checkpoint work units consumed from the bound WTP. Set
equality is required; a subset is invalid even when all named branches exist.

Each `steps` entry has a stable sequence number and binds:

- one operation from the closed set `verify`, `absorb-prerequisite`,
  `merge-to-parent`, `checkpoint-review`, `integration-test`, `reconcile`, or
  `final-main`;
- exact source and target branch identities;
- `source_pin`, `target_pin_before`, and `target_tree_before`;
- declared WTP node/edge/overlap references and prerequisite order;
- merge mode and the selected predeclared reconciliation alternative;
- checkpoint, validation, hygiene, authority, evidence, and recovery inputs;
- a fail-closed `state` and `consequential` flag.

A pin is either `exact` with a full 40-hex commit (and tree where required), or
`unavailable-blocking` with a named open decision. The latter exists so a
dormant plan can represent the full future sequence without inventing a REF.
It never satisfies an executable step. Every consequential step must have exact
pins, `state: ready`, current external authority, and all boundary checks.

Prerequisites are absorbed in WTP/TODO topological order. Checkpoint-free
content may move only under the current branch workflow. Crossing a declared
checkpoint requires the exact independent review and induced Acceptance batch;
the IP cannot manufacture either.

## 5. Immutable Acceptance-closure snapshot

Every planned checkpoint crossing binds one `acceptance_closure` with:

- WTP REF/digest, checkpoint work unit, integration target pin, closure
  algorithm/version, normalized prerequisite edges, and accepted-boundary
  stops;
- one member for every induced terminal Task/Subtask: work unit,
  implementation candidate REF/tree digest, Task-contract REF/digest, terminal
  disposition and bookkeeping REF, claim/provenance REF, Acceptance decision
  REF/record digest/candidate binding, reviewer and authority REF,
  invalidation/supersession state, and evidence-manifest REF/digest;
- applicable decision and waiver REFs;
- normalized member manifest plus `closure_digest`.

The closure digest uses the IP canonicalization rules after removing only
`closure_digest`. Audit timestamps are excluded from closure content identity.
Member order is lexicographic by `work_unit`; edges and boundary stops use their
declared order. Missing, stale, invalidated, superseded-incompatible, or
candidate-mismatched Acceptance is `blocking-stale`, never refreshable.

An unavailable future closure uses `state: unavailable-blocking`, an empty
member list, and a named open decision. It cannot be attached to a ready or
consequential step.

## 6. Reconciliation and concurrent drift

The WTP owns structural overlap classes. The IP selects only an alternative
already declared by the WTP and this plan:

- `abort-on-conflict`: stop without changing either side;
- `linewise-union`: reconcile only declared paths, preserve both sides,
  prohibit blanket ours/theirs, and check loss plus duplicate headings/records;
- `regenerate-declared-output`: run one pinned deterministic generator and
  compare its output digest;
- `no-reconciliation`: require a clean fast-forward or clean declared merge.

The plan records candidate paths, actor authority, pre/post tree IDs, conflict
manifest, retained decisions, and evidence. A novel path, strategy, ownership
transfer, or authority boundary requires a new WTP and IP revision as
applicable; it is never an execution-time improvisation.

## 7. Refresh events versus new revisions

Append-only `events` may refresh only exact runtime tips, observed ancestry,
evidence timestamps, and recomputable hygiene or closure observations when:

1. the bound WTP REF, digest, status, topology, scope, prerequisite meaning,
   checkpoint reach, authority, validation, and recovery remain unchanged;
2. the current IP already declares the selected response;
3. the event binds old/new pins, reason, closed stale class, recomputed
   ancestry/overlap/closure/hygiene results, actor identity, evidence manifest,
   and event digest;
4. every downstream step is revalidated before continuation.

Events are immutable and ordered. They record execution history; they do not
edit plan intent.

A new IP revision is mandatory for any WTP digest or structural change, merge
order or prerequisite-meaning change, scope/overlap/checkpoint/authority change,
new reconciliation strategy, validation-profile change, recovery change, or
final-`main` method change. The new revision names the previous IP REF+digest,
impact, carried events, invalidated steps, and safe restart point. Bad plans are
marked `superseded` or `withdrawn`; history is retained.

## 8. Hygiene, validation, evidence, and recovery

Every step declares required commands/procedures, baseline, environment
controls, expected exit status, counts/population, and content digests. A
successful command is evidence of execution, not Acceptance or authority.

Immediately before any integration mutation:

- re-read the inbox and current authority;
- confirm the exact refs and clean assigned worktree;
- run the repository integration-hygiene checker and require exit `0`;
- at a root advance, also require symbolic `HEAD=refs/heads/main`, exact target
  pin, `git diff --quiet`, and `git diff --cached --quiet`, each successful;
- stop without cleaning, stashing, resetting, or appropriating foreign state
  on any failure.

Recovery is step-specific and never broader than current authority. The plan
names a last valid pin, stop condition, preservation requirements, rollback or
revert method, verification, and escalation owner. Rewriting history,
`git update-ref` on checked-out `main`, deleting `preserved/*`, clearing another
owner's verdict, or editing an Acceptance record in place is forbidden.

## 9. Final-`main` planned step

`final-main` may appear exactly once and only as the last step. It remains a
plan until separately authorized. It must bind:

- exact integrated Feature candidate and target-before pins;
- all mandatory checkpoint and induced Acceptance-closure snapshots;
- final test/evidence manifest;
- current privileged Integrator identity plus external authority REF;
- root hard-preflight and repository hygiene commands/evidence;
- permitted merge mode under target-branch policy;
- post-merge ref/tree/status verification;
- tag/preservation and recovery route;
- the separately authorized `DONE.md`/Feature-closure action, or an explicit
  statement that closure is out of scope.

A non-final occurrence, unresolved pin, missing authority, missing preflight,
missing closure, or executable flag in a dormant/trial plan is invalid.

## 10. Open decisions and safe defaults

Every open decision has an ID, owner, current safe default, trigger/deadline,
affected requirements and steps, and behavior while unresolved. The only safe
default for a missing execution input is `block affected steps and retain the
last valid plan`. No placeholder, `TBD`, optimistic assumption, or green test
may permit work.

## 11. Conformance matrix

Implementations and reviews must cover at least:

| Case | Expected result |
|---|---|
| Complete dormant initial plan | schema-valid; no step executable |
| Declared source-tip refresh | append-only event valid after recomputation |
| Structural or ordering drift | new IP revision required |
| Missing/stale/invalid Acceptance | affected checkpoint step blocking |
| Withdrawn/incompatible WTP | whole plan invalid |
| Unknown or omitted overlap | whole plan invalid |
| Partial node/edge consumption | whole plan invalid |
| Final-main missing authority or preflight | invalid |
| Final-main not last or more than once | invalid |

JSON Schema proves shape and the conditional exact-pin/authority boundary for
consequential and final-`main` steps. The composed validator owned by `0046-04`
also proves final-step position and uniqueness, graph set equality, reachability,
canonicalization, digest reproduction, closure semantics, status freshness, and
authority-sensitive refusal. Until that validator and the required reviews
exist, manual checks are evidence only and the contracts remain dormant.
