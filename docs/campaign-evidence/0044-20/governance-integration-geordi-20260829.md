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
