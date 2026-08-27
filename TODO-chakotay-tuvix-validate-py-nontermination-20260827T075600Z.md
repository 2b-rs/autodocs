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
- Full `scan_repository()` cProfile run against all 116 real tracked paths:
  **TOTAL_TIME 384.26s** (6m24s), 2,028,414,648 function calls. This CORRECTS
  Kathryn's ~95s naive extrapolation — actual runtime is ~4x that. Reproduction
  command recorded verbatim in `validate.check_automation_safety`'s docstring
  and in `test_validate_automation_safety_budget.py`'s module docstring.
  - Top cost: `automation_safety._shell_structural_text` — 19,507,375 calls,
    249.9s self time / 329.4s cumulative, reached via
    `_shell_symbol` (22,718 calls, 357.7s cumulative) <- `scan_shell` (only
    **11** calls, 360.5s cumulative) <- `scan_text` (116 calls, 371.1s
    cumulative, i.e. nearly the whole 384.26s total).
  - **Key finding: the cost is NOT evenly spread across the 116 files.** Only
    11 of the 116 tracked paths are shell scripts, and those 11 alone account
    for ~360s of the 384s total (~94%). `scan_python` (105 calls, the other
    ~105 files) only cost 10.6s cumulative. Kathryn's 20-file sample
    apparently included a disproportionate number of expensive shell scripts,
    which is why per-file extrapolation from that sample undershot reality —
    the true cost driver is per-shell-script complexity (looks like O(n^2)-ish
    behavior in `_shell_structural_text`'s repeated scanning), not a flat
    per-file cost.
  - Secondary cost: `_read_tracked_sources`/`_read_index_source`'s per-path
    `git show`/subprocess calls — measured at 10.4-12.3s cumulative total
    across all 116 paths (~0.09-0.1s/call). This is real but small (~3% of
    total runtime) compared to the shell-scanning cost; the candidate driver
    hypothesized before profiling (subprocess-per-file overhead) is confirmed
    present but NOT the dominant factor.
  - **GATE-SCOPE FINDING, NOT FIXED (per hard boundary):**
    `automation_safety.py:1897 _shell_structural_text` (and its caller
    `_shell_symbol` at :1951, both inside `scan_shell`/`scan_text`'s shell
    path) is the concrete, precise cost driver: ~330s cumulative / ~86% of
    total runtime, concentrated in 11 files. This lives inside `scan_text`
    (shell branch), which this investigation is explicitly not authorized to
    change — any change here could alter what the automation-safety gate
    detects. Recorded here as a finding; NOT fixed. A future gate-scope-
    reviewed task (decision-record@v1 + independent Architect scope review
    per AGENTS.md) would need to profile `_shell_structural_text` itself
    (likely repeated linear rescans over increasing prefixes/suffixes of the
    same shell source — the 19.5M calls for only 11 files strongly suggests
    non-linear behavior) before any fix is attempted.

## Outcomes status

1. Visibility (progress instrumentation in validate.py main()): DONE, committed
   ae2252a2c on branch validate-py-nontermination-20260827. Adds `CHECKS`
   (explicit ordered list) and `run_checks()` emitting
   `[validate] n/total start/done <name> (Xs)` lines. 5 deterministic tests in
   `_src/tests/test_validate_run_checks.py`, all <0.01s, no timing assumptions.
2. Profiling: DONE. See measurements above. 384.26s measured (not ~95s
   extrapolated); dominant cost isolated to `_shell_structural_text` in 11
   shell files; gate-scope finding recorded, not fixed.
3. Budget + regression tests: DONE.
   - Runtime budget documented in `check_automation_safety`'s docstring
     (exact reproduction command, exact numbers, exact bottleneck) and
     referenced from the budget test module docstring.
   - `_src/tests/test_validate_automation_safety_budget.py`: fast always-on
     ratio-budget test for `tracked_automation_paths` (20x a 0.25s baseline,
     diagnostic message on failure); opt-in (`RUN_SLOW_VALIDATE_BUDGET=1`,
     skipped by default) full-scan ratio-budget test (3x the 384.26s
     baseline = ~19min ceiling, diagnostic message on failure) — per Jean-
     Luc's exact guidance: deterministic tests preferred, wall-clock budget
     kept generous/ratio-based with diagnostics rather than a tight absolute
     threshold.

## Validation run

`cd _src && python3 -m unittest tests.test_validate_run_checks
tests.test_validate_automation_safety_budget tests.test_validate_workflow_lifecycle
tests.test_validate_parallel_links tests.test_automation_safety -v`
-> 136 tests, OK, 1 skipped (the opt-in slow full-scan budget test), 23.5s.
`python3 -c "import validate"` -> imports cleanly, no syntax errors.

## Handoff

None — actively worked by this session. Next: commit outcome 2+3 slice
(validate.py docstring addition + budget test file), update this claim to
[x]/handover per the (not-yet-anchored-in-root, but content-correct)
worktree-branch convention, report final numbers to dispatcher `chakotay`.
