# Privileged integration claim — gov-0022-01 decision main integration

- **Owner token:** `agent:geordi:gov-0022-01-decision-main-integration:20260828T1151Z`
- **Capability class:** `privileged`
- **Authority:** priority-offer atomic award `1787917856827-753e4ea7`, accepted by Geordi on 2026-08-28.
- **Item / boundary:** `0022-01-governance-package` integration only; no Acceptance, checkpoint verdict, Feature/DONE move, product/backlog activation, gate change, cleanup, push, or scope widening.
- **Pinned main baseline:** `main@0e0650e664bae7519db7ed1a26656059c073a65b`.
- **Pinned source:** `gov-0022-01-decision-data-20260828@55439d98bc81be7ed19287d851569eb675e70cb4`; substantive `b2d87ae87d6cb6c635b57b29482f4afa0dc8276e`; reconciliation `7bf03e6963`.
- **Branch / worktree:** `integrate-gov-0022-01-geordi-20260828` / `.worktrees/integrate-gov-0022-01-geordi-20260828`.
- **Permitted source paths:** `docs/dossiers/dec-0022-001.md`; `docs/dossiers/0022-feature-breakdown-proposal.md`; `docs/campaign-evidence/0022-01/independent-scope-review-brief.md`; `docs/campaign-evidence/0022-01/independent-scope-review.md`; `TODO-data-0022-01-governance-package-1787912073801-8890cbdc.md`.
- **Write scope:** permitted source additions above; this claim; fresh integration evidence; conditional guarded root merge only after all assigned gates pass.

## Startup record

- Fresh isolated worktree is clean at the exact pinned baseline.
- Next: independently inspect source paths and digests, DEC identifier/conformance, authority blobs, Saru review identity/pins/binding conditions, and no-activation boundary. Stop and report any drift, conflict, collision, material mismatch, unexpected path, or nonzero gate.

## Review result before guarded merge

- Exact five-path carry verified byte-for-byte against source tip; no unexpected source path is staged.
- DEC identifier is unique at the pinned baseline; the `decision-record@v1` fields, independent Saru review identity/pin/verdict, all eight binding conditions, and the two required current-main `DEC-0020-002` authority blobs were independently rechecked.
- Review evidence: `docs/campaign-evidence/0022-01/governance-integration-geordi-20260828.md`.
- Conditional next: commit this bounded candidate, then run exact-candidate hygiene, root preflight, guarded root merge, and immediate postflight. Any nonzero gate stops without repair or cleanup.
