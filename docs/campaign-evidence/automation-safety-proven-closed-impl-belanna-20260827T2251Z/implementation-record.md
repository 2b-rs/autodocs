# DEC-0038-007 `proven-closed` — implementation record (PART-01 input)

**Implementer:** `agent:belanna:automation-safety-proven-closed-impl:20260827T2251Z`, Team Voyager,
capability class `privileged`, role `Implementierer` for this item only (distinct from today's other
Integrator work — see the explicit hat-switch acknowledged in agent-inbox `1787871106493-ca77a2b4` /
`1787871114783-ae9299a2`).

**Purpose of this record:** satisfies `saru`'s r2 forward condition F-R2-02
(`TODO-jadzia-automation-safety-proven-closed-20260827.md`): "a PART-01 implementation record is
required before this can be called review-complete for actual integration into
`automation_safety.py`/the policy schema." This file is ordinary work-product evidence, **not** an edit
to `docs/dossiers/dec-0038-007-automation-safety-proven-closed.md` itself — that DEC is a governance
artifact (`DEC-*`, `docs/dossiers/`) requiring main-only authoring per `DEC-0044-012`, explicitly out of
this item's write scope, and untouched here. Adding the actual `PART-01` review-participation entry to
the DEC record is a separate governance-edit act for whoever holds that authority (Kathryn, per the
r1/r2/r3 transcription pattern already used for this DEC); this record is the input for that entry, not
a substitute for it.

**F-R2-03 compliance:** implementer (`belanna`) is distinct from `jadzia` (Architect, drafted the DEC)
and `saru` (independent reviewer of the DEC). DEC-0038-007 was already merged to `main` before this
item's branch was cut (confirmed at branch base `2a02ac32bfe505cfcf493906d51f346c6149ad9c`, which
already contains `docs/dossiers/dec-0038-007-automation-safety-proven-closed.md` at its final r3 text).
`POLICY_STALE` is not weakened (see below). `owner_ref` reachability verification is not omitted (see
below) — it is a new, real mechanical check, not a rubber stamp.

## Scope item 1 — schema/checker mechanism (CON-01/CON-02/CON-03)

Commit `da179c7f841f3504135f3685cd13ecf2a490ad8a` on this branch.

- `_DISPOSITION_KINDS` now includes `"proven-closed"` alongside the existing two kinds (CON-01).
- New required fields for `proven-closed` only: `owner_ref` (full 40-hex lowercase commit SHA) and
  `proof_summary` (>=30 non-whitespace characters). Both are rejected as extraneous on the other two
  kinds, preventing silent dead fields.
- `owner_ref` reachability is a real mechanical check: `git cat-file -e <sha>^{commit}` executed against
  the repository root, memoized per validation run via a `reachability_cache` dict (33 entries can share
  one proof commit; this avoids 33 redundant subprocess calls). The `^{commit}` peel operator means a
  blob or tag sharing a hex prefix cannot be mistaken for a commit.
- `owner_task`/`expires_after_task` terminal-state rejection (`is terminal; disposition expired`) is
  waived **only** when `kind == "proven-closed"` (CON-02, both fields, not just `owner_task`). The
  format/existence check ("absent from TODO.md/DONE.md") is **not** waived for either field — a
  `proven-closed` entry must still name a real Task for provenance, just not a non-terminal one.
- `expires_after_task`/`expires_on` presence is no longer required for `proven-closed` (its expiry model
  is reachability + digest match, not a live-Task/date model per the original 2026-08-20 suggestion this
  DEC formalizes) but the field, if present, is still format/existence-validated.
- `evidence_sha256` requirement and the `POLICY_STALE` digest-mismatch path (the actual finding-matching
  key against live scanner output) are **completely untouched** by this change — CON-03's "unmatched
  digests must still correctly trigger `POLICY_STALE`" holds because that code path was not modified at
  all, only read from (see `test_policy_stale_still_triggers_for_proven_closed_on_digest_mismatch`).

### Adversarial completion evidence (`DEC-0038-004`)

AE-1 applies: this changes blocking/gate classification (which disposition kinds pass validation).

- **AE-2:** pre-change baseline is any commit before `da179c7f8` on this branch (equivalently, `main` at
  `2a02ac32b`); candidate is `da179c7f8`.
- **AE-3, red-on-baseline/green-on-candidate:**
  `AutomationSafetyProvenClosedTests.test_falsification_terminal_owner_task_now_passes_only_with_proof`
  — a terminal-`owner_task` entry with `kind: proven-closed` and real proof anchoring. On the baseline
  checker this exact case fails with `owner_task ... is terminal; disposition expired` (proven identical
  by the pre-existing, unmodified `AutomationSafetyPolicyTests.test_terminal_owner_task_expires_disposition`,
  same terminal-owner_task fixture, `kind: blocking-task`). On the candidate it passes.
- **AE-4, named adjacent cases (8 beyond the falsification case):** missing `owner_ref`; malformed
  `owner_ref` (not 40-hex); well-formed but **unreachable** `owner_ref` (mechanical check, not just
  format); short `proof_summary`; missing `proof_summary`; `owner_ref`/`proof_summary` present on a
  non-`proven-closed` kind (rejected); `expires_after_task`/`expires_on` **absent** for `proven-closed`
  (now permitted, previously would have been required); `expires_after_task` **present and terminal**
  for `proven-closed` (waived, per CON-02 covering both fields).
- **AE-5:** not triggered. No set/sequence invariant (dedup/union/closure/multiplicity/ordering) is
  asserted by this change — it is per-entry classification logic, not a claim about the disposition set
  as a whole.
- **AE-6:** additive only — no existing test, check, or requirement was removed or weakened; the digest
  match path and the two other kinds' behavior are byte-for-byte unchanged.

**Test evidence:** `_src/tests/test_automation_safety.py`, git-backed fixture (`AutomationSafetyProvenClosedTests`,
11 new cases, real `git init`/`commit` per test, not mocked, so `owner_ref` reachability is genuinely
exercised). Full file: **136/136 passed**. `python3 -m py_compile` clean on both changed files.

## Scope item 2 — migration of the 33 `owner_task: 0038-16` entries

Commit `fbe35fe031048d90d63dfe895b8bc9fd1512e5ea` on this branch. Full per-entry reasoning is in that
commit's message; summary:

- **13 migrated** to `proven-closed`, because their existing rationale already documented real,
  independently re-checkable proof rather than deferred work:
  - 1 entry (`_src/tools/sync_to_devel.sh` `AUTO001`): `owner_ref`
    `92ab55f49e19025b543fedce8627c9f7fac64815` (Task `0038-14`'s fault-injection proof commit).
  - 12 entries (`runner-host/run-loop.sh`: 9×`AUTO001`, 2×`AUTO006`, 1×`AUTO002`): `owner_ref`
    `3a6e73620f52fb3e0faa54a53f2ccd250a044409` (Task `0038-28`'s substantive re-verification commit).
  - Both `owner_ref` values independently confirmed reachable via `git cat-file -t` before use, not
    merely copied from the rationale text.
- **20 left untouched** (still correctly failing the terminal check), because their rationale documents
  genuinely open work, not proven safety:
  - 6 entries (`bootstrap_instance.sh`×3, `publish_public_site.sh`×3): rationale says a Task "owns
    replacement of"/"owns proving" — future remediation, not proof.
  - 5 entries (`provision_tmp_worktree.sh`, `AUTO001`): rationale says a Task "still owns classifying and
    hardening" — open work.
  - 9 entries (`runner-host/run-loop.sh`, `AUTO010`): each rationale contains an explicit "Dead-deferral
    correction" admitting the original `0038-10` deferral was unfalsifiable, with the real remediation
    "carried forward... into the `0037-46.01` typed-action queue" — i.e., openly still-unresolved.
    Migrating these would be exactly the rubber-stamp DEC-0038-007 exists to prevent.

**Verified with the actual tool, not by inspection alone:** `python3 _src/tools/automation_safety.py
--json` against this candidate: `verdict: FAIL` (expected — 20 genuinely open findings remain
undispositioned, correctly so), `policy_errors: 66 → 40` (all 40 remaining are exactly the 20
correctly-untouched entries × 2 checks each), `unresolved_critical: 22 → 11`, `disposed_critical: 2 →
13`. Full test suite rerun after migration: 136/136 passed.

## Scope item 3 — Seven's `0039-01` `AUTO010` case (`_src/tests/test_derive_tk2_measurement_population.py`)

**Not migrated. Investigated and the evidence does not hold up under my own check — reported rather than
forced, per the dispatch's own explicit instruction.**

The referenced test file does not exist on `main` (confirmed: `git ls-tree main` has no such path). It
exists only on the unmerged local branch `0039-01` (Seven's own reserved-but-not-yet-started Task per
`TODO.md:449`; read-only `git grep`/`git ls-tree` on that branch, without checkout or merge, confirmed
Wesley's diagnosis is real and does live there — `TODO-seven-0039-01-20260824T091500Z.md` and
`docs/dossiers/0039-01-effectiveness-measurement.md`). Since `_validate_dispositions` matches disposition
entries against the live scanner's `finding_keys` computed from the **current working tree**, and this
item's branch is based on `main` (which lacks the file entirely), any disposition entry naming that path
would immediately fail `POLICY_STALE` — there is no finding for it to match. Beyond the mechanical
failure, adding a policy entry that names line numbers/content from an unmerged, unreviewed branch would
pre-commit to specifics of work that hasn't landed and could change before it does.

**Disposition:** left for whoever merges/completes `0039-01` to add the disposition (with real `owner_ref`
pointing at whatever commit contains Wesley's diagnosis, once that diagnosis and the file it describes are
actually on `main`). Not migrated, not forced, not touched.

## Explicitly not done

No edit to `docs/dossiers/dec-0038-007-automation-safety-proven-closed.md` (governance artifact, main-only,
out of scope). No `main` advance. No `DONE.md` move. No Acceptance claimed for this or any other item. No
mutation of branch `0039-01`. No weakening of `POLICY_STALE` or omission of `owner_ref` reachability
verification (F-R2-03).
