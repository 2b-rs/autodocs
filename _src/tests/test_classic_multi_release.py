"""Integration tests for Classic COM multi-release data in the immutable version store."""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = _REPO_ROOT / "_src"
_CP_RECORD = _SRC / "spec" / "versions" / "AUTOSAR" / "CP" / "record"

sys.path.insert(0, str(_SRC / "tools"))
import asof_view as av  # noqa: E402
import delta_view as dv  # noqa: E402
from canonical_id import parse_canonical_id  # noqa: E402
from version_id import parse_version_id  # noqa: E402

SWS_COM_00001 = "AUTOSAR/CP/record/SWS_Com_00001"
TARGET_RELEASES = ("R19-11", "R20-11", "R21-11", "R22-11", "R25-11")
SAMPLE_ID_RANGE = tuple(f"SWS_Com_{n:05d}" for n in range(1, 16))

_REQUIRED_VERSION_KEYS = frozenset(
    {"version_id", "canonical_id", "release", "content", "recorded_at"}
)


class ClassicComMultiReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sws_com_files = sorted(_CP_RECORD.glob("SWS_Com_*.jsonl"))
        if not cls.sws_com_files:
            raise unittest.SkipTest("no SWS_Com_*.jsonl under CP/record")

    def test_sws_com_jsonl_files_exist_with_required_structure(self):
        """Every Classic COM JSONL line has the version-store contract fields."""
        self.assertGreater(len(self.sws_com_files), 0)
        for path in self.sws_com_files:
            stem = path.stem
            expected_cid = f"AUTOSAR/CP/record/{stem}"
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertTrue(lines, msg=f"empty store file: {path.name}")
            for line_no, line in enumerate(lines, start=1):
                line = line.strip()
                if not line:
                    continue
                with self.subTest(file=path.name, line=line_no):
                    entry = json.loads(line)
                    self.assertTrue(_REQUIRED_VERSION_KEYS <= set(entry.keys()))
                    if "meta" in entry:
                        self.assertIsInstance(entry["meta"], dict)
                    self.assertEqual(entry["canonical_id"], expected_cid)
                    self.assertIsInstance(entry["content"], str)
                    self.assertTrue(entry["content"].strip())
                    self.assertRegex(entry["release"], r"^R\d{2}-\d{2}$")
                    self.assertRegex(
                        entry["recorded_at"],
                        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$",
                    )

    def test_sws_com_00001_covers_documented_target_releases(self):
        path = _CP_RECORD / "SWS_Com_00001.jsonl"
        self.assertTrue(path.is_file(), "SWS_Com_00001.jsonl must exist")
        releases = {
            json.loads(line)["release"]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        for release in TARGET_RELEASES:
            self.assertIn(release, releases, msg=f"missing release {release} on SWS_Com_00001")

    def test_as_of_release_sws_com_00001_returns_release_specific_history(self):
        view_r20 = av.as_of_release(SWS_COM_00001, "R20-11")
        view_r25 = av.as_of_release(SWS_COM_00001, "R25-11")

        self.assertEqual(view_r20["canonical_id"], SWS_COM_00001)
        self.assertEqual(view_r25["canonical_id"], SWS_COM_00001)

        v20 = view_r20["version"]
        v25 = view_r25["version"]
        self.assertIsNotNone(v20)
        self.assertIsNotNone(v25)
        self.assertEqual(v20["release"], "R20-11")
        self.assertEqual(v25["release"], "R25-11")
        self.assertNotEqual(v20["version_id"], v25["version_id"])
        self.assertEqual(
            v20["version_id"],
            "AUTOSAR/CP/record/SWS_Com_00001@rel:R20-11#a77f568c",
        )
        self.assertEqual(
            v25["version_id"],
            "AUTOSAR/CP/record/SWS_Com_00001@rel:R25-11#924080ec",
        )
        self.assertIn("R20 - 11", v20["content"])
        self.assertIn("Com_TriggerTransmit", v25["content"])
        self.assertNotIn("Com_ Trigger Transmit", v25["content"])

        for release in TARGET_RELEASES:
            view = av.as_of_release(SWS_COM_00001, release)
            self.assertEqual(view["version"]["release"], release)
            self.assertIn(f"@rel:{release}#", view["version"]["version_id"])

    def test_delta_view_since_r20_11_lists_changed_classic_com_requirements(self):
        result = dv.delta_view(release="R20-11")
        baseline_ts = result["baseline"]["resolved_timestamp"]
        self.assertIsNotNone(baseline_ts)
        self.assertEqual(result["baseline"]["release"], "R20-11")

        changed = result["changed_requirements"]
        self.assertIn(SWS_COM_00001, changed)

        com_changed = [cid for cid in changed if cid.startswith("AUTOSAR/CP/record/SWS_Com_")]
        self.assertGreater(len(com_changed), 10)
        for cid in com_changed:
            self.assertRegex(cid, r"^AUTOSAR/CP/record/SWS_Com_[A-Z0-9_]+$")

        # At least one later release for 00001 was recorded strictly after the R20-11 baseline.
        path = _CP_RECORD / "SWS_Com_00001.jsonl"
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        later = [e for e in entries if e["recorded_at"] > baseline_ts and e["release"] > "R20-11"]
        self.assertTrue(later, msg="expected post-R20-11 versions after baseline timestamp")

    def test_canonical_namespace_and_version_id_conventions(self):
        version_id_re = re.compile(
            r"^AUTOSAR/CP/record/SWS_Com_[A-Z0-9_]+@rel:R\d{2}-\d{2}#[0-9a-f]{8}$"
        )
        for path in self.sws_com_files:
            if path.stem not in SAMPLE_ID_RANGE:
                continue
            with self.subTest(record=path.stem):
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    cid = entry["canonical_id"]
                    parsed = parse_canonical_id(cid)
                    self.assertIsNotNone(parsed)
                    self.assertEqual(parsed["project"], "AUTOSAR/CP")
                    self.assertEqual(parsed["kind"], "record")
                    self.assertEqual(parsed["id"], path.stem)
                    self.assertRegex(entry["version_id"], version_id_re)
                    self.assertTrue(entry["version_id"].startswith(f"{cid}@rel:"))
                    vid = parse_version_id(entry["version_id"])
                    self.assertEqual(vid["canonical_id"], cid)
                    self.assertEqual(vid["release"], entry["release"])


if __name__ == "__main__":
    unittest.main()
