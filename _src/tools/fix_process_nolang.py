#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os

process_json_path = "_src/sources/pages/process.json"
with open(process_json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# In process.json, any block that links to repo root files (logs/, TODO-*.md) should have "nolang": true
# so that the language translation tree does not render broken relative links like ar/logs/...
for block in data.get("main", []):
    h = block.get("html", "")
    if "TODO-perplexity-" in h or "logs/backlog-bookkeeping" in h or "Ausführungs-Archive" in h or "Verifikations- &amp; Ausführungs-Archive" in h:
        block["nolang"] = True

with open(process_json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=1, ensure_ascii=False)
print("Updated process.json blocks with nolang: true where appropriate.")
