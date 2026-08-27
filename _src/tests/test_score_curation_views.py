import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_src" / "tools"))
import score_curation_views as views


class ScoreCurationViewsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        corpus, report, queue = views.reproduce()
        cls.model = views.view_model(corpus, report, queue)
        cls.files = views.render(cls.model)

    def test_pinned_corpus_generates_every_candidate_page(self):
        self.assertEqual(2239, self.model["counts"]["records"])
        self.assertEqual(2239, self.model["counts"]["candidate_pages"])
        self.assertEqual({"invalid/to-be-confirmed": 2239}, self.model["counts"]["by_status"])
        record_pages = [name for name in self.files if name.startswith("records/") and name.endswith(".html")]
        self.assertEqual(2240, len(record_pages))  # listing plus every individual candidate
        self.assertEqual(2239, len([name for name in record_pages if name != "records/index.html"]))
        self.assertEqual("bd6e23ae7454e7dee4daba98a104fa76db0ef9cdf54713ef35569a6c992ef0e2", views.sha256(self.files["review_request.js"]))
        self.assertEqual("7fa99621f52bac786f6793024eda694f0d54454cd8715bc346292c6c5d0d133c", views.sha256(self.files["style.css"]))
        self.assertNotIn("assets/view.css", self.files)
        self.assertIn(b'id="flag-for-review-protocol"', self.files["process.html"])
        self.assertIn(b'id="storage-and-privacy"', self.files["process.html"])
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "view"
            views.write_tree(output, self.files)
            views.validate_tree(output, self.files, client=False)
            self.assertEqual(2239, len([path for path in (output / "records").glob("*.html") if path.name != "index.html"]))

    def test_unmanaged_provenance_receipt_is_rejected_from_generated_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "view"
            views.write_tree(output, self.files)
            (output / "integration-provenance-unmanaged.md").write_text("receipt", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "generated tree differs from deterministic expected output"):
                views.validate_tree(output, self.files, client=False)


    def test_no_javascript_marker_and_review_route_cover_every_candidate(self):
        pages = [payload.decode("utf-8") for name, payload in self.files.items() if name.startswith("records/") and name != "records/index.html"]
        self.assertEqual(2239, len(pages))
        for page in pages:
            self.assertIn(views.UNVALIDATED_MARKER, page)
            self.assertIn('data-validation-state="unvalidated"', page)
            self.assertIn('id="source-derived-content"', page)
            self.assertIn("Source-derived candidate content — unvalidated", page)
            self.assertIn('data-curation-route="review-request"', page)
            self.assertIn("review_request.js", page)
            self.assertNotIn('data-validation-state="valid"', page)
            self.assertNotIn('data-validation-state="accepted"', page)

    def test_omitted_or_misleading_marker_is_rejected(self):
        altered = dict(self.files)
        candidate = next(name for name in altered if name.startswith("records/") and name.endswith(".html") and name != "records/index.html")
        altered[candidate] = altered[candidate].replace(views.UNVALIDATED_MARKER.encode("utf-8"), b"VALIDATED CANDIDATE").replace(b'data-unvalidated-marker="awaiting-curator-confirmation"', b'data-validation-state="valid"')
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "view"
            views.write_tree(output, altered)
            with self.assertRaisesRegex(ValueError, "candidate marker missing"):
                views.validate_tree(output, altered, client=False)


    def test_source_derived_content_is_complete_and_safely_escaped(self):
        source_by_page = {record["page"]: record["source_derived_content"] for record in self.model["records"]}
        self.assertEqual(2239, len(source_by_page))
        for page, content in source_by_page.items():
            rendered = self.files[page].decode("utf-8")
            self.assertIn("Source-derived candidate content — unvalidated", rendered)
            self.assertIn(views.html.escape("\n".join(line.rstrip() for line in content.splitlines())), rendered)
        candidate = self.model["records"][0]
        unsafe = dict(candidate, source_derived_content='<script>alert("unsafe")</script>')
        rendered = views.render_record(unsafe).decode("utf-8")
        self.assertIn("&lt;script&gt;alert(&quot;unsafe&quot;)&lt;/script&gt;", rendered)
        self.assertNotIn('<script>alert("unsafe")</script>', rendered)

    def test_omitted_source_derived_content_is_rejected(self):
        altered = dict(self.files)
        candidate = next(name for name in altered if name.startswith("records/") and name.endswith(".html") and name != "records/index.html")
        altered[candidate] = altered[candidate].replace(b'<section id="source-derived-content"', b'<section id="removed-source-derived-content"', 1)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "view"
            views.write_tree(output, altered)
            with self.assertRaisesRegex(ValueError, "candidate source-derived content missing"):
                views.validate_tree(output, altered, client=False)

    def test_collision_and_manifest_remain_traceable(self):
        unresolved = self.model["unresolved"]
        self.assertEqual("invalid/to-be-confirmed", unresolved["status"])
        self.assertEqual(1, sum(1 for record in self.model["records"] if record["unresolved_collision"]))
        evidence = json.loads(self.files["evidence.json"])
        self.assertEqual(2239, len(evidence["candidate_manifest"]))
        self.assertEqual(self.model["candidate_manifest_sha256"], evidence["candidate_manifest_sha256"])


if __name__ == "__main__":
    unittest.main()
