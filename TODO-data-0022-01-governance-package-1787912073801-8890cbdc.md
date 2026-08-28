# Active claim — `0022-01` governance package

- **item:** `0022-01-governance-package`
- **related task:** `0022-01`
- **request_id:** `1787912073801-8890cbdc`
- **owner_token:** `agent:data:0022-01-governance-package:1787912073801-8890cbdc`
- **state:** `[x]` — bounded governance candidate complete
- **coordination_state:** `complete`
- **lease_active:** `false`
- **capability_class:** `privileged`
- **process role:** management-instantiated Architect and governance candidate author; not Implementer or Integrator
- **atomic award:** agent-inbox offer `1787912073801-8890cbdc`, awarded to `data` on 2026-08-28
- **planned duration:** 240 minutes
- **base_commit:** `main@8948a602320c7c0781ed9a578a42b664dfd2eff4`
- **branch:** `gov-0022-01-decision-data-20260828`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/gov-0022-01-decision-data-20260828`
- **decision allocation:** `DEC-0022-001`; allocated as the next collision-free `DEC-0022-*` identifier after a read-only scan of the exact base above returned no existing `DEC-0022-*` identifier
- **claim-first write scope:** this claim file only
- **write scope after Project Lead releases the claim-first gate:** this claim; `docs/dossiers/dec-0022-001.md`; `docs/dossiers/0022-feature-breakdown-proposal.md`; `docs/campaign-evidence/0022-01/independent-scope-review-brief.md`; `docs/campaign-evidence/0022-01/independent-scope-review.md`
- **execution scope:** direct local Git and bounded document validation in this worktree; no network, credentials, external systems, ECU execution, or shared-root mutation
- **must not:** edit `TODO.md`; mutate an operative gate or backlog; implement; accept; integrate; cross a checkpoint; move a Feature to `DONE.md`; advance `main`; install a shared validator; cite an authority source not reachable from the chosen governance baseline

## Exact inputs

- Proposal candidate: `0022-01@1d4776bb7112ea5bca689d80ac18f32e8d610018`.
- Proposal substantive REF: `0ce489193b5c50090340b327854d3c6dc21626cd`.
- Independent review substantive REF: `aebc93ede12ec979d7c84b3bf1574c48359429ec`.
- Independent review terminal tip: `184bae8c63f23cb15fc4ea7292b79fd53c4733ec`.
- Review verdict: `scope-ok-with-conditions`.
- Decision contract: `decision-record@v1` plus every binding review condition.

## Binding review conditions

1. `0023-11` is a use-time consumer only, not a new Task-start edge.
2. `0024-02` is a downstream use/release consumer only, not a new Task-start edge.
3. `0028-01` is future SYS.1 activation only, not a current `0022-01` start edge.
4. No broad/unconditional start edges are introduced.
5. `0022-02.02` remains candidate-root-only; no shared/default validator is registered.
6. Mechanical A1 fields precede any later operative Task-graph mutation; checkpoint reach remains bounded to the interface contract.
7. `not-decided` remains non-passing at every activation, use, and evidence gate.
8. The DEC is allocated on current `main` and cites only authority sources reachable from that baseline. If `DEC-0020-002` is unreachable, the exact required carry-in is reported to Jean-Luc before it enters scope.

## Startup and stop conditions

- Current `main` and the allocation point were rechecked before branch creation.
- The branch/worktree were created from the exact base above and contain no authored change except this claim.
- Substantive authoring starts only after Jean-Luc independently verifies and releases the committed claim-only REF.
- Material `main` drift, identifier collision, missing reachable authority, or conflict with the independent review stops the chain and returns evidence.
- The chain ends at a committed governance candidate/evidence return. Governance integration is a separate pinned award to Geordi.

## Waiting-state reconciliation

- **2026-08-28T11:20:22Z:** `main` advanced from the allocation point
  `8948a602320c7c0781ed9a578a42b664dfd2eff4` to
  `e38a688c56f01fd3d8ab825593ee899ea0c7b4f2`. The intervening delta changes
  only four foreign Geordi claim records; it does not touch this package's
  declared paths, decision sources, proposal/review inputs, or Task contract.
- A fresh scan of current `main` still finds no `DEC-0022-*` identifier. Both
  required authority inputs remain absent:
  `docs/dossiers/dec-0020-02-evidence-boundary-enforcement.md` and
  `docs/dossiers/0020-02-gate-scope-review.md`.
- Jean-Luc has routed recovery for the hygiene-blocked exact two-path carry-in
  (`agent-inbox:1787915135380-9dc007f3`). Substantive authoring remains stopped;
  the next action is unchanged: receive the new main REF, verify both exact
  paths and digests, then reconcile the governance branch before authoring.

## Terminal handoff

- **Unblock:** Project Lead message `agent-inbox:1787916756077-6a532a66`
  reported final `main@0dda470a9496434f3f0ff89a899e794ccf60df0e`;
  Integrator completion `agent-inbox:1787916822362-a7211389` confirmed candidate
  hygiene, root preflight, and postflight PASS. The two main-visible authority
  blobs exactly match the held inputs: decision `da4242a865aede7fa567c0a37ffc740b4ce24d7f`
  and review `1717e89262c557fda6fd5a86094d59f33a8a7351`.
- **Baseline reconciliation:** exact-candidate hygiene passed across 243
  registered worktrees. Current main was merged without conflict at
  `7bf03e6963442b06c6a52f1fc339fe164d2af12c`; no root checkout or main ref was
  mutated by Data.
- **Substantive REF:** `b2d87ae87d6cb6c635b57b29482f4afa0dc8276e`.
- **Products and SHA-256:** `docs/dossiers/dec-0022-001.md`
  `ed2c699904b2368f6e6364423c34866612ff9ab9889584d3d7a7511d4f6efc8b`;
  proposal `126774f75bac69f1c5dcc8784bfb4de61c1b55542a57e9d8afc2950b23177080`;
  review brief `ba59f8314d80ccf4dfbbba62484a1d63c903c3b9f91c58379a70d3f3e02ad3bc`;
  independent review `3c7573058dc80b650f163b5cfb3f6048e6333240435b992cc8c8e0a4e9c8b721`.
- **Validation:** `process_doc_doctor.py --root . --json` returned exit 0 and
  `ok: true`; its sole error is the unrelated pre-existing broken link in
  `docs/dossiers/0044-03-gate-scope-proposal.md`, and `DEC-0022-001` receives
  only the expected pre-integration unreferenced-decision advisory. Exact-path
  staged diff check passed.
- **Disposition:** Data's Architect/governance-candidate work is terminal and
  ownership is released. Separate privileged integration from this pinned
  candidate is required before any operative backlog mutation. This claim does
  not implement the SYS interface, edit `TODO.md`, accept work, cross a
  checkpoint, activate a gate, advance `main`, or close Feature `0022`.
