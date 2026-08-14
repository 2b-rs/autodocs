#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import unittest
from unittest.mock import patch, MagicMock

import sys
_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import validate


class TestClientRenderedGerman(unittest.TestCase):
    def test_pick_review_notice_page(self):
        # de returns None or a valid de page
        de_page = validate._pick_review_notice_page("de")
        # en page if exists should have review notice
        en_page = validate._pick_review_notice_page("en")
        if en_page:
            self.assertTrue(os.path.exists(en_page))
            self.assertTrue(en_page.endswith(".html"))

    def test_check_client_rendered_german_de_ignored(self):
        # German canonical pages are exempt
        res = validate._check_client_rendered_german_one_lang("de")
        self.assertEqual(res, [])

    def test_check_client_rendered_german_detects_german_string(self):
        # Mock subprocess to simulate JS output containing hardcoded German strings
        fake_result = json.dumps({
            "url": "/fake/en/classes/foo.html",
            "bodyText": "Some english text with mit Review-Bedarf included",
            "pageErrors": []
        })
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = fake_result

        with patch("validate._pick_review_notice_page", return_value="/tmp/fake_page.html"):
            with patch("subprocess.run", return_value=mock_proc):
                problems = validate._check_client_rendered_german_one_lang("en")
                self.assertTrue(any("mit Review-Bedarf" in p for p in problems))

    def test_check_client_rendered_german_clean_output(self):
        # Mock subprocess returning clean translated text
        fake_result = json.dumps({
            "url": "/fake/en/classes/foo.html",
            "bodyText": "1 API element requiring review. Clean english translation.",
            "pageErrors": []
        })
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = fake_result

        with patch("validate._pick_review_notice_page", return_value="/tmp/fake_page.html"):
            with patch("subprocess.run", return_value=mock_proc):
                problems = validate._check_client_rendered_german_one_lang("en")
                self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
