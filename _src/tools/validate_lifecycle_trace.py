#!/usr/bin/env python3
"""Lifecycle trace validator over explicit candidate roots only (0022-02.02).

Enforces node and edge contract constraints without repository-wide side-effects.
"""

import sys
import json
import argparse
from pathlib import Path

VALID_NODE_TYPES = {
    "requirement", "architecture-element", "detailed-design-unit",
    "source-code-unit", "configuration-item", "measure", "result"
}

VALID_EDGE_TYPES = {
    "satisfies", "implements", "verifies-unit", "verifies-integration",
    "qualifies-software", "validates-operational"
}

def validate_trace_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        return {"ok": False, "errors": [f"File not found: {manifest_path}"]}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"ok": False, "errors": [f"Malformed JSON: {e}"]}

    errors = []
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    node_ids = set()
    for n in nodes:
        nid = n.get("id")
        ntype = n.get("type")
        if not nid:
            errors.append("Node missing 'id'")
            continue
        if nid in node_ids:
            errors.append(f"Duplicate node id: {nid}")
        node_ids.add(nid)
        if ntype not in VALID_NODE_TYPES:
            errors.append(f"Invalid node type '{ntype}' for node {nid}")

    for e in edges:
        etype = e.get("type")
        src = e.get("source")
        tgt = e.get("target")
        if etype not in VALID_EDGE_TYPES:
            errors.append(f"Invalid edge type '{etype}'")
        if src not in node_ids:
            errors.append(f"Edge source not found in nodes: {src}")
        if tgt not in node_ids:
            errors.append(f"Edge target not found in nodes: {tgt}")

    return {"ok": len(errors) == 0, "errors": errors, "node_count": len(nodes), "edge_count": len(edges)}

def main():
    parser = argparse.ArgumentParser(description="Validate lifecycle trace manifest")
    parser.add_argument("manifest", type=Path, help="Path to lifecycle trace JSON manifest")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    args = parser.parse_args()

    result = validate_trace_manifest(args.manifest)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["ok"]:
            print(f"PASS: Valid trace manifest ({result['node_count']} nodes, {result['edge_count']} edges)")
        else:
            print("FAIL: Validation errors encountered:")
            for err in result["errors"]:
                print(f" - {err}")
    sys.exit(0 if result["ok"] else 1)

if __name__ == "__main__":
    main()
