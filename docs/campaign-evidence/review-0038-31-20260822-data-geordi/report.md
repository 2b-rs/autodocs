# Independent integration-checkpoint re-review — Task 0038-31

- **Verdict:** `accepted`
- **Reviewer:** `Data-Geordi-20260822T203511Z`, persona Geordi, privileged Integrator
- **Dispatcher:** Data
- **Reviewed candidate:** branch `0038-31`, exact tip `7ab79af32ec3d1fd83964049b773cad9e8c077e4`, tree `7e84c95be040b8f81f90b4679422a403fb0ff772`
- **Substantive correction:** `94bab196df7786f57e97994dd73f822cb50556e0`, tree `4439f02bdabea363331573f028a0c1b6915b3258`
- **Correction parent:** `0c669200b2120fdf95193851fa60001756171773`, tree `9a4302a058ae59ce00f5b558c0583858d5b566df`
- **Prior rejected review:** `0db2a4fd9de266519c3aea75845256588126f137`; report `docs/campaign-evidence/review-0038-31-20260822/report.md`
- **Review branch/worktree:** `review-0038-31-data-geordi-20260822T203511Z`; `.review-worktrees/0038-31-data-geordi-20260822T203511Z`
- **Exact-candidate validation worktree:** detached `/tmp/autodocs-review-0038-31-data-geordi-candidate`
- **Authority epoch at decision:** `main@0d04432d6a4c6ae7f67a7818c6b9ab93266a527d`; the newly effective `DEC-CAP-003` was read and does not affect this read-only product review.

## Decision

The corrected candidate satisfies the Task contract. The prior major finding is closed: the line-collision case now preserves the maximum multiplicity, and independent tests show that the construction is general rather than a one-case patch. No existing finding is lost, suppressed, reclassified, or hidden on a clean tree. The mandatory checkpoint remains confirmed; this review does not downgrade or move it.

No critical, major, or minor finding remains. One observation is recorded below. No candidate fix, Feature/main integration, `DONE.md` move, push, runner operation, external mutation, or root-checkout write occurred.

## Pinned contract and manifests

The normative contract was read from current authoritative `TODO.md@0d04432d6a4c6ae7f67a7818c6b9ab93266a527d`; its imperative, prerequisite, acceptance criteria, Definition of Done, and mandatory-checkpoint paragraph are byte-equivalent to the candidate's normative text. Canonical JSON uses UTF-8, sorted keys, and compact separators.

- **Contract SHA-256:** `5333dc95dfb6b48dc4b9e1968506f10fb9d03dff860ee1c9caaa03ea96b72067`
- **Work-product manifest SHA-256:** `3b280ec5e9b2072e153355f1004c850bfb455b228028f427cfa56f8bd6d36e74`
- **Prerequisite-acceptance SHA-256:** `70d563a79cfe6134a8cbefd7d6819d5f1fbf2a8c5914dd886d877589785a2d8d`

Work-product population at the exact candidate:

| Path | Role | Bytes | SHA-256 |
|---|---:|---:|---|
| `_src/tools/automation_safety.py` | implementation | 122251 | `5616d4506c753e2ba74cfbed1c99be94f6b6a6b566b9199515c96204f5b4cb5d` |
| `_src/tests/test_automation_safety.py` | validation | 72042 | `b2048522c4aafbfb070ebba2b9ad3d002b04a328e015699db6f5e95757bdcd6c` |
| `docs/pipeline/automation-safety.md` | normative documentation | 22370 | `ffba6671fb08baa16f1ee743aa91a34954f8a7f2c02b009386c0979e881fc317` |

The original implementation commit `5aebcd2a7c3cb2e832414cfb5bfcb5d53e11f825` changes only these three work products. The corrective substantive commit changes only the implementation and test work products (22 and 64 changed lines respectively). The final candidate adds only append-only claims and Task bookkeeping after that substantive commit. `automation_safety_policy.json`, the disposition mechanism, and `_src/validate.py` are unchanged by the Task.

## Prerequisite closure

The parsed transitive closure is acyclic and has no missing endpoint. Direct prerequisite `0038-14` expands to 29 predecessor Tasks/Subtasks and 54 edges, ending at `0037-48` and `0038-01`. Every predecessor is `[x]`, present in the exact candidate, and unflagged as an integration checkpoint; therefore the attribute-driven target policy has no predecessor `Acceptance: ✓` boundary to require or fabricate. The closure was reviewed bottom-up for terminal state, checkpoint state, endpoint existence, edge direction, and candidate reachability before the target review. Direct predecessor `0038-14` and its scanner/policy foundation are exercised again by the live gate and full scanner suite below.

The digest above binds the complete sorted edge set and all 29 rows as `state=x`, `checkpoint=false`, `acceptance_record=false`; `accepted_boundaries` is the empty set. This follows the repository's checkpoint-only acceptance policy and the existing accepted `0038-26` precedent for the same direct predecessor; it does not invent acceptance for unflagged work.

## Independent red-before-green proof

I loaded the exact old implementation from correction parent `0c669200b...` and the corrected implementation from `94bab196...` as separate modules, then ran each against fresh hermetic Git repositories created under `tempfile.TemporaryDirectory`. The harness is reviewer-authored and does not import the submitted test class.

| Case | Old | Corrected | Expected |
|---|---:|---:|---:|
| New copy precedes existing content; Index 1 / Worktree 2; second worktree occurrence collides with index line 6 | **1** | **2** | 2 |
| Worktree copy follows existing content | 2 | 2 | 2 |
| Index 2 / Worktree 1 | 2 | 2 | 2 |
| Two distinct symbols in one file, each with Index 1 / Worktree 2 and its own line collision | **2** | **4** | 4 |

For the required F1 case, both occurrences have evidence SHA-256 `93822c714c83f05b94691cadf438406b3d5cb553660ae8bf4877ffe4c21f1e76`. Old output is only index line 6; corrected output is lines 5 and 6. For the two-group case, old output loses one occurrence in each of `danger_a` and `danger_b`; corrected output retains lines 5/6 and 10/11.

The construction is general. For each code-site key, the algorithm keeps the earliest variant's representatives, then adds exactly `m-k` occurrences from a later variant of size `m>k` while excluding already-kept lines. Each individual variant has distinct lines after within-variant deduplication; therefore at most `k` of its `m` lines collide, leaving at least `m-k` fresh lines. A deterministic property run covered 10,000 randomly generated cases with one to four variants, multiplicity zero to eight, and overlapping lines; after the downstream line-bearing dedupe, every case retained exactly the maximum per-variant multiplicity and all earliest-variant representatives.

## Validation

- `python3 -m unittest _src.tests.test_automation_safety.IndexWorktreeVariantMergeTests -v` — **14/14 passed**, 85.050s.
- `python3 -m unittest _src.tests.test_automation_safety -v` — 135 tests, exactly one failure: `test_current_safe_aggregate_controls_do_not_regress`, reporting `_src/tools/runner_transaction.py: ['AUTO010']`. The `runner_transaction.py` blob is identical before the original implementation, after it, before the correction, and after it (`f3363db43add9a8dc8937def065a853d70daac3e`); this is the pre-existing `0038-33` failure and is neither caused nor hidden here.
- `python3 _src/tools/automation_safety.py --json` — exit 0, `PASS`, scanned files 109, findings 73, advisory 38, disposed critical 24, unresolved critical 0, policy errors 0; sources `authoritative=index`, `also_scanned=[worktree]`, no divergent path.
- Whole-population clean-tree comparison, old module `0c669200b...` versus corrected `94bab196...` on the same exact candidate tree — both have the preceding counts and identical canonical finding-identity-set SHA-256 `74a1ebcd5dcb256cbc0e811c79d70f420b81e062431eef6414996642a430d215` over `(path,line,rule,symbol,evidence_sha256,severity,status)`.
- Direct `_src.validate.check_automation_safety()` integration invocation — one check performed, zero structured findings and zero errors. The additive `sources` block remains transparent to the consumer, which reads only policy errors and unresolved critical findings.
- `python3 -m py_compile _src/tools/automation_safety.py _src/tests/test_automation_safety.py` — passed.
- `git diff --check 0c669200b...94bab196...` — passed.
- Candidate commit/tree connectivity and all inspected diffs — passed; exact-candidate tracked worktree remained unchanged.

## Findings and observations

- Prior `F1` (major): **closed**. The old position-based top-up selected a colliding occurrence that downstream dedupe removed; the corrected collision-free top-up retains maximum multiplicity.
- `O1` (observation, non-blocking): the submitted `test_new_uncommitted_copy_colliding_after_the_index_line_keeps_both` docstring says its first worktree occurrence collides with the index line, while the actual fixture and inline comment correctly place the index at line 5 and worktree occurrences at lines 6/7 (no collision). The test still correctly covers the required “copy after existing” neighbor, and the discrepancy affects neither behavior nor assurance.

## Authority, independence, and DEC-0044-013

- **Dispatching identity:** Data.
- **Reviewer persona:** Geordi, privileged Integrator, session `Data-Geordi-20260822T203511Z`, distinct from both Data and implementer `Harry-Dax-20260822T183800Z`.
- **Context given:** exact candidate/substantive/prior-review identities and paths; the prior rejected report; the required F1 red-before-green geometry and three neighboring cases; the instruction to inspect all changes and rerun focused/full validation; exact review branch/worktree and write/authority limits; the mandatory verbatim-briefing record.
- **Context not given:** no expected acceptance verdict; no implementer session access; no unpublished implementation rationale or validation result beyond repository artifacts; no precomputed digest or closure answer; no permission to repair the candidate, integrate it, move `DONE.md`, push, or alter `main`.
- **Conflicts:** none. The reviewer is not the claim owner, principal implementer, decisive technical author, or sole validation producer. No waiver is used.

### Verbatim briefing

```text
You are Data-Geordi-20260822T203511Z. Explicitly assume persona Geordi, privileged Integrator, independent from implementer Harry-Dax-20260822T183800Z and dispatcher Data. Keep all reports concise and in English. Announce to agent-inbox as `Data-Geordi-20260822T203511Z`, role `Integrator`, runtime `zed/gpt-5.6-sol`; check inbox at start and before each consequential action. Direct Git/tests only; never runner/run.sh.

Assignment: independent privileged re-review of Task 0038-31 after prior rejection. Candidate branch `0038-31`, exact tip `7ab79af32ec3d1fd83964049b773cad9e8c077e4`, substantive `94bab196df7786f57e97994dd73f822cb50556e0`. Prior rejected review REF `0db2a4fd9`; report is `docs/campaign-evidence/review-0038-31-20260822/report.md` in worktree `.review-worktrees/0038-31-kolos-20260822T153500Z`. Read AGENTS.md, SANDBOX.md, TODO.md, task-acceptance.md, process roles, exact Task contract, prior report, candidate claim/diffs/tests. Pin exact baseline, contract/digests, transitive non-accepted prerequisite closure, and review bottom-up.

Critical verification: independently prove the red-before-green regression for Index 1 / Worktree 2 where the new copy precedes existing content and line numbers collide (expected old behavior 1 finding vs correct 2). Then test neighboring cases: worktree copy after existing, Index 2 / Worktree 1, and multiple colliding code locations in one file. Determine whether the construction is general or merely patches one case. Inspect all candidate changes and rerun relevant full/focused suites.

Create branch `review-0038-31-data-geordi-20260822T203511Z` and isolated review worktree `/Users/tobias.anton/devel/autodocs/.review-worktrees/0038-31-data-geordi-20260822T203511Z` from current main. Mandatory hygiene and root hard preflight before mutation. Initial write scope exactly `docs/campaign-evidence/review-0038-31-20260822-data-geordi/report.md` and `TODO-Data-Geordi-0038-31-review-20260822T203511Z.md`; if and only if accepted, a separate path-limited TODO.md Acceptance bookkeeping commit with real review REF/digests. No product/candidate fixes, no main/Feature merge, no DONE.md, no push.

DEC-0044-013 record requirement: reproduce THIS ENTIRE BRIEFING verbatim in the report; record dispatching identity Data, reviewer persona Geordi, context given and not given. Verdict append-only: accepted/rejected/inconclusive. At rejection/inconclusive, do not self-fix or integrate. Report commits, verdict, validation, findings, and any escalation to Data.
```

## Evidence metadata correction

The first evidence commit `f829b116fe87856cd65a31f19875c210e865a681` committed the correct report and claim bytes, but its message transcribed both pre-commit receipt digests incorrectly. The actual SHA-256 values printed immediately before that commit were:

- report: `125a408b2a6e61332208bf7a540ed1ff57955a1100a0c85e4060765ea76a57a6`;
- claim: `694ce194c3b76096a7f36baa2372c62e31cbba0d3ff035deba2cdce06f8c0051`.

This correction is append-only; it changes no verdict, baseline, manifest, validation result, finding, or authority statement. The correction commit is the final Review REF used by acceptance bookkeeping.
