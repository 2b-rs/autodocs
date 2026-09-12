"""Pretty-print issue preview pages for local browsing."""

from __future__ import annotations

import importlib.util
import tempfile
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "issue_preview", ROOT / "_src/tools/issue_preview.py")
PREVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREVIEW)
VIEWS = PREVIEW.views
FIXTURES = ROOT / "_src/tests/fixtures/0037-11.02"
ISSUES = FIXTURES / "issues"


class IssuePreviewTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.catalog, _ = VIEWS.render(ISSUES, ROOT)

    def test_preview_path_matching(self):
        self.assertEqual(PREVIEW.match_preview_path("/issues/"), ("index", None))
        self.assertEqual(PREVIEW.match_preview_path("/issues/0037/"), ("item", "0037"))
        self.assertEqual(
            PREVIEW.match_preview_path("/issues/0037/0037-01/"), ("item", "0037-01"))
        self.assertEqual(
            PREVIEW.match_preview_path("/issues/0037/0037-01.01/"),
            ("item", "0037-01.01"))
        self.assertIsNone(PREVIEW.match_preview_path("/issues/0037/index.md"))
        self.assertIsNone(PREVIEW.match_preview_path("/issues/_views/catalog.json"))
        self.assertIsNone(PREVIEW.match_preview_path("/issues/0037/0038-01/"))
        self.assertTrue(PREVIEW.needs_slash_redirect("/issues/0037"))
        self.assertFalse(PREVIEW.needs_slash_redirect("/issues/0037/"))

    def test_feature_page_shows_status_and_children(self):
        page = PREVIEW.render_item(ROOT, "0081", self.catalog, issues_root=ISSUES)
        self.assertIn("0081", page)
        self.assertIn("Fixture feature covering classified graph edges.", page)
        self.assertIn("chip-in_progress", page)
        self.assertIn("In progress", page)
        self.assertIn("0081-01", page)
        self.assertIn("0081-02", page)
        self.assertIn("Blocked", page)
        self.assertIn("0082", page)
        self.assertIn("Generated view — not authority", page)
        self.assertNotIn("<script>", page)

    def test_task_page_links_parent_and_prerequisites(self):
        page = PREVIEW.render_item(ROOT, "0081-01", self.catalog, issues_root=ISSUES)
        self.assertIn('href="/issues/0081/"', page)
        self.assertIn("0081-02", page)
        self.assertIn("Open task with a start-gate prerequisite.", page)
        self.assertIn("AC-001", page)

    def test_closed_archive_is_not_shown_as_completed(self):
        page = PREVIEW.render_item(ROOT, "0082", self.catalog, issues_root=ISSUES)
        self.assertIn("archived-not-accepted", page)
        self.assertIn("Closed · archived-not-accepted", page)
        self.assertNotIn('chip-closed">Closed</span>', page)

    def test_legacy_unverified_children_are_not_shown_as_open_work(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            issues = tmp / "issues"
            feature = issues / "0090"
            task = feature / "0090-01"
            feature.mkdir(parents=True)
            task.mkdir()
            feature.joinpath("index.md").write_text(
                '---\nschema_version: "1.0"\nid: "0090"\nlevel: "feature"\n'
                'state: "closed"\nvisibility: "internal"\norigin:\n'
                '  kind: "migrated-from-legacy-todo"\nauthority: "shadow"\n---\n\n'
                "## Goal\n\nClosed fixture feature.\n\n## Scope\n\nPreview rollup.\n\n"
                "## Acceptance criteria\n\n- **AC-001** Children stay labeled.\n\n"
                "## Definition of Done\n\nPreview distinguishes legacy terminals.\n",
                encoding="utf-8",
            )
            task.joinpath("index.md").write_text(
                '---\nschema_version: "1.0"\nid: "0090-01"\nlevel: "task"\n'
                'parent: "0090"\nstate: "open"\nvisibility: "internal"\nlabels:\n'
                '  - "legacy-terminal-unverified"\norigin:\n'
                '  kind: "migrated-from-legacy-todo"\n'
                '  source: "legacy:DONE.md:1"\nauthority: "shadow"\n---\n\n'
                "## Goal\n\nImported terminal without closure.\n\n## Scope\n\n"
                "Preview must not treat this as current work.\n\n"
                "## Acceptance criteria\n\n- **AC-001** Status is legacy unverified.\n\n"
                "## Definition of Done\n\nLabel is visible on parent and child.\n",
                encoding="utf-8",
            )
            catalog = {
                "schema": "issue-catalog@v1",
                "authority": "generated-view",
                "generation_id": "sha256:" + ("a" * 64),
                "items": [
                    {
                        "id": "0090",
                        "level": "feature",
                        "parent": None,
                        "state": "closed",
                        "lifecycle_status": "closed",
                        "url": "/issues/0090/",
                        "title": "Closed fixture feature.",
                        "prerequisites": [],
                        "criteria": [],
                        "source": {"path": "issues/0090/index.md"},
                    },
                    {
                        "id": "0090-01",
                        "level": "task",
                        "parent": "0090",
                        "state": "open",
                        "lifecycle_status": "open",
                        "url": "/issues/0090/0090-01/",
                        "title": "Imported terminal without closure.",
                        "prerequisites": [],
                        "criteria": [],
                        "source": {"path": "issues/0090/0090-01/index.md"},
                    },
                ],
            }
            page = PREVIEW.render_item(tmp, "0090", catalog, issues_root=issues)
            self.assertIn("Legacy terminal · unverified", page)
            self.assertIn("chip-legacy-unverified", page)
            self.assertIn("<strong>1</strong> legacy unverified", page)
            self.assertIn("DEC-0037-008", page)
            child = PREVIEW.render_item(tmp, "0090-01", catalog, issues_root=issues)
            self.assertIn("Legacy terminal · unverified", child)
            self.assertNotIn('chip-open">Open</span>', child)
            index = PREVIEW.render_index(catalog, issues_root=issues)
            self.assertIn("1 legacy unverified", index)

    def test_index_lists_features(self):
        page = PREVIEW.render_index(self.catalog)
        self.assertIn("0081", page)
        self.assertIn("0082", page)
        self.assertIn("Issues", page)

    def test_html_escapes_untrusted_text(self):
        self.assertIn("&lt;script&gt;", PREVIEW.format_body("<script>alert(1)</script>"))
        self.assertIn("<strong>bold</strong>", PREVIEW.format_inline("**bold**"))
        self.assertIn("<code>id</code>", PREVIEW.format_inline("`id`"))

    def test_markdown_pretty_print(self):
        html = PREVIEW.markdown_to_html(
            "# Title\n\nSee [docs](docs/pipeline/issue-store.md).\n\n"
            "- [ ] open item\n- [x] **done**\n- [p] running\n\n"
            "```python\nprint('<hi>')\n```\n"
        )
        self.assertIn("<h1>Title</h1>", html)
        self.assertIn('href="docs/pipeline/issue-store.md"', html)
        self.assertIn("task-open", html)
        self.assertIn("task-done", html)
        self.assertIn("task-progress", html)
        self.assertIn("<strong>done</strong>", html)
        self.assertIn("&lt;hi&gt;", html)
        self.assertNotIn("<script>", PREVIEW.markdown_to_html("<script>alert(1)</script>"))
        self.assertIn("&lt;script&gt;", PREVIEW.markdown_to_html("<script>alert(1)</script>"))

    def test_markdown_page_keeps_frontmatter(self):
        page = PREVIEW.render_markdown_page(
            "---\nid: \"0081\"\nstate: \"open\"\n---\n\n## Goal\n\nHello `code`.\n",
            url_path="/issues/0081/index.md",
            filename="index.md",
        )
        self.assertIn("Frontmatter", page)
        self.assertIn("id: &quot;0081&quot;", page)
        self.assertIn("<h2>Goal</h2>", page)
        self.assertIn("<code>code</code>", page)
        self.assertIn("?raw=1", page)

    def test_not_found_page(self):
        page = PREVIEW.render_not_found("0099")
        self.assertIn("No issue item at this path.", page)


class IssuePreviewServerTest(unittest.TestCase):
    def setUp(self):
        handler = PREVIEW.IssuePreviewHandler
        handler.repo = ROOT
        handler.directory = str(ROOT)
        handler.preview = PREVIEW.Preview(ROOT)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def _get(self, path: str):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.request("GET", path)
            response = conn.getresponse()
            return response.status, response.getheader("Content-Type"), response.read()
        finally:
            conn.close()

    def test_issue_url_is_html_status_not_listing(self):
        status, content_type, body = self._get("/issues/0037/")
        text = body.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn("0037", text)
        self.assertIn("Git-Native Issue Store", text)
        self.assertNotIn("Directory listing", text)
        self.assertIn("0037-01", text)

    def test_markdown_is_html_not_downloaded(self):
        status, content_type, body = self._get("/issues/0037/index.md")
        text = body.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn("<!DOCTYPE html>", text)
        self.assertIn("Git-Native Issue Store", text)
        self.assertIn("schema_version", text)
        self.assertIn("<h2>Goal</h2>", text)

    def test_raw_markdown_query_is_plain_text(self):
        status, content_type, body = self._get("/issues/0037/index.md?raw=1")
        self.assertEqual(status, 200)
        self.assertIn("text/plain", content_type)
        self.assertIn(b"schema_version:", body)
        self.assertNotIn(b"<!DOCTYPE html>", body)

    def test_missing_item_is_404(self):
        status, _, body = self._get("/issues/9999/")
        self.assertEqual(status, 404)
        self.assertIn(b"No issue item at this path.", body)


if __name__ == "__main__":
    unittest.main()
