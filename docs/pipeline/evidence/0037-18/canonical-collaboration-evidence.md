# Task 0037-18: Canonical Collaboration Process Specification Evidence

## Overview

Task `0037-18` completes the normative specification of the canonical collaboration process in `docs/pipeline/issue-lifecycle.md`.

## Criteria Coverage

- **AC-001 (Collaboration Semantics):**
  - Canonical state mapping and transitions from legacy markers (`[ ]`, `[p]`, `[?]`, `[u]`, `[w]`, `[x]`).
  - Strict criteria evidence rules via `closure.json` with reachable commit/digest locators.
  - Same-clone CAS acquisition using `refs/autodocs/claims/<item-id>` and cross-clone integration rules.
  - Explicit lease lifecycle: `proposed`, `active`, `renewing`, `released`, `expired`, `takeover-pending`, `superseded`, `rejected`.
  - Parent-package aggregation and feature closure invariants.
  - Semantic-deadlock and intent-preserving backlog repair protocols.
  - Append-only tooling and collaboration suggestion handling.
  - Clear separation from requirement curation queue and ASPICE change management lifecycles.

- **AC-002 & AC-003 (Cutover & Bootstrap Boundary):**
  - Clearly designates `docs/pipeline/issue-lifecycle.md` as shadow/future specification until Feature 0037 cutover.
  - Identifies `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, and `agent-workflow.json` as the operative bootstrap bundle until cutover.

## Validation

Schema compliance and document consistency verified.
