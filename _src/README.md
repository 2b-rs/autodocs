# `_src/` — source and build-tooling map

This file is a navigation map of what currently lives under `_src/`, added by
Task `0038-24` alongside the `runner-host/` package relocation. It maps
existing categories to their current stable paths and records a deferred
clustering plan. It does **not** relocate anything: every path below stays
exactly where it is today; nothing here creates a second authoritative copy.

## What moved out of `_src/` (Task 0038-24)

The four privileged host execution scripts previously at `_src/run-loop.sh`,
`_src/perplexity-cpu-loop.js`, `_src/perplexity-echo.as`, and
`_src/perplexity-loop.applescript` now live under the root-level
[`runner-host/`](../runner-host/) package — see its
[`README.md`](../runner-host/README.md) and
[`MANIFEST.json`](../runner-host/MANIFEST.json). They were host-only
executables that never belonged conceptually to the generated-documentation
source tree; everything else described below is unchanged and stays under
`_src/`.

## Current top-level `_src/` categories

| Path | Category | Contents |
|---|---|---|
| `_src/*.md` (`ARCHITEKTUR.md`, `KONVENTIONEN.md`, `WARTUNG.md`, `SPEC_BUILD_PROCESS.md`, `SPEC_TRACEABILITY.md`, `SCHEMA_LANGUAGE.md`, `REQUIREMENT_TEXT_REPAIR.md`) | Normative build/maintenance docs | Architecture, conventions, maintenance guide, and spec-process documentation for the generator pipeline itself. |
| `_src/generate.py`, `_src/validate.py` | Build entry points | The two commands named in the project's golden rule (`python3 _src/generate.py && python3 _src/validate.py`). |
| `_src/extract.py`, `_src/build_indexes.py`, `_src/build_component_graph.py`, `_src/seqgen.py`, `_src/render_diagrams.py`, `_src/lib_docmodel.py`, `_src/lib_svgdiag.py` | Core generation pipeline | Spec extraction, index/graph building, sequence and diagram generation, and the shared document-model/SVG libraries the generator depends on. |
| `_src/i18n_extract.py`, `_src/i18n_translate.py`, `_src/i18n_diagrams.py`, `_src/lib_i18n.py` | i18n pipeline | Per-language extraction, translation, and diagram-localization stages plus their shared library. |
| `_src/ai_workflow.py` | AI trace/content workflow | Drives the `_src/ai/` trace generation and downstream content stages. |
| `_src/tools/publish_public_site.sh` | Publication | Pushes the built public tree to the deploy repo (see the project's Publication section in `CLAUDE.md`); the sole whole-site publisher (`0038-32` retired the former `_src/publish.sh`, see `docs/pipeline/tools.md`). |
| `_src/site.json` | Site/i18n configuration | Canonical language list and site-wide settings consumed by the generator and i18n stages. |
| `_src/runner-states.mmd` | Diagram source | Mermaid source for the runner state-machine diagram (see also `_src/tools/orphan-state-diagram/`, a separate frozen historical snapshot used to regenerate that specific diagram — not a live consumer of any tracked script path). |
| `_src/ai/` | Generated AI trace data | Per-class/service trace JSON consumed by the content pipeline. |
| `_src/content/` | Generated intermediate content | HTML fragment sources feeding the final generated tree. |
| `_src/data/` | Structured spec data | Normalized data extracted from the upstream specification. |
| `_src/diagrams/` | Generated diagram sources/outputs | Per-class/service `.dot`/`.svg` diagram artifacts. |
| `_src/sources/` | Page/source models | `_src/sources/pages/**` JSON page models consumed by the generator. |
| `_src/spec/` | Upstream specification inputs | PDF/spec inputs and caches consumed by `_src/tools/spec_upstream.py` and related extraction tooling. |
| `_src/templates/` | Generation templates | Templates used by the generator to render the final HTML tree. |
| `_src/i18n/` | i18n working data | Per-language work products, including the `_src/i18n/work/**` one-off write scripts tracked by `_src/tools/chore_tool_inventory_data.json`. |
| `_src/tools/` | Reusable project scripts | ~90 tracked automation/validation/bookkeeping tools; see [`docs/pipeline/tools.md`](../docs/pipeline/tools.md), the authoritative catalog. |
| `_src/tests/` | Hermetic test modules | ~40 `test_*.py` modules covering the tools above and the generator pipeline. |
| `_src/logs/` | Retained historical execution logs | Timestamped evidence directories predating the current `output/logs/<task-id>/<request-id>/` convention; not a live write target for new work. |

## Deferred clustering plan

The flat `_src/` top level mixes at least five conceptually distinct
concerns — generator pipeline, i18n pipeline, AI trace workflow, generated
intermediate data, and reusable tooling/tests — that have accreted
incrementally rather than by designed layout. A future clustering pass could
group these into subdirectories (for example `_src/pipeline/`, `_src/i18n/`
already exists as a natural boundary, `_src/generated/` for `content/`,
`data/`, `diagrams/`, `ai/`) without changing any tool's *logic*, only its
*path*.

This is deliberately **not** performed by Task `0038-24`: the Task's own
Definition of Done requires preserving stable paths for all non-host `_src`
sources and prohibits broadly relocating them or creating a second
authoritative compatibility copy in the same change that introduces
`runner-host/`. A path-stable move of this size also touches every tool's
default `--root`-relative paths, `docs/pipeline/tools.md`'s catalog, and
numerous fixture paths under `_src/tests/` — it needs its own bounded Task
with its own deterministic reference inventory, exactly the kind this
document's "Task 0038-24" precedent (see `runner-host/README.md`) already
demonstrates. Recorded here as a scoped, not-yet-scheduled backlog item rather
than performed silently or left undocumented.
