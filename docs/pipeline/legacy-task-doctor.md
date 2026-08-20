# Legacy Task/Claim/Bootstrap Doctor

Status: implemented legacy safety adapter for Feature `0038`, Task `0038-04`.

## Purpose and authority boundary

`_src/tools/legacy_task_doctor.py` reads the pre-cutover collaboration database and reports structural drift without repairing it. Its authoritative inputs are the current worktree bytes of:

- `TODO.md`;
- `DONE.md`;
- `agent-workflow.json`;
- sorted top-level `TODO-*.md` claim/coordination files;
- `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, the selected instruction bundle, and `SENTINEL.md` when present.

The tool is limited to the `legacy-lists` era. It neither creates a second issue store nor becomes the permanent bootstrap authority. Task `0037-42` owns the future `agent-doctor` implementation; Task `0038-16` maps or retires this legacy adapter during queue/issue-store handoff.

### Deliberate legacy limitation: one authorized non-Task coordination record

`AGENTS.md` authorizes a temporary `TODO-<agent-id>.md` coordination record for
a user-directed activity that is not an existing Task, provided it does not
falsely mark an unrelated Task `[p]`. The legacy doctor nevertheless models all
top-level `TODO-*.md` records as Task claims. The exact known false positive is:

- path: `TODO-claude-re-intake-20260818T003223Z-845170c0e4da.md`;
- immutable token:
  `agent:claude:re-intake:20260818T003223Z-845170c0e4da`;
- deliberate shape: no `task_id`, because Feature `0040` did not yet exist and
  the record coordinated the user-directed requirements-intake activity rather
  than claiming a Task;
- expected finding: `LTD-CLAIM-IDENTITY-MISMATCH`, because the token component
  `re-intake` is not a canonical Task ID.

The token MUST remain byte-for-byte unchanged: retrofitting a Task ID would
break the stronger immutable-owner-token rule and falsify the historical
coordination scope. This is a documented limitation of the retiring legacy
adapter, not a general exception for malformed Task claims. There is no
filename-, token-, or rule-wide suppression; all Task claims remain subject to
the normal checks, and the known finding remains visible. No code, tool, or
schema change is made for this single historical record.

The doctor does **not**:

- edit, rename, create, or delete repository files;
- stage or commit work;
- acquire, release, take over, or finalize a claim;
- execute, inspect, create, remove, restore, or consume root `run.sh`;
- inspect transaction locks, recovery journals, or backups owned by `0038-02`;
- calculate derived write-scope collisions owned by `0038-06`;
- infer approval, authority, ownership, or human decisions from display names or filenames.

## Invocation and exit codes

```sh
python3 _src/tools/legacy_task_doctor.py
python3 _src/tools/legacy_task_doctor.py --json
python3 _src/tools/legacy_task_doctor.py --root /path/to/worktree --json
```

There is intentionally no `--fix`, `--apply`, output-file, recovery, finalization, or claim-selection option.

| Exit | Verdict | Meaning |
|---:|---|---|
| `0` | `CLEAN` | The complete stable input set produced zero findings. |
| `1` | `FINDINGS` | The complete stable input set produced one or more findings. |
| `2` | `INCOMPLETE` | A required input was missing/unsafe/changing or the bounded Git reachability probe failed. No reconciliation plan from a mixed snapshot is emitted. |

Without `--json`, stdout is a summary of at most ten lines. With `--json`, stdout is exactly one canonical UTF-8 JSON object plus a final LF; human text is retained only in its `summary` array.

## Read-only and consistency model

1. The adapter accepts only regular, non-symlink UTF-8 inputs under the supplied root and bounds each input at 12 MiB.
2. It discovers claims only as sorted top-level names matching `TODO-*.md`; it never recurses through logs, output, evidence, or archives.
3. Parsing and analysis operate on immutable bytes already read into memory.
4. Authoritative full commit IDs and exact full claim bases are checked before and after analysis through the same fixed read-only command:

   ```text
   git --no-optional-locks rev-list --all
   ```

   The process uses an argument vector, no shell, `GIT_OPTIONAL_LOCKS=0`, `LC_ALL=C`, no stdin, and a 15-second timeout.
5. Before reporting, every input digest, the exact claim-name set, and the reachable local-ref commit set are read again. Any change produces `INCOMPLETE` and suppresses all plans.
6. Error details are normalized without absolute filesystem paths or embedded newlines. Reports contain no timestamp, duration, PID, absolute root, or filesystem-enumeration order.

The focused tests snapshot every fixture path, byte, mode, type, and symlink target around every library scan and around representative clean and finding CLI scans.

## Normalized model

The report schema is `legacy-task-doctor-report@v1`. It contains:

- deterministic input path/size/SHA-256 records;
- selected bootstrap fields;
- Feature, Task, ID-less historical-entry, claim, REF, and prerequisite inventories;
- source paths and one-based line spans;
- claim identity, exact scope paths, and resume-state presence;
- REF visibility (`visible` or HTML-comment `hidden`) and role (`authoritative-task`, `authoritative-feature`, or `narrative`);
- prerequisite edges with their declared dependent and prerequisite;
- stable findings and non-destructive exact-path reconciliation plans.

Object keys are sorted. Features and Tasks retain document order (`TODO.md` before `DONE.md`); claims and inputs sort by repository-relative path; REFs sort by path/line/column/value; findings sort by severity, rule, path, line, subject, and evidence digest.

Every finding contains:

```json
{
  "rule": "LTD-CLAIM-STATE-DIVERGED",
  "severity": "error",
  "category": "claim",
  "path": "TODO-example-1000-01-claim.md",
  "line": 10,
  "subject": "1000-01",
  "message": "claim state [p] disagrees with authoritative Task state [ ]",
  "evidence": "state: [p]",
  "evidence_sha256": "...",
  "related_paths": ["TODO.md"]
}
```

Every plan identifies the source rule, exact path/line/subject, target paths, expected source-document digest, action class, and required actor. `automatic` and `destructive` are always `false`. Foreign-claim findings require the claim owner or an authorized maintainer; a plan never instructs another agent to appropriate or delete the claim.

## Backlog and marker rules

The valid legacy markers are exactly `[ ]`, `[u]`, `[p]`, `[?]`, `[w]`, and `[x]`. `[x]` and `[w]` satisfy prerequisite terminality. `ARCHIVED — NOT ACCEPTED` remains historical and never satisfies Feature completion.

| Rule | Meaning |
|---|---|
| `LTD-MARKER-UNDEFINED` | A Task, legacy entry, or claim uses an undefined marker such as `[d]`. |
| `LTD-ID-DUPLICATE` | A Feature or Task/Subtask ID occurs more than once across the authoritative lists. |
| `LTD-TASK-HEADER-MALFORMED` | A Task-like checklist entry has a malformed canonical Task ID/header instead of disappearing into legacy text. |
| `LTD-FEATURE-HEADER-MALFORMED` | A current Feature header lacks its canonical four-digit ID. |
| `LTD-PARENT-CLOSURE-ELIGIBLE` | A `[ ]` parent Task with no active claim has terminal direct children and terminal explicit start gates; package work should be claimed rather than skipped. |
| `LTD-FEATURE-CLOSURE-ELIGIBLE` | An open TODO Feature has terminal direct Tasks and terminal Feature gates. |

Eligible-package findings are advisory start signals, not automatic closure: the owning agent must still perform the parent's or Feature's own consistency, aggregation, validation, evidence, and bookkeeping criteria.

## REF rules

A visible Task-header `REF:` or exact indented `- REF:` bullet is authoritative for a Task. A `Completed: ... REF:` line is authoritative for a completed Feature. Other references in closure/history prose are normalized as narrative evidence, not silently promoted into closure fields.

Authoritative refs must be full lowercase 40-hex commit IDs reachable from a local ref. Short hashes, `verified`, `pending commit`, `local-*`, empty values, and HTML-comment refs are retained and diagnosed rather than credited.

| Rule | Meaning |
|---|---|
| `LTD-REF-HIDDEN` | A REF is inside an HTML comment. |
| `LTD-REF-MALFORMED` | A visible authoritative value is not a full lowercase commit ID. |
| `LTD-REF-PLACEHOLDER` | A visible authoritative value is empty, `verified`, `pending commit`, or `local-*`. |
| `LTD-REF-MISSING` | A terminal non-archive Task or completed Feature lacks a visible authoritative REF. |
| `LTD-REF-DUPLICATE` | One item has more than one visible authoritative REF occurrence. |
| `LTD-REF-UNREACHABLE` | A full authoritative commit is absent from `git rev-list --all`. |
| `LTD-REF-STATE-DIVERGED` | A nonterminal Task carries an authoritative closure REF. |

The doctor intentionally gives archived-not-accepted placeholder labels informational severity: they remain non-Git history and receive no completion evidence credit.

## Claim rules

Identity fields are read only from the top-level preamble or the `## Claim identity` section; later runner-history fields cannot silently replace the immutable claim identity. Canonical fields use plain `key: value` lines. Legacy bullet/backtick forms remain parseable so the historical runner-format failure is visible.

Required Task-claim identity fields are `task_id`, `request_id`, `owner_token`, `base_commit`, `capability_class`, and `state`. An immutable token has the form `agent:<agent>:<task-id>:<claim-id>` and the filename must equal `TODO-<agent>-<task-id>-<claim-id>.md` exactly. The declared Task must exist in `TODO.md` or `DONE.md`. A full base must be reachable; `pending-discovery` is the one explicit pre-discovery exception. Active claims require only safe in-root, non-glob exact paths in a write-scope section and a non-placeholder `## Next step` that is the final section.

When a machine field named `write_scope` or `write_scopes` is present, its comma-separated or JSON-array paths must equal the path-bearing Intended-write-scope section. The field is optional in legacy claims, but disagreement is not ignored.

| Rule | Meaning |
|---|---|
| `LTD-CLAIM-FIELDS-MISSING` | Required identity fields are absent. |
| `LTD-CLAIM-FIELD-DUPLICATE` | A canonical identity field occurs more than once in the identity region. |
| `LTD-CLAIM-FIELD-NONCANONICAL` | A required field uses legacy bullet/backtick syntax. |
| `LTD-CLAIM-IDENTITY-MISMATCH` | Task/request/token/filename or capability components disagree. |
| `LTD-CLAIM-BASE-ABBREVIATED` | A base is a short hexadecimal abbreviation. |
| `LTD-CLAIM-BASE-INVALID` | A base is neither `pending-discovery` nor a full commit. |
| `LTD-CLAIM-BASE-UNREACHABLE` | A full base is not reachable from a local ref. |
| `LTD-CLAIM-STATE-DIVERGED` | Claim state and authoritative Task marker disagree. |
| `LTD-CLAIM-TASK-MISSING` | A claim declares a Task absent from both authoritative lists. |
| `LTD-CLAIM-TERMINAL-RETAINED` | A claim remains after its Task reached `[x]` or `[w]`. |
| `LTD-CLAIM-SCOPE-MISSING` | An active claim has no exact path-bearing scope. |
| `LTD-CLAIM-SCOPE-MISMATCH` | Optional machine scope and human scope section disagree. |
| `LTD-CLAIM-SCOPE-INVALID` | A scope escapes the root, uses a glob, names `.git`, or treats root `run.sh` as Task write scope. |
| `LTD-CLAIM-NEXT-STEP-MISSING` | An active claim has no non-placeholder final resume action. |
| `LTD-TASK-CLAIM-MISSING` | A `[p]` Task has no exact active claim. |
| `LTD-TASK-CLAIM-DUPLICATE` | More than one `[p]` claim resolves to the same Task. |
| `LTD-TASK-CLAIM-POINTER-MISMATCH` | The Task's claim path/token/base note disagrees with the exact claim. |

No age-based staleness is inferred because current policy defines no claim TTL.

## Prerequisite rules

The parser validates complete comma-separated Task and Feature declarations before retaining each `dependent:prerequisite` pair. It rejects a malformed suffix even when an earlier pair parsed, and checks containing-item left side, endpoint existence, duplicates, self-edges, terminality consistency, and deterministic cycles. It never drops an unknown endpoint.

| Rule | Meaning |
|---|---|
| `LTD-PREREQ-MALFORMED` | A Task or Feature `PREREQ:` list is absent, partial, or has malformed trailing content. |
| `LTD-PREREQ-LHS` | A relation's left side differs from its containing Task or Feature. |
| `LTD-PREREQ-ENDPOINT-MISSING` | A dependent or prerequisite ID is absent. |
| `LTD-PREREQ-DUPLICATE` | The same explicit edge occurs more than once. |
| `LTD-PREREQ-SELF` | An item depends on itself. |
| `LTD-PREREQ-CYCLE` | The explicit graph contains a canonicalized cycle. |
| `LTD-TERMINAL-UNSATISFIED-PREREQ` | A terminal item still has a nonterminal explicit prerequisite. |

The doctor detects syntactic graph errors. General semantic-deadlock repair remains an agent/backlog-authority responsibility because arbitrary prose intent cannot be inferred safely.

## Bootstrap and instruction rules

`agent-workflow.json` is decoded with duplicate-key rejection and checked against the closed `agent-workflow-bootstrap@v1` field set, enums, lexical forms, profile/epoch/phase combinations, and selected bundle path. Local instruction links must remain in-root and resolve without symlinks to the expected regular Markdown file (or declared directory target). The targeted sentinel contradiction requires a positive write/create directive and has aligned-policy negative controls.

| Rule | Meaning |
|---|---|
| `LTD-BOOT-INVALID` | JSON shape, required value, enum, version, digest syntax, or bundle path is invalid. |
| `LTD-BOOT-UNKNOWN-FIELD` | Selector contains an unknown field. |
| `LTD-BOOT-CROSS-FIELD` | Profile, epoch, and write phase disagree. |
| `LTD-BOOT-DIGEST-PLACEHOLDER` | Digest is an obvious repeated-character placeholder. |
| `LTD-BOOT-BUNDLE-MISSING` | Selected valid bundle path does not exist. |
| `LTD-BOOT-COMMAND-MISSING` | Selected bundle names an unavailable exact recovery command. |
| `LTD-INSTRUCTION-LINK-MISSING` | A local instruction reference does not resolve. |
| `LTD-INSTRUCTION-NEAR-NAME` | Missing `SENTINTEL.md` has near-name `SENTINEL.md`, making policy identity ambiguous. |
| `LTD-POLICY-CONTRADICTION` | `SENTINEL.md` directs escalation through `run.sh` while `SANDBOX.md` forbids that channel. |

The selector's digest syntax and obvious placeholder are checkable, but the current contract does not unambiguously define its digest preimage. The doctor therefore does not invent a semantic digest algorithm; full policy-digest verification remains with `0037-42`.

## Input and execution rules

| Rule | Meaning |
|---|---|
| `LTD-INPUT-MISSING` | A required source cannot be found/read. |
| `LTD-INPUT-NONREGULAR` | An input is unsafe, nonregular, symlinked, too large, or not UTF-8. |
| `LTD-INPUT-CHANGED` | Input names or bytes changed during the scan. |
| `LTD-GIT-PROBE` | The bounded read-only reachability command failed or returned malformed output. |

These rules produce `INCOMPLETE`, and stale reconciliation plans are suppressed.

## Fixtures and validation

Hermetic cases live under `_src/tests/fixtures/legacy_task_doctor/`:

- `clean` proves a canonical Task/claim/bootstrap produces no findings;
- `aligned-policy` proves two intentional sentinel files with aligned non-runner policy do not false-positive;
- `marker-and-refs` freezes `[d]`, inline/multiline hidden, verified/pending/local, short, duplicate, unreachable, and premature REFs;
- `claim-drift` freezes orphan/state/terminal-retention/exact immutable filename/base/unsafe scope/final-next-step/Task-pointer failures;
- `prerequisites-and-parent` freezes Task and Feature missing/wrong/partial/malformed/cyclic edges, terminality drift, and safe eligible parent closure;
- `bootstrap-policy` freezes escaping links and the current `SENTINTEL.md`/`SENTINEL.md`/`run.sh`/unavailable-command contradictions.

Run focused validation with:

```sh
python3 -m py_compile _src/tools/legacy_task_doctor.py _src/tests/test_legacy_task_doctor.py
python3 -m unittest discover -s _src/tests -p 'test_legacy_task_doctor.py' -v
python3 _src/tools/automation_safety.py --root . --path _src/tools/legacy_task_doctor.py --json
python3 _src/tools/legacy_task_doctor.py --root . --json
```

The live repository is expected to return `FINDINGS` until later owner/authority Tasks reconcile the diagnosed legacy history. A nonzero live diagnostic verdict is therefore evidence of detected drift, not failure of the doctor itself.

`logs/legacy-task-doctor/0038-04-current-determinism.json` is the compact tracked evidence manifest for the Task's current-worktree check. It binds the tool digest, canonical command, aggregate input-manifest digest, two equal full-report byte counts/SHA-256 digests, normalized finding/plan digests, rule counts, inventory, bounded summary, and zero automatic/destructive/takeover/runner-token plans. The full reports remain task-scoped ignored validation logs rather than a large tracked copy of active foreign coordination data.
