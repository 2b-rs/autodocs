# Feature 0040 main-integration candidate repair — 2026-08-20

## Purpose and scope

This is corrective implementation evidence, not an acceptance review or an
integration verdict. Independent review
`docs/pipeline/approvals/0040-feature-main-integration-review-worf-picard-20260820T000400Z.md`
(reviewer commit `ebc6c018afe571bf847ddbaa22343e89da937fe4`) rejected the
historical Feature `0040` candidate because it diverged from target `main` at
`74af28df766ab0e55c4c43dcaebd6631ce40aefb` and retained a superseded
normative two-class model.

The repair pulls only current target `main` policy into Feature branch `0040`.
This is permitted by `docs/pipeline/branch-workflow.md` *Integration policy
precedence*: target policy governs, and target-policy changes may be pulled into
the candidate. No policy originating on a foreign branch is imported.

## Corrective result

- Merge `c560fbc2fdc5bf39811a545894560f648364f49a` brings target `main`
  `c0a274e66fd36516e748a0d309bcd35fa5b7e561` into the candidate.
- `docs/pipeline/process-roles.md` now states the current three-class model:
  `sandboxed-grunt`, `unprivileged`, and `privileged`; execution and authority
  remain separate; `unprivileged` has direct execution but no acceptance or
  integration authority.
- The current normative role policy is English. Historical German source and
  review records remain unchanged as evidence. Historical two-class assertions
  are explicitly identified as superseded historical context, not current
  normative policy.
- The prior `DONE.md` closure/review/rejection records remain append-only. The
  `TODO.md` corrective task tracks revalidation of this repaired candidate; it
  does not grant acceptance or authorize a Feature-to-`main` merge.

## Boundaries and residual risk

This repair cannot make the historical `0040-09` acceptance current for the
new merge result and does not review or approve the repaired candidate. A fresh,
independently assigned privileged reviewer must inspect the candidate against the
current target policy before any Feature-to-`main` integration is reconsidered.

## User-prompt provenance (verbatim)

> ok then go ahead. use the correct key next time. Reopen the completed task/branch and let subagents perform the corrective action(s). After these things have been resolved, check again whether the 0039-01 blocker is resolved. if so, proceed to integration. A privileged integrator subagent shall be started to review & merge back the features that are ready.

> I hereby authorize the github ssh key for publishing the website. I accept the digest-bound Phase-6-package. What is DEC-0040-005? Explain in simple terms. New decision: The Project Manager Persona may act as a Management role. He is not omnipotent, but escalation level 2, i.e. if the unprivileged orchestrator cannot resolve an issue by himself. Exact authority of Project Manager remains tbd.

> Re github key: it may be the wrong key. The allowed keys' public keys have SHA256:wtCFvdCIurWZj2NT4deL9Rg9uwqsL5nj17jlaoTW7a0 or SHA256:+oo7DoLWJP3RtulD24fsHw57zTp/K3V9WrpGOKFT52M. Find the correct key in ~/devel/identities and configure the projekt to use it. Feature 0040: I've revisited the decision together with Picard already. So check again.
