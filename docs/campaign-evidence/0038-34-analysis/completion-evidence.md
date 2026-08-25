# `0038-34` — completion evidence and scope-conformance checklist

- **Implementer:** `Tom-Sisko-20260825T091500Z`, unprivileged
- **Branch:** `0038-34`
- **Pre-mutation baseline:** `0ff38ff81d42d203cc94699fdb7fcce65446ec98` (catch-up merge of `main@28d7a0091`)
- **Substantive REFs:** `53dcd0412` (projection), `72bc3b30a` (checker + fixtures), `154ebeaa8` (placement fix)
- **Governing authority:** `DEC-0038-004`
  (`docs/dossiers/dec-0038-004-adversarial-completion-evidence.md`) and the binding
  pre-mutation Architect scope review by `data`
  (`docs/campaign-evidence/0038-34-architect-scope-review.md`, verdict `supports`).

## 1. The six binding conditions from the Architect scope review

| # | Binding condition | Where satisfied | Verified how |
|---|---|---|---|
| 1 | Requirement is **claim-bound**, not role-bound | `AE-1` — applicability follows the altered behavior/contract; the block states explicitly "never by file type, by whether an implementer or a reviewer executes the case, or by whether the existing suite is green" | `test_block_is_additive_and_names_its_decision_record` asserts `claim-bound` present |
| 2 | Exact before/candidate **red-first** evidence | `AE-2` (exact baselines) + `AE-3` (red on pre-change, green on candidate, real command, bounded output or immutable reference; always-green, mock-bypass and prose each nonconforming) | fixtures `test_missing_red_baseline`, `test_always_green_negative`, `test_mocked_changed_path_is_not_conforming` |
| 3 | **At least two named neighbor cases** | `AE-4` — two *distinct* adjacent cases, each with dimension, expected, observed, why-adjacent; a case that turned out fine is a pass, naming none is not | `test_fewer_than_two_neighbors`, `test_missing_neighbor_result`, `test_two_neighbors_probing_the_same_dimension` |
| 4 | Property/generative or exhaustive evidence **only** for claimed set/sequence invariants, with oracle/domain/replay/count | `AE-5` — triggered only by the `set-sequence-invariant` class; requires invariant/oracle, generation domain or enumeration boundary, seed/replay where applicable, actual executed count; explicitly imposes no universal minimum | `test_set_claim_without_property_evidence`, `test_missing_oracle_and_domain`, `test_missing_executed_case_count`; the *only-for-set-claims* half is proven by `test_out_of_scope_bookkeeping_carries_no_obligation` (no property demand on an excluded change) |
| 5 | **Additive** to every existing authority, acceptance and checkpoint control | `AE-6` (adds to, replaces and weakens nothing, never converts an authority question into a test-only question) + `AE-7` (exclusions leave every pre-existing requirement in force) | diff is purely additive: **13 insertions / 0 deletions** in `AGENTS.md`, **14 / 0** in `TODO.md` against `0ff38ff81`; zero removed lines in either file |
| 6 | **Identical projections**, no divergent wording | One byte-identical delimited block in both files rather than two paraphrases | block SHA-256 `d6df354494cbf69fcf5d40c07667e11f8165d1f55c043099aebae8e92269aa2e` in both; `check_adversarial_evidence.py --projection` exits `0`; `test_live_repository_projections_are_identical` |

Additionally required by the scope review and satisfied: **`0044-04` is excluded from the
evidence base** and appears only in `scope-exclusions.md` §2 as the demonstration of why
the rule needs an exclusion boundary; the **worked example** uses `0038-33` for its four
independently red controls and preserves the initial `inconclusive` verdict
(`worked-example.md` §6); it uses `0038-31` for the property boundary and states that
**code reading found the defect and property testing closed it** (`worked-example.md` §5).

## 2. One-for-one normative-proposition comparison

`data`'s CON-06 requires identical normative meaning in both operative locations. The two
projections are not two texts that must be compared proposition by proposition — they are
**the same bytes**, so the comparison is exact rather than interpretive:

```
$ diff <(extract-block AGENTS.md) <(extract-block TODO.md)   # empty
$ sha256  AGENTS.md block = TODO.md block
  d6df354494cbf69fcf5d40c07667e11f8165d1f55c043099aebae8e92269aa2e
```

All eight propositions `AE-1 … AE-8` are asserted present in **both** files by
`test_all_eight_propositions_present_in_both_files`. Divergence, partial projection, and
absence from both are each detected, by `test_divergent_projection`,
`test_inconsistent_partial_projection` and `test_absent_from_both_is_reported_as_inactive`.

## 3. Validation actually run

| Check | Result |
|---|---|
| `python3 -m unittest _src.tests.test_adversarial_evidence` | **21/21 OK**, 0.16 s |
| `check_adversarial_evidence.py --projection .` | `PASS`, exit `0` |
| Malformed-input handling | exit `2`, never passes (`test_malformed_input_exits_two_and_never_passes`) |
| `process_doc_doctor.py --json` | exit `0`, 31 findings, **byte-identical finding set to the baseline — 0 new** |
| `automation_safety.py --json` | `FAIL` — **pre-existing, see §5** |
| Diff shape vs `0ff38ff81` | `AGENTS.md` 13/0, `TODO.md` 14/0, zero removed lines |
| `AGENTS.md` ordered list 1..10 | unbroken after the `154ebeaa8` placement fix |

### Fault injection — because a green suite is not evidence under this very rule

`AE-3` says a case that was always green falsifies nothing. That applies to my own
fixtures, so each rule was disabled in turn and the suite re-run:

| Rule disabled in the checker | Suite result |
|---|---|
| `AE-3` red-baseline check | **RED** (1 failure) |
| `AE-4` too-few-neighbors check | **RED** (2 failures) |
| `AE-5` property-evidence check | **RED** (1 error) |
| `AE-5` oracle/domain check | **RED** (1 failure) |
| `AE-8` divergence check | **RED** (1 failure) |
| all restored | **GREEN**, 21/21 |

## 4. Self-application: is *this* change in scope of its own rule?

Under `AE-1`, this Task's operative change to `AGENTS.md` and `TODO.md` is
**documentation-only** and therefore **excluded by `AE-7`**. The rule does not demand
red-first evidence of the commit that introduces the rule. The evidence in §3 was produced
because the **Architect scope review independently required it** for this Task, not because
`AE-1` was triggered. Recording this distinction matters: reading `AE-1` as covering its
own introduction would be exactly the ritual-compliance failure `DEC-0038-004` ALT-02
rejects.

The checker and fixtures (`72bc3b30a`) are new isolated functionality asserting nothing
about an existing set, so they too fall outside `AE-1`.

## 5. Known limits — surfaced actively for the checkpoint reviewer

1. **`automation_safety.py` returns `FAIL` on this candidate, and it does so on the
   baseline too.** 22 unresolved findings in `_src/tools/bootstrap_instance.sh` and
   `_src/tools/provision_tmp_worktree.sh`, plus 66 policy errors, all of the form
   `owner_task 0038-16 is terminal; disposition expired`. Attribution evidence: **zero
   findings in either file this Task adds**; my `TODO.md` diff touches **zero task-marker
   lines**; `_src/tools/automation_safety_policy.json` is **untouched**; and `0038-16` is
   `[w]` identically on `main@28d7a0091` and on this branch. This is the recurring
   "Task closes → dispositions expire repo-wide" class already recorded in the `AGENTS.md`
   suggestion log (2026-08-20, `agent:seven-bellana`), now triggered by `0038-16`. It is
   **not** repaired here: it is outside this Task's scope and belongs to whoever owns the
   disposition policy. A confirming baseline run at `28d7a0091` was launched; if it has
   not been reconciled into this file, the reviewer should treat the attribution above as
   the argument and re-run to confirm.
2. **The checker cannot judge adjacency or domain adequacy.** `AE-5` explicitly reserves
   "does the domain meaningfully exercise the claim" to the reviewer, and nothing
   mechanically prevents an implementer from naming two weak neighbors. The residual
   ritual-compliance risk `data` identified is **reduced, not eliminated**.
3. **`check_adversarial_evidence.py` is not wired into `_src/validate.py` or any gate.**
   It is a usable tool and a fixture harness; it does not yet run automatically, so
   nothing currently forces a completion record through it. Wiring it in would change gate
   behavior and is therefore itself an `AE-1`/`cross-item-blast-radius` change requiring
   its own decision record — deliberately not done here.
4. **`completion-evidence@v1` is introduced by this checker as a JSON shape and is not
   yet a registered repository schema.** No existing completion record uses it. It is the
   checker's input format, not a mandated authoring format; `AE-1..AE-8` are prose
   requirements and can be satisfied in prose, as this very document does.
5. **Incident during this Task, disclosed in full:** a `git stash` / `git stash pop` pair
   run from this worktree popped a **pre-existing foreign stash entry** into this
   worktree's index (~16,900 paths), because the stash stack is **repository-wide and
   shared across worktrees**, not per-worktree. Recovery: `git reset --hard 154ebeaa8`.
   Verified afterwards — all three stash entries still present and undropped, working tree
   clean, `git status --porcelain` empty, 21/21 green, no foreign content committed, no
   other worktree and not the root checkout written to. The one measurement invalidated
   was an `automation_safety` run that had executed against the contaminated tree; it was
   discarded and re-run. See the claim's progress log and the suggestion appended to
   `AGENTS.md`.
