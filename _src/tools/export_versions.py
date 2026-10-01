#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_versions.py — Statically export specification version records & catalog
for GitHub Pages and static client-side diffing in versions.html.

Produces:
  - versions/catalog.json (lightweight metadata index for search & list)
  - versions/data/{id}.json (on-demand version histories & lifecycle data)
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
ROOT = SRC.parent
TOOLS = SRC / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import version_store as vs


def export_all_versions(dest_dir: Path | None = None, tracked_only: bool = True):
    t0 = time.time()
    dest = dest_dir or (ROOT / "versions")
    data_dir = dest / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    if tracked_only:
        try:
            raw = subprocess.check_output(
                ["git", "ls-files", str(SRC / "spec" / "versions")],
                cwd=ROOT,
                text=True,
                timeout=30,
            )
            version_files = [ROOT / line for line in raw.splitlines() if line.endswith(".jsonl")]
        except Exception:
            version_files = sorted((SRC / "spec" / "versions").rglob("*.jsonl"))
    else:
        version_files = sorted((SRC / "spec" / "versions").rglob("*.jsonl"))

    print(f"Exporting {len(version_files)} version records into {dest} ...")

    std_rels_map = {
        "AP": ("R17-03", "R17-10", "R18-03", "R18-10", "R19-03", "R19-11", "R20-11", "R25-11"),
        "CP": ("R18-10", "R19-11", "R20-11", "R21-11", "R22-11", "R25-11"),
    }

    catalog_items = []
    exported_count = 0

    for path in version_files:
        if not path.is_file():
            continue
        try:
            lines = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        except Exception:
            continue
        if not lines:
            continue

        cid = lines[0].get("canonical_id", "")
        req_id = path.stem
        platform = "CP" if "AUTOSAR/CP" in cid else "AP"
        std_rels = std_rels_map.get(platform, ())
        recorded_rels = set(v.get("release") for v in lines if v.get("release"))
        last_rel = lines[-1].get("release")

        dropped_in = []
        if last_rel and std_rels:
            for r in std_rels:
                if r > last_rel and r not in recorded_rels:
                    dropped_in.append(r)

        lifecycle = {
            "canonical_id": cid,
            "is_dropped": bool(dropped_in),
            "last_active_release": last_rel,
            "dropped_in": dropped_in,
            "first_dropped_release": dropped_in[0] if dropped_in else None,
            "latest_platform_release": std_rels[-1] if std_rels else None,
        }

        rels = [l.get("release", "") for l in lines]
        catalog_items.append({
            "id": req_id,
            "canonical_id": cid,
            "platform": platform,
            "version_count": len(lines),
            "releases": rels,
            "latest_release": rels[-1] if rels else "",
            "is_dropped": lifecycle["is_dropped"],
            "first_dropped_release": lifecycle["first_dropped_release"],
            "file": f"versions/data/{req_id}.json",
        })

        record_data = {
            "ok": True,
            "canonical_id": cid,
            "versions": lines,
            "lifecycle": lifecycle,
        }

        record_file = data_dir / f"{req_id}.json"
        record_file.write_text(
            json.dumps(record_data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        exported_count += 1

    catalog_items.sort(key=lambda x: (-x["version_count"], x["id"]))
    catalog_payload = {
        "ok": True,
        "total": len(catalog_items),
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "items": catalog_items,
    }

    catalog_file = dest / "catalog.json"
    catalog_file.write_text(
        json.dumps(catalog_payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    elapsed = round(time.time() - t0, 2)
    print(f"Export completed in {elapsed}s: {exported_count} records and catalog written to {dest}")
    return exported_count


def main():
    dest = ROOT / "versions"
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        dest = Path(sys.argv[1]).resolve()
    export_all_versions(dest)


if __name__ == "__main__":
    main()
