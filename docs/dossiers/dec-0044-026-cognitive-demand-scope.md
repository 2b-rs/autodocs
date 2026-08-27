### `DEC-0044-026` — Bound cognitive-demand calibration without changing the established vocabulary

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-25T23:47:26+02:00`
- **Deciding identity:** `agent:data:0044-06:cognitive-demand-20260825T214726Z-0d41a19f`
- **Role:** `Architekt`
- **Authority reference:** `agent-inbox:1787694446375-0d41a19f`; `task:0044-06`; `docs/pipeline/process-roles.md#architect`
- **Subject:** Pre-mutation scope for estimating, calibrating, and recording cognitive demand under `RQ-CB-05` and the still-customer-confirmation-bound interpretation `RQ-CB-06`
- **Decision:** Task `0044-06` must preserve the existing closed `cognitive_demand` vocabulary `low | medium | high | critical`. Its smallest authorized reach is a repository-local study, a deterministic and explainable estimator over the five observable dimensions already named by the Task, a calibration dataset of at least ten historical work packages with predeclared inclusion and outcome rules, prediction/outcome records for later recalibration, and a two-channel nondeterminism protocol: implementer self-flagging plus an independent orchestrator-side result-quality gate. The estimator may inform scheduling but must not independently grant capability, assignment, ownership, Acceptance, integration, or execution authority. Initial activation is staged: the implementation records a shadow prediction alongside the existing value and reports disagreement; it does not rewrite existing values or automatically block, reassign, or downgrade work. Any enforcement or vocabulary change requires a later decision and review after `0044-08` resolves the customer-confirmation point.
- **Technical justification:** Accepted `0044-04` already normatively defines the four values at `docs/pipeline/feature-breakdown.md:71`; `0044-05` consumes that field for deterministic capability matching. Inventing a parallel scale would make the two accepted contracts disagree, while immediately enforcing an uncalibrated estimator would let a noisy scheduling input block unrelated work. The Task itself supplies five observable dimensions: scope breadth, reasoning depth, context volume, ambiguity, and verification hardness. A versioned scoring rubric can map each dimension to the existing four values, aggregate conservatively, and retain the full vector and rationale so mispredictions are diagnosable. Historical calibration must bind predictions to outcomes observable in repository evidence—completion/rework, validation failure, `[u]`/defect disposition, and measured resource evidence when actually recorded—without treating token count, success, or self-report alone as ground truth. Shadow operation provides falsification evidence while preserving authority boundaries and the unresolved `RQ-CB-06` interpretation.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Preserve the four-value vocabulary and introduce an explainable, shadow-mode calibration method with separate self-flag and independent quality-gate signals.
    - **Disposition:** `selected`
    - **Reason:** It satisfies `0044-06` while preventing an unvalidated estimate from changing another item's authority or lifecycle.
  - **ALT-02:** Replace the vocabulary with numeric scores, additional labels, or model-specific tiers.
    - **Disposition:** `rejected`
    - **Reason:** It would contradict accepted `0044-04`, break `0044-05` consumers, and exceed the assigned scope.
  - **ALT-03:** Use token consumption or successful completion as the sole calibration target.
    - **Disposition:** `rejected`
    - **Reason:** Either proxy confounds package demand with agent/runtime variation and hides unusable outputs, rework, and lucky completion.
  - **ALT-04:** Activate automatic rejection or reassignment immediately from the estimated class.
    - **Disposition:** `rejected`
    - **Reason:** Calibration quality is not yet established and `RQ-CB-06` remains an interpretation awaiting the customer-confirmation point at `0044-08`.
- **Consequences:**
  - **CON-01:** The future Implementer must document an ordinal rubric for all five dimensions, the deterministic aggregation and tie/escalation rules, and examples at every vocabulary boundary; no sixth value, alias, or model-specific class is permitted.
  - **CON-02:** Calibration must use at least ten historical Tasks selected by a rule fixed before outcome analysis, cover success and failure/rework outcomes plus more than one Feature and demand band, cite immutable evidence, and publish mispredictions and exclusions rather than optimizing them away.
  - **CON-03:** Every prediction record must bind estimator version, Task/contract REF and digest, five-dimension vector, resulting existing class, rationale/evidence references, predictor identity/time, and later observed outcome/disposition; prediction and outcome are append-only and distinguish missing evidence from a low score.
  - **CON-04:** Self-flagging is an implementer signal, not `[u]`, Acceptance, or permission to abandon work. It records the unexpected condition, affected dimension, completed evidence, safe next step, and requested orchestration response while preserving the active claim unless authoritative lifecycle rules say otherwise.
  - **CON-05:** The independent result-quality gate evaluates required artifacts, validation, contract coverage, and evidence regardless of self-confidence. A missing self-flag cannot make unusable output pass; a self-flag cannot make conforming output fail without the gate's own evidence.
  - **CON-06:** Shadow predictions may be consumed by `0044-08` analysis and future scheduling experiments, but `0044-04` values, `0044-05` matching eligibility, current claims, checkpoints, and Task markers remain unchanged during this phase.
  - **CON-07:** A later proposal to enforce estimates across work units must report false-high and false-low rates, boundary confusion, missing-data behavior, and agent/runtime sensitivity; it requires its own cross-item decision and independent Architect scope review.
  - **CON-08:** Rollback removes the later estimator/study integration and stops new predictions while preserving all versioned prediction/outcome evidence, this decision, the scope review, and prior backlog/Acceptance history.
- **Affected work units:**
  - `task:0044-04`
  - `task:0044-05`
  - `task:0044-06`
  - `task:0044-08`
  - `feature:0044`
  - `repository:autodocs`
- **Affected gates:**
  - `planning:feature-breakdown-cognitive-demand`
  - `scheduling:agent-work-package-match`
  - `validation:0044-06-calibration-evidence`
  - `quality:orchestrator-result-review`
  - `integration:0044-08`
  - `feature-closure:0044`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:data:0044-06:cognitive-demand-20260825T214726Z-0d41a19f`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** The accompanying pre-mutation scope review constrains implementation and cross-item reach; it is not implementation, Acceptance, or integration authority.
- **Waiver:** `none`

#### `DEC-0044-026-C001`

- **Event format:** `decision-record-correction@v1`
- **Target record:** `DEC-0044-026`
- **Recorded at:** `2026-08-26T13:43:22Z`
- **Correcting identity:** `agent:data:0044-06:dec-0044-026-gate-grammar-20260826T134322Z-22b5d8c9`
- **Role:** `Architekt`
- **Authority reference:** `DEC-0044-026`; Project Lead correction assignment `agent-inbox:1787751722012-0343f4f8`; read-only grammar finding `agent-inbox:1787751663880-c41d7f3f`
- **Correction reason:** The original affected-gate block used the non-canonical prefixes `planning:`, `scheduling:`, and `quality:`. This event maps those three existing gate identities to the closed `decision-record@v1` grammar according to their already-declared lifecycle effect, without adding, removing, widening, narrowing, or activating a gate.
- **Target field:** `Affected gates`
- **Previous effective block SHA-256:** `fdf255f80fcdce2be25ecbc9a8638e6b31ad5a07a990fbce1261d923c319a2d1`
- **Replacement block:**
  ```markdown
  - **Affected gates:**
    - `validation:feature-breakdown-cognitive-demand`
    - `task-start:agent-work-package-match`
    - `validation:0044-06-calibration-evidence`
    - `validation:orchestrator-result-review`
    - `integration:0044-08`
    - `feature-closure:0044`
  ```

#### `DEC-0044-026-C002`

- **Event format:** `decision-record-correction@v1`
- **Target record:** `DEC-0044-026`
- **Recorded at:** `2026-08-26T13:57:55Z`
- **Correcting identity:** `agent:data:0044-06:dec-0044-026-c002-20260826T135755Z-190105ed`
- **Role:** `Architekt`
- **Authority reference:** `DEC-0044-026`; Project Lead correction assignment `agent-inbox:1787752584355-32800305`; independent negative review `4ad4389fc8322e610357df99e77bf550bfc3ded4:docs/dossiers/0044-026-gate-grammar-scope-review.md`
- **Correction reason:** `DEC-0044-026-C001` mapped the invalid scheduling prefix to a `task-start:` gate even though its slug was not a work-unit ID and the base decision authorizes shadow validation, not start blocking. This event selects the narrowest reading supported by the decision's declared content: validate and record work-package-match evidence without changing matching eligibility, assignment, execution authority, lifecycle state, or Task start.
- **Target field:** `Affected gates`
- **Previous effective block SHA-256:** `6ab313136b533f698b578ef143cfe32040518e4274b8f525df2ac17b34553c39`
- **Replacement block:**
  ```markdown
  - **Affected gates:**
    - `validation:feature-breakdown-cognitive-demand`
    - `validation:agent-work-package-match`
    - `validation:0044-06-calibration-evidence`
    - `validation:orchestrator-result-review`
    - `integration:0044-08`
    - `feature-closure:0044`
  ```

#### Current-main re-pin note — 2026-08-25

After `main` advanced to `433b41b04cd4b353f9681947a9e3c7897a751855`,
this governance artifact was re-pinned without rewriting prior commits. The
re-derived candidate retains `5ff57c7717208283c1000530b93318b633d64918`
as ancestry and carries current `Base-Ref`, `Prior-Candidate`, and
`Policy-Origin-Branch: main` provenance in the re-pin commit. All decision
fields and effective cognitive-demand semantics remain unchanged.
