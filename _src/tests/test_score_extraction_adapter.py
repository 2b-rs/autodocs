#!/usr/bin/env python3
"""Hermetic and retained-snapshot tests for the Task 0019-04 extractor."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
sys.path.insert(0, str(TOOLS))
import score_extraction_adapter as adapter  # noqa: E402
import score_source_snapshot as snapshot  # noqa: E402

MANIFEST_PATH = ROOT / "_src" / "spec" / "campaigns" / "eclipse-score-v0.6.0.json"
PROFILE_PATH = ROOT / "_src" / "spec" / "import-profiles" / "eclipse-score-v0.6.0.json"


def write_tar(path: Path, files: Mapping[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w") as archive:
        for name in sorted(files):
            member = tarfile.TarInfo(name)
            member.size = len(files[name])
            member.mtime = 0
            archive.addfile(member, io.BytesIO(files[name]))


class ScoreExtractionAdapterTests(unittest.TestCase):
    def prepare_campaign(self, root: Path, score_docs: Mapping[str, bytes] | None = None, extra_score: Mapping[str, bytes] | None = None):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        score_docs = score_docs or {
            "docs/design.md": b"```{dec_rec} Pinned design decision\n:id: dec__pinned\n```\n",
        }
        score_files = {
            "LICENSE": b"Apache-2.0\n",
            "MODULE.bazel": b'module(name = "score_platform")\n',
            "tools/format/BUILD": b"exports_files([\"format.py\"])\n",
            **score_docs,
            **(extra_score or {}),
        }
        process_files = {
            "LICENSE": b"Apache-2.0\n",
            "process/roles.rst": b".. role:: Project Lead\n   :id: rl__project_lead\n",
        }
        sources = {source["repository"]: source for source in manifest["sources"]}
        for repository, files in (("score", score_files), ("process_description", process_files)):
            source = sources[repository]
            archive_path = root / source["snapshot_archive"]
            write_tar(archive_path, files)
            source["archive"]["sha256"] = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        manifest["snapshot"]["inventory_sha256"] = "0" * 64
        manifest_path = root / "_src/spec/campaigns/eclipse-score-v0.6.0.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        _, digest, _ = snapshot.write_inventory(manifest, root)
        manifest["snapshot"]["inventory_sha256"] = digest
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        profile_path = root / "_src/spec/import-profiles/eclipse-score-v0.6.0.json"
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
        return manifest, profile, manifest_path, profile_path

    def test_successful_extraction_is_deterministic_and_noncanonical(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, profile, _, _ = self.prepare_campaign(Path(temporary))
            first = adapter.extract(manifest, profile, Path(temporary))
            second = adapter.extract(manifest, profile, Path(temporary))
            self.assertEqual(adapter.canonical_json_bytes(first), adapter.canonical_json_bytes(second))
            self.assertFalse(first["complete"])
            self.assertFalse(first["canonical_corpus_written"])
            self.assertEqual(4, first["summary"]["observations"])
            self.assertEqual({"module", "component", "design-doc", "process-doc"}, {item["decision"]["record"]["kind"] for item in first["observations"]})

    def test_missing_source_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest, profile, manifest_path, profile_path = self.prepare_campaign(root)
            (root / manifest["sources"][0]["snapshot_archive"]).unlink()
            output = root / "raw.json"
            output.write_text("prior output\n", encoding="utf-8")
            completed = subprocess.run([sys.executable, str(TOOLS / "score_extraction_adapter.py"), str(manifest_path), str(profile_path), "--repository-root", str(root), "--output", str(output)], text=True, capture_output=True, check=False)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("retained source verification failed", completed.stderr)
            self.assertEqual("prior output\n", output.read_text(encoding="utf-8"))

    def test_invalid_archive_hash_identifies_pinned_source_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest, profile, _, _ = self.prepare_campaign(root)
            manifest["sources"][0]["archive"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(adapter.ExtractionError, "repository=.*process_description|repository=.*score") as raised:
                adapter.extract(manifest, profile, root)
            self.assertIn("retained source verification failed", str(raised.exception))

    def test_invalid_ref_pin_is_rejected_with_source_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest, profile, _, _ = self.prepare_campaign(root)
            manifest["sources"][0]["resolved_commit"] = "0" * 40
            with self.assertRaisesRegex(adapter.ExtractionError, "manifest/profile pin mismatch.*repository"):
                adapter.extract(manifest, profile, root)

    def test_malformed_sphinx_need_is_a_deterministic_review_observation(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, profile, _, _ = self.prepare_campaign(Path(temporary), {"docs/design.md": b".. dec_rec:: Bad identifier\n   :id: invalid id\n"})
            result = adapter.extract(manifest, profile, Path(temporary))
            malformed = [item for item in result["observations"] if item["decision"]["condition_id"] == "REVIEW-MALFORMED-NEED-ID"]
            self.assertEqual(1, len(malformed))
            self.assertIsNone(malformed[0]["decision"]["record"])

    def test_duplicate_identity_is_reviewed_not_materialized_twice(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, profile, _, _ = self.prepare_campaign(Path(temporary), {
                "docs/a.md": b"```{dec_rec} First\n:id: dec__same\n```\n",
                "docs/b.md": b"```{dec_rec} Second\n:id: dec__same\n```\n",
            })
            result = adapter.extract(manifest, profile, Path(temporary))
            design_observations = [item for item in result["observations"] if item["candidate"]["source_class"] == "score-design-need"]
            decisions = [item["decision"]["condition_id"] for item in design_observations]
            self.assertEqual(["QUEUE-INITIAL-CURATION", "REVIEW-DUPLICATE-CANONICAL"], decisions)
            self.assertEqual(1, sum(item["decision"]["record"] is not None for item in design_observations))

    def test_unsupported_selected_artifact_is_retained_as_a_noncanonical_skip(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, profile, _, _ = self.prepare_campaign(Path(temporary), extra_score={"docs/diagram.png": b"not documentation"})
            result = adapter.extract(manifest, profile, Path(temporary))
            self.assertIn({"repository": "score", "release_ref": "v0.6.0", "resolved_commit": manifest["sources"][0]["resolved_commit"], "path": "docs/diagram.png", "locator": "https://github.com/eclipse-score/score/blob/db1f5bb87ad7f41b40b6aca4b96a889d8798735e/docs/diagram.png", "reason": "UNSUPPORTED-ARTIFACT"}, result["skipped_artifacts"])

    def test_retained_campaign_repeated_output_is_byte_identical(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.json"
            second = Path(temporary) / "second.json"
            adapter.write_output(first, adapter.extract(manifest, profile, ROOT))
            adapter.write_output(second, adapter.extract(manifest, profile, ROOT))
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
