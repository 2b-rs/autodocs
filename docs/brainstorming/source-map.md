# Source Map

This is a curated map of the repository's brainstorming-heavy material.
Nothing here is a TODO list; those remain in the project root.

## Root-level sources

| Source | Type | Notes |
|---|---|---|
| `SPEC_QUALITY_ROADMAP.md` | Roadmap / future-work memo | High-signal brainstorming file. It argues that the three quality checks form a causal chain and proposes a staged plan for provenance-aware triage, clustering, a per-record review view, and workflow reuse. |
| `README.md` | Entry / operational pointer | Mostly not brainstorming; included only indirectly because it points to the canonical maintenance and conventions docs. |
| `AGENTS.md` | Execution policy for automation | Operational rules, not brainstorming-heavy, but it frames how future automation ideas must be executed (`run.sh`, no direct script execution through MCP). |
| `BACKLOG.md` | Live checklist | Left in root as an active task list, not duplicated here. |
| `TODO.md` | Live checklist | Left in root by explicit exception. |

## `_src/` design sources

| Source | Type | Notes |
|---|---|---|
| `_src/SPEC_TRACEABILITY.md` | Design spec | Defines the intended long-term model for provenance, evidence, inference, claims, and traceability. This is one of the most important architectural idea documents in the repo. |
| `_src/SPEC_BUILD_PROCESS.md` | Process design | Defines the idealized 0–6 campaign lifecycle: invalidate, crosscheck, triage, AI decision, backend repair, evidence harvest, publish. Partly implemented, partly aspirational. |
| `_src/KONVENTIONEN.md` | Editorial design rules | Contains policy-level intent: language choices, truth-source rules, evidence expectations for AI text, and multilingual boundaries. |
| `_src/WARTUNG.md` | Maintenance philosophy | Explains the layering model (Spec-DB → KI-Kuratierung → Komposition → i18n → HTML) and the rule that generated trees are never manually edited. |
| `_src/ai/RICHTLINIEN.md` | AI curation policy | Governs how AI-generated explanations and diagrams should behave; directly tied to regeneration logic. |
| `_src/i18n/ANWEISUNG.md` | Translation policy | Machine-checkable invariants and design constraints for translation work. |

## Code/docstrings with strong design rationale

| Source | Type | Notes |
|---|---|---|
| `_src/tools/upstream_evidence.py` | Rationale-bearing tool docstring | Encodes the principle "Preserve raw evidence at every stage" and explains why immutable before-state capture is necessary before parser changes can be judged. |
| `_src/ai_workflow.py` | Workflow docstring | Documents the separate AI-content regeneration loop: invalidieren → auftrag → merge. |
| `_src/tools/curation_flags.py` | Workflow/rationale docstring | Explains why curation decisions become flags for a KI agent, and why that agent may propose but never self-apply. |
| `_src/tools/review_ingest.py` | Workflow/rationale docstring | Explains why the record is the leading, revision-safe store and why `text_hash` conflict detection exists. |

## How to use this folder

- Read `quality-roadmap.md` for unresolved quality/reporting ideas.
- Read `traceability-and-evidence.md` for the deeper provenance/inference
  architecture.
- Read `content-and-i18n.md` for policy-level thinking around AI-generated
  text, translation, maintenance, and editorial constraints.
