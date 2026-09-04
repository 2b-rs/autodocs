# 0037-31 final frozen migration candidate — gate rework r1

- Task: `0037-31`
- Assignment: `1788519031177-793919ee`
- Same-slot rework award: `1788521108922-dbc1a91c`
- Claim mode: `claimless-frozen-transaction`
- Source: `7dbc94db262979b41bc225d6571d610123a47814`
- Source tree: `6a6c40de53f15245a084bbdc68b526f07ab5b534`
- Closure transaction: `f5a806c52a63e00edac5c0aa8bb0793227ae3af1`
- Run: `0037-31-post-delta-7dbc94db-r2`
- Result: `rejected`, retained, immutable, not promotable

The DEC-0037-033 importer contradiction is repaired: the canonical orchestrator
reserved its fresh hidden staging directory, imported the pinned source, and
atomically retained the completed candidate. No direct or broad `_src/output`
permission was added.

The run then exposed 930 existing `IMP-CLAIM-OPAQUE` blockers. The pinned source
and this exact award contain no signed `migration-dispositions@v1` input, and
production `run_migration()` has no disposition-input interface. Weakening or
inventing those authority decisions is outside this two-gate repair. The result
therefore remains fail-closed and is not Task completion or Acceptance.
