# Traceability and Evidence

This file consolidates the deeper design thinking spread across
`_src/SPEC_TRACEABILITY.md`, `_src/SPEC_BUILD_PROCESS.md`, and the rationale in
`_src/tools/upstream_evidence.py`.

## Big architectural goal

The long-term model is not just "scrape facts from PDFs". It is:

- every fact must have provenance,
- direct extraction and inference must be separable,
- weak evidence may be preserved even before it becomes a canonical fact,
- evidence outlives the current interpretation,
- generated HTML/CSV/diagram artifacts are disposable.

This is the conceptual center of the spec-record architecture.

## Key ideas from `SPEC_TRACEABILITY.md`

### No fact without provenance

No record field should be persisted without a traceability entry.

### Separate asserted from inferred

A stored value should be classifiable as something like:
- asserted,
- inferred,
- conflicting,
- rejected.

### Evidence can be plural and durable

A fact may have multiple supporting pieces of evidence; traceability is not a
single backlink.

### Weak or rejected evidence should still survive

The design explicitly values preserving weak, conflicting, or rejected
material, rather than only the currently accepted interpretation.

## Key ideas from `SPEC_BUILD_PROCESS.md`

### Campaign-driven rebuilds

A spec rebuild should happen as a named campaign, so history, reports, and
status transitions stay attributable.

### Three-way field comparison

Each field should ideally keep three voices:
- backend A,
- backend B,
- legacy DB value.

That makes DB correction a transparent decision, not a silent overwrite.

### AI decision is about extraction truth, not standard truth

The AI-decider is allowed to resolve ambiguous extraction outcomes, but not to
invent or reinterpret what the standard means when the source is silent.

### Informal evidence is allowed, but carefully bounded

Evidence from prose, examples, documentation, or code may support a claim or
suggest a missing element — but must never silently become a published fact.
New elements become hypotheses first.

## Key idea from `upstream_evidence.py`

The tool docstring adds a crucial operational refinement:

> Preserve raw evidence at every stage.

Before parser logic changes, the **before-state** must be captured as an
immutable observation. Otherwise, a later improvement or regression cannot be
judged fairly, because the original evidence trail has been overwritten.

This is especially important because so much of the repository's quality work
is iterative parser repair.

## Tension / unresolved design space

This combined design suggests a system more expressive than the currently
materialized records:

| Design ambition | Current reality |
|---|---|
| Every fact has explicit provenance | Only partially materialized today |
| Rich evidence / counter-evidence / claim model | Mostly described, not broadly populated in live records |
| Inference with durable traceability | Designed, but not yet a large implemented inference layer |
| Campaign manifests and full history everywhere | Pilot-only / unevenly materialized |

## Why this matters

Without this architecture, the DB is just a cache of current extraction
results. With it, the DB becomes a **reviewable knowledge base** where facts,
claims, corrections, uncertainty, and evidence can coexist without being
flattened into one silent current value.
