# Legacy write-scope collision planning

`_src/tools/legacy_scope_planner.py` is the read-only collision planner for the legacy `TODO.md`/claim period. It answers one question before mutation: can the proposed participants operate in parallel, must they be serialized, or is the plan unsafe or incomplete?

The planner does not execute actions, alter claims, inspect or consume root `run.sh`, stage files, or mutate Git. It composes existing authorities instead of maintaining another dependency graph:

- `_src/tools/legacy_task_doctor.py::scan_repository()` supplies normalized active legacy claims and claim findings.
- `docs/pipeline/issue-derived-artifacts-v1.json` supplies the authoritative `issue-regeneration-dag@v1` source/output ownership graph.
- The request supplies exact typed Git and runner snapshots plus exact legacy generator, i18n, and publication output scopes that are not yet represented by that DAG.

## Invocation

```sh
python3 _src/tools/legacy_scope_planner.py \
  --root . \
  --request /path/to/request.json \
  --json
```

Without `--json`, the command prints at most ten summary lines. Exit status is:

| Exit | Meaning |
|---:|---|
| `0` | `PARALLEL` or explicitly ordered `SERIALIZE` plan |
| `1` | `BLOCK`; at least one write/read, write/write, snapshot, derived-output, sole-writer, or promotion-group collision exists |
| `2` | `INCOMPLETE`; the request, DAG, or active-claim evidence is malformed or insufficient |

`BLOCK` and `INCOMPLETE` both forbid mutation. A reported serialization order is advisory evidence for preparing a later non-overlapping request; it does not authorize the blocked request to run.

## Closed request contract

The top-level schema is `legacy-scope-planner-request@v1`:

```json
{
  "schema": "legacy-scope-planner-request@v1",
  "participants": [
    {
      "id": "task-a",
      "actor": {"id": "actor:task-a"},
      "reads": [],
      "writes": [{"path": "docs/example.md", "kind": "file"}],
      "sources": [{"path": "issues/0038/0038-06/index.md", "kind": "file"}],
      "actions": [],
      "after": []
    }
  ],
  "snapshots": {
    "git": {
      "head": "0123456789abcdef0123456789abcdef01234567",
      "index_tree": "89abcdef0123456789abcdef0123456789abcdef",
      "worktree_digest": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
      "dirty": []
    },
    "runner": {
      "snapshot_id": "runner-snapshot:request-42",
      "reads": [],
      "writes": []
    }
  }
}
```

Unknown and duplicate fields are rejected at every level. IDs are stable bounded strings. Every path is a normalized repository-relative POSIX path. Write scopes cannot contain globs, escape through `..`, address `.git`, or address root `run.sh`.

### Actors and active claims

A participant not representing an existing claim uses only `actor.id`. A participant representing an active claim supplies both exact fields:

```json
{
  "id": "0038-06",
  "actor": {
    "id": "agent:zed:0038-06:request-id",
    "owner_token": "agent:zed:0038-06:request-id",
    "claim_path": "TODO-zed-0038-06-request-id.md"
  }
}
```

The actor ID and owner token must equal the doctor-normalized claim owner, and the participant's exact write paths must equal the claim's normalized scope. Every other active claim is added as a foreign participant. Missing, invalid, mismatched, or non-resolvable foreign scope makes the result `INCOMPLETE`; an empty or malformed claim is never treated as disjoint.

### Scope kinds

A scope is an exact object:

```json
{"path": "docs/pipeline", "kind": "directory"}
```

`file` scopes overlap only the same path. A `directory` overlaps the same directory and every path below its segment boundary. For example, `docs/pipeline` overlaps `docs/pipeline/tools.md`, but not `docs/pipeline-old/tools.md`.

- `reads`: immutable inputs that must not overlap another participant's write.
- `writes`: direct authoritative or candidate writes.
- `sources`: exact files being changed that must be expanded through the authoritative issue-regeneration DAG. An unmatched source makes the plan `INCOMPLETE`.

Every `writes` scope that intersects a non-derived DAG input is expanded automatically, including file and directory writes imported from foreign active claims. Directory/glob intersection is segment-safe: `issues` and `issues/nested` intersect `issues/**/*.md`, while `issues-archive` does not. Callers cannot bypass derived-scope analysis by omitting a matching file from `sources`; duplicate `writes`/`sources` expansion is collapsed.

### Typed legacy action outputs

The issue DAG does not yet describe every deployed whole-site generator, translation, report, or publication output. Those outputs must be declared by the typed action/request producer; the planner does not infer them from prose or source code.

```json
{
  "id": "render-process-locales",
  "type": "i18n",
  "outputs": [
    {"path": "process.html", "kind": "file"},
    {"path": "en/process.html", "kind": "file"}
  ],
  "prefixes": [
    {"path": "output/build-reports", "kind": "directory"}
  ],
  "promotion_group": "legacy-site"
}
```

Supported types are `generator`, `i18n`, and `publication`. `outputs` are exact file or directory scopes. `prefixes` are directory scopes for run-specific output families. A promotion group means its output set is one atomic publication boundary; two participants cannot split the same group.

### Git and runner snapshots

The request carries exact snapshots captured by the caller:

- `snapshots.git.head`: full lowercase commit OID.
- `snapshots.git.index_tree`: full lowercase index-tree OID.
- `snapshots.git.worktree_digest`: SHA-256 identity of the captured worktree-path snapshot.
- `snapshots.git.dirty`: staged, unstaged, and untracked paths bound to that identity.
- `snapshots.runner.snapshot_id`: stable identity of the captured active-runner state.
- `snapshots.runner.reads`: paths read by another active runner request.
- `snapshots.runner.writes`: paths written by another active runner request.

The planner does not run Git or query a mutable runner slot itself. This keeps planning deterministic and makes snapshot capture the caller's explicit responsibility. A proposed read or write that overlaps a dirty or runner scope blocks. The caller must recapture/recheck the same identities immediately before mutation; a retained plan is not a lease and must not authorize work after HEAD, index, worktree, claims, or runner state changes.

### Explicit ordering

`after` contains participant IDs that must precede the participant. Acyclic ordering without a collision yields `SERIALIZE`. Cycles and unknown IDs are rejected. Ordering does not waive a collision: an overlapping request remains `BLOCK`, with a safe serialization order supplied only as a preparation aid.

## Derived-scope expansion

For every explicit `sources` path and every file or directory in `writes` that segment-safely intersects a non-derived DAG input, the planner:

1. matches canonical/configuration inputs in `issue-regeneration-dag@v1`;
2. selects downstream stages through the DAG's declared `depends_on` edges;
3. adds each selected stage's exact outputs;
4. retains source → stage → output explanation chains;
5. carries sole-writer and promotion-group ownership into collision classification.

Before expansion, the planner rejects duplicate stage IDs, unknown or cyclic dependencies, duplicate output writers, mismatched `sole_writer`, unresolved derived inputs, and derived producers not present in the consumer's dependency ancestry. The result binds the exact DAG path and SHA-256 digest; the planner never writes a second graph.

## Collision classes

| Class | Meaning |
|---|---|
| `exact-direct` | Two direct write scopes name the same path |
| `ancestor-directory` | A directory scope contains another participant's path |
| `write-vs-read` | A write overlaps another participant's immutable read |
| `derived-output` | Two source changes expand to the same DAG output |
| `source-vs-derived` | A source-expanded output overlaps a direct/action scope |
| `sole-writer` | Multiple participants attempt one DAG-owned output |
| `promotion-group` | Participants split one atomic promotion group |
| `git-dirty` | Proposed access overlaps the bound dirty-tree snapshot |
| `runner-snapshot` | Proposed access overlaps another runner's read/write snapshot |
| `unknown-incomplete-scope` | Active claim or contract evidence cannot prove safety |

Each collision names participants, exact paths, producer chains, and a deterministic explanation.

## Historical `0036-05` / `0036-06` fixture

The two historical Tasks had disjoint committed source paths but overlapping execution outputs. One broad all-locale generation and one targeted process-page translation generation both owned `process.html`, localized `*/process.html` outputs, and a shared publication boundary. Direct source comparison therefore looked safe while execution overlapped.

The retained fixture models both typed action output sets. The expected result is `BLOCK`, with exact, directory-ancestor, and promotion-group evidence. Companion fixtures prove:

- overlapping locale subsets block;
- different page and locale outputs can run in parallel;
- issue source changes collide transitively with page-model and localized issue outputs;
- malformed foreign claims, dirty Git paths, and active runner scopes fail closed.

## Result contract

The result schema is `legacy-scope-planner-result@v1`. It contains:

- `verdict`: `PARALLEL`, `SERIALIZE`, `BLOCK`, or `INCOMPLETE`;
- `plan.strategy`, topological `ordered_groups`, and bounded `safe_serialization_order`;
- SHA-256 bindings for the request, DAG, and complete canonical doctor report, plus the exact Git/runner snapshot identities;
- participant and collision counts;
- deterministic collision records and explanations;
- a bounded human summary.

Repeated planning over identical request, DAG, complete doctor report, and snapshots is byte-identical after canonical JSON serialization. Normal execution always loads the DAG from the named repository path and calls the doctor directly. The importable API permits alternate DAG/doctor values only under an explicit injected-test mode; such results are labeled `injected` and carry no authoritative DAG-path claim.

## Validation

```sh
python3 -m py_compile \
  _src/tools/legacy_scope_planner.py \
  _src/tests/test_legacy_scope_planner.py

python3 -m unittest discover \
  -s _src/tests \
  -p 'test_legacy_scope_planner.py' \
  -v

python3 -m unittest discover \
  -s _src/tests \
  -p 'test_legacy_task_doctor.py'

python3 _src/tools/automation_safety.py \
  --root . \
  --path _src/tools/legacy_scope_planner.py \
  --path _src/tools/legacy_task_doctor.py \
  --json
```
