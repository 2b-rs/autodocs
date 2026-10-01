# Atomic cutover manifest fixture

This directory is the non-operative `0041-02` handoff. It does not activate
`atomic-checkin-contract@v1`, alter the current two-commit rule, satisfy the
`0041-06` checkpoint, or authorize integration.

## Files and binding

- `atomic-cutover-manifest.json` is the `atomic-cutover-manifest@v1` source
  inventory and ordered activation contract.
- `../../../dossiers/0041-02-atomic-checkin-contract.md` is the human-readable
  `atomic-checkin-contract@v1` pinned by SHA-256 in the manifest.
- Every `consumer_inputs` entry pins the bytes observed at
  `main@f5763cf21e98066f7e932d50a2b0e9c5802550f9` and states its activation
  obligation. A changed or missing input is `ATC-MANIFEST-STALE` until impact is
  reviewed and the manifest is regenerated.
- A `null` candidate digest means the named producer has not supplied and pinned
  that output. Because `pending_digest_blocks_activation` is true, it is never a
  wildcard or permission to proceed.

The manifest records two current path mismatches in the declared `0041-06`
write scope. The live runner-transaction and hygiene test files are under
`_src/tools/`, while the Task contract names `_src/tests/`. The activation owner
must obtain a scope correction or authoritative resolution before mutation; it
must not silently omit, duplicate, or relocate those tests.

## Validation rules

A conforming validator fails unless all of these are true:

1. JSON parses with no duplicate object keys; `schema_version`, manifest ID,
   source baseline, activation owner, and target ref equal the recorded values.
2. Every digest is lowercase 64-hex or an explicitly pending `null` candidate
   digest. Every pinned path exists as a regular repository file and hashes to
   the recorded value.
3. Consumer paths are unique, all six categories are present, and every current
   path named by the `0041-06` contract is either pinned or explicitly recorded
   as a declared-path mismatch.
4. Before activation, every pending output prefix is replaced by an enumerated
   exact file set with digests; both declared-path mismatches are resolved; and
   the old-writer scan has zero unclassified reachable hits.
5. The validation steps run in the listed order. No later green result waives an
   earlier failure, missing authority, checkpoint, hygiene result, or digest.

The positive commit-message example is defined in contract §10. Required
negative cases cover missing and duplicate trailers, malformed and wrong Task
identity, missing/non-ancestor/stale base, partial tree, non-final claim,
unrelated scope, old writer, partial activation, CAS loss, authority crossing,
ambiguous history, and incoherent rollback. Migration and rollback examples are
also normative in that section.

## Handoff and activation boundary

Task `0041-03` consumes the pinned contract to prepare the non-operative
Acceptance-owned reference transition. Task `0041-06` re-pins all changed input
bytes, enumerates and hashes every candidate output, resolves the two path
mismatches, executes the complete validation order, and assembles one candidate
tree. Only a separately assigned privileged Integrator may record the mandatory
checkpoint verdict and perform the single authorized `main` ref advance after
the required hygiene checks. Task `0041-05` later proves the real workflow end
to end.
