# Architect gate-scope review — Task `0020-02` evidence-boundary enforcement

## Review identity and boundary

- **Verdict:** `scope-ok-mit-auflagen`
- **Reviewed at:** `2026-08-26T12:35:00Z`
- **Reviewer:** `agent:uras:0020-02-scope:20260826T121659Z-30d0c5d1`
- **Role:** management-instantiated Architect (Team yrevocsiD roster, inbox `uras`)
- **Capability class:** `privileged` (this Architect review and its record only)
- **Dispatcher:** `leirbag` (coordination `1787746566416-30d0c5d1`; mailbox is not Management authority)
- **Implementer:** `hguh` / `agent:hguh:0020-02:20260826T120900Z` (identity distinct; claim and worktree not overwritten)
- **Review type:** independent pre-mutation cross-item gate-scope review of proposed enforcement reach
- **Not:** Task acceptance, integration review, integration verdict, implementation, `Acceptance: ✓`, checkpoint crossing, Feature closure, `DONE.md`, `refs/heads/main`, Feature `0033`, or Task `0020-03`

This is the supporting Architect scope review required by `AGENTS.md`'s Cross-item gate-scope review exception and `docs/pipeline/process-roles.md` TK-2. Green tests were not run and would not prove that the scope is correct.

Companion decision record: `DEC-0020-002` in `docs/dossiers/dec-0020-02-evidence-boundary-enforcement.md`. That record is authored on this review branch. The Implementer must make it reachable on `0020-02` before any qualifying enforcement mutation. This session does not mutate `.worktrees/0020-02`.

## 1. Pinned baseline (independently measured)

| Object | SHA | Note |
|---|---|---|
| current `main` | `6a153726bf4ecc838220572034ad707bd923940e` | matches dispatcher pin |
| Feature `0020` | `1cb33a5797f62284a224681ef479e15718ad7446` | matches pin; ancestor of candidate |
| `0020-01` branch | `ae7a4e93f059b4f4e5cf826f0cc94f3b07199a9c` | matches pin; ancestor of candidate |
| `0020-01` REF / `DEC-0020-001` | `b56f44ef75f3a1afce2b101484ec75eb7e9e133a` | ancestor of candidate |
| candidate `0020-02` / this review HEAD | `532b1482636f0760a7e0ffdd5d5882cb84fb11da` | implementer porcelain empty; hold stands |
| contract blob | `8b53ca3fdd867ec99e9ccc5bf81829c5651f5ca8` | `docs/dossiers/req-0020-02-evidence-boundary.md` |
| contract SHA-256 | `7cf9e46dd10bef9ccf63278f0d0bc4003adadebc34ae81abfa49713e063f89a2` | bytes at the candidate |
| implementer claim blob | `ed00487d9ce84c34f10c92abcccc3ec78ac45b69` | `TODO-hguh-0020-02-20260826T120900Z.md` |

Pinned governing inputs at the same candidate:

| Input | SHA-256 |
|---|---|
| `docs/dossiers/req-0020-02-evidence-boundary.md` | `7cf9e46dd10bef9ccf63278f0d0bc4003adadebc34ae81abfa49713e063f89a2` |
| `docs/dossiers/dec-0020-01-ecu-scope.md` | `fe2e172e0b5a7f22c3cd36876b268add509e274f28e5cbe87051129bf780e1e1` |
| `TODO-hguh-0020-02-20260826T120900Z.md` | `70eace74cfec39e7ea6da67c7d119c84e166b3bc0f5d6cb7378af242a0aa1239` |
| `docs/pipeline/decision-record.md` | `dea2c93ad046d67a129d6b30b7715609a49afde26f47e5039cc2c2159cdb66c0` |
| `docs/pipeline/process-roles.md` | `a142e8885751c1c8a97faabfae7b6c579f1599333d3fd3e11ed869831191fc43` |
| `docs/pipeline/roles/architect.md` | `201699d0071a8d07d6cc10c816f2743b2d8f0d8636eab4856275dca2dcb056fa` |
| `AGENTS.md` | `c9f5999ff27a3cf0de4a2d1d0b2f8b0da5425ca4aa0553c3f106e3dcbdce638d` |
| `docs/ASPICE/05-evidence-register.md` | `0148dc019b898d0209e78ce5951b5f48a79e8df5149527d7ff19b02b78b67211` |
| `docs/ASPICE/01-assessment-basis-and-scope.md` | `f9b19367b2b0d4ababcb2e981a8bc13d5a83abdaad82fc78e7ec2eef6eccc75b` |
| `docs/ASPICE/02-level-1-requirements.md` | `e743b960a0e3699ec71789034ec9b548c4aa4fc997ae0f008112715f6240b846` |
| `docs/ASPICE/04-gap-roadmap.md` | `561641bb793b330690d8da0a8febffc9fcb1d3adde2ad17c6013731618702b52` |

`DEC-0020-*` on `main` at this pin: only `DEC-0020-001`. `DEC-0020-002` was free.

## 2. Independence and context record

This session assumed the Architect persona explicitly and is distinct from Implementer `hguh` and Dispatcher `leirbag`. Privilege authorizes direct review execution; it does not authorize Acceptance, integration, or implementation of the enforcer.

Context given:

- the four mandatory briefing fields in `1787746566416-30d0c5d1`;
- implementer hold `1787746738703-f342f642` and wait-for-REF `1787746994382-c1ce7d67`;
- the candidate contract, especially §6 consumers, §7 gate table, and `PD-0020-02-01`..`05`;
- pins for `main`, Feature `0020`, `0020-01`, and `DEC-0020-001`.

Context not given:

- no private Management deliberation beyond recorded `DEC-0020-001`;
- no requested Acceptance or integration outcome;
- no authority to start `0020-03` or touch Feature `0033`;
- no implementation draft of an enforcer (hguh stopped before that mutation).

## 3. Predicate and reach

Canonical predicate (`decision-record@v1` §2, `cross-item-blast-radius`): the **actual declared behavior** of a gate can block the start, validation, acceptance, integration, publication, or closure of another work unit, or change that unit's contract.

hguh's §7 table is correct as a classification of *candidates*:

| Candidate behavior | Qualifies? | Independent finding |
|---|---|---|
| The dossier stating SHALLs for `0020-02`'s own contract (`REQ-0020-01`–`REQ-0020-09`) | No | Local definition. Other units are not blocked by this file existing. Matches the “routine local” negative case in `process-roles.md`. |
| Adding TODO prerequisites from `0020-07` / `0020-08` / `0025-*` / envelope Features onto this contract | Yes | Would change another unit's start or closure contract. |
| A repository check that fails other Tasks' validation when metadata/origin rules are unmet | Yes | Same class as `0038-03`: shared validation can block unrelated units. |
| A freeze/assessment rule that rejects mixed-origin or cross-product sets | Yes | Blocks Feature `0025` freeze / assessment closure. |
| A local fixture that only tests this contract's examples | No, while it cannot fail another unit | Task-local. |

Existing backlog text already names wrong-origin freeze (`0025-02`) and excludes documentation-pipeline/synthetic evidence from ECU outcome claims (`0025-03`). Feature `0019` already states that `0020-02` classifies it as `documentation-execution`. `0020-07` and `0020-08` already list `PREREQ` on `0020-02`. Those existing edges are Feature-breakdown inheritance, not a new mutation by `hguh` and not affirmative retention of a contested gate.

`0020-09` does **not** currently list `0020-02` as a start prerequisite. Adding that edge would be a new start-gate and is not authorized here. When `0020-09` later runs, its own already-written refusal of substituted interface evidence must apply this boundary; that is use-time enforcement, not a new start contract.

## 4. Product decisions

| ID | Disposition | Bound |
|---|---|---|
| `PD-0020-02-01` | **Closed** by `DEC-0020-002` | Refuse **at use** of an evidence item for Feature `0020` assessment input, catalogue, selected-profile register, freeze, or process-instance demonstration, and **at freeze** for `0025-02`/`0025-03`. Not at arbitrary Task start. Not as a default `_src/validate.py` check. |
| `PD-0020-02-02` | **Open** | Encoding/schema is not required to close gate-scope. Constraint: the chosen representation must not become a repository-wide required header on files that are not offered as Feature `0020` assessment/catalogue/register/freeze evidence. |
| `PD-0020-02-03` | **Open** | Closed token sets for `validity` / `retention` / `confidentiality` may wait for `0020-08`. First refusal may treat those fields as required and non-empty without a closed vocabulary. |
| `PD-0020-02-04` | **Closed** | `docs/ASPICE/01-assessment-basis-and-scope.md`, `02-level-1-requirements.md`, `04-gap-roadmap.md`, and `05-evidence-register.md` remain **informative** vocabulary sources. They are not live gates. `0020-08` may later generate or replace them; this Task must not activate them. |
| `PD-0020-02-05` | **Open** for `0020-03` / `0020-04` / `0020-09` | Constraint: a separately identified shared/external interface-evidence item is not opportunistic aggregation under `REQ-0020-05`. |

## 5. Named consumers — authorized vs not gated

**May apply the refusal (use/freeze, not new start-gates):**

- `task:0020-07` assessment input / official-outcome worksheets
- `task:0020-08` process/work-product/evidence catalogue
- `task:0020-09` selected-profile execution register (at run, without adding `0020-09:0020-02` as a start prerequisite)
- `task:0025-02` selected-profile readiness / freeze block on wrong-origin
- `task:0025-03` evidence-index freeze (exclude documentation-pipeline and synthetic from ECU outcome claims)

**Classified, no new start-gate, no live survey gate:**

- `feature:0019` remains `documentation-execution` when used at all
- Features `0022`–`0032` and `0011`–`0018` under the Feature `0020` ASPICE envelope consume this boundary later through the selected-profile path; this review does not add start-gates onto them
- `docs/ASPICE/*` survey files named in §6

**Out of this review and still forbidden:** Feature `0033`; Task `0020-03` implementation; `Acceptance: ✓`; Feature `0020` integration; `refs/heads/main`.

## 6. Minimum authorized scope

After `DEC-0020-002` is reachable on the Implementer's `0020-02` baseline, `hguh` may:

1. Keep the local contract `docs/dossiers/req-0020-02-evidence-boundary.md` as the inspectable definition (`REQ-0020-09`).
2. Add Task-local fixtures or an optional helper **only** if that helper is not registered as a default blocking check in `_src/validate.py` or any other shared validation that other Tasks must pass.
3. Record, in `0020-02` history, that consumer-side refusal at the named use/freeze gates is the operational meaning of “enforce” for this Task.
4. Stop. Do not implement freeze/assessment refusal inside this Task against other units' trees.

`0020-02` may reach implementation-complete `[x]` on that local contract plus optional non-blocking fixtures without wiring a repository-wide gate. Consumer Tasks named above remain responsible for applying the refusal when they consume evidence.

## 7. Forbidden mutations (auflagen, before any enforcement mutation)

1. **A-01.** Do not register an origin/metadata checker in `_src/validate.py` or in any default suite other Tasks must pass.
2. **A-02.** Do not add TODO prerequisites onto `0020-09`, `0025-*`, `0019`, `0011`–`0018`, `0022`–`0032`, or `0020-03`. Existing `0020-07:0020-02` and `0020-08:0020-02` stay as inherited Feature edges; do not widen them.
3. **A-03.** Do not treat `docs/ASPICE/*` as a live gate.
4. **A-04.** Do not start `0020-03` or touch Feature `0033` from this claim.
5. **A-05.** Do not mutate `.worktrees/0020-02` from this Architect session; the Implementer merges or otherwise carries `DEC-0020-002` and this review onto `0020-02`.
6. **A-06.** This review is not `Acceptance: ✓`, not an integration verdict, and not Feature closure.
7. **A-07.** A later helper's encoding must not require metadata headers on files that are not offered as Feature `0020` assessment/catalogue/register/freeze evidence.

On dissent or a material baseline change of the contract at `532b14826`, mutation remains blocked until a new supporting review binds the new candidate.

## 8. Briefing record

Dispatcher briefing `1787746566416-30d0c5d1` stated the four mandatory fields reproduced in `TODO-uras-0020-02-scope-20260826T121659Z-30d0c5d1.md`. This review used that briefing, the candidate contract, `DEC-0020-001`, the Feature `0020` / `0025` / `0019` backlog text at the candidate, and the named `docs/ASPICE` survey files. It did not use Memory-helper writes (`memory_append` safety hold still in force).
