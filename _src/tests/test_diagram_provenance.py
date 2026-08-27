"""Tests for diagram SVG provenance manifests (Task `0037-27.02`)."""
from __future__ import annotations

import importlib.util
import json
import os
import random
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "diagram_provenance.py"
STORE = ROOT / "_src" / "tools" / "provenance_store.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "diagram_provenance"
COMMIT = "c" * 40
COMMIT_TOOL = "d" * 40
COMMIT_CFG = "e" * 40


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


dp = _load("diagram_provenance", TOOL)
ps = _load("provenance_store", STORE)

SVG = FIXTURES.joinpath("canonical.svg").read_text(encoding="utf-8")
DOT = FIXTURES.joinpath("source.dot").read_bytes()
LABELS = FIXTURES.joinpath("en.labels.json").read_bytes()


class DiagramProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "_src" / "tools").mkdir(parents=True)
        (self.root / "provenance" / "_schema").mkdir(parents=True)
        shutil.copy(STORE, self.root / "_src" / "tools" / "provenance_store.py")
        shutil.copy(
            ROOT / "_src" / "tools" / "provenance_views.py",
            self.root / "_src" / "tools" / "provenance_views.py",
        )
        shutil.copy(
            ROOT / "_src" / "tools" / "provenance_query.py",
            self.root / "_src" / "tools" / "provenance_query.py",
        )
        shutil.copy(
            ROOT / "provenance/_schema/provenance-graph-v1.schema.json",
            self.root / "provenance/_schema/provenance-graph-v1.schema.json",
        )
        shutil.copy(
            ROOT / "provenance/_schema/provenance-reverse-v1.schema.json",
            self.root / "provenance/_schema/provenance-reverse-v1.schema.json",
        )
        self.wf = dp.DiagramProvenanceWorkflow(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def _render(self, **overrides):
        args = dict(
            source_path="_src/diagrams/demo/svg_01.dot",
            source_bytes=DOT,
            svg_path="_src/diagrams/demo/svg_01.svg",
            svg_text=SVG,
            language="de",
            issue="0037-27.02",
            criterion="AC-diagram-provenance",
            source_commit=COMMIT,
            tool_commit=COMMIT_TOOL,
            config_commit=COMMIT_CFG,
        )
        args.update(overrides)
        return self.wf.record_render(**args)

    def test_records_envelope_and_source_to_svg_members(self):
        rec = self._render()
        roles = {m["role"] for m in rec["members"]}
        self.assertEqual(
            roles,
            {"source-model", "theme", "tool", "config", "rendered-svg"},
        )
        self.assertEqual(rec["language"], "de")
        self.assertEqual(rec["issue"], "0037-27.02")
        self.assertTrue(rec["svg_digest"].startswith("sha256:"))
        self.assertTrue((self.root / "provenance" / "runs" / f"{rec['run_id']}.json").is_file())
        self.assertNotIn("run_id", SVG)
        self.assertNotIn(rec["run_id"], SVG)

    def test_rejects_svg_provenance_injection(self):
        dirty = SVG.replace("</svg>", "<!-- diagram-provenance@v1 run_id=x --></svg>")
        with self.assertRaises(dp.DiagramProvenanceError) as ctx:
            dp.assert_svg_without_provenance(dirty)
        self.assertEqual(ctx.exception.code, "DP-SVG-INJECT")
        with self.assertRaises(dp.DiagramProvenanceError):
            self._render(svg_text=dirty)

    def test_source_change_marks_exact_svg_stale(self):
        first = self._render()
        stale = self.wf.stale_svgs(
            source_path=first["source_path"],
            source_bytes=DOT + b"\n# changed\n",
            labels_bytes=None,
        )
        self.assertEqual([s["svg_path"] for s in stale], [first["svg_path"]])
        self.assertEqual(stale[0]["svg_digest"], first["svg_digest"])

    def test_mtime_only_does_not_mark_stale(self):
        first = self._render()
        stale = self.wf.stale_svgs(
            source_path=first["source_path"],
            source_bytes=DOT,
            labels_bytes=None,
        )
        self.assertEqual(stale, [])

    def test_theme_change_marks_stale(self):
        first = self._render()
        stale = self.wf.stale_svgs(
            source_path=first["source_path"],
            source_bytes=DOT,
            labels_bytes=None,
            theme_constants={"C_BG": "#000000", "C_TEXT": "#fff", "FONT": "x"},
        )
        self.assertEqual(len(stale), 1)

    def test_labels_change_marks_translated_not_unrelated_language(self):
        de = self._render()
        en = self._render(
            svg_path="_src/i18n/en/diagrams/demo/svg_01.svg",
            language="en",
            labels_path="_src/i18n/en/labels.json",
            labels_bytes=LABELS,
        )
        stale_en = self.wf.stale_svgs(
            source_path=de["source_path"],
            source_bytes=DOT,
            labels_bytes=b'{"edge": "kante"}',
            language="en",
        )
        stale_de = self.wf.stale_svgs(
            source_path=de["source_path"],
            source_bytes=DOT,
            labels_bytes=None,
            language="de",
        )
        self.assertEqual([s["svg_path"] for s in stale_en], [en["svg_path"]])
        self.assertEqual(stale_de, [])

    def test_regeneration_links_replacement(self):
        first = self._render()
        second = self._render(
            source_bytes=DOT + b"\n# v2\n",
            svg_text=SVG.replace("graph0", "graph1"),
            previous=first,
        )
        self.assertIsNotNone(second["invalidation"])
        self.assertEqual(
            second["invalidation"]["previous_svg"]["digest"],
            first["svg_digest"],
        )
        self.assertEqual(
            second["invalidation"]["replacement_svg"]["digest"],
            second["svg_digest"],
        )
        events_dir = self.root / "provenance" / "events"
        relations = []
        for path in events_dir.rglob("*.json"):
            relations.append(json.loads(path.read_text(encoding="utf-8"))["relation"])
        self.assertIn("invalidated-by", relations)
        self.assertIn("regenerated-by", relations)
        self.assertIn("supersedes", relations)

    def test_bidirectional_trace_canonical_and_translated(self):
        de = self._render()
        en = self._render(
            svg_path="_src/i18n/en/diagrams/demo/svg_01.svg",
            language="en",
            labels_path="_src/i18n/en/labels.json",
            labels_bytes=LABELS,
        )
        fwd = self.wf.trace(kind="issue", identifier="0037-27.02", direction="forward")
        self.assertTrue(fwd["found"])
        paths = {f["path"] for f in fwd["files"]}
        self.assertIn(de["svg_path"], paths)
        self.assertIn(en["svg_path"], paths)
        self.assertIn(de["source_path"], paths)
        rev_de = self.wf.trace(
            kind="artifact",
            identifier=f"{de['svg_path']}@{de['svg_digest']}",
            direction="reverse",
        )
        self.assertIn("issue:0037-27.02", rev_de["issues"])
        rev_en = self.wf.trace(
            kind="artifact",
            identifier=f"{en['svg_path']}@{en['svg_digest']}",
            direction="reverse",
        )
        self.assertIn("issue:0037-27.02", rev_en["issues"])

    def test_env_hook_noop_without_root(self):
        os.environ.pop("DIAGRAM_PROVENANCE_ROOT", None)
        src = self.root / "_src" / "diagrams" / "demo" / "svg_01.dot"
        src.parent.mkdir(parents=True)
        src.write_bytes(DOT)
        out = dp.maybe_record_from_env(
            src, SVG, language="de", repository_root=self.root
        )
        self.assertIsNone(out)

    def test_member_set_property(self):
        """AE-5: every recorded set contains source+theme+svg; identity tracks those digests."""
        rng = random.Random(2702)
        seen = 0
        for i in range(24):
            src = f"graph {rng.randint(0, 10**6)}".encode()
            lab = None if i % 3 == 0 else json.dumps({"k": str(i)}).encode()
            rec = self._render(
                source_bytes=src,
                source_path=f"_src/diagrams/p{i}.dot",
                svg_path=f"_src/diagrams/p{i}.svg",
                labels_path=None if lab is None else f"_src/i18n/en/p{i}.json",
                labels_bytes=lab,
                language="de" if lab is None else "en",
            )
            roles = [m["role"] for m in rec["members"]]
            self.assertEqual(len(roles), len(set(roles)))
            self.assertIn("source-model", roles)
            self.assertIn("theme", roles)
            self.assertIn("rendered-svg", roles)
            if lab is None:
                self.assertNotIn("labels", roles)
            else:
                self.assertIn("labels", roles)
            identity = dp.input_identity(rec["members"])
            self.assertEqual(identity, rec["identity"])
            seen += 1
        self.assertEqual(seen, 24)


if __name__ == "__main__":
    unittest.main()
