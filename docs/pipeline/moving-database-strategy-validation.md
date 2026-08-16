# Moving-Database Strategy — Aggregate Validation

Status: validation evidence for Task `0037-06`.

## Evidence set

- `issue-migration-shadow-import.md` defines full re-imports from an exact committed legacy tree into fresh, disposable candidate roots; stale or malformed candidates are rejected, never refreshed or merged in place.
- `schema-upgrade-reconciliation.md` defines pure version-to-version transforms into fresh roots, semantic clean-import equivalence, externally stored provenance, authorized immutable-ID replay, and stable blocking findings instead of automatic merges.
- `issue-cutover-rollback.md` defines immutable watermarks, append-only compare-and-swap control history, one writable authority per epoch, atomic selector switching, and provenance-only rollback before the signed point of no return.

## Aggregate finding

The three contracts have disjoint mutation domains: legacy source/candidate import roots, fresh upgrade roots plus standing provenance, and selector/control-ledger transitions. Each rejects stale/colliding state rather than applying last-writer-wins behavior. Therefore the moving-database strategy satisfies Task `0037-06` acceptance criteria and is ready for inclusion in the architecture review package.
