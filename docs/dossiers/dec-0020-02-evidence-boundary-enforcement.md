# Decision — evidence-boundary enforcement reach (`0020-02`)

**Identifier:** `DEC-0020-002`, checked against `main`
`6a153726bf4ecc838220572034ad707bd923940e` (only `DEC-0020-001` there).
No `DEC-0020-002` on `main` or on candidate `0020-02@532b1482636f0760a7e0ffdd5d5882cb84fb11da` at allocation.

Supporting Architect scope review: `docs/dossiers/0020-02-gate-scope-review.md`
(reviewer `agent:uras:0020-02-scope:20260826T121659Z-30d0c5d1`, distinct from
Implementer `hguh`). Mailbox assignment `1787746566416-30d0c5d1` is
coordination, not authority.

---

### `DEC-0020-002` — Evidence-boundary enforcement is refuse-at-use/freeze for named ECU consumers, not a repository-wide start or validation gate

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-26T12:35:00Z`
- **Deciding identity:** `agent:uras:0020-02-scope:20260826T121659Z-30d0c5d1`
- **Role:** `Architekt`
- **Authority reference:** `docs/pipeline/process-roles.md` TK-2 operational pre-mutation rule; `AGENTS.md` Cross-item gate-scope review exception; Task `0020-02` Architect assignment. Dispatcher mail `1787746566416-30d0c5d1` is coordination only.
- **Subject:** Operational meaning of “enforce” for Task `0020-02` (`PD-0020-02-01`) and whether activating that enforcement may block or change other work units' start, validation, freeze, or closure contracts.
- **Decision:** Defining the closed origin set, required metadata, and substitution/aggregation prohibitions in `docs/dossiers/req-0020-02-evidence-boundary.md` is a local `0020-02` contract and is not itself a cross-item gate. Activating enforcement that other units must pass **is** `cross-item-blast-radius`. The authorized enforcement point is **refusal at use** of an evidence item for Feature `0020` assessment input, catalogue, selected-profile register, freeze, or process-instance demonstration, and **refusal at freeze** for `0025-02` / `0025-03`. It is **not** refusal at arbitrary Task start, **not** a default `_src/validate.py` or other shared-suite check, **not** a live `docs/ASPICE/` gate, and **not** a new TODO start-prerequisite onto `0020-09`, `0025-*`, `0019`, `0011`–`0018`, `0022`–`0032`, or `0020-03`. Existing `0020-07:0020-02` and `0020-08:0020-02` edges remain inherited Feature-breakdown prerequisites and are not widened. `docs/ASPICE` survey files stay informative (`PD-0020-02-04`). Encoding and closed vocabularies for `validity` / `retention` / `confidentiality` remain open (`PD-0020-02-02`, `PD-0020-02-03`) with the constraint that first refusal may require presence and non-empty values, and that encoding must not impose metadata headers on files not offered for those uses. Shared/external interface evidence, once separately identified by `0020-03` / `0020-04` / `0020-09`, is not opportunistic aggregation (`PD-0020-02-05` constraint).
- **Technical justification:** The Task text requires both define and enforce, and the Feature goal is to prevent documentation-pipeline evidence from being misrepresented as ECU process-instance evidence. A repository-wide validator would block unrelated work (the `0038-03` failure class). Extra start-gates on envelope Features would change contracts for units that do not yet produce ECU execution evidence. Consumer Tasks `0020-07`, `0020-08`, `0020-09`, `0025-02`, and `0025-03` already name assessment input, catalogue, register, wrong-origin freeze, or documentation-pipeline exclusion; binding refusal to those use/freeze points is the smallest declared behavior that makes substitution and opportunistic aggregation observable without gating the rest of the repository. Local fixtures that cannot fail another unit do not trigger the predicate.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Refuse at use/freeze for the named ECU evidence consumers; keep the local contract; forbid default shared validation and extra start-gates.
    - **Disposition:** `selected`
    - **Reason:** Matches the Task's prohibit-substitution language at the points that already consume ECU evidence, without creating a repository-wide block.
  - **ALT-02:** Wire a default `_src/validate.py` or shared-suite check that fails other Tasks when origin or metadata rules are unmet.
    - **Disposition:** `rejected`
    - **Reason:** Declared shared validation would block unrelated units; that is the `0038-03` blast-radius class.
  - **ALT-03:** Add new TODO start-prerequisites onto `0020-09`, `0025-*`, Feature `0019`, and envelope Features `0011`–`0018` / `0022`–`0032`.
    - **Disposition:** `rejected`
    - **Reason:** That would change those units' start contracts before they produce ECU execution evidence; `0020-09` already refuses substituted interface evidence at run without a new start edge on `0020-02`.
  - **ALT-04:** Close `0020-02` as definition-only and leave `PD-0020-02-01` undecided.
    - **Disposition:** `rejected`
    - **Reason:** The Task says “enforce”; leaving reach undecided would block every later consumer mutation that needs this exception satisfied.
  - **ALT-05:** Refuse at every Task start that mentions evidence, including documentation and UX work.
    - **Disposition:** `rejected`
    - **Reason:** Over-reach: those units are not the Feature `0020` assessment/catalogue/register/freeze uses named in `REQ-0020-01`.
- **Consequences:**
  - **CON-01:** `0020-02` may complete implementation on the local contract plus optional fixtures or a helper that cannot fail another unit; that is not `Acceptance: ✓`.
  - **CON-02:** `0020-07`, `0020-08`, `0020-09`, `0025-02`, and `0025-03` must apply the refusal at their own use or freeze gates when they consume evidence; this record does not implement those gates.
  - **CON-03:** Features `0011`–`0018`, `0019`, and `0022`–`0032` receive no new start-gate from this decision; Feature `0019` remains classified `documentation-execution` when used.
  - **CON-04:** `docs/ASPICE/*` survey files remain informative until a later catalogue Task explicitly replaces that status.
  - **CON-05:** Qualifying enforcement mutation stays blocked until this record is reachable on the Implementer baseline together with the supporting review; this Architect session does not merge into `.worktrees/0020-02` or advance `main`.
  - **CON-06:** Rollback is not to activate any shared checker or extra start-gate if this record is not on the intended baseline, and not to treat survey files as live gates.
  - **CON-07:** Residual risk: until the named consumers run, substitution can still be offered in prose; the local contract makes that a visible contract breach, not yet a mechanical block.
- **Affected work units:**
  - `task:0020-02`
  - `task:0020-07`
  - `task:0020-08`
  - `task:0020-09`
  - `task:0025-02`
  - `task:0025-03`
  - `feature:0020`
  - `feature:0025`
  - `feature:0019`
  - `feature:0011`
  - `feature:0012`
  - `feature:0013`
  - `feature:0014`
  - `feature:0015`
  - `feature:0016`
  - `feature:0017`
  - `feature:0018`
  - `feature:0022`
  - `feature:0027`
  - `feature:0028`
  - `feature:0029`
  - `feature:0030`
  - `feature:0031`
  - `feature:0032`
- **Affected gates:**
  - `validation:0020-07-assessment-input`
  - `validation:0020-08-evidence-catalogue`
  - `validation:0020-09-selected-profile-register`
  - `validation:0025-02-selected-profile-readiness`
  - `validation:0025-03-evidence-freeze`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:hguh:0020-02:20260826T120900Z`
    - **Role:** `Requirements Engineer`
    - **Participation:** `consulted`
    - **Position:** `supports`
    - **Note:** Independently classified local SHALLs as not a cross-item gate and enforcement activation as `cross-item-blast-radius`; stopped before mutation and held candidate `532b1482636f0760a7e0ffdd5d5882cb84fb11da`.
- **Waiver:** `none`
