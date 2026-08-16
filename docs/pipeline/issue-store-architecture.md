# Issue-Store Architecture Baseline

Status: pre-implementation baseline assembled by Task `0037-37`.

The architecture is Git-native, single-authority per epoch, deterministic for derived artifacts, and guarded by claim/epoch/base/scope fencing. Canonical items and provenance are immutable Git-tree inputs; catalogs, graphs, page models, localization registers, and HTML are derived only. Migration imports committed legacy trees into disposable candidates, upgrades use pure fresh-root transforms, and cutover uses append-only compare-and-swap control history with no dual writes.

Implementation must use the versioned sandboxed runner protocol: bounded inputs/outputs, declared resources/scopes/credentials, preflight, exact tests, failure behavior, and substantive/bookkeeping commit separation. No implementation task assumes privileged execution. Approval trust begins only after the policy bundle at the package commit is independently confirmed and the approval ref/signature/digests verify.
