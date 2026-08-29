# `0044-20` terminal-claim lifecycle governance integration evidence

## Assignment and pins

- Assignment: `1788039731603-52e3d8ff`.
- Integrator: `geordi`, privileged and independent of Architect `data`.
- Exact target: `main@9834ed04024962f7fb15e15f6843c2c9fa61cdeb`.
- Accepted source: `0044-20-terminal-claim-lifecycle-architecture-data-20260829@784bc64f25c09d6e9afd11869adc4ef9d0f016ad`.
- Source base: `2ffc0d2a26eea939b74ceb4754309ff2de22e5fb`.
- Claim-first REF: `c718ac7c1`.
- Real provenance-preserving merge REF: `8e08723eea7df49e9294528dce01177bc2bcbd8f` with trailer `Policy-Origin-Branch: main`.

## Scope and contract verification

The source worktree was clean. The awarded integration worktree started clean
at the exact target, which also equaled current `main`. The target delta from
the source base was exactly
`TODO-jadzia-0037-15-chain-20260829.md`, disjoint from the four architecture
paths. The real merge completed without a conflict.

The candidate changes exactly six authorized paths:

1. `TODO.md`
2. `TODO-data-0044-20-1788038395542-d19fafda.md`
3. `docs/dossiers/0044-20-terminal-claim-lifecycle-scope-review.md`
4. `docs/dossiers/dec-0044-033-terminal-claim-lifecycle.md`
5. `TODO-geordi-0044-20-1788039731603-52e3d8ff.md`
6. `docs/campaign-evidence/0044-20/governance-integration-geordi-20260829.md`

Independent contract assertions passed: exactly one `0044-20` Task exists;
its prerequisite is `0044-17`; it is a mandatory checkpoint; `0044-08`
depends on it; `DEC-0044-033` is a `decision-record@v1` with the
`cross-item-blast-radius` trigger and no waiver; the separate Architect review
is `scope-ok-with-conditions`, contains its binding conditions, and both
records name the bounded `0020-10` consumer boundary. No Feature `0020` path
is changed.

## Validation before root integration

- `git diff --check 9834ed040..HEAD`: PASS.
- `_src/tools/process_doc_doctor.py --root . --json`: exit `0`, `ok: true`,
  196 documents, 34 inherited findings including two inherited errors; neither
  error is in an awarded path.
- `_src/tools/legacy_task_doctor.py --root . --json`: global exit `1` with
  inherited findings, but the required attributable filter reports zero
  findings containing `0044-20` after the integration claim was canonicalized.
- Focused contract assertion script: PASS.

Pre-integration candidate hygiene, the immediate root preflight/equality/merge,
and immediate root postflight are recorded below after actual execution. Any
non-pass or target drift stops the integration.

## Integration gate result

- Candidate: `0bd235d4af98ebfc51c920db11c318c7106bb30a`.
- `check_integration_hygiene.py --candidate-ref 0bd235d4a --json`: exit `0`,
  `ok: true`, `findings: []`, 89 registered worktrees.
- Equality observation: current `main` was
  `ac63e74fadf1ea45fd2de7e74c7dd98ba0635770`, not awarded target
  `9834ed04024962f7fb15e15f6843c2c9fa61cdeb`.
- Intervening delta: one disjoint added path,
  `TODO-jadzia-distribution-20260829-03.md`.

**VERDICT: BLOCKED — target drift.** The exact-target gate stopped before the
root preflight or merge. No root mutation, postflight claim, candidate rebuild,
foreign cleanup, Feature `0020` action, implementation, Acceptance, or external
effect occurred. A fresh exact-baseline award is required to continue.

## R2 recovery result

Fresh recovery assignment `1788040319615-0a706b4b` authorized the canonical
Integrator claim path, adopted preserved candidate `ce9bcbd77826a9d74f6eb18ba91eee30124e2a0b`,
and pinned exact target `main@ac63e74fadf1ea45fd2de7e74c7dd98ba0635770`.
The prior cancelled assignment and both of its findings remain append-only.

Before R2 reconciliation, `main` had advanced to
`4945dbf8b375257656a2153d876b82cd2c1b9d6e`; the complete intervening delta
was the single added path `TODO-jadzia-0044-07-integration-20260829.md`.

**VERDICT: BLOCKED — further target drift.** The equality rule stopped R2
before any target merge, conflict resolution, candidate hygiene, root
preflight, root merge, or postflight. No foreign or root state was changed.

## R3 recovery pins

Fresh recovery assignment `1788040585988-e67acf77` adopts preserved candidate
`6e2b05c2337725ceb7b5e85ab265da8a9a0587cc` and pins exact held target
`main@2e8e8399944e25715443e61d1675dbe2835d0e29`. Jadzia confirmed the bounded
hold in `agent-inbox:1788040529307-14707a46`.

The target carry is exactly four added paths, which R3 requires to remain
byte-identical:

- `TODO-jadzia-distribution-20260829-03.md`
- `TODO-jadzia-0044-07-integration-20260829.md`
- `TODO-jadzia-0017-03-integration-20260829.md`
- `TODO-jadzia-0037-23-integration-20260829.md`

R1 and R2 findings remain append-only; R3 does not retroactively authorize
either stopped attempt.
