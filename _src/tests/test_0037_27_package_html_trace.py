"""Package-level HTML→issue/trigger/source/run trace across 0037-27 families.

Adversarial completion evidence (DEC-0038-004):
- AE-2 baselines: pre-change `7076df3b1bb8d97bc7f3534e66cffee86c4a971b` (0037-27.05
  tip; package adapter absent); candidate this working tree.
- AE-3 falsification: `html_family_trace.assemble_cross_family` is missing on
  the baseline (git cat-file red) and green here, producing reverse HTML traces
  to each producer run/issue.
- AE-4 adjacent: (1) generated HTML/SVG contain no provenance markers;
  (2) a second live HTML generate without invalidation remains HTP-MIXED-RUN.
- AE-5: identity over the five families; each assemble yields exactly those
  five named family keys with run_id and issue.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "7076df3b1bb8d97bc7f3534e66cffee86c4a971b"
COMMIT = "c" * 40
COMMIT_TOOL = "d" * 40
COMMIT_CFG = "e" * 40
ADAPTER = ROOT / "_src" / "tools" / "html_family_trace.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


trace = _load("html_family_trace", ADAPTER)
htp = _load("html_tree_provenance", ROOT / "_src" / "tools" / "html_tree_provenance.py")

PC = ROOT / "_src" / "tests" / "fixtures" / "page_composition"
DG = ROOT / "_src" / "tests" / "fixtures" / "diagram_provenance"
I18N = ROOT / "_src" / "tests" / "fixtures" / "0037-27.04"
HTML = ROOT / "_src" / "tests" / "fixtures" / "html_tree_provenance"


class PackageHtmlFamilyTraceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "_src" / "tools").mkdir(parents=True)
        (self.root / "provenance" / "_schema").mkdir(parents=True)
        for name in (
            "provenance_store.py",
            "provenance_views.py",
            "provenance_query.py",
            "version_id.py",
            "typed_claim.py",
            "ai_workflow_persist.py",
            "diagram_provenance.py",
            "page_composition_provenance.py",
            "i18n_translation_provenance.py",
            "html_tree_provenance.py",
            "html_family_trace.py",
        ):
            shutil.copy(ROOT / "_src" / "tools" / name, self.root / "_src" / "tools" / name)
        for schema in (
            "provenance-graph-v1.schema.json",
            "provenance-reverse-v1.schema.json",
        ):
            shutil.copy(
                ROOT / "provenance" / "_schema" / schema,
                self.root / "provenance" / "_schema" / schema,
            )

    def tearDown(self):
        self.tmp.cleanup()

    def _assemble(self):
        segments_de = json.loads((I18N / "segments.de.json").read_text(encoding="utf-8"))
        segments_en = json.loads((I18N / "segments.en.json").read_text(encoding="utf-8"))
        return trace.assemble_cross_family(
            self.root,
            source_commit=COMMIT,
            tool_commit=COMMIT_TOOL,
            config_commit=COMMIT_CFG,
            fragment_bytes=(PC / "fragment.json").read_bytes(),
            records_bytes=(PC / "records.json").read_bytes(),
            evidence_bytes=(PC / "evidence.json").read_bytes(),
            instructions_bytes=(PC / "instructions.txt").read_bytes(),
            policy_bytes=(PC / "policy.json").read_bytes(),
            config_bytes=(PC / "config.json").read_bytes(),
            composed_bytes=(PC / "composed.json").read_bytes(),
            template_bytes=(HTML / "template.html").read_bytes(),
            source_dot=(DG / "source.dot").read_bytes(),
            svg_text=(DG / "canonical.svg").read_text(encoding="utf-8"),
            labels_bytes=(DG / "en.labels.json").read_bytes(),
            segment_source=segments_de["seg-prose-01"]["m"],
            segment_translation=segments_en["seg-prose-01"],
        )

    def test_traces_html_to_issue_trigger_source_and_producer_run(self):
        report = self._assemble()
        self.assertEqual(report["missing_html_roles"], [])
        self.assertEqual(set(report["families"]), set(trace.FAMILIES))
        self.assertTrue(report["reverse"]["html"]["found"])
        self.assertTrue(report["forward"]["html_issue"]["found"])
        self.assertTrue(report["reverse"]["claim"]["found"])
        self.assertEqual(report["reverse"]["claim"]["run_id"], report["families"]["ai"]["run_id"])
        self.assertEqual(report["reverse"]["i18n"]["run_id"], report["families"]["i18n"]["run_id"])
        self.assertEqual(report["reverse"]["i18n"]["source_id"], "seg-prose-01")
        self.assertTrue(report["forward"]["diagram_issue"]["found"])
        html_path = self.root / report["html_path"]
        self.assertTrue(html_path.is_file())
        htp.assert_html_without_provenance(html_path.read_text(encoding="utf-8"))
        for family, rec in report["families"].items():
            self.assertTrue(rec["run_id"], msg=family)
            self.assertTrue(rec["issue"], msg=family)
            self.assertTrue(rec["source_versions"], msg=family)
        self.assertEqual(report["issue"], "0037-27")
        self.assertEqual(report["criterion"], "DoD-html-family-trace")
        self.assertEqual(report["source_commit"], COMMIT)
        envelope = self.root / "provenance" / "html-family-trace.json"
        self.assertTrue(envelope.is_file())

    def test_second_live_html_generate_is_mixed_run(self):
        report = self._assemble()
        wf = htp.HtmlTreeWorkflow(self.root, clock=lambda: trace.STAMP)
        with self.assertRaises(htp.HtmlTreeProvenanceError) as ctx:
            wf.generate_language_tree(
                language="en",
                page_model_path="_src/sources/pages/guide.json",
                page_model_bytes=(PC / "composed.json").read_bytes(),
                template_path="_src/templates/page.html",
                template_bytes=(HTML / "template.html").read_bytes(),
                ai_path="_src/content/ai/guide-claim.html",
                ai_bytes=b"<p>x</p>",
                diagram_path="_src/diagrams/demo/svg_01.svg",
                diagram_bytes=(DG / "canonical.svg").read_bytes(),
                i18n_path="_src/i18n/en/titles.json",
                i18n_bytes=b'{"title":"x"}',
                html_relpath="en/other.html",
                issue="0037-27",
                criterion="DoD-html-family-trace",
                source_commit=COMMIT,
                tool_commit=COMMIT_TOOL,
                config_commit=COMMIT_CFG,
            )
        self.assertEqual(ctx.exception.code, "HTP-MIXED-RUN")

    def test_family_cardinality_property(self):
        executed = 0
        for _ in range(3):
            self.tmp.cleanup()
            self.setUp()
            report = self._assemble()
            self.assertEqual(len(report["families"]), 5)
            self.assertEqual(set(report["families"]), set(trace.FAMILIES))
            executed += 1
        self.assertEqual(executed, 3)

    def test_falsification_adapter_absent_on_baseline(self):
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{BASELINE}:_src/tools/html_family_trace.py"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(listed.returncode, 0)
        self.assertTrue(ADAPTER.is_file())


if __name__ == "__main__":
    unittest.main()
