# Task 0044-05 mandatory checkpoint re-review

**Outcome:** `rejected`

**Reviewed at:** `2026-08-25T21:12:11+02:00`

**Reviewer:** `geordi` (Geordi La Forge, privileged Team Enterprise Integrator)

**Authority:** `agent-inbox:jean-luc→geordi:1787685001155-e6cde308`, relaying the
current user's Alternative-A authorization for a fresh independent re-review and
conditional supersession only if accepted

**Corrected candidate:** `b9d402d643a08f9a6b5466e7ba96c6b774f44e52`

**Expected target:** `refs/heads/main@5aefac8533bb85fec930851dbb6446608a34b352`

## Boundary and pinned state

The reviewer is independent of Architect `data`, `.02` Implementer `gabriel`,
`.03` Implementer `belanna`, and parent-completion Implementer `belanna`. The
current-user authorization permits additive supersession of the prior `[u]`
verdict only after a technically accepted re-review; it does not predetermine
the outcome.

- Parent marker: `[x]`; mandatory checkpoint retained; prior `[u]` verdict and
  rejected review `5208d4b31677792a9f9685085fa7053071f55938` reachable and
  unchanged.
- Exact current Task block SHA-256:
  `e91f6fa0f52da0f5763fb81ba425be603f52d22bbc6cdfde30f27cba9b7d1b09`.
- Exact 24-path `main..candidate` manifest SHA-256:
  `cb8696176fb195938836658c3b873d8fd56e8d9b8057c3f91ad4b6a1d8da2188`.
- Direct accepted prerequisite `0044-04` Acceptance-block SHA-256:
  `84457b57026c18ffb322c258b245263739f752838e622394c1b704498c8923ee`.
- `main`, original product `2c563040563b350f26e6c85b0dccb8c211fdbdef`,
  schema correction `e637660978fdbd1eb7f73dd115757b69b0819b63`, and blocked-verdict
  tip `016bbcc94ecc469bc7bb817ceacbf0acde52dc35` are ancestors of the
  corrected candidate.

## Closed prior finding and independently reproduced positive evidence

`F-0044-05-GEORDI-001` is closed on this candidate. The corrected nested
`sources`, `test_scope`, `resource_bounds`, `descriptor_sha256`, and
`rejections` shapes are present. The result schema now declares `error`,
requires it for `invalid-input`, and forbids it for ordinary results.

Independent runs on the exact candidate:

- `python3 -m unittest _src.tests.test_capability_match`: 19 tests, exit `0`.
- The committed profile, descriptor, successful result, and genuine legacy
  invalid-input result pass the committed structural schema validator.
- Self-application exits `0` and reproduces the committed successful result
  byte-for-byte.
- Legacy schema SHA-256 remains
  `ee553404d0e859e4fdd1876edb0d4dc8d016921f92818fbd143ba4ad71870955`.
- Focused automation safety: `PASS`, zero findings, policy errors, and
  unresolved critical findings.
- `git diff --check 5aefac853..b9d402d643`: exit `0`.
- The dormant-pilot sentence remains byte-identical in `AGENTS.md` and
  `docs/pipeline/capability-matching.md`; neither `_src/generate.py` nor
  `_src/validate.py` activates the matcher.

These positives do not close the separate full-contract finding below.

## Finding F-0044-05-GEORDI-002 — schemas still accept forbidden authority combinations

**Severity:** `major`

**Disposition:** `open; blocks Acceptance, verdict supersession, and integration`

The approved architecture states, normatively, that profile cross-field rules
are part of the closed contract and that the descriptor schema itself enforces
class/route consistency. In particular:

- `sandboxed-grunt` profiles may use `runner` or `none`, never `direct`;
- `unprivileged`/`privileged` profiles may use `direct` or `none`, never
  `runner`;
- `Integrator` profiles require privileged class and the named review rights;
- descriptors bind sandboxed class to `none` plus optional `runner`, and direct
  classes to exactly `direct` plus `none`; and
- `cognitive_classes_served` is a non-empty ordered prefix of
  `low, medium, high, critical`.

The corrected profile and descriptor schemas contain no `allOf`/`if`/`then`
constraints for these combinations. Their independent JSON Schema validator
therefore accepts instances that `capability_match.py` rejects before matching.
Three exact neighbor reproductions were run without modifying the candidate:

```text
profile sandboxed-direct:
  published_schema=ACCEPT
  matcher=REJECT SCHEMA_CROSS_FIELD:sandboxed-direct
descriptor privileged-runner:
  published_schema=ACCEPT
  matcher=REJECT SCHEMA_CROSS_FIELD:direct-routes
descriptor non-prefix cognitive:
  published_schema=ACCEPT
  matcher=REJECT SCHEMA_COGNITIVE_PREFIX
```

This is a second schema/tool inconsistency, distinct from the corrected missing
nested shapes. It violates architecture sections 5–7, the `.02` criterion that
closed schemas and cross-field authority constraints implement the `.01`
contract, and the parent completion claim of schema/tool/docs consistency. A
schema-valid profile or descriptor can still be unusable by the matching tool,
including combinations located directly on the capability-class authority
boundary the parent checkpoint exists to protect. The 19-test suite checks the
private matcher validator but has no negative schema-neighbor assertion for
these cross-field combinations.

## Decision and recovery

Decision: `rejected`. No implementation was repaired during re-review. The
prior `[u]` verdict remains current and is not superseded. No `Acceptance: ✓`,
checkpoint crossing, exact-candidate hygiene verdict, root preflight, `main`
advance, Feature closure, or broad activation was performed.

The smallest corrective scope is Implementer-owned: encode the normative
profile and descriptor cross-field constraints in the published JSON Schemas,
including class/execution, privileged-role/right, exact route-set, and cognitive
prefix rules; add schema-level negative-neighbor fixtures that show each
forbidden combination is rejected by the schema as well as the matcher. Then
rerun the complete corrected package and request another independently pinned
re-review. This rejected record and the earlier rejection remain append-only.
