# Task `0040-10` — automation-safety scope and finding dispositions

**Task:** `0040-10`
**Implementation baseline:** `0a193b758`
**Decision timestamp:** `2026-08-18T14:13:07Z`
**Automation role under review:** privileged host bootstrapper and run loop
**Resolved path in this worktree:** `_src/run-loop.sh`

## Identity and provenance

- **Decision identity:** owner token `agent:zed:0040-10:20260818T141307Z-894c3cd8b63b`, acting as privileged Project Manager and implementation coordinator.
- **Implementation identity:** delegated non-privileged subagent session `6d9ae83a-8d45-479a-9807-13f22b8745a5`, acting only in the Implementer role inside the isolated worktree.
- **Validation identity:** the same delegated Implementer session ran the retained static scans, syntax checks, and focused tests. Validation is evidence, not Acceptance.
- **Peer-review identity:** independent non-privileged subagent session `4a1ba28c-5be3-4ba5-94b8-1d856337844f` reviewed the implementation and supplied remediation findings. This was an implementation peer review, not a mandatory checkpoint review and not Acceptance.
- **Acceptance identity:** none. Neither the decision owner, delegated Implementer, validator, nor this remediation record claims `Acceptance: ✓`.

## Scope and method

This Task repaired and classified the automation-safety findings attributed to
`_src/run-loop.sh` and, during peer-review remediation, updated policy-only baseline
dispositions for the two provisioners without editing either provisioner source. It did
not execute the run loop, install packages, access the network, activate services,
mutate host configuration, run Git, edit backlog or claim state, or change the foreign
`0038-24` work unit. The `0038-24` relocation to
`runner-host/` remains separate: a later path move must rebind these exact path/line/hash
dispositions, but must not remove the bootstrapper from static safety coverage.

The pre-change worktree scan is retained at
`logs/validate-automation-safety/0040-10/pre-change-run-loop.json`. It reported exactly
21 findings: 10 unresolved critical findings and 11 high advisories, with no policy
loaded. The final exact-path scan is retained at
`logs/validate-automation-safety/0040-10/final-run-loop.json` and reports 21 exact
dispositions, zero unresolved critical findings, and zero policy errors.

## TK-2 decision record

### `DEC-0040-10-001` — keep the privileged host bootstrapper in static automation-safety coverage

- **Status:** decided and implemented; not accepted.
- **Decision timestamp:** `2026-08-18T14:13:07Z`.
- **Deciding identity:** owner token `agent:zed:0040-10:20260818T141307Z-894c3cd8b63b`, acting as privileged Project Manager and implementation coordinator.
- **Implementation delegation:** non-privileged subagent session `6d9ae83a-8d45-479a-9807-13f22b8745a5`, acting as Implementer. The delegate implemented and validated the bounded work but did not make the TK-2 decision and has no acceptance authority.
- **Peer review:** independent non-privileged subagent session `4a1ba28c-5be3-4ba5-94b8-1d856337844f` supplied implementation-review findings. This remediation addresses those findings without treating that review as a mandatory checkpoint decision or claiming acceptance.
- **Trigger:** TK-2 applies because excluding or globally weakening the gate would affect every automation work unit, not only Task `0040-10`.
- **Subject:** whether privileged host-only automation should remain within `_src/tools/automation_safety.py` static scan coverage.
- **Decision:** keep the privileged host bootstrapper in the tracked Python/shell scan regardless of its current or future directory. Do not add a `runner-host/**` exclusion, do not exclude `_src/run-loop.sh`, and do not weaken the scanner's sticky fail-closed function-declaration boundary. Repair demonstrably unchecked result handling in the script, then use only exact path/rule/line/symbol/evidence-hash dispositions for conservative findings. Every disposition expires with open Task `0038-10`.
- **Technical justification:** host privilege increases the consequence of unchecked cleanup, installation, key initialization, shell execution, and false PASS output. Directory relocation changes neither those effects nor their failure modes. The scanner's conservative shell model cannot prove all function invocation contexts, but its exact evidence digest ensures any command or aggregate change invalidates the recorded judgment. Task `0038-10` already owns the durable immutable attempt-result contract that resolves the remaining `AUTO010` lifecycle debt.
- **Compensating controls:** explicit nonzero handling in `_src/run-loop.sh`; one entry per exact finding; no globs or directory suppressions; expiry on `0038-10`; retained before/after JSON; `bash -n`; focused policy and scanner tests; and mandatory re-scan after a path move or source-byte change.

### Alternatives considered

1. **Exclude privileged host code, or exclude a future `runner-host/**` subtree. Rejected.** This would make the gate green by hiding the highest-impact automation and would let a file move silently erase safety coverage. It also conflicts with the recorded `0038-24` interaction, which states that relocation does not remediate the findings.
2. **Weaken function handling globally so explicit-looking local branches are trusted. Rejected.** The scanner documentation and fixtures deliberately fail closed because aliases, groups, conditionals, caller contexts, and multiline invocation forms can suppress shell `errexit`. A global relaxation would create false negatives in unrelated automation.
3. **Rewrite the complete host runner into a new transaction architecture in this Task. Rejected.** That exceeds the bounded repair, conflicts with the foreign relocation scope, and duplicates Task `0038-10`'s immutable result contract. It would increase change risk while the live gate is blocked.
4. **Chosen: repair real status gaps and bind every remaining finding exactly.** This restores a checkable gate without pretending that high-risk lifecycle debt is complete.

### Consequences

- The host bootstrapper remains scan-visible at any tracked `.sh` path.
- A command, line, symbol, path, or complete aggregate evidence change makes its policy entry stale and blocks validation.
- The nine `AUTO010` high findings in the 21-item run-loop set remain explicitly owned lifecycle debt, not declarations of durable safety.
- The two `AUTO006` findings are accepted only for the exact confirmation/batch-gated official Homebrew installer invocations.
- `0038-10` completion expires all 21 entries; that Task must remove or re-authorize them against its immutable result implementation.
- A later `0038-24` move updates paths and exact identities only after rescanning final moved bytes; this Task does not move files or claim that scope.

## Individual finding dispositions

`Pre` identifies the finding captured before this Task. `Final` identifies the exact
post-fix finding bound in `_src/tools/automation_safety_policy.json`.

| ID | Rule / severity | Symbol | Pre line / evidence SHA-256 | Final line / evidence SHA-256 | Individual disposition |
|---|---|---|---|---|---|
| C1 | `AUTO001` critical | `<module>` | `398` / `b3b639f003fe1a0b578f75661b3fa5e8a76c23851b06be1ed46ba32a786ae621` | `425` / `73115cd7ee7309e03fb6d2668e86efd0d899928db2c9a6639c0be4f26b1f0a51` | **Fixed + narrow suppression.** Setup, self-test mutations, logging, execution pipelines, and archival now have explicit failure paths; both pipeline statuses are aggregated. The remaining finding is the intentional sticky function-boundary false positive. |
| H1 | `AUTO010` high | `<module>` | `398` / `b3b639f003fe1a0b578f75661b3fa5e8a76c23851b06be1ed46ba32a786ae621` | `425` / `73115cd7ee7309e03fb6d2668e86efd0d899928db2c9a6639c0be4f26b1f0a51` | **Blocking Task `0038-10`.** Mutable logs/counters do not yet form an immutable operation-linked attempt and recovery record. |
| C2 | `AUTO001` critical | `cleanup_runner_state` | `495` / `d9d09988e682dd37fab84fdcf6600091ba827ab0eccddfc4669b8cc1e7fb907c` | `413` / `fe2df92e4fef4b1c124d76fea54cdf6908d7c9d80ccbc3e33bb3be7aef2f76ec` | **Fixed + narrow suppression.** The handler is defined before setup and armed immediately after temporary-directory creation; it conditionally resumes AppleScript only when that function exists, preserves an existing nonzero status, and makes cleanup-only failure nonzero. |
| H2 | `AUTO010` high | `cleanup_runner_state` | `495` / `d9d09988e682dd37fab84fdcf6600091ba827ab0eccddfc4669b8cc1e7fb907c` | `413` / `fe2df92e4fef4b1c124d76fea54cdf6908d7c9d80ccbc3e33bb3be7aef2f76ec` | **Blocking Task `0038-10`.** Cleanup lacks an immutable attempt-linked outcome. |
| C3 | `AUTO001` critical | `install_homebrew` | `705` / `98d566f540fa982407d3e983e171a826174e3028c26ebb3bd1961226ceefbdd0` | `737` / `471634bda72a8addd6478eee90cd8ab62f9ca58a859e2db0dc1410b4c9b2beb9` | **Fixed + narrow suppression.** Both installer-file cleanup paths are checked; failed post-install cleanup forces the aggregate install status nonzero. |
| H3 | `AUTO010` high | `install_homebrew` | `705` / `98d566f540fa982407d3e983e171a826174e3028c26ebb3bd1961226ceefbdd0` | `737` / `471634bda72a8addd6478eee90cd8ab62f9ca58a859e2db0dc1410b4c9b2beb9` | **Blocking Task `0038-10`.** Installer cleanup has no immutable phase result/recovery state. |
| H4 | `AUTO006` high | `install_homebrew` | `710` / `173f83a785b01ae0dd54ef650099f2f119d4ab413ce74a00e5a855efa586461f` | `744` / same digest | **Narrow suppression.** Exact `/bin/bash` invocation of the downloaded official installer in explicit `--init --batch`; result feeds `install_status`. |
| H5 | `AUTO006` high | `install_homebrew` | `715` / `a2e305bc60c95032285f8149280d9bbce7e1e63ef6e48ba8f0d2ff99c5067dd6` | `749` / same digest | **Narrow suppression.** Exact interactive `/bin/bash` invocation is `--init` and terminal-confirmation gated; result feeds `install_status`. |
| C4 | `AUTO001` critical | `brew_install_or_upgrade` | `790` / `ecfbd0585fe2ae0f280ce417f211ab80fb8d43db1d03a50c9aa74d039a14a1d2` | `828` / `7d5554b45adb3988c4ee82bb32fecc6f6cc771c9115a448883f2d6495bd4c95a` | **Fixed + narrow suppression.** Install/upgrade branches now return nonzero immediately and return zero only after success. |
| H6 | `AUTO010` high | `brew_install_or_upgrade` | `790` / `ecfbd0585fe2ae0f280ce417f211ab80fb8d43db1d03a50c9aa74d039a14a1d2` | `828` / `7d5554b45adb3988c4ee82bb32fecc6f6cc771c9115a448883f2d6495bd4c95a` | **Blocking Task `0038-10`.** Host package mutation lacks an immutable phase result and retry identity. |
| C5 | `AUTO001` critical | `install_python_package` | `796` / `ebd5b252474ab7b740ccf444249ac5ac1e4fd538760d16ccd5bfdcf06e870b6b` | `836` / `3698bb66d4ea65802acd9e724ef340611b656b4748d7052fe1694f7902d03c7e` | **Fixed + narrow suppression.** Isolated pip installation now has explicit failure and success returns. |
| H7 | `AUTO010` high | `install_python_package` | `796` / `ebd5b252474ab7b740ccf444249ac5ac1e4fd538760d16ccd5bfdcf06e870b6b` | `836` / `3698bb66d4ea65802acd9e724ef340611b656b4748d7052fe1694f7902d03c7e` | **Blocking Task `0038-10`.** The isolated package mutation lacks immutable phase/retry state. |
| C6 | `AUTO001` critical | `initialize_github_key` | `802` / `e3a61b9637f005618f15a8b44127f531806a508e1b739015d188de3f7f032bc8` | `845` / `232a335a4d6ca3438657b790382b5653f8abb9b86b94dd86c8a64b4ec4c6b730` | **Fixed + narrow suppression.** Directory creation and both permission mutations now use explicit checked branches and nonzero returns. |
| H8 | `AUTO010` high | `initialize_github_key` | `802` / `e3a61b9637f005618f15a8b44127f531806a508e1b739015d188de3f7f032bc8` | `845` / `232a335a4d6ca3438657b790382b5653f8abb9b86b94dd86c8a64b4ec4c6b730` | **Blocking Task `0038-10`.** Key initialization lacks immutable operation-linked outcome and recovery evidence. |
| C7 | `AUTO001` critical | `install_playwright_module` | `843` / `1fd8c8fb8ae3c3863490068864fa9668f5b819583654ea560bc83098aaa9d40a` | `894` / `f5695dba427b6011da679e5c8b797d84fa21dbfefa610f2287634d990d27ab19` | **Fixed + narrow suppression.** Version-pinned prefix-local npm install now has explicit failure/success returns. |
| H9 | `AUTO010` high | `install_playwright_module` | `843` / `1fd8c8fb8ae3c3863490068864fa9668f5b819583654ea560bc83098aaa9d40a` | `894` / `f5695dba427b6011da679e5c8b797d84fa21dbfefa610f2287634d990d27ab19` | **Blocking Task `0038-10`.** npm mutation lacks immutable operation-linked phase and retry state. |
| C8 | `AUTO001` critical | `install_playwright_webkit` | `847` / `e00c09cf37d49c10c42002a05fd7445c06facb85a239f5d967580c83bbe0349d` | `901` / `00ae31da8ad088d4ad959b4e484912201c7e40a947983cf1722b56a3df8768c3` | **Fixed + narrow suppression.** Prefix-local browser installation now has explicit failure/success returns. |
| H10 | `AUTO010` high | `install_playwright_webkit` | `847` / `e00c09cf37d49c10c42002a05fd7445c06facb85a239f5d967580c83bbe0349d` | `901` / `00ae31da8ad088d4ad959b4e484912201c7e40a947983cf1722b56a3df8768c3` | **Blocking Task `0038-10`.** Browser mutation lacks immutable operation-linked phase and retry state. |
| C9 | `AUTO001` critical | `record` | `1070` / `e6d29a266993eb6d0f7e07cdc75b054334d79594a79787f90c1893b12012cec1` | `1130` / `89fc22f40a918e725d97eb8c637d05832a55626dafc62c0b25fe3f2434dc138d` | **Fixed + narrow suppression.** Detail cleanup/copy failures append fail-valued self-test records and therefore force the generated self-test nonzero. |
| H11 | `AUTO010` high | `record` | `1070` / `e6d29a266993eb6d0f7e07cdc75b054334d79594a79787f90c1893b12012cec1` | `1130` / `89fc22f40a918e725d97eb8c637d05832a55626dafc62c0b25fe3f2434dc138d` | **Blocking Task `0038-10`.** The mutable self-test log is not yet an immutable operation-linked result. |
| C10 | `AUTO002` critical | `<module>` | `1224` / `5a1ce8dd302e0c1e4dbb37e4b17c37398d38871da7b2ee4ceec8afd9c0592b25` | `1334` / `dfa85c3c59c6b60b8a560fcfabfa596f1aa27ec2cdb7ea1f42495994e6386007` | **Fixed + narrow suppression.** Process, fail-log, and cleanup statuses form one aggregate; any nonzero prints FAILED and exits before PASS. |

## Current-baseline findings discovered by the full scan

These are separate from the exact 21-item run-loop set. Peer review authorized only
policy and evidence changes for them; neither provisioner source was edited.

| ID | Path / rule / severity | Exact identity | Disposition and owner |
|---|---|---|---|
| B1 | `_src/tools/provision_tmp_worktree.sh` / `AUTO001` critical | line `41`, `<module>`, `e460b86b406a54658989c2017713330f0ea889d7fa2682d11157c97751c40133` | **Refreshed blocking disposition, `0038-14`.** The source is explicitly `SUPERSEDED`; its retained branch/prune/ignored-repair/delete/worktree-add aggregate remains legacy mutator debt until `0038-14` classifies or retires it. The prior policy line `27` was stale after the explanatory header expanded. |
| B2 | `_src/tools/provision_worker_clone.sh` / `AUTO001` critical | line `86`, `<module>`, `1d26f6ffd567197b8cd9b1c279c6660aa1ffa83108c3468be5bcb03e2b2887b7` | **Narrow suppression, `0041-05`.** The privileged clone provisioner retains the scanner's fail-closed module/function-boundary finding; the exact branch/rebuild aggregate stays behind refusal gates and must be exercised by Feature integration/e2e. |
| B3 | `_src/tools/provision_worker_clone.sh` / `AUTO010` critical | line `86`, `<module>`, `1d26f6ffd567197b8cd9b1c279c6660aa1ffa83108c3468be5bcb03e2b2887b7` | **Blocking disposition, `0041-05`.** Branch creation and destructive target rebuild lack an operation-linked durable lifecycle/recovery result; `0041-05` owns the integrated end-to-end disposition. |

The superseded provisioner's same evidence also emits an undispositioned high
`AUTO010` advisory. It remains machine-visible and owned conceptually by `0038-14`;
it was not one of the three full-scan blockers because it creates neither an unresolved
critical nor a policy error.

## Code changes behind the dispositions

- Runner directory creation and permissions fail explicitly.
- `cleanup_runner_state` is defined before setup and its traps are armed immediately after successful `RUNNER_TMP_DIR` creation, closing the early-exit leak window.
- Early cleanup checks whether `resume_applescript` is defined before calling it, preserves an existing nonzero status, and converts cleanup-only failure to exit `1`.
- Homebrew installer cleanup participates in the installation result.
- Homebrew, pip, Playwright module, WebKit, and SSH key setup wrappers return explicit success/failure.
- Self-test detail cleanup/copy failures enter `SELFTEST_FAILURES`.
- The outer self-test aggregates process, fail-valued log, and generated-script cleanup statuses; execution cannot continue after a failed self-test and PASS is printed only for aggregate zero.
- Runner log pipelines capture both `PIPESTATUS` members; log-writer failure can no longer be hidden by a successful run script.
- Setup, links, archival, counter writes, and sandbox-profile refreshes have explicit fatal paths.

## Validation evidence and limitations

| Validation | Result | Retained evidence |
|---|---|---|
| `bash -n` on `_src/run-loop.sh` | PASS | command result; no output |
| Exact worktree `_src/run-loop.sh` scan with the 21-entry policy subset | PASS: 21 findings, 10 disposed critical, 0 unresolved critical, 0 policy errors | `final-run-loop.json`; `run-loop-policy.json` |
| Focused run-loop plus two-provisioner scan | PASS: 25 findings, 13 disposed critical, 0 unresolved critical, 0 policy errors, 1 undispositioned high advisory | `remediation-focused-scan.json`; `remediation-focused-policy.json` |
| Worktree-byte full automation scan with final policy | PASS: 71 findings, 35 disposed critical, 0 unresolved critical, 0 policy errors | `final-worktree-full-scan.json`; `final-policy.json` |
| Policy unit-test class | PASS: 4 tests | `policy-tests.txt` |
| Targeted evidence-identity and sticky function-boundary tests | PASS: 3 tests | `targeted-scanner-tests.txt` |
| Source/policy/report/dossier consistency checker | PASS: early trap ordering, status behavior, exact identities, 9 run-loop `AUTO010`, 3 baseline blockers, provenance, and retained-policy byte equality | `remediation_consistency_check.py`; `consistency-checks.txt` |
| Initial live dual-source scan before privileged staging | Expected FAIL: 10 unresolved critical, all from old indexed `_src/run-loop.sh`; 0 policy errors and no remaining provisioner blockers | `final-full-scan.json`; `final-policy.json` |
| Final live dual-source scan after privileged path-limited staging | **PASS:** 71 findings, 35 disposed critical, 0 unresolved critical, 0 policy errors | `post-stage-full-scan.json` |

The delegated non-privileged Implementer was explicitly forbidden to run Git, stage, or
commit, so its initial live scan honestly retained the old indexed run-loop variant. The
privileged owning session subsequently staged only the declared Task paths and reran the
default dual-source scanner against the exact final policy. That retained run passed with
zero unresolved critical findings and zero policy errors. Validation is not acceptance, and
no `Acceptance: ✓` is claimed.
