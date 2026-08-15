import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import review_request_package as rrp  # noqa: E402
from version_id import content_hash8  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "review_request"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ReviewRequestPackageTests(unittest.TestCase):
    def test_valid_github_issue_package_has_no_errors(self):
        pkg = load("valid_github_issue.json")
        self.assertEqual(rrp.validate(pkg), [])
        self.assertTrue(rrp.is_valid(pkg))

    def test_valid_json_export_package_has_no_errors(self):
        pkg = load("valid_json_export.json")
        self.assertEqual(rrp.validate(pkg), [])
        self.assertTrue(rrp.is_valid(pkg))

    def test_invalid_package_reports_multiple_errors(self):
        pkg = load("invalid_missing_fields.json")
        errors = rrp.validate(pkg)
        self.assertTrue(errors)
        self.assertTrue(any("unknown schema" in e for e in errors))
        self.assertTrue(any("rationale" in e for e in errors))
        self.assertTrue(any("request_id" in e for e in errors))
        self.assertFalse(rrp.is_valid(pkg))

    def test_new_request_id_matches_schema_pattern(self):
        rid = rrp.new_request_id()
        self.assertTrue(rid.startswith("review-request:"))
        self.assertIsNotNone(rrp._REQUEST_ID_RE.match(rid))

    def test_dedup_key_ignores_request_id(self):
        a = load("valid_github_issue.json")
        b = dict(a)
        b["request_id"] = rrp.new_request_id()
        self.assertEqual(rrp.dedup_key(a), rrp.dedup_key(b))

    def test_canonical_serialize_is_deterministic_regardless_of_key_order(self):
        pkg = load("valid_github_issue.json")
        reordered = dict(reversed(list(pkg.items())))
        self.assertEqual(rrp.canonical_serialize(pkg), rrp.canonical_serialize(reordered))

    def test_content_hash8_is_deterministic(self):
        content = "Global time as a service for applications..."
        h1 = content_hash8(content)
        h2 = content_hash8(content)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 8)

    def test_is_stale_requires_both_hash_and_version_mismatch(self):
        pkg = load("valid_github_issue.json")
        self.assertFalse(rrp.is_stale(pkg, pkg["target_content_hash"], pkg["target_version_id"]))
        self.assertFalse(rrp.is_stale(pkg, "deadbeef", pkg["target_version_id"]))
        self.assertTrue(rrp.is_stale(
            pkg, "deadbeef",
            "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#deadbeef"))

    def test_json_export_null_version_id_is_valid(self):
        pkg = load("valid_json_export.json")
        self.assertIsNone(pkg["target_version_id"])
        self.assertEqual(rrp.validate(pkg), [])


if __name__ == "__main__":
    unittest.main()
