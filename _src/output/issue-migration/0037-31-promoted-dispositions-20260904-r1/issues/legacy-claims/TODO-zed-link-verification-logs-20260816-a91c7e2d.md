# Temporary coordination claim — Link Verification Logs to Published Reports and Commit Evidence

request_id: link-verification-discovery-20260816-a91c7e2d
owner_token: agent:zed:user-directed-link-verification-logs:20260816-a91c7e2d
base_commit: pending-discovery
capability_class: sandboxed/grunt
state: [p]

## Assignment

User-directed work not represented by a single existing Task. No unrelated `TODO.md` item is marked `[p]`.

## User prompt provenance

# TASK INSTRUCTION: Link Verification Logs to Published Reports and Commit Evidence

## Context & Objectives
Under ASPICE SUP.8 (Configuration Management) and SUP.2/SWE.6 (Verification & Testing), all objective verification logs, qualification runs, and backlog closure diff records must be configuration-controlled, committed to Git, and discoverable via direct click paths from the published process and report pages. Ephemeral diagnostic scratchpads must be removed.
Distribute the work across subagents to avoid exceeding the context window.
## Scope of Work

### 1. Update Published Report Page Models (`_src/sources/pages/*.json`)
Ensure the following report models contain explicit links and descriptions referencing their respective archived log and evidence directories:

1. `_src/sources/pages/process.json`:
   - Under "Pipeline-Artefaktklassen" & "Runner-Laufpaare", link to `logs/backlog-bookkeeping-and-commit/` 
     and session task claims (`TODO-perplexity-*.md`).
2. `_src/sources/pages/build-reports.json`:
   - Add a "Verifikations- & Qualifikations-Protokolle" section linking to:
     - `logs/runner-qualification-0037-48/`
     - `logs/ref-commit-0037-37/`
     - `logs/ref-commit-0037-48/`
3. `_src/sources/pages/extraction-reports.json` & `traceability.json`:
   - Reference the spec truthing and crosscheck verification logs:
     - `logs/spec-truthing-evidence/`
     - `logs/spec-truthing-apply/`
4. `_src/sources/pages/curation-report.json` & `open-reviews.json`:
   - Under UI Validation, link to `_src/logs/validate-review-request-ui/` phase logs and `.rc` return codes.

## Intended write scope

- `_src/sources/pages/process.json`
- `_src/sources/pages/build-reports.json`
- `_src/sources/pages/extraction-reports.json`
- `_src/sources/pages/traceability.json`
- `_src/sources/pages/curation-report.json`
- `_src/sources/pages/open-reviews.json`
- This temporary claim file
- Root `run.sh` only as a one-use runner request envelope
- Retained validation/commit evidence under a new task-scoped `logs/` directory if the runner requires it

## Runner scope

1. Fixed read-only discovery: exact HEAD, authority state, index/worktree status, active claims, and singleton-slot state; zero mutation.
2. After non-execution edits: JSON/page-model validation, link/path checks, generated-output impact checks if applicable, and a path-limited substantive commit carrying verbatim user-prompt provenance.
3. Reconcile/delete this temporary claim only after authoritative commit evidence is available; any bookkeeping/claim cleanup commit remains separate if required.

## External resources

None. No network, credentials, external mutation, package installation, or privileged-agent dependency.

## Coordination and assumptions

- Independent page-model groups may be delegated to subagents with disjoint write sets.
- Existing active claims were checked for the six exact page paths; no overlap was found.
- Links will follow the page-model's established repository-link representation and language/style conventions, determined from the files before editing.
- Existing unrelated staged, unstaged, untracked, and active-claim work must be preserved.

## Progress

- 2026-08-16: Read `AGENTS.md`, `SANDBOX.md`, authoritative `TODO.md`, active claim inventory, and relevant live claims. Classified this session as sandboxed/grunt. Temporary claim created with `base_commit: pending-discovery`.

## Next step

Publish the fixed read-only discovery request if the singleton slot is free, then inspect/delegate the six disjoint page-model updates while awaiting the result.
