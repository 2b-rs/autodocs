# Reusable Tool Creation and Continuous Improvement Process

**Status:** Candidate normative process. It becomes a baseline only through independent review and an explicit authority decision. It does not authorize product architecture, acceptance, release, safety/security/privacy risk acceptance, credentials, network access, external mutation, tool registration, or production execution.

## 1. Boundary and layers

This process governs reusable libraries, validators, planners, generators, controlled mutators, migrations, reporters, and adapters. It is separate from Feature definition (`feature-definition-and-breakdown.md`) and from Task acceptance. A candidate is not a qualified, registered, or deployed tool.

| Layer | Accountable role | Permitted outcome | Prohibited outcome |
|---|---|---|---|
| Control | Process owner | Lifecycle/profile decision record | Self-authorization or risk acceptance |
| Tool | Semantic owner | Typed, bounded findings or planned effect | Hidden scope expansion or self-qualification |
| Execution | Runner/operation owner | Allowlisted typed action under a profile | Generic shell, arbitrary executable, or requester arguments |
| Evidence | Evidence owner | Immutable attempt/result and compact evidence | Rewriting authority or persisting secrets |

## 2. Lifecycle and gates

1. **Discover.** Record the recurring need, baseline cost/risk, semantic signature, and reuse-before-create search across catalog, typed actions, code, tests, proposals, deprecations, and third-party options.
2. **Decide.** An accountable authority records reuse, configure, extend, consolidate, create, acquire, remain manual, or reject. Occurrence counts are pilot hypotheses, never automatic productization gates.
3. **Isolate candidate.** Pin candidate bytes, contract, fixtures, inputs, expected access, resource bounds, and non-production profile. Candidate code has no credentials, network, live target, or registry authority.
4. **Qualify.** Test deterministic interface, modes, scope, negative/recovery cases, concurrency, security/privacy controls, failure injection, and canaries for one exact profile.
5. **Review and pilot.** An independent reviewer evaluates a pinned package, baseline comparison, residual limits, semantic owner, and explicit deployment-or-rejection decision.
6. **Register/deploy only by separate authority.** A future registration binds exact implementation digest, typed action, argument builder, profile, configuration, and consumer. Unknown actions, generic shell, arbitrary repository scripts, candidate paths, and unreviewed versions are rejected.
7. **Operate and improve.** Measure real results, assess drift and duplicate signals, consolidate one semantic core where evidence supports it, and requalify material change.
8. **Suspend, deprecate, or retire.** Suspend on credible unsafe/unknown behavior; retire consumers, actions, configurations, credentials, and authority before removing execution capability while retaining history.

## 3. Role, action, and decision boundaries

| Role | Owns | May decide | Must not decide or perform alone |
|---|---|---|---|
| Process owner | Process version, tailoring, measures, and improvement records | Candidate-process changes within the declared scope | Product architecture, acceptance, deployment, or risk acceptance |
| Semantic owner | Tool meaning, contract, compatibility, support, and retirement plan | Bounded semantic implementation and compatibility analysis | Qualification, registry registration, or override of an authority gate |
| Operation owner | Typed action/profile implementation and recovery mechanics | Allowlisted execution mechanics within an approved profile | Generic shell dispatch, arbitrary executable paths, candidate promotion, or self-registration |
| Evidence owner | Immutable attempt/result records and compact evidence | Evidence retention and factual correction | Rewrite authority, suppress failures, or retain secrets |
| Independent reviewer | Qualification package and pilot review | Qualified-for-profile, revise, reject, suspend, or retire recommendation | Self-review of authored work or a separate product/safety/privacy/release decision |
| Named authority | Registration, deployment, exceptions, and risk decisions in its remit | The exact recorded decision | Open-ended execution permission or an unbounded exception |

A proposal, qualification decision, registration decision, deployment decision, and retirement decision are separate records. A candidate-package PASS is evidence of structural completeness only; it is never a qualification, registration, deployment, or acceptance decision.

## 4. Required contracts and boundaries

A reusable tool/action contract MUST define identity/version/digest; purpose and non-goals; typed inputs/configuration; stable outputs/statuses; read-only, dry-run, JSON, and separately authorized apply modes; exact/derived scope; side-effect class; determinism; idempotency/retry/recovery; resource/concurrency limits; privacy/network/credential policy; result/evidence schema; compatibility; semantic owner; qualification profile; and deprecation/retirement triggers.

`--check` does not repair, install, or register. `--dry-run` follows apply planning without effects. A trusted action implementation builds argument vectors only from validated typed fields. The `0037-46.01` queue is the future production action boundary; legacy mechanisms map to one typed action or a retirement trigger and do not become a competing protocol.

| Side-effect class | Retry rule |
|---|---|
| Read-only | Retry only after recording input/result identity. |
| Candidate-writing | Retry in a fresh isolated candidate root. |
| Atomic local | Verify preimage and idempotency key before retry. |
| Transactional/per-item resumable | Preserve journal and receipts; resume only stable incomplete items. |
| External/irreversible | Never blind-retry; reconcile by idempotency key and escalate unknown state. |

Defaults are no network, credential, external mutation, or undeclared path access. A credential is an opaque approved handle, never a secret in a contract or result. Unknown derived scope, traversal, symlink escape, unexpected access, stale preimage, or evidence/source alias fails closed.

## 5. Qualification, review, and evidence

Qualification plans cover schema/unit checks, hermetic determinism, hostile-path and injection cases, concurrency/collision behavior, failure injection at every commit point, and known-bad canaries. Exit zero or output presence is not PASS. A result is PASS only with all mandatory stages/canaries, no error finding, planned effects, and persisted immutable evidence; otherwise it is FAIL, SKIP under a declared condition, or INCONCLUSIVE.

One semantic owner is accountable for meaning, compatibility, support, qualification, measures, and retirement. Registry administration is a separate control role. Independent review is required before a candidate becomes qualified for any profile; authors and sole validation producers do not self-approve. Review does not grant any separate product, safety, privacy, release, or external-service authority.

## 6. Pilots, measures, and continuous improvement

Before a pilot, pre-register matched work units, source snapshot, baseline and candidate identities, method order, measurement window, exclusions, and acceptance oracle. Preserve failures and report each pilot shape separately:

- one new reusable capability; and
- one extension or consolidation of an existing semantic core.

Measure safety, first-attempt success, wall-clock and active time separately from queue wait, retries and reconciliation, context needed to start/review/recover, maintenance effort, and unique retained evidence volume. Every measure names source, denominator, baseline, owner, privacy class, and bias/limitation. Automation counts do not demonstrate performance, innovation, or process capability.

An improvement record may propose retain, revise, consolidate, suspend, deprecate, or retire. It names the evidence, semantic owner, affected consumers/actions/configurations, compatibility/migration plan, requalification need, expiry, and decision authority. A retired tool retains historical results but loses ordinary execution authority.

## 7. Exceptions and migration

An emergency exception is unavailable for schedule pressure or convenience. It requires named incident and specialist authorities, an exact digest and typed action, least privilege, bounded scope, immutable result, recovery journal, kill switch, compensating controls, and expiry of one operation or 24 hours. It returns to suspension; repeated exception use never becomes qualification.

Until `0037` cutover, `TODO.md`/claims remain authoritative. After cutover, the issue store and `0037-46.01` typed queue carry the corresponding catalog/action records. No migration may dual-maintain competing authorities or promote a candidate merely by documenting it.

## 8. Automotive SPICE relationship

This process is process support only. Its improvement, reuse, configuration, verification, measurement, and evidence practices may support later assessment preparation, but no tool, pilot, metric, or review asserts Automotive SPICE capability, conformity, ISO 26262 tool confidence, or product suitability.
