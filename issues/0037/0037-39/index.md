---
schema_version: "1.0"
id: "0037-39"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-37"
  - "0037-51"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2223"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-39:0037-37, 0037-39:0037-51 Provision and verify the approved reproducible Python/Node/Graphviz rendering toolchain. **Claim:** `TODO-julian-0037-39-20260824T162900Z.md` (`agent:julian:0037-39:20260824T162900Z`). **Implementation completion (2026-08-24, Julian, unprivileged Programmer):** REF `7dcaf135c4323bf9f566baa2d9739e02c43bf0be`. Exact Python/Node/npm/Graphviz/parser versions, deterministic environment and canonical SVG rules are enforced by `tools/toolchain/manifest.json` and `tools/toolchain/check.py`; Python and Node dependencies are exact/locked, Noto Sans plus OFL are tracked and digest-bound, and canonical DOT/SVG fixtures reproduce byte-for-byte. Validation: focused suite 6/6 PASS; clean hash-locked Python install/parser probe/repeated render PASS; `npm ci --ignore-scripts` PASS (0 vulnerabilities); `git diff --check` PASS. **Acceptance: ✓** (2026-08-27, Integrator `paul`, unabhängig von Implementierer `Julian` / `agent:julian:0037-39:20260824T162900Z`). Abgenommene Baseline `7dcaf135c4323bf9f566baa2d9739e02c43bf0be`; Review-REF `b6d2bfdfe4850ad2cf7c1d898105088409e01378`; AWARD `1787865994204-934c578e`. No checkpoint crossed or upward integration performed.

## Scope

- **DEC-0037-002 execution model:** Provision and validate directly in the item worktree. A Dispatcher may select a Runner for a Task-ID-bound long job; the retired queue transport is not a prerequisite.

## Acceptance criteria

- **AC-001** Commit root `pyproject.toml`, hash-pinned `requirements.lock`, Node lock consistency, tracked font assets/licenses, and a toolchain manifest containing supported Python/Node/Graphviz versions, locale/timezone/environment variables, Graphviz flags, and SVG canonicalization rules selected by `0037-37`
- **AC-002** provide offline/clean install verification or explicit checks for approved system packages and reject version/font drift

## Definition of Done

A directly executing Programmer provisions/checks a clean environment in the item worktree and reproduces parser probes and fixed DOT/SVG fixtures byte-for-byte after canonicalization. A Dispatcher may instead select a Runner for a Task-ID-bound long provisioning or reproduction job; the retained job evidence includes progress, cancellation/recovery behavior, and exact inputs/results. Unsupported versions, missing fonts, locale/timezone drift, and unpinned dependencies fail with actionable rule IDs; neither direct execution nor Runner selection grants additional authority.
