import copy
import hashlib
import importlib.util
import json
import os
import shutil
import tempfile
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "issue-title-i18n")
SPEC = importlib.util.spec_from_file_location("i18n_translate", os.path.join(ROOT, "i18n_translate.py"))
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class IssueTitleI18nTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="issue-title-i18n-")
        self.i18n = os.path.join(self.tmp, "i18n")
        self.site = os.path.join(self.tmp, "site.json")
        self.catalog = os.path.join(self.tmp, "catalog.json")
        self.public = os.path.join(self.tmp, "public.json")
        for name, target in (("site.json", self.site), ("catalog.json", self.catalog),
                             ("public.json", self.public)):
            shutil.copyfile(os.path.join(FIXTURES, name), target)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def extract(self):
        return MOD.extract_issue_titles(self.catalog, self.public, self.site, self.i18n)

    def load(self, language):
        with open(os.path.join(self.i18n, language, "issues.json"), encoding="utf-8") as stream:
            return json.load(stream)

    def write_json(self, path, value):
        with open(path, "w", encoding="utf-8") as stream:
            json.dump(value, stream)

    def merge_file(self, language, translation, digest=None, item_id="0037-24.01"):
        digest = digest or self.load("en")["records"][0]["source_title_hash"]
        path = os.path.join(self.tmp, "merge.jsonl")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(json.dumps({"item_id": item_id, "source_title_hash": digest,
                                     "translation": translation}, ensure_ascii=False) + "\n")
        return path

    def test_extract_schema_public_only_and_dynamic_languages(self):
        expected = self.extract()
        self.assertEqual(["0037-24.01"], list(expected))
        self.assertEqual({"de", "en", "es", "ar"}, set(os.listdir(self.i18n)))
        english = self.load("en")
        self.assertEqual("issue-title-translations@v1", english["schema"])
        self.assertEqual("en", english["source_locale"])
        self.assertEqual("canonical", english["records"][0]["status"])
        self.assertNotIn("0099", json.dumps(english))
        self.assertEqual("pending", self.load("de")["records"][0]["status"])

    def test_split_merge_round_trip_ltr_and_arabic_rtl(self):
        self.extract()
        title = self.load("en")["records"][0]["translation"]
        for language, translation in (
            ("de", "Implementiere `REF: abcdef1234567890abcdef1234567890abcdef12` für 0037-24.01 und {name}."),
            ("es", "Implementar `REF: abcdef1234567890abcdef1234567890abcdef12` para 0037-24.01 y {name}."),
            ("ar", "نفّذ `REF: abcdef1234567890abcdef1234567890abcdef12` لـ 0037-24.01 و{name}."),
        ):
            rows = MOD.split_issue_titles(language, self.site, self.i18n,
                                          os.path.join(self.tmp, language + ".jsonl"))
            self.assertEqual(title, rows[0]["source_title"])
            merged = MOD.merge_issue_titles(language, self.merge_file(language, translation),
                                             "translator-1", "run-1", self.site, self.i18n)
            self.assertEqual(1, merged)
            record = self.load(language)["records"][0]
            self.assertEqual("translated", record["status"])
            self.assertEqual(translation, record["translation"])
            self.assertEqual({"id": "translator-1"}, record["translator"])
            self.assertEqual({"id": "run-1"}, record["run"])
            self.assertEqual([], MOD.split_issue_titles(
                language, self.site, self.i18n, os.path.join(self.tmp, language + "-done.jsonl")))

    def test_source_change_invalidates_translation_and_rejects_stale_merge(self):
        self.extract()
        translation = "Implementar `REF: abcdef1234567890abcdef1234567890abcdef12` para 0037-24.01 y {name}."
        MOD.merge_issue_titles("es", self.merge_file("es", translation), "t", "r", self.site, self.i18n)
        with open(self.catalog, encoding="utf-8") as stream:
            catalog = json.load(stream)
        old_hash = catalog["items"][0]["title_source_hash"]
        catalog["items"][0]["title"] += " Updated."
        new_hash = "sha256:" + hashlib.sha256(catalog["items"][0]["title"].encode()).hexdigest()
        catalog["items"][0]["title_source_hash"] = new_hash
        with open(self.public, encoding="utf-8") as stream:
            public = json.load(stream)
        public["items"][0]["title_source_hash"] = new_hash
        self.write_json(self.catalog, catalog)
        self.write_json(self.public, public)
        self.extract()
        record = self.load("es")["records"][0]
        self.assertEqual("stale", record["status"])
        self.assertEqual(old_hash, record["source_title_hash"])
        self.assertEqual(new_hash, record["expected_source_title_hash"])
        with self.assertRaisesRegex(ValueError, "stale source hash"):
            MOD.merge_issue_titles("es", self.merge_file("es", translation, old_hash),
                                   "t", "r2", self.site, self.i18n)

    def test_rejects_duplicate_wrong_item_and_protected_token_changes(self):
        self.extract()
        good = "نفّذ `REF: abcdef1234567890abcdef1234567890abcdef12` لـ 0037-24.01 و{name}."
        path = self.merge_file("ar", good)
        with open(path, encoding="utf-8") as source:
            duplicate = source.read()
        with open(path, "a", encoding="utf-8") as stream:
            stream.write(duplicate)
        with self.assertRaisesRegex(ValueError, "duplicate merge item"):
            MOD.merge_issue_titles("ar", path, "t", "r", self.site, self.i18n)
        with self.assertRaisesRegex(ValueError, "wrong-item"):
            MOD.merge_issue_titles("ar", self.merge_file("ar", good, item_id="9999"),
                                   "t", "r", self.site, self.i18n)
        bad = "نفّذ `REF: abcdef1234567890abcdef1234567890abcdef12` لـ 0037-99.01 و{name}."
        with self.assertRaisesRegex(ValueError, "geschützte Tokens"):
            MOD.merge_issue_titles("ar", self.merge_file("ar", bad), "t", "r", self.site, self.i18n)

    def test_document_validation_duplicate_and_header(self):
        self.extract()
        doc = self.load("de")
        doc["records"].append(copy.deepcopy(doc["records"][0]))
        self.write_json(os.path.join(self.i18n, "de", "issues.json"), doc)
        with self.assertRaisesRegex(ValueError, "doppelter"):
            MOD.issue_title_status(self.site, self.i18n)
        doc["records"] = doc["records"][:1]
        doc["source_locale"] = "de"
        self.write_json(os.path.join(self.i18n, "de", "issues.json"), doc)
        with self.assertRaisesRegex(ValueError, "Header"):
            MOD.issue_title_status(self.site, self.i18n)

    def test_completeness_reports_every_configured_language(self):
        self.extract()
        status = MOD.issue_title_status(self.site, self.i18n)
        self.assertEqual({"de", "en", "es", "ar"}, set(status["languages"]))
        self.assertFalse(status["complete"])
        self.assertTrue(status["languages"]["en"]["complete"])
        self.assertEqual(1, status["languages"]["ar"]["counts"]["pending"])

    def test_extraction_rejects_hash_and_visibility_mismatch(self):
        with open(self.public, encoding="utf-8") as stream:
            public = json.load(stream)
        public["items"][0]["title_source_hash"] = "sha256:" + "0" * 64
        self.write_json(self.public, public)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.extract()
        shutil.copyfile(os.path.join(FIXTURES, "public.json"), self.public)
        with open(self.catalog, encoding="utf-8") as stream:
            catalog = json.load(stream)
        catalog["items"][0]["visibility"] = "internal"
        self.write_json(self.catalog, catalog)
        with self.assertRaisesRegex(ValueError, "visibility"):
            self.extract()


if __name__ == "__main__":
    unittest.main()
