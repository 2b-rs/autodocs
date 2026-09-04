---
schema_version: "1.0"
id: "0037-09.02"
level: "subtask"
parent: "0037-09"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-03"
  - "0037-08"
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2237"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0037-09.02:0037-03, 0037-09.02:0037-08 Implement lifecycle, claim, authority/signature, criterion-evidence, closure, archive, and commit-reference validation.

## Scope

- **Claim:** `TODO-Gabriel-Detmer-0037-09.02-20260825T041620Z.md` (`owner_token: agent:gabriel-detmer-20260825t041620z:0037-09.02:20260825T041620Z` provenance; current `agent:gabriel-owosekun-20260825t043500z:0037-09.02:20260825T043500Z`)
  - **REF:** `d2fd153a97f21003583fabaa62f74618cd874df5`
  - **Implementation evidence (2026-08-25, Gabriel):** IV0910–IV0922 in `_src/tools/issue_validate.py`; negative fixtures `_src/tests/fixtures/0037-09.02/cases.json`; working-tree and staged-index coverage; `uv run python _src/tests/test_issue_validate.py` 13/13 OK. 0037-09.01 rules not weakened. Claim remains on branch `0037-09.02`. **Acceptance: ✓** (2026-08-27, Integrator `belanna`, independent of Implementer `Gabriel-Detmer`/`Gabriel-Owosekun` / owner_token `agent:gabriel-owosekun-20260825t043500z:0037-09.02:20260825T043500Z`). Original review: reviewed baseline `3aa10521fea7b18dff9c93b252e13d2e624d7480`; Review-REF `49e85efb0b71df751c7a337d20c00a127d3ee2a4`; verdict ACCEPTED. Re-verified after the `0037-09-wave-C` merge against merged tree `6b4f8bab94042246ca2a352210f0bda43bba9017`: delta on the reviewed files (`_src/tools/issue_validate.py`, `_src/tests/test_issue_validate.py`) confirmed purely sibling-additive (new provenance/projection code and one appended test class; zero deletions/modifications of the reviewed IV0910–IV0922 logic, fixtures, or property test); 17/17 rerun clean. Bookkeeping base `1969e055a5d9697b1db32ca15d5294b290d6f9fc`; AWARD `1787870158204-892fa008`. Full evidence: `docs/campaign-evidence/review-0037-09.02-belanna-20260827T210115Z/review.md` and `docs/campaign-evidence/0037-09.02-reverify-belanna-20260827T2236Z/reverify.md`. No checkpoint crossed or upward integration performed.

## Acceptance criteria

- **AC-001** Detect illegal transitions, missing/expired/overlapping/stale-base claims, invalid claim refs, completion without checked criteria/closure/reachable evidence/role approval, invalid/revoked signatures, non-commit or same-commit refs, false Feature closure, and archive/not-accepted inflation

## Definition of Done

Transition/race/signature/closure fixtures cover every state/disposition and fixed authority policy revision with deterministic diagnostics.
