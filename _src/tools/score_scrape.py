#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score_scrape.py — Scrape curatable records from Eclipse S-CORE repository trees (0009-02).

Implements the repository crawler/scraper for Eclipse S-CORE codebases adhering to:
- docs/pipeline/score-identity-scheme.md (0009-01 kind/ID taxonomy & 0009-04 release versioning)
- _src/tools/canonical_id.py (ECLIPSE/S-CORE project naming)
- _src/tools/version_id.py (hash/version helpers)

Scrapes four kinds of units:
1. module: from MODULE.bazel (or directory fallback)
2. component: from subdirectories containing BUILD / BUILD.bazel packages
3. design-doc: from sphinx-needs directive blocks in .rst / .md doc files
4. process-doc: from process_description docs / sphinx-needs items
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_PROJECT = "ECLIPSE/S-CORE"
SPHINX_NEED_DIRECTIVE_RE = re.compile(
    r"\.\.\s+(req|need|spec|arch_element|feat|work_product)::\s*([^\n\r]+)",
    re.IGNORECASE
)
SPHINX_NEED_ID_RE = re.compile(r":id:\s*([A-Za-z0-9_\-\.]+)")
SPHINX_NEED_TITLE_RE = re.compile(r":title:\s*([^\n\r]+)")
BAZEL_MODULE_RE = re.compile(r'module\s*\(\s*name\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


def content_hash8(data: str | bytes) -> str:
    """Compute truncated SHA-256 (32 bits / 8 hex chars)."""
    if isinstance(data, str):
        raw = data.encode("utf-8")
    else:
        raw = data
    return hashlib.sha256(raw).hexdigest()[:8]


def parse_bazel_module_name(module_bazel_path: Path) -> Optional[str]:
    """Extract module(name = "...") from MODULE.bazel."""
    if not module_bazel_path.is_file():
        return None
    try:
        content = module_bazel_path.read_text(encoding="utf-8", errors="replace")
        match = BAZEL_MODULE_RE.search(content)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return None


def extract_sphinx_needs(file_path: Path) -> List[Dict[str, Any]]:
    """Parse sphinx-needs blocks from rst/md documentation files."""
    needs = []
    if not file_path.is_file():
        return needs
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return needs

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        match = SPHINX_NEED_DIRECTIVE_RE.search(line)
        if match:
            need_type = match.group(1).lower()
            inline_title = match.group(2).strip()
            need_id = None
            need_title = inline_title
            block_lines = [line]
            i += 1
            while i < len(lines) and (lines[i].startswith("   ") or lines[i].startswith("\t") or lines[i].strip() == ""):
                b_line = lines[i]
                block_lines.append(b_line)
                id_match = SPHINX_NEED_ID_RE.search(b_line)
                if id_match:
                    need_id = id_match.group(1).strip()
                title_match = SPHINX_NEED_TITLE_RE.search(b_line)
                if title_match:
                    need_title = title_match.group(1).strip()
                i += 1

            block_text = "\n".join(block_lines)
            if not need_id:
                # generate deterministic ID from type and content hash if not explicitly set
                need_id = f"SCORE_{need_type.upper()}_{content_hash8(block_text)}"
            needs.append({
                "type": need_type,
                "id": need_id,
                "title": need_title,
                "raw": block_text
            })
        else:
            i += 1
    return needs


class ScoreRepoScraper:
    """Crawls an Eclipse S-CORE repository directory and emits curatable records."""

    def __init__(self, repo_path: Path, release_label: str = "main",
                 source_ref_kind: str = "release-branch",
                 source_commit: Optional[str] = None,
                 repo_origin: Optional[str] = None):
        self.repo_path = repo_path.resolve()
        self.release_label = release_label
        self.source_ref_kind = source_ref_kind
        self.source_commit = source_commit or "0000000000000000000000000000000000000000"
        self.repo_origin = repo_origin or f"eclipse-score/{self.repo_path.name}"

    def scrape(self) -> List[Dict[str, Any]]:
        records = []

        # 1. Module record
        module_bazel = self.repo_path / "MODULE.bazel"
        bazel_name = parse_bazel_module_name(module_bazel)
        module_id = bazel_name if bazel_name else self.repo_path.name

        module_summary = f"Eclipse S-Core module {module_id}"
        readme_file = self.repo_path / "README.md"
        if readme_file.is_file():
            try:
                module_summary = readme_file.read_text(encoding="utf-8", errors="replace")[:1000]
            except Exception:
                pass

        mod_raw = f"module:{module_id}:{module_summary}"
        chash_mod = content_hash8(mod_raw)
        canonical_mod_id = f"{DEFAULT_PROJECT}/module/{module_id}"
        version_mod_id = f"{canonical_mod_id}@rel:{self.release_label}#{chash_mod}"

        records.append({
            "project": DEFAULT_PROJECT,
            "kind": "module",
            "id": module_id,
            "canonical_id": canonical_mod_id,
            "version_id": version_mod_id,
            "title": f"Module: {module_id}",
            "description": module_summary,
            "provenance": {
                "source_repo_origin": self.repo_origin,
                "source_ref_kind": self.source_ref_kind,
                "source_ref": self.release_label,
                "source_commit": self.source_commit,
                "source_path": "/"
            }
        })

        # 2. Component records (Bazel packages)
        for root, dirs, files in os.walk(self.repo_path):
            if any(p.startswith(".") for p in Path(root).parts):
                continue
            rpath = Path(root)
            if rpath == self.repo_path:
                continue
            has_build = any(f in ("BUILD", "BUILD.bazel") for f in files)
            if has_build:
                rel_parts = rpath.relative_to(self.repo_path).parts
                comp_pkg = ".".join(rel_parts)
                comp_id = f"{module_id}.{comp_pkg}"
                comp_raw = f"component:{comp_id}"
                chash_comp = content_hash8(comp_raw)
                canonical_comp_id = f"{DEFAULT_PROJECT}/component/{comp_id}"
                version_comp_id = f"{canonical_comp_id}@rel:{self.release_label}#{chash_comp}"

                records.append({
                    "project": DEFAULT_PROJECT,
                    "kind": "component",
                    "id": comp_id,
                    "canonical_id": canonical_comp_id,
                    "version_id": version_comp_id,
                    "title": f"Component: {comp_id}",
                    "description": f"Bazel package component at {rpath.relative_to(self.repo_path)}",
                    "provenance": {
                        "source_repo_origin": self.repo_origin,
                        "source_ref_kind": self.source_ref_kind,
                        "source_ref": self.release_label,
                        "source_commit": self.source_commit,
                        "source_path": str(rpath.relative_to(self.repo_path))
                    }
                })

        # 3. Design docs and process docs (Sphinx-needs)
        is_process_repo = "process" in self.repo_path.name.lower()
        for root, dirs, files in os.walk(self.repo_path):
            if any(p.startswith(".") for p in Path(root).parts):
                continue
            rpath = Path(root)
            for f in files:
                if f.endswith((".rst", ".md")):
                    fpath = rpath / f
                    needs = extract_sphinx_needs(fpath)
                    for n in needs:
                        kind = "process-doc" if is_process_repo else "design-doc"
                        need_id = n["id"]
                        raw_content = n["raw"]
                        chash = content_hash8(raw_content)
                        can_id = f"{DEFAULT_PROJECT}/{kind}/{need_id}"
                        ver_id = f"{can_id}@rel:{self.release_label}#{chash}"

                        records.append({
                            "project": DEFAULT_PROJECT,
                            "kind": kind,
                            "id": need_id,
                            "canonical_id": can_id,
                            "version_id": ver_id,
                            "title": n["title"],
                            "description": raw_content,
                            "sphinx_need_type": n["type"],
                            "provenance": {
                                "source_repo_origin": self.repo_origin,
                                "source_ref_kind": self.source_ref_kind,
                                "source_ref": self.release_label,
                                "source_commit": self.source_commit,
                                "source_path": str(fpath.relative_to(self.repo_path))
                            }
                        })

        return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape Eclipse S-CORE repository into curatable records.")
    parser.add_argument("repo_path", type=Path, help="Path to local Eclipse S-Core repository checkout")
    parser.add_argument("--release", default="main", help="Release label or tag")
    parser.add_argument("--ref-kind", choices=["tag", "release-branch"], default="release-branch")
    parser.add_argument("--commit", default="0000000000000000000000000000000000000000", help="Git commit SHA")
    parser.add_argument("--output", type=Path, help="Optional JSON output file path")

    args = parser.parse_args()
    if not args.repo_path.is_dir():
        sys.stderr.write(f"Error: Directory {args.repo_path} does not exist\n")
        return 1

    scraper = ScoreRepoScraper(
        repo_path=args.repo_path,
        release_label=args.release,
        source_ref_kind=args.ref_kind,
        source_commit=args.commit
    )
    records = scraper.scrape()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"records": records, "count": len(records)}, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Scraped {len(records)} records to {args.output}")
    else:
        print(json.dumps({"records": records, "count": len(records)}, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
