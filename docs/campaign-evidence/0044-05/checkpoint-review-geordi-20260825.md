# Task 0044-05 mandatory checkpoint review

**Outcome:** `rejected`

**Reviewed at:** `2026-08-25T20:29:44+02:00`

**Reviewer:** `geordi` (Geordi La Forge, privileged Team Enterprise Integrator)

**Authority:** `agent-inbox:jean-luc→geordi:1787682425261-41defefd`

**Candidate:** `1aeaed098eb28f4c56e5ec07de56e3b0334ffcf3`

**Expected target:** `refs/heads/main@5aefac8533bb85fec930851dbb6446608a34b352`

## Assignment, independence, and boundary

Project Lead `jean-luc` assigned the exact mandatory parent-checkpoint review,
Task Acceptance, and conditional atomic landing of `0044-05`. The reviewer is
distinct from Architect `data`, `.02` Implementer `gabriel`, `.03` Implementer
`belanna`, and parent-completion Implementer `belanna`. No waiver is used.

The assignment covers the complete `0044-05` package and its prerequisite-closed
review boundary only. It does not close Feature `0044`, activate broad matching,
accept unrelated Tasks, or authorize any other candidate.

## Pinned contract and topology

- The exact Task block at the candidate is `[x]`, retains
  `Integration review: mandatory`, and has contract SHA-256
  `f5df6a321eb41c1922c93fdbc6581bb2bd821fe15858927d2f7e95bd1e9a2e71`.
- `0044-04` is the direct accepted prerequisite boundary. Its current Acceptance
  block digest is
  `84457b57026c18ffb322c258b245263739f752838e622394c1b704498c8923ee`.
- The reviewed package includes child chain
  `0044-05.01 -> 0044-05.02 -> 0044-05.03 -> 0044-05` and product
  `2c563040563b350f26e6c85b0dccb8c211fdbdef`.
- Merge `7af5dc7848f5b7a35575f688ac4be0c446c005df` has exact ordered parents
  `5aefac8533bb85fec930851dbb6446608a34b352` then
  `4468a78d1d208bc81090ebed77de2fc34d602ed6`.
- The 20-path candidate manifest digest is
  `049d3027b2c7c84a0a3add01027f04e33f49e56eb510a18e40024c268a35aa0d`.

## Independently reproduced conforming evidence

- `python3 -m unittest _src.tests.test_capability_match`: 16 tests, exit `0`.
- The committed self-application invocation exits `0` and reproduces
  `result-belanna-0044-05.03.json` byte-for-byte.
- Legacy schema SHA-256 remains
  `ee553404d0e859e4fdd1876edb0d4dc8d016921f92818fbd143ba4ad71870955`.
- Focused `automation_safety.py`: `PASS`, two files, zero findings, zero policy
  errors, zero unresolved critical findings.
- `git diff --check 5aefac853..1aeaed098`: exit `0`.
- Product ancestry, exact topology, and the byte-identical dormant-pilot sentence
  in `AGENTS.md` and `docs/pipeline/capability-matching.md` were confirmed.
- No matcher wiring exists in `_src/generate.py` or `_src/validate.py`; broad
  repository activation and historic credit are not introduced.

These green checks do not close the finding below because the focused suite uses
the matcher's private validation functions and never proves that emitted or
committed instances conform to the published JSON Schemas.

## Finding F-0044-05-GEORDI-001 — published schemas contradict the contract

**Severity:** `major`

**Disposition:** `open; blocks Acceptance and integration`

The architecture and Task contract require closed, machine-readable schemas for
the profile, descriptor, and result. The committed schemas do not encode that
contract:

1. In `task-requirement-profile-v1.schema.json`, `test_scope` and
   `resource_bounds` each declare `additionalProperties: false` but declare no
   allowed `properties`. The committed self-application profile contains four
   fields in each object. Under JSON Schema 2020-12 those eight fields are all
   forbidden, so the evidence instance accepted by `capability_match.py` cannot
   validate against its own published schema.
2. The same schema gives `sources` no `items` contract. The result schema gives
   `descriptor_sha256` and `rejections` no `items` contracts. Their documented
   closed member shapes, required fields, patterns, and rejection structure are
   therefore not machine-enforced by the schemas.
3. `capability-match-result-v1.schema.json` closes the root with
   `additionalProperties: false` but does not declare `error`. Every documented
   invalid-input JSON result emitted by the CLI includes `error`; for example a
   legacy descriptor returns exit `2` with `error: SCHEMA_UNKNOWN_FIELD`. That
   output is forbidden by its claimed result schema.

Direct structural reproduction on the candidate reported:

```text
task.test_scope: additionalProperties=False allowed=[]
  forbidden=['command','derived_from','expected_evidence','kind']
task.resource_bounds: additionalProperties=False allowed=[]
  forbidden=['expected_token_range','max_cpu_seconds','max_memory_mib','max_wall_seconds']
invalid-result error field: root additionalProperties=False error_allowed=False
result.descriptor_sha256: items_declared=False
result.rejections: items_declared=False
profile.sources: items_declared=False
```

The environment does not provide the optional third-party `jsonschema` module;
the finding does not depend on it. It follows directly from the committed
Draft-2020-12 keywords and the exact committed instances. The absent validator
also exposes the focused suite's coverage gap; it is not itself a product
nonconformity because the implementation is required to remain stdlib-only.

This violates the parent acceptance criterion requiring JSON schemas for both
inputs, `.01`'s closed-schema and result contract, `.02`'s closed-schema
implementation criterion, and the package-completion claim of schema/tool/docs
consistency. A consumer validating against the schemas receives a different
answer from the matcher, including on the package's own self-application
evidence.

## Decision and recovery

Decision: `rejected`. The major finding is demonstrated on the exact candidate.
No implementation was repaired during review. No `Acceptance: ✓` bookkeeping,
checkpoint crossing, hygiene verdict, root merge, Feature closure, or broad
activation was performed.

The smallest corrective scope is Implementer-owned: complete the three JSON
Schemas so their nested instance/result shapes and invalid-input representation
match the approved architecture; add positive and negative schema-conformance
fixtures covering the real self-application profile/result and an invalid-input
CLI result; rerun the focused suite, legacy canary, self-application digest
comparison, automation-safety, and diff checks. A later independent review must
pin the corrected candidate and reconsider the complete package. The current
candidate and this rejected review remain append-only evidence.
