#!/usr/bin/env python3
"""Locale-neutral public privacy projector (Task 0037-23.01).

Writes `_src/data/issue-graph-public.json`. Fail-closed allowlist: only
`visibility: public-summary` items and approved fields. No translated titles.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path("_src/tools/privacy_projector.py")
OUTPUT_PATH = Path("_src/data/issue-graph-public.json")
ALLOWED_ITEM_KEYS = (
    "id",
    "level",
    "title_key",
    "title_source_hash",
    "state_coarse",
    "public_prerequisites",
    "public_summary_key",
    "link",
)
ALLOWED_ROOT_KEYS = (
    "schema",
    "authority",
    "policy_digest",
    "generation_id",
    "digests",
    "restricted_item_count",
    "items",
    "edges",
)
COARSE_STATE = {
    "open": "open",
    "in_progress": "in_progress",
    "blocked": "blocked",
    "closed": "closed",
    "withdrawn": "withdrawn",
}
LEAK_TOKENS = (
    "claim.json",
    "SECRETLEAK",
    "/private/",
    "owner_token",
    "decision_ref",
    "finding_id",
    "TODO-",
)
POLICY = {
    "schema": "privacy-projector-policy@v1",
    "allowed_item_keys": list(ALLOWED_ITEM_KEYS),
    "visibility_required": "public-summary",
    "exclude": [
        "claims", "identities", "private_paths", "findings", "decisions",
        "evidence", "security_labels", "unreleased", "incident_edges_to_omitted",
        "translated_title",
    ],
}


class PrivacyProjectorError(ValueError):
    pass


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def _digest_bytes(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _title_key(item_id):
    return f"issues.{item_id}.title"


def _summary_key(item_id):
    return f"issues.{item_id}.summary"


def _coarse_state(item):
    state = item.get("state")
    if state not in COARSE_STATE:
        raise PrivacyProjectorError(f"missing privacy decision/state for {item.get('id')}")
    labels = item.get("labels") or []
    if "security" in labels or "unreleased" in labels:
        return None
    return COARSE_STATE[state]


def _scan_leaks(blob):
    lowered = blob.lower()
    for token in LEAK_TOKENS:
        if token.lower() in lowered:
            raise PrivacyProjectorError(f"leaked restricted fixture token {token!r}")


def project(catalog, graph=None):
    if not isinstance(catalog, dict) or "items" not in catalog:
        raise PrivacyProjectorError("catalog missing items")
    items = catalog.get("items")
    if not isinstance(items, list):
        raise PrivacyProjectorError("catalog items must be a list")
    public_ids = []
    restricted = 0
    projected = []
    by_id = {}
    for item in items:
        if not isinstance(item, dict):
            raise PrivacyProjectorError("catalog item must be an object")
        vis = item.get("visibility")
        item_id = item.get("id")
        if vis is None or vis == "internal" or vis != "public-summary":
            if vis not in {None, "internal", "public-summary"}:
                raise PrivacyProjectorError(f"unknown visibility class {vis!r}")
            restricted += 1
            continue
        if not item_id or not item.get("level"):
            raise PrivacyProjectorError("public item missing id/level")
        if item.get("endpoint_status") == "malformed":
            raise PrivacyProjectorError(f"malformed public item {item_id}")
        coarse = _coarse_state(item)
        if coarse is None:
            restricted += 1
            continue
        hash_val = item.get("title_source_hash")
        if not hash_val or not str(hash_val).startswith("sha256:"):
            raise PrivacyProjectorError(f"missing title_source_hash for {item_id}")
        rec = {
            "id": item_id,
            "level": item["level"],
            "title_key": _title_key(item_id),
            "title_source_hash": hash_val,
            "state_coarse": coarse,
            "public_prerequisites": list(item.get("prerequisites") or []),
            "public_summary_key": _summary_key(item_id),
            "link": item.get("url") or f"/issues/{item_id}/",
        }
        if set(rec) != set(ALLOWED_ITEM_KEYS):
            raise PrivacyProjectorError("allowlist drift")
        if "title" in rec:
            raise PrivacyProjectorError("translated/source title must not appear")
        public_ids.append(item_id)
        by_id[item_id] = rec
        projected.append(rec)
    public_set = set(public_ids)
    for rec in projected:
        kept = []
        for dep in rec["public_prerequisites"]:
            if dep in public_set:
                kept.append(dep)
            elif dep in {item.get("id") for item in items}:
                continue
            else:
                raise PrivacyProjectorError(f"dangling public edge {rec['id']}->{dep}")
        rec["public_prerequisites"] = sorted(kept)
    projected.sort(key=lambda entry: entry["id"])
    edges = []
    if graph:
        for edge in graph.get("edges") or []:
            src, dst = edge.get("source"), edge.get("target")
            if src in public_set and dst in public_set:
                edges.append({
                    "source": src,
                    "target": dst,
                    "kind": edge.get("kind") or "prerequisite",
                })
            # incident edges to omitted nodes are dropped, not emitted
        edges.sort(key=lambda edge: (edge["source"], edge["kind"], edge["target"]))
    policy_digest = _digest_bytes(_canonical_json(POLICY).encode("utf-8"))
    catalog_digest = _digest_bytes(_canonical_json(catalog).encode("utf-8"))
    tool_digest = _digest_bytes((ROOT / TOOL_PATH).read_bytes()) if (ROOT / TOOL_PATH).is_file() else _digest_bytes(b"")
    generation_id = _digest_bytes(_canonical_json({
        "catalog": catalog_digest,
        "policy": policy_digest,
        "tool": tool_digest,
    }).encode("utf-8"))
    document = {
        "schema": "issue-graph-public@v1",
        "authority": "generated-view",
        "policy_digest": policy_digest,
        "generation_id": generation_id,
        "digests": {
            "catalog_sha256": catalog_digest,
            "policy_sha256": policy_digest,
            "tool_sha256": tool_digest,
        },
        "restricted_item_count": restricted,
        "items": projected,
        "edges": edges,
    }
    extra_root = set(document) - set(ALLOWED_ROOT_KEYS)
    if extra_root:
        raise PrivacyProjectorError(f"unknown root fields {sorted(extra_root)}")
    encoded = _canonical_json(document)
    _scan_leaks(encoded)
    roundtrip = json.loads(encoded)
    if _canonical_json(roundtrip) != encoded:
        raise PrivacyProjectorError("projection is not deterministic")
    return document, encoded


def write_public(document_bytes, repository_root):
    dest = Path(repository_root) / OUTPUT_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".json.tmp")
    tmp.write_text(document_bytes, encoding="utf-8")
    tmp.replace(dest)
    return dest


def reverse_check(document, catalog):
    extra_root = set(document) - set(ALLOWED_ROOT_KEYS)
    if extra_root:
        raise PrivacyProjectorError(f"unknown root fields {sorted(extra_root)}")
    for item in document.get("items") or []:
        extra = set(item) - set(ALLOWED_ITEM_KEYS)
        if extra:
            raise PrivacyProjectorError(f"unknown projected fields {sorted(extra)}")
    public_ids = {item["id"] for item in document["items"]}
    for item in catalog.get("items") or []:
        vis = item.get("visibility")
        if vis == "public-summary" and item.get("id") not in public_ids:
            labels = item.get("labels") or []
            if "security" in labels or "unreleased" in labels:
                continue
            raise PrivacyProjectorError(f"public-summary item omitted: {item.get('id')}")
        if vis != "public-summary" and item.get("id") in public_ids:
            raise PrivacyProjectorError(f"restricted id leaked: {item.get('id')}")
    blob = _canonical_json(document)
    for item in catalog.get("items") or []:
        if item.get("visibility") != "public-summary":
            if item.get("id") and item["id"] in blob:
                raise PrivacyProjectorError(f"restricted id leaked in bytes: {item['id']}")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", default=str(ROOT))
    parser.add_argument("--catalog-json")
    parser.add_argument("--graph-json")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    repository_root = Path(args.repository_root).resolve()
    try:
        if args.catalog_json:
            catalog = json.loads(Path(args.catalog_json).read_text(encoding="utf-8"))
        else:
            raise PrivacyProjectorError("--catalog-json is required")
        graph = None
        if args.graph_json:
            graph = json.loads(Path(args.graph_json).read_text(encoding="utf-8"))
        document, encoded = project(catalog, graph)
        reverse_check(document, catalog)
        if args.write:
            write_public(encoded, repository_root)
        else:
            sys.stdout.write(encoded)
        return 0
    except (PrivacyProjectorError, OSError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
