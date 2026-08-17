# Structural Legacy Task/Claim Editor

Status: implemented planning and promotion-preflight contract for Feature `0038`, Task `0038-05.01`. Authoritative publication remains disabled until `0038-05.02` integrates this contract into the durable coordinator completed by `0038-02`.

## Purpose and authority boundary

`_src/tools/legacy_task_editor.py` replaces free-form legacy backlog/claim rewriting with:

1. a closed `legacy-task-editor-operation@v1` operation;
2. exact structural parsing and digest-bound preconditions;
3. pure byte-splice rendering;
4. a content-addressed candidate plus bounded unified diff;
5. complete mutation-free promotion preflight;
6. a machine-readable coordinator-required handoff result.

It supports typed plans for:

- pickup;
- progress;
- closure;
- wontfix;
- parent aggregation without parent auto-closure;
- REF insertion or exact stale-REF correction;
- claim handoff;
- claim finalization;
- append-only correction.

The editor does **not** run Git, shell commands, heredocs, root `run.sh`, network clients, package managers, or the clock. `recorded_at` is an explicit operation input. It never interprets a caller-supplied regex, glob, pathspec, shell string, or Markdown replacement fragment.

`0038-05.01` deliberately performs no authoritative write. Portable pathname replacement cannot provide repository-authority compare-and-swap or race-safe rollback against uncooperative writers, even for one file. The `promote` command therefore validates every source/candidate precondition and returns exit `50`, verdict `verified-coordinator-required`, and complete handoff evidence. `0038-05.02` owns all single-file, multi-file, create, archive, and deletion publication through `_src/tools/runner_transaction.py` after `0038-02` installs durable lock/journal/resume/rollback behavior.

The old `_src/tools/task_bookkeeping_closure.py` is retired and mutation-free. Its compatibility APIs and CLI return a fail-closed message directing callers to this editor.

## CLI

Planning:

```sh
python3 _src/tools/legacy_task_editor.py plan \
  --operation operation.json \
  --root . \
  --candidate-dir output/logs/<task>/<request>/candidate \
  --json
```

Promotion preflight and coordinator handoff:

```sh
python3 _src/tools/legacy_task_editor.py promote \
  --candidate-manifest output/logs/<task>/<request>/candidate/candidate.json \
  --expect-candidate-sha256 <64-lowercase-hex> \
  --root . \
  --json
```

There is no inline `--fix`, arbitrary text replacement, direct claim deletion, or one-step plan-and-apply command.

Exit groups:

| Exit | Meaning |
|---:|---|
| `0` | Candidate planned successfully. |
| `10` | Operation JSON/schema/value failure. |
| `20` | Source/precondition/digest/state failure. |
| `30` | Render or postcondition failure. |
| `40` | Candidate/member/diff/semantic-equivalence failure. |
| `50` | Candidate and current preimages verified; durable coordinator publication is required. |
| `90` | Internal failure before authoritative mutation (the tool has no authoritative mutation path in `.01`). |

## Closed operation contract

Top-level fields are:

```json
{
  "schema": "legacy-task-editor-operation@v1",
  "operation_id": "task-operation-001",
  "kind": "closure",
  "recorded_at": "2026-08-17T08:00:00Z",
  "subject": {
    "feature_id": "0038",
    "task_id": "0038-05.01"
  },
  "actor": {
    "request_id": "request-001",
    "owner_token": "agent:zed:0038-05.01:request-001"
  },
  "backlog": {
    "path": "TODO.md",
    "expected_document_sha256": "...",
    "expected_feature_sha256": "...",
    "expected_task_sha256": "...",
    "expected_marker": "p"
  },
  "claim": {
    "path": "TODO-zed-0038-05.01-request-001.md",
    "expected_document_sha256": "...",
    "expected_task_id": "0038-05.01",
    "expected_request_id": "request-001",
    "expected_owner_token": "agent:zed:0038-05.01:request-001",
    "expected_state": "p"
  },
  "payload": {
    "substantive_ref": "0123456789abcdef0123456789abcdef01234567",
    "summary": "Implemented and validated the exact deliverable."
  }
}
```

All objects reject duplicate and unknown keys. `subject`, `actor`, backlog, claim, and payload identities must agree. Any operation touching an existing claim requires the exact current claim owner/request as actor. Claim filenames must match `TODO-<agent>-<task>-<request>.md`; Task pointer path, owner token, and base must match the claim. Pickup accepts `base_commit: pending-discovery` for the documented sandboxed bootstrap flow.

Narrative fields must be one non-structural printable line. ASCII controls, every Python `splitlines()` separator (including U+0085/U+2028/U+2029), HTML-comment delimiters, angle brackets, and fence delimiters are rejected. Paths are exact in-root paths without `.git`, root `run.sh`, traversal, backslashes, globs, or role aliasing. Backlog/source/destination/archive path roles are pairwise disjoint.

## Structural parser

The parser operates on exact UTF-8 bytes and preserves byte offsets:

- Features are canonical column-zero `## Feature: XXXX — ...` headers.
- Tasks are canonical column-zero `- [m] **XXXX-YY[.ZZ]** ...` headers.
- Task content ends before the next non-indented structural line, including neighboring Task, Campaign, or Feature headings.
- Task-like text inside HTML comments or fenced code blocks is not structural.
- Fence opening/closing uses the same backtick/tilde character, at least the opening length, no more than three leading spaces, and whitespace-only close suffixes.
- Normative `Acceptance criteria` and `Definition of Done` are exact two-space-indented sibling bullets and honor the same comment/fence visibility.
- Visible authoritative REFs exclude HTML-comment values.
- Claims support canonical identity sections and retained legacy preamble/bullet/backtick variants without incidental reformatting; missing `task_id` may be derived only from a valid owner token.

A target Feature and Task must each be structurally unique. Rendering splices only the exact Task or claim span. Candidate postconditions compare ordered Feature/Task identities, normative-section counts, claim-pointer counts, required marker transitions, and visible authoritative REF cardinality.

## Operation semantics

| Kind | Required behavior |
|---|---|
| `pickup` | `[ ]`/`[?]` → `[p]`; reject another active claim; render exact canonical pointer and new canonical claim. |
| `progress` | Require active `[p]`; append Task progress or claim progress plus a new final next step. |
| `closure` | Require active `[p]` Task/claim, exact pointer, one DoD, no visible REF; render `[x]`, one full REF, and closure evidence. |
| `wontfix` | Require active `[p]` Task/claim and no REF; render `[w]`, full disposition REF, and nonempty Reason. |
| `parent-aggregation` | Require `[p]` parent, one DoD, exact complete same-Feature direct-child set, terminal markers, block digests, and visible REFs; append evidence without closing parent. |
| `ref-injection` | Require terminal `[x]`/`[w]`; insert when no visible REF exists or replace exactly one expected old REF and append correction history. |
| `claim-handoff` | Require active exact owner and explicit owner-release token; plan exact TODO pointer replacement, destination claim, source archive, and source deletion. |
| `claim-finalization` | Require terminal Task with one visible REF and exact active claim/pointer; plan pointer finalization, exact archive, and exact claim deletion. |
| `append-correction` | Append one unique correction ID to the exact Task or active claim; never rewrite prior history. |

Multi-file/create/delete plans are fully rendered and reviewed, but publication remains `0038-05.02` work.

## Candidate contract

`write_candidate()` creates a new candidate directory containing:

```text
candidate.json
diff.patch
blobs/<sha256>.before
blobs/<sha256>.after
```

`legacy-task-editor-candidate@v1` embeds:

- exact operation raw and canonical contract digests;
- the complete canonical operation;
- subject identity;
- every change path/action/span/before/after digest and byte count;
- a complete planning read set;
- the exact intended-create absent-path set;
- content-addressed member paths;
- the diff digest/size;
- `standalone_allowed: false`.

Candidate validation closes every nested object and enforces cross-object semantics:

- each replace/delete before digest equals the same read-set entry;
- each create path appears in `absent_paths`, and that set equals all create paths;
- read and absent sets are disjoint;
- embedded backlog/claim contract preimages are present;
- member paths exactly match their content digests;
- before and after blobs match digest/size;
- the retained diff equals a fresh diff over verified blobs.

## Promotion preflight and semantic equivalence

`verify_candidate_for_promotion()`:

1. verifies exact candidate manifest bytes;
2. validates every nested candidate field;
3. reads candidate members component-by-component without symlinks;
4. verifies before/after blobs and recomputes the exact diff;
5. rechecks every declared current read-set path and intended-absent path;
6. decodes the embedded canonical operation;
7. rediscovers all current top-level claims;
8. reruns the pure planner against fresh authoritative sources;
9. byte-compares the fresh read set, absent set, changes, spans, blobs, and diff with the candidate.

This prevents an internally consistent but operation-inconsistent candidate, omitted claim preimage, omitted create precondition, or newly appearing active claim from receiving verified handoff status.

`promote_candidate()` returns `legacy-task-editor-result@v1` with:

- verdict `verified-coordinator-required`;
- exact operation ID/kind;
- all verified changes;
- candidate manifest path/digest;
- `preflight_verified: true`;
- verified diff, read set, and absent paths;
- `promotion.requested: true`, `performed: false`, `atomicity: coordinator-required`;
- finding `LTE-PROMOTE-COORDINATOR-REQUIRED`.

No authoritative bytes are changed.

## Stable rules

| Rule family | Examples |
|---|---|
| Operation | `LTE-OP-JSON`, `LTE-OP-SCHEMA`, `LTE-OP-UNKNOWN-FIELD`, `LTE-OP-UNSAFE-VALUE` |
| Path/input | `LTE-PATH-UNSAFE`, `LTE-INPUT-MISSING`, `LTE-INPUT-NONREGULAR`, `LTE-INPUT-CHANGED` |
| Preimage | `LTE-DOCUMENT-DRIFT`, `LTE-BLOCK-DRIFT`, `LTE-PROMOTE-DRIFT` |
| Structure | `LTE-FEATURE-NOT-UNIQUE`, `LTE-TASK-NOT-UNIQUE`, `LTE-TASK-BOUNDARY`, `LTE-SECTION-NOT-UNIQUE` |
| Lifecycle/REF | `LTE-STATE-TRANSITION`, `LTE-REF-AMBIGUOUS`, `LTE-WONTFIX-REASON` |
| Parent | `LTE-PARENT-CHILD-SET`, `LTE-PARENT-CHILD-NONTERMINAL` |
| Claim | `LTE-CLAIM-IDENTITY`, `LTE-CLAIM-POINTER`, `LTE-CLAIM-CONFLICT`, `LTE-CLAIM-FINALIZE-MISMATCH` |
| Candidate | `LTE-NOOP`, `LTE-UNRELATED-BYTES`, `LTE-CANDIDATE-POSTCONDITION`, `LTE-CANDIDATE-TAMPERED` |
| Publication | `LTE-PROMOTE-COORDINATOR-REQUIRED` |

## Historical fixtures and validation

`_src/tests/fixtures/legacy_task_editor/` binds minimal synthetic byte shapes to:

- `9e033f32` → `9c4795bb` → `cd6d8db1` neighboring-header corruption/repair;
- `723b485d` and `a1cbbbdc` stale pre-amend REF corrections;
- the `0036-05` wildcard claim-deletion envelope;
- structural duplicate and fenced-decoy Task text;
- current/legacy claim identity variants;
- parent/child aggregation;
- hidden REFs and fenced normative-section decoys.

The focused suite covers all nine operation plans, byte-exact prefix/suffix preservation, pending-discovery pickup, actor/claim ownership, role alias rejection, complete read/absent sets, coherent semantic candidate tampering, newly appearing claims, source drift, nested candidate/path/member/diff/blob tampering, mixed fence/comment syntax, Unicode line separators, CLI planning, structured coordinator handoff, and fail-closed legacy-helper retirement.

Run:

```sh
python3 -m py_compile _src/tools/legacy_task_editor.py _src/tools/task_bookkeeping_closure.py _src/tests/test_legacy_task_editor.py
python3 -m unittest discover -s _src/tests -p 'test_legacy_task_editor.py' -v
python3 _src/tools/automation_safety.py --root . \
  --path _src/tools/legacy_task_editor.py \
  --path _src/tools/task_bookkeeping_closure.py --json
```

## Deferred integration

`0038-05.02`, gated by `0038-02`, must:

- register a fixed editor-candidate action in `runner_transaction.py`;
- consume the complete verified candidate result above;
- recheck all preimages under its durable lock/journal immediately before publication;
- replace `render_task_closure()` rather than retain duplicate semantics;
- promote single- and multi-file changes with crash recovery;
- persist result/recovery evidence before final claim deletion;
- prove every failure boundary through injected tests.
