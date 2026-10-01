# Task evidence packs

`_src/tools/task_evidence_pack.py` builds a compact, content-addressed
`task-evidence-pack@v1` manifest for a single Task attempt (Task `0038-12`).
It replaces the pattern of copying raw probe scripts and repeated log output
verbatim into every timestamped log directory with one manifest, a
deduplicated blob store, and pointers to tracked source/scripts by exact Git
commit and path.

## Where it is used

A closure or validation step that needs to retain evidence calls `build` with
the exact argv/action, base commit, tool identity, the environment ID from
`_src/tools/environment_doctor.py`'s `prepared-environment@v1` fingerprint
(`0038-09`), exit status, an explicit list of evidence paths, and a criterion
mapping. It writes the manifest plus any newly seen blob content once under a
content-addressed blob store, and never duplicates bytes already stored under
the same digest.

```text
python3 _src/tools/task_evidence_pack.py build \
  --root . \
  --blob-root output/logs/<task-id>/evidence-blobs \
  --out-manifest output/logs/<task-id>/<request-id>/evidence-pack.json \
  --task-id 0038-12 \
  --action test-runner-transaction \
  --base-commit <sha> \
  --tool-name task_evidence_pack \
  --exit-status 0 \
  --items-json '[{"path": "output/logs/.../result.txt"}]' \
  --criteria-json '[{"id": "definition-of-done", "satisfied_by": ["output/logs/.../result.txt"]}]'
```

`verify` re-checks a manifest against its blob store and any tracked-ref
commits, without trusting the manifest's own claims:

```text
python3 _src/tools/task_evidence_pack.py verify \
  --root . --blob-root output/logs/<task-id>/evidence-blobs \
  --manifest output/logs/<task-id>/<request-id>/evidence-pack.json
```

## What it records and rejects

Each declared evidence path becomes exactly one item: a `blob` (content
copied once into the digest-keyed store; a bounded excerpt capped at 20 lines
/ 8 KiB is retained, matching the excerpt bound in `SANDBOX.md`) or a
`tracked-ref` (a script/source file already committed at an exact commit —
referenced by commit and path instead of being duplicated). The builder fails
closed, before writing anything, on:

- **secrets** — PEM/AWS/GitHub/Slack/bearer/generic key-value patterns in the
  candidate bytes (`EVP-SECRET-*`);
- **broad globs** — any declared path containing `*`, `?`, or `[` instead of
  an exact path (`EVP-BROAD-GLOB`);
- **unrelated-run evidence** — a path naming a Task ID other than the pack's
  own `task_id`, unless explicitly listed in `related_task_ids`
  (`EVP-UNRELATED-RUN`);
- **ignored scratch as sole closure proof** — a pack whose only evidence is a
  git-ignored log path with no captured `blob`/`tracked-ref` item
  (`EVP-SCRATCH-SOLE-PROOF`).

A criterion mapping (`{"id": ..., "satisfied_by": [path, ...]}`) must resolve
only to items actually present in the pack (`EVP-CRITERION-UNKNOWN-ITEM`),
keeping the acceptance-criterion trace real instead of prose-only.

## Demonstration against the historical baseline

`_src/tests/test_task_evidence_pack.py` replays the real 184-file/10,384-line
evidence commit `50b20829` cited by the Feature `0038` "Evidence baseline
(2026-08-16)" paragraph in `TODO.md`. Packing its `_src/logs/validate-review-request-ui/**`
subtree (28 files) yields 6 `tracked-ref` items (the probe scripts
`four_url_probe.cjs`/`make_review_fixture.py`, each duplicated verbatim across
two timestamped directories in the original commit, are referenced once) and
22 `blob` items deduplicated to fewer unique blobs, and the resulting pack
verifies clean. A second test shows that mixing in a path from
`logs/backlog-bookkeeping-and-commit/0037-01-*` — genuinely unrelated Task
evidence present in that same historical commit — is rejected with
`EVP-UNRELATED-RUN`.
