#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the universal mutation audit ledger (`mutation-audit-ledger@v1`).

Covers recording, reading, input hashing, receipt integrity, append-only
prefix preservation, missing-input handling, and HTML rendering.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import mutation_ledger as ml  # noqa: E402

EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


class LedgerCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "_src" / "output").mkdir(parents=True)
        (self.root / "docs" / "evidence").mkdir(parents=True)
        self.primary, self.mirror = ml.ledger_paths(self.root)

    def record(self, action="test-action", operator="tester", details=None, **kwargs):
        kwargs.setdefault("root", self.root)
        return ml.record_mutation(action, operator, details if details is not None else {"n": 1}, **kwargs)


class TestRecordAndRead(LedgerCase):
    def test_record_creates_primary_and_identical_mirror(self):
        entry = self.record()
        self.assertEqual(entry["schema"], ml.SCHEMA)
        self.assertEqual(entry["action"], "test-action")
        self.assertEqual(entry["operator"], "tester")
        self.assertEqual(entry["status"], "ok")
        self.assertTrue(self.primary.is_file())
        self.assertTrue(self.mirror.is_file())
        self.assertEqual(self.primary.read_bytes(), self.mirror.read_bytes())
        self.assertTrue(self.primary.read_bytes().endswith(b"\n"))

    def test_read_returns_appended_entries_oldest_first(self):
        first = self.record(action="one", details={"k": "a"})
        second = self.record(action="two", details={"k": "b"})
        entries = ml.read_mutation_entries(root=self.root)
        self.assertEqual([e["action"] for e in entries], ["one", "two"])
        self.assertEqual(entries[0]["entry_id"], first["entry_id"])
        self.assertEqual(entries[1]["entry_id"], second["entry_id"])

    def test_limit_keeps_most_recent_in_chronological_order(self):
        self.record(action="a")
        self.record(action="b")
        self.record(action="c")
        entries = ml.read_mutation_entries(limit=2, root=self.root)
        self.assertEqual([e["action"] for e in entries], ["b", "c"])

    def test_empty_ledger_reads_as_empty_list(self):
        self.assertEqual(ml.read_mutation_entries(root=self.root), [])

    def test_failed_status_is_error(self):
        entry = self.record(success=False, details={"reason": "rejected"})
        self.assertEqual(entry["status"], "error")

    def test_action_and_operator_must_be_non_empty(self):
        with self.assertRaises(ml.LedgerError):
            self.record(action="  ")
        with self.assertRaises(ml.LedgerError):
            ml.record_mutation("ok", "  ", {}, root=self.root)


class TestHashing(LedgerCase):
    def test_input_digest_pins_file_bytes(self):
        path = self.root / "in.bin"
        path.write_bytes(b"alpha")
        first = self.record(inputs=[path], details="hash-1")
        digest = first["input_digests"][0]["sha256"]
        self.assertEqual(digest, hashlib.sha256(b"alpha").hexdigest())
        path.write_bytes(b"alpha!")
        second = self.record(action="again", inputs=[path], details="hash-2")
        self.assertNotEqual(first["input_digests"][0]["sha256"], second["input_digests"][0]["sha256"])

    def test_missing_input_is_not_hashed_as_empty_file(self):
        """Adjacent: a missing path must not collide with the empty-file digest."""
        missing = self.root / "gone.txt"
        entry = self.record(inputs=[missing], details="missing")
        row = entry["input_digests"][0]
        self.assertTrue(row["missing"])
        self.assertIsNone(row["sha256"])
        self.assertNotEqual(row.get("sha256"), EMPTY_SHA256)

    def test_empty_file_hash_is_the_empty_digest(self):
        path = self.root / "empty.txt"
        path.write_bytes(b"")
        entry = self.record(inputs=path, details="empty")
        self.assertEqual(entry["input_digests"][0]["sha256"], EMPTY_SHA256)
        self.assertNotIn("missing", entry["input_digests"][0])

    def test_output_summary_records_size_and_digest(self):
        out = self.root / "out.json"
        out.write_text('{"ok": true}\n', encoding="utf-8")
        entry = self.record(outputs=[out], details="out")
        summary = entry["output_summary"][0]
        self.assertEqual(summary["size"], out.stat().st_size)
        self.assertEqual(summary["sha256"], ml.sha256_file(out))
        self.assertIn("mtime", summary)


class TestReceiptIntegrity(LedgerCase):
    def test_receipt_covers_payload_excluding_itself(self):
        entry = self.record(details={"payload": True})
        self.assertTrue(ml.verify_receipt(entry))
        self.assertEqual(entry["receipt_sha256"], ml.compute_receipt_sha256(entry))
        body = {k: v for k, v in entry.items() if k != "receipt_sha256"}
        expected = hashlib.sha256(
            json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.assertEqual(entry["receipt_sha256"], expected)

    def test_tampered_receipt_is_rejected_on_read(self):
        """AE-3: rewriting status after the fact fails receipt verification."""
        self.record(details={"ok": True})
        lines = self.primary.read_text(encoding="utf-8").splitlines()
        tampered = json.loads(lines[0])
        tampered["status"] = "error"
        # Keep the original receipt — the payload no longer matches.
        self.assertFalse(ml.verify_receipt(tampered))
        self.primary.write_text(json.dumps(tampered, ensure_ascii=False) + "\n", encoding="utf-8")
        self.mirror.write_text(self.primary.read_text(encoding="utf-8"), encoding="utf-8")
        self.assertEqual(ml.read_mutation_entries(root=self.root), [])

    def test_malformed_line_does_not_hide_later_valid_entry(self):
        good = self.record(action="kept")
        raw = self.primary.read_bytes()
        poisoned = b"{not json\n" + raw
        self.primary.write_bytes(poisoned)
        self.mirror.write_bytes(poisoned)
        entries = ml.read_mutation_entries(root=self.root)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["entry_id"], good["entry_id"])


class TestAppendOnlyAndDataLoss(LedgerCase):
    def test_second_append_preserves_existing_bytes(self):
        self.record(action="first")
        before = self.primary.read_bytes()
        self.record(action="second")
        after = self.primary.read_bytes()
        self.assertTrue(after.startswith(before))
        self.assertGreater(len(after), len(before))
        self.assertEqual(after, self.mirror.read_bytes())

    def test_read_falls_back_to_mirror_when_primary_is_gone(self):
        entry = self.record(action="survives")
        self.primary.unlink()
        entries = ml.read_mutation_entries(root=self.root)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["entry_id"], entry["entry_id"])

    def test_unique_entry_ids_across_a_sequence(self):
        """AE-5: append sequence has unique identities and verifying receipts."""
        ids = []
        for index in range(12):
            entry = self.record(action=f"seq-{index}", details={"i": index})
            ids.append(entry["entry_id"])
            self.assertTrue(ml.verify_receipt(entry))
        self.assertEqual(len(ids), len(set(ids)))
        entries = ml.read_mutation_entries(root=self.root)
        self.assertEqual(len(entries), 12)
        self.assertEqual([e["action"] for e in entries], [f"seq-{i}" for i in range(12)])
        self.assertTrue(all(ml.verify_receipt(e) for e in entries))


class TestRender(LedgerCase):
    def test_page_uses_reports_domain_shell_and_table(self):
        self.record(action="user-feedback-received", operator="demo", details={"n": 1})
        out = self.root / "mutation-ledger.html"
        html_text = ml.render_mutation_ledger_page(root=self.root, out_path=out)
        self.assertTrue(out.is_file())
        self.assertEqual(html_text, out.read_text(encoding="utf-8"))
        self.assertIn('data-domain="reports"', html_text)
        self.assertIn('aria-current="page"', html_text)
        self.assertIn("user-feedback-received", html_text)
        self.assertIn("Timestamp", html_text)
        self.assertIn("Action", html_text)
        self.assertIn("Operator", html_text)
        self.assertIn("Target Files", html_text)
        self.assertIn("Receipt Digest", html_text)
        self.assertIn("class=\"shell\"", html_text)
        self.assertIn('href="process.html"', html_text)
        self.assertIn('href="build-reports.html"', html_text)

    def test_error_badge_and_empty_state(self):
        empty = ml.render_mutation_ledger_html([])
        self.assertIn("Keine Mutation-Einträge", empty)
        failed = self.record(action="curation-ingest", success=False, details={})
        html_text = ml.render_mutation_ledger_html([failed])
        self.assertIn("ml-badge-err", html_text)
        self.assertIn("FEHLER", html_text)

    def test_html_escapes_operator_and_action(self):
        entry = self.record(action="a<b>", operator='x"y', details={"t": "<script>"})
        html_text = ml.render_mutation_ledger_html([entry])
        tbody = html_text.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
        self.assertNotIn("<script>", tbody)
        self.assertIn("a&lt;b&gt;", tbody)
        self.assertIn("x&quot;y", tbody)


class TestHooks(unittest.TestCase):
    def test_feedback_loop_records_invalidation_and_regeneration(self):
        text = (TOOLS / "feedback_loop.py").read_text(encoding="utf-8")
        self.assertIn('"feedback-loop-invalidation"', text)
        self.assertIn('"feedback-loop-regeneration"', text)

    def test_curation_ingest_records_curation_ingest(self):
        text = (TOOLS / "curation_ingest.py").read_text(encoding="utf-8")
        self.assertIn('"curation-ingest"', text)

    def test_serve_records_feedback_and_curate_routes(self):
        text = (TOOLS.parent / "serve.py").read_text(encoding="utf-8")
        self.assertIn('"user-feedback-received"', text)
        self.assertIn('"curation-decision-applied"', text)
    def test_module_did_not_exist_on_the_unstarted_branch_tip(self):
        """AE-2/AE-3: the ledger module is new on this candidate; import is the green side."""
        self.assertTrue((TOOLS / "mutation_ledger.py").is_file())
        self.assertEqual(ml.SCHEMA, "mutation-audit-ledger@v1")
        self.assertTrue(callable(ml.record_mutation))
        self.assertTrue(callable(ml.read_mutation_entries))
        self.assertTrue(callable(ml.render_mutation_ledger_page))


if __name__ == "__main__":
    unittest.main()
