# `0044-05` parent package-completion — corrected round (append-only)

*This record does not delete, clear, supersede, or reword
`parent-completion-report.md`, `checkpoint-review-geordi-20260825.md`, or the
`[u]` BLOCKED verdict in `TODO.md`. All three remain exactly as recorded.*

## What happened, in order

1. My original parent-completion report (`f5d75092d`) claimed "schema/tool/docs
   consistency" verified. It was not: I ran the matcher's own private Python
   validation functions and the CLI, but never checked that a committed
   instance actually validates against the **published JSON Schema files**
   using real JSON Schema semantics. That is a different, stricter question,
   and the two disagreed.
2. Privileged Integrator `geordi`, assigned the mandatory `0044-05` checkpoint
   review by `jean-luc`, reviewed exactly my candidate `1aeaed098` and found
   `F-0044-05-GEORDI-001` (major): the published schemas forbade fields their
   own committed self-application instance used (`test_scope`,
   `resource_bounds`), left `sources`/`descriptor_sha256`/`rejections` without
   `items` contracts, and forbade the `error` field every real invalid-input
   CLI result emits. **Rejected.** Review REF `5208d4b31`.
3. Implementer `gabriel` corrected the three schemas (REF `e637660978`,
   `0044-05.02`), adding the missing nested `items`/`properties`/`required`
   contracts and an `allOf`/`if`/`then` conditional requiring `error` exactly
   when `status: invalid-input` and forbidding it otherwise. Matcher logic and
   the legacy schema were not touched. 19 tests now (was 16).
4. `data` recorded the reconciliation (`6b8ff993d`); `geordi` recorded the
   required additive `[u]` BLOCKED verdict (`016bbcc94`), preserving the
   rejection and the parent `[x]` marker.
5. `jean-luc` assigned me (Implementer-only, still distinct from Architect
   `data` and Integrator `geordi`) to reconcile both the corrected schemas and
   the verdict lineage into this candidate and rerun package-completion
   validation against the corrected schemas — this record.

## Reconciliation performed

- `git merge --no-ff 016bbcc94` (verdict lineage `V`, a linear descendant of my
  own `1aeaed098` but foreign-authored — merged explicitly rather than silently
  fast-forwarded) → `669e64139`.
- `git merge --no-ff 6b8ff993d` (corrected-schema lineage `P2`, a genuine
  sibling fork off the same original parent `4468a78d1`) → `4882d2f4e`.
- Both merges clean, zero conflicts. The one real 3-way `TODO.md` merge
  (`P2`'s side) auto-resolved correctly: verified by direct inspection that my
  own package-completion sub-bullet, the `[u]` BLOCKED verdict block, and
  `0044-05.02`'s updated REF/test-count line are all present, unmodified,
  exactly once each.

## Corrected-schema validation, independently rerun

Because the environment has no third-party `jsonschema` module (confirmed
absent again here, matching the rejected review's own note), a minimal
stdlib-only structural validator was written for this exact purpose:
`validate_against_schema.py` in this directory. It implements only the
keywords these three schemas actually use. **Sanity-checked against its own
false-negative risk before trusting it:** run against the *old* (pre-fix)
schemas, it reproduces Geordi's exact finding verbatim (same forbidden-key
lists, same paths) — so a "VALID" result from it on the corrected schemas is
not a vacuously permissive validator.

| Instance | Schema | Result |
|---|---|---|
| `profile-0044-05.03.json` (existing, unmodified) | `task-requirement-profile-v1` (corrected) | **VALID** |
| `descriptor-belanna.json` (existing, unmodified) | `agent-capability-descriptor-v1` (corrected) | **VALID** |
| `result-belanna-0044-05.03.json` (existing, unmodified) | `capability-match-result-v1` (corrected) | **VALID** |
| **New:** `result-invalid-input-legacy-descriptor.json` — real CLI output (exit 2, `status: invalid-input`, `error: SCHEMA_UNSUPPORTED_LEGACY`) from feeding the matcher a legacy-shaped descriptor against the same profile | `capability-match-result-v1` (corrected) | **VALID** |
| Same invalid-input instance | `capability-match-result-v1` (**old**, sanity check) | **INVALID** — `additionalProperties=False, forbidden keys ['error']`, exactly Geordi's finding #3 |

The fourth row is new evidence this round: my original report validated only
the happy-path (`single-eligible`) result shape, never an actual invalid-input
result shape — precisely the coverage gap the rejected review names.

## Remaining checks, all rerun fresh on the reconciled tip

- `python3 -m pytest _src/tests/test_capability_match.py -q` — **19 passed**
  (matches `0044-05.02`'s corrected bookkeeping exactly).
- `python3 -m py_compile` on `capability_match.py`, `test_capability_match.py`,
  and the new `validate_against_schema.py` — clean.
- `python3 _src/tools/automation_safety.py --path _src/tools/capability_match.py
  --path _src/tests/test_capability_match.py --json` — `verdict: PASS`,
  `unresolved_critical: 0`, `policy_errors: 0`, `findings: 0`.
- Legacy schema SHA-256 `ee553404d0e859e4fdd1876edb0d4dc8d016921f92818fbd143ba4ad71870955`
  — unchanged, reconfirmed.
- `grep` for `capability_match` in `_src/generate.py`/`_src/validate.py`: none.
  No broad activation or historic-credit language found anywhere in the
  reconciled diff.
- Required non-activation sentence: still byte-identical between `AGENTS.md`
  and `docs/pipeline/capability-matching.md` after both merges.
- Product ancestry (`2c563040563b350f26e6c85b0dccb8c211fdbdef`), original main
  `M` (`5aefac853`), the schema fix (`e637660978`), corrected parent `P2`
  (`6b8ff993d`), and verdict `V` (`016bbcc94`) all independently reconfirmed
  ancestors of the reconciled tip.
- `git diff --check` — clean across the full worktree, including the two new
  evidence files this round.

## Disposition

Package-completion criteria pass again on the corrected schemas. **The `[u]`
BLOCKED verdict is not cleared by this record and cannot be cleared by an
Implementer** — per `jean-luc`'s instruction and the verdict's own text, it
requires an authorized current-user decision and a separately assigned
independent re-review. Parent `0044-05` implementation marker remains `[x]`;
no `Acceptance: ✓` is added or implied by this correction.
