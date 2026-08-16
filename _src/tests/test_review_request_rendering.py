import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lib_docmodel as dm


class TestReviewRequestRendering(unittest.TestCase):
    def test_render_blocks_includes_review_request_payload(self):
        blocks = [{
            "t": "rec",
            "attrs": [["class", "rec"], ["id", "AUTOSAR/AP/record/TSyncUserGuide"]],
            "lead": "",
            "status": {"state": "valid/curator-decided", "reason": "confirmed"},
            "review_request": {
                "canonical_id": "AUTOSAR/AP/record/TSyncUserGuide",
                "release": "R25-11",
                "content_text": "Time sync description",
                "source_url": "https://example.invalid/spec.pdf",
                "title": "TSync User Guide"
            },
            "blocks": [{"t": "html", "html": "<p>Content</p>"}]
        }]
        rendered = ''.join(dm.render_blocks(blocks, 1))
        self.assertIn('review-request-panel', rendered)
        self.assertIn('data-review-request-open', rendered)
        self.assertIn('review-request-data', rendered)
        self.assertIn('https://example.invalid/spec.pdf', rendered)
        self.assertIn('valid/curator-decided', rendered)
        self.assertIn('@rel:R25-11#', rendered)

    def test_duplicate_open_request_replaces_trigger(self):
        blocks = [{
            "t": "rec",
            "attrs": [["class", "rec"], ["id", "AUTOSAR/AP/record/TSyncUserGuide"]],
            "lead": "",
            "status": {"state": "valid/curator-decided"},
            "review_request": {
                "canonical_id": "AUTOSAR/AP/record/TSyncUserGuide",
                "has_open_review_request": True,
                "existing_request_url": "https://example.invalid/issues/42"
            },
            "blocks": [{"t": "html", "html": "<p>Content</p>"}]
        }]
        rendered = ''.join(dm.render_blocks(blocks, 1))
        self.assertIn('review-request-duplicate', rendered)
        self.assertNotIn('data-review-request-open', rendered)

    def test_open_queue_item_suppresses_trigger_and_shows_state(self):
        """0021-06: an ingested (queue) review-request item, not just manually
        set has_open_review_request, must suppress the trigger and surface
        queue state/identity/target version -- discovered organically from
        spec/curation-queue/, matching what review_request_ingest.py writes."""
        with tempfile.TemporaryDirectory() as td:
            srcdir = Path(td)
            open_dir = srcdir / "spec" / "curation-queue" / "open"
            open_dir.mkdir(parents=True)
            (open_dir / "req-1.json").write_text(json.dumps({
                "item_kind": "review-request",
                "id": "req-1",
                "identity": "github_authenticated",
                "decided_by": "jdoe",
                "created": "2026-08-15T00:00:00Z",
                "decision_basis": {
                    "target_canonical_id": "AUTOSAR/AP/record/TSyncUserGuide",
                    "target_version_id": "AUTOSAR/AP/record/TSyncUserGuide@rel:R25-11#abc123",
                    "target_status_snapshot": "valid/curator-decided",
                    "authoritative_actor": "jdoe",
                    "request_id": "req-1",
                },
            }), encoding="utf-8")
            dm._REVIEW_REQUEST_INDEX = None
            blocks = [{
                "t": "rec",
                "attrs": [["class", "rec"], ["id", "AUTOSAR/AP/record/TSyncUserGuide"]],
                "lead": "",
                "status": {"state": "valid/curator-decided"},
                "review_request": {"canonical_id": "AUTOSAR/AP/record/TSyncUserGuide"},
                "blocks": [{"t": "html", "html": "<p>Content</p>"}]
            }]
            rendered = ''.join(dm.render_blocks(blocks, 1, srcdir=str(srcdir)))
            dm._REVIEW_REQUEST_INDEX = None
        self.assertIn('review-request-duplicate', rendered)
        self.assertNotIn('data-review-request-open', rendered)
        self.assertIn('req-1', rendered)
        self.assertIn('github_authenticated', rendered)
        self.assertIn('jdoe', rendered)
        self.assertIn('R25-11', rendered)

    def test_no_queue_item_still_allows_trigger(self):
        """0021-06 regression guard: absence of any queue file must not
        spuriously suppress the trigger (empty-queue-dir edge case)."""
        with tempfile.TemporaryDirectory() as td:
            srcdir = Path(td)
            (srcdir / "spec" / "curation-queue" / "open").mkdir(parents=True)
            dm._REVIEW_REQUEST_INDEX = None
            blocks = [{
                "t": "rec",
                "attrs": [["class", "rec"], ["id", "AUTOSAR/AP/record/OtherRecord"]],
                "lead": "",
                "status": {"state": "valid/curator-decided"},
                "review_request": {"canonical_id": "AUTOSAR/AP/record/OtherRecord"},
                "blocks": [{"t": "html", "html": "<p>Content</p>"}]
            }]
            rendered = ''.join(dm.render_blocks(blocks, 1, srcdir=str(srcdir)))
            dm._REVIEW_REQUEST_INDEX = None
        self.assertIn('data-review-request-open', rendered)
        self.assertNotIn('review-request-duplicate', rendered)

    def test_render_page_includes_review_request_js(self):
        _ROOT = Path(__file__).resolve().parents[2]
        page_tmpl = (_ROOT / '_src' / 'templates' / 'page.html.tmpl').read_text(encoding='utf-8')
        page = {
            'title': 'Test', 'file': 'test.html', 'body_class': '', 'nav_html': '',
            'main_lead': '', 'footer': 'default',
            'main': [{
                't': 'rec', 'attrs': [['class', 'rec'], ['id', 'AUTOSAR/AP/record/TSyncUserGuide']],
                'status': {'state': 'valid/auto-approved'},
                'review_request': {'canonical_id': 'AUTOSAR/AP/record/TSyncUserGuide'},
                'blocks': [{'t': 'html', 'html': '<p>Content</p>'}]
            }]
        }
        html = dm.render_page(page, {'default': ''}, page_tmpl)
        self.assertIn('review_request.js', html)

if __name__ == '__main__':
    unittest.main()
