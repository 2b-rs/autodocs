# `DEC-0044-020` — Independent Architect gate-scope review

**Review status:** `supports`, subject to every binding wording and activation
constraint in section 5. This is the independent scope review required by the
`cross-item-blast-radius` exception before normative mutation. It is not Task
Acceptance, an integration review, an integration verdict, or `Acceptance: ✓`.

**Reviewed decision baseline:** commit
`ac2f8ea0200c3dd74b80b346667784f63b126ff4`, file
`docs/dossiers/dec-0044-020-acceptance-closure.md`, SHA-256
`5f982f008d9a691de4864ea0a5f99f3f65ef0a01385ec2055f56a0815535a123`.

**Reviewer:** `agent:data:DEC-0044-020:20260823T173904Z`, distinct Data persona,
assigned as `Architekt`, capability class `privileged`. The reviewer did not
author the Management decision, its decisive semantics, or the normative
implementation and has no Acceptance or integration authority under this
assignment.

**Review time:** `2026-08-23T17:39:04Z`.

## 1. Assignment and supplied boundary

Dispatcher `jean-luc` assigned the following bounded work, first through the
session briefing and then through mailbox thread `DEC-0044-020`:

- assume the distinct Data persona and Architect role;
- review exactly `DEC-0044-020` at commit `ac2f8ea02` and the digest above;
- assess ordinary `[x]`/`[w]` implementation consumption, transitive bottom-up
  Task Acceptance, exclusive Architect checkpoint authority, and the rule that
  a checkpoint may be added until the affected Task has current Acceptance but
  not silently afterward;
- inspect `TODO.md`, `AGENTS.md`, `docs/pipeline/task-acceptance.md`,
  `docs/pipeline/branch-workflow.md`, `docs/pipeline/decision-record.md`,
  `docs/pipeline/process-roles.md`, and relevant validators;
- write only this review (plus an optional own claim, not used), commit it
  separately and report the full commit REF;
- do not modify the decision record or normative files, accept work, cross an
  integration checkpoint, move a Feature or `main`, or touch external state.

This restatement preserves the operative briefing fields and prohibitions. The
separate later mailbox assignment concerning external `0037-*` Task Acceptance
is not exercised by this review and creates no authority inside this scope.

## 2. Independent conclusion

I support all three substantive distinctions in the decision:

1. **Implementation flow:** absent an explicit acceptance-before-start edge,
   required `[x]`/`[w]` predecessors satisfy the ordinary successor
   implementation-start gate. This preserves construction concurrency.
2. **Acceptance closure:** assignment to accept a target deterministically
   expands to every required transitive `[x]`/`[w]` predecessor that lacks
   current valid Acceptance. The batch is reviewed bottom-up, and every member
   receives its own decision before the target may receive current Acceptance.
3. **Checkpoint authority and timing:** only a Management-instantiated Architect
   may set, clear, or move the checkpoint attribute. The Architect may add a
   checkpoint while the affected node lacks current Acceptance, including after
   `[x]`/`[w]`; current Acceptance closes that window. A later change requires
   separately authorized append-only invalidation/reopening first.

The distinction is coherent: **checkpoint marking decides which node initiates
an integration review; prerequisite closure decides which additional nodes must
be accepted in that review batch.** An unmarked Task does not independently
trigger privileged review and does not block ordinary successor implementation,
but it still receives its own Acceptance decision if it is an unaccepted
required predecessor of a target now being accepted.

## 3. Cross-item reach and affected gates

The canonical predicate applies. The rule can change the acceptance and closure
of every dependent Task and Feature and can change the future integration gate
of a not-yet-accepted node. It therefore reaches beyond `0038`, even though
`0038` is the immediate operational case.

Affected work units and paths are at least:

- `repository:autodocs` and all present/future Task, Subtask, and Feature
  prerequisite closures;
- `feature:0038`, including its internal and external `0037-*` prerequisites;
- `path:TODO.md`, `path:AGENTS.md`,
  `path:docs/pipeline/task-acceptance.md`,
  `path:docs/pipeline/branch-workflow.md`, and
  `path:docs/pipeline/process-roles.md`;
- validator-facing documentation for any tool that reports checkpoint or
  Feature-closure readiness.

Affected gates are:

- ordinary Task/Subtask implementation start gates;
- Task Acceptance for every target and its transitive required predecessor
  closure;
- checkpoint designation and checkpoint-boundary integration;
- Feature integration and Feature closure, immediately including `0038`.

The decision record's `repository:autodocs` subject and work-unit entry cover
the repository-wide reach, but its normative implementation must not be limited
to the three paths or two `0038` gates enumerated in the record. The additional
affected texts above already contain directly contradictory formulations and
must be aligned in the same governance change or explicitly marked as
superseded by the new rule.

## 4. Confirmed apparent and actual contradictions

The reviewed baseline contains these concrete collisions:

- `docs/pipeline/task-acceptance.md:15` says checkpoint selection is "decided up
  front", which excludes the directed late-designation window.
- `docs/pipeline/task-acceptance.md:19`, `AGENTS.md:178`, and
  `docs/pipeline/branch-workflow.md:406-408` say unflagged work carries no
  Acceptance record. Without a qualification, that contradicts the required
  individual Acceptance of unaccepted prerequisite-closure members.
- `TODO.md:9` says unflagged work needs no such record. This is correct only for
  independently triggering a review or satisfying an ordinary implementation
  start gate, not once that work enters an Acceptance batch.
- `TODO.md:67` says a node is reviewed only if marked. It needs the explicit
  caveat requested by Management: an Architect may mark it at any time before
  current Acceptance. It must also distinguish the initiating checkpoint review
  from induced predecessor Task Acceptance.
- `docs/pipeline/task-acceptance.md:225-230` says a checkpoint review need not
  accept its predecessor chain and moves that duty to Feature closure. That is
  incompatible with prerequisite-closed Task Acceptance if the review emits
  current `Acceptance: ✓` for the checkpoint. The text may preserve a narrow
  *technical pre-review* of the checkpoint, but that pre-review cannot grant
  current Task Acceptance until the bottom-up closure is accepted.
- `AGENTS.md:175-178` and `docs/pipeline/branch-workflow.md:402-408` conflate
  checkpoint integration reviews with all records created by the induced
  Acceptance batch. They need the same initiating-node versus batch-member
  distinction.
- `_src/tools/legacy_task_doctor.py` currently treats any syntactic Acceptance
  mark as sufficient checkpoint credit and its Feature readiness calculation
  checks only unaccepted mandatory checkpoints, not their current transitive
  Acceptance closure. Existing `task-acceptance.md:174-184` correctly says
  legacy readiness output is advisory. Normative text must retain that fail-
  closed warning; no tool result may be represented as proof of the new closure
  until the validator is extended and tested.

## 5. Binding wording and implementation constraints

The following constraints are necessary for this `supports` verdict. A
normative mutation that omits or reverses one is outside the reviewed scope and
requires a new decision and independent scope review.

### C-01 — Use one exact two-gate distinction everywhere

Every affected document must state, without relying on implied context:

> `[x]`/`[w]` ordinarily satisfies an implementation-start prerequisite without
> Acceptance. When Task Acceptance is assigned for a target, every required
> transitive `[x]`/`[w]` predecessor without current valid Acceptance enters the
> same bottom-up batch and receives an individual decision before the target can
> receive current `Acceptance: ✓`.

An explicit acceptance-before-start edge remains the only exception to the
ordinary start rule.

### C-02 — Qualify every "only checkpoints are reviewed" statement

The required sense is:

> Only a marked checkpoint independently triggers an integration review. This
> does not exclude unmarked predecessors from the prerequisite-closed Task-
> Acceptance batch induced by that review, and it does not mean checkpoint
> placement is frozen at decomposition.

No document may retain the unqualified claims "unflagged work carries no
Acceptance record" or "reviewed only if marked".

### C-03 — State the Architect's complete timing rule

At least `TODO.md`, `AGENTS.md`, and `task-acceptance.md` must state:

> Checkpoint placement is exclusively Architect authority. An Architect may add
> `Integration review: mandatory`, with recorded rationale, at any time before
> the affected node has current Acceptance, including while it is `[x]`/`[w]`.
> Current Acceptance closes that window. A later addition, removal, or movement
> requires separately authorized append-only invalidation or reopening first;
> history is never rewritten.

This timing permission does not waive `TK-2` or the cross-item gate-scope review
exception. A late checkpoint that can affect another unit's start, validation,
acceptance, integration, publication, or closure still needs the applicable
decision record and distinct Architect scope review before mutation.

### C-04 — Define "current Acceptance" and the late-designation race

"Current" means reachable, non-invalidated Acceptance bound to the exact Task
contract, work-product baseline, prerequisite Acceptance set, authority epoch,
and review evidence. Historical, stale, superseded, rejected, inconclusive, or
invalidated records do not close the Architect's window.

Review evidence and Acceptance bookkeeping remain separate commits. Immediately
before the bookkeeping commit, the reviewer must compare-and-swap the expected
Task block, checkpoint attribute, contract digest, prerequisite graph, and
Acceptance state. If an Architect added or changed a checkpoint after the review
baseline was pinned but before bookkeeping, the pinned review is stale and must
not be promoted. The changed checkpoint scope is reviewed first. This prevents
both lost updates and silent retroactive gates.

### C-05 — Preserve append-only history and handle already integrated work

A checkpoint may be added to an unaccepted Task even if its implementation has
already been merged upward. The designation cannot rewrite history or pretend
the earlier merge was reviewed; it gates any later boundary crossing and Feature
closure until the newly required review passes. Current Acceptance may not be
silently stripped or overwritten to create this state.

Existing Acceptance attempts remain append-only. At activation, pre-existing
records used as current credit must undergo impact analysis against the clarified
prerequisite-closure rule. An incomplete prerequisite set cannot be silently
grandfathered as proof of current prerequisite-closed Task Acceptance; it needs
additive disposition and, where required, reacceptance. Historical Features
already in `DONE.md` remain governed by the existing explicit non-retroactivity
rule.

### C-06 — Keep assignment, independence, and individual decisions exact

Assignment to accept a target authorizes only its deterministically enumerated
required closure under the pinned graph; the reviewer records that enumeration
before review. Graph or contract drift requires a new pinned baseline, not scope
appropriation. Every induced predecessor receives its own `accepted`, `rejected`,
or `inconclusive` result and its own evidence/bookkeeping relationship. TK-1,
specialist authority, digest binding, and bottom-up ordering apply to every batch
member, not only the initiating checkpoint.

### C-07 — Activation and validation

The clarified rule applies immediately to new Acceptance decisions and to any
still-open Feature integration/closure, including Feature `0038`, after the
normative governance commit becomes active on `main`. Documentation validation
must search all normative mirrors for the contradictory phrases identified in
section 4. Until machine enforcement proves transitive current Acceptance,
legacy doctor readiness remains advisory and privileged review performs the
closure calculation independently.

## 6. Verdict

**Position: supports.** `DEC-0044-020` selects the only interpretation that
simultaneously preserves implementation throughput, complete Acceptance
assurance, Architect risk response, and append-only review provenance. The
scope is repository-wide and cross-item. Normative mutation may proceed only
with constraints C-01 through C-07 implemented consistently; this review grants
no Acceptance, merge, integration, Feature closure, waiver, or specialist-risk
authority.
