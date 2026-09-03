# Issue-store emergency recovery

`_src/tools/issue_recovery.py` is the bounded, stdlib-only recovery surface for
an activated Git-native issue store. It accepts explicit paths and authority
generation values. It does not discover credentials, mutate legacy
`TODO.md`/`DONE.md`, activate the issue store, publish, or promise reverse
migration after the authority cutover.

## Required sequence

1. `freeze` compare-and-swaps the recovery generation, requires an
   `issue-store-writable` selector, writes `issue-store-write-frozen`, and moves
   live session and claim directories into a generation-bound invalidation
   area before repair work starts. Missing or stale generation/state blocks.
2. `export` records all regular files under the issue, provenance, invalidated
   claim, and artifact sets as deterministic path/digest/base64 entries. The
   canonical manifest digest binds the complete set.
3. `restore` validates every manifest and content digest, rejects unsafe or
   duplicate paths and non-empty targets, builds a sibling staging directory,
   and promotes it by atomic rename.
4. `replay` orders immutable events by sequence and ID. Its durable ledger
   makes matching retries no-ops; reused IDs with different payloads and paths
   containing different bytes are blocking conflicts.
5. `repair` applies a bounded content plan only while frozen and only when each
   current file matches its declared SHA-256. `regenerate` delegates the full
   declared DAG to `issuectl regenerate --all`; either failure blocks release.
6. `release` accepts only a generation-matching `issue-recovery-release@v1`
   whose canonical payload digest matches and whose independently verified
   signature flag is exactly true. It restores writable selector state and
   advances the recovery generation. The tool verifies recorded signature
   status; it neither owns signing keys nor manufactures release authority.

Sandboxed callers use the seven fixed IDs in
`_src/runner/issue-recovery-actions-v1.json`. An optional runner transports the
action; it never supplies emergency or release authority. Direct callers use
the same CLI and checks.

## Failure, recovery, and limits

All outputs are JSON. A refusal exits `2` with a stable `RECOVERY-*` code.
File replacements and restored-tree promotion are atomic. If a process stops
between invalidation, selector replacement, and control-record replacement,
operators must keep writes disabled, inspect the generation-bound invalidation
directory, and repeat or forward-complete the same generation; they must not
guess a newer epoch or delete preserved bytes.

The tool provides no zero-data-loss or fixed-RTO guarantee. Data not present in
the frozen export or immutable later-event input cannot be reconstructed.
Large exports are memory-bound by the JSON/base64 representation. Exact RTO is
therefore proportional to source bytes, validation, replay, repair, and full
regeneration time. Reverse conversion into legacy backlog files is expressly
unsupported after the issue-store point of no return and requires a separately
authorized future migration process.
