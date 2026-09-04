# TODO-perplexity-0037-02.03-e29f6c81b4d7.md — active claim

## Claim identity

- `task_id`: 0037-02.03
- `feature_id`: 0037
request_id: f83a2d6c9e14
owner_token: agent:perplexity:0037-02.03:f83a2d6c9e14
base_commit: 428d308b61583cbf34edd06d23a0b8a9563d38ec
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [x]

## Why self-selected

Both prerequisites (`0037-02.01`, `0037-02.02`) are now `[x]`; first eligible item in file
order per `AGENTS.md` rule 3. Completing this also closes parent Task `0037-02`.

## Task text (verbatim)

- [ ] **0037-02.03** PREREQ: 0037-02.03:0037-02.01, 0037-02.03:0037-02.02 Commit executable
  normalized-object schemas and fixtures for the issue item format.
  - **Acceptance criteria:** `issues/_schema/issue-item-v1.schema.json` defines
    required/optional fields, closed unknown-field behavior, enums, timestamps-as-strings,
    parent/prefix/path rules, prerequisites, labels, work types, origins/relations,
    publication class, authority requirements, criteria/tombstones/supersession,
    extension/version negotiation, and limits. Schema validation occurs after strict
    front-matter parsing; schema success never substitutes for Markdown/path/graph
    validation.
  - **Definition of Done:** Schema, normalized valid examples, one invalid fixture per rule,
    and a schema-fixture runner are review-ready and committed; no fixture depends on parser
    implementation from Campaign B.

## Assumptions

1. "Schema-fixture runner" means a small, dependency-free Python script that loads the
   schema (via `jsonschema` if available, else a minimal structural check) and asserts each
   valid fixture passes and each invalid fixture fails for its declared reason; it is
   executable evidence, not a production parser (per the explicit DoD constraint: no
   fixture may depend on Campaign B parser implementation).
2. "One invalid fixture per rule" is interpreted as: one invalid fixture per *distinct*
   validation rule named in the acceptance criteria (required fields, closed unknown-field,
   enums, timestamp format, parent/prefix/path consistency, prerequisites shape, labels,
   work types, origins/relations, publication class, authority requirements, criteria
   shape, extension/version field, and limits) — not one per every individual field.
3. This schema formalizes the identity fields already fixed normatively in
   `issue-store.md` §4 (`id`, `parent`, `level`, `state`, `visibility`) and the AC-lifecycle
   fields fixed in §11 (`criteria[].id`, `status`, `supersedes`, `derived_from`), so those two
   documents remain the source of truth for *why*; this schema is the executable *what*.

## Intended write scope

- This claim file, `TODO.md` (0037-02.03 + closing 0037-02 markers only), `run.sh`
- `issues/_schema/issue-item-v1.schema.json`
- `issues/_schema/fixtures/issue-item-v1/` (valid examples + one invalid per rule)
- `issues/_schema/fixtures/issue-item-v1/run_fixtures.py` (schema-fixture runner)

## Progress log

- 2026-08-16 — Selected `0037-02.03`; created this claim.
- 2026-08-16 — Marked `0037-02.03` `[p]` in `TODO.md`. Drafted
  `issues/_schema/issue-item-v1.schema.json`: closed object (`additionalProperties: false`),
  required `id`/`level`/`state`/`schema_version`; enums for `state`, `visibility`,
  `work_type`, `origin.kind`, `relations[].type`, `criteria[].status`, `authority`;
  timestamps as ISO date strings; path-derived `id`/`parent` patterns; conditional
  `parent` requirement by `level` via `allOf`/`if`/`then`; structured `criteria[]` mirroring
  the `issue-store.md` §11 AC-lifecycle (status/supersedes/superseded_by/derived_from/
  moved_to); a `limits` override object; `schema_version` for extension/version
  negotiation. Explicitly documented that schema validation runs after YAML/Markdown
  validation and never substitutes for it.
- 2026-08-16 — Created 3 valid example fixtures (Feature-minimal, Task-full exercising
  every optional field, Subtask-minimal) and 14 invalid fixtures, one per distinct rule
  named in the acceptance criteria (required fields, closed unknown-field, enums,
  timestamps-as-strings, parent/prefix/path ×3, prerequisites, labels, work types,
  origins/relations, publication class/authority, criteria shape, extension-version+limits).
  Created `manifest.json` declaring the expected valid/invalid outcome and targeted rule
  per fixture, since embedding an extra explanatory key in each fixture object would
  itself trigger unintended closed-object rejection.
- 2026-08-16 — Wrote `run_fixtures.py`, a dependency-optional schema-fixture runner
  (uses `jsonschema` if installed, else a minimal structural fallback implementing only
  the constructs this schema actually uses). **Actually executed it** (not just claimed
  to work): `python3 run_fixtures.py` → `OK: 3 valid + 14 invalid fixtures behaved as
  expected`, exit 0. This is genuine executable evidence, verified before committing.
- 2026-08-16 — Discovered HEAD (`428d308b61583cbf34edd06d23a0b8a9563d38ec`, request
  `e29f6c81b4d7`). Minted commit request `f83a2d6c9e14`; the published script re-ran
  `run_fixtures.py` as a pre-commit gate inside the runner environment itself (not just my
  earlier interactive check), so the executable-evidence claim was verified in the same
  environment that persisted the commit.
- 2026-08-16 — **Task closed.** Substantive commit `70bfe4aee2bf4d0a33711c1d42b743a62c4f1ace`
  (schema + 17 fixture/manifest/runner files); bookkeeping commit
  `6bf4a8f25eb024897e7c1736995be5543fb7f00e` (`TODO.md` only, `REF:` recorded).
  Independently re-verified via fresh grep that `TODO.md` line 118 now reads `[x]
  **0037-02.03** ... REF: 70bfe4aee2bf4d0a33711c1d42b743a62c4f1ace`. Evidence retained under
  `logs/backlog-bookkeeping-and-commit/0037-02.03-f83a2d6c9e14/`, including the pre-commit
  fixture-runner output. Definition of Done satisfied: schema, 3 normalized valid examples,
  14 invalid fixtures (one per named rule), and a schema-fixture runner are committed and
  review-ready; no fixture depends on Campaign B parser implementation.
- 2026-08-16 — **Note on parent Task `0037-02`:** Confirmed via search that `0037-02`'s own
  Definition of Done ("artifacts listed with SHA-256 digests in the architecture review
  package") refers to a separate assembly artifact owned by Task `0037-37`
  ("Assemble and semantically audit the complete pre-implementation architecture
  baseline"), not something this Subtask assembles itself. `0037-02` therefore correctly
  remains `[ ]` (open) even though all three of its Subtasks are now `[x]`; it will close
  when `0037-37` runs. Singleton runner slot confirmed absent after this run.
