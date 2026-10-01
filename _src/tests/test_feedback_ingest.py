#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_feedback_ingest.py — form validation, envelope, SHA-256 receipt, queue files.

Acceptance oracle for the user-feedback ingest workflow. Pre-change baseline is
``29aeadfbd34c84d7f02951f33b4383217c046330`` (module absent). The candidate is
this worktree.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import random
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "_src"
TOOLS = SRC / "tools"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(TOOLS))

import feedback_ingest as fi  # noqa: E402
import lib_docmodel as dm  # noqa: E402

PRE_CHANGE = "29aeadfbd34c84d7f02951f33b4383217c046330"
TEMPLATE = SRC / "templates" / "page.html.tmpl"
JS_CLIENT = ROOT / "review_request.js"

VALID = {
    "target_id": "AUTOSAR/AP/record/TSyncUserGuide",
    "category": "typo",
    "severity": "editorial",
    "title": "Missing comma in TSync lead",
    "description": "The lead sentence omits a comma after the module name.",
    "proposed_change": "- old\n+ new",
    "submitter": "qa-reviewer",
}


def _envelope(**overrides):
    payload = dict(VALID)
    payload.update(overrides)
    return fi.build_envelope(
        payload,
        feedback_id=overrides.get("feedback_id") or "uf-12345678-1234-1234-1234-1234567890ab",
        submitted_at=overrides.get("submitted_at") or "2026-09-29T20:48:32Z",
        status=overrides.get("status") or "queued",
    )


class FormValidationTests(unittest.TestCase):
    def test_valid_form_normalizes_german_labels(self):
        fields = fi.validate_form({
            **VALID,
            "category": "Typo",
            "severity": "Editorial",
        })
        self.assertEqual(fields["category"], "typo")
        self.assertEqual(fields["severity"], "editorial")

    def test_missing_title_is_rejected(self):
        with self.assertRaises(fi.FeedbackIngestError) as ctx:
            fi.validate_form({**VALID, "title": "  "})
        self.assertIn("title", str(ctx.exception))

    def test_short_description_is_rejected(self):
        with self.assertRaises(fi.FeedbackIngestError):
            fi.validate_form({**VALID, "description": "too short"})

    def test_unknown_category_is_rejected(self):
        with self.assertRaises(fi.FeedbackIngestError) as ctx:
            fi.validate_form({**VALID, "category": "sabotage"})
        self.assertIn("category", str(ctx.exception))

    def test_control_characters_are_rejected(self):
        with self.assertRaises(fi.FeedbackIngestError):
            fi.validate_form({**VALID, "title": "bad\x00title-here"})

    def test_optional_submitter_and_proposed_change(self):
        fields = fi.validate_form({
            "target_id": VALID["target_id"],
            "category": "Unklarheit",
            "severity": "Minor",
            "title": "Please clarify bound",
            "description": "The upper bound of retry is not stated.",
        })
        self.assertEqual(fields["proposed_change"], "")
        self.assertEqual(fields["submitter"], "")
        self.assertEqual(fields["category"], "unklarheit")
        self.assertEqual(fields["severity"], "minor")


class EnvelopeAndReceiptTests(unittest.TestCase):
    def test_envelope_schema_and_receipt_sha256(self):
        env = _envelope()
        self.assertEqual(env["schema"], "user-feedback-envelope@v1")
        self.assertTrue(fi.verify_receipt(env))
        body = {k: v for k, v in env.items() if k != "receipt_hash"}
        expected = hashlib.sha256(fi.canonical_json_bytes(body)).hexdigest()
        self.assertEqual(env["receipt_hash"], expected)
        self.assertEqual(len(env["receipt_hash"]), 64)

    def test_receipt_hash_excludes_its_own_field(self):
        env = _envelope()
        mutated = dict(env)
        mutated["receipt_hash"] = "0" * 64
        self.assertFalse(fi.verify_receipt(mutated))

    def test_description_mutation_breaks_receipt(self):
        env = _envelope()
        tampered = dict(env)
        tampered["description"] = env["description"] + " (tampered)"
        self.assertFalse(fi.verify_receipt(tampered))
        self.assertTrue(fi.verify_receipt(env))

    def test_unicode_canonical_json_is_stable(self):
        env = _envelope(title="Übersetzung 日本語", description="Die Beschreibung enthält Unicode und Umlaute.")
        self.assertTrue(fi.verify_receipt(env))
        again = fi.compute_receipt_hash({k: v for k, v in env.items() if k != "receipt_hash"})
        self.assertEqual(env["receipt_hash"], again)


class QueueFileTests(unittest.TestCase):
    def test_queue_file_creation_is_atomic_and_named(self):
        env = _envelope()
        with tempfile.TemporaryDirectory() as tmp:
            path = fi.write_queue_file(env, Path(tmp))
            self.assertTrue(path.is_file())
            self.assertEqual(path.name, "20260929T204832Z-uf-12345678-1234-1234-1234-1234567890ab.json")
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded, env)
            self.assertTrue(fi.verify_receipt(loaded))

    def test_identical_replay_is_idempotent(self):
        env = _envelope()
        with tempfile.TemporaryDirectory() as tmp:
            first = fi.write_queue_file(env, Path(tmp))
            second = fi.write_queue_file(env, Path(tmp))
            self.assertEqual(first, second)
            self.assertEqual(len(list(Path(tmp).glob("*.json"))), 1)

    def test_conflicting_envelope_same_id_is_rejected(self):
        env = _envelope()
        other = _envelope(title="A completely different summary")
        with tempfile.TemporaryDirectory() as tmp:
            fi.write_queue_file(env, Path(tmp))
            with self.assertRaises(fi.FeedbackIngestError) as ctx:
                fi.write_queue_file(other, Path(tmp))
            self.assertIn("conflicting", str(ctx.exception))
            loaded = json.loads((Path(tmp) / fi.queue_filename(env)).read_text(encoding="utf-8"))
            self.assertEqual(loaded["title"], env["title"])

    def test_script_payload_is_stored_as_data(self):
        env = _envelope(
            title="See attached markup",
            description="<script>alert(1)</script> still a documentation issue.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = fi.write_queue_file(env, Path(tmp))
            raw = path.read_text(encoding="utf-8")
            self.assertIn("<script>alert(1)</script>", json.loads(raw)["description"])
            self.assertTrue(fi.verify_receipt(json.loads(raw)))


class HttpIngestTests(unittest.TestCase):
    def test_http_post_writes_queue_and_returns_receipt(self):
        previous = fi.FeedbackHandler.queue_dir
        with tempfile.TemporaryDirectory() as tmp:
            fi.FeedbackHandler.queue_dir = Path(tmp)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), fi.FeedbackHandler)
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = httpd.server_address[:2]
                conn = http.client.HTTPConnection(host, port, timeout=5)
                body = json.dumps(VALID).encode("utf-8")
                conn.request("POST", "/api/user-feedback", body=body, headers={"Content-Type": "application/json"})
                res = conn.getresponse()
                payload = json.loads(res.read().decode("utf-8"))
                conn.close()
                self.assertEqual(res.status, 201, payload)
                self.assertTrue(payload["ok"])
                self.assertTrue(payload["feedback_id"].startswith("uf-"))
                self.assertEqual(len(payload["receipt_hash"]), 64)
                self.assertEqual(payload["status"], "submitted")
                files = list(Path(tmp).glob("*.json"))
                self.assertEqual(len(files), 1)
                stored = json.loads(files[0].read_text(encoding="utf-8"))
                self.assertTrue(fi.verify_receipt(stored))
                self.assertEqual(stored["receipt_hash"], payload["receipt_hash"])
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=5)
                fi.FeedbackHandler.queue_dir = previous

    def test_http_rejects_invalid_category(self):
        previous = fi.FeedbackHandler.queue_dir
        with tempfile.TemporaryDirectory() as tmp:
            fi.FeedbackHandler.queue_dir = Path(tmp)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), fi.FeedbackHandler)
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = httpd.server_address[:2]
                conn = http.client.HTTPConnection(host, port, timeout=5)
                body = json.dumps({**VALID, "category": "nope"}).encode("utf-8")
                conn.request("POST", "/api/user-feedback", body=body, headers={"Content-Type": "application/json"})
                res = conn.getresponse()
                payload = json.loads(res.read().decode("utf-8"))
                conn.close()
                self.assertEqual(res.status, 400)
                self.assertFalse(payload["ok"])
                self.assertEqual(list(Path(tmp).glob("*.json")), [])
            finally:
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=5)
                fi.FeedbackHandler.queue_dir = previous


class TemplateAndClientTests(unittest.TestCase):
    def test_template_wires_feedback_trigger(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn('data-feedback-open', text)
        self.assertIn("Feedback", text)
        self.assertIn("%(review_request_js)s", text)
        page = {
            "title": "Feedback",
            "file": "test.html",
            "body_class": "",
            "nav_html": "",
            "main_lead": "",
            "footer": "default",
            "main": [{"t": "html", "html": "<p>x</p>"}],
        }
        html = dm.render_page(page, {"default": ""}, text)
        self.assertIn("data-feedback-open", html)
        self.assertIn("review_request.js", html)

    def test_js_canonical_receipt_matches_python(self):
        env = _envelope()
        payload = {
            "target_id": env["target_id"],
            "category": env["category"],
            "severity": env["severity"],
            "title": env["title"],
            "description": env["description"],
            "proposed_change": env["proposed_change"],
            "submitter": env["submitter"],
        }
        script = (
            "const fb = require(process.env.FB_JS);"
            "const payload = JSON.parse(process.env.FB_PAYLOAD);"
            "const env = fb.buildFeedbackEnvelope(payload, {"
            "feedback_id: process.env.FB_ID, submitted_at: process.env.FB_TS, status: 'queued'"
            "});"
            "process.stdout.write(JSON.stringify(env));"
        )
        env_vars = dict(os.environ)
        env_vars.update({
            "FB_JS": str(JS_CLIENT),
            "FB_PAYLOAD": json.dumps(payload, ensure_ascii=False),
            "FB_ID": env["feedback_id"],
            "FB_TS": env["submitted_at"],
        })
        proc = subprocess.run(
            ["node", "-e", script],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=20,
            env=env_vars,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        js_env = json.loads(proc.stdout)
        self.assertEqual(js_env["receipt_hash"], env["receipt_hash"])
        self.assertEqual(js_env["schema"], "user-feedback-envelope@v1")
        self.assertTrue(fi.verify_receipt(js_env))

    def test_existing_review_request_exports_still_present(self):
        script = (
            "const fb = require(process.env.FB_JS);"
            "if (typeof fb.generateUUIDv7 !== 'function') process.exit(3);"
            "if (typeof fb.buildConfirmedPackage !== 'function') process.exit(4);"
            "if (typeof fb.buildFeedbackEnvelope !== 'function') process.exit(5);"
            "process.stdout.write('ok');"
        )
        proc = subprocess.run(
            ["node", "-e", script],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=20,
            env={**os.environ, "FB_JS": str(JS_CLIENT)},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "ok")


class AdversarialEvidenceTests(unittest.TestCase):
    """AE-1..AE-5 for receipt hashing, identity, and queue cardinality."""

    def test_ae3_module_absent_on_baseline_receipt_green_here(self):
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{PRE_CHANGE}:_src/tools/feedback_ingest.py"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(listed.returncode, 0)
        env = _envelope()
        tampered = dict(env)
        tampered["description"] = env["description"] + " x"
        self.assertFalse(fi.verify_receipt(tampered))
        self.assertTrue(fi.verify_receipt(env))

    def test_ae4_adjacent_severity_changes_receipt(self):
        editorial = _envelope(severity="editorial")
        minor = fi.build_envelope(
            {**VALID, "severity": "minor"},
            feedback_id=editorial["feedback_id"],
            submitted_at=editorial["submitted_at"],
            status="queued",
        )
        self.assertTrue(fi.verify_receipt(editorial))
        self.assertTrue(fi.verify_receipt(minor))
        self.assertNotEqual(editorial["receipt_hash"], minor["receipt_hash"])
        self.assertEqual(editorial["feedback_id"], minor["feedback_id"])

    def test_ae4_adjacent_optional_proposed_change_normalizes(self):
        with_empty = _envelope(proposed_change="")
        omitted = fi.build_envelope(
            {
                "target_id": VALID["target_id"],
                "category": VALID["category"],
                "severity": VALID["severity"],
                "title": VALID["title"],
                "description": VALID["description"],
                "submitter": VALID["submitter"],
            },
            feedback_id=with_empty["feedback_id"],
            submitted_at=with_empty["submitted_at"],
            status="queued",
        )
        self.assertEqual(with_empty["receipt_hash"], omitted["receipt_hash"])
        present = fi.build_envelope(
            {**VALID, "proposed_change": "use a markdown diff"},
            feedback_id=with_empty["feedback_id"],
            submitted_at=with_empty["submitted_at"],
            status="queued",
        )
        self.assertNotEqual(with_empty["receipt_hash"], present["receipt_hash"])

    def test_ae5_unique_queue_files_and_receipts(self):
        rng = random.Random(20260929)
        seen_ids = set()
        seen_hashes = set()
        severities = ("blocker", "major", "minor", "editorial")
        categories = list(fi.CATEGORIES)
        with tempfile.TemporaryDirectory() as tmp:
            queue = Path(tmp)
            for i in range(40):
                payload = {
                    **VALID,
                    "title": f"Case {i:02d} unique title",
                    "description": f"Generated description number {i:02d} with enough text.",
                    "severity": rng.choice(severities),
                    "category": rng.choice(categories),
                }
                env = fi.build_envelope(
                    payload,
                    feedback_id="uf-%08x-1234-1234-1234-1234567890ab" % i,
                    submitted_at="2026-09-29T20:48:%02dZ" % (i % 60),
                    status="queued",
                )
                path = fi.write_queue_file(env, queue)
                self.assertTrue(path.is_file())
                seen_ids.add(env["feedback_id"])
                seen_hashes.add(env["receipt_hash"])
                self.assertTrue(fi.verify_receipt(json.loads(path.read_text(encoding="utf-8"))))
            files = list(queue.glob("*.json"))
            self.assertEqual(len(files), 40)
            self.assertEqual(len(seen_ids), 40)
            self.assertEqual(len(seen_hashes), 40)
            self.assertEqual(len(files), len({p.name for p in files}))


if __name__ == "__main__":
    unittest.main()
