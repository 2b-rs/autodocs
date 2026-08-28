# `0044-07` Architect scope review for `DEC-0044-030`

**Verdict:** `supports`

**Reviewer:** `data`, Management-instantiated Architect, owner token
`agent:data:0044-07:20260827T115800Z-e2f77b46`

**Review scope:** the cross-item reach of Management-selected option B only.
This is a supporting scope review, not Task acceptance, implementation,
activation, an integration verdict, or permission to advance `main`.

## Pinned inputs

- reconciled Task branch baseline: `0044-07` merge of exact
  `main@cf56c7e2e7f9c2383f87c4d4eaa57f954311486a`;
- decision input:
  `docs/campaign-evidence/0044-07/architect-role-catalog-decision-packet.md@6539c7c0d`;
- Management selection: `agent-inbox:1787901177228-90a8b1db`;
- operative assignment: `agent-inbox:1787901222930-181cd035`;
- decision candidate: `DEC-0044-030` in
  `docs/dossiers/dec-0044-030-global-three-class-runner-policy.md`.

## Reach review

The decision has genuine cross-item reach because it fixes the global
execution-architecture baseline used by Features `0044` and `0037`, the
accepted `0044-04`/`0044-05` capability interfaces, and later consumer-policy
gates. Its reach is nevertheless bounded to retaining the current global
architecture and defining the conditions under which a separate consumer may
be narrower. It does not itself create such a restriction.

The reviewed affected work units are `repository:autodocs`, Feature `0044`,
Tasks `0044-04`, `0044-05`, `0044-07`, and `0044-08`, and Feature `0037`. The
reviewed gates are the `0044-07` implementation-start gate, capability-matching
validation, `0044` integration and closure, and any future bounded
`direct-execution-only` consumer gate. No other work unit is declared blocked,
reopened, invalidated, or migrated by this record.

## Interface and authority findings

The selected scope preserves these accepted interfaces and invariants:

1. the global capability classes remain exactly `sandboxed-grunt`,
   `unprivileged`, and `privileged`;
2. the queue-backed runner route and typed transport remain available;
3. absent or unestablished runtime class continues to fail closed to the
   sandboxed/runner procedure rather than being inferred as direct;
4. accepted v1 profile, descriptor, match-result, and matcher contracts remain
   byte-preserved and semantically valid;
5. matching remains non-authoritative evidence and grants none of assignment,
   ownership, claim, scope, independence, Acceptance, waiver, integration,
   release, or risk authority;
6. Runner is a process role/mechanism, not a capability-class value.

The decision changes no schema, matcher, catalog, roster, runner implementation,
queue, authority file, Task marker, accepted interface, or active consumer
policy. In particular it does not grandfather a direct-only rule into Feature
`0037`. A later consumer restriction is a new declared behavior and must name
its exact consumers, gates, evidence, negative behavior, activation, and
recovery. If its actual reach meets the cross-item predicate, it requires its
own decision and distinct Architect review before the first mutation.

## Activation, verification, and recovery

The retention decision becomes governance-visible only after the decision and
this review are integrated to `main` by the separately authorized Integrator.
That visibility removes the policy-choice uncertainty for later `0044-07`
planning; it does not implement or activate a role catalog or consumer rule.

A future bounded direct-only consumer must verify, at minimum, one permitted
direct descriptor, rejection of sandboxed and ambiguous descriptors with stable
reasons, preservation of non-authority semantics, unchanged unrelated-consumer
behavior, and deterministic rollback. Its activation must follow ordinary
implementation, validation, Acceptance/integration, and checkpoint authority.

Recovery from a bad bounded rule is local to that consumer: disable or revert
the rule and restore its prior accepted contract. Global class vocabulary,
runner transport, fail-closed fallback, accepted v1 bytes, and append-only
decision history remain intact. If safe local recovery cannot be shown, the
consumer restriction must not activate.

## Scope verdict

I support the selected option-B scope. It is the smallest intent-preserving
global decision: it answers the architecture question without prematurely
removing enforcement, invalidating accepted interfaces, or imposing a direct
route on unrelated work. Implementation must remain separated from this
Architect identity, and integration/Acceptance authority remains unchanged.
