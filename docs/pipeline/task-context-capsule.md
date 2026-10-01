# Task context/resume capsule

`_src/tools/task_context_capsule.py` builds one bounded, read-only "resume
capsule" for a single Task: enough machine JSON plus a short human summary to
pick the Task back up after a context/tool-budget boundary, a premature
completion report, or a plain handoff — without repeating completed work,
changing owner, or dropping a blocker.

It is Task `0038-07` of Feature `0038`. It never mutates a file, claim, ref,
or the runner slot, and performs no Git/subprocess call and no network
access.

## Composition, not reimplementation

The capsule generator reads three existing authorities instead of reparsing
`TODO.md`/claims or re-deriving scope/attempt state itself:

- **`legacy_task_doctor.py::scan_repository()`** (Task `0038-04`) supplies the
  normalized Task/Feature/claim/prerequisite model, the authority-selector
  digest block, and structural findings. The capsule filters this report to
  the one Task/claim it was asked about; it never reparses `TODO.md`,
  `DONE.md`, or claim files for identity data.
- **`legacy_scope_planner.py`** (Task `0038-06`) supplies the authoritative
  `issue-regeneration-dag@v1` loader/validator and its graph-walking helpers
  (`_source_stages`/`_descendants`/`_producer_chain`, `_infer_claim_scope`).
  The capsule reuses exactly these to expand a claim's **explicit** write
  scope into its **derived** (DAG-downstream) scope. It deliberately does
  not fabricate a full `legacy_scope_planner.plan_request` participant/
  Git/runner snapshot: this tool answers "what would be downstream of my own
  declared scope", not "do I collide with another active claim", which
  remains the collision planner's job.
- **`runner_transaction.py`** (Task `0038-10`) supplies the immutable
  per-attempt `result.json` and the atomic `current.json` pointer under
  `output/logs/<task_id>/`. The capsule only *reads* those files — it never
  writes, archives, or otherwise mutates them — to report the "pending
  request/result" and "completed phases" fields from the same evidence the
  runner itself persisted, and to detect a tampered/inconsistent result via
  the pointer's bound SHA-256.

## Invocation

```sh
python3 _src/tools/task_context_capsule.py --root . --task-id 0038-07 --json
python3 _src/tools/task_context_capsule.py --root . --task-id 0038-07
python3 _src/tools/task_context_capsule.py --root . --task-id 0038-07 \
  --claim-path TODO-example-0038-07-abc123.md
```

Without `--json`, stdout is a bounded summary of at most ten lines. With
`--json`, stdout is exactly one compact canonical UTF-8 JSON object (sorted
keys, no extraneous whitespace) plus a final LF — compact rather than
indented, because this tool's whole purpose is fitting a byte budget.

| Exit | Verdict | Meaning |
|---:|---|---|
| `0` | `OK` | Capsule built; a Task/claim/pending-attempt snapshot is present (a Task may still have no active claim). |
| `1` | `TASK-NOT-FOUND` | No Task with the given ID exists in `TODO.md` or `DONE.md`. |
| `2` | `INCOMPLETE` | The underlying `legacy_task_doctor` scan is incomplete (unstable/missing inputs), or `--task-id` is not a well-formed identifier. |

`--claim-path` disambiguates which active claim to use when more than one
`[p]` claim resolves to the same Task (already flagged by the doctor as
`LTD-TASK-CLAIM-DUPLICATE`); without it, the capsule picks the
lexicographically first claim path deterministically and sets
`claim_ambiguous: true`.

## Capsule schema

The schema is `task-context-capsule@v1`. Top-level fields:

| Field | Source | Meaning |
|---|---|---|
| `task` | doctor | ID, marker, feature ID, title, path/line. |
| `feature` | doctor | ID/title/path of the owning Feature. |
| `prerequisites` | doctor | Direct prerequisite IDs with their terminal (`[x]`/`[w]`, or Feature in `DONE.md`) state. |
| `claim` | doctor | Exact active claim's path, owner token, request ID, base commit, capability class, state, resume-note presence. |
| `claim_ambiguous` | doctor | `true` when more than one active claim resolves to the Task. |
| `authority` | doctor | `input_digests` (SHA-256/size of `AGENTS.md`/`SANDBOX.md`/`PRIVILEGED.md`/`agent-workflow.json`) plus the `agent-workflow-bootstrap@v1` selector fields. |
| `scope.explicit` | doctor | The claim's own declared write-scope paths. |
| `scope.derived` | scope planner | DAG-downstream outputs of any explicit scope path that is itself a non-derived DAG input, with source→stage→output chains. |
| `scope.dag_considered` | scope planner | Whether the authoritative DAG could be loaded/validated at all. |
| `pending_attempt.current_pointer` | runner transaction | The `current.json` pointer's task/request/verdict/lifecycle/result-path fields, if present. |
| `pending_attempt.result` | runner transaction | A bounded subset of the pointed-to `result.json`: verdict, lifecycle state, current phase, per-phase name/status/exit code, findings' rule/message, commits, recovery text, evidence paths. |
| `pending_attempt.result_consistent` | runner transaction | Whether the result bytes' SHA-256 matches the pointer's bound `result_sha256`; `false` flags tampering or a stale/mismatched pointer. |
| `completed_phases` | runner transaction | Names of phases with `status: "passed"` in the pending attempt's result, in original order, deduplicated. |
| `material_findings` | doctor | Doctor findings whose `subject` is this Task ID or whose `path` is this claim's path, bounded to 15. |
| `retained_evidence` | doctor + runner transaction | `{path, sha256}` pairs for the claim file and the pending attempt's `result.json`, plus bare evidence paths (journal/prepared-result/promotion-journal) named by that result. |
| `next_action` | claim file | The claim's own `## Next step` section content (the doctor only exposes *presence*, not text), or a fallback message when no active claim exists. |
| `next_action_truncated` | this tool | Whether `next_action` was shortened to fit the byte budget. |
| `budget` | this tool | `max_bytes` (the fixed or caller-supplied budget) and `actual_bytes` (the true compact-JSON size of the returned capsule, kept self-consistent by construction). |
| `truncated` | this tool | Per-field drop counts recorded while fitting the budget. |
| `summary` | this tool | At most ten human-readable lines. |

## Bounded-size guarantee

The default budget is `DEFAULT_MAX_CAPSULE_BYTES = 8192` (8 KiB of compact
canonical JSON); callers may override it with `--max-bytes`/`max_bytes=`.
When the assembled capsule exceeds the budget, fields are dropped one item
at a time, lowest priority first, recomputing the true serialized size after
every drop:

1. `material_findings` (tail first);
2. `scope.derived`;
3. `prerequisites`;
4. `completed_phases`;
5. `retained_evidence`;
6. `authority.input_digests` (drop order: `agent-workflow.json`,
   `PRIVILEGED.md`, `SANDBOX.md`, `AGENTS.md` — least load-bearing for an
   immediate resume decision first).

Once every one of those is empty, `next_action` is shrunk as a last resort:
each step strictly halves its un-ellipsized core length (a monotonic,
provably terminating reduction — this is unit-tested directly, since an
earlier draft of this shrink step could plateau and loop) until a 16-
character floor, after which it becomes `null`. The Task/Feature identity,
claim identity, and schema/verdict fields are never dropped. `budget.actual_bytes`
is always the exact compact-JSON length of the capsule actually returned
(computed via a short fixed-point pass, since recording the size changes the
size field's own serialized width). For a pathological budget smaller than
the irreducible skeleton, the loop still terminates promptly and reports the
true achieved size rather than silently claiming the budget was met.

## Read-only and safety model

- Every file read (claim, DAG, `current.json`, `result.json`, instruction
  bundle) goes through a bounded, symlink-rejecting, regular-file,
  UTF-8-checked reader; oversized or unsafe inputs are treated as absent
  rather than partially trusted.
- `reachable_commits` may be injected (as `legacy_task_doctor.scan_repository`
  already supports) for hermetic fixtures; normal callers omit it.
- The tool never writes to `output/logs/**`, a claim, `TODO.md`/`DONE.md`, or
  the runner slot, and it takes no lock.

## Fixtures and validation

`_src/tests/test_task_context_capsule.py` is a hermetic, tempdir-based suite
(no shared fixture-file corpus; each test builds a minimal self-contained
legacy-list repository). It covers Task-not-found/malformed-ID/incomplete-scan
verdicts, claim identity/scope/next-step extraction, DAG-derived-scope
expansion (both a real DAG-source path and a non-source path), pending-attempt
reading including a tampered-result-bytes consistency check, material-finding
scoping, ambiguous-claim handling and disambiguation, budget enforcement
(including a pathological-tiny-budget termination guarantee), bounded
`render_summary`, and CLI exit codes.

Two fixtures reconstruct the exact historical incidents named by this Task's
Definition of Done:

- `test_resume_0037_48_premature_publication` replays the real 2026-08-16
  `0037-48` incident — a turn exhausted its tool budget and prematurely
  reported publishing `run.sh` before it existed (see the retained claim
  `TODO-perplexity-0037-48-a7f3c1e29b04.md` and `TODO.md`'s Progress log for
  that Task) — using the claim's own verbatim recorded "Next step" text, and
  asserts the capsule surfaces the correct pending phase-2 work rather than
  the already-completed discovery phase.
- `test_resume_0036_06_context_overflow` reconstructs `0036-06`'s recorded
  context-overflow lesson (`TODO.md`'s Feature-`0038` evidence baseline names
  "context overflow" among current legacy claims; `DONE.md`'s closure
  evidence records ten locale registers, a stable-ID JSONL pipeline, and
  fail-closed `translate.googleapis.com` retries that "exceeded the original
  900-request estimate"). Because that claim predates the branch-workflow
  claim-retention rule and was deleted at Feature closure, no literal claim
  file survives; the fixture is an evidence-grounded reconstruction of a
  plausible mid-run state (some locales already complete, the rest pending),
  documented as such rather than presented as a byte-for-byte replay.

```sh
python3 -m py_compile \
  _src/tools/task_context_capsule.py \
  _src/tests/test_task_context_capsule.py

python3 -m unittest discover -s _src/tests -p 'test_task_context_capsule.py' -v

python3 _src/tools/automation_safety.py \
  --root . \
  --path _src/tools/task_context_capsule.py \
  --path _src/tests/test_task_context_capsule.py \
  --json
```
