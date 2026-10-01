#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test suite for score_scrape.py (0009-02)."""
import json
import shutil
import tempfile
from pathlib import Path
import sys

# Ensure _src/tools is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_scrape import ScoreRepoScraper, parse_bazel_module_name, extract_sphinx_needs


def test_score_scraper():
    tmp_dir = Path("/tmp/test_score_repo")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)

    try:
        # Create mock module
        (tmp_dir / "MODULE.bazel").write_text('module(name = "communication", version = "2026.1")\n', encoding="utf-8")
        (tmp_dir / "README.md").write_text("# Communication Module\nProvides ara::com support.\n", encoding="utf-8")

        # Create mock component package
        comp_dir = tmp_dir / "mw" / "com"
        comp_dir.mkdir(parents=True)
        (comp_dir / "BUILD.bazel").write_text('cc_library(name = "com")\n', encoding="utf-8")

        # Create mock sphinx-needs doc
        doc_dir = tmp_dir / "docs"
        doc_dir.mkdir(parents=True)
        (doc_dir / "arch.rst").write_text("""
Architecture Overview
=====================

.. req:: IPC Communication Requirement
   :id: REQ_SCORE_COM_001
   :title: Fast IPC transport

   The communication module shall provide low-latency IPC.
""", encoding="utf-8")

        scraper = ScoreRepoScraper(
            repo_path=tmp_dir,
            release_label="2026.1",
            source_ref_kind="tag",
            source_commit="abcdef1234567890abcdef1234567890abcdef12",
            repo_origin="eclipse-score/communication"
        )
        records = scraper.scrape()

        assert len(records) >= 3, f"Expected at least 3 records, got {len(records)}"

        kinds = {r["kind"] for r in records}
        assert "module" in kinds, "Missing module kind"
        assert "component" in kinds, "Missing component kind"
        assert "design-doc" in kinds, "Missing design-doc kind"

        mod_rec = next(r for r in records if r["kind"] == "module")
        assert mod_rec["id"] == "communication"
        assert mod_rec["canonical_id"] == "ECLIPSE/S-CORE/module/communication"
        assert "@rel:2026.1#" in mod_rec["version_id"]
        assert mod_rec["provenance"]["source_ref_kind"] == "tag"

        comp_rec = next(r for r in records if r["kind"] == "component")
        assert comp_rec["id"] == "communication.mw.com"
        assert comp_rec["canonical_id"] == "ECLIPSE/S-CORE/component/communication.mw.com"

        doc_rec = next(r for r in records if r["kind"] == "design-doc")
        assert doc_rec["id"] == "REQ_SCORE_COM_001"
        assert doc_rec["canonical_id"] == "ECLIPSE/S-CORE/design-doc/REQ_SCORE_COM_001"

        print("All score_scrape unit tests passed successfully!")
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    test_score_scraper()
