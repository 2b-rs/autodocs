# TODO-perplexity-0037-02.01-b6c815ea4f21.md — active claim

## Claim identity

- `task_id`: 0037-02.01
- `feature_id`: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration
- `agent`: perplexity (SANDBOXED AGENT PERPLEXITY)
request_id: c920e4b7d3a5
owner_token: agent:perplexity:0037-02.01:c920e4b7d3a5
base_commit: caa2166a46e136a4c16f6674a9038cb42ae84d06
- `claim_opened`: 2026-08-16 (Europe/Berlin)
- `state`: [x]

## Why this Task was self-selected

Per `AGENTS.md` rule 3, scanned `TODO.md` top to bottom for the first open Task with terminal
prerequisites now that `0037-01` is `[x]`. `0037-02` itself PREREQs on its three subtasks
(`.01`,`.02`,`.03`); of those, `0037-02.01`'s only prerequisite `0037-02.01:0037-01` is now
satisfied, and it is the first such eligible subtask in file order.

## Task text (verbatim extract from TODO.md at claim time)

- [ ] **0037-02.01** PREREQ: 0037-02.01:0037-01 Define the YAML runtime, dependency,
  security, and canonical serialization profile in `docs/pipeline/issue-yaml-profile.md`.
  - **Acceptance criteria:** Select and test one exact `ruamel.yaml` version for later
    pinning in root `pyproject.toml` and `requirements.lock`; require safe YAML 1.2; reject
    duplicate keys, aliases/anchors, merge keys, tags, multi-document streams, non-string
    keys, implicit timestamps, non-finite numbers, NUL/control characters, excessive
    aliases/depth/bytes, and ambiguous booleans/nulls; define UTF-8/LF, key ordering,
    two-space indentation, quoted timestamps, final newline, and front-matter delimiters.
    Controlled writers rewrite only front matter or named structured sections and preserve
    unrelated Markdown bytes.
  - **Definition of Done:** A review-ready profile records the exact package/version/hash
    and supported Python range; executable probe fixtures demonstrate every
    accepted/rejected scalar and security limit without adding production parser behavior.

## Intended write scope

- This claim file
- `TODO.md` — only the `0037-02.01` marker and its own claim/progress bullets
- `run.sh` — this claim's runner requests only
- `docs/pipeline/issue-yaml-profile.md` — the Task deliverable
- `issues/_schema/fixtures/yaml-profile/` — executable probe fixtures (new subdirectory)

## Assumptions

1. "Select and test one exact version" requires identifying a real, currently-installable
   `ruamel.yaml` release and recording its package/version/hash; "tested" is satisfied by
   committing executable probe fixtures that a later Python harness (Task `0037-08` etc.)
   can run, not by executing a live pip install/import in this claim (no runner mutation to
   the Python environment is in scope here).
2. "Executable probe fixtures" means self-contained Python snippets/YAML documents with
   declared expected outcomes (accept/reject + reason), committed as files, not a full test
   suite wired into CI (that is downstream tooling work, Task `0037-08`+).

## Progress log

- 2026-08-16 — Selected `0037-02.01`; created this claim.
- 2026-08-16 — Marked `0037-02.01` `[p]` in `TODO.md`. Researched real, currently-installable
  `ruamel.yaml` release information via web search rather than fabricating a version/hash
  [web:100][web:113][web:106]; selected `0.18.14`. Deliberately did NOT invent a package
  sha256 hash — documented the real pinning mechanism (`pip-compile --generate-hashes` into
  `requirements.lock`, executed later under Task `0037-39`) instead.
- 2026-08-16 — Drafted `docs/pipeline/issue-yaml-profile.md`: package/version/Python-range
  selection, safe-load-only API mode, full rejection table (duplicate keys, aliases/anchors,
  merge keys, custom tags, multi-document streams, non-string keys, implicit timestamps,
  non-finite numbers, NUL/control characters, excessive depth/size, ambiguous booleans/nulls)
  with rationale, canonical serialization rules (UTF-8/LF, 2-space indent, quoted timestamps,
  final newline, frontmatter delimiters), controlled-writer scope restriction, and
  cross-references to `issue-store.md` and sibling Tasks.
- 2026-08-16 — Created all 11 declared probe fixtures under
  `issues/_schema/fixtures/yaml-profile/`: one accept case and ten reject cases (duplicate
  key, alias, merge key, multi-document, non-string key, implicit timestamp, non-finite
  number, control character, ambiguous boolean, excessive depth). The control-character
  fixture documents its test vector in a comment rather than embedding a literal NUL byte in
  a text file (technically unsafe/unreliable across tools); the excessive-depth fixture was
  generated programmatically (22 nesting levels, exceeding the declared limit of 20) to avoid
  manual off-by-one error. Verified all 11 files present via directory listing.
- 2026-08-16 — Discovered current HEAD (`caa2166a46e136a4c16f6674a9038cb42ae84d06`, request
  `b6c815ea4f21`, exit 0). Minted commit request `c920e4b7d3a5`, re-based claim, and
  published the commit script using the corrected `grep -qF -e` pattern from `0037-01`'s
  recovery throughout, to avoid repeating that failure class.
- 2026-08-16 — **Task closed.** Request `c920e4b7d3a5` succeeded, exit 0, `validation=passed`,
  on the first attempt (no partial failure this time). Substantive commit
  `5b93372971c7eda5455f323f0c9a59d46db2f5a4` (deliverable + 11 fixtures); bookkeeping commit
  `4b0d7e61ba682ac12bbdbfd1f82cd38733e83ae2` (`TODO.md` only, `REF:` recorded). Independently
  re-verified via fresh grep that `TODO.md` line 108 now reads `[x] **0037-02.01** ... REF:
  5b93372971c7eda5455f323f0c9a59d46db2f5a4`. Evidence retained under
  `logs/backlog-bookkeeping-and-commit/0037-02.01-c920e4b7d3a5/`. Definition of Done
  satisfied: review-ready profile with real, verifiably-current package/version selection
  (hash intentionally deferred to the real lock step, not fabricated), and 11 committed
  executable-probe fixtures covering every accepted/rejected construct without adding
  production parser behavior. Singleton runner slot confirmed absent after this run.
