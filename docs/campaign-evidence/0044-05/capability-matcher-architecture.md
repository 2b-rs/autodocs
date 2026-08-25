# Task 0044-05 capability-matcher architecture baseline

Status: Architect predecessor contract for `0044-05.01`. `DEC-0044-025` is
integrated on `main` at `174b10078c519d81ff43703ee45b572e19180101`. This work
product does not activate matching,
assign an agent, grant authority, or accept work.

## 1. Goal and observable boundary

Task `0044-05` implements `RQ-CB-01..03` and Management decision
`DEC-0044-004`: an Architect writes a machine-readable requirement profile; a
deterministic, stdlib-only matcher returns every capable agent descriptor with
explainable rejections; the orchestrator, not the Architect or matcher, chooses
among eligible agents. An Implementer can run the same matcher against its own
descriptor before accepting the job.

The result is capability evidence only. It is never proof of assignment,
ownership, current availability, claim acquisition, independence, Acceptance,
waiver, specialist approval, release authority, or permission to exceed the
Task's write scope.

## 2. Sources and disposition

| Source | Revision | Class | Derived obligation |
| --- | --- | --- | --- |
| `TODO.md`, Feature/Task `0044`/`0044-05` | accepted predecessor tree `c8d3c1672d57021e670ed5e9c2141b24dea9e0cd`; authoritative `main` at start `6a937f8414440cc84233954012ff802eaf57924c` | authority | Two machine-readable schemas, deterministic matcher, self-check, role/class mapping, tests, tool registration, briefing input |
| `docs/dossiers/re-intake-prozessverbesserung-integration-und-capabilities.md`, `RQ-CB-01..03`, `DEC-0044-004`, `DEC-0044-025` | `main@174b10078c519d81ff43703ee45b572e19180101` | authority | Architect specifies requirements; orchestrator selects without AI; staged activation and legacy preservation |
| `docs/pipeline/feature-breakdown.md` | accepted `0044-04` candidate `c8d3c1672d57021e670ed5e9c2141b24dea9e0cd` | authority | Rights, data, tools, execution need, cognitive demand, independence, branch, source/order/test derivation |
| `SANDBOX.md` and `docs/pipeline/process-roles.md` | `main@6a937f8414` | authority | Three capability classes; direct execution and authority remain separate; Integrator requires privileged; fail-safe fallback |
| `issues/_schema/agent-capability-v1.schema.json` | accepted `0037-45` REF `b01d56f134671c89693a9f7a3781b43f761ffd29` | legacy shared contract | Preserve unchanged; its two-class runner contract is not a matcher descriptor |
| `TODO.md`, `0038-19` deferred finding | `0038-19` REF `18b563144a87ab5fb830c6f663eccd4934c13667` | evidence | Existing schema omission of `unprivileged` is known; do not conceal it through in-place mutation |
| `docs/pipeline/decision-record.md` | `main@6a937f8414` | authority | TK-2 record and affected-gate scope before matcher mutation |

Assumption A-01: token/context capacity and cognitive capability can change
between dispatch and execution. The descriptor is therefore an input snapshot,
not a timeless identity claim. Task `0044-06` owns calibration and overwhelmed-
agent behavior; this Task owns only controlled classes and deterministic
comparison.

Assumption A-02: agent availability and quota measurement are scheduling inputs,
not capabilities proven by this matcher. An `unknown` capacity rejects; no
descriptor is upgraded from historical success or model branding.

## 3. Findings and ownership

| ID | Finding | Disposition / owner |
| --- | --- | --- |
| F-01 | Legacy `agent-capability@v1` has only `sandboxed-grunt` and `privileged`. | Preserve it byte-for-byte. New `agent-capability-descriptor@v1` is owned by `0044-05`; any Feature-0037 migration remains separately explicit. |
| F-02 | The accepted breakdown record shape has cognitive demand but no token/context field. | The Task profile schema adds token and context budget classes without rewriting the accepted instruction. `0044-06` may later calibrate their meanings before `0044-08`. |
| F-03 | Static roster data cannot prove per-Task independence, dynamic quota, availability, credentials, or current data access. | Descriptors are digestable snapshots. Required assurance handles must be present; absence/unknown rejects. Separate authority gates still apply. |
| F-04 | A matcher that selects one agent would make the Architect's profile an implicit scheduling decision. | Output the complete sorted eligible set. Multiple matches are valid and reported as `multiple-eligible`; the orchestrator selects separately. |
| F-05 | A privileged agent can execute a lower-authority Task but does not thereby gain permission to accept its own work. | Class compatibility and process-role checks are independent; match results state the non-authorizing boundary. |

## 4. Versioned files and ownership

### 4.1 Executable/schema unit (`0044-05.02`)

- `issues/_schema/task-requirement-profile-v1.schema.json`
- `issues/_schema/agent-capability-descriptor-v1.schema.json`
- `issues/_schema/capability-match-result-v1.schema.json`
- `_src/tools/capability_match.py`
- `_src/tests/test_capability_match.py`
- `_src/tests/fixtures/capability-match/`

The unit must not modify `issues/_schema/agent-capability-v1.schema.json`.

### 4.2 Adoption/governance unit (`0044-05.03`)

- `AGENTS.md` — profile/result as mandatory Feature-0044 pilot briefing input,
  without claiming broad activation;
- `docs/pipeline/capability-matching.md` — public contract, activation,
  non-authority boundary, CLI, failure and recovery;
- `docs/pipeline/tools.md` — tool registration;
- `docs/pipeline/README.md` — process-document index.

These are governance paths. They are authored in an item-owned worktree on a
branch cut from then-current `main` and integrated only by an expressly assigned
privileged Integrator after the mandatory hygiene/preflight sequence.

## 5. Task requirement profile contract

Schema ID: `task-requirement-profile@v1`.

The root is a closed object (`additionalProperties: false`) with these required
fields:

| Field | Type / controlled value | Semantics |
| --- | --- | --- |
| `schema` | constant `task-requirement-profile@v1` | Version discriminator |
| `profile_id` | non-empty stable string | Immutable profile/snapshot identifier |
| `task_id` | `^[0-9]{4}-[0-9]{2}(\.[0-9]{2})?$` | Exact work unit |
| `process_role` | `Architect`, `Implementer`, `Integrator`, `Requirements Engineer`, `QA Manager`, or registered specialist ID | Required role; does not assign a persona |
| `capability_class` | `sandboxed-grunt`, `unprivileged`, `privileged` | Minimum policy class required by the work |
| `execution_needs` | `none`, `runner`, `direct` | Exactly one route; alternative routes require separate profiles |
| `required_rights` | unique sorted string array | Required capability/right IDs |
| `required_data_handles` | unique sorted string array | Named handles only; never secret values or private paths |
| `required_tools` | unique sorted string array | Required executable or non-execution tool IDs |
| `token_budget_class` | `small`, `medium`, `large`, `very-large` | Minimum supplied token capacity snapshot |
| `context_budget_class` | `small`, `medium`, `large`, `very-large` | Minimum supplied context capacity snapshot |
| `cognitive_demand` | `low`, `medium`, `high`, `critical` | Minimum served cognitive-demand class |
| `required_assurances` | unique sorted string array | Stable external assurance handles, including independence/credential checks when required |
| `sources` | non-empty array of source bindings | Requirement/decision/architecture/evidence derivation |
| `test_scope` | closed object | Kind, derived-from list, command/procedure, expected evidence |
| `resource_bounds` | closed object | Advisory max CPU seconds, wall seconds, memory MiB, and expected token range |

Cross-field validity is normative:

- `sandboxed-grunt` permits `execution_needs` `runner` or `none`, never `direct`;
- `unprivileged` and `privileged` permit `direct` or `none`, never `runner`;
- `Integrator` requires `privileged` and the rights
  `acceptance.review` and `integration.checkpoint` as applicable;
- `privileged` is required whenever `required_rights` includes
  `acceptance.review`, `integration.checkpoint`, or `feature.close`;
- profiles requiring no privileged act use `sandboxed-grunt` or `unprivileged`
  according to execution need even when a privileged identity may later satisfy
  them; and
- empty data/tool/right/assurance arrays are explicit, not omitted.

Source bindings are closed objects with `kind` (`requirement`, `decision`,
`architecture`, `evidence`, `assumption`), `reference`, and `derivation`.

## 6. Agent capability descriptor contract

Schema ID: `agent-capability-descriptor@v1`. It is deliberately distinct from
legacy `agent-capability@v1`.

The root is a closed snapshot object with these required fields:

| Field | Type / controlled value | Semantics |
| --- | --- | --- |
| `schema` | constant `agent-capability-descriptor@v1` | Version discriminator |
| `descriptor_id` | non-empty stable string | Snapshot identity used in result/digest evidence |
| `agent_id` | registered stable agent identity | Scheduling identity, not a claim owner token |
| `process_roles` | unique sorted role array | Roles the current assignment may assume |
| `capability_class` | one of the three current classes | Exact current class; never inferred from tool presence |
| `execution_routes` | unique sorted array of `none`, `runner`, `direct` | Routes actually authorized for this session |
| `rights` | unique sorted string array | Available rights; excess rights never widen Task scope |
| `data_handles` | unique sorted string array | Available named handles; no secret values |
| `tools` | unique sorted string array | Available tool IDs |
| `token_budget_class` | ordered budget class | Current supplied/verified capacity class |
| `context_budget_class` | ordered budget class | Current supplied/verified capacity class |
| `cognitive_classes_served` | unique ordered-prefix array | Explicit classes served; branding is not evidence |
| `assurances` | unique sorted stable-handle array | Current external checks such as independence or credential assurance |
| `capacity_status` | `available`, `unavailable`, `unknown` | `unknown` and `unavailable` reject |
| `snapshot_reference` | non-empty stable reference | Provenance for dynamic capability statement |

The schema enforces class/route consistency with current policy:

- `sandboxed-grunt` has `none` and optionally `runner`, never `direct`;
- `unprivileged` has `none` and `direct`, never `runner`;
- `privileged` has `none` and `direct`, never `runner`.

The descriptor does not contain secrets, raw credential paths, model marketing
names, or a claim that an assurance is true without a stable handle.

## 7. Matching semantics

### 7.1 Validation and canonicalization

1. Parse UTF-8 JSON and reject BOM, duplicate object keys, non-finite numbers,
   wrong root types, unknown schema IDs, and unknown fields.
2. Validate the complete closed contract and cross-field rules before matching.
3. Reject duplicate `descriptor_id` or `agent_id` values in one invocation.
4. Compare arrays as sets but require canonical input ordering. Report
   non-canonical order as invalid input rather than silently rewriting evidence.
5. Never read wall-clock time, environment capability, Git state, network,
   credentials, or model metadata. Every result derives only from explicit
   bytes and the matcher version.

### 7.2 Eligibility predicates

A descriptor is eligible only when every predicate passes:

1. `capacity_status == available`.
2. `process_role` is in `process_roles`.
3. Capability class is compatible:
   - required `privileged` -> actual `privileged`;
   - required `unprivileged` -> actual `unprivileged` or `privileged`;
   - required `sandboxed-grunt` with route `runner` -> actual
     `sandboxed-grunt` with `runner`;
   - required `sandboxed-grunt` with route `none` -> any actual class with
     `none`.
4. `execution_needs` is in `execution_routes`.
5. Each required right, data handle, tool, and assurance is present.
6. Token and context class rank is at least the required rank.
7. `cognitive_demand` is explicitly listed in `cognitive_classes_served`.
8. The role/class hard constraints in section 5 pass even if the descriptor has
   a nominal right string.

Extra descriptor capabilities do not alter the Task contract or suppress a
rejection. In particular, privileged class cannot satisfy a runner route, an
`Integrator` role cannot be inferred from privilege, and a right string cannot
override a class or role conflict.

### 7.3 Stable rejection codes and order

For each rejected descriptor, emit all applicable reasons in this fixed order:

1. `CAPACITY_UNAVAILABLE`
2. `CAPACITY_UNKNOWN`
3. `PROCESS_ROLE_MISSING`
4. `CAPABILITY_CLASS_INCOMPATIBLE`
5. `EXECUTION_ROUTE_MISSING`
6. `RIGHT_MISSING`
7. `DATA_HANDLE_MISSING`
8. `TOOL_MISSING`
9. `TOKEN_BUDGET_INSUFFICIENT`
10. `CONTEXT_BUDGET_INSUFFICIENT`
11. `COGNITIVE_CLASS_UNSERVED`
12. `ASSURANCE_MISSING`
13. `AUTHORITY_CONSTRAINT_FAILED`

Repeated set reasons are secondarily sorted by the missing value. Invalid input
uses separate `INPUT_*`/`SCHEMA_*` codes and produces no eligibility claim.

## 8. Result and CLI contract

Result schema ID: `capability-match-result@v1`. Required fields:

- `schema`, `matcher_version`, `profile_id`, `profile_sha256`;
- sorted `descriptor_sha256` bindings;
- `status`: `single-eligible`, `multiple-eligible`, `none-eligible`, or
  `invalid-input`;
- sorted `eligible_agent_ids`;
- sorted `rejections`, each binding `agent_id`, `descriptor_id`, and all stable
  reasons; and
- `non_authority_notice`, a constant stating that the result grants no
  assignment, ownership, independence, acceptance, waiver, or scope.

CLI:

```text
python3 _src/tools/capability_match.py \
  --profile <task-requirement-profile.json> \
  --descriptor <agent-capability-descriptor.json> [--descriptor <path> ...] \
  [--agent-id <exact-id>] [--json]
```

- Batch mode exit `0`: at least one eligible descriptor, including multiple.
- Batch mode exit `1`: valid inputs, no eligible descriptor.
- Self-check (`--agent-id`) exit `0`: exact agent is eligible; exit `1`: exact
  agent is present but rejected.
- Exit `2`: malformed/unsupported input, duplicate identity, missing requested
  agent, I/O failure, or internal failure. Exit `2` is never a non-match.
- Human output is at most ten summary lines. `--json` is canonical UTF-8 JSON
  with sorted keys, compact separators, and exactly one final LF.

## 9. Test design

All tests are hermetic and stdlib-only. Required positive/negative population:

| Case | Required proof |
| --- | --- |
| Exact eligible | Every required dimension satisfied; `single-eligible`, exit 0 |
| Privileged superset for direct Implementer task | Eligible but result grants no acceptance/integration authority |
| Sandboxed no-execution task | Sandboxed and higher classes may be eligible; complete sorted set |
| Ambiguous/multiple | Two descriptors eligible; `multiple-eligible`; Architect/matcher chooses neither |
| No eligible | Valid descriptors with all rejection dimensions represented; exit 1 |
| Runner mismatch | Direct classes cannot satisfy `runner` |
| Authority mismatch | Right string cannot make non-privileged Integrator eligible |
| Missing data/tool/assurance | Stable per-value reasons, no secret/path output |
| Capacity insufficient/unknown | Ordered comparisons and fail-closed unknown |
| Invalid schema/version/field/key order | Exit 2 and no eligibility set |
| Duplicate JSON key and duplicate identity | Exit 2 before matching |
| Determinism | Input permutation and repeated run produce byte-identical canonical result after canonical-order enforcement fixtures are normalized |
| Self-check | Eligible and rejected exact-agent cases; absent ID is exit 2 |
| Legacy canary | `agent-capability@v1` input is rejected as unsupported and its tracked bytes remain unchanged |

The implementer reports exact test counts, Python version, exit codes, resource
use, focused automation-safety output, and `git diff --check`. Tests must include
a red-first mutation proving the authority-class constraint fails when removed.

## 10. Decomposition and prerequisite graph

### `0044-05.01` — Architect shared contract and gate-scope baseline

- Role: Architect (`data` currently owns only this preparation).
- Prerequisite: `0044-04` accepted work-product baseline.
- Deliverables: `DEC-0044-025` on `main`; this architecture document; repaired
  Task graph and exact child contracts.
- Write scope: Task claim/TODO block, this evidence directory, and the separate
  governance decision branch only.
- Validation: decision-record structure/manual field-order audit; exhaustive
  source/consumer inventory; prerequisite/ID/cycle checks; `git diff --check`.
- Capability: `privileged`, `execution_needs: direct`, cognitive `high`, token
  12k–24k, context `large`; no external data or credentials.
- Checkpoint: not independently mandatory. No-checkpoint justification: it
  defines a reviewed contract and performs no executable gate or external
  effect; the parent `0044-05` mandatory checkpoint reviews the whole package.

### `0044-05.02` — Implement schemas, matcher, fixtures, and self-check

- Role: Implementer, identity distinct from Data.
- Prerequisite: implementation completion of `0044-05.01`
  as specified by the repaired Task contract; `DEC-0044-025` must be reachable
  on `main` before first matcher mutation.
- Exact write scope: section 4.1 plus own claim and its Task/Subtask bookkeeping.
- Prohibitions: no governance documents, legacy schema mutation, activation,
  agent selection, Acceptance, integration, or `main` advance.
- Capability: `unprivileged`, direct Python/Git, cognitive `high`, token
  16k–32k, context `large`, CPU 1, memory <= 1 GiB, wall <= 20 minutes for the
  focused suite.
- Checkpoint: not independently mandatory. No-checkpoint justification: the
  executable is not activated and the parent `0044-05` mandatory checkpoint is
  the immediate upward boundary; duplicating a child checkpoint adds no risk
  isolation before the complete adoption contract exists.

### `0044-05.03` — Adopt the versioned contract in pilot governance

- Role: privileged Implementer distinct from Data and from the Integrator.
- Prerequisite: `0044-05.02` implementation complete.
- Exact write scope: section 4.2 plus own coordination/bookkeeping record.
- Topology: observe exact then-current `main` SHA `M`; create a new item-owned
  governance branch/worktree at `M`; merge `--no-ff` the exact completed parent
  `0044-05` tip carrying `.01` and `.02`, so `M` is first parent and the parent
  Task tip is second parent; only then author the path-limited governance edits.
  If `main` drifts before mutation, stop and recalculate rather than replaying a
  stale policy baseline. This declared merge carries the executable/schemas and
  their claims into the candidate; it is not an undeclared `.03` scope widening.
- Acceptance: briefing text names profile/result as pilot inputs, preserves the
  four existing mandatory dispatch fields, makes no broad-activation claim,
  registers CLI/failure/recovery, and states legacy schema distinction.
- Atomic availability rule: the `.03` candidate must never be integrated as
  documentation-only. Before integration its briefing text is candidate policy,
  not active authority; after integration the same candidate also contains the
  tested matcher and schemas. The exact non-activation wording is: “This pilot
  requirement becomes operative only when this governance commit and the bound
  `0044-05.02` product are both reachable from `main`; it does not activate
  repository-wide dispatch enforcement, grant authority, or credit historic
  dispatches.” Validation proves the bound product SHA and all three schemas are
  ancestors/files of the candidate and that the sentence appears in `AGENTS.md`
  and `docs/pipeline/capability-matching.md`.
- Capability: `privileged` solely because current governance paths and direct
  execution require it; the Implementer role may not exercise Acceptance or
  integration authority. Cognitive `medium-high`, token 10k–20k, context
  `medium`, CPU under 5 minutes.
- Checkpoint: not independently mandatory. No-checkpoint justification: it
  wires the already-tested mechanism only for the bounded pilot and cannot
  activate broad dispatch; the parent mandatory checkpoint reviews composition.
- Integration boundary: the `.03` Implementer may prepare and validate this
  combined candidate but may not review, accept, or land it. A separately
  assigned privileged Integrator evaluates the complete parent `0044-05`
  checkpoint, including `.01`, `.02`, `.03`, exact second-parent provenance,
  executable/docs consistency, and the no-broad-activation boundary, before any
  ff-only advance of `main` to the prepared candidate.

### Parent `0044-05` package completion

After all three children are terminal, a session distinct from Data performs
package consistency: schemas/tool/docs agree, the legacy canary is unchanged,
self-application evidence is current, no broad activation exists, and every
finding is dispositioned. The parent retains its existing mandatory integration
checkpoint. A separately assigned independent privileged Integrator reviews and
accepts the prerequisite-closed package; `0044-08` remains the Feature's sole
terminal integrating Task.

Order is strictly `0044-05.01 -> 0044-05.02 -> 0044-05.03 -> 0044-05`.
`0044-06` may run in parallel after `0044-04`; `0044-07` waits for the parent
`0044-05`, and `0044-08` waits for `0044-05`, `0044-06`, and `0044-07` plus its
other declared prerequisites.

## 11. Recovery and activation

- Before `0044-08`, rollback is deletion/reversion of pilot briefing wiring on
  a reviewed governance candidate; retain schema versions, match results, and
  findings. The existing `SANDBOX.md`/claim rules continue unchanged.
- Invalid or inconclusive matching never falls back to AI selection. It returns
  exit 2 or no eligible agent and the existing authority route decides whether
  the profile/descriptor must be corrected.
- A descriptor capacity drop after dispatch does not rewrite history. Record a
  new descriptor snapshot/result and use the `0044-06` overwhelmed-agent path.
- Broad activation requires an explicit `0044-08` decision and evidence. No
  historic dispatch is grandfathered or retroactively credited.
- Schema supersession is additive. Never rewrite or delete legacy
  `agent-capability@v1` or prior result evidence.

## 12. Additive governance-ID collision finding

After the initial preparation was committed, Project Leads `jean-luc` and `michael`
independently verified that sibling governance candidate `d4acf24bc` already
uses `DEC-0044-022` for a different decision and also carries
`DEC-0044-023`/`024`. The capability-matching record at `0ff7bd63d` is therefore
colliding evidence, not an integrable authority record. No architecture content
in this document is activated by that candidate.

Both histories were preserved. The capability decision was recut as
`DEC-0044-025`, reconciled additively with post-0020 `main` using merge tip
`174b10078c`, and integrated by an independently assigned privileged
Integrator. The colliding `0ff7bd63d` / `20bf78883` line and stale r2 tip
`a058b915d` remain provenance only and must never be treated as integration
candidates.
