# Feature-Abschluss ASPICE Batch 2

**Act:** aggregierter Feature-Abschluss für Features `0016`, `0017`, `0018` und `0019`.
**Date:** 2026-09-29.
**Integration tip before this act:** `3170be4607490cbdac3661a0dbd4eba781489d5c` (`task-hk-aspice-2`).
**Contract:** `docs/pipeline/task-acceptance.md` (Feature aggregate acceptance).
**Writer:** dispatch run `20260929-215510-grok-hk-aspice-2`. This act does not create, alter, or remove any Task-level `Acceptance: ✓` record.

The prescribed feature-line rendering for a passing aggregate is `**Acceptance: ✓** (2026-09-29, Project Lead jadzia, Integration by obrien).` That sentence records the assigned confirmation. It is not a claim that this run re-accepted each child.

## 1. Result

| Feature | Children in scope | `[x]` | current `Acceptance:` | Feature disposition |
| --- | --- | --- | --- | --- |
| `0016` | `0016-01`..`0016-15` (15; no extras) | 15 | 15, all 2026-09-12, Project Lead jadzia, Integration by obrien | closed |
| `0017` | `0017-01`..`0017-07` (7; no extras) | 7 | 7, all 2026-09-12, Project Lead jadzia, Integration by obrien | closed |
| `0018` | `0018-01`..`0018-10` (10; no extras) | 10 | 0 | open, integration verdict `inconclusive` |
| `0019` | `0019-01`..`0019-10` and `0019-13` (11; no `0019-11`, no `0019-12`) | 11 | 11 (`0019-01`..`0019-05` on 2026-09-12; `0019-06`..`0019-10` and `0019-13` on 2026-09-15), Project Lead jadzia, Integration by obrien | closed |

`0018` is not marked `(feature, closed)` and receives no feature-level `Acceptance: ✓`. `task-acceptance.md` says a non-passing aggregate blocks closure and does not rewrite the true task markers. All ten `0018` task lines stay `[x]` without Acceptance, as they were.

## 2. What was checked

Against `TODO.md` at the integration tip above, before the feature-line edit:

- Every header matching `^- \[[ xw?pu]\] \*\*<id>\*\*` was parsed (501 headers).
- For each in-scope id: checkbox, `(task, open|closed)`, and whether the line contains `Acceptance:`.
- Child sets were compared with the assigned ranges. No missing id and no extra child under these four features.
- Direct `PREREQ:` endpoints outside the feature were resolved to their TODO headers and checked for `[x]`/`[w]` plus `Acceptance:`.
- Paths in backticks under `docs/`, `scripts/`, or `_src/` were tested with `os.path.isfile`.
- Each `REF: \`<hex>\`` was tested with `git cat-file -t`. The repository is not shallow (`git rev-parse --is-shallow-repository` printed `false`).
- `Integration review: mandatory` does not occur on any line of these four feature spans. The file contains 11 such attributes, all outside this batch.
- Before-image SHA-256 of the feature header plus its child lines, UTF-8, newline-joined, at the tip above:

| Feature | SHA-256 |
| --- | --- |
| `0016` | `0311b1755015ada88cf4cb07546dbd89abb1a05abc1daab5843e48606dd31d10` |
| `0017` | `4333cf12cada1bb37f82331bd99e839d6bf1ac4fc956a121d6df264f27e207e2` |
| `0018` | `2b3aa00d012643963b1188bcffac4cb582d119a52377c07055b265690a929d76` |
| `0019` | `0c33677896e219d55cd572c31f4a823b12cbe4087bf6cbdcf48f9cce46cde5e3` |

No product test, generator, or browser run was executed. This act changes backlog markers and this dossier only.

## 3. Feature 0016

**Goal.** Problem Resolution, Change Request, and Product Release Control (`TODO.md`). The shadow item `issues/0016/index.md` repeats that title and sets `authority: shadow`. Its AC-001 and Definition of Done only preserve imported identity. They were not used as a second closure oracle.

**Definition of Done applied here.** Every in-scope child is terminal `[x]` and already carries current Acceptance; direct external prerequisites of those children do too; cited work-product paths exist; no integration checkpoint is unmarked-as-passed because none is declared. The normative move of the section into `DONE.md` is not part of this act (see section 7).

**Children.** `0016-01` through `0016-15`, each `[x] (task, open)` with Acceptance dated 2026-09-12.

**Direct external prerequisites, all `[x]` with Acceptance:** `0011-05`, `0012-02`, `0013-08`, `0014-13`, `0015-03`, `0015-06`, `0015-07`, `0015-09`.

**Cited paths, all present:**

| Task | Path |
| --- | --- |
| `0016-01` | `docs/pipeline/sup9-problem-record-model.md` |
| `0016-02` | `docs/pipeline/sup9-swe-discrepancy-resolution-procedure.md`, `docs/pipeline/problem-resolution-metrics.md` |
| `0016-03` | `docs/pipeline/sup9-sup10-classification-rules.md` |
| `0016-04` | `docs/pipeline/sup10-change-impact-and-authorization.md` |
| `0016-05` | `docs/pipeline/sup9-sup10-verification-and-closure.md` |
| `0016-06` | `docs/pipeline/spl2-release-specification.md` |
| `0016-07` | `docs/pipeline/release-publication-architecture.md` |
| `0016-08` | `docs/pipeline/sup10-accepted-change-lifecycle-record.md` |
| `0016-09` | `docs/pipeline/sup10-rejected-change-lifecycle-record.md` |
| `0016-10` | `docs/pipeline/sup9-high-impact-alert-urgent-action-exercise.md` |
| `0016-11` | `docs/pipeline/sup10-supersession-invalidation-revisit-record.md` |
| `0016-12` | `docs/pipeline/sup9-sup10-status-and-trend-report.md` |
| `0016-13` | `docs/pipeline/backlog-classification-migration-rules.md` |
| `0016-14` | `docs/pipeline/external-intake-integration.md` |
| `0016-15` | `docs/pipeline/external-finding-integration-rules.md` |

**REF objects.** Present: `b584bbd4a`, `3ec9a101f`, `c690def5f`, `6e18fb770`, `df6377313`, `39092e45d`, `f25484635`, `3e4b6d8a1`. Absent from this repository (not a commit, tree, or blob): `4abdc14` (`0016-02`), `b293adc` (`0016-03`), `6734664` (`0016-04`), `c042df8` (`0016-05`), `79ee47c` (`0016-08`), `887d05d` (`0016-10`), `78299c0` (`0016-12`). The cited files for those seven tasks exist at HEAD. Last commit touching each file: `83e385e9a` (`0016-02` paths), `d7df6568b` (`0016-03`, `0016-04`), `93b7419a9` (`0016-05`), `c054335c8` (`0016-08`), `442b11357` (`0016-10`), `ed6b8793c` (`0016-12`). Those tips are not the cited short ids. Existing task Acceptance lines were not edited.

**Confirmation.** Feature line set to `[x] (feature, closed)` with the assigned Acceptance sentence. Child lines unchanged.

## 4. Feature 0017

**Goal.** Risk Management, Measurement, and Management Review. Shadow item `issues/0017/index.md` is the same identity-preservation stub (`authority: shadow`).

**Children.** `0017-01` through `0017-07`, each `[x] (task, open)` with Acceptance dated 2026-09-12.

**Direct external prerequisites, all `[x]` with Acceptance:** `0011-01`, `0012-06`, `0012-08`, `0015-06`.

**Cited paths, all present:** `docs/dossiers/req-0017-01-risk-strategy.md`, `docs/dossiers/dec-0017-001-man5-risk-strategy.md`, `docs/dossiers/0017-01-man5-risk-strategy-scope-review.md`, `docs/pipeline/man5-risk-register.md`, `docs/pipeline/man5-recurring-risk-review-procedure.md`, `docs/pipeline/man6-measurement-metrics.md`, `docs/pipeline/man6-measurement-specification.md`, `docs/pipeline/trend-reporting-guidelines.md`, `docs/pipeline/management-review-procedure.md`.

**REF objects present:** `fe645c415c498a4fd83ccc6b5371c6ba28d2aba1`, `ed2995afa`, `02eadd471`, `30be1f05e`, `59c31ef7f`, `1e1881488`. `0017-02` cites the register path and `REG-RSK-20260829-01`, not a commit. Its claim filename `TODO-benjamin-0017-02-20260829.md` is not at the repository root. The retained copy is `issues/legacy-claims/TODO-benjamin-0017-02-20260829.md` and records `state: [x]`.

**Confirmation.** Feature line set to `[x] (feature, closed)` with the assigned Acceptance sentence. Child lines unchanged.

## 5. Feature 0018 — inconclusive

**Goal.** Automotive ECU SPICE CL2 Pilot, Internal Assessment, and Readiness Closure. Shadow item `issues/0018/index.md` is open, `authority: shadow`. `issues/0018/0018-01/index.md` carries the label `legacy-terminal-unverified`.

**Children.** `0018-01` through `0018-10` are `[x] (task, open)`. None of the ten lines contains `Acceptance:`. None cites a `REF:`.

**Blocking prerequisites.**

| Edge | Predecessor | State |
| --- | --- | --- |
| `0018-01` → `0025-10` | `0025-10` | `[x]`, no Acceptance (`TODO.md` line of that task) |
| `0018-04` → `0015-10` | `0015-10` | `[x]`, no Acceptance |
| `0018-01` → `0011-02`, `0018-01` → `0012-09` | both | `[x]` with Acceptance |

**Claims.** `DONE-benjamin-0018-01-20260919.md` through `DONE-benjamin-0018-10-20260919.md` each record state `review`, not an accepted disposition.

**Work products observed, not acceptance-bound.** These files exist and name the task in the title. They are not referenced from the TODO lines, and this act does not accept them:

| Task | Path |
| --- | --- |
| `0018-01` | `docs/pipeline/ecu-pilot-managed-assessment-plan.md` |
| `0018-02` | `docs/pipeline/ecu-pilot-managed-execution-dossier.md` |
| `0018-03` | `docs/pipeline/ecu-pilot-repeatability-dossier.md` |
| `0018-04` | `docs/pipeline/ecu-preassessment-evidence-catalogue.md` |
| `0018-05` | `docs/pipeline/ecu-pilot-level2-assessment-report.md` |
| `0018-06` | `docs/pipeline/ecu-pilot-finding-triage-governance.md` |
| `0018-07` | `docs/pipeline/ecu-pilot-reassessment-cycle-record.md` |
| `0018-08` | `docs/pipeline/ecu-pilot-independent-readiness-review.md` |
| `0018-09` | `docs/pipeline/ecu-pilot-published-assessment-profile.md` |
| `0018-10` | `docs/pipeline/ecu-pilot-cl2-claim-authorization.md` |

**Verdict.** `inconclusive`. Author: dispatch run `20260929-215510-grok-hk-aspice-2`. Authority: `docs/pipeline/task-acceptance.md`. Timestamp: `2026-09-29T22:03:37+02:00`. Affected: `0018-01`..`0018-10`. Integration tip: `3170be4607490cbdac3661a0dbd4eba781489d5c`. The same sentence is the non-checkbox line directly under the `0018` feature heading in `TODO.md`. The feature checkbox stays `[ ]` and the state stays `(feature, open)`.

The assigned sentence `[x] **0018** (feature, closed) ... **Acceptance: ✓**` was not written. Writing it would record a feature acceptance the child rows do not support.

## 6. Feature 0019

**Goal.** Eclipse S-Core Database Import. Shadow item `issues/0019/index.md` is the identity-preservation stub (`authority: shadow`).

**Children.** The complete child set in `TODO.md` is the assigned set: `0019-01`..`0019-10` and `0019-13`. There is no `0019-11` and no `0019-12` header. Every in-scope row is `[x] (task, open)` with Acceptance. Dates: `0019-01`..`0019-05` on 2026-09-12; `0019-06`..`0019-10` and `0019-13` on 2026-09-15.

**Direct prerequisites** are inside the feature only. All of those internal endpoints carry Acceptance.

**Cited paths, all present:** `docs/pipeline/eclipse-score-v0.6.0-snapshot-evidence-inventory.md`, `docs/pipeline/s-core-import-profile.md`, `scripts/score_extractor.py`, `scripts/score_normalizer.py`, `docs/pipeline/eclipse-score-v0.6.0-phase6-curator-package.md`, `docs/pipeline/aspice-level1-score-import.md`.

**REF objects, all present:** `111a5b90527cb6cb5f2b5bdcf8fad3a0237c41dd`, `fd2a3b441`, `f775e6f29`, `15fc42acc`, `41aff9779`, `43968b25fb23bb26e236bd3f420fce0cc1eef9af`, `71fa107fa1786a0ee7b0538fc952684fb6b1d44c`, `f36581f643445d74df6ab032a8217574ad5900ee`, `e56336fbec0eed3860851a85e38615b1370b7113`, `8e03946eb4f56f28ea303704fdb1656b6959503f`, `1d7356543008ab0048e308d351b8f6a631b2efa4`.

**Confirmation.** Feature line set to `[x] (feature, closed)` with the assigned Acceptance sentence. Child lines unchanged. This closure does not add a capability claim. `0019-10` already limits the campaign to `documentation-execution`.

## 7. Boundaries, edges, and data-loss choices

- **No `DONE.md` move.** `task-acceptance.md` describes a path-isolated move into `DONE.md` after a passing aggregate. This assignment allows `TODO.md` and this dossier only. Closed features `0038`, `0042`, and `0050` already remain in `TODO.md` with `(feature, closed)`. The three passing features stay in `TODO.md` the same way. No task text was deleted.
- **No child-marker edits.** Task checkboxes, Acceptance sentences, REFs, and claim names were not rewritten. The seven unreachable `0016` short ids stay on their historical lines.
- **No issue-store edit.** `issues/0016`, `issues/0017`, `issues/0018`, and `issues/0019` stay `state: open` with `authority: shadow`. `issues/_views/summaries/open.md` still shows the old open feature lines. Those views are derived. This act did not run a generator under `_src/`. A later regeneration from the shadow items can drop the `TODO.md` closure marks. That is an open drift risk, not a silent sync.
- **`TODO.md` banner.** The file starts with `GENERATED-VIEW: not authoritative. Do not hand-edit.` The same file is the live backlog this assignment names, and the shadow items say they were migrated from it. Only the three feature headings and the `0018` verdict line were edited. The generated header hashes were left untouched.
- **No integrating-task checkpoint.** None of the four features has a node marked `Integration review: mandatory` or a terminal integrating task. `task-acceptance.md` says that, absent an override, a feature does not close without that review. The passing closures follow the assigned bookkeeping sentence and the `0042` rendering. They do not invent a checkpoint review that was not in the tree.
- **Transitive closure limit.** Direct prerequisites of the in-scope tasks were checked. Ancestors behind those direct endpoints were not re-walked. The child Acceptance rows dated 2026-09-12 and 2026-09-15 were taken as the existing acceptance boundary, not re-issued.
- **`0018` documents.** The ten pilot files listed above were not modified and were not treated as accepted baselines.
- **No source edit.** Nothing under `_src/` was changed.

## 8. Residual gaps

1. `0018` is not closed. Ten terminal tasks have no current Acceptance; `0015-10` and `0025-10` also have none; the ten Benjamin claims remain `review`.
2. Seven `0016` REF short ids are not objects in this repository. The cited files exist; the recorded ids do not resolve.
3. `0017-02` names a claim file that is not at the repository root. The legacy-claims copy is present.
4. Shadow issue items and `issues/_views/summaries/open.md` still say the four features are open.
5. The sections were not moved to `DONE.md`.
6. No full ancestor walk beyond the direct prerequisites, and no fresh execution of the cited Python tools or the ECU pilot records.
