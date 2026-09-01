# Fail-closed legacy runner transactions

Status: legacy safety bridge. This tool does not replace Feature `0037`'s typed
queue and does not change the singleton-runner lifecycle defined in
`SANDBOX.md`.

## Atomic implementation check-ins

`_src/tools/runner_transaction.py` has one Task-closing profile:
`atomic-check-in-v1`. It produces **one** path-limited implementation commit.
That commit contains every declared substantive path, the terminal `TODO.md`
transition, and the finalised-but-retained claim. It never tries to contain its
own object ID and never follows the implementation check-in with a bookkeeping
commit.

The commit message must include the verbatim `User-Prompt-Provenance:` section
and exactly these terminal Git trailers:

```text
Task-ID: 0038-01
Base-Ref: 0123456789abcdef0123456789abcdef01234567
```

`Task-ID` must equal the manifest identity. `Base-Ref` must be full lowercase
40-hex, equal the manifest's pre-substantive `expected_base`, and be an ancestor
of the generated commit. The runner parses the actual created commit message,
not merely manifest text. It rejects absent, duplicate, malformed, mismatched,
stale, and non-ancestor trailers.

The old `close-task-v1` wire value and every `bookkeeping` manifest member are
rejected. Old two-commit journals remain readable for recovery only; they do
not authorize a new two-commit implementation lifecycle.

## Safety properties

- An exact Task, request, owner token, claim, base, authority selector, branch,
  manifest digest, contract digest, and file scope are bound before mutation.
- Fixed reviewed action IDs are run in a detached candidate worktree. Manifests
  never contain arbitrary shell commands or executable paths.
- Structured reports with failures, generator input mutation, validator tree
  mutation, undeclared candidate changes, symlinks, runtime-log aliases, and
  index overlap all fail closed.
- Generated outputs, terminal `TODO.md`, and finalised claim are atomically
  promoted with a drift-safe rollback journal before one `git update-ref` CAS.
  Existing unrelated index entries are preserved.
- The post-CAS verifier checks the branch tip, actual trailers, terminal marker,
  committed claim state, working paths, and temporary-index tree before it
  records success.
- The claim is not archived or deleted. Its `state:` changes from `[p]` to the
  requested `[x]` or `[w]` and it records that it is finalised in the atomic
  check-in. This is durable provenance, not a live write lease.

## Required claim binding

In addition to ordinary claim content, the active claim has one-line binding
fields similar to:

```text
task_id: 0038-01
request_id: example-0038-01-20260816-a1b2c3
owner_token: agent:example:0038-01:example-0038-01-20260816-a1b2c3
base_commit: 0123456789abcdef0123456789abcdef01234567
state: [p]
transaction_profile: atomic-check-in-v1
transaction_manifest: output/requests/0038-01/example-0038-01-20260816-a1b2c3.json
transaction_completion_json: {"closure_text":"Implemented and verified the declared change.","terminal_marker":"[x]","todo_path":"TODO.md"}
```

The runner also binds canonical action, authority, read-path, write-path, and
commit-message JSON fields. `transaction_write_paths_json` includes the
substantive paths, `TODO.md`, and the exact claim. Any material change after
claim creation fails preflight.

## Atomic manifest example

```json
{
  "schema": "legacy-runner-transaction@v1",
  "profile": "atomic-check-in-v1",
  "identity": {
    "task_id": "0038-01",
    "request_id": "example-0038-01-20260816-a1b2c3",
    "owner_token": "agent:example:0038-01:example-0038-01-20260816-a1b2c3",
    "claim_path": "TODO-example-0038-01-example-0038-01-20260816-a1b2c3.md",
    "manifest_path": "output/requests/0038-01/example-0038-01-20260816-a1b2c3.json",
    "expected_base": "0123456789abcdef0123456789abcdef01234567"
  },
  "authority": {
    "selector_path": "agent-workflow.json",
    "authority_epoch": "legacy-writable",
    "authority_profile": "legacy-lists",
    "write_phase": "legacy-writable",
    "runner_protocol": "runner-request@v1"
  },
  "scope": {
    "read_paths": ["_src/generate.py", "_src/validate.py"],
    "input_paths": ["_src/sources/pages/example.json"],
    "output_paths": ["example.html"],
    "substantive_paths": ["_src/sources/pages/example.json", "example.html"]
  },
  "actions": [
    {"id": "generate-site", "timeout_seconds": 900, "reports": []},
    {"id": "validate-project", "timeout_seconds": 900, "reports": []}
  ],
  "commit": {
    "message": "feat(0038-01): implement the requested change\n\nUser-Prompt-Provenance:\n<verbatim user prompt>\n\nTask-ID: 0038-01\nBase-Ref: 0123456789abcdef0123456789abcdef01234567"
  },
  "completion": {
    "todo_path": "TODO.md",
    "terminal_marker": "[x]",
    "closure_text": "Implemented and verified the declared change."
  }
}
```

The Task must be `[p]` in the expected-base `TODO.md`; the current `TODO.md`
and claim must still match that base at preflight. `closure_text` is exactly one
line. `atomic-check-in-v1` requires generate followed by validation. A terminal
non-implementation disposition uses `terminal_marker: "[w]"` and still carries
substantive disposition evidence and both trailers.

## Non-closing verification profile

`verify-and-commit-v1` is deliberately non-closing. It performs a scoped,
path-limited substantive commit after declared validation and requires
provenance, but it cannot include `completion` or `bookkeeping`. On success it
leaves both `TODO.md` and the active `[p]` claim unchanged. Its result and
journal explicitly record that claim finalisation is not required.

This is the authoritative reconciliation of `0038-25`: a validation-only
profile may succeed only as a named non-closing action; it cannot silently
remove a claim or represent Task completion. Task closure must use
`atomic-check-in-v1`.

## Execution and recovery

Generate a thin envelope with:

```text
python3 _src/tools/runner_transaction.py render-envelope \
  --manifest output/requests/0038-01/example-0038-01-20260816-a1b2c3.json
```

It contains only the canonical `exec python3 _src/tools/runner_transaction.py
run --manifest …` call. `lint-envelope` rejects extra commands, direct Git,
deletions, inline Python, and direct generator/validator invocation.

Every boundary is recorded below:

```text
output/logs/<task-id>/<request-id>/
```

including action stdout/stderr, retained reports, promotion backups/journal,
prepared result, transaction journal, and final result. A failed pre-CAS action
rolls back only paths that still equal the promoted state; newer edits are never
overwritten. CAS loss also rolls back the transaction's promoted paths while
leaving the competing branch winner untouched.

After a hard kill following atomic CAS, `recover` validates the canonical branch
tip, actual trailers, ancestor relation, terminal `TODO.md`, and retained claim.
A valid tree is reported complete without mutation. `finalize-claim` rejects
these modern journals because archival would destroy the committed provenance.
It remains available only for an old journal that lacks the explicit
`claim_finalization_required: false` marker and already proves legacy
publication.

```text
python3 _src/tools/runner_transaction.py recover --root <repo> --request-id <request-id>
python3 _src/tools/runner_transaction.py doctor --root <repo>
```

## Fixed actions and validation

| Action ID | Phase | Registry command |
|---|---|---|
| `generate-site` | generate | current Python + `_src/generate.py` |
| `validate-project` | validate | current Python + `_src/validate.py` |
| `test-runner-transaction` | validate | current Python + runner test module |

Run the hermetic suite with:

```text
PYTHONDONTWRITEBYTECODE=1 python3 _src/tools/test_runner_transaction.py
```

It covers atomic success, trailer rejection, marker/tree mismatch, action and
structured-report failures, rollback/CAS races, hard-kill recovery, retained
claims, index isolation, path/symlink protections, legacy recovery, and
non-closing `verify-and-commit-v1` claim preservation.
