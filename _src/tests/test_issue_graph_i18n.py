"""Localized public/maintainer graph contract tests for 0037-24.02."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "_src"
FIX = SRC / "tests" / "fixtures" / "issue-graph-i18n"
SPEC = importlib.util.spec_from_file_location("i18n_translate_graph", SRC / "i18n_translate.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
LANGS = ["de", "en", "es", "pt", "fr", "ru", "ar", "hi", "ko", "zh", "nl"]
TITLE = "Public issue `0099`"
TITLE_HASH = "sha256:" + hashlib.sha256(TITLE.encode()).hexdigest()


class IssueGraphI18nTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="issue-graph-i18n-"))
        self.i18n = self.tmp / "i18n"
        self.output = self.tmp / "data"
        self.site = self.tmp / "site.json"
        self.public = self.tmp / "public.json"
        shutil.copy(FIX / "site.json", self.site)
        payload = json.loads((FIX / "public.json").read_text())
        payload["items"][0]["title_source_hash"] = TITLE_HASH
        self.public.write_text(json.dumps(payload), encoding="utf-8")
        strings = {key: "%s:%s" % ("en", key) for key in sorted(MOD.GRAPH_UI_REQUIRED)}
        ui = {}
        for lang in LANGS:
            ui[lang] = {"graph": {"schema": MOD.GRAPH_UI_SCHEMA,
                                   "summaries": {"issues.0099.summary": "%s:summary" % lang},
                                   "strings": {key: "%s:%s" % (lang, key) for key in strings}}}
            status = "canonical" if lang == "en" else "translated"
            translation = TITLE if lang == "en" else "%s %s" % (lang, TITLE)
            doc = {"schema": MOD.ISSUE_SCHEMA, "language": lang, "source_locale": "en",
                   "records": [{"item_id": "0099", "source_locale": "en",
                                "source_title_hash": TITLE_HASH, "translation": translation,
                                "translator": {"id": "fixture"}, "run": {"id": "fixture"},
                                "status": status}]}
            path = self.i18n / lang
            path.mkdir(parents=True)
            (path / "issues.json").write_text(json.dumps(doc), encoding="utf-8")
        self.ui = self.i18n / "ui.json"
        self.ui.write_text(json.dumps(ui), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def generate(self):
        return MOD.generate_public_graph_payloads(
            str(self.public), str(self.site), str(self.i18n), str(self.ui), str(self.output))

    def test_all_configured_languages_deterministic_and_local_links(self):
        paths = self.generate()
        self.assertEqual(len(paths), 11)
        first = {Path(p).name: Path(p).read_bytes() for p in paths}
        self.assertEqual(paths, self.generate())
        self.assertEqual(first, {Path(p).name: Path(p).read_bytes() for p in paths})
        for lang in LANGS:
            payload = json.loads((self.output / ("issue-graph-public.%s.json" % lang)).read_text())
            self.assertEqual(payload["language"], lang)
            self.assertEqual(payload["direction"], "rtl" if lang == "ar" else "ltr")
            prefix = "/" if lang == "de" else "/%s/" % lang
            self.assertEqual(payload["items"][0]["link"], prefix + "issues.html#0099")
            self.assertIn("0099", payload["items"][0]["title"])
            self.assertEqual(payload["items"][0]["public_summary"], "%s:summary" % lang)

    def test_missing_ui_fails_without_partial_publication(self):
        ui = json.loads(self.ui.read_text())
        del ui["fr"]["graph"]
        self.ui.write_text(json.dumps(ui), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing required graph UI"):
            self.generate()
        self.assertFalse(self.output.exists())

    def test_missing_and_stale_title_fail(self):
        path = self.i18n / "es" / "issues.json"
        doc = json.loads(path.read_text())
        doc["records"] = []
        path.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing/stale public title"):
            self.generate()
        doc["records"][0:0] = [{"item_id": "0099", "source_locale": "en",
                                "source_title_hash": "sha256:" + "c" * 64,
                                "expected_source_title_hash": TITLE_HASH,
                                "translation": "es " + TITLE, "translator": {"id": "fixture"},
                                "run": {"id": "fixture"}, "status": "stale"}]
        path.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing/stale public title"):
            self.generate()

    def test_protected_tokens_rejected(self):
        path = self.i18n / "pt" / "issues.json"
        doc = json.loads(path.read_text())
        doc["records"][0]["translation"] = "título público"
        path.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "geschützte Tokens"):
            self.generate()

    def test_maintainer_fallback_is_explicit_english(self):
        ui = json.loads(self.ui.read_text())
        del ui["nl"]["graph"]
        self.ui.write_text(json.dumps(ui), encoding="utf-8")
        result = MOD.maintainer_graph_ui("nl", str(self.ui))
        self.assertTrue(all(row["fallback"] for row in result.values()))
        self.assertEqual({row["lang"] for row in result.values()}, {"en"})
        html = (ROOT / "tools" / "todo-dependency-graph.html").read_text()
        embed = (ROOT / "tools" / "todo-graph-embed.js").read_text()
        self.assertIn("data-i18n-fallback', 'canonical-en", html)
        self.assertIn("data-i18n-fallback', 'canonical-en", embed)
        self.assertIn("setAttribute('lang', ui.language)", embed)

    def test_maintainer_sources_do_not_embed_german_graph_chrome(self):
        blobs = "\n".join((ROOT / p).read_text() for p in [
            "tools/todo-graph-core.js", "tools/todo-graph-embed.js",
            "tools/todo-dependency-graph.html"])
        for token in ("Abhängigkeitsgraph", "geschlossen", "zurückgezogen", "Wird geladen"):
            self.assertNotIn(token, blobs)

    def test_client_core_selects_all_languages_and_visible_fallback(self):
        register = json.loads(self.ui.read_text())
        script = """
const core=require(process.argv[1]);
const ui=JSON.parse(process.argv[2]);
const langs=JSON.parse(process.argv[3]);
const out=langs.map(l=>core.graphUi(ui,l,true));
delete ui.nl.graph;
const fallback=core.graphUi(ui,'nl',true);
process.stdout.write(JSON.stringify({langs:out.map(x=>x.language), fallback}));
"""
        result = subprocess.run(
            ["node", "-e", script, str(ROOT / "tools" / "todo-graph-core.js"),
             json.dumps(register), json.dumps(LANGS)], capture_output=True, text=True, check=True)
        value = json.loads(result.stdout)
        self.assertEqual(value["langs"], LANGS)
        self.assertTrue(value["fallback"]["fallback"])
        self.assertEqual(value["fallback"]["language"], "en")


if __name__ == "__main__":
    unittest.main()
