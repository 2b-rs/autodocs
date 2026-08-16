# Issue Derived-Artifacts and Regeneration DAG

Status: review-ready architecture contract for task 0037-05. This contract defines `issue-regeneration-dag@v1`; it does not activate production generators.

## Source and derived matrix

| Class | Paths / records | Authority | Rule |
|---|---|---|---|
| Canonical | `issues/**/*.md`, `provenance/**/*.json`, committed evidence | Git tree | Never regenerated; validate before every derived stage |
| Agent configuration | `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, `agent-workflow.json` | Git tree | Declared config inputs; digested into generation ID |
| Derived internal | `data/issue-catalog.internal.json`, graph JSON/DOT/SVG | DAG stage sole writer | Rebuild from canonical inputs only |
| Derived public | public catalog, page models, i18n register, localized HTML tree | DAG stage sole writer | Omit restricted data; atomic promotion as one group |
| Ephemeral | validation output and reports | run-local | Cannot be an input; stale/self-consuming reports are invalid |

## Manifest rules

`docs/pipeline/issue-derived-artifacts-v1.json` is the complete executable manifest. Each stage has a stable ID, argv array (never a shell string), typed input globs, exact outputs, one sole writer, required status, retention, privacy, determinism, promotion group, cleanup rule, and validator.

The deterministic generation ID is SHA-256 over declared canonical-input, schema, tool, and configuration digests. UUIDv7 run IDs are allowed only in external execution-run manifests and never embedded in deterministic artifacts. No SQLite stage exists in v1.

## Validation rules

Reject cycles, unknown dependencies, duplicate IDs, a stage that depends on itself, undeclared/multiply written outputs, derived inputs without their producing stage, report inputs, missing required stages, and an invalid argv. Every committed derived path has exactly one stage and validator. `issue-publication` promotes the catalog, graph, page model, i18n register, and localized HTML tree atomically after all validators pass.

## Fixtures

Fixtures under `issues/_schema/fixtures/issue-regeneration-dag-v1/` cover a valid manifest plus cycle, duplicate-writer, stale/derived-input-without-producer, report-self-consumption, and missing-required-stage failures.
