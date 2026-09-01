import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_src" / "tools"))
import prepare_score_curation_export as export


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


class PrepareScoreCurationExportTests(unittest.TestCase):
    RECORDS = 2

    def fixture(self, temporary):
        source = temporary / "candidate"
        records = source / "records"
        records.mkdir(parents=True)
        manifest = []
        page = f'<html><head><link rel="stylesheet" href="../style.css"><script src="../review_request.js"></script></head><body data-validation-state="unvalidated"><p data-unvalidated-marker="awaiting-curator-confirmation">{export.MARKER}</p><a id="source-locator" href="https://example.invalid/source">source</a><section data-curation-route="review-request"></section></body></html>'
        for index in range(self.RECORDS):
            name = f"records/{index:024x}.html"
            (source / name).write_text(page, encoding="utf-8")
            manifest.append({"canonical_id": f"ID-{index}", "version_id": f"VER-{index}", "page": name, "status": {"state": export.STATUS}, "source_locator": "https://example.invalid/source"})
        (records / "index.html").write_text(f"<html>{export.MARKER}</html>", encoding="utf-8")
        (source / "process.html").write_text(f'<html>{export.MARKER}<section id="flag-for-review-protocol"></section><section id="storage-and-privacy"></section></html>', encoding="utf-8")
        (source / "review_request.js").write_bytes((ROOT / "review_request.js").read_bytes())
        (source / "style.css").write_bytes((ROOT / "docs/campaign-evidence/eclipse-score-v0.6.0-curation-review/style.css").read_bytes())
        evidence = {"scope": "unvalidated-curation-candidates", "validation_marker": export.MARKER, "counts": {"records": self.RECORDS, "candidate_pages": self.RECORDS, "by_status": {export.STATUS: self.RECORDS}}, "candidate_manifest_sha256": hashlib.sha256(canonical(manifest)).hexdigest(), "candidate_manifest": manifest}
        validation = {"scope": "unvalidated-curation-candidates", "result": "PASS", "candidate_manifest_sha256": evidence["candidate_manifest_sha256"]}
        (source / "evidence.json").write_bytes(canonical(evidence))
        (source / "validation.json").write_bytes(canonical(validation))
        expected = {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in ("evidence.json", "validation.json")}
        return source, expected

    def test_successful_preparation_is_byte_identical_and_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            source, expected = self.fixture(Path(directory))
            destination = Path(directory) / "export"
            with patch.object(export, "EXPECTED", expected), patch.object(export, "EXPECTED_RECORDS", self.RECORDS):
                first = export.prepare(source, destination)
                second = export.prepare(source, destination)
            self.assertEqual(first, second)
            self.assertEqual(self.RECORDS, first["record_pages"])
            source_files = export.regular_files(source)
            destination_files = export.regular_files(destination)
            self.assertEqual(export.public_files(source_files).keys(), destination_files.keys())
            self.assertTrue(all(source_files[name].read_bytes() == destination_files[name].read_bytes() for name in destination_files))

    def test_marker_status_and_manifest_mismatches_refuse(self):
        for change, expression in ((lambda source: (source / "records/000000000000000000000000.html").write_text("<html>missing</html>", encoding="utf-8"), "marker missing"), (lambda source: (source / "evidence.json").write_text("{}", encoding="utf-8"), "manifest digest mismatch"), (lambda source: (source / "records/000000000000000000000000.html").write_text((source / "records/000000000000000000000000.html").read_text(encoding="utf-8").replace('data-validation-state=\"unvalidated\"', 'data-validation-state=\"valid\"'), encoding="utf-8"), "status marker missing")):
            with tempfile.TemporaryDirectory() as directory:
                source, expected = self.fixture(Path(directory))
                change(source)
                with patch.object(export, "EXPECTED", expected), patch.object(export, "EXPECTED_RECORDS", self.RECORDS), self.assertRaisesRegex(ValueError, expression):
                    export.prepare(source, Path(directory) / "export")

    def test_source_internal_files_are_excluded_and_allowlisted_artifacts_are_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            source, expected = self.fixture(Path(directory))
            destination = Path(directory) / "export"
            (source / "dom-assertions.json").write_text("internal", encoding="utf-8")
            (source / "integration-review.md").write_text("internal", encoding="utf-8")
            (source / ".provenance-receipt").write_text("internal", encoding="utf-8")
            (source / "index.html").write_text(f'<html>{export.MARKER}<a href="unresolved.html">collision</a></html>', encoding="utf-8")
            (source / "en").mkdir()
            (source / "en/index.html").write_text(f'<html>{export.MARKER}<a href="../unresolved.html">collision</a></html>', encoding="utf-8")
            (source / "en/unresolved.html").write_text(f"<html>{export.MARKER}</html>", encoding="utf-8")
            (source / export.CANONICAL_LANGUAGE).mkdir(exist_ok=True)
            (source / export.CANONICAL_LANGUAGE / "unresolved.html").write_text(f"<html>{export.MARKER}</html>", encoding="utf-8")
            with patch.object(export, "EXPECTED", expected), patch.object(export, "EXPECTED_RECORDS", self.RECORDS):
                first = export.prepare(source, destination)
                second = export.prepare(source, destination)
            self.assertEqual(first, second)
            self.assertIn(f'href="{export.CANONICAL_LANGUAGE}/unresolved.html"', (destination / "index.html").read_text(encoding="utf-8"))
            self.assertIn('href="unresolved.html"', (destination / "en/index.html").read_text(encoding="utf-8"))
            self.assertFalse((destination / "dom-assertions.json").exists())
            self.assertFalse((destination / "integration-review.md").exists())
            self.assertFalse((destination / ".provenance-receipt").exists())
            self.assertEqual(set(export.public_files(export.regular_files(source))), set(export.regular_files(destination)))

    def test_every_configured_language_directory_is_public(self):
        for language in export.PUBLIC_LANGUAGES:
            self.assertTrue(export.is_public_export_path(f"{language}/index.html"))

    def test_scope_leak_unmanaged_destination_and_overlap_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            source, expected = self.fixture(Path(directory))
            destination = Path(directory) / "export"
            with patch.object(export, "EXPECTED", expected), patch.object(export, "EXPECTED_RECORDS", self.RECORDS):
                export.prepare(source, destination)
                (destination / "unexpected.txt").write_text("leak", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "unexpected public export path"):
                    export.validate_tree(destination)
                with self.assertRaisesRegex(ValueError, "unexpected public export path"):
                    export.prepare(source, destination)
                with self.assertRaisesRegex(ValueError, "overlap"):
                    export.prepare(source, source)
        with tempfile.TemporaryDirectory() as directory:
            source, expected = self.fixture(Path(directory))
            path = source / "records/000000000000000000000000.html"
            path.write_text(path.read_text(encoding="utf-8").replace("https://example.invalid/source", "../../private.html"), encoding="utf-8")
            with patch.object(export, "EXPECTED", expected), patch.object(export, "EXPECTED_RECORDS", self.RECORDS), self.assertRaisesRegex(ValueError, "link escapes export scope"):
                export.prepare(source, Path(directory) / "export")

    def test_browser_url_refusals_and_removed_targets_fail_closed(self):
        refused = (
            ("//example.invalid/x", "protocol-relative"),
            ("/absolute.html", "non-allowlisted"),
            ("javascript:alert(1)", "non-allowlisted"),
            ("..\\private.html", "unsafe link"),
            ("%2e%2e/%2e%2e/private.html", "escapes export scope"),
        )
        for target, expression in refused:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                source, expected = self.fixture(Path(directory))
                page = source / "records/000000000000000000000000.html"
                page.write_text(page.read_text(encoding="utf-8").replace("https://example.invalid/source", target), encoding="utf-8")
                with patch.object(export, "EXPECTED", expected), patch.object(export, "EXPECTED_RECORDS", self.RECORDS), self.assertRaisesRegex(ValueError, expression):
                    export.prepare(source, Path(directory) / "export")

        with tempfile.TemporaryDirectory() as directory:
            source, expected = self.fixture(Path(directory))
            destination = Path(directory) / "export"
            with patch.object(export, "EXPECTED", expected), patch.object(export, "EXPECTED_RECORDS", self.RECORDS):
                export.prepare(source, destination)
                (destination / "review_request.js").unlink()
                with self.assertRaisesRegex(ValueError, "pinned payload mismatch"):
                    export.validate_tree(destination)


if __name__ == "__main__":
    unittest.main()
