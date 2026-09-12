---
schema_version: "1.0"
id: "0040-04"
level: "task"
parent: "0040"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:524"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Implement bidirectional evidence-to-code traceability at file and commit level, with a tool that reports broken or missing ends as findings. REF: `7437905a6a6c0b7987ab6870f19cc5fc45ff774b`.

## Scope

- **Reason (2026-08-18, trilateral agreement round 5):** Duplicate. `0037-17.02` (deterministic provenance graph and reverse indexes), `0037-17.03` (bounded forward/reverse trace query APIs with machine-readable output) and `0037-10.04` (`issuectl … trace`) already cover `RQ-TRACE-02/03/04`, and they build against the issue store that replaces `TODO.md` rather than against `TODO.md` itself. Finding E of the requirements baseline checked for duplication against `0039-01` only and missed `0037` — the defect is in the analysis, not in `0037`. `RQ-TRACE-01/02/03/04` are carried forward as requirements on `0037-17.02`/`0037-17.03`; no separate tool is built.
  - **Requirements covered:** `RQ-TRACE-01`, `RQ-TRACE-02`, `RQ-TRACE-03`, `RQ-TRACE-04`; decision `DEC-0040-004`.
  - **Context and explicit limit:** The customer decided **file and commit level**. Line- and symbol-level resolution is explicitly **not** an acceptance criterion and must not be introduced: it would reproduce exactly the failure mode of `T5`, where digest-bound records went stale on the next edit and blocked the whole repository. The forward direction (requirement → evidence) largely exists via `REF` and evidence directories; the **return direction** (evidence → requirement, code → requirement) is what is missing and what ASPICE's bidirectional practice actually requires.
  - **Integration review:** **mandatory** is *not* set. **No-checkpoint justification (architect):** the tool is read-only, repairs nothing, and is explicitly barred from becoming a blocking gate without a separate recorded decision — the precise coupling mistake of `T1`. Should implementation nevertheless propose a blocking integration, that proposal is itself a `RQ-DEC-05` decision and must be escalated rather than decided inside the Task.

### Campaign C — Process, standard references, and effectiveness

## Acceptance criteria

- **AC-001** A tested, cataloged tool under `_src/tools/` resolves, for a given Task/Feature, the evidence set and the touched files and commits, and resolves the reverse: for a given file or commit, the Tasks and requirements it serves. Missing, dangling, or unresolvable ends are reported as structured findings with exact path and identifier — never silently tolerated (`RQ-TRACE-04`). The evidence baseline of a closed item is shown to survive subsequent work (`RQ-TRACE-01`), with a regression test that proves a later Task cannot overwrite or delete it. The tool is registered in `docs/pipeline/tools.md`. It is **read-only** and repairs nothing

## Definition of Done

Committed with real `REF`; focused hermetic tests cover the forward direction, the return direction, a broken link, a missing evidence set, and a renamed file; the tool runs against the current repository and its output is retained as evidence; whether it is wired into `_src/validate.py` is deferred to `0040-09` and, if wired, must be advisory-only unless a recorded decision says otherwise.
