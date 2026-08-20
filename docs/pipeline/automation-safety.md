# Automation-safety validation

`_src/tools/automation_safety.py` is the stdlib-only static safety gate for tracked Python and shell automation. It detects destructive or false-success orchestration before such code is accepted as routine Task tooling. The checker is read-only: it never rewrites a finding, script, policy, index, claim, or backlog file.

## Run it

From the repository root:

```sh
python3 _src/tools/automation_safety.py
python3 _src/tools/automation_safety.py --json
```

A live scan discovers scripts through `git ls-files`. It inspects both index and worktree bytes whenever they differ, and falls back to the index when an unrelated worktree deletion makes a path unavailable. A staged risk therefore cannot be hidden behind safe unstaged bytes. Policy index/worktree divergence is itself a blocking error. Live scans exclude `logs/**`, `output/**`, `node_modules/**`, test files, and fixture directories. Archived scripts and fixture text are therefore not accidentally treated as executable current policy.

Extensionless frozen bytes are scanned only when their language is explicit:

```sh
python3 _src/tools/automation_safety.py \
  --fixture _src/tests/fixtures/automation_safety/old_runner_envelope.sh.fixture \
  --language shell --json
```

`_src/validate.py` calls the live checker through `check_automation_safety()` before the generated-tree checks. An import error, unreadable tracked script, malformed policy, stale disposition, or unresolved critical finding is a project-validation error.

## Stable rules

| Rule | Default severity | Condition |
|---|---|---|
| `AUTO001` | critical | A mutating or statically unresolved subprocess result is unchecked or explicitly ignored. |
| `AUTO002` | critical | A required failure can still reach an unconditional PASS/zero-success result. |
| `AUTO003` | critical | Mutation or Git staging uses a broad directory, `-A`, `.`, or wildcard scope. |
| `AUTO004` | critical | A force update targets `main`, `master`, or an equivalent protected refspec. |
| `AUTO005` | high | An integration remote, branch, user, or email identity is embedded in automation. It is elevated to critical for publication/integration commands. |
| `AUTO006` | high | Automation invokes a shell interpreter (`os.popen`, `os.system`, `shell=True`, or a shell command). It is elevated in authority/backlog contexts. |
| `AUTO007` | critical | A function presented as an audit/check/validation also repairs source state. |
| `AUTO008` | critical | Destructive or authoritative mutation occurs before a required validation, identity, revision, or capability gate. |
| `AUTO009` | critical | A Git commit, push, or ref-publication result is ignored. |
| `AUTO010` | high | Destructive automation lacks operation-linked durable outcome, journal, rollback, or recovery state. It is elevated for VCS publication or authoritative backlog mutation. |

`AUTO000` is an internal critical finding for a source file that cannot be parsed or inspected. It cannot be suppressed.

Python inspection uses the AST and resolves canonical, module-aliased, directly imported, and simple assignment-aliased `subprocess`/`os` callables. Every reachable static argv assignment contributes a command variant; an unresolved executable remains unsafe unless the call propagates its status. Command classification unwraps supported execution prefixes such as `env`, including quote-aware `-S`/`--split-string` argv expansion with fail-closed malformed input, and direct shell-interpreter argv (`sh -c`, `bash`, and equivalents) remains mutating/unchecked unless its subprocess result propagates; embedded publication commands retain their Git rules and also emit `AUTO006`. `check=False` is not itself a finding: direct nonzero checks must dominate the call and propagate on every nested branch, while returned `CompletedProcess` values, checked `Popen.wait()` status, and returned per-item failure aggregates remain valid wrapper contracts. An aggregate return must actually carry the collection or become nonzero when it is nonempty; merely mentioning `failures` in an always-zero expression is insufficient. Successful termination such as `sys.exit(0)` or `raise SystemExit(0)` never counts as failure propagation. Every destructive operation missing durable state receives its own finding identity, including operations grouped into a module recovery scope. A filename such as `status` or `result` is not durable evidence by itself: the written payload must contain outcome/recovery state, be emitted in the same guaranteed statement sequence after the operation (or through a linked writer call in that sequence), and share a concrete argument/result identity with that operation unless it is a full recovery journal. Conditional, comprehension-contained, generator-suspended, process-termination-unreachable, or otherwise bypassable writers do not prove durable state.

Shell inspection is deliberately conservative and command-oriented rather than a general shell parser. Its mutator vocabulary shares the Python command policy (`chmod`, `chown`, `cp`, `install`, `ln`, `mkdir`, `mv`, `rm`, `tee`, `touch`, `truncate`, and `sed -i`) and tokenizes every simple command in control lists, including quote-unwrapped command words, absolute paths, supported command prefixes with option operands, reordered short options, and `sed` in-place suffixes such as `-i.bak`. It reconstructs backslash-continued logical commands and models module-level contexts where Bash suppresses `set -e` (`if`/`while`/`until` tests, inversion, AND/OR lists, and background jobs); a module-level pipeline is checked through `errexit` only when `pipefail` applies. Because a line-oriented scanner cannot soundly prove every direct, aliased, grouped, prefixed, redirected, multiline, conditional, or background invocation of a shell function, implicit module/caller `errexit` is no longer trusted for any later mutation once a function declaration appears. This sticky fail-closed boundary recognizes brace, split-line, `function name` declarations with shell command-word names, and non-brace compound declarations at line-leading, reserved-word/whitespace, or unquoted command-list/group positions in shell-accurate backslash-newline-concatenated logical commands (including continuations inside tokens), so even an imperfect diagnostic end boundary cannot restore a false module-level green. Exact function symbols still use a quote/comment/expansion-aware structural parser for evidence, but symbols do not control the safety verdict. Such functions or later mutations require remediation or one exact expiring disposition. At module scope, only literal nonzero or same-handler `$?` `exit` values are trusted, not arbitrary variables or an unverified function merely named `fail`, `die`, or `fatal`; a wrapper that consumes `"$@"` remains unsafe when it can continue after recording failure. Aggregated shell findings hash the complete reconstructed logical command for every contributing operation—even a single continued command—so changing an executable or adding another unchecked mutation/publication invalidates an existing exact disposition. Shell durable state requires outcome content in the immediate guaranteed command sequence after the operation and sharing a concrete variable/argument identity; conditional lists, same-line early termination, and detached or bypassable writers do not count. Publication severity is derived from parsed command identity, so quoted/prefixed checked commits and pushes without durable state remain critical. Direct `$?`/`PIPESTATUS` counts only on the next executable line when no earlier sequential, conditional, pipeline, asynchronous, command-substitution, or backtick command can replace it, while a full recovery journal may carry its own identity. A `status`- or `result`-named redirection target alone is never sufficient.

The fixture suite freezes both sides of that boundary:

- historical unchecked add/commit plus unconditional PASS;
- protected force publication and embedded identity;
- wildcard legacy claim closure without recovery;
- mutation before a required gate;
- shell execution and validation-time repair;
- a checked wrapper and per-item continuation with an aggregate nonzero result;
- subprocess import/callable aliases, `env`/shell-interpreter argv, conditional argv variants, unresolved executables, zero-code `SystemExit`, semantic aggregate returns, nested all-branch propagation, checked `Popen.wait()` status, and per-operation durable-state identity;
- continued module commands, fail-closed function-contained mutations across direct/aliased/grouped/background invocation shapes, status-consuming wrappers, zero-valued handler variables, unverified handler names, `errexit` suppression in module conditionals/AND-OR/background contexts, and pipeline behavior with and without `pipefail`;
- detached, misordered, conditional, comprehension-contained, generator-suspended, separate-line/same-line/asynchronous/command-substitution stale-status, wrong-identity, early-termination, and operation-linked Python and shell durable-state writes;
- quoted/prefixed commands in shell control lists and full evidence identity for backslash-continued commands.

Run the focused tests with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest _src.tests.test_automation_safety
```

## Finding and exit contract

Every finding contains:

- stable `rule` and `severity`;
- exact repository-relative `path` and one-based `line`;
- enclosing `symbol` where available;
- exact source-span `evidence` (all contributing commands for an aggregate shell finding);
- SHA-256 of those evidence bytes;
- `status`: `unresolved`, `disposed`, or `advisory`;
- an exact disposition object when status is `disposed`.

JSON output is stable and includes scanned paths, counts, policy errors, and `PASS`/`FAIL`. The process exits nonzero only when at least one critical finding is unresolved or policy evaluation fails. Undispositioned high advisories remain visible for lifecycle classification and do not silently become accepted behavior. An exact policy entry may classify a high finding, but the JSON retains the finding, rationale, owner, expiry, and independently testable invariant.

## Narrow dispositions

`_src/tools/automation_safety_policy.json` may disposition a known finding only with all of the following:

- one exact path, rule, line, enclosing symbol, and full evidence-span SHA-256; aggregate evidence binds every contributing operation;
- `kind` equal to `blocking-task` or `narrow-suppression`;
- a concrete rationale;
- one open owner Task;
- `expires_after_task`, an ISO `expires_on` date, or both;
- an independently testable expected safe invariant.

Globs, directories, broad file ignores, missing owners, duplicate entries, and undocumented risk acceptance are rejected. A disposition expires automatically when any of these occurs:

1. the evidence bytes or line move/change, so the exact finding no longer matches;
2. its owner or expiry Task becomes `[x]` or `[w]`;
3. its calendar expiry passes;
4. the finding disappears but the stale policy entry remains.

Expiry is fail closed. The operator must remove the stale entry after a real fix, or review and bind a replacement entry to the new exact finding. Completing a blocking Task without eliminating or explicitly re-authorizing its finding therefore cannot leave a permanent exemption behind.

## Current remediation and blocking map

Task `0038-03` directly removed three false-green paths:

- `_src/tools/link_verification_evidence.py` is now an audit helper. It reports scratch state, validates JSON without repair, uses generation check mode, checks every required subprocess result, reports Git status read-only, and never stages or commits.
- `_src/tools/build_report.py` now requires all four schema-valid producer stages from one exact non-empty `run_archive_ref` cohort, never borrows stale stages from another run, rejects malformed envelopes/timestamps/findings and uncorrelated reports, retains malformed/missing-stage findings, treats missing/invalid exit codes as failure, defaults overall success to false, and returns the combined nonzero exit code.
- `_src/tools/spec_extraction_campaign.py` binds every job and raw output path to a deterministic attempt identity covering the manifest inputs and extraction contract. Its manifest invokes a `run-job` worker that checks current tool/runtime/backend contracts and emits an exact attempt/job/extractor/result envelope; bare, copied, nonzero, malformed, or contract-drifted outputs cannot satisfy reporting. Historical outputs remain retained but cannot satisfy a changed manifest; incomplete current attempts still write comparison and scorecard artifacts and exit nonzero.

The remaining live critical findings are not accepted as safe. Exact entries block them on existing work:

| Paths/risk | Blocking Task |
|---|---|
| `_src/tools/publish_public_site.sh`: fixed export cleanup, no durable recovery, broad staging | `0038-13` candidate isolation and promotion |
| `_src/tools/bootstrap_ssh_known_hosts.sh`: AND-list setup failure and trust-store append before fingerprint gate | `0038-14` |
| `_src/tools/bootstrap_instance.sh`: embedded remote, ignored remote removal, mutation before readiness gates | `0038-15` approval-readiness productization |
| `_src/tools/manage_approval_readiness.py`: in-place authority-policy write without durable recovery | `0038-15` |

| `_src/i18n/work/{hi,zh}/*write*.sh`: unchecked one-off absolute-path writers | `0038-14` classification/retirement |
| Privileged host bootstrapper (`runner-host/run-loop.sh`, moved from `_src/` by `0038-24`): exact high lifecycle debt for setup, cleanup, installers, self-test artifacts, and mutable runner outcomes | `0038-10` immutable aggregate results; the 21 exact dispositions are re-pointed to open Task `0038-28` (see below) |

Task `0040-10` repaired the privileged host bootstrapper's genuine status gaps without weakening the scanner: setup and archival mutations have explicit fatal paths; the status-preserving cleanup trap is armed immediately after successful `RUNNER_TMP_DIR` creation and safely tolerates `resume_applescript` not yet being defined; installer wrappers propagate failure; both runner/log pipeline statuses are aggregated; self-test process, fail-log, and cleanup statuses gate PASS and execution. The shell scanner intentionally retains findings across its sticky function-declaration boundary. Each retained finding therefore has one exact path/rule/line/symbol/evidence-hash disposition owned by open Task `0038-28`; the two exact `AUTO006` entries document the confirmation-gated official Homebrew installer, while each `AUTO010` entry remains explicit immutable-result debt. The TK-2 scope decision, alternatives, consequences, and all 21 individual dispositions are recorded in [`docs/dossiers/0040-10-automation-safety-scope-and-dispositions.md`](../dossiers/0040-10-automation-safety-scope-and-dispositions.md). Moving the bootstrapper into `runner-host/` under Task `0038-24` must rebind exact paths after scanning final bytes; it must not add a host-code or directory exclusion.

Task `0038-26` removed the embedded publication identity/destination and the unconditional force-push from both `_src/publish.sh` and `_src/tools/publish_public_site.sh`, and removed the six now-resolved dispositions those two scripts previously carried (re-pointed there from expired `0038-14`). Both scripts now require the caller to supply `PUBLISH_REMOTE`/`PUBLISH_IDENTITY_NAME`/`PUBLISH_IDENTITY_EMAIL` explicitly (no default resolves to the public repository), and `publish_public_site.sh`'s history-rewriting force-update is gated behind explicit `PUBLISH_ALLOW_FORCE_PUSH=1` plus a named `PUBLISH_FORCE_APPROVAL_REF`, recording the pre-update remote SHA as a recovery point. The remaining `publish_public_site.sh` row above (fixed export cleanup / broad staging, `0038-13`) is untouched by this Task and still open.

Task `0038-05.01` retired `_src/tools/task_bookkeeping_closure.py` as a mutation-free fail-closed compatibility shim and removed its two exact blocking dispositions. `_src/tools/legacy_task_editor.py` writes only review candidates; every authoritative promotion returns `LTE-PROMOTE-COORDINATOR-REQUIRED` until `0038-05.02` integrates the verified candidate contract with the durable transaction coordinator.
| `_src/tools/provision_tmp_worktree.sh`: explicitly superseded privileged worktree provisioner; exact retained legacy branch/prune/repair/delete/add aggregate | `0038-14` mutator lifecycle classification or retirement; refreshed exact `AUTO001` blocker |
| `_src/tools/provision_worker_clone.sh`: current privileged clone provisioner; exact branch creation and guarded destructive target-rebuild aggregate lacks a durable lifecycle result | `0041-05` Feature integration/e2e; exact `AUTO001` narrow and `AUTO010` blocking dispositions |
| `_src/tools/sync_to_devel.sh`: destructive backup sync with implicit lock/cleanup/result lifecycle | `0038-14` mutator lifecycle and classification |

The full-scan baseline findings added during `0040-10` peer-review remediation are recorded separately from its 21 run-loop findings in [`docs/dossiers/0040-10-automation-safety-scope-and-dispositions.md`](../dossiers/0040-10-automation-safety-scope-and-dispositions.md). The stale superseded-worktree entry is rebound to current line `41` and owner `0038-14`; the clone provisioner's exact line-`86` `AUTO001`/`AUTO010` findings expire with `0041-05`. Neither provisioner source was changed by this remediation.

Other high findings—such as destructive extraction, legacy shell execution, and missing durable state—remain machine-visible advisories for `0038-14` and related lifecycle Tasks. They are not hidden by the critical blocking policy.

## Operator response

1. Run the JSON scan and identify the exact rule/path/line.
2. Prefer a root-cause fix and add or update a known-bad fixture.
3. If an existing open Task already owns a larger safe redesign, add only an exact hash-bound blocking disposition.
4. Never update a digest merely to make validation green. Re-evaluate the changed source and its owner Task first.
5. Run the focused tests, the live checker, and `_src/validate.py` before committing.
