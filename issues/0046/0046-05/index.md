---
schema_version: "1.0"
id: "0046-05"
level: "task"
parent: "0046"
state: "open"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:982"
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
  - id: "AC-005"
    status: "active"
---

## Goal

(P0; Integration review: mandatory) Produce the redacted public agent-description projection, validate privacy/abuse controls, and atomically publish it through the canonical item-owned staging path to `2b-rs/autodocs`.

## Scope

- **Prerequisites:** `0046-03`.
  - **Planned order:** position `10`; may run in parallel with `0046-04`.
  - **Test scope:** `end_to_end+security`; whole-output forbidden-content scan, manifest/digest/source binding, dry-run retention, partial rebuild/publish, stale candidate, remote failure, restart and rollback.
  - **Capability profile:** `capability_class=privileged; execution_needs=direct; cognitive_demand=critical; independence="implementer cannot approve content, certify release, accept checkpoint or deploy without explicit publication authority"`.
  - **Branch/worktree:** `parent: "0046"; name: "0046-05"; worktree: "/Users/tobias.anton/devel/autodocs/.worktrees/0046-05"`; publisher runs only in this item-owned worktree.
  - **Exhaustive write scope (autodocs source):** `_src/tools/render_public_agent_profiles.py`, `_src/tests/test_render_public_agent_profiles.py`, `_src/tools/publish_public_site.sh`, `_src/tests/test_publish_public_site.py`, `_src/templates/public_agent_profile.html`, `docs/pipeline/agent-profile-public-manifest-schema.json`, `docs/pipeline/agent-profile-publication-receipt-schema.json`, `output/publish-export/files_to_export.txt`, `output/publish-export/tree/**`; external promotion scope is only the generated public tree on `2b-rs/autodocs:publish-main` under separately explicit publication authority.
  - **A1:** `target_policy_check: { field: A1-target-policy-integrability, verdict: fits, checked_target: main, basis: "REQ-0046-09/10/12/13/14/15 and canonical item-owned public publisher boundaries", checked_at: "2026-09-01T07:46:00Z", recorded_by: "agent:data:agent-profile-feedback-loop-architecture-20260901:1788246769727-b6ee15d5" }`.
  - **Review rationale:** public release, privacy/security and external-effect checkpoint.

## Acceptance criteria

- **AC-001** only allow-listed redacted HTML/assets enter the fresh standalone staging repo
- **AC-002** raw sources/prompts/profiles/secrets/internal controls/private provenance are absent
- **AC-003** source/export/digests/remote receipt bind exactly
- **AC-004** generated output never enters source-history `main`
- **AC-005** failure/rollback are recoverable

## Definition of Done

source/tests/schemas and dry-run evidence committed; actual external promotion occurs only under explicit authority and records exact remote/public receipt.
