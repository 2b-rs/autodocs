# Task `0044-03` — DEC-0044-019 gate-scope proposal and Architect-review package

**Status:** non-authoritative preparation only. This file is not a decision
record, not a scope approval, not Task acceptance, and not an integration review.
It must not be read as permission to change checkpoint-test policy.

## 1. Pinned context

- **Task:** `0044-03`, prerequisite `0044-01`, requirement `RQ-IP-07`.
- **Task contract:** the rule must state what an Integrator executes (not only
  reads) at a checkpoint; derive test obligation from architecture and
  interface contracts; retain run evidence; define the no-automation case; and
  apply the rule to one real pending integration as a worked example.
- **Reserved identifier:** `DEC-0044-019`, reserved on `main` for `0044-03`.
  The reservation is explicitly not approval, a decision record, or a scope
  review.
- **Preparation baseline:** `main` =
  `418f09b79efe36a7856c98fc42dec2bd4e8c43e0`; item branch `0044-03` and its
  worktree were created from that baseline.

## 2. Predicate verdict and affected reach

The canonical `cross-item-blast-radius` predicate applies: the declared rule
can block validation, acceptance, integration, or closure of at least one other
work unit, and changes that unit’s evidence contract. This is actual declared
gate behavior, not a hypothetical bug or a shared-path argument.

Affected work units and gates for the proposed decision are:

| Unit/gate | Why it is in scope |
|---|---|
| `task:0044-03` | Produces the checkpoint test-obligation rule. |
| `task:0044-01`, `0044-04`, `0044-05`, `0044-12`, `0044-13`, `0044-14`, `0044-15` | Existing Feature-0044 tasks carrying mandatory integration-review attributes; their checkpoint evidence is directly governed by the rule. |
| `task:0044-08`, `integration:0044`, `feature-closure:0044` | Feature integration and closure must prove that the rule composes with the other process controls. |
| `repository:autodocs`, `integration:*`, `feature-closure:*` | Future checkpoint and closure gates inherit the repository-wide rule; this is the required future reach, not an invitation to mutate them now. |
| `task:0043-07`, `feature:0043` | Real pending mandatory integration selected as the worked-example target; no 0043 artifact or marker is changed by this preparation. |

The implementation must verify the current checkpoint inventory before writing
the authoritative rule. If a listed unit is no longer a checkpoint at that
time, the decision record must explain the corrected scope rather than silently
drop it.

## 3. Proposed decision question (`DEC-0044-019`)

What executable integration-test obligation applies at each mandatory
checkpoint, how must its scope and kind be derived from the architecture and
interface contracts of the integrated items, what evidence must the run leave,
and what explicit disposition is required when no automated test exists?

### Candidate disposition for Architect review (not selected authority)

At each mandatory checkpoint, the Integrator executes a checkpoint-specific
test set derived from the integrated items’ declared architecture risks,
interfaces, invariants, failure modes, and external effects. The obligation
must name the test kind and scope, the candidate revision, inputs/environment,
command or typed action, result, and a digest-bound evidence reference. A test
run is review evidence; it never creates acceptance authority or replaces the
checkpoint review.

When no automated test exists, the checkpoint must use a defined manual or
inspection fallback where one can provide meaningful evidence, record the
missing-automation gap and its limits, and take the explicit fail or `[u]`
integration-verdict path when the criterion cannot be established. There is no
silent pass caused by an absent test. The fallback must not claim stronger
assurance than it provides.

### Alternatives

1. **No execution obligation:** rejected for failing the explicit “not only
   read” requirement and leaving checkpoint behavior dependent on inspection
   quality alone.
2. **One universal fixed suite at every checkpoint:** rejected as both
   under-inclusive for architecture-specific interfaces and over-inclusive for
   unrelated work; it does not derive scope from the integrated contracts.
3. **Selected candidate — proportional, derived execution with an explicit
   no-automation path:** retained for Architect review because it satisfies
   RQ-IP-07 while keeping test scope tied to declared architecture and risk.

### Constraints

- The rule must not weaken `task-acceptance.md`, `branch-workflow.md`,
  `AGENTS.md`, capability classes, or checkpoint authority.
- The Integrator executes and records tests, but only the separately required
  review/acceptance authority can decide the checkpoint outcome.
- Evidence must be reproducible enough for independent review: exact candidate,
  inputs, environment/tool identity where material, command/action, result,
  and digest/reference.
- A manual fallback is an explicitly bounded evidence method, not permission to
  waive a missing criterion.
- The worked example must be real and pending; it must not edit or accept
  Feature 0043.

## 4. Architect scope-review request

Management must instantiate an Architect distinct from this implementer. The
Architect’s review is limited to scope and authority before mutation:

1. confirm or reject application of `cross-item-blast-radius` to the declared
   checkpoint-test behavior;
2. confirm the affected-unit/gate list, including repository-wide future
   `integration:*` and `feature-closure:*` reach;
3. test whether “execute, not only read” is operationally defined without
   silently changing acceptance or integration authority;
4. review the derivation inputs (architecture risks, interfaces, invariants,
   failure modes, external effects) and the evidence minimum;
5. review the no-automation fallback, especially its fail/`[u]` behavior and
   residual-risk statement;
6. verify that `0043-07` is a real pending checkpoint and that the worked
   example will demonstrate derivation rather than merely repeat a generic test;
7. identify any narrower or wider scope required before the decision record is
   authored on `main`.

The Architect must return a recorded scope verdict before any mutation that
implements, activates, widens, narrows, affirmatively retains, or removes the
qualifying gate scope. This package does not supply that verdict.

## 5. Verbatim context package for independent “Lore” review

The following excerpts are reproduced verbatim so an independent Architect can
review the scope without relying on this proposal’s interpretation.

### 5.1 Task contract (verbatim from `TODO.md`)

> **0044-03** PREREQ: 0044-03:0044-01 Answer "Integrationstests?": define which integration tests checkpoints require and how their scope and kind are derived from the architecture. *(architect-elaboration)*
>
> **Requirements covered:** `RQ-IP-07`.
>
> **Acceptance criteria:** A documented rule states what an integrator must execute (not only read) at a checkpoint, how the test obligation is derived from the architecture and interface contracts of the integrated items, what evidence the run leaves, and what happens when no automated test exists; the rule is applied to at least one real pending integration as a worked example.
>
> **Definition of Done:** Committed; `task-acceptance.md` and `branch-workflow.md` reference the rule; the worked example is retained as evidence.
>
> **Integration review:** not mandatory. **No-checkpoint justification (architect):** adds a review obligation rather than a capability; failure mode is a documented gap, caught at `0044-08`.

### 5.2 Canonical predicate (verbatim from `docs/pipeline/decision-record.md`)

> `cross-item-blast-radius` | The decision can block the start, validation, acceptance, integration, release, or closure of at least one **other** work unit, or change that unit's contract. This applies regardless of whether the deciding node is marked as an integration checkpoint.

### 5.3 Reserved identifier (verbatim from `dec-branching-merging-strategie.md`)

> | `DEC-0044-019` | Task `0044-03` | Dispatcher `data` | Verbindliche ausführbare Testverpflichtung an verpflichtenden Checkpoints, proportional aus Architekturrisiken/Schnittstellen/Invarianten/externen Effekten abgeleitet; Nachweis nennt Kommando, Eingabe, Kandidat, Digest, Ergebnis; fehlende Automatisierung erfordert ausdrücklichen manuellen Rückfallpfad samt aufgezeichneter Lücke und Fail-/`[u]`-Weg, niemals ein stilles Bestehen |
>
> **Was diese Reservierung nicht ist:** keine Genehmigung des Inhalts, keine Scope-Prüfung, keine Abnahme. Beide Vorgänge erfüllen nach übereinstimmender Einschätzung ihrer Vorbereiter das kanonische `cross-item-blast-radius`-Prädikat und benötigen vor der qualifizierenden Mutation zusätzlich die unabhängige Scope-Prüfung eines von Management instanziierten Architekten. Die Reservierung verhindert lediglich, dass zwei Sessions dieselbe Nummer belegen.

### 5.4 Existing checkpoint authority (verbatim from `TODO.md` header)

> **Cross-item gate scope is decided and reviewed before mutation.** During Feature breakdown and again before implementation, apply the canonical `cross-item-blast-radius` predicate from [`decision-record@v1`](docs/pipeline/decision-record.md#2-wann-ein-datensatz-verpflichtend-ist): qualifying declared gate behavior can block the start, validation, acceptance, integration, publication, or closure of another work unit, or change that other unit's contract. A shared path, difficulty, unfamiliarity, green validation, or a hypothetical ordinary bug is not sufficient.
>
> **The pre-mutation gate is narrow and mandatory.** Before the first mutation that implements, activates, widens, narrows, affirmatively retains, or removes a qualifying gate scope, a conforming `decision-record@v1` and a supporting scope review by a management-instantiated architect whose identity is distinct from the Implementer's identity must exist. Affirmative retention is a deliberate in-scope decision to preserve existing, already-contested gate behavior; passive inheritance is excluded. The review is a scope-authority check, not Task acceptance, integration review, an integration verdict, or `Acceptance: ✓`; green validation does not establish scope correctness, completeness, or authority.

### 5.5 Checkpoint semantics (verbatim from `TODO.md` header)

> A checkpoint gates upward integration, not implementation start. Dependents may still implement on a checkpoint's `[x]`/`[w]` and merge it in; only crossing the checkpoint boundary upward — and treating its work as *integrated* — waits for the integrator's passing review.

## 6. Safety and handoff

This proposal intentionally changes no checkpoint-test behavior and creates no
decision record. The implementer remains at `[p]` pending the independent
Architect review and the conforming decision record on `main`. After those
conditions are met, a separately authorized implementation may use this package
as a candidate, re-pin current contracts, and update the authoritative docs.
