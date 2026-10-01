# Issue Derived-Artifacts and Regeneration DAG

Status: canonical process documentation for the **implemented** parts of the `issue-regeneration-dag@v1`
contract (Task `0037-19`). This baseline was defined by Task `0037-05` as an architecture
contract; this revision documents what is actually built and runnable today, and names the
gap to full end-to-end regeneration explicitly rather than describing it as done.

## Source and derived matrix

| Class | Paths / records | Authority | Rule |
|---|---|---|---|
| Canonical | `issues/**/*.md`, `provenance/**/*.json`, committed evidence | Git tree | Never regenerated; validate before every derived stage |
| Agent configuration | `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, `agent-workflow.json` | Git tree | Declared config inputs; digested into generation ID |
| Derived internal | `issues/_views/catalog.json`, `issues/_views/dependency-graph.json` | `issue_views.py` sole writer today | Rebuilt from canonical inputs only; see "What is actually implemented" below for the manifest's aspirational output paths |
| Derived public | public catalog/graph projections, page models, i18n register, localized HTML tree | Declared in the manifest, not yet built | See gap note below (Task `0037-25.01`) |
| Ephemeral | validation output and reports | run-local | Cannot be an input; stale/self-consuming reports are invalid |

## The manifest

`docs/pipeline/issue-derived-artifacts-v1.json` is the executable-shaped manifest for schema
`issue-regeneration-dag@v1`. It declares seven stages (`validate-canonical`,
`build-internal-catalog`, `build-public-projection`, `build-graphs`, `build-page-models`,
`render-html`, `render-reports`), each with a stable ID, argv array (never a shell string),
typed input globs, exact outputs, one sole writer, required status, retention, privacy,
determinism, promotion group, cleanup rule, and validator.

The deterministic generation ID is SHA-256 over declared canonical-input, schema, tool, and
configuration digests. UUIDv7 run IDs are allowed only in external execution-run manifests
and never embedded in deterministic artifacts.

### What is actually implemented today

Two independent things are real and runnable; a third, connecting them, is not yet built.

1. **Manifest structural validation is real.** `_src/tools/issue_validate.py` implements
   `_dag_structural_diagnostics()` against `DAG_SCHEMA = "issue-regeneration-dag@v1"` and
   `REQUIRED_STAGE_IDS` (the same seven IDs above). It rejects cycles, unknown/self
   dependencies, duplicate stage IDs, multiply-written or undeclared outputs, derived inputs
   without an exact producing stage, self-consuming or report-derived inputs, missing
   required stages, and malformed `argv` (non-array, empty, or containing shell
   metacharacters). Invoke it via:

   ```
   python3 _src/tools/issuectl.py validate --dag docs/pipeline/issue-derived-artifacts-v1.json --format human
   ```

   This prints `PASS` against the current manifest. Six fixtures exercise this validator —
   see "Fixtures" below — and `_src/tests/test_issue_validate.py` covers both the fixtures
   and this manifest (58/58 tests passing as of this revision).

2. **Catalog and graph views are real and computable/writable.** `_src/tools/issue_views.py`
   (`build_catalog`, `build_graph`, `render`) reads `issues/**/*.md` and produces a catalog
   document and a dependency-graph document, each carrying its own `generation_id`. Reachable
   two ways:
   - `python3 _src/tools/issuectl.py view --kind catalog --format human` (or `--kind graph`)
     computes the view in-process and prints it (JSON by default); this does not write to
     disk.
   - `python3 _src/tools/issue_views.py --write` persists the computed catalog and graph to
     `issues/_views/catalog.json` and `issues/_views/dependency-graph.json` — **these are the
     real current output paths**, not the manifest's declared
     `data/issue-catalog.internal.json` / `data/issue-graph.json`. `issuectl graph` and
     `issuectl list`/`trace` consume the same `render()` computation, not a separate stored
     artifact, so a stale on-disk view cannot silently diverge from what those commands
     report by default; passing `--require-views` to `issuectl view` (or `graph`/`list`/
     `trace`, which share the same flag) instead reads the committed
     `issues/_views/*.json` files and fails closed (`IssueViewsError`) if they are missing or
     no longer match a fresh `render()` of canonical input.
   - `_src/tools/issue_migration_report.py` (Task `0037-16`) is the separate, already
     terminal source/target cutover gate; it does not participate in this catalog/graph
     computation but is a canonical-input precondition other consumers rely on.

3. **The DAG is not yet wired to a single orchestrator that executes it end-to-end.** The
   manifest's per-stage `argv` (e.g. `issuectl.py render --catalog internal`,
   `issuectl.py render --page-models`, `generate.py --issues`, `issuectl.py report`) do not
   correspond to subcommands that exist yet. `issuectl.py`'s real subcommand set today is:
   `validate`, `view`, `graph`, `list`, `trace`, `create`, `edit`, `criterion-allocate`,
   `criterion-withdraw`, `criterion-supersede`, `criterion-move`, `prereq`, `relation`,
   `claim`, `renew`, `release`, `handoff`, `recover`, `finding`, `decision`,
   `criterion-check`, `close` — there is no `render` and no `report` subcommand, and
   `_src/generate.py` has no `--issues` flag. Implementing `issuectl regenerate --all` as the
   typed sandboxed-runner action that actually runs this manifest stage-by-stage is Task
   `0037-25.01`, which is still open and lists this task (`0037-19`) as one of its own
   prerequisites — i.e. this documentation is expected to exist before that orchestrator is
   built, not after. Until `0037-25.01` lands, "regeneration" in this repository means:
   validate the manifest structurally, then run the catalog/graph view path directly; there
   is no single command that walks all seven declared stages.

## Validation rules

The validator enforces: no cycles, no unknown dependencies, no duplicate IDs, no stage
depending on itself, no undeclared or multiply-written outputs, no derived input lacking its
producing stage, no report-derived inputs feeding another stage, no missing required stage,
and no invalid `argv`. Every committed derived path is meant to have exactly one stage and
validator once the remaining stages are implemented; today only `validate-canonical`'s
concern (issue-store validation, distinct from manifest-structure validation) and the
catalog/graph portion of `build-internal-catalog`/`build-graphs` have working implementations
behind them, per the mapping above. `issue-publication`, the promotion group that would
atomically publish catalog, graph, page model, i18n register, and localized HTML tree
together, remains declared but not yet reachable — no stage currently writes a public
projection, page model, i18n register, or localized HTML tree.

## Fixtures

Fixtures under `issues/_schema/fixtures/issue-regeneration-dag-v1/` cover a valid manifest
(`valid.json`) plus five structural-failure cases exercised by
`_src/tests/test_issue_validate.py`: `invalid-cycle.json`, `invalid-duplicate-writer.json`,
`invalid-missing-required-stage.json`, `invalid-report-self-consumption.json`, and
`invalid-stale-derived-input.json`.

## For a maintainer or agent today

- To check the manifest is still structurally sound after editing it: run the `validate --dag`
  command above.
- To see the current issue catalog or dependency graph: run `issuectl.py view --kind catalog`
  or `--kind graph`.
- To refresh the committed views after canonical issue changes: run
  `python3 _src/tools/issue_views.py --write` from the repository root, then re-run
  `issuectl.py view --require-views` to confirm the written views are not stale.
- Do not expect `issuectl.py render`, `issuectl.py report`, or `generate.py --issues` to
  exist yet; they are declared in the manifest for the future orchestrator (`0037-25.01`) and
  will be documented here once implemented, not before.
