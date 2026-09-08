---
schema_version: "1.0"
id: "0019-01"
level: "task"
parent: "0019"
state: "closed"
visibility: "internal"
prerequisites:
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2986"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

Establish the v0.6.0 source bill of materials and release-pinning policy. REF: `111a5b90527cb6cb5f2b5bdcf8fad3a0237c41dd`. Claim: `TODO-terra-1-0019-01-20260819T130000Z-b19c61d4.md`; owner_token: `agent:terra-1:0019-01:20260819T130000Z-b19c61d4`.

## Scope

- **Completion evidence (2026-08-19):** The committed `score-source-bom@v1` pins `eclipse-score/score@v0.6.0` (`db1f5bb87ad7f41b40b6aca4b96a889d8798735e`, path `docs`) and the release-declared `process_description@v1.6.0` (`04e9cd30bc657033a764dbb75f07e03e4ccbbc12`, path `process`), with Apache-2.0 licence paths and deterministic `git archive` SHA-256 values. Build/render-only `tooling` and `docs-as-code` dependencies are explicitly excluded. `python3 _src/tests/test_score_campaign_manifest.py` passed 11 tests; `python3 _src/tools/score_campaign_manifest.py --require-complete _src/spec/campaigns/eclipse-score-v0.6.0.json` passed; and local clone verification checked every origin, commit, and archive hash. No acceptance review is claimed.

## Acceptance criteria

- **AC-001** A reviewed `_src/spec/campaigns/eclipse-score-v0.6.0.json` exists and lists every in-scope repository/component, upstream release label/ref, resolved immutable commit SHA, source URL, source-tree path(s), content/archive hash, license/source notice, and `score_scrape.py` revision
- **AC-002** exclusions and their rationale are recorded
- **AC-003** the manifest validates against the campaign schema

## Definition of Done

Manifest/schema validation and a reproducibility check pass; the manifest is committed; the source set is sufficient to re-fetch or verify every imported artifact without referring to `main`.
