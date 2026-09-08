---
schema_version: "1.0"
id: "0038-12"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0038-09"
  - "0038-10"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1731"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

PREREQ: 0038-12:0038-09, 0038-12:0038-10 Define compact content-addressed Task evidence packs. REF: `a8aa72749`. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-12-Commit)`). Abgenommene Baseline `a8aa72749`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). 23/23 Tests am eigenen REF (unittest test_task_evidence_pack).

## Scope

- **Completion evidence (2026-08-20):** Added `_src/tools/task_evidence_pack.py` (`task-evidence-pack@v1` manifest builder/verifier: content-addressed deduplicated blob store, `tracked-ref` pointers to committed source/scripts by exact commit+path instead of copying them into timestamped logs, bounded 20-line/8KiB excerpts, and fail-closed rejection of secrets/broad globs/unrelated-Task evidence/ignored-scratch-as-sole-proof/unmapped criteria), its hermetic test module `_src/tests/test_task_evidence_pack.py`, and `docs/pipeline/task-evidence-pack.md` in `a8aa72749` on branch `0038-12` (based off Feature branch `0038` at `41f70cc72`, fast-forward merging prerequisite branch `0038-10` to tip `539ea06bb`; prerequisite `0038-09` was already present on `0038`). The DoD's representative bundle is the real historical commit `50b20829` (184 files/10,384 lines) cited by this Feature's "Evidence baseline" paragraph: packing its `_src/logs/validate-review-request-ui/**` subtree (28 files) yields 6 lossless `tracked-ref` items (two probe scripts duplicated verbatim across timestamped directories in that commit collapse to one reference each) and 22 `blob` items deduplicated to fewer unique blobs, verifying clean; a companion test shows a genuinely unrelated path from `logs/backlog-bookkeeping-and-commit/0037-01-*` in that same commit is rejected as unrelated-run evidence. `python3 -m py_compile` on both new files passed; `python3 -m unittest _src.tests.test_task_evidence_pack -v` passed 23/23; `python3 _src/tools/automation_safety.py --path _src/tools/task_evidence_pack.py --json` and the same for the test module both returned `verdict: PASS` with zero findings. Claim `TODO-seven-rebi-0038-12-20260820T022255Z.md` travels on branch `0038-12` per `docs/pipeline/branch-workflow.md`; branch left at rest, not merged into `0038`/`main` by this unprivileged session.

## Acceptance criteria

- **AC-001** Record argv/action, base/tool/environment, exit status, counts, input/output digests, privacy class, bounded excerpt, full-log digest/path, commits, and criterion mapping
- **AC-002** store duplicate content once
- **AC-003** reference tracked source/scripts by commit/blob rather than copying them into timestamped logs
- **AC-004** reject secrets, unrelated-run evidence, broad globs, and ignored scratch as sole closure proof

## Definition of Done

A representative 184-file/10,384-line historical evidence bundle is losslessly represented by a concise manifest plus unique blobs and remains navigable/auditable; duplicate probe scripts/source dumps are eliminated without losing provenance.
