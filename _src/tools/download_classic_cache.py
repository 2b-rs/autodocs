#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""download_classic_cache.py — Vervollständigt den PDF-Cache für AUTOSAR Classic R20-11.

Lädt fehlende Spezifikationen von autosar.org herunter und legt sie unter
_src/spec/pdf-cache/R20-11/AUTOSAR/CLASSIC/ ab.
"""
from __future__ import annotations

import os
import ssl
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_TOOLS_DIR = Path(__file__).resolve().parent
_SRC_DIR = _TOOLS_DIR.parent
CACHE_DIR = _SRC_DIR / "spec" / "pdf-cache" / "R20-11" / "AUTOSAR" / "CLASSIC"
BASE_URL = "https://www.autosar.org/fileadmin/standards/R20-11/CP/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def create_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
    except Exception:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get_missing_candidate_list() -> List[str]:
    """Find all candidate files from R19-11 and R21-11 that are missing in R20-11."""
    r19_dir = _SRC_DIR / "spec" / "pdf-cache" / "R19-11" / "AUTOSAR" / "CLASSIC"
    r21_dir = _SRC_DIR / "spec" / "pdf-cache" / "R21-11" / "AUTOSAR" / "CLASSIC"

    candidates = set()
    if r19_dir.is_dir():
        candidates.update(f.name for f in r19_dir.glob("*.pdf"))
    if r21_dir.is_dir():
        candidates.update(f.name for f in r21_dir.glob("*.pdf"))

    existing = set(f.name for f in CACHE_DIR.glob("*.pdf"))
    missing = sorted(candidates - existing)
    return missing


def download_one(filename: str, ssl_ctx: ssl.SSLContext, max_retries: int = 3) -> Tuple[str, bool, int, str]:
    """Download a single PDF file and verify its contents.
    Returns: (filename, success, size_in_bytes, message)
    """
    dest_path = CACHE_DIR / filename
    temp_path = CACHE_DIR / f"{filename}.tmp"
    url = BASE_URL + filename

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
                if resp.status != 200:
                    return filename, False, 0, f"HTTP {resp.status}"

                content_len = resp.headers.get("content-length")
                expected_size = int(content_len) if content_len and content_len.isdigit() else None

                with open(temp_path, "wb") as f_out:
                    downloaded = 0
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f_out.write(chunk)
                        downloaded += len(chunk)

                # Verify PDF header
                with open(temp_path, "rb") as f_check:
                    header = f_check.read(5)
                    if header != b"%PDF-":
                        temp_path.unlink(missing_ok=True)
                        return filename, False, 0, "Corrupted PDF header"

                if expected_size and downloaded != expected_size:
                    temp_path.unlink(missing_ok=True)
                    if attempt < max_retries:
                        time.sleep(1)
                        continue
                    return filename, False, 0, f"Size mismatch: {downloaded} != {expected_size}"

                temp_path.replace(dest_path)
                return filename, True, downloaded, "OK"

        except urllib.error.HTTPError as he:
            temp_path.unlink(missing_ok=True)
            if he.code == 404:
                return filename, False, 0, "404 Not Found"
            if attempt < max_retries:
                time.sleep(2)
                continue
            return filename, False, 0, f"HTTP {he.code}: {he.reason}"
        except Exception as exc:
            temp_path.unlink(missing_ok=True)
            if attempt < max_retries:
                time.sleep(2)
                continue
            return filename, False, 0, str(exc)

    return filename, False, 0, "Max retries exceeded"


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ssl_ctx = create_ssl_context()

    missing = get_missing_candidate_list()
    print(f"Checking {len(missing)} candidate files missing from R20-11 cache...")

    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    total_bytes = 0

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(download_one, f, ssl_ctx): f for f in missing}
        for future in as_completed(futures):
            fname, success, size, msg = future.result()
            if success:
                downloaded_count += 1
                total_bytes += size
                print(f"[OK] {fname} ({size / 1024 / 1024:.2f} MB)")
            elif "404" in msg:
                skipped_count += 1
            else:
                failed_count += 1
                print(f"[FAIL] {fname}: {msg}")

    duration = time.time() - t0
    print("\n" + "=" * 60)
    print(f"Download complete in {duration:.1f}s")
    print(f"Downloaded: {downloaded_count} files ({total_bytes / 1024 / 1024:.1f} MB)")
    print(f"Skipped (404/not in CP): {skipped_count}")
    print(f"Failed: {failed_count}")
    total_now = len(list(CACHE_DIR.glob("*.pdf")))
    print(f"Total PDFs now in {CACHE_DIR.name}: {total_now}")


if __name__ == "__main__":
    main()
