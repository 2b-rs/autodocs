import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(SRC / "tools"), str(SRC)]
from validate_page_i18n import check_family, page_texts


class ValidatePageI18nTests(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory(); root = Path(temp.name)
        page = {"i18n_complete": True, "title": "Hallo Welt", "main": [{"t":"html", "html":"<h1 id='title'>Hallo Welt</h1><div id='flow' aria-label='Ablauf'><svg><text>Start</text></svg><p>Deutsch fallback</p></div>"}]}
        (root / "source.json").write_text(json.dumps(page), encoding="utf-8")
        (root / "i18n").mkdir(); segments, labels = page_texts(page)
        (root / "i18n/segments.de.json").write_text(json.dumps({key:{} for key in segments}), encoding="utf-8")
        (root / "i18n/labels.de.json").write_text(json.dumps({key:1 for key in labels}), encoding="utf-8")
        german = "<html><body><h1 id='title'>Hallo Welt</h1><div id='flow' aria-label='Ablauf'><svg><text>Start</text></svg><p>Deutsch fallback</p></div></body></html>"
        localized = "<html><body><h1 id='title'>Hello world</h1><div id='flow' aria-label='Flow'><svg><text>Start</text></svg><p>Translated</p></div></body></html>"
        (root / "page.html").write_text(german, encoding="utf-8"); (root / "en").mkdir(); (root / "en/page.html").write_text(localized, encoding="utf-8")
        family = {"id":"fixture", "status":"active", "source":"source.json", "register_root":"i18n", "page":"page.html", "locales":["en"], "fallback_markers":["Deutsch fallback"], "protected_terms":["Start"]}
        return temp, root, family

    def test_positive_and_protected_identifier(self):
        temp, root, family = self.fixture()
        with temp: self.assertEqual(check_family(root, family), [])

    def test_missing_extraction(self):
        temp, root, family = self.fixture()
        with temp:
            (root / "i18n/segments.de.json").write_text("{}", encoding="utf-8")
            self.assertIn("missing-extraction", [item["code"] for item in check_family(root, family)])

    def test_fallback_anchor_aria_svg_and_stale_output(self):
        temp, root, family = self.fixture()
        with temp:
            bad = "<html><body><h1 id='changed'>Hello</h1><div><svg></svg><p>Deutsch fallback</p></div></body></html>"
            (root / "en/page.html").write_text(bad, encoding="utf-8")
            codes = {item["code"] for item in check_family(root, family)}
            self.assertTrue({"anchor-mismatch", "aria-coverage", "inline-svg-coverage", "fallback-or-leak"} <= codes)
            (root / "en/page.html").unlink()
            self.assertIn("missing-rendered-output", {item["code"] for item in check_family(root, family)})

    def test_retired_family_is_not_checked(self):
        temp, root, family = self.fixture()
        with temp:
            family["status"] = "retired"; (root / "en/page.html").unlink()
            self.assertEqual(check_family(root, family), [])


if __name__ == "__main__":
    unittest.main()
