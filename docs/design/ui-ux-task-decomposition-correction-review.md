# Independent Architect re-review — UI/UX task-decomposition correction

## Review identity and boundary

- **Reviewer:** `agent:data:ui-ux-task-decomposition-correction-review:20260824T112834Z`
- **Role / capability:** independent Architect reviewer; `privileged`
- **Candidate:** substantive correction `3f9aa330f0085dba87e5701dafbcc51c667c835e`, carried by claim tip `619e2f41e66d326eef9db98de94030eea1f53a8f`
- **Prior review:** `1907ddc344ed775543da9aa6de3bd7be9ea4f752`
- **Later controlling clarification:** Runner amendment `5d5996d07d8e8be71a99722a12e3afcb1d57919a`
- **Scope:** independent re-review of the five prior finding groups and consistency with the later Runner amendment. This is not Acceptance, integration, backlog mutation, checkpoint crossing, or Feature closure.

## Verdict

**Rejected.** The correction materially resolves finding group 5 and
substantially improves group 3, but groups 1, 2, and 4 remain materially open. The
document is not yet safe to allocate into executable Tasks: its package overlay
uses repeated ranges and generic labels instead of bounded package-specific
execution contracts, while its Runner treatment lacks the shared accepted
job-control contract and intermediate checkpoint required by the later
Architect amendment.

## Findings

### F-UIUX-CORR-001 — Critical — Runner is named but the amended interface and checkpoint are absent

The conventions correctly retire `sandboxed-grunt`, queue mutation, and
`run.sh`, separate direct execution from authority, and retain Runner as a
Dispatcher-selected role. That closes the original capability-class confusion.
It does not, however, satisfy the later amendment at `5d5996d07`: the proposal
has no shared predecessor product equivalent to amended `0037-21`, no complete
Task-ID-bound job record/lifecycle contract, no current-Acceptance-before-start
edges for consumers, and no intermediate mandatory checkpoint for that shared
interface. Its only Runner material is the short convention and staffing text;
the terminal review floor cannot substitute for the specifically required
intermediate interface checkpoint.

Required correction: add a bounded shared operational-role/background-job
interface package defining the amendment's identity, lifecycle, status,
resource/time, cancellation, retry/idempotence, evidence, handoff, cleanup,
recovery, and authority-negative controls; make it an intermediate mandatory
checkpoint with rationale; and encode current-Acceptance-before-start edges for
every package that consumes Runner-controlled background execution. Preserve
Runner as normally `unprivileged` and preserve the retirement of the sandbox
transport.

### F-UIUX-CORR-002 — Critical — F-N packages still declare post-migration `_src/**` writes

F-N.1, F-N.2, and F-N.3 still declare write scopes under `_src/import/` and
`_src/import/classic/`. This contradicts the later normative statement that
every F-F..F-O package writing implementation content may never write `_src/**`.
The conflict is not safely resolved by precedence: the executable overlay says
it wins on conflict and defines each row's write set as the package's “declared
Prereq + Scope/Write scope,” thereby carrying the three stale `_src/**` scopes.

Required correction: move all three F-N write sets to exact `src/**` paths,
place their starts behind E.T, and include them in the relocation collision
manifest. Then mechanically reject every post-migration package contract that
contains an `_src/**` output.

### F-UIUX-CORR-003 — High — the executable-contract overlay is uniform template data, not executable package contracts

The new 77-row overlay is complete by row count, but almost every non-terminal
row repeats the same validation (`unit/contract, negative, changed-path`),
recovery, resource ranges, cognitive/uncertainty/risk ranges, and placeholder
branch target. Terminal rows repeat a second template. Values such as
`1–4 CPU`, `5–60 min`, `tests 2k–12k`, `risk low–high`, `feature/<id>`, and
“declared Prereq + Scope/Write scope” do not identify the exact command or
harness, exact outputs, package-specific failure/recovery proof, or a bounded
estimate. The overlay itself also defers broad-directory expansion to allocation
instead of supplying the collision-free write manifest required before these
proposals can be treated as bounded executable work packages.

This leaves the substance of prior finding group 4 open despite filling every
table cell. Required correction: provide package-specific validation profiles
or exact commands and expected outputs, concrete write/evidence manifests,
package-specific recovery rehearsal, meaningful resource/time/test/uncertainty
estimates, and explicit branch/merge targets or a deterministic allocation rule
that produces them. Ranges spanning low through high risk or an order of
magnitude in runtime are not bounded estimates.

## Disposition of the five prior finding groups

1. **Capability / Runner model: partially resolved, still blocking.** Direct
   execution and authority separation are correct; the amended Runner shared
   interface, accepted predecessor edges, and intermediate checkpoint are absent.
2. **`_src` → `src` migration: unresolved and blocking.** F-N.1–N.3 retain
   `_src/import/**` write scopes which the overlay incorporates; the later
   prohibition is internally contradictory rather than executable.
3. **Gate enforceability: substantially resolved.** The normative gate table
   adds the missing D.T/K.T/J.T and F.1 acceptance edges, connects I.1 retirement
   to all release terminals, and binds qualifying cross-item gates to a decision
   record and distinct Architect scope review. Allocation must materialize these
   machine edges; no separate blocker is raised here.
4. **Package executability: unresolved and blocking.** The overlay is exhaustive
   in rows but generic in substance, as F-UIUX-CORR-003 details.
5. **Exact traceability: resolved.** RQ-012/013 receive implementation and
   terminal owners; exact Feature RQ sets and inclusive view-range mappings cover
   the 119-view inventory with one implementation owner and terminal verifier.
   The terminal Q mapping remains pinned to the baseline and is explicitly
   required to be copied and set-equality checked at allocation.

## Validation performed

- Pinned and inspected candidate `3f9aa330f0`, handoff `619e2f41e6`, prior
  review `1907ddc344e`, and amendment `5d5996d07d`; verified the amendment's
  actual branch tip is `b38c3202d0d40812733204d4386388ff73234599`.
- Reviewed the corrected decomposition, correction claim, prior findings, and
  the amendment's affected-node, dependency, checkpoint, and validation bounds.
- Confirmed the proposal's declared counts: 16 Feature sections, 77 package
  rows, 16 terminal packages, all 32 RQ identifiers, all 24 Q identifiers, and
  inclusive view mappings totaling 119.
- Changed-path inspection found three post-migration package write scopes under
  `_src/import/**` (F-N.1–N.3), contradicting the normative migration paragraph.
- Compared every original finding group against the normative overlay,
  migration/gate graph, exact trace section, and the later Runner amendment.
- `git diff --check` passes for this review worktree after authoring.

## Handoff

The candidate must not be allocated unchanged. A correction limited to the
three open finding groups can preserve the resolved gate and trace sections.
This verdict grants no Acceptance or integration credit.

## Second correction re-review — candidate `5651bff97596dde165ae09555b7374ea086f3988`

### Baseline and latest verdict

- **Second substantive correction:**
  `7aeedacd6405b63023d89cefb9bf149cc349978c`
- **Second correction claim tip:**
  `5651bff97596dde165ae09555b7374ea086f3988`
- **Prior rejected review:**
  `a3d6e1e8817910676b647d90c82d79d7c2c08bbc`
- **Review scope:** unchanged; independent Architect re-review of the three
  open finding groups only, without candidate mutation, Acceptance,
  integration, checkpoint crossing, `main` mutation, or Feature closure.

**Rejected.** The candidate fixes the F-N migration paths and adds the intended
A.4 lifecycle, consumer edges, and intermediate checkpoint. It still does not
baseline a consumable shared A.4 product, and its normative executable overlay
leaves every package dependent on an unowned validator. All terminal validation
contracts are also outside their declared write/evidence manifests, while all
77 branch targets contradict the repository branch contract. The decomposition
therefore remains unsafe to allocate as executable Tasks.

### F-UIUX-CORR-R2-001 — Critical — the A.4 shared interface is outside A.4's normative write manifest

The A.4 package bullet at candidate lines 128–154 correctly names the versioned
`operational-role-v1.json` and `background-job-v1.json` products and supplies
the required lifecycle, negative controls, checkpoint, recovery, and review
rationale. However, the overlay declares that it wins on conflict (lines
593–598), and A.4's overlay row (line 607) permits only
`src/ui/a/a-4/**`, `tests/uiux/a-4/**`, the package-local
`uiux-packages/a-4.{json,writes.json}`, and package evidence. It does not permit
either named shared contract under `docs/design/contracts/`.

Consequently the machine A.4 start edges can require current Acceptance of A.4,
but the package cannot produce the two shared interface products its consumers
are meant to accept. The prose lifecycle is materially improved; the explicit
predecessor work product is not baselined in an executable write contract.

Required correction: include the exact versioned shared-contract paths and
their schemas/fixtures in A.4's normative manifest, identify their public
types, validation/error behavior and compatibility/recovery rules, and bind the
consumer edges to those exact products and digests. Preserve the A.4
intermediate checkpoint and current-Acceptance-before-start semantics.

### F-UIUX-CORR-R2-002 — Critical — all package validation depends on an unowned tool; terminal contract inputs have no owner

Every one of the 77 overlay rows invokes
`src/tools/uiux_validate_package.py`, but no package manifest owns that path,
the candidate contains no such tool, and no predecessor product or dependency
edge supplies it. The commands are therefore syntactically package-specific
but not executable from their declared prerequisite graphs.

In addition, all 16 terminal rows invoke
`docs/design/contracts/uiux-packages/<terminal>.json` and
`<terminal>.writes.json`, while their normative write/evidence manifests contain
only terminal evidence. A whole-population check found the omission for E0.T
and A.T through O.T. Those validation inputs have no declared producer.

Required correction: create one bounded shared validation-interface predecessor
that owns the validator, schemas, result contract, negative fixtures, recovery,
and compatibility rules, with the necessary reviewed consumer gates; or replace
the shared command with package-owned exact harnesses. Give every terminal
contract input an exact producer and prerequisite. Any new shared blocking gate
must satisfy `decision-record@v1` and distinct Architect scope-review rules
before activation.

### F-UIUX-CORR-R2-003 — High — the deterministic branch rule contradicts the normative item-branch topology

All 77 rows target
`feature/<allocated-feature-id>/<package>` and merge to
`feature/<allocated-feature-id>`. The current branch workflow instead requires
the branch name to be the allocated item's exact ID, with Task branches based on
the exact Feature-ID branch and Subtask branches based on the exact Task-ID
branch (`docs/pipeline/branch-workflow.md`, lines 34–45). The proposed rule is
deterministic, but it deterministically produces the wrong branch identity and
does not distinguish Task from Subtask parentage.

Required correction: bind each allocated package to its exact allocated item ID
and parent item branch, preserving prerequisite-branch merges and carried claim
files. Do not introduce a second branch-naming convention inside the portfolio.

### Advisory — malformed overlay heading

Candidate line 593 begins with literal `+##`, so the normative overlay is not a
Markdown heading. This is not the basis of the rejection, but it should be
removed so renderers and structure-aware tooling recognize the section.

### Re-review disposition of the original five groups

1. **Capability / Runner model: still blocking.** The conceptual role,
   lifecycle, consumer set, accepted start edges, and intermediate checkpoint
   are now present, but the exact shared A.4 products remain outside the
   normative write manifest.
2. **`_src` → `src` migration: resolved.** N.1–N.3 now use disjoint
   `src/import/classic/n-*` roots and require E.T; no `_src/import/**` output
   remains.
3. **Gate enforceability: resolved for this review scope.** The A.4 consumer
   gate is machine-listed, uses `⊳acc`, and preserves the decision/scope-review
   requirement. Finding R2-002 concerns the missing validation predecessor, not
   removal of those corrected edges.
4. **Package executability: still blocking.** Exact-looking commands and paths
   do not form an executable graph when their common tool and terminal contract
   inputs have no owner, and their branch targets violate the repository
   topology.
5. **Exact traceability: remains resolved.** The second correction does not
   regress the exact RQ/Q/view ownership established by the first correction.

### Second-round validation evidence

- Pinned the exact `7aeedacd64` substantive correction and `5651bff975` claim
  tip; verified direct parentage and a clean candidate worktree.
- Whole-population table parse: 77 unique package rows, 16 terminal rows, 77
  validator command users, zero validator write owners, and 16 terminal rows
  whose invoked contract/write-manifest inputs are absent from their normative
  write/evidence manifests.
- Compared the A.4 bullet, overlay, machine gate table, and controlling Runner
  amendment `5d5996d07d8e8be71a99722a12e3afcb1d57919a`.
- Compared all 77 declared branch targets with the normative item-ID branch
  rules in `docs/pipeline/branch-workflow.md`.
- `git diff --check` passes for the candidate correction. The process-document
  doctor exits 0 with the current repository-wide baseline of 118 documents,
  30 findings, and one pre-existing unrelated broken-link error in
  `docs/dossiers/0044-03-gate-scope-proposal.md`; it does not validate this
  design document's executable graph.
- Pre-mutation integration hygiene passed over 161 registered worktrees for the
  isolated review worktree. No candidate or shared-root file was changed.

### Second-round handoff

The exact candidate `5651bff975` must not be allocated unchanged. This review
changes no candidate file and grants no Acceptance, integration, checkpoint, or
Feature-closure credit.

## Third correction re-review — candidate `9190e5a346d87edbc62a4d38b4050bb2aab000eb`

### Baseline, boundary, and verdict

- **Third substantive correction:**
  `7707b8d00a7e5cfc3e733cd990c7be373e3aa41b`
- **Third correction claim tip:**
  `9190e5a346d87edbc62a4d38b4050bb2aab000eb`
- **Prior rejected review:**
  `6b8a81ff1171127a95b44795bd4d1852df4ffe7b`
- **Scope:** unchanged independent Architect re-review of findings
  F-UIUX-CORR-R2-001 through R2-003 plus regression inspection. This is not
  Task Acceptance, integration, checkpoint crossing, backlog/governance
  mutation, `main` mutation, allocation, or Feature closure.

**Passed — no blocking finding remains in the assigned re-review scope.** The
candidate now owns and types A.4's exact shared interface products, gives every
package an owned validation harness and owned contract inputs, and binds every
package branch to the exact allocated item and parent item IDs. The migration,
Runner lifecycle/checkpoint/consumer gates, exact trace mappings, and prior gate
corrections remain intact. This verdict is Architect work-product review only;
it grants no `Acceptance: ✓` or integration credit.

### Disposition of second-round findings

1. **F-UIUX-CORR-R2-001 — closed.** A.4's normative row now owns
   `operational-role-v1.{json,schema.json}`,
   `background-job-v1.{json,schema.json}`, the background-job fixtures, its
   package contract/write manifest, implementation, tests, and evidence. The
   appended normative interface text defines the public role, capability,
   identity, state, status, result, cancellation, retry, handoff, and recovery
   types; invalid fields/transitions; compatibility/versioning; recovery; and
   exact shared-contract-digest binding by consumers. The A.4 intermediate
   checkpoint and current-Acceptance-before-start edges remain unchanged.
2. **F-UIUX-CORR-R2-002 — closed.** All 77 validation commands now invoke their
   package-owned `tests/uiux/<package>/validate.py`; no command references the
   removed portfolio-global validator. Every row owns its package contract and
   write manifest. All 16 terminal rows additionally own their harness,
   fixtures, terminal contracts, candidate manifest, validation, recovery, and
   resource evidence. No invoked validation input is left without a declared
   producer/write scope.
3. **F-UIUX-CORR-R2-003 — closed.** All 77 branch columns now use exact
   `<allocated-item-id>` and `<allocated-parent-item-id>` substitutions. The
   normative rule defines Task→Feature and Subtask→Task parentage, prerequisite
   and claim carriage, and rejection of prefixes, slugs, aliases, or parent
   mismatch, matching `docs/pipeline/branch-workflow.md`.
4. **Prior advisory — closed.** The overlay heading is now valid Markdown
   `## 4a`; the stray leading `+` is absent.

### Regression review

- The substantive delta is limited to the executable overlay, its ownership and
  interface explanations, and the correction claim. It does not alter the gate
  table, exact RQ/Q/view mappings, Feature/package inventory, or migration rule.
- F-N.1–N.3 retain disjoint `src/import/classic/n-*` roots, E.T prerequisites,
  and the repository-wide `_src/**` prohibition for post-migration packages.
- A.4 remains the sole shared Runner interface and an intermediate mandatory
  checkpoint; all nine enumerated consumers retain `⊳acc A.4` start gates and
  digest binding. No sandbox transport, runner queue, `run.sh`, or authority
  inheritance is reintroduced.
- The inventory remains 16 Features, 77 unique packages, and exactly 16
  terminal integrating packages, one per Feature. Exact trace ownership remains
  unchanged.

### Third-round validation evidence

- Verified exact parentage `5651bff975` → `7707b8d00` → `9190e5a346` and a
  clean candidate worktree.
- Whole-population parse: 77 unique rows; 16 terminals; zero missing
  package-owned harnesses; zero missing package contract/write-manifest pairs;
  zero old global-validator users; zero invalid branch-target rows.
- Negative scans: zero malformed `+##` headings, zero `_src/import`
  occurrences, and zero old `feature/<allocated-feature-id>` branch prefixes.
- Confirmed A.4's two versioned shared products, schemas, fixtures, named public
  types, error/transition rules, compatibility and recovery bounds, and exact
  digest consumption.
- `git diff --check` passes for the complete third correction. Pre-mutation
  integration hygiene passes over 163 registered worktrees for the isolated
  review worktree.

### Third-round handoff

Within the assigned scope, candidate `9190e5a346` is suitable for the separate
allocation/integration workflow. Outstanding human decisions and external
inputs already declared by the decomposition remain allocation gates; this
review neither resolves nor waives them. No candidate, backlog, governance,
Acceptance, integration, or `main` state was changed.
