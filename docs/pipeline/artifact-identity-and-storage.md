# Artifact Identity, Manifests, Storage, and Indexing Contract

## Overview

This document specifies the artifact identity, canonical hashing, storage layout, and index reconstruction rules for `provenance@v1`.

## 1. Artifact Identity and Digest Rules

- **Canonical JSON Hashing:** Artifact set manifests and metadata objects compute SHA-256 digests over sorted, whitespace-normalized canonical UTF-8 JSON (`set_digest = sha256:<hex>`).
- **File Members:** Every member file within an artifact set requires:
  - `path`: Repository-relative path.
  - `digest`: `sha256:<64-hex-chars>` of the raw file content bytes.
  - `size_bytes`: Integer size in bytes (minimum 0).
  - `media_type`: MIME/media type string (e.g., `application/json`, `text/markdown`).
  - `source_commit`: 40-character Git commit hash providing byte provenance.
- **Tree Ordering Independence:** The manifest `members` list is canonically sorted by `path` ascending. The `set_digest` is deterministic regardless of member authoring sequence.

## 2. Storage Layout and Pinning

One-file stores with atomic creation semantics are pinned to:
- `provenance/events/YYYY/MM/<uuidv7>.json` — Immutable provenance events.
- `provenance/artifact-sets/<uuidv7>.json` — Immutable artifact set manifests.
- `provenance/runs/<uuidv7>.json` — Execution run records.
- `provenance/findings/YYYY/MM/<uuidv7>.json` — Static/dynamic verification findings.

## 3. Views and Indexing

- All indexing files located under `provenance/_views/` (e.g. relation graphs, reverse lookup catalogs) are **disposable derived artifacts**.
- Index files never serve as relation or state authority.
- The entire `provenance/_views/` directory can be deterministically reconstructed from the immutable one-file stores at any time.

## 4. Privacy and Redaction

- Restricted members require explicit `redacted: true/false`.
- Public projections must exclude restricted member manifests and confidential byte digests.
