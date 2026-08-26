# Independent Architect review — UI/UX Task decomposition

## Review identity and immutable baseline

- **Reviewer:** Architect `data` (Team Enterprise), distinct from candidate
  Architect `seven` (Team Voyager)
- **Review authority:** Project Lead `jean-luc`, agent-inbox thread
  `ui-ux-task-decomposition-20260824`
- **Candidate:** `ui-ux-task-decomposition-20260824@76d227ed73b48b0e48d66e585d0c5e0a13de1868`
- **Candidate artifact:** `docs/design/ui-ux-task-decomposition.md`
- **Requirements handoff:** `40ceb3d2eb4cd818547833c9f5b9ecb50408bf9a`
- **Requirements candidate:** `ae11b1f8beacaaf4a84998ed6f99b2d5cf3533fd`
- **Requirements review:** `9896d9d2073c91a9345b7c1f03cce3ffa817cb01`
  (`review-ready`; no open requirements finding)
- **Relevant newer architecture input:** current-user direct-execution direction
  recorded for `0037-51` at `a57582e6cdf60a2d5ba37d1af3ff3be7de3afe77`;
  bounded Architect decision/scope-review candidate
  `review-0037-51-scope-data-20260824T083513Z@9f4d3f6ee04389a77dc296ed21a85f918d75739d`
- **Review branch:** `review-ui-ux-task-decomposition-data-20260824`
- **Review claim:** `TODO-data-ui-ux-task-decomposition-review-20260824.md`

This is an independent architecture/decomposition verdict. It is not Task
Acceptance, an integration review, a checkpoint crossing, an implementation
authorization, an identifier allocation, or a Feature-closure decision. The
review changed neither the candidate nor its requirements/design corpus.

## Verdict

**Verdict: `rejected`.** The candidate has a sound Feature skeleton and passes
its headline count checks, but it is not yet a bounded executable decomposition.
Five material finding groups remain: the capability model is stale and one
terminal assigns checkpoint work to an ineligible capability; the directory
migration is not represented in the dependency/path graph; several declared
cross-item gates are absent or unenforceable; most package contracts omit the
validation/recovery/resource detail promised by their convention; and summary
coverage prose is standing in for exact package-level requirement/quality/view
ownership. These defects can change implementation start, write collision,
review authority, security, and acceptance behavior, so allocation must not
proceed from this candidate.

## Independently reproduced passing evidence

- The candidate diff from the requirements handoff adds only the candidate
  Architect claim and the decomposition; `git diff --check` passes.
- There are 16 unique Feature sections: F-E0 and F-A through F-O.
- There are 77 unique package IDs with the declared per-Feature counts.
- There are 16 terminal IDs, exactly one per Feature. All 16 say
  `Integration review: mandatory` and provide a checkpoint rationale.
- Normalizing `F-X.T` references to package `X.T` and F-E0 acceptance to E0.T,
  every parsed package prerequisite endpoint exists and the declared package
  graph has no syntactic cycle.
- The source baselines contain 32 unique contiguous `RQ-UIUX-001..032`, all 24
  `Q-01..Q-24`, and exact inventory/route-matrix set equality for 119 unique
  view IDs.
- D-01 through D-06 are all carried into a neutrality/consumption table rather
  than silently assigned a value in the pinned candidate.

Those passes do not resolve the semantic and contract findings below.

## Findings

### F-UIUX-DECOMP-001 — Critical — execution capability and checkpoint authority are contradictory

The convention defines `sg` as “sandboxed-grunt via runner queue” and assigns
that capability to 55 of 77 packages (`ui-ux-task-decomposition.md:26-28`). The
future architecture direction now requires direct Shell/Git execution for every
agent and removal of runner-only dependencies (the newer input pinned above);
carrying `sg` into a new UI/UX portfolio would immediately recreate the
dependency being retired. This is material architecture drift, not a
terminology-only issue. The 0037-51 artifacts are not treated as integrated
governance here; they preserve and analyze the direct current-user input that
the corrected decomposition must reconcile before allocation.

Independently, E0.T is both the terminal integrating Task and a cross-item
ratification checkpoint, but its capability is `sg + independent reviewer`
(`:85-93`). A sandboxed-grunt cannot cross a mandatory integration checkpoint,
and an independent reviewer is not a substitute for a separately authorized
privileged Integrator. Thus E0.T is internally invalid even under the candidate's
own current-governance vocabulary.

**Required correction:** replace the `sg/up` execution split with direct
execution capability requirements while keeping execution, authority,
independence, competence, data, external-resource, and specialist requirements
separate. Assign E0.T a privileged Integrator and a distinct competent reviewer;
do not infer either from direct tool access. Re-run a normative scan proving no
future package requires `sandboxed-grunt`, a runner queue, or a runner action.

### F-UIUX-DECOMP-002 — Critical — F-E migration order and downstream write paths permit collisions

The candidate says that named prerequisites, not phase labels, control starts
(`:47-48`), that F-E is an isolated `_src`→`src` migration (`:56-57`), and that
implementation uses `_src/**` only until F-E relocates it (`:32-36`). Yet 33
packages in F-F through F-O still declare `_src/**` write scopes, while none is
transitively gated by E.T. Examples begin with F.1/F.2/F.3 (`:280-305`) and
continue through the control-plane, ticket, import, and research packages.

Consequently the named graph permits downstream work to create or modify the
old tree while F-E moves it, although the prose calls P3/P4 post-migration and
claims the migration is isolated. Phase prose cannot prevent that start, and a
compatibility shim does not make overlapping source-tree ownership disjoint.

**Required correction:** choose one explicit topology. The supported reading is
to gate every post-migration source consumer through E.T (directly or through an
explicit accepted predecessor interface) and change its write scope to `src/**`.
If pre-migration implementation is intended instead, the candidate must define
the complete relocation manifest, ownership handoff, branch merge order, and
collision-free freeze; it may not call P2 isolated. Validate reachability and
scope collision on the resulting graph, not on phase names.

### F-UIUX-DECOMP-003 — High — cross-item gates are incomplete or not encoded in the graph

The candidate correctly identifies seven gate-scope areas in section 5, but the
set is not complete for its own declared behavior:

- D.T and K.T acceptance block I.4 and F-L; K.T and J.T acceptance plus D-04
  block F-M. Those are cross-item start-contract changes and require TK-2
  decision records plus distinct Architect scope review, independently of the
  terminal checkpoint flags. Section 5 omits D.T, K.T, and J.T as such gates.
- F.1 says A.T and B.T are “accepted foundations” (`:282-285`) without the
  convention's `⊳acc` marker, leaving the actual start rule ambiguous.
- I.1 promises browser-PAT retirement **before any redesigned page ships**
  (`:364-370`), but only I.T depends on I.1. No other Feature terminal or
  publication gate consumes it, so the cross-Feature prohibition is
  unenforceable in the proposed DAG.
- M.1 encodes its J.T/K.T/D-04 conditions in prose as a “Start gate” rather than
  the required `Prereq` field. A parser implementing the candidate's own
  convention therefore sees M.1 without prerequisites.

**Required correction:** enumerate every gate whose declared behavior changes a
different work unit; name affected units and gates; require a conforming
decision record and distinct Architect scope review before the first qualifying
mutation; and encode each start/publication dependency as a machine-checkable
edge with one acceptance semantic. Add an enforceable predecessor from I.1 to
every release boundary it claims to block, or narrow the claim.

### F-UIUX-DECOMP-004 — High — most package contracts are not self-contained or executable

The convention promises exact write scope, validation kind/evidence, RQ/Q/view
coverage, risk/recovery, and advisory test-design sizing for every package
(`:21-30`). A structured field audit of all 77 package blocks found:

- 75 without a `Validation` field;
- all 15 terminal blocks other than E0.T without an exact `Write scope` field;
- 73 without a package-specific risk and recovery field;
- all 77 without an advisory runtime/CPU range (E0.1 names CPU as a measurement
  output, not an execution estimate), all 77 without cognitive-demand and
  uncertainty ranges, and all 77 without an allocation-neutral branch target;
- M.1 without the promised `Prereq` field.

Some scopes mention tests or failure cases, and section 8 supplies a generic
release recovery paragraph, but neither is an exact Task validation/recovery
contract. Several packages also name broad shared directories such as
`_src/ui/components/`, `_src/ui/universes/`, or `_src/ui/governance/` without a
file manifest or intra-Feature ownership boundary. An implementer would have to
make substantive architecture, evidence, recovery, and collision decisions.

**Required correction:** give every package a uniform bounded contract with
inputs/predecessor products, exact output/write paths, test scope and kind,
commands or harness/profile, evidence paths, capability/data/tool/external
needs, risk and package-specific recovery, advisory tokens/test-design,
runtime/CPU, cognitive demand, uncertainty and material-risk ranges with
assumptions, and an allocation-neutral branch/merge target. Split any package
whose exact write set cannot be made disjoint or retained in one context.

### F-UIUX-DECOMP-005 — High — summary references do not provide exact package-level trace ownership

Section 7 claims that all 32 requirements appear in package Coverage lines and
that roadmap bindings are preserved unchanged (`:588-597`). Independent parsing
of the 77 package blocks disproves the first statement: RQ-UIUX-012 and
RQ-UIUX-013 do not occur in any package block; they appear only later in the
summary. Comparison with the roadmap's per-Feature matrix also finds missing
bindings in most Feature sections—for example F-B lacks RQ-011/012/013/014/026,
F-D lacks RQ-020/032, and F-I/F-J each lack RQ-002/012/032.

The same problem affects view ownership. Only seven of the 119 exact inventory
IDs occur in package blocks; labels such as “KN family”, “RP”, “SYS family”, or
the section-7 family totals (`:604-608`) do not say which bounded package owns
each row, its states, no-JS mode, permissions, responsive/localization evidence,
or terminal verification. Quality gates Q-01..Q-24 are globally named, but many
consumer obligations are likewise assigned only by summary phrases such as
“consumer terminals”, not by the concrete terminal package contract.

**Required correction:** add a machine-readable or mechanically checkable
package trace matrix mapping every package to exact RQ IDs, Q gates, and view
IDs/ranges, and every baseline item back to at least one implementation package
and one terminal verifier. Prove exact equality with the roadmap requirement
matrix, quality trace matrix, and 119-row route matrix; reject missing, extra,
duplicate-owner, or summary-only coverage.

## Semantic graph disposition

The normalized explicit package references form a syntactic DAG, but the
candidate's claim of semantic-deadlock safety is not accepted. The F-E path
collision, unenforceable I.1 release condition, ambiguous F.1 acceptance gate,
and prose-only M.1 start gate mean the executable graph is not the graph the
analysis says it checked.

## Decision and authority note

During this review, mailbox message `1787565781899-43843aa4` relayed alleged
Management values for D-01, D-02, and D-06. Mail is coordination and does not
establish authority; it arrived after the immutable candidate and is not used to
rewrite or re-score that baseline. The relay was sent to Project Lead `jean-luc`
for verification against a direct user record and durable handling by the
assigned owner. D-01..D-06 therefore remain unresolved for this verdict.

## Re-review entry criteria

A fresh immutable candidate is reviewable when it:

1. dispositions all five finding groups additively and records any changed
   assumptions or authority inputs;
2. retains 16 Features, exactly one terminal integrating Task per Feature, and
   justified intermediate checkpoints unless a new Architect decision explains
   a different bounded structure;
3. passes exact ID/count/set, prerequisite endpoint/cycle/direction, semantic
   deadlock, write-scope collision, gate-scope, and package-field validators;
4. demonstrates exact RQ/Q/view ownership rather than summary-only coverage;
5. remains allocation-neutral and changes no backlog, Acceptance, integration,
   `main`, or closure state merely to answer this review.

The reviewer did not implement corrections and does not accept or integrate the
candidate.
