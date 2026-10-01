#!/usr/bin/env python3
"""Merge per-document trace JSON outputs (produced by parallel workers) and
write the combined traceability records once, sequentially, to avoid
concurrent writers racing on the same output directory."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spec_scrape as s

parts_dir = Path(sys.argv[1])
campaign = sys.argv[2] if len(sys.argv) > 2 else "traceability-import"

merged = {}
for part in sorted(parts_dir.glob("*.json")):
    data = json.loads(part.read_text(encoding="utf-8"))
    merged.update(data.get("traceability", {}))

write_report = s.write_traceability_records(merged, campaign)

total = sum(len(v) for v in merged.values())
print("documents with traceability rows:", len(merged))
print("total RS rows:", total)
print("written:", len(write_report["written"]), "updated:", len(write_report["updated"]),
      "total canonical RS records:", write_report["total"])
