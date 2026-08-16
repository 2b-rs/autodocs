import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))

import validate  # pyright: ignore[reportImplicitRelativeImport]


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


class ParallelLinkValidationTests(unittest.TestCase):
    def setUp(self):
        validate.problems.clear()
        validate.structured_findings.clear()
        validate.checks_performed.clear()
        InlineExecutor.last_max_workers = None

    def test_parallel_scan_preserves_link_and_anchor_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.html").write_text(
                """<html><body>
                <a href="b.html#ok">valid</a>
                <a href="b.html#missing">bad anchor</a>
                <a href="missing.html">bad file</a>
                <a href="#">placeholder</a>
                <a href="https://example.com/ignored">external</a>
                <img src="asset.png"><img src="missing.png">
                </body></html>""",
                encoding="utf-8",
            )
            (root / "b.html").write_text(
                '<html><body><section id="ok">target</section></body></html>',
                encoding="utf-8",
            )
            (root / "c.html").write_text(
                '<html><body><a href="a.html">back</a></body></html>',
                encoding="utf-8",
            )
            (root / "d.html").write_text(
                '<html><body><a href="a.html#missing-local">bad</a></body></html>',
                encoding="utf-8",
            )
            (root / "asset.png").write_bytes(b"fixture")

            with mock.patch.object(validate, "ROOT", str(root)), \
                 mock.patch.object(validate, "LANGS", []), \
                 mock.patch.object(validate, "WORKERS", 2), \
                 mock.patch.object(validate, "ProcessPoolExecutor", InlineExecutor):
                validate.check_links()
            parallel_findings = [dict(finding) for finding in validate.structured_findings]
            parallel_problems = list(validate.problems)

            validate.problems.clear()
            validate.structured_findings.clear()
            validate.checks_performed.clear()

            def fail_if_constructed(*_args, **_kwargs):
                raise AssertionError("serial scan should not construct a process pool")

            with mock.patch.object(validate, "ROOT", str(root)), \
                 mock.patch.object(validate, "LANGS", []), \
                 mock.patch.object(validate, "WORKERS", 99), \
                 mock.patch.object(validate, "ProcessPoolExecutor", fail_if_constructed):
                validate.check_links()
            serial_findings = [dict(finding) for finding in validate.structured_findings]
            serial_problems = list(validate.problems)

        self.assertEqual(InlineExecutor.last_max_workers, 2)
        self.assertEqual(parallel_findings, serial_findings)
        self.assertEqual(parallel_problems, serial_problems)
        self.assertEqual(validate.checks_performed, ["check_links"])
        self.assertEqual(
            parallel_findings,
            [
                {
                    "category": "placeholder-link",
                    "severity": "error",
                    "message": 'Platzhalter-Link href="#" in a.html (placeholder)',
                    "ref": "a.html",
                },
                {
                    "category": "dead-link",
                    "severity": "error",
                    "message": "toter interner Link in a.html -> b.html#missing (Anker fehlt)",
                    "ref": "a.html",
                },
                {
                    "category": "dead-link",
                    "severity": "error",
                    "message": "toter interner Link in a.html -> missing.html (Datei fehlt)",
                    "ref": "a.html",
                },
                {
                    "category": "dead-link",
                    "severity": "error",
                    "message": "toter interner Link in d.html -> a.html#missing-local (Anker fehlt)",
                    "ref": "d.html",
                },
                {
                    "category": "missing-image",
                    "severity": "error",
                    "message": "fehlende Bilddatei in a.html -> missing.png",
                    "ref": "a.html",
                },
            ],
        )
        messages = "\n".join(finding["message"] for finding in parallel_findings)
        self.assertNotIn("b.html#ok (", messages)
        self.assertNotIn("asset.png", messages)


if __name__ == "__main__":
    unittest.main()
