# 0044-13 final pre-neutralization inventory (R2)

Captured at `2026-08-28T21:20:07Z` after `DEC-0044-031` reached `autodocs/main@7892e40db1f5d208a85c0e13fd90288969b32d3f` and before either supervisor activation source, generated configuration, or supervisor-managed process was changed. Management authority: `agent-inbox:1787944900878-1dc85eda`. Decision-integration assignment `1787951447854-05003420` is accepted; Geordi's verified checkpoint result is `agent-inbox:1787951868724-26a33474`.

## Preserved executable and transaction state

- Live hook: `/Users/tobias.anton/devel/autodocs/.githooks/reference-transaction`
- Hook mode/size/inode/mtime: `-rwxr-xr-x`, `20798`, `113484015`, `2026-08-28T15:13:37+0200`
- Hook SHA-256: `a4393fc5aeb2986bb191c6c6aac34e844869bb67ff604e0225b9e35efb4ff9aa`
- Retained log: `/Users/tobias.anton/devel/autodocs/.git/autodocs/reference-transactions.jsonl`
- Log mode/size/inode/mtime: `-rw-------`, `48070`, `113485883`, `2026-08-28T22:08:17+0200`
- Log SHA-256: `e2224059c60364191b830476b35b720eb7ef034256288c132e6e6183f1883a5a`
- Log line count: `11`
- Pending regular-file count: `0`

The hook, retained log, and empty pending directory remain in place and unchanged. `pre-neutralization-files-r2.tar` preserves their bytes and metadata together with the complete generated Git-configuration directory, all current refs and ref reflogs, `packed-refs`, and the exact pre-neutralization supervisor source and tests. The archive contains `1272` entries and has SHA-256 `5df39837e671e826aff34c954852a4027ca41729a065c378f4bf5a4702a5a0ec`.

## Activation and source pins

- Generated agent Git configurations: `47`; configurations containing `hooksPath`: `47`.
- SHA-256 of the lexically sorted `shasum -a 256` listing for those configurations: `1cb9512595726be03725d5aae8d2cd956e6bfd092ab01667424e6a475b46e440`.
- Current Jean-Luc process has command-scope `core.hooksPath=/Users/tobias.anton/devel/autodocs/.githooks` and the same path in its generated global Git configuration.
- Active supervisor source: `agent-inbox/main@3d4f75f2f9a299e06eb9b967286597d157ec87b6`; source digests: `supervisor.py=b096b0bbad90fbe2b332d2fbc0781ed13fdcbcad711d1d87fbf386af93748d4b`, `test_supervisor.py=dad4238ef0c6f8317bb424e89bc0b8a83fc1645dd88dad1bd4224741e95e864c`.
- Prepared item-owned neutralization commit: `agent-inbox/contain-0044-13-supervisor-hook-activation-jean-luc-20260828@027b43f5b2dfdfed5609dfce6d089457906a1f8b`; it removes only the two generator emissions and updates the focused identity tests.

## Repository and recovery pins

- Autodocs `refs/heads/main`: `7892e40db1f5d208a85c0e13fd90288969b32d3f`.
- Complete lexically sorted `%(refname) %(objectname)` listing: `675` refs; SHA-256 `f337fcad0d254b43f9a29e953810aa05a5ec19f1e5bbc6b95669647b678a6215`.
- Main reflog head: `7892e40db1f5d208a85c0e13fd90288969b32d3f`, fast-forwarded from `9aa2124ebe94daba465c4dda364afcb877803055` by the accepted R6 integration.

No hook, retained log, pending item, ref, reflog, generated Git configuration, supervisor source, supervisor-managed process, backlog marker, Acceptance record, or integration evidence was changed while producing this inventory.
