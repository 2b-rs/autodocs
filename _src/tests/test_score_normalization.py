#!/usr/bin/env python3
"""Hermetic normalization tests for Task 0019-05."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
FIXTURE = ROOT / "_src" / "tests" / "fixtures" / "score_normalization" / "raw-fixture-corpus.json"
PROFILE = ROOT / "_src" / "spec" / "import-profiles" / "eclipse-score-v0.6.0.json"

sys.path.insert(0, str(TOOLS))
import canonical_id  # noqa: E402
import score_import_profile as import_profile  # noqa: E402
import score_normalization as normalization  # noqa: E402
import version_id  # noqa: E402


def fixture_raw() -> tuple[dict[str, Any], dict[str, Any]]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    observations = []
    for item in fixture["candidates"]:
        candidate = copy.deepcopy(item["candidate"])
        observations.append({"candidate": candidate, "decision": import_profile.evaluate_candidate(profile, candidate)})
    raw = {
        "schema": "score-raw-extraction@v1",
        "project": fixture["project"],
        "release": fixture["release"],
        "manifest_sha256": "a" * 64,
        "profile_id": profile["profile_id"],
        "profile_version": profile["profile_version"],
        "profile_sha256": "b" * 64,
        "observations": observations,
    }
    return raw, fixture


class ScoreNormalizationTests(unittest.TestCase):
    def test_fixture_corpus_materializes_all_kinds_with_deterministic_identity(self) -> None:
        raw, fixture = fixture_raw()
        first = normalization.normalize(raw, fixture["import_date"])
        second = normalization.normalize(copy.deepcopy(raw), fixture["import_date"])
        self.assertEqual(normalization.canonical_json_bytes(first), normalization.canonical_json_bytes(second))
        self.assertEqual({"module", "component", "design-doc", "process-doc"}, {record["kind"] for record in first["records"]})
        self.assertEqual(4, len(first["records"]))
        self.assertFalse(first["canonical_corpus_written"])
        self.assertFalse(first["queue_written"])
        self.assertFalse(first["publication_permitted"])

        for record in first["records"]:
            self.assertEqual("score-normalized-record@v1", record["schema"])
            self.assertEqual(f"{record['project']}/{record['kind']}/{record['id']}", record["canonical_id"])
            self.assertEqual({"project": "ECLIPSE/S-CORE", "kind": record["kind"], "id": record["id"]}, canonical_id.parse_canonical_id(record["canonical_id"]))
            parsed_version = version_id.parse_version_id(record["version_id"])
            self.assertEqual(record["canonical_id"], parsed_version["canonical_id"])
            self.assertEqual(fixture["release"], parsed_version["release"])
            self.assertEqual(record["content_hash8"], parsed_version["hash8"])
            self.assertEqual(record["content_hash"][:8], record["content_hash8"])
            self.assertEqual("invalid/to-be-confirmed", record["status"]["state"])
            self.assertEqual(fixture["import_date"], record["history"][0]["date"])
            self.assertEqual(record["status"]["state"], record["history"][0]["to"])
            provenance = record["provenance"]
            self.assertEqual(record["traceability"]["sources"][0]["resolved_commit"], provenance["source_commit"])
            self.assertEqual(record["traceability"]["sources"][0]["locator"], provenance["source_locator"])
            self.assertIn("campaign_manifest_sha256", provenance)
            self.assertIn("import_profile_sha256", provenance)

    def test_fixture_collision_and_contradiction_are_discovered_candidates_not_queued(self) -> None:
        raw, fixture = fixture_raw()
        result = normalization.normalize(raw, fixture["import_date"])
        exceptions = result["exception_candidates"]
        self.assertEqual({"identity-collision", "source-contradiction"}, {item["exception_kind"] for item in exceptions})
        self.assertEqual(2, len(exceptions))
        for item in exceptions:
            self.assertEqual("score-normalization-exception-candidate@v1", item["schema"])
            self.assertEqual("discovered", item["lifecycle_state"])
            self.assertEqual("0019-07", item["physical_queue_writer"])
            self.assertFalse(item["queue_written"])
            self.assertTrue(item["candidate_id"].startswith("score-normalization-exception:"))
            self.assertEqual("ECLIPSE/S-CORE/design-doc/dec_rec__infra__dev_tools", item["canonical_id"])

    def test_direct_duplicate_records_are_not_overwritten(self) -> None:
        raw, fixture = fixture_raw()
        source = next(item for item in raw["observations"] if item["decision"].get("record", {}).get("kind") == "module")
        identical = copy.deepcopy(source)
        contradictory = copy.deepcopy(source)
        contradictory["decision"]["record"]["title"] = "A contradictory module title"
        raw["observations"].extend([identical, contradictory])
        result = normalization.normalize(raw, fixture["import_date"])
        self.assertEqual(4, len(result["records"]))
        direct_exceptions = [item for item in result["exception_candidates"] if item["condition_id"].startswith("NORMALIZATION-")]
        self.assertEqual({"identity-collision", "source-contradiction"}, {item["exception_kind"] for item in direct_exceptions})
        self.assertTrue(all(item["existing_version_id"] for item in direct_exceptions))

    def test_invalid_import_date_and_incomplete_provenance_fail_closed(self) -> None:
        raw, fixture = fixture_raw()
        with self.assertRaisesRegex(normalization.NormalizationError, "ISO-8601"):
            normalization.normalize(raw, "today")
        raw["observations"][0]["decision"]["record"]["provenance"].pop("source_commit")
        with self.assertRaisesRegex(normalization.NormalizationError, "source_commit"):
            normalization.normalize(raw, fixture["import_date"])

    def test_cli_is_atomic_and_repeatable(self) -> None:
        raw, fixture = fixture_raw()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw_path = root / "raw.json"
            output = root / "normalized.json"
            raw_path.write_bytes(normalization.canonical_json_bytes(raw))
            first = subprocess.run(
                [sys.executable, str(TOOLS / "score_normalization.py"), str(raw_path), "--import-date", fixture["import_date"], "--output", str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, first.returncode, first.stderr)
            first_bytes = output.read_bytes()
            second = subprocess.run(
                [sys.executable, str(TOOLS / "score_normalization.py"), str(raw_path), "--import-date", fixture["import_date"], "--output", str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual(first_bytes, output.read_bytes())
            output.write_text("previous output\n", encoding="utf-8")
            failed = subprocess.run(
                [sys.executable, str(TOOLS / "score_normalization.py"), str(raw_path), "--import-date", "not-a-date", "--output", str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, failed.returncode)
            self.assertEqual("previous output\n", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
