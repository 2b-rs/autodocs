import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))

import generate  # pyright: ignore[reportImplicitRelativeImport]


class InlineExecutor:
    last_max_workers = None

    def __init__(self, max_workers=None, **_kwargs):
        type(self).last_max_workers = max_workers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def map(self, func, iterable, chunksize=1):
        del chunksize
        for item in iterable:
            yield func(item)


class FakeStat:
    def __init__(self, lang):
        self.treffer = len(lang)
        self.fehlend = {"missing-%s" % lang: "text"}


class GenerateLanguagesTests(unittest.TestCase):
    def test_publication_chooser_links_are_language_specific(self):
        canonical = generate.publication_links("@@AUTOSAR_TREE_HREF@@ @@SCORE_TREE_HREF@@")
        translated = generate.publication_links("@@AUTOSAR_TREE_HREF@@ @@SCORE_TREE_HREF@@", "fr")
        self.assertEqual(canonical, "index.html eclipse-score-v0.6.0-curation-review/de/index.html")
        self.assertEqual(translated, "index.html ../eclipse-score-v0.6.0-curation-review/fr/index.html")

    def test_languages_use_bounded_pool_and_report_in_input_order(self):
        calls = []

        def fake_generate_lang(lang, only=None, check=False, announce=True):
            calls.append((lang, only, check, announce))
            return 7, FakeStat(lang), []

        output = io.StringIO()
        with mock.patch.object(generate, "WORKERS", 2), \
             mock.patch.object(generate, "ProcessPoolExecutor", InlineExecutor), \
             mock.patch.object(generate, "generate_lang", side_effect=fake_generate_lang), \
             redirect_stdout(output):
            results = generate.generate_languages(
                ["en", "es", "en", "fr", "pt"], only={"index.html"}
            )

        self.assertEqual(InlineExecutor.last_max_workers, 2)
        self.assertEqual([result[0] for result in results], ["en", "es", "fr", "pt"])
        self.assertEqual(
            calls,
            [
                ("en", {"index.html"}, False, False),
                ("es", {"index.html"}, False, False),
                ("fr", {"index.html"}, False, False),
                ("pt", {"index.html"}, False, False),
            ],
        )
        summary_lines = [line for line in output.getvalue().splitlines() if line]
        self.assertEqual(len(summary_lines), 4)
        self.assertIn("[en]", summary_lines[0])
        self.assertIn("[es]", summary_lines[1])
        self.assertIn("[fr]", summary_lines[2])
        self.assertIn("[pt]", summary_lines[3])

    def test_rejects_language_alias_outside_configured_targets(self):
        with self.assertRaisesRegex(ValueError, "unsupported language"):
            generate.generate_languages(["en", "./en"])

    def test_single_language_avoids_process_pool(self):
        def fail_if_constructed(*_args, **_kwargs):
            raise AssertionError("process pool should not be constructed")

        with mock.patch.object(generate, "ProcessPoolExecutor", fail_if_constructed), \
             mock.patch.object(
                 generate,
                 "generate_lang",
                 return_value=(2, FakeStat("en"), []),
             ):
            results = generate.generate_languages(["en"], check=True)

        self.assertEqual(results, [("en", 2, 2, 1, [])])


if __name__ == "__main__":
    unittest.main()
