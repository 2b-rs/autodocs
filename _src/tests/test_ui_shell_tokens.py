#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify the 6-domain shell and design-token contract (F-B).

Baseline (red): git object 29aeadfbd34c84d7f02951f33b4383217c046330
Candidate: working tree sources rendered through generate.py / render_page.
"""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
ROOT = SRC.parent
sys.path.insert(0, str(SRC / "tools"))
sys.path.insert(0, str(SRC))

import generate  # pyright: ignore[reportImplicitRelativeImport]
import lib_docmodel as dm
from report_page_header import (  # pyright: ignore[reportImplicitRelativeImport]
    mark_report_shell_chrome,
    report_page_header,
    rewrite_hex_report_css,
    tokenize_report_markup,
)

REPORT_PAGES = (
    "extraction-reports.html",
    "curation-report.html",
    "build-reports.html",
    "open-reviews.html",
)

PRECHANGE_REF = "29aeadfbd34c84d7f02951f33b4383217c046330"
DOMAINS = ("extract", "build", "curate", "review", "trace", "explore", "work")
REQUIRED_TOKENS = (
    "--bg-canvas",
    "--bg-surface",
    "--bg-subtle",
    "--border-default",
    "--font-sans",
    "--font-mono",
    "--color-teal-600",
    "--color-teal-700",
    "--status-approved",
    "--status-candidate",
    "--status-rejected",
    "--status-trace",
)
CONTROLS = (
    'data-universe="autosar-adaptive"',
    'data-universe="eclipse-score"',
    'data-search-input',
    'data-theme-toggle',
    'data-density-toggle',
    'class="langs"',
)
MINIMAL_PAGE = {
    "title": "Shell fixture",
    "file": "process.html",
    "body_class": "",
    "nav_html": "Start",
    "main_lead": "",
    "footer": "extracted",
    "main": [{"t": "html", "html": "<h1>Fixture</h1>"}],
}


def git_show(path: str, ref: str = PRECHANGE_REF) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "%s:%s" % (ref, path)],
        text=True,
    )


def css_bundle() -> str:
    tokens = (SRC / "static" / "tokens.css").read_text(encoding="utf-8")
    style = (ROOT / "style.css").read_text(encoding="utf-8")
    return tokens + "\n" + style


def render_generate(page_file: str = "process.html") -> str:
    page_tmpl, footers = dm.load_templates()
    pages = [page for page in dm.iter_pages({page_file}) if page["file"] == page_file]
    if not pages:
        raise AssertionError("generate.py fixture page missing: %s" % page_file)
    _name, html_text, errs = generate._render_one((pages[0], footers, page_tmpl, False))
    if errs:
        raise AssertionError(errs)
    return generate.publication_links(html_text)


class TestUiShellTokens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = render_generate("process.html")
        cls.css = css_bundle()
        cls.baseline_tmpl = git_show("_src/templates/page.html.tmpl")
        cls.baseline_css = git_show("style.css")

    def test_generate_html_includes_six_domain_navigation(self):
        html = self.generated
        self.assertIn('class="shell"', html)
        self.assertIn('aria-label="Application domains"', html)
        for domain in DOMAINS:
            with self.subTest(domain=domain):
                self.assertIn('data-domain="%s"' % domain, html)
                self.assertIn(">%s<" % domain.capitalize(), html)

    def test_generate_html_includes_header_controls(self):
        html = self.generated
        for token in CONTROLS:
            with self.subTest(token=token):
                self.assertIn(token, html)
        self.assertIn('data-theme="light"', html)
        self.assertIn('data-density="comfortable"', html)
        self.assertIn('class="skip-link"', html)
        self.assertIn('id="main"', html)
        self.assertIn("index.html", html)
        self.assertIn("eclipse-score-v0.6.0-curation-review", html)

    def test_css_contains_required_tokens_dark_mode_and_media_queries(self):
        css = self.css
        for token in REQUIRED_TOKENS:
            with self.subTest(token=token):
                self.assertIn(token, css)
        self.assertIn('[data-theme="dark"]', css)
        self.assertIn('[data-density="compact"]', css)
        self.assertIn(":focus-visible", css)
        self.assertIn("Satoshi", css)
        self.assertIn("ui-monospace", css)
        self.assertRegex(css, r"@media\s*\(\s*max-width:\s*767px\s*\)")
        self.assertRegex(css, r"@media\s*\(\s*max-width:\s*320px\s*\)")
        self.assertRegex(css, r"@media\s*\(\s*max-width:\s*1279px\s*\)")

    def test_six_domain_nav_red_on_baseline_green_on_candidate(self):
        """AE-3: pre-change chrome has no domain nav; generate.py output does."""
        for domain in DOMAINS:
            with self.subTest(domain=domain):
                self.assertNotIn('data-domain="%s"' % domain, self.baseline_tmpl)
                self.assertIn('data-domain="%s"' % domain, self.generated)
        self.assertNotIn("--bg-canvas", self.baseline_css)
        self.assertIn("--bg-canvas", self.css)
        self.assertNotIn('[data-theme="dark"]', self.baseline_css)
        self.assertIn('[data-theme="dark"]', self.css)

    def test_nested_page_keeps_language_tree_explore_and_root_reports(self):
        """Adjacent: class page must climb to catalog but leave nolang reports at root."""
        page = dict(MINIMAL_PAGE)
        page["file"] = "classes/cl_fixture.html"
        page_tmpl, footers = dm.load_templates()
        de_html = dm.render_page(page, footers, page_tmpl, lang="de")
        en_html = dm.render_page(page, footers, page_tmpl, lang="en")
        self.assertIn('data-domain="explore" href="../index.html"', de_html)
        self.assertIn('data-domain="build" href="../build-reports.html"', de_html)
        self.assertIn('data-domain="explore" href="../index.html"', en_html)
        self.assertIn('data-domain="build" href="../../build-reports.html"', en_html)
        self.assertIn('data-domain="curate" href="../../curation-report.html"', en_html)

    def test_compact_density_reduces_shell_padding_tokens(self):
        """Adjacent: compact mode is a distinct density contract, not just dark."""
        css = self.css
        dark_idx = css.index('[data-theme="dark"]')
        compact_idx = css.index('[data-density="compact"]')
        compact_block = css[compact_idx:compact_idx + 400]
        self.assertIn("--shell-pad-block: 6px", compact_block)
        self.assertIn("--font-size-ui: 14px", compact_block)
        self.assertNotEqual(dark_idx, compact_idx)
        self.assertIn("overflow-x: hidden", css)

    def test_report_header_uses_token_fallbacks_not_hex(self):
        """Report landscape chrome must consume tokens.css variables."""
        baseline = git_show("_src/tools/report_page_header.py")
        header = report_page_header(
            generator="tool.py",
            data_source="records.json",
            purpose="Explains the report.",
            generated_at="2026-08-21T09:07:00Z",
        )
        self.assertIn("#f7f8ff", baseline)
        self.assertIn("#d9dce3", baseline)
        self.assertNotIn("#f7f8ff", header)
        self.assertNotIn("#d9dce3", header)
        self.assertIn("var(--bg-card, var(--bg-surface))", header)
        self.assertIn("var(--border-subtle, var(--border-default))", header)
        self.assertIn("var(--text-primary, var(--color-ink))", header)
        self.assertIn("var(--text-secondary, var(--color-ink-muted))", header)
        self.assertIn('[data-density="compact"]', header)

    def test_hex_rewrite_and_adjacent_domain_chrome(self):
        """AE-3/AE-4: hex CSS is rewritten; Curate vs Reports mark different domains."""
        sample = (
            ".tr-head{border:1px solid #d9dce3;background:linear-gradient(135deg,#f7f8ff,#eef5ff)}"
            ".tr-grid article{background:#fff;color:#596274}"
        )
        rewritten = rewrite_hex_report_css(sample)
        self.assertNotIn("#d9dce3", rewritten)
        self.assertNotIn("#fff", rewritten)
        self.assertIn("var(--bg-card, var(--bg-surface))", rewritten)
        self.assertIn("var(--text-secondary, var(--color-ink-muted))", rewritten)
        compact = tokenize_report_markup(sample + "</style>")
        self.assertIn('[data-density="compact"] .tr-table th', compact)
        fixture = (
            '<nav class="shell-universe"><a data-universe="eclipse-score" href="x">S-Core</a></nav>'
            '<button type="button" class="shell-toggle" data-theme-toggle>Light</button>'
            '<nav class="shell-domains">'
            '<a data-domain="curate" href="curation-report.html">Curate</a>'
            '<a data-domain="reports" href="build-reports.html">Reports</a>'
            "</nav>"
        )
        curate = mark_report_shell_chrome(fixture, "curation-report.html")
        reports = mark_report_shell_chrome(fixture, "extraction-reports.html")
        self.assertIn('data-domain="curate" aria-current="page"', curate)
        self.assertNotIn('data-domain="reports" aria-current="page"', curate)
        self.assertIn('data-domain="reports" aria-current="page"', reports)
        self.assertIn('class="langs"', curate)
        self.assertIn(">Adaptive<", curate)
        self.assertIn(">Classic<", curate)
        self.assertIn(">S-Core<", curate)

    def test_published_report_pages_carry_shell_toggles(self):
        """Live report HTML must expose the 6-domain shell contract."""
        for name in REPORT_PAGES:
            path = ROOT / name
            with self.subTest(page=name):
                self.assertTrue(path.is_file(), "missing %s" % name)
                html = path.read_text(encoding="utf-8")
                self.assertIn('class="shell"', html)
                self.assertIn("data-theme-toggle", html)
                self.assertIn("data-density-toggle", html)
                self.assertIn("data-feedback-open", html)
                self.assertIn('class="skip-link"', html)
                self.assertIn('id="main"', html)
                self.assertIn("var(--bg-card, var(--bg-surface))", html)
                self.assertIn("var(--border-subtle, var(--border-default))", html)


if __name__ == "__main__":
    unittest.main()
