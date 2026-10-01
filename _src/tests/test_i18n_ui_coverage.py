import json
import os
import unittest
import sys

# Ensure _src is in the path so we can import lib_i18n if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import lib_i18n

class TestI18nUiCoverage(unittest.TestCase):
    def setUp(self):
        self.ui_path = os.path.join(lib_i18n.I18N, "ui.json")
        with open(self.ui_path, 'r', encoding='utf-8') as f:
            self.ui_data = json.load(f)
            
        self.expected_langs = ['de', 'en', 'es', 'pt', 'fr', 'ru', 'ar', 'hi', 'ko', 'zh', 'nl']
        self.expected_keys = {
            "universes": ["adaptive", "classic", "score", "switch_universe"],
            "nav_domains": ["explore", "trace", "curate", "review", "work", "reports"],
            "inspector": ["title", "stereotype", "status", "actions", "delete_btn", "confirm_delete", "accept", "reject", "rationale"],
            "feedback": ["title", "category", "description", "suggestion", "severity", "submit", "receipt_title"],
            "discuss": ["title", "context_title", "ask_placeholder", "generate_proposal", "submit_to_curation"]
        }

    def test_all_languages_present(self):
        for lang in self.expected_langs:
            self.assertIn(lang, self.ui_data, f"Language '{lang}' is missing from ui.json")

    def test_all_expected_sections_and_keys_present(self):
        for lang in self.expected_langs:
            lang_data = self.ui_data[lang]
            for section, keys in self.expected_keys.items():
                self.assertIn(section, lang_data, f"Section '{section}' missing in language '{lang}'")
                for key in keys:
                    self.assertIn(key, lang_data[section], f"Key '{key}' missing in section '{section}' for language '{lang}'")
                    
                    val = lang_data[section][key]
                    self.assertIsInstance(val, str, f"Value for '{section}.{key}' in '{lang}' must be a string")
                    self.assertTrue(len(val.strip()) > 0, f"Value for '{section}.{key}' in '{lang}' is empty")

    def test_lib_i18n_loading(self):
        # Assert that lib_i18n helper function loads and renders the strings correctly
        for lang in self.expected_langs:
            seg, lab, ui_all = lib_i18n.lade_register(lang)
            for section in self.expected_keys.keys():
                self.assertIn(section, ui_all, f"lade_register did not load '{section}' for '{lang}'")

if __name__ == '__main__':
    unittest.main()
