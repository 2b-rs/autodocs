# Cross-Release ID Naming Scheme (0006-15)

Status: pinned and implemented 2026-08-13 in `_src/tools/version_id.py`.
Layered on the canonical identity from **0006-02** (`project/kind/id`,
release-free).

## Motivating scenario

A curator decides on a requirement's value; a later AUTOSAR release changes
that same requirement. The system must find every AI-generated artifact
whose evidence depended on the now-superseded decision or requirement
version, without ever deleting a prior decision, curation, evidence
snippet, synthesis, or specification version.

Versioning grain for AUTOSAR AP: requirement level.

## ID families

| Family | Format | Minted by |
|---|---|---|
| Canonical requirement identity | `project/kind/id` (0006-02) | `_src/tools/canonical_id.py` |
| Requirement version | `<canonical-id>@rel:<release>#<hash8>` | `_src/tools/version_id.py::requirement_version_id()` |
| Curation decision | `curation:<uuid7>` | `_src/tools/version_id.py::curation_id()` |
| Evidence snippet | `evidence:<uuid7>` | `_src/tools/version_id.py::evidence_id()` |
| AI artifact/synthesis | `artifact:<uuid7>` | `_src/tools/version_id.py::artifact_id()` |
| Supersession edge | `supersedes:<old-version-id>-><new-version-id>` | `_src/tools/version_id.py::supersession_edge()` |

## Pinned design decisions

- **Content hash**: SHA-256 truncated to the first 8 hex characters
  (`content_hash8()`). 32 bits of entropy is sufficient collision
  resistance at per-requirement-per-release scale while staying short
  and human-readable.
- **UUIDv7**: this project's Python has no `uuid.uuid7()` in stdlib
  (verified 2026-08-13), so `version_id.py::uuid7()` implements RFC 9562
  directly: 48-bit millisecond Unix timestamp + version/variant bits +
  74 random bits, giving time-sortable IDs across concurrent queue/
  browser/AI write paths (per **0006-06**) without a central allocator.

## Non-goals of this task

This task only mints and parses IDs. It does **not** yet:
- wire minting calls into `review_flags.py`/`curation_flags.py` write paths
  (that is **0006-16**/**0006-17** scope: an immutable version store and
  pinning decisions/evidence to specific versions),
- implement the evidence/dependency graph (**0006-18**, blocked on a
  manager decision), or
- implement confidence history (**0006-19**, blocked on a manager decision).
