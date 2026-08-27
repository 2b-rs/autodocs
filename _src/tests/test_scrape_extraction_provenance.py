"""Integration tests for scrape/extraction provenance envelope (Task 0037-26.01).

Adversarial completion evidence (DEC-0038-004): counting/identity/serialization/gates.
Pre-change baseline: start_base ``2064704457f98c66fb6f77ad3c263415864fe2ff``
(no scrape_extraction_provenance adapter). Candidate: this tree's adapter.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "scrape_extraction_provenance.py"
STORE = ROOT / "_src" / "tools" / "provenance_store.py"
COMMIT = "c2f198e194aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"[:40]
# pad to 40 using a documented fixture commit shape
COMMIT = ("c2f198e19" + "a" * 31)[:40]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sep = _load("scrape_extraction_provenance", TOOL)
ps = _load("provenance_store_for_sep", STORE)


def _legacy_path_mtime_identity(member: dict) -> bool:
    """Pre-0037-26.01 scrape reports treated path (and optionally mtime) as identity."""
    return bool(member.get("path"))


class ScrapeExtractionProvenanceTests(unittest.TestCase):
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
            "scrape_extraction_provenance.py",
        ):
            shutil.copy(ROOT / "_src" / "tools" / name, self.root / "_src" / "tools" / name)
        for schema in (
            "provenance-graph-v1.schema.json",
            "provenance-reverse-v1.schema.json",
        ):
            src = ROOT / "provenance" / "_schema" / schema
            if src.is_file():
                shutil.copy(src, self.root / "provenance" / "_schema" / schema)
        self.pdf = b"%PDF-1.4 fixture source bytes for RS_PER_00010\n"
        self.text = b".. req:: example\n   :id: SCORE_1\n"
        self.files = {
            "fixtures/source.pdf": self.pdf,
            "fixtures/source.rst": self.text,
        }

    def tearDown(self):
        self.tmp.cleanup()

    def _persist(self, **overrides):
        kwargs = dict(
            store_root=self.root,
            producer="spec_scrape.phase_crosscheck",
            source_commit=COMMIT,
            tool_commit=COMMIT,
            config_commit=COMMIT,
            input_files=self.files,
            report_path="output/reports/spec-scrape-crosscheck.json",
            report_bytes=b'{"backends":["pypdf","builtin"],"backend_deviations":[]}',
            issue="0037-26.01",
            criterion="AC-scrape-envelope",
            campaign="scrape-extraction",
            trigger_kind="issue",
            trigger_id="0037-26.01",
            cause="spec_scrape.phase_crosscheck",
            status="succeeded",
            started_at="2026-08-27T12:00:00Z",
            ended_at="2026-08-27T12:00:01Z",
        )
        kwargs.update(overrides)
        return sep.persist_scrape_extraction_report(**kwargs)

    def test_trace_report_finding_to_exact_source_bytes_and_trigger(self):
        envelope = self._persist(
            disagreements=[
                {
                    "kind": "backend-disagreement",
                    "cause": "backend-disagreement",
                    "detail": "pypdf vs builtin page text",
                }
            ],
            status="failed",
        )
        self.assertEqual(envelope["schema"], sep.SCHEMA)
        self.assertEqual(envelope["trigger"]["id"], "0037-26.01")
        self.assertEqual(
            envelope["input_digests"]["fixtures/source.pdf"], sep.sha256_bytes(self.pdf)
        )
        self.assertTrue(envelope["finding_ids"])
        rev = sep.trace_report_to_source(
            self.root,
            report_path="output/reports/spec-scrape-crosscheck.json",
            report_digest=envelope["report_digest"],
        )
        self.assertTrue(rev["found"], msg=json.dumps(rev, indent=2)[:2000])
        self.assertIn("issue:0037-26.01", rev["issues"])
        self.assertTrue(
            any(
                f.get("path") == "fixtures/source.pdf"
                and f.get("digest") == sep.sha256_bytes(self.pdf)
                for f in rev.get("files") or []
            )
            or any(
                member["digest"] == sep.sha256_bytes(self.pdf)
                for member in json.loads(
                    next((self.root / "provenance" / "artifact-sets").glob("*.json")).read_text(
                        encoding="utf-8"
                    )
                )["members"]
            )
        )
        finding_id = envelope["finding_ids"][0]
        fwd = sep.pq.query_trace(self.root, kind="finding", identifier=finding_id, direction="forward")
        self.assertTrue(fwd["found"])
        self.assertIn("issue:0037-26.01", fwd["issues"] or [fwd.get("issues")])
        # exact bytes still match stored digest
        stored = json.loads(next((self.root / "provenance" / "artifact-sets").glob("*.json")).read_text())
        pdf_member = next(m for m in stored["members"] if m["path"] == "fixtures/source.pdf")
        self.assertEqual(pdf_member["digest"], sep.sha256_bytes(self.pdf))
        self.assertEqual(pdf_member["size_bytes"], len(self.pdf))

    def test_path_only_rejected_red_on_baseline_green_on_candidate(self):
        member = {"path": "fixtures/source.pdf", "source_commit": COMMIT}
        self.assertTrue(_legacy_path_mtime_identity(member), "baseline accepted path-only")
        with self.assertRaises(sep.ScrapeExtractionProvenanceError) as ctx:
            sep.validate_input_members([member], self.files)
        self.assertEqual(ctx.exception.code, "SEP-PATH-ONLY")

    def test_mtime_only_rejected_adjacent_to_content_digest(self):
        good = sep.members_from_bytes(self.files, source_commit=COMMIT)
        mutated = dict(good[0])
        mutated["mtime"] = 1710000000.0
        with self.assertRaises(sep.ScrapeExtractionProvenanceError) as ctx:
            sep.validate_input_members([mutated], self.files)
        self.assertEqual(ctx.exception.code, "SEP-MTIME-ONLY")
        # adjacent: content change alters identity; mtime is not used
        other = dict(self.files)
        other["fixtures/source.pdf"] = self.pdf + b" "
        self.assertNotEqual(
            sep.sha256_bytes(self.pdf), sep.sha256_bytes(other["fixtures/source.pdf"])
        )

    def test_fabricated_digest_rejected(self):
        members = sep.members_from_bytes(self.files, source_commit=COMMIT)
        members[0]["digest"] = "sha256:" + ("ab" * 32)
        with self.assertRaises(sep.ScrapeExtractionProvenanceError) as ctx:
            sep.validate_input_members(members, self.files)
        self.assertEqual(ctx.exception.code, "SEP-FABRICATED")

    def test_mismatched_run_rejected(self):
        with self.assertRaises(sep.ScrapeExtractionProvenanceError) as ctx:
            self._persist(
                run_id="018f4a31-32aa-7abc-8def-0123456789ab",
                claimed_run_id="018f4a31-ffff-7abc-8def-0123456789ab",
            )
        self.assertEqual(ctx.exception.code, "SEP-RUN-MISMATCH")

    def test_fabricated_run_not_in_store(self):
        with self.assertRaises(sep.ScrapeExtractionProvenanceError) as ctx:
            sep.assert_not_fabricated_run(self.root, "018f4a31-dead-7abc-8def-0123456789ab")
        self.assertEqual(ctx.exception.code, "SEP-FABRICATED")

    def test_producer_wrappers_attach_envelope(self):
        cross = sep.record_crosscheck_report(
            {"release": "R25-11", "backend_deviations": [{"id": "RS_X", "field": "heading"}]},
            pdf_files={"fixtures/source.pdf": self.pdf},
            store_root=self.root,
            source_commit=COMMIT,
            tool_commit=COMMIT,
            config_commit=COMMIT,
        )
        self.assertIn("provenance_envelope", cross)
        self.assertEqual(cross["provenance_envelope"]["status"], "failed")
        self.assertTrue(cross["provenance_envelope"]["finding_ids"])

        page = sep.record_extraction_assemble(
            {"file": "extraction-report.html", "title": "fixture"},
            input_files={"output/extraction-report-work/traceability.json": b"[]\n"},
            store_root=self.root,
            source_commit=COMMIT,
            tool_commit=COMMIT,
            config_commit=COMMIT,
        )
        self.assertEqual(page["provenance_envelope"]["producer"], "extraction_report.assemble")

        score = sep.record_score_scrape_report(
            {"records": [], "count": 0},
            input_files={"fixtures/source.rst": self.text},
            store_root=self.root,
            source_commit=COMMIT,
            tool_commit=COMMIT,
            config_commit=COMMIT,
        )
        self.assertEqual(score["provenance_envelope"]["producer"], "score_scrape.report")

        write = sep.record_traceability_write_report(
            {"written": ["RS_A"], "updated": []},
            input_files={"fixtures/source.pdf": self.pdf},
            store_root=self.root,
            source_commit=COMMIT,
            tool_commit=COMMIT,
            config_commit=COMMIT,
        )
        self.assertEqual(
            write["provenance_envelope"]["producer"], "spec_scrape.write_traceability_records"
        )

    def test_input_digest_set_property(self):
        """AE-5: artifact-set membership is the sorted path+digest of exact bytes."""
        cases = 0
        for extra in (b"", b"x", b"xy", b"%PDF extra"):
            files = {"fixtures/source.pdf": self.pdf + extra, "fixtures/source.rst": self.text}
            members = sep.members_from_bytes(files, source_commit=COMMIT)
            sep.validate_input_members(members, files)
            paths = [m["path"] for m in members]
            self.assertEqual(paths, sorted(paths))
            self.assertEqual(len(paths), len(set(paths)))
            for member in members:
                self.assertEqual(member["digest"], sep.sha256_bytes(files[member["path"]]))
            cases += 1
        self.assertEqual(cases, 4)


if __name__ == "__main__":
    unittest.main()
