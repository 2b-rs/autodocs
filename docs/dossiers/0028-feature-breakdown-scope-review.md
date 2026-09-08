# Architect cross-item scope review — Feature `0028`

## Review identity and baseline

- **Reviewer:** management-instantiated Architect Data,
  `agent:data:0028-feature-breakdown:1788043592587-75bc2401`
- **Exact baseline:** `main@d30b27ab1da5cbbb9a650573190fcbd9b7b207e1`
- **Decision reviewed:** `DEC-0028-001`
- **Review kind:** pre-mutation cross-item gate-scope review; not Task
  Acceptance, integration review, checkpoint verdict, risk acceptance, or
  Feature closure
- **Separation:** Data authors architecture only and is prohibited from future
  `0028` implementation and integration.

## Predicate and reach verdict

The canonical `cross-item-blast-radius` predicate applies. The breakdown
changes Feature `0028` start, integration, and closure gates and defines the
conditional input contract selected by `0029-01`. It also binds activation to
the authoritative `0020-09` selected-profile register, `0022-01` SYS interface
row, and `0027-01` operative plan boundary.

**Verdict: supports with binding conditions.** The five-stage graph is the
smallest bounded design that preserves conditional SYS.1 semantics and avoids
false process credit.

## Binding conditions

1. `0028-01` fails closed until an append-only Management disposition names
   internal/shared SYS.1 responsibility, performer, agreement/acceptance
   authorities, exact baseline, and assessed-unit outcomes. Architecture
   authoring does not satisfy that activation.
2. No unconditional prerequisite is added from `0028-*` to `0029-01`.
   `0029-01` chooses its internal/shared or external input path at use time.
3. `0028-04` owns the sole agreed stakeholder-requirements output contract.
   `0028-02` and `0028-03` produce inputs and analysis only; they cannot claim
   agreement, approval, or downstream readiness.
4. `0028-01`, `0028-04`, and terminal `0028-05` retain mandatory checkpoints.
   `0028-02` and `0028-03` remain unflagged because they are reversible,
   documentation-only evidence producers with no external effect; both are
   reviewed through their downstream checkpoints.
5. Exactly one terminal integrating Task exists: `0028-05`. It integrates but
   does not manufacture missing stakeholder evidence, approve requirements,
   assign ratings, activate SYS.1, or perform `0029-01`.
6. No earlier repository source, `0013-02` candidate, external artifact,
   scenario, generated trace, or green test is implicitly grandfathered as an
   agreed SYS.1 baseline or process-performance proof.
7. The interface self-applies prospectively. Rollback and supersession remain
   additive; the last accepted baseline is retained and consumers are notified
   before reuse.

## Checkpoint rationale

| Node | Verdict | Reach/risk basis |
| --- | --- | --- |
| `0028-01` | mandatory | authority/security-of-claim boundary; false pass activates a currently excluded process |
| `0028-02` | not mandatory | bounded source register, no external effect; downstream checks reject missing/unauthorized sources |
| `0028-03` | not mandatory | reversible elicitation/analysis evidence; cannot agree or publish the baseline |
| `0028-04` | mandatory | shared cross-Feature output consumed conditionally by `0029-01` |
| `0028-05` | mandatory | exactly-one terminal integration and Feature review floor |

Green validation is execution evidence only and cannot establish authority,
scope correctness, stakeholder agreement, process performance, or Acceptance.
