---
schema_version: "1.0"
id: "0038-13"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-06"
  - "0038-08"
  - "0038-11"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1736"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0038-13:0038-06, 0038-13:0038-08, 0038-13:0038-11 Isolate generated candidates and enforce output/diff/realism budgets. REF: `716335631`.

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-13-Commit)`). Abgenommene Baseline `716335631`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. 39/39 eigene Tests am eigenen REF.
  - **Completion evidence (2026-08-20):** Added `_src/tools/candidate_budget.py` (`candidate-budget@v1`/`candidate-manifest@v1`/`candidate-budget-report@v1`/`candidate-promotion-pointer@v1` schemas) and its hermetic test module `_src/tests/test_candidate_budget.py` in `716335631` on branch `0038-13` (based off Feature branch `0038`, fast-forward merging prerequisite branch `0038-11` to tip `a3b9d4dd0`, which transitively carries `0038-10`'s and `0038-12`'s commits; prerequisites `0038-06`/`0038-08` were already present on `0038`). `candidate_root()` reuses `0038-11`'s `.partial`-style run-specific `output/logs/<task-id>/<request-id>/.candidates/` shape so a candidate is never generated over a shared/fixed path; the budget contract's `sole_writer` mirrors `0038-06`'s sole-writer collision hazard; `evaluate()` returns PASS/FAIL/INCONCLUSIVE with the same discipline as `0038-08`'s `task_validation.py`; `promote()` is atomic/recoverable via a single `current.json` pointer file per destination (the `0038-10` atomic-pointer shape), refuses a non-PASS report, refuses to overwrite a destination owned by a foreign `sole_writer`, and never promotes a path outside the declared `allowed_paths` even given a stale caller-supplied report. Fixtures are grounded in this Feature's "Evidence baseline (2026-08-16)" paragraph: a 4,503-file on-disk generation (one shared `setUpClass` pass covering both the matching-budget and one-file-short cases to bound wall time), a stale fixed export path owned by a foreign `sole_writer`, incomplete language subtrees, synthetic-only UI data caught by a duplicate-content-ratio guard (the Feature `0021` "synthetic-only green" pattern), an undersized "downloaded" payload caught by a per-category realism byte floor, and clean-checkout reproduction via a content-only (not timestamp-based) manifest digest. `python3 -m py_compile` passed on both files; `python3 -m unittest _src.tests.test_candidate_budget -v` passed **39/39** (242.9s wall time, dominated by the 4,503-file fixture's on-disk generation/hashing pass); `python3 _src/tools/automation_safety.py --path _src/tools/candidate_budget.py --json` returned `verdict: PASS`, `unresolved_critical: 0`, `policy_errors: 0` (4 advisory `AUTO010` findings on `promote()`'s `shutil.rmtree` calls — the same expected pattern as `artifact_retention.py`'s deletion-tool advisories); the same check on the test module returned `verdict: PASS` with zero findings. Claim `TODO-seven-dara-0038-13-20260820T060000Z.md` travels on branch `0038-13` per `docs/pipeline/branch-workflow.md`; branch left at rest, not merged into `0038`/`main` by this unprivileged session.

## Acceptance criteria

- **AC-001** Generate into run-specific candidate roots, validate before promotion, declare sole writer and expected file/count/byte budgets, compare exact source-to-output manifests, split source versus generated review, and require production-realistic rendered/downloaded/submitted bytes plus negative paths—not only synthesized in-memory objects. Large or unexplained diffs block before commit

## Definition of Done

Fixtures cover a 4,503-file generation, stale fixed export path, incomplete language trees, synthetic-only UI data, actual downloaded payload mismatch, and clean-checkout reproduction; promotion is atomic/recoverable and no unrelated generated family is swept in.
