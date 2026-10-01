# Architect gate-scope review — terminal claim lifecycle

**Verdict:** `scope-ok-with-conditions`

**Reviewer:** `agent:data:0044-20:1788038395542-d19fafda`, Management-instantiated
Architect, privileged for this bounded architecture record. The identity is
distinct from the `0020-10` implementers and must remain distinct from the
later `0044-20` Implementer and Integrator.

**Authority:** atomic award `agent-inbox:1788038395542-d19fafda`.

**Decision:** `docs/dossiers/dec-0044-033-terminal-claim-lifecycle.md`.

This is the supporting pre-mutation review required by the cross-item
gate-scope exception. It is not implementation, Task Acceptance, an integration
review or verdict, permission to advance `main`, or permission to mutate
Feature `0020`.

## Evidence and reach

- The authority documents require implementation claims to finalize at
  `[x]`/`[w]`, stay `TODO-*` until Acceptance, and rename byte-identically to
  `DONE-*` only in accepted-item bookkeeping.
- Current `main` Task `0044-17` (`635b9c810d`) implements those accepted-path
  semantics and no longer emits `LTD-CLAIM-TERMINAL-RETAINED`.
- The `0020-10` product exists at `b4c1874678798353bcbdbf5ad2d08ce5e3c9ad7d`;
  its older branch-local doctor still rejects terminal `TODO-*`, and its Task
  marker plus two participating root claims are not yet one terminal set.
- The actual declared behavior can block validation, integration, and closure
  of `0020-10` and every other legacy candidate. The
  `cross-item-blast-radius` predicate therefore applies.

The smallest intent-preserving scope is: define typed claim state as the lease
signal, keep the accepted-path boundary, require exact-set atomic finalization,
pin policy-sensitive validation to the target integration policy, add bounded
Task `0044-20`, and make Feature integrator `0044-08` depend on it. No product
exception, bulk migration, authority waiver, or Acceptance shortcut is needed.

## Binding conditions

1. **Exact set:** terminal finalization includes `TODO.md` and every root claim
   canonically naming the exact item; missing, ambiguous, foreign, or partially
   writable sets fail closed.
2. **Atomic alignment:** marker, real REF, claim state, inactive lease, and
   terminal coordination change together. A terminal claim with a live award
   or lease is invalid.
3. **Acceptance boundary:** terminal unaccepted claims remain `TODO-*`.
   `DONE-*` requires current Acceptance and byte-identical exact-item rename.
4. **Policy provenance:** legacy-product validation records the canonical
   target-policy validator ref and digest. Branch-local stale bytes cannot
   override the integration policy.
5. **Compatibility:** no bulk rename or history rewrite. Existing accepted
   records remain; inconsistent legacy claims change only in an authorized
   terminal, review, or Acceptance transaction.
6. **Activation:** the governance rule activates only after this decision and
   review reach `main`. Automation activates only after separate `0044-20`
   implementation and mandatory integration review.
7. **`0020-10` resume:** after governance activation, a fresh coordinator award
   may resume it only if its scope covers `TODO.md` and both participating exact
   root claims, the target-policy validator is proven, and the complete
   transition is one commit. Otherwise the existing hold remains.
8. **Separation:** this Architect does not implement, accept, integrate, or
   close either Feature. The later Implementer and Integrator are distinct.

## Verification required from `0044-20`

Red-first and adjacent-case tests cover active `TODO-*`, lease-free terminal
awaiting-Acceptance `TODO-*`, accepted `DONE-*`, premature `DONE-*`, marker/claim
divergence, active-award/lease rejection, missing and ambiguous exact claims,
two-claim all-or-nothing finalization, and a pre-`0044-17` candidate validated
with recorded target-policy provenance. Property or exhaustive population
tests prove that no subset of a multi-claim set is accepted as terminal.

## Rollback and migration review

The decision is append-only after publication. Automation rollback is a normal
revert of `0044-20`, leaving the documented manual fail-closed transaction in
force. Migration is lazy; no global write is performed. This avoids irreversible
or external effect and preserves existing Acceptance provenance.

## Conclusion

The scope is approved with conditions 1–8. The decision and backlog contract
may be integrated by a separate privileged Integrator. No qualifying gate
mutation may exceed those conditions without a new decision and Architect
scope review.
