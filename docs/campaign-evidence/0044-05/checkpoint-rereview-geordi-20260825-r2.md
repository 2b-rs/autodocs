# Task 0044-05 mandatory checkpoint re-review — second correction

**Outcome:** `accepted`

**Reviewed at:** `2026-08-25T21:26:00+02:00`

**Reviewer:** `geordi` (Geordi La Forge, privileged Team Enterprise Integrator)

**Authority:** `agent-inbox:jean-luc→geordi:1787685806304-66071b55`, queued
after the separately assigned 0038 governance review and authorizing a fresh
independent review of the exact correction plus conditional additive verdict
supersession under the repository owner's already recorded authorization

**Reviewed candidate:** `74d3a6fb90b79f5dac9fb26d22f78223f268617e`

**Corrective product:** `5bd9d880ff89b81fce04cc5f893a07010638d52d`

**Binding blocked baseline:** `6940900f67c26e2e9d4e0118c5d9b7e06bb229e8`

## Pinned boundary

The reviewer is independent of Architect `data`, schema/matcher Implementer
`gabriel`, governance Implementer `belanna`, and parent-package Implementer
`belanna`. The assignment permits neither silent repair nor a weakened
contract. The current-user Alternative-A authorization cited by the blocked
verdict permits additive supersession only after an accepted fresh review.

- Exact reviewed Task block SHA-256:
  `b52e21551d3d81ea690300727c6cf5a5e5dadc57ad1287354e783ba3a176262f`.
- Exact five-path correction manifest SHA-256 (path, NUL, blob SHA-256, LF):
  `ae89b3e312c9a851ea0a141896a7113109909cd6091568697b766c7b7f458f92`.
- Direct accepted prerequisite `0044-04` block SHA-256:
  `a33f73d8500b9a5e5fbc755119e1169fa5aa37b3133854b4e7ca481aad26cbd6`.
- The blocked baseline, rejected candidate, both prior rejected reviews, and
  their additive verdicts are reachable and remain append-only.

## Independent validation

The complete architecture and Task contract were reread, including sections
5–7 of `capability-matcher-architecture.md`, all three child packages, the
parent package-completion records, both prior findings, the dormant-pilot
boundary, and the prerequisite-closed Acceptance rule.

Fresh runs on the exact reviewed candidate:

- `python3 -m unittest _src.tests.test_capability_match`: **21 tests**, exit 0.
- `python3 -m py_compile` for matcher and test module: exit 0.
- focused `automation_safety.py` for the changed test module: **PASS**, zero
  findings, policy errors, and unresolved critical findings.
- committed self-application profile, descriptor, successful result, and real
  invalid-input result: all **VALID** against their published schemas.
- `git diff --check 6940900f67..74d3a6fb90`: exit 0.

The three exact neighbors from `F-0044-05-GEORDI-002` were independently
reproduced against both the blocked and corrected schemas:

| Neighbor | Blocked schema | Corrected schema | Matcher |
|---|---|---|---|
| sandboxed-grunt profile with `direct` | ACCEPT | REJECT | REJECT |
| privileged descriptor with `runner` | ACCEPT | REJECT | REJECT |
| cognitive classes `[low, high]` | ACCEPT | REJECT | REJECT |

Positive boundaries also remain covered: allowed sandboxed `none`/`runner`,
direct-class routes, a privileged Integrator with both required rights, and all
four valid cognitive prefixes pass schema and matcher validation.

Protected implementation bytes are unchanged from the blocked baseline:

- matcher SHA-256:
  `d607740fdec98fadc35688d46ce8da7b6e62e71d3ad8dd51107313677f8af828`;
- result-schema SHA-256:
  `5dfada1ae6d8e67ad3ce26076b98fca8553ffc7e197e182834a663b82eaea551`;
- legacy-schema SHA-256:
  `ee553404d0e859e4fdd1876edb0d4dc8d016921f92818fbd143ba4ad71870955`.

## Finding disposition and decision

- `F-0044-05-GEORDI-001`: closed; nested shapes and conditional invalid-input
  result remain schema-valid and independently exercised.
- `F-0044-05-GEORDI-002`: closed; the published schemas now encode the
  normative class/route, Integrator/right, privileged-right, exact descriptor
  route-set, and cognitive-prefix constraints, with schema/matcher neighbor
  tests.
- No new material finding was identified. Broad dispatch activation remains
  absent; the matcher remains a bounded Feature-0044 pilot and grants no
  assignment, authority, independence, Acceptance, waiver, or scope.

Decision: `accepted`. The exact parent checkpoint and its `.01`, `.02`, and
`.03` package members are eligible for individual prerequisite-closed
Acceptance bookkeeping. The current `[u]` verdict may be superseded only by a
separate additive bookkeeping commit referencing this real review REF and the
repository owner's recorded authorization. Integration still depends on an
unchanged target, compare-and-swap, exact-candidate hygiene, and root preflight.
