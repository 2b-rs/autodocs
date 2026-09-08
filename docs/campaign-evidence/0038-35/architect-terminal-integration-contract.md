# Feature 0038 terminal integration contract

Status: Architect work product under `DEC-0038-005`. It defines Task `0038-35`
and grants no implementation, Acceptance, integration, or closure authority.

## Independent Architect gate-scope review

**Position: supports**, for exact authority baseline
`96e7a8b71a75773fd2f7193245792243e704a574` and the Task contract in this
candidate. Reviewer identity
`agent:data:0038-terminal-integration:20260825T192007Z-6d7f42a9` is the
management-instantiated Architect and is distinct from every future
Implementer, structured Task reviewer, and terminal Integrator.

The `cross-item-blast-radius` and `material-architecture-or-repository-behavior`
triggers apply: this Task blocks or permits Acceptance aggregation, Feature
integration, closure bookkeeping, and the `TODO.md`→`DONE.md` transition for
all 38 existing Feature work units. The smallest intent-preserving scope is one
terminal mandatory checkpoint with all 38 nodes directly enumerated, fresh
structured review of `0038-33`/`0038-34`, a digest-bound aggregate, and
fail-closed closure ordering. A waiver, partial node list, implicit transitive
coverage, or reuse of historical partial integration would be under-scoped.

Affected work units are Feature `0038`, new Task `0038-35`, all 38 listed
prerequisites, and the repository closure state. Affected gates are
`task-start:0038-35`, `task-acceptance:0038-33`,
`task-acceptance:0038-34`, `integration:0038-35`,
`feature-aggregate-review:0038`, and `feature-closure:0038`. This review supports
only the declared reach; it is not Acceptance, an integration review, an
integration verdict, implementation permission, or closure authority.

## Goal and preserved history

Task `0038-35` restores the exactly-one terminal integration floor missing from
Feature `0038`. It supersedes only the no-closure condition identified as R-6
in `docs/pipeline/approvals/0038-main-integration-20260821T000000Z.md`.
The partial integration note, `DEC-0038-001`, every historical rejection, every
accepted/rejected Task review, preserved tag, and R-1…R-10 narrative remain
append-only evidence. No earlier partial integration is relabelled as closure.

## Complete prerequisite boundary

`0038-35` directly names every one of the 38 existing Feature-0038 work units
as a prerequisite, including child units and `[w]` dispositions. This makes the
closure boundary mechanically explicit rather than relying on incidental graph
reachability. In particular, `0038-33` and `0038-34` are direct prerequisites
and receive fresh structured Acceptance at their current pinned baselines.

The Integrator expands the complete prerequisite-closed review batch from the
exact `0038-35` candidate. Current valid Acceptance may bound ordinary nodes
under `task-acceptance.md`, except that `DEC-0038-005` deliberately requires
fresh review records for `0038-33` and `0038-34`; their prior records remain
history but do not satisfy this terminal run.

## Roles and order

1. **Architect — Data (this package):** defines `0038-35`, its mandatory
   checkpoint, graph, contracts, roles, and validation. No implementation or
   review authority.
2. **Implementer — distinct from Data and all terminal reviewers:** creates the
   aggregate manifest, digest set, validation evidence, closure candidate, and
   recovery/handoff package on branch `0038-35` cut from the Feature `0038`
   branch after merging all done prerequisites. Capability class `privileged`
   because the candidate includes authoritative backlog/closure bookkeeping;
   the role is Implementer only and may not accept or integrate.
3. **Fresh structured Task reviewer(s):** privileged identities independent of
   each reviewed Task's implementers, Data, the `0038-35` Implementer, and the
   terminal Integrator where feasible under the recorded separation rules.
   They issue new append-only decisions for exact pinned `0038-33` and
   `0038-34` baselines, review bottom-up, rerun the named executable evidence,
   and preserve all earlier rejections.
4. **Terminal Integrator — distinct from Data and Implementers:** receives an
   exact assignment for the candidate/target/mode. It runs candidate hygiene,
   complete prerequisite-closed Acceptance, the Feature aggregate review,
   required validation, root preflight before/after, and alone may integrate
   and move Feature `0038` to `DONE.md` after every gate passes.

Order is strict: architecture integration → `0038-35` implementation → fresh
`0038-33`/`0038-34` structured review and induced batch review → terminal
checkpoint/aggregate review → closure bookkeeping candidate → root integration
and `DONE.md` move. Any rejection or inconclusive result stops the sequence and
is recorded append-only; it is never repaired silently by the Integrator.

## Implementer write scope and deliverables

The future Implementer claim must bind exact paths before mutation. The minimal
product scope is:

- `docs/campaign-evidence/0038-35/aggregate-manifest.json`;
- `docs/campaign-evidence/0038-35/implementation-evidence.md`;
- `docs/campaign-evidence/0038-35/validation/` for bounded structured outputs;
- Task `0038-35` bookkeeping in `TODO.md` and its own claim file; and
- a closure-candidate manifest that describes—but does not prematurely perform—
  the exact Feature block removal/addition between `TODO.md` and `DONE.md`.

The manifest binds: exact Task contract bytes/digest; source `main`, Feature,
and candidate SHAs; all 38 prerequisite IDs, markers, REFs, Acceptance states,
contract/work-product/review evidence digests; the fresh `0038-33`/`0038-34`
review-record IDs and baselines; historical rejection references; validation
commands/results; TODO/DONE block digests; rollback/recovery instructions; and
the expected root target SHA. Unknown, missing, duplicated, stale, or
unreachable evidence fails closed.

## Acceptance and validation contract

The package is eligible for terminal integration only when all of these hold:

- every prerequisite is terminal and reachable from the candidate;
- current structured Acceptance covers the complete induced batch, with new
  append-only decisions for `0038-33` and `0038-34` on their exact current
  baselines;
- the aggregate manifest recomputes byte-for-byte and has no missing,
  duplicated, stale, or unreviewed node;
- focused suites named by `0038-33` and `0038-34`, repository validation,
  automation-safety policy validation, task/claim/backlog structural checks,
  decision-record validation, and `git diff --check` pass at the exact candidate;
- `docs/pipeline/approvals/0038-main-integration-20260821T000000Z.md`, historical
  rejection records, and preserved snapshots are unchanged;
- the proposed `DONE.md` block preserves the Feature goal, authority, terminal
  Task dispositions, all Acceptance/review REFs, the terminal aggregate review,
  manifest/evidence digests, closure timestamp/authority, and recovery pointer;
- exactly one terminal integrating Task exists for Feature `0038`; and
- no `TODO.md` removal, `DONE.md` addition, Feature closure, or `main` advance
  occurs before the terminal Integrator records a passing verdict.

## Capability and resource profile

- Architect: `privileged`, direct read/Git/text validation, cognitive `high`,
  token 12k–24k, context `large`; no network, credentials, or external effects.
- Implementer: `privileged`, direct Git plus deterministic local validation,
  cognitive `high`, token 20k–40k, context `very-large`, CPU up to 30 minutes,
  memory up to 2 GiB; no network, credentials, publication, or root mutation.
- Structured reviewers/Integrator: `privileged`, independent, exact assignment;
  cognitive `critical`, token 24k–48k, context `very-large`, validation wall
  budget up to 60 minutes and 4 GiB. Root merge/closure remains Integrator-only.

Rollback before integration is abandonment of the candidate branch while all
history remains reachable. After a failed review, append the finding and create
a new corrected candidate; never rewrite decisions or rejections. After root
integration, recovery follows the preserved exact pre-merge SHA and documented
branch-workflow procedure; no autonomous reset or tag deletion is permitted.
