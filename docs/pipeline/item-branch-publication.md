# Direct item-branch publication

This is the direct-execution publication contract for Task `0041-04`,
requirements `RQ-WT-03` and `RQ-WT-06`, and `DEC-0041-007`. It complements
[`worker-clone-provisioning.md`](worker-clone-provisioning.md): provisioning
creates or restores an isolated checkout on the bare item branch; publication
is the separate, explicit operation that transfers its committed result to the
same bare item branch in a configured remote.

The interface grants no assignment, credential, review, Acceptance,
integration, release, waiver, or risk authority. The caller must already hold
those permissions. The tool validates only the supplied item/ref transaction;
it never infers authority from a role, mailbox, claim filename, remote URL, or
available credential.

## Interface

```sh
python3 _src/tools/publish_item_branch.py \
  --repo /absolute/path/to/isolated-clone \
  --item 0041-04 \
  --source 0041-04 \
  --target 0041-04 \
  --remote origin \
  --expected-old 0123456789abcdef0123456789abcdef01234567 \
  [--dry-run]
```

All six values are mandatory. `--remote` is a configured remote **name**, not a
URL or refspec. It must resolve to exactly one push URL. That URL is used for
the read-only exact-ref query but is never printed, so embedded transport data
or credentials cannot enter the outcome. The tool does not invoke credential
helpers itself; ordinary Git transport decides whether the preconfigured
remote is usable.

`--item`, `--source`, and `--target` must be the identical canonical bare item
ID (`XXXX`, `XXXX-YY`, or `XXXX-YY.ZZ`). `refs/heads/...`, another item's
branch, detached `HEAD`, aliases, and protected names are refused. The checked
out branch and `HEAD` must equal the explicit source, and the source worktree
must contain no staged, tracked, or untracked difference.

`--expected-old` is a full lowercase object ID. Use the repository's all-zero
object ID only when the target must not exist. A nonzero expected commit must
already be available in the isolated clone; the tool never fetches or silently
changes local refs to obtain it.

## Guard and mutation order

The publisher fails closed in this order:

1. Validate the repository, canonical item/source/target binding, protected-ref
   boundary, configured remote name, checked-out branch, clean state, source
   commit, and full expected object.
2. Resolve exactly one push URL and query only `refs/heads/<target>`. A missing,
   multiple, malformed, or stale result stops before push.
3. Require the source to be a descendant of a nonzero expected old commit.
   Thus a non-fast-forward update is rejected before Git receives a push.
4. Recheck the source `HEAD`, branch, and complete status immediately before
   mutation. Concurrent local change stops as `PUB-LOCAL-RACE`.
5. Push the exact source object to the exact target with a ref-specific
   compare-and-swap lease. The lease is a race detector, not force authority:
   the independent ancestry check above has already forbidden a non-fast-
   forward tree. No `+` refspec or unbounded force option is used.
6. Query the exact remote ref again. Success is reported only when it equals
   the source object. The source `HEAD`, branch, index/worktree status digest,
   and bytes must still match the preflight snapshot.

`--dry-run` executes steps 1–4 and emits the intended transaction without
calling `git push`.

## Outcome and recovery evidence

Standard output is exactly one sorted JSON object with schema
`item-branch-publication-outcome@v1`. It includes the item, source/target,
remote name, expected/observed/source/after object IDs, whether a push was
attempted, whether the source worktree was preserved, a stable result code,
and a bounded recovery action. Raw remote URLs and Git output are not emitted;
the push result is represented by its return code and SHA-256 digest.

The caller retains this JSON in its ordinary task/run evidence. Important
states are:

| Code | Meaning | Safe next action |
|---|---|---|
| `PUB-DRY-RUN` | Every guard passed; no mutation attempted | Re-run the same pinned command without `--dry-run` |
| `PUB-OK` | Post-push exact-ref query equals the source | Retain outcome; continue only under the owning workflow |
| `PUB-ALREADY-PUBLISHED` | Remote already equals source, including retry after an ambiguous response | Retain outcome; do not push again |
| `PUB-EXPECTED-STALE` | Remote differed before push | Inspect and explicitly re-pin; never substitute the observed value automatically |
| `PUB-NON-FAST-FORWARD` | Source does not descend from expected old | Reconcile history outside this tool; force is not an option |
| `PUB-LOCAL-RACE` | Source state changed after preflight | Stop, inspect local ownership/state, and restart from a clean pin |
| `PUB-CAS-LOST` | Remote changed during the guarded window | Inspect the reported post-race object and explicitly re-pin |
| `PUB-PUSH-FAILED` | Push failed and the remote is provably unchanged | Correct transport/policy outside the tool, then retry the same command |
| `PUB-INTERRUPTED` | Execution stopped before a known result | Query the exact remote ref, then retry; idempotence detects prior success |

Any other refusal is resolved at its named input or state boundary. A green
JSON outcome proves only this one ref transaction; it is not Acceptance,
checkpoint approval, integration authority, publication permission, or release
approval.

## Hermetic verification

Run the focused suite with:

```sh
python3 -m unittest -v _src.tools.test_publish_item_branch
```

The suite creates only disposable local repositories. It covers ordinary and
absent-target success, protected/noncanonical/mismatched refs, missing or
ambiguous remotes, dirty state, malformed/stale expected objects,
non-fast-forward history, local and remote CAS races, interruption/retry,
push rejection, dry-run, idempotent retry, and canonical-worktree preservation.
It never uses a network URL, credential, protected ref, or project remote.
