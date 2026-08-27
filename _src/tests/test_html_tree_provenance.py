"""Integration tests for page-generation HTML language-tree provenance (0037-27.05).

Adversarial completion evidence (DEC-0038-004):
- AE-2 baselines: pre-change `52e1e9c1159c7af79d0808f4f00be9016ef18f54` (0037-27.04);
  candidate this working tree (`html_tree_provenance.py` + generate.py hook).
- AE-3 falsification: a second live generate for the same language without
  invalidating the first is a mixed-run tree (`HTP-MIXED-RUN`). Absent on the
  baseline (module missing → ImportError/red).
- AE-4 adjacent: (1) governed page-model change marks the tree stale and linked
  regeneration records `invalidated-by`/`regenerated-by`; (2) byte-identical
  inputs (mtime-only) do not mark stale.
- AE-5: identity over the five producer-family input roles; each mutated family
  yields exactly one stale tree.
"""
from __future__ import annotations

import importlib.util
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "html_tree_provenance.py"
STORE = ROOT / "_src" / "tools" / "provenance_store.py"
GENERATE = ROOT / "_src" / "generate.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "html_tree_provenance"
BASELINE = "52e1e9c1159c7af79d0808f4f00be9016ef18f54"
COMMIT = "c" * 40
COMMIT_TOOL = "d" * 40
COMMIT_CFG = "e" * 40
STAMP = "2026-08-27T13:10:00Z"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


htp = _load("html_tree_provenance", TOOL)
ps = _load("provenance_store", STORE)

PAGE = FIXTURES.joinpath("page-model.json").read_bytes()
TEMPLATE = FIXTURES.joinpath("template.html").read_bytes()
AI = FIXTURES.joinpath("ai.html").read_bytes()
DIAGRAM = FIXTURES.joinpath("diagram.svg").read_bytes()
I18N = FIXTURES.joinpath("i18n.json").read_bytes()


class HtmlTreeProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "_src" / "tools").mkdir(parents=True)
        (self.root / "provenance" / "_schema").mkdir(parents=True)
        shutil.copy(STORE, self.root / "_src" / "tools" / "provenance_store.py")
        for name in ("provenance_views.py", "provenance_query.py", "version_id.py"):
            shutil.copy(ROOT / "_src" / "tools" / name, self.root / "_src" / "tools" / name)
        shutil.copy(
            ROOT / "provenance/_schema/provenance-graph-v1.schema.json",
            self.root / "provenance/_schema/provenance-graph-v1.schema.json",
        )
        shutil.copy(
            ROOT / "provenance/_schema/provenance-reverse-v1.schema.json",
            self.root / "provenance/_schema/provenance-reverse-v1.schema.json",
        )
        self.wf = htp.HtmlTreeWorkflow(self.root, clock=lambda: STAMP)

    def tearDown(self):
        self.tmp.cleanup()

    def _generate(self, **overrides):
        args = dict(
            language="en",
            page_model_path="_src/sources/pages/guide.json",
            page_model_bytes=PAGE,
            template_path="_src/templates/page.html",
            template_bytes=TEMPLATE,
            ai_path="_src/content/ai/guide-claim.html",
            ai_bytes=AI,
            diagram_path="_src/diagrams/guide.svg",
            diagram_bytes=DIAGRAM,
            i18n_path="_src/i18n/en/titles.json",
            i18n_bytes=I18N,
            html_relpath="en/guide.html",
            issue="0037-27.05",
            criterion="AC-html-tree-provenance",
            source_commit=COMMIT,
            tool_commit=COMMIT_TOOL,
            config_commit=COMMIT_CFG,
        )
        args.update(overrides)
        return self.wf.generate_language_tree(**args)

    def test_binds_provenance_store_schema_version(self):
        self.assertEqual(htp.ps.SCHEMA_VERSION, ps.SCHEMA_VERSION)
        rec = self._generate()
        self.assertEqual(rec["schema_version"], ps.SCHEMA_VERSION)

    def test_manifests_inputs_outputs_tree_and_validation_release(self):
        rec = self._generate()
        roles = {m["role"] for m in rec["members"]}
        self.assertEqual(roles, {"page-model", "template", "ai", "diagram", "i18n", "language-html"})
        self.assertTrue(rec["tree_digest"].startswith("sha256:"))
        self.assertEqual(rec["issue"], "0037-27.05")
        self.assertEqual(rec["criterion"], "AC-html-tree-provenance")
        self.assertTrue(rec["validation_id"])
        self.assertTrue(rec["release_id"])
        html = (self.root / rec["html_path"]).read_text(encoding="utf-8")
        htp.assert_html_without_provenance(html)
        self.assertFalse((self.root / rec["html_path"]).read_bytes().startswith(b"{"))
        envelope = self.root / rec["envelope_path"]
        self.assertTrue(envelope.is_file())
        self.assertTrue(str(envelope).endswith(".json"))
        relations = [
            json.loads(p.read_text(encoding="utf-8"))["relation"]
            for p in (self.root / "provenance" / "events").rglob("*.json")
        ]
        self.assertIn("verifies", relations)
        self.assertIn("published-as", relations)

    def test_trace_html_to_every_producer_family(self):
        rec = self._generate()
        traced = self.wf.trace_html_to_families(rec["html_path"])
        self.assertEqual(traced["missing_families"], [])
        self.assertEqual(set(traced["families"]), set(htp.PRODUCER_FAMILIES))
        self.assertTrue(traced["reverse"]["found"])
        fwd = self.wf.trace(kind="issue", identifier="0037-27.05", direction="forward")
        self.assertTrue(fwd["found"])

    def test_rejects_mixed_run_tree(self):
        self._generate()
        with self.assertRaises(htp.HtmlTreeProvenanceError) as ctx:
            self._generate(html_relpath="en/other.html")
        self.assertEqual(ctx.exception.code, "HTP-MIXED-RUN")

    def test_stale_inputs_and_consistent_regeneration(self):
        first = self._generate()
        mutated = PAGE.replace(b"Pipeline Guide", b"Pipeline Guide v2")
        work = self.wf.regeneration_work(
            page_model_bytes=mutated,
            template_bytes=TEMPLATE,
            ai_bytes=AI,
            diagram_bytes=DIAGRAM,
            i18n_bytes=I18N,
            language="en",
        )
        self.assertEqual([w["html_path"] for w in work], [first["html_path"]])
        second = self._generate(page_model_bytes=mutated, previous=first)
        self.assertIsNotNone(second["invalidation"])
        self.assertEqual(second["invalidation"]["cause"], "governed page-generation input change")
        self.assertNotEqual(second["tree_digest"], first["tree_digest"])
        relations = [
            json.loads(p.read_text(encoding="utf-8"))["relation"]
            for p in (self.root / "provenance" / "events").rglob("*.json")
        ]
        self.assertIn("invalidated-by", relations)
        self.assertIn("regenerated-by", relations)
        html = (self.root / second["html_path"]).read_text(encoding="utf-8")
        self.assertIn("Pipeline Guide v2", html)
        htp.assert_html_without_provenance(html)

    def test_mtime_only_does_not_mark_stale(self):
        self._generate()
        work = self.wf.regeneration_work(
            page_model_bytes=PAGE,
            template_bytes=TEMPLATE,
            ai_bytes=AI,
            diagram_bytes=DIAGRAM,
            i18n_bytes=I18N,
            language="en",
        )
        self.assertEqual(work, [])

    def test_rejects_html_provenance_injection(self):
        with self.assertRaises(htp.HtmlTreeProvenanceError) as ctx:
            self._generate(html_bytes=b"<html><body>run_id=secret</body></html>")
        self.assertEqual(ctx.exception.code, "HTP-HTML-INJECT")

    def test_identity_property_over_producer_families(self):
        self._generate()
        rng = random.Random(2705)
        executed = 0
        originals = {
            "page_model_bytes": PAGE,
            "template_bytes": TEMPLATE,
            "ai_bytes": AI,
            "diagram_bytes": DIAGRAM,
            "i18n_bytes": I18N,
        }
        for key, original in originals.items():
            mutated = original + bytes([rng.randint(1, 255)])
            kwargs = dict(originals)
            kwargs[key] = mutated
            work = self.wf.regeneration_work(language="en", **kwargs)
            self.assertEqual(len(work), 1, msg=key)
            executed += 1
        self.assertEqual(executed, 5)

    def test_generate_py_hook_is_opt_in(self):
        src = GENERATE.read_text(encoding="utf-8")
        self.assertIn("html_tree_provenance", src)
        self.assertIn("--provenance", src)
        self.assertTrue(htp.provenance_requested(["--lang=en", "--provenance"]))
        self.assertFalse(htp.provenance_requested(["--lang=en"]))
        self.assertTrue(htp.provenance_requested([], env={"HTML_TREE_PROVENANCE": "1"}))

    def test_falsification_module_absent_on_baseline(self):
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{BASELINE}:_src/tools/html_tree_provenance.py"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(listed.returncode, 0)
        self.assertTrue(TOOL.is_file())


if __name__ == "__main__":
    unittest.main()
