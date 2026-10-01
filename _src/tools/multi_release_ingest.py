"""Multi-Release Requirement Ingestion Engine for Autodocs.

Extracts specification requirements from AUTOSAR standard PDFs across multiple
releases in _src/spec/pdf-cache/, tracks revisions, and ingests them into the
immutable version store (_src/spec/versions/) using up to 10 parallel CPU workers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

_TOOLS_DIR = Path(__file__).resolve().parent
_SRC_DIR = _TOOLS_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import canonical_id as cid_mod
import spec_scrape
import version_store as vs
from version_id import requirement_version_id, content_hash8

_LOGGER = logging.getLogger("autodocs.multi_release_ingest")

# Canonical AUTOSAR requirement ceiling and floor delimiters
REQ_PATTERN = re.compile(
    r"\[([A-Za-z0-9_]+)\]([^\n⌈]*\n(?:[^\n⌈]*\n)*?)\s*⌈([^⌋]+)⌋",
    re.DOTALL
)

KNOWN_RELEASES = [
    "R17-03_R1.1.0",
    "R17-10_R1.2.0",
    "R18-03_R1.4.0",
    "R18-10_R4.4.0_R1.5.0",
    "R19-03",
    "R19-11",
    "R20-11",
    "R21-11",
    "R22-11",
    "R23-11",
    "R24-11",
    "R25-11",
]


def normalize_release_tag(folder_name: str) -> str:
    """Normalize folder names like R18-10_R4.4.0_R1.5.0 to release tags like R18-10."""
    m = re.match(r"^(R\d{2}-\d{2})", folder_name)
    if m:
        return m.group(1)
    if folder_name.startswith("R4."):
        return folder_name
    return folder_name


def parse_pdf_requirements(pdf_path_str: str, release_tag: str) -> List[Dict[str, Any]]:
    """Extract all delimited requirements from one PDF."""
    pdf_path = Path(pdf_path_str)
    if not pdf_path.is_file():
        return []

    try:
        pages = spec_scrape.pdf_pages(pdf_path, backend="builtin")
    except Exception as exc:
        _LOGGER.debug("Failed to extract pages from %s: %s", pdf_path, exc)
        return []

    all_text = "\n".join(pages)
    matches = REQ_PATTERN.findall(all_text)
    items = []

    # Determine platform from path or file name
    is_classic = "CLASSIC" in str(pdf_path) or "AUTOSAR_CP_" in pdf_path.name or "AUTOSAR_SWS_" in pdf_path.name and "AUTOSAR_AP_" not in pdf_path.name
    platform_kind = "CP" if is_classic else "AP"

    seen_ids: Set[str] = set()
    for req_id, header, body in matches:
        req_id = req_id.strip()
        if not (req_id.startswith("SWS_") or req_id.startswith("RS_") or req_id.startswith("PRS_")):
            continue
        if req_id in seen_ids:
            continue
        seen_ids.add(req_id)

        clean_body = " ".join(body.split()).strip()
        clean_header = " ".join(header.split()).strip()
        full_content = (clean_header + " " + clean_body).strip() if clean_header else clean_body

        canonical_id = f"AUTOSAR/{platform_kind}/record/{req_id}"
        items.append({
            "canonical_id": canonical_id,
            "req_id": req_id,
            "release": release_tag,
            "content": full_content,
            "source_pdf": pdf_path.name,
        })

    return items


def _worker_process_pdf(args: Tuple[str, str]) -> List[Dict[str, Any]]:
    pdf_path_str, release_tag = args
    return parse_pdf_requirements(pdf_path_str, release_tag)


def ingest_releases(
    pdf_paths_with_releases: List[Tuple[Path, str]],
    max_workers: int = 10,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Ingest requirements from PDFs across releases in parallel using max_workers."""
    t0 = time.monotonic()
    tasks = [(str(p), rel) for p, rel in pdf_paths_with_releases]
    print(f"Ingesting from {len(tasks)} PDFs using {max_workers} CPU workers...")

    all_items: List[Dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for res in executor.map(_worker_process_pdf, tasks, chunksize=1):
            all_items.extend(res)

    print(f"Extracted {len(all_items)} requirement snapshots across PDFs.")

    # Sort items chronologically by release
    def rel_sort_key(item: dict) -> str:
        return item["release"]

    all_items.sort(key=rel_sort_key)

    # Ingest into version_store
    recorded_count = 0
    duplicate_count = 0
    error_count = 0

    # Group by canonical_id to measure version revisions
    revisions_per_id: Dict[str, List[str]] = defaultdict(list)

    if not dry_run:
        for it in all_items:
            cid = it["canonical_id"]
            rel = it["release"]
            content = it["content"]
            try:
                vid = vs.record_version(
                    cid,
                    rel,
                    content,
                    meta={"trigger_kind": "multi_release_ingest", "source_pdf": it["source_pdf"]},
                )
                revisions_per_id[cid].append(vid)
                recorded_count += 1
            except Exception as exc:
                _LOGGER.debug("Error recording %s: %s", cid, exc)
                error_count += 1

    dur = time.monotonic() - t0
    multi_ver_count = sum(1 for vids in revisions_per_id.values() if len(set(vids)) > 1)

    return {
        "ok": True,
        "pdfs_processed": len(tasks),
        "snapshots_extracted": len(all_items),
        "recorded_count": recorded_count,
        "unique_requirements": len(revisions_per_id),
        "multi_version_requirements": multi_ver_count,
        "errors": error_count,
        "duration_seconds": round(dur, 2),
        "workers": max_workers,
    }


def find_target_pdfs(
    pdf_cache_root: Path,
    releases: Optional[List[str]] = None,
    modules: Optional[List[str]] = None,
    docs: Optional[List[str]] = None,
) -> List[Tuple[Path, str]]:
    """Discover PDF paths matching releases and filter criteria."""
    targets = []
    selected_releases = set(releases) if releases else None

    for rel_dir in sorted(pdf_cache_root.iterdir()):
        if not rel_dir.is_dir() or rel_dir.name.startswith("."):
            continue

        rel_tag = normalize_release_tag(rel_dir.name)
        if selected_releases and rel_tag not in selected_releases and rel_dir.name not in selected_releases:
            continue

        for pdf_path in rel_dir.glob("**/*.pdf"):
            name = pdf_path.name
            if modules:
                # Check if matches any requested module
                matched_mod = False
                for m in modules:
                    m_lower = m.lower()
                    if f"_{m_lower}" in name.lower() or f"_{m.upper()}" in name:
                        matched_mod = True
                        break
                if not matched_mod:
                    continue

            if docs:
                matched_doc = any(d in name for d in docs)
                if not matched_doc:
                    continue

            targets.append((pdf_path, rel_tag))

    return targets


def main():
    parser = argparse.ArgumentParser(description="Multi-release requirement ingestion engine.")
    parser.add_argument("--releases", "-r", help="Comma-separated release tags (e.g. R18-10,R19-11,R20-11,R21-11,R22-11,R25-11)")
    parser.add_argument("--modules", "-m", help="Comma-separated module identifiers (e.g. com,core,log,os)")
    parser.add_argument("--docs", "-d", help="Comma-separated document name substrings (e.g. COM,Core,LogAndTrace)")
    parser.add_argument("--workers", "-w", type=int, default=10, help="Max parallel CPU workers (default: 10)")
    parser.add_argument("--dry-run", action="store_true", help="Extract without saving to version store")
    parser.add_argument("--json", action="store_true", help="Output summary in JSON format")
    args = parser.parse_args()

    cache_dir = _SRC_DIR / "spec" / "pdf-cache"
    rels = [x.strip() for x in args.releases.split(",")] if args.releases else None
    mods = [x.strip() for x in args.modules.split(",")] if args.modules else None
    docs = [x.strip() for x in args.docs.split(",")] if args.docs else None

    pdf_targets = find_target_pdfs(cache_dir, releases=rels, modules=mods, docs=docs)
    print(f"Found {len(pdf_targets)} matching PDFs in cache.")

    workers = min(args.workers, os.cpu_count() or 10)
    summary = ingest_releases(pdf_targets, max_workers=workers, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"\nIngest completed in {summary['duration_seconds']}s using {summary['workers']} CPUs:")
        print(f"  PDFs processed:             {summary['pdfs_processed']}")
        print(f"  Snapshots extracted:        {summary['snapshots_extracted']}")
        print(f"  Snapshots recorded:         {summary['recorded_count']}")
        print(f"  Unique requirements:        {summary['unique_requirements']}")
        print(f"  Multi-version requirements: {summary['multi_version_requirements']}")
        print(f"  Errors:                     {summary['errors']}")


if __name__ == "__main__":
    main()
