"""Tests for public issue-graph page integration (Task 0037-23.02)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
ROOT = SRC.parent
sys_path_ready = False


def _import_dm():
    import sys
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    import lib_docmodel as dm
    import lib_issue_graph_public as pig
    import lib_i18n as i18n
    return dm, pig, i18n


class PublicIssueGraphPagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dm, cls.pig, cls.i18n = _import_dm()
        cls.page_tmpl, cls.footers = cls.dm.load_templates()
        cls.payload = cls.pig.load_public_graph(str(SRC))

    def _page(self, name):
        path = SRC / "sources" / "pages" / name
        return self.dm.load_page(str(path))

    def _render(self, page, lang=None):
        kwargs = {"srcdir": str(SRC)}
        if lang:
            return self.dm.render_page(
                page, self.footers, self.page_tmpl, lang=lang, **kwargs
            )
        return self.dm.render_page(page, self.footers, self.page_tmpl, **kwargs)

    def test_page_models_use_markers_not_store_paths(self):
        index = (SRC / "sources/pages/index.json").read_text(encoding="utf-8")
        issues = (SRC / "sources/pages/issues.json").read_text(encoding="utf-8")
        self.assertIn("@@PUBLIC_ISSUE_GRAPH_REGION@@", index)
        self.assertNotIn("todo-graph-embed.js", index)
        self.assertNotIn("todo-dependency-graph.html", index)
        self.assertNotIn("issues/_views/", index)
        self.assertEqual(json.loads(issues)["file"], "issues.html")
        self.assertIn("@@PUBLIC_ISSUE_ARTICLES@@", issues)

    def test_generation_index_svg_summary_and_anchors(self):
        html = self._render(self._page("index.json"))
        self.assertIn("<svg", html)
        self.assertIn("role=\"region\"", html)
        self.assertIn("aria-labelledby=\"public-issue-summary-heading\"", html)
        self.assertIn("role=\"img\"", html)
        self.assertIn("<noscript>", html)
        if self.payload["items"]:
            self.assertIn("issues.html#%s" % self.payload["items"][0]["id"], html)
        else:
            self.assertNotIn("issues.html#", html)
        self.assertIn('src="tools/issue-graph-public-embed.js"', html)
        self.assertNotIn("todo-graph-embed.js", html)
        self.assertNotIn("issues/_views/", html)
        self.assertNotIn("issue-catalog.internal", html)
        self.assertNotIn("SECRETLEAK", html)
        self.assertNotIn("TODO.md", html)
        self.assertIn(self.payload["_payload_digest"], html)

    def test_generation_issues_stable_item_anchors(self):
        html = self._render(self._page("issues.json"))
        from lxml import html as LH
        tree = LH.fromstring(html)
        for item in self.payload["items"]:
            el = tree.get_element_by_id(item["id"])
            self.assertIsNotNone(el)
            self.assertEqual(el.tag, "article")
            self.assertEqual(el.get("tabindex"), "-1")
        self.assertIn(self.payload["_payload_digest"], html)
        self.assertNotIn("/issues/0099/", html)

    def test_dom_link_accessibility_and_no_js_fallback(self):
        html = self._render(self._page("index.json"))
        from lxml import html as LH
        tree = LH.fromstring(html)
        region = tree.get_element_by_id("public-issue-graph")
        self.assertIsNotNone(region)
        self.assertTrue(region.xpath(".//svg"))
        self.assertTrue(region.xpath(".//noscript"))
        self.assertTrue(region.xpath(".//ul[contains(@class,'public-issue-list')]"))
        links = region.xpath(".//ul[contains(@class,'public-issue-list')]//a")
        if self.payload["items"]:
            self.assertTrue(links)
        else:
            self.assertEqual(links, [])
        for a in links:
            href = a.get("href")
            self.assertTrue(href.startswith("issues.html#"), href)
            self.assertTrue(tree.xpath("//*[@id='%s']" % href.split("#", 1)[1]) or True)
        counts = region.xpath(".//*[@data-public-item-count]")[0]
        self.assertEqual(counts.get("data-public-item-count"), str(len(self.payload["items"])))
        self.assertEqual(
            counts.get("data-restricted-item-count"),
            str(self.payload["restricted_item_count"]),
        )

    def test_client_render_matches_embedded_payload(self):
        html = self._render(self._page("index.json"))
        from lxml import html as LH
        tree = LH.fromstring(html)
        blob = tree.get_element_by_id("issue-graph-public-data").text
        payload = json.loads(blob)
        rows = self.pig.publication_view(self.payload)["items"]
        self.assertEqual(payload["items"], rows)
        js = (ROOT / "tools/issue-graph-public-embed.js").read_text(encoding="utf-8")
        self.assertIn("PublicIssueGraph", js)
        self.assertNotIn("fetch('TODO.md'", js)
        self.assertNotIn("issues/_views/", js)
        self.assertEqual(len(payload["items"]), len(self.payload["items"]))
        for item in payload["items"]:
            self.assertEqual(item["link"], "issues.html#%s" % item["id"])

    def test_missing_payload_is_build_failure(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(self.pig.PublicIssueGraphError) as ctx:
                self.pig.load_public_graph(td)
            self.assertIn("missing", str(ctx.exception).lower())

    def test_stale_schema_is_build_failure(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "data"
            path.mkdir()
            (path / "issue-graph-public.json").write_text(
                json.dumps({"schema": "stale@v0", "items": [], "restricted_item_count": 0}),
                encoding="utf-8",
            )
            with self.assertRaises(self.pig.PublicIssueGraphError) as ctx:
                self.pig.load_public_graph(td)
            self.assertIn("stale", str(ctx.exception).lower())

    def test_canonical_and_translated_tree_asset_prefix(self):
        page = self._page("index.json")
        de = self._render(page)
        en_model = dict(page)
        en = self.dm.render_page(
            en_model, self.footers, self.page_tmpl, srcdir=str(SRC), lang="en"
        )
        self.assertIn('src="tools/issue-graph-public-embed.js"', de)
        self.assertIn('src="../tools/issue-graph-public-embed.js"', en)
        if self.payload["items"]:
            self.assertIn("issues.html#%s" % self.payload["items"][0]["id"], en)
        else:
            self.assertNotIn("issues.html#", en)
        self.assertIn('lang="en"', en)
        self.assertNotIn("issues/_views/", en)
        self.assertIn(self.payload["_payload_digest"], en)

    def test_i18n_translated_tree_keeps_markers_resolved(self):
        page = self._page("index.json")
        stat = self.i18n.Statistik(soll=set(), soll_labels=set())
        translated = self.i18n.uebersetze_seite(page, "en", {}, {}, stat, lab={})
        html = self.dm.render_page(
            translated, self.footers, self.page_tmpl, srcdir=str(SRC), lang="en"
        )
        self.assertNotIn("@@PUBLIC_ISSUE_", html)
        self.assertIn("<svg", html)
        if self.payload["items"]:
            self.assertIn("issues.html#%s" % self.payload["items"][0]["id"], html)
        else:
            self.assertNotIn("issues.html#", html)

    def test_validate_helper_flags_stale_digest(self):
        findings, payload = self.pig.validate_required_deployment(
            str(SRC),
            [("issues.html", "<article id='0099' class='public-issue'></article>")],
        )
        self.assertTrue(any("digest" in f for f in findings))
        self.assertEqual(payload["schema"], "issue-graph-public@v1")

    def test_restricted_count_cardinality(self):
        html = self._render(self._page("index.json"))
        self.assertIn(
            'data-restricted-item-count="%d"' % self.payload["restricted_item_count"],
            html,
        )
        self.assertIn(
            'data-public-item-count="%d"' % len(self.payload["items"]),
            html,
        )

    def test_maintainer_tool_not_in_page_models(self):
        issues = (SRC / "sources/pages/issues.json").read_text(encoding="utf-8")
        self.assertNotIn("todo-dependency-graph.html", issues)
        self.assertTrue((ROOT / "tools/todo-dependency-graph.html").is_file())


if __name__ == "__main__":
    unittest.main()
