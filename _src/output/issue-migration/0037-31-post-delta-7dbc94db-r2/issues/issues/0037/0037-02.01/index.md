---
schema_version: "1.0"
id: "0037-02.01"
level: "subtask"
parent: "0037-02"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2007"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

PREREQ: 0037-02.01:0037-01 Define the YAML runtime, dependency, security, and canonical serialization profile in `docs/pipeline/issue-yaml-profile.md`. REF: 5b93372971c7eda5455f323f0c9a59d46db2f5a4 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-02.01:b6c815ea4f21`). Abgenommene Baseline `5b93372971c7eda5455f323f0c9a59d46db2f5a4`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). issue-yaml-profile.md + 11 YAML-Probe-Fixtures vorhanden.

## Scope

- **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-02.01-b6c815ea4f21.md`, `owner_token: agent:perplexity:0037-02.01:b6c815ea4f21`, request ID `b6c815ea4f21`, `base_commit: pending-discovery`. Self-selected per `AGENTS.md` rule 3 as the first eligible subtask now that `0037-01` is `[x]`.

## Acceptance criteria

- **AC-001** Select and test one exact `ruamel.yaml` version for later pinning in root `pyproject.toml` and `requirements.lock`
- **AC-002** require safe YAML 1.2
- **AC-003** reject duplicate keys, aliases/anchors, merge keys, tags, multi-document streams, non-string keys, implicit timestamps, non-finite numbers, NUL/control characters, excessive aliases/depth/bytes, and ambiguous booleans/nulls
- **AC-004** define UTF-8/LF, key ordering, two-space indentation, quoted timestamps, final newline, and front-matter delimiters. Controlled writers rewrite only front matter or named structured sections and preserve unrelated Markdown bytes

## Definition of Done

A review-ready profile records the exact package/version/hash and supported Python range; executable probe fixtures demonstrate every accepted/rejected scalar and security limit without adding production parser behavior.
