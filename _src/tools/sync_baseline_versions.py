"""Baseline version synchronization for autodocs spec database.

Scans all current spec records in _src/spec/records/ and records their canonical
baseline versions into the immutable version store (_src/spec/versions/), using
up to 10 CPU workers in parallel.
"""
from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_TOOLS_DIR = Path(__file__).resolve().parent
_SRC_DIR = _TOOLS_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import canonical_id as cid_mod
import version_store as vs
from version_id import requirement_version_id, content_hash8

_LOGGER = logging.getLogger("autodocs.sync_baseline")


def _extract_blocks_text(blocks: Any) -> List[str]:
    texts = []
    if isinstance(blocks, str):
        t = re.sub(r"<[^>]+>", " ", blocks)
        t = " ".join(t.split())
        if t:
            texts.append(t)
    elif isinstance(blocks, list):
        for item in blocks:
            texts.extend(_extract_blocks_text(item))
    elif isinstance(blocks, dict):
        for k, v in blocks.items():
            if k not in ("attrs", "status", "history", "upstream", "namespace_meta", "t", "src"):
                texts.extend(_extract_blocks_text(v))
    return texts


def _process_adaptive_file(file_path_str: str) -> List[Tuple[str, str, str]]:
    """Process an individual Adaptive record file. Returns list of (canonical_id, release, content)."""
    p = Path(file_path_str)
    try:
        with open(p, "r", encoding="utf-8") as f:
            rec = json.load(f)
    except Exception:
        return []

    rec_id = rec.get("id") or p.stem
    canonical_id = f"AUTOSAR/AP/record/{rec_id}"

    # Extract content text
    content_text = rec.get("content_text") or rec.get("text") or rec.get("value") or ""
    if not content_text and rec.get("blocks"):
        content_text = " ".join(_extract_blocks_text(rec["blocks"])).strip()

    if not content_text:
        content_text = f"AUTOSAR Adaptive specification requirement {rec_id}"

    release = rec.get("release") or "R25-11"
    return [(canonical_id, release, content_text)]


def _process_classic_file(file_path_str: str) -> List[Tuple[str, str, str]]:
    """Process a Classic multi-requirement file (e.g. CP_COM.json)."""
    p = Path(file_path_str)
    try:
        with open(p, "r", encoding="utf-8") as f:
            rec = json.load(f)
    except Exception:
        return []

    results = []
    blocks = rec.get("blocks") or []
    current_sws = None
    current_text = []

    for block in blocks:
        html = block.get("html", "") if isinstance(block, dict) else ""
        m_sws = re.search(r"\[(SWS_CP_[A-Za-z0-9_]+|SWS_[A-Za-z0-9_]+)\]", html)
        if m_sws:
            if current_sws and current_text:
                cid = f"AUTOSAR/CP/record/{current_sws}"
                results.append((cid, "R20-11", " ".join(current_text).strip()))
            current_sws = m_sws.group(1)
            current_text = [re.sub(r"<[^>]+>", " ", html)]
        elif current_sws:
            txt = " ".join(_extract_blocks_text(block)).strip()
            if txt:
                current_text.append(txt)

    if current_sws and current_text:
        cid = f"AUTOSAR/CP/record/{current_sws}"
        results.append((cid, "R20-11", " ".join(current_text).strip()))

    # Also record the module container itself
    mod_id = rec.get("id") or p.stem
    cid_mod_rec = f"AUTOSAR/CP/record/{mod_id}"
    mod_text = " ".join(_extract_blocks_text(blocks)).strip() or f"AUTOSAR Classic module {mod_id}"
    results.append((cid_mod_rec, "R20-11", mod_text))

    return results


def _record_batch(items: List[Tuple[str, str, str]]) -> Tuple[int, int]:
    """Worker task: records a batch of items into version_store."""
    recorded = 0
    errors = 0
    for cid, release, content in items:
        try:
            vs.record_version(cid, release, content, meta={"trigger_kind": "baseline_sync"})
            recorded += 1
        except Exception as exc:
            errors += 1
    return recorded, errors


def sync_all_baseline(max_workers: int = 10, limit: Optional[int] = None) -> Dict[str, Any]:
    """Scan all records and sync baseline versions in parallel using max_workers CPUs."""
    t0 = time.monotonic()
    records_dir = _SRC_DIR / "spec" / "records"
    
    # Collect files
    adaptive_files = []
    classic_files = []

    for path in records_dir.glob("**/*.json"):
        if "classic" in path.parts:
            classic_files.append(str(path))
        elif "score" not in path.parts:
            adaptive_files.append(str(path))

    if limit:
        adaptive_files = adaptive_files[:limit]
        classic_files = classic_files[:limit]

    total_files = len(adaptive_files) + len(classic_files)
    print(f"Scanning {total_files} record files ({len(adaptive_files)} Adaptive, {len(classic_files)} Classic)...")

    # Extract in parallel
    items_to_record = []
    
    # Process adaptive
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for res in executor.map(_process_adaptive_file, adaptive_files, chunksize=50):
            items_to_record.extend(res)

    # Process classic
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for res in executor.map(_process_classic_file, classic_files):
            items_to_record.extend(res)

    print(f"Extracted {len(items_to_record)} requirement baselines. Ingesting into version store with {max_workers} CPUs...")

    # Partition into chunks for parallel recording
    chunk_size = max(20, len(items_to_record) // (max_workers * 4) + 1)
    chunks = [items_to_record[i:i + chunk_size] for i in range(0, len(items_to_record), chunk_size)]

    total_recorded = 0
    total_errors = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for rec_count, err_count in executor.map(_record_batch, chunks):
            total_recorded += rec_count
            total_errors += err_count

    dur = time.monotonic() - t0
    summary = {
        "ok": True,
        "files_scanned": total_files,
        "requirements_extracted": len(items_to_record),
        "recorded_count": total_recorded,
        "error_count": total_errors,
        "duration_seconds": round(dur, 2),
        "workers": max_workers,
    }
    return summary


def main():
    parser = argparse.ArgumentParser(description="Sync baseline versions from _src/spec/records into _src/spec/versions.")
    parser.add_argument("--workers", "-w", type=int, default=10, help="Number of CPU workers (default: 10)")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Limit number of files for quick testing")
    parser.add_argument("--json", action="store_true", help="Output summary as JSON")
    args = parser.parse_args()

    workers = min(args.workers, os.cpu_count() or 10)
    res = sync_all_baseline(max_workers=workers, limit=args.limit)

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"Sync complete in {res['duration_seconds']}s using {res['workers']} CPU workers.")
        print(f"  Requirements extracted: {res['requirements_extracted']}")
        print(f"  Recorded in version store: {res['recorded_count']}")
        print(f"  Errors: {res['error_count']}")


if __name__ == "__main__":
    main()
