---
schema_version: "1.0"
id: "0002-01"
level: "task"
parent: "0002"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:92"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

define the target audience and scope of the published process description: curator/maintainer-facing operational documentation, not AGENT-only rules — DECIDED 2026-08-14: audience is **both** curators/maintainers and AI agents, but with a key distinction the page must respect: the published process description documents the pipeline (what happens, in what order, what artifacts flow where) for human/agent readers alike; it is NOT the place for the actual AI-agent operating instructions (e.g. `AGENTS.md`-style directives). Those instructions are themselves **curatable artifacts that flow through the process pipeline** (subject to review/curation like other pipeline inputs), not static reference documentation — so they get referenced/linked from the process page as "an artifact type in the pipeline," but their content is not authored on this page. TODO (design impact for 0002-03 onward): the page structure must (a) include a section identifying agent-instruction files as a pipeline artifact/input class alongside specs, translations, and diagrams, and (b) link to wherever those instruction files live and to their curation-queue entries, rather than embedding or duplicating instruction content.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
