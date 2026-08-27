# Claim: validate.py non-termination investigation

owner_token: agent:chakotay-tuvix:validate-py-nontermination-20260827:20260827T075600Z
agent: chakotay-tuvix-20260827t075600z
capability_class: unprivileged
dispatcher: chakotay
item: validate-py-nontermination-20260827 (temporary infrastructure item, not a TODO.md Task)
branch: validate-py-nontermination-20260827
base_pin: a1718ba972c103d172a5902be01b7c1f9c2bb155 (main, verified ancestor by dispatcher)
worktree: /Users/tobias.anton/devel/.worktrees/validate-py-nontermination-20260827
state: [p]

## Context

Geordi's Feature 0037 checkpoint recorded `python3 _src/validate.py` as INCONCLUSIVE:
no result after four bounded 30s intervals. Kathryn's bounded probing (lead, not full
measurement):
- `check_automation_safety` (check 1/12 in validate.py main()) did not finish within 40s isolated
- `automation_safety.py --json` directly did not finish within 60s
- `tracked_automation_paths()` returned 116 paths in 0.14s (filter is fast)
- `scan_text` over a 20-file sample took 16.38s ~= 0.82s/file
- Naive extrapolation: 116 * 0.82s ~= 95s (not confirmed by a full run)

Working hypothesis to verify: validate.py isn't hanging, it's slow and silent — which
looks like a hang to a bounded caller.

## Write scope

- `_src/validate.py`
- `_src/tools/automation_safety.py` (instrumentation/measurement only — see hard boundary)
- `_src/tests/**` covering these
- this claim file
- short-lived measurement scripts (kept in-repo committed, or removed before finishing)

## Hard gate-scope boundary (binding, do not cross)

`automation_safety.py` is a cross-item gate. NOT ALLOWED in this task: any change to
`scan_text`, path-selection (`tracked_automation_paths`), or filtering logic
(`_excluded_live_path` etc) — anything that could change what the gate detects. If a
concrete cost driver is found there, STOP AT THE FINDING, record it, do not fix it.

## Prohibitions

No Acceptance, no checkpoint verdict, no integration, no `main`, no `DONE.md`, no push
(local commits only, report SHAs), no `memory_append`, no `git add -A`/`.`, no touching
`logs/agent-memory/**`, no re-pinning Geordi's frozen INCONCLUSIVE checkpoint (candidate
`0515e0dfb`).

## Investigation notes (running log)

### Structure confirmed

- `_src/validate.py` `main()` runs exactly 12 checks in this order: `check_automation_safety`,
  `check_build`, `check_links`, `check_langs`, `check_requirement_review_schema`,
  `check_namespaces`, `check_home_links`, `check_no_hardcoded_german`,
  `check_client_rendered_german`, `check_record_status`, `check_workflow_lifecycle`,
  `check_report_freshness`. No existing progress output between checks — first output
  is the final OK/PROBLEME block after all 12 finish. This matches Geordi's blocker
  exactly: nothing to observe mid-run.
- `check_automation_safety()` (validate.py:804-844) calls
  `automation_safety.scan_repository(Path(ROOT), policy_path=...)`.
- `scan_repository()` (automation_safety.py:2912-2932): for each of the 116 tracked
  paths (from `tracked_automation_paths`), calls `_read_tracked_sources(root, path)`,
  which internally calls `_read_index_source` -> `subprocess.run(["git", "show",
  ":%s" % path], cwd=root)` **once per path** (a fresh git subprocess per file), plus a
  worktree read, then `scan_text()` on each variant.
- Candidate cost driver identified but NOT touched (per hard boundary — this is in the
  read/subprocess-per-path machinery, not scan_text/path-selection/filtering itself,
  but touching it would change what/how the gate reads sources, so treated as in-scope-adjacent
  and left alone pending real profiling numbers): 116 `git show` subprocess spawns,
  one per tracked path, inside `_read_tracked_sources`/`_read_index_source`
  (automation_safety.py:2624-2664). Each subprocess spawn has real fixed overhead
  independent of file size — this is a plausible explanation for the reported
  ~0.8s/file even on small files, distinct from `scan_text`'s AST-walk cost.

### Measurements (real repo, worktree
  /Users/tobias.anton/devel/.worktrees/validate-py-nontermination-20260827)

- `tracked_automation_paths(Path('.'))`: 116 paths, 0.251s (confirms Kathryn's ~0.14s
  lead within the same order of magnitude; delta likely cold-vs-warm git process cache).
- Full `scan_repository()` profile: see below, filled in after background run completes.

## Outcomes status

1. Visibility (progress instrumentation in validate.py main()): IN PROGRESS
2. Profiling (full 116-path run, cProfile): IN PROGRESS (background run started)
3. Budget + regression tests: NOT STARTED

## Handoff

None yet — actively worked by this session.
