# Atomic implementation check-in contract

## 1. Identity, status, and authority

- **Schema/version:** `atomic-checkin-contract@v1`
- **Contract ID:** `autodocs-0041-atomic-checkin-v1`
- **Source baseline:** `f5763cf21e98066f7e932d50a2b0e9c5802550f9`
- **Authority:** `DEC-0041-006` as corrected by `C001`–`C005`, and task allocation `DEC-0041-007`
- **Status:** non-operative candidate contract. Its presence on a branch does not change the current two-commit/implementation-`REF` rule.
- **Activation owner:** Task `0041-06`, through exactly one separately reviewed main-ref advance containing every manifest-bound consumer.

The SHA-256 of this file is the contract digest. The companion
`atomic-cutover-manifest@v1` pins that digest. Any byte change creates a new
candidate digest and invalidates downstream candidate and review bindings.

## 2. Normative vocabulary

- **Task:** one canonical legacy Task ID matching
  `^[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?$`.
- **base ref:** the full lowercase 40-hex commit ID captured by the immutable
  transaction/attempt record after claim-first setup and all authorized
  prerequisite preintegration, immediately before the first substantive
  change. The finalized claim copies this already-known value in the carrying
  tree; the open claim does not try to contain its own commit ID.
- **carrying commit:** the single implementation or disposition commit whose
  tree contains the complete scoped delta, finalized claim, and terminal Task
  marker and whose message contains the required trailers.
- **carrying tree:** the tree object of the carrying commit.
- **terminal marker:** `[x]` for implemented or `[w]` for a supported
  non-implementation disposition.
- **finalized claim:** the exact owned claim in the carrying tree, terminal in
  implementation lifecycle terms and complete without the carrying commit's
  not-yet-known object ID.
- **activation candidate:** the complete `0041-06` tree, not any producer
  branch, that binds this contract and the manifest.
- **historical record:** evidence governed by a pre-activation contract. It is
  preserved byte-for-byte and is not implicitly upgraded.

`MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHALL NOT`, and `MAY` are normative.

## 3. Exact commit-message grammar

The carrying commit message is UTF-8 and has this shape:

```text
<nonempty single-line subject>

<optional body paragraphs>

Task-ID: <canonical-task-id>
Base-Ref: <40-lowercase-hex-commit-id>
```

Rules:

1. `Task-ID` and `Base-Ref` are case-sensitive ASCII trailer tokens.
2. Exactly one physical line for each token MUST appear in the final trailer
   block. Continuation lines, folded values, duplicate tokens, case variants,
   empty values, comments, backticks, prefixes, suffixes, and inline copies do
   not satisfy the grammar.
3. `Task-ID` MUST match the canonical Task ID in the assignment, claim,
   authoritative Task line, transaction request, branch binding, and result.
4. `Base-Ref` MUST name an existing commit in the same repository, be reachable
   from the carrying commit, equal the immutable transaction/attempt's
   pre-substantive capture and the finalized claim's copied value, and be the
   carrying commit's first parent. All prerequisite merges and claim-first setup
   therefore occur before base capture.
5. Other trailers MAY be present only when their tokens cannot be confused with
   these two. A second semantic source for Task or base identity is forbidden.
6. The subject/body MUST NOT claim Acceptance, checkpoint passage, integration,
   Feature closure, release, or waiver unless separately authorized and carried
   by a different lifecycle transaction.

The first-parent equality in rule 4 is the v1 operational proof that the named
ancestor is the exact pre-substantive branch state rather than an older,
technically reachable but stale commit.

## 4. Preconditions and carrying-tree invariants

Before the first substantive byte changes, the implementer MUST:

1. hold an exact atomic award and immutable owner token;
2. create and commit the claim on the correct item branch;
3. merge every authorized done-but-unintegrated prerequisite required by the
   branch workflow without crossing a checkpoint;
4. verify the Task contract, write scope, prerequisite state, expected branch,
   and clean/index state; and
5. capture the resulting `HEAD` as `base_ref` in immutable transaction/attempt
   evidence without changing the tree. The open claim may identify that capture
   record but MUST NOT be committed again merely to embed the captured commit's
   own ID. The carrying tree copies the value into the finalized claim.

The carrying tree MUST satisfy all of these conjunctive invariants:

- the Task changes exactly once from `[p]` to `[x]` or `[w]`;
- the owned claim is present, names the same Task/request/owner token/base ref,
  has the corresponding terminal implementation disposition, and includes
  deliverable/disposition, validation, findings, and handoff evidence;
- every required work product or disposition artifact is present at its
  declared path and every changed path is in the award/claim manifest;
- no unrelated, foreign-owned, staged-only, generated-but-undeclared, or
  authority-prohibited byte is introduced;
- the terminal Task block and claim require no implementation `REF`, carrying
  hash, placeholder hash, or self-reference;
- `[w]` includes a reason, investigation evidence, affected scope, downstream
  effect, and authorized boundary; `[x]` includes the required product and
  implementer validation;
- no `Acceptance: ✓`, review verdict, checkpoint attribute change, claim rename
  to `DONE-*`, Feature closure, or `DONE.md` movement is performed; and
- the diff from `Base-Ref` to the carrying tree is the complete implementation
  transaction. A partial tree, second implementation-bookkeeping commit, or
  post-base intermediate commit is invalid.

After the first substantive change, amend, squash, rebase, filter, graft, or
other history rewriting is prohibited. Correction is additive under a new
commit or, when the carrying transaction has not published, by abandoning the
unpublished candidate and regenerating it from the same recorded base without
misrepresenting the abandoned object as completion.

## 5. Marker and claim semantics

`[x]` means implementation-complete and awaiting Acceptance. `[w]` means a
supported non-implementation disposition is complete and awaiting Acceptance.
Both remain ordinary implementation start gates unless a Task explicitly
requires Acceptance before start. Neither is Acceptance or Feature closure.

An open `[p]` Task and claim contain no implementation or review commit ID. They
MAY name the immutable capture record, but the claim MUST NOT create a new
pre-substantive commit merely to embed that commit's own ID. The finalized claim
in the carrying tree records the captured `Base-Ref`, contract version/digest,
manifest version/digest, validation identities, and product digests, but MUST
NOT guess the carrying commit ID. The Task header likewise contains no
implementation `REF` under v1.

The carrying commit ID is learned only after the commit exists. It is returned
by the transaction as immutable evidence and later consumed by the separate
review lifecycle.

## 6. Acceptance and authority boundary

Implementation completion grants no Acceptance, reviewer independence,
checkpoint, integration, Feature closure, release, signing, exception, risk
acceptance, or Management authority.

When separately assigned, Acceptance MUST additively bind:

- the exact carrying commit and tree;
- the exact independent review-decision commit;
- the pinned review baseline and Task-contract digest;
- direct and transitive prerequisite closure and current Acceptance boundaries;
- work-product, contract, activation-manifest, and validation-result digests;
- reviewer identity, assignment, independence, authority epoch, findings, and
  disposition.

Acceptance evidence and its path-isolated `Acceptance: ✓` bookkeeping remain
separate commits because both referenced commit IDs exist by then. Acceptance
bookkeeping never amends or rewrites the carrying commit or its claim.

## 7. Fail-closed error vocabulary

Every writer, parser, diagnostic, and gate MUST return or map to these stable
semantic codes. Tool-specific prefixes MAY wrap them but MUST preserve the
canonical code in structured output.

| Code | Required meaning |
| --- | --- |
| `ATC-TRAILER-MISSING` | Either required trailer is absent. |
| `ATC-TRAILER-DUPLICATE` | A required token or semantic case variant occurs more than once. |
| `ATC-TRAILER-MALFORMED` | Token placement, spelling, value syntax, encoding, folding, or trailer block is invalid. |
| `ATC-TASK-WRONG` | Trailer Task, claim, request, branch, or Task block identities differ. |
| `ATC-BASE-MISSING` | The named base object does not exist as a commit in the repository. |
| `ATC-BASE-NONANCESTOR` | The named base is not reachable as an ancestor of the carrying commit. |
| `ATC-BASE-STALE` | The base is reachable but is not the recorded immediate pre-substantive first parent. |
| `ATC-IDENTITY-CONTRADICTORY` | Multiple authoritative inputs disagree or an old/new contract is mixed. |
| `ATC-MARKER-MISMATCH` | Task and claim marker/disposition do not agree or transition is illegal. |
| `ATC-CLAIM-MISSING` | The exact owner-token claim is absent or ambiguous. |
| `ATC-CLAIM-NOT-FINAL` | Claim lacks final product/disposition, validation, findings, or handoff data. |
| `ATC-TREE-PARTIAL` | Deliverable, terminal Task, and finalized claim are not all in the carrying tree. |
| `ATC-SCOPE-UNRELATED` | The carrying diff includes undeclared or foreign bytes. |
| `ATC-HISTORY-REWRITTEN` | Post-substantive ancestry was rewritten or continuity is falsely asserted. |
| `ATC-MANIFEST-STALE` | Contract, manifest, baseline, consumer blob, or candidate digest differs. |
| `ATC-OLD-WRITER-REACHABLE` | A live path can still require/create implementation `REF` or second bookkeeping. |
| `ATC-ACTIVATION-PARTIAL` | The proposed activation omits or separately lands a synchronous consumer. |
| `ATC-CAS-LOST` | Expected branch/ref state changed before publication or activation. |
| `ATC-AUTHORITY` | The attempted transition exceeds implementation authority. |
| `ATC-HISTORICAL-AMBIGUOUS` | A historical/reopened record cannot be classified safely. |
| `ATC-ROLLBACK-INCOHERENT` | Rollback would mix contracts, discard evidence, or omit an activated consumer. |

No warning, fallback, inferred value, "best effort", or successful child exit
may convert one of these conditions into completion.

## 8. Historical, in-flight, and reopened work

1. Terminal and accepted records completed before activation remain readable
   under their contemporaneous contract and are not rewritten, backfilled, or
   represented as v1-compliant.
2. Work still `[ ]`, `[u]`, or `[p]` at activation has no completion credit. It
   either completes under the old contract before activation or receives an
   explicit migration record binding its preserved old claim/base/candidates,
   new owner/claim/base, and v1 contract digest. Mixed closure is rejected.
3. A materially reopened post-activation Task preserves all old evidence but
   uses v1 for the new delta and carrying commit. Earlier Acceptance is
   invalidated or bounded additively by the authorized lifecycle.
4. Historical candidate branches named by `DEC-0041-006`/`007` are evidence
   only. Merge, cherry-pick, squash, rebase, copying, or semantic transplantation
   is prohibited unless separately authorized reconstruction records the
   abandoned lineage and a fresh base/claim/carrying commit.
5. When classification is ambiguous, `ATC-HISTORICAL-AMBIGUOUS` blocks rather
   than grandfathering the record.

## 9. Activation, old-writer absence, and rollback

Preparation under `0041-02` and `0041-03` is non-operative. `0041-06` MUST:

1. pin this contract and manifest by SHA-256;
2. re-read every current consumer blob and reject drift;
3. bind every produced candidate path and digest;
4. assemble governance, editor, transaction, diagnostic, hygiene evidence or
   required fixes, tests, and matching guidance in one candidate tree;
5. prove no reachable current-authority entry point teaches, requires, accepts,
   or creates implementation-header `REF` or a second implementation-bookkeeping
   commit;
6. run the manifest validation order and negative/recovery matrix;
7. obtain the independently assigned mandatory checkpoint PASS against the
   exact combined tree; and
8. activate only through one authorized main-ref advance with required hygiene
   preflight and postflight.

After activation, Task `0041-05` MUST carry one real assigned item through the
complete provision, work, publication, atomic terminal transition, diagnostics,
hygiene, and Acceptance boundary. Contract validation alone is not that
end-to-end proof and cannot satisfy the Feature's terminal review floor.

Before activation, rollback abandons candidate branches and changes no operative
byte. After activation, rollback is one separately reviewed ref advance that
reverts the manifest's entire consumer set to its pinned coherent pre-activation
tree, preserves v1-era and historical evidence, invalidates affected work
additively, and completes impact analysis before work resumes.

## 10. Examples

### Positive carrying commit

Given claim-first/preintegration `HEAD`
`1111111111111111111111111111111111111111` and Task `1234-05`:

```text
feat(1234-05): complete bounded widget contract

Task-ID: 1234-05
Base-Ref: 1111111111111111111111111111111111111111
```

The commit's first parent is the stated base; its tree contains the complete
declared product, `1234-05 [x]`, and the finalized matching claim. No
implementation `REF` or Acceptance record is present.

### Negative cases

- Missing `Base-Ref` → `ATC-TRAILER-MISSING`.
- Two `Task-ID` lines, including a case variant → `ATC-TRAILER-DUPLICATE`.
- `Base-Ref: abc123` → `ATC-TRAILER-MALFORMED`.
- Reachable grandparent instead of the recorded first parent → `ATC-BASE-STALE`.
- Correct trailers but Task `[p]` or claim `[p]` → `ATC-TREE-PARTIAL` or
  `ATC-CLAIM-NOT-FINAL`.
- Correct tree plus `REF: pending` or a second closure commit →
  `ATC-IDENTITY-CONTRADICTORY`.
- Candidate changes an undeclared foreign claim → `ATC-SCOPE-UNRELATED`.
- Implementation writes `Acceptance: ✓` → `ATC-AUTHORITY`.

### Migration example

An item `[p]` when activation occurs retains its old claim and candidate as
historical evidence. A separately authorized migration record names their
digests, closes that ownership without completion credit, creates a fresh claim
from a new recorded base, and completes the new delta under v1. No old commit is
rewritten and no old validation is claimed as current.

### Rollback example

If pre-activation validation fails, discard the unintegrated `0041-06`
candidate; the two-commit rule stays operative. If a post-activation defect is
found, advance `main` through a separately reviewed rollback containing the
complete manifest-bound pre-activation consumer set, preserve atomic-era
carrying/Acceptance records, record invalidation impact, and block mixed writers
until the coherent contract is restored.

## 11. Requirement and decision trace

| Source | Contract coverage |
| --- | --- |
| `RQ-CI-01` / `REQ-0041-02-RD-01` / `DEC-0041-006 CON-01` | §§3–5 single carrying commit/tree. |
| `RQ-CI-02` / `REQ-0041-02-RD-02` / `CON-02` | §§3 and 7 exact trailers, ancestry, stale-base refusal. |
| `RQ-CI-03` / `REQ-0041-02-RD-03` / `CON-03` | §§5–6 no self-reference; Acceptance-owned identities. |
| `RQ-CI-04` / `REQ-0041-02-RD-04` / `CON-04`, `CON-06`, `CON-07`, `CON-10` | §8 preservation, migration, reopening, reconstruction. |
| `RQ-CI-05` / `REQ-0041-02-RD-05` / `CON-05`, `CON-08`, `CON-11`–`CON-13` | §9 synchronous consumers, old-writer proof, rollback. |
| `REQ-0041-02-RD-06` / `CON-03`, `CON-09` | §6 strict authority separation. |
| `DEC-0041-007 CON-01`–`CON-10` | Non-operative status, digest handoff, sole `0041-06` activation, checkpoints, rollback, and unchanged terminal floor in §§1, 8, and 9. |

## 12. Known current blockers carried into the manifest

The manifest must make all of these mechanically visible: freshness; prohibited
historical reuse; complete synchronous scope; one grammar; atomic tree; runner
journal/CAS/recovery preservation; editor safeguards; implementation versus
Acceptance diagnostics; hygiene compatibility; matching-guidance closure;
Acceptance separation; coherent rollback; ordered Tasks; both mandatory reviews;
real end-to-end proof; separately assigned integration authority; current marker
and non-operative status; and absence of external effects. None is waived by
this document or by green validation of this producer package.

The current `0041-06` write-scope declaration names the runner-transaction and
hygiene tests under `_src/tests/`, while the observed current files are under
`_src/tools/`. The manifest records both mismatches. They block activation until
the scope is corrected or authoritatively resolved; an activation owner must not
silently omit, duplicate, relocate, or treat the live tests as out of scope.
