import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lib_docmodel as dm


class TestReviewRequestBrowser(unittest.TestCase):
    def test_browser_flow_exported_not_submitted(self):
        _ROOT = Path(__file__).resolve().parents[2]
        page_tmpl = (_ROOT / '_src' / 'templates' / 'page.html.tmpl').read_text(encoding='utf-8')
        footers = {'default': ''}
        page = {
            'title': 'Review Request Test',
            'file': 'tests/review-request.html',
            'body_class': '', 'nav_html': '', 'main_lead': '', 'footer': 'default',
            'main': [{
                't': 'rec',
                'attrs': [['class', 'rec'], ['id', 'AUTOSAR/AP/record/TSyncUserGuide']],
                'status': {'state': 'valid/curator-decided', 'reason': 'confirmed'},
                'review_request': {
                    'canonical_id': 'AUTOSAR/AP/record/TSyncUserGuide',
                    'release': 'R25-11',
                    'content_text': 'Time sync description',
                    'source_url': 'https://example.invalid/spec.pdf',
                    'title': 'TSync User Guide'
                },
                'blocks': [{'t': 'html', 'html': '<p>Content</p>'}]
            }]
        }
        html = dm.render_page(page, footers, page_tmpl)

        workspace_tmp_root = (_ROOT / 'output' / '_review_request_test_tmp')
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(workspace_tmp_root)) as td:
            td = Path(td)
            (td / 'tests').mkdir(exist_ok=True)
            (td / 'review.js').write_text((_ROOT / 'review.js').read_text(encoding='utf-8'), encoding='utf-8')
            (td / 'review_request.js').write_text((_ROOT / 'review_request.js').read_text(encoding='utf-8'), encoding='utf-8')
            (td / 'fold.js').write_text((_ROOT / 'fold.js').read_text(encoding='utf-8'), encoding='utf-8')
            (td / 'cytoscape.min.js').write_text('', encoding='utf-8')
            (td / 'component-graph.js').write_text('', encoding='utf-8')
            (td / 'style.css').write_text((_ROOT / 'style.css').read_text(encoding='utf-8'), encoding='utf-8')
            target = td / 'tests' / 'review-request.html'
            target.write_text(html, encoding='utf-8')

            env = dict(os.environ)
            candidate_node_paths = [
                '/tmp/autodocs/output/npm-prefix/node_modules',
                '/Users/tobias.anton/devel/autodocs/output/npm-prefix/node_modules',
                '/Users/tobias.anton/devel/autodocs/node_modules',
                str(_ROOT / 'node_modules'),
            ]
            valid_paths = [p for p in candidate_node_paths if os.path.isdir(p)]
            if valid_paths:
                env['NODE_PATH'] = os.pathsep.join(valid_paths) + os.pathsep + env.get('NODE_PATH', '')
            proc = subprocess.run(
                ['node', str((_ROOT / '_src' / 'tools' / 'check_review_request_ui.cjs').resolve()), str(target.resolve())],
                capture_output=True, text=True, cwd=str(_ROOT), timeout=30, env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)
            self.assertIn('missing-context', result['confirmText'])
            self.assertIn('Downloaded — not yet submitted.', result['stateText'])
            self.assertEqual(result['payload']['canonical_id'], 'AUTOSAR/AP/record/TSyncUserGuide')
            self.assertEqual(result['payload']['status'], 'valid/curator-decided')
            self.assertEqual(result['payload']['source_url'], 'https://example.invalid/spec.pdf')
            self.assertIn('QA Reviewer', result['confirmText'])

if __name__ == '__main__':
    unittest.main()
