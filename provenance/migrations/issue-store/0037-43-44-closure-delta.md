# Frozen closure delta — Tasks 0037-43 and 0037-44

- Schema: `frozen-closure-delta-evidence@v1`
- Transaction: `0037-43-44-closure-delta-1788512992649-36e30730`
- Assignment: `1788512992649-36e30730`
- Decision: `DEC-0037-031`
- Base: `e6db416ef8c41770cd09cba3dfef5ceb389a0e60`
- Original source watermark: `c170c8f34831f3a28b6d4dab67c02c61e3dad53e`
- Authority epoch: `legacy-frozen`
- Selector digest: `sha256:49c844c34df6609f4bdec4b618bb5461db4e3848ef7336ca1e7f4a843c122188`

## Exact completion bindings

| Task | Main-ancestral product | Canonical integration receipt |
|---|---|---|
| `0037-43` | `0ca70a810b6fc7977bad7b2c5bc0a7f4cbcc697d` | `867d12f6ac95301a6fa1aaf53649f778feb7c353` |
| `0037-44` | `e6a9251b1a6a98c53a8dc22ab2d6fffa288d79aa` | `e54ebbb41bab6bc66b8f028735cd446628fd9db7` |

The transaction changes only the two Task markers and their exact existing
implementation claims, plus the policy, transaction verifier, tests, and this
evidence pair. It records implementation completion only. It creates no
`Acceptance: ✓`, changes no prerequisite, checkpoint, acceptance criterion,
Task prose, product byte, authority selector, or broader frozen-state rule.

The original quiescence observation remains bound to the source watermark
above. The manifest separately records pre-delta and post-delta aggregate
digests; the latter is the required input for dependent gate revalidation.
Exact replay is idempotent. A changed idempotence key, base, selector, epoch,
watermark, path, blob, product, receipt, tool, evidence, or aggregate digest is
rejected before the frozen backlog exception receives policy credit.

## Integration and recovery boundary

The protected integration policy recognizes the exception only when the exact
nine-path candidate passes the verifier in `_src/tools/runner_transaction.py`.
Direct push, skipped validation, administrator status, or an unproved partial
candidate supplies no credit. Promotion remains an independent Integrator's
atomic compare-and-swap action. Before promotion, recovery is abandonment of
the candidate. After source integration, recovery requires a separately
authorized additive compensating transaction; no evidence or ref is deleted.
