#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hermetic tests for the closed AI-commentary feedback loop.

The suite never writes the real ``_src`` tree. A sentinel from that tree is
compared at the end so a path bug cannot silently regenerate the corpus.
"""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REAL_SRC = ROOT / "_src"
TOOL = REAL_SRC / "tools" / "feedback_loop.py"
SENTINEL = REAL_SRC / "ai" / "traces" / "modules" / "com" / "main_01.json"
SENTINEL_BYTES = SENTINEL.read_bytes()
REAL_MUTATION = REAL_SRC / "output" / "mutation-audit-ledger.jsonl"
REAL_MIRROR = ROOT / "docs" / "evidence" / "mutation-audit-ledger.jsonl"
REAL_RTE_PAGE = ROOT / "classic" / "rte.html"
REAL_SCORE_PAGE = ROOT / "score" / "core.html"
REAL_AI_CLASSIC = REAL_SRC / "content" / "ai" / "classic"
REAL_AI_SCORE = REAL_SRC / "content" / "ai" / "score"


def _bytes_or_none(path: Path):
    return path.read_bytes() if path.is_file() else None


REAL_MUTATION_BYTES = _bytes_or_none(REAL_MUTATION)
REAL_MIRROR_BYTES = _bytes_or_none(REAL_MIRROR)
REAL_RTE_BYTES = _bytes_or_none(REAL_RTE_PAGE)
REAL_SCORE_BYTES = _bytes_or_none(REAL_SCORE_PAGE)
REAL_AI_CLASSIC_EXISTS = REAL_AI_CLASSIC.exists()
REAL_AI_SCORE_EXISTS = REAL_AI_SCORE.exists()

FROZEN = datetime.datetime(2026, 9, 29, 22, 48, 22, tzinfo=datetime.timezone.utc)
RECORD = "SWS_CM_00701"
PREFIX = "SWS_CM_007010"
NEAR = "SWS_CM_00701_04"
OTHER = "SWS_CORE_00001"
SCORE = "ECLIPSE/S-CORE/component/score_platform.tools.format"


def _load():
    spec = importlib.util.spec_from_file_location("feedback_loop_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fl = _load()


def _sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _tree(root: Path) -> dict:
    found = {}
    if not root.exists():
        return found
    for path in root.rglob("*"):
        if path.is_file():
            found[str(path.relative_to(root))] = path.read_bytes()
    return found


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _json(path: Path, obj) -> None:
    _write(path, json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


def _record(text: str = "Method to update the event cache.") -> dict:
    return {
        "id": RECORD,
        "blocks": [
            {"t": "html", "html": '<h3 class="recname"><span class="kind">function</span> GetNewSamples</h3>'},
            {"t": "html", "html": '<div class="desc"><p>%s</p></div>' % text},
        ],
    }


def _trace(fragment: str, record_id: str, digest: str, **extra) -> dict:
    base = {
        "fragment": fragment,
        "seite": "classes/demo.html",
        "art": "usage",
        "elemente": [record_id],
        "zitate": [record_id],
        "quellen": ["dok-1"],
        "wissen": [{"aussage": "bestehend", "quelle": "dok-1", "fundstelle": record_id}],
        "annahmen": [{"annahme": "a", "begruendung": "b"}],
        "prompt": None,
        "modell": None,
        "policy_version": 1,
        "laeufe": [{
            "datum": "2026-08-01",
            "modell": None,
            "policy_version": 1,
            "transkript": "legacy",
        }],
        "diagramme": {"content/ai/classes/demo/keep.dot": {"entscheidung": "keep"}},
        "status": "aktuell",
        "elemente_stand": {record_id: digest},
        "curator_note": "keep-me",
    }
    base.update(extra)
    return base


def _html(citation: str) -> str:
    return (
        '<div class="ai usage"><p class="ai-note">alt</p>'
        "<p>Alttext. Beleg: [%s].</p></div>" % citation
    )


class LoopCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = Path(self.tmp.name)
        self.pages = []
        self.record_path = self.src / "spec" / "records" / "SWS_CM" / ("%s.json" % RECORD)
        _json(self.record_path, _record("version-one"))
        self.v1 = self.record_path.read_bytes()
        self.digest_v1 = _sha1(self.v1)
        _json(self.record_path, _record("version-two"))
        self.v2 = self.record_path.read_bytes()
        self.digest_v2 = _sha1(self.v2)
        self.assertNotEqual(self.digest_v1, self.digest_v2)
        other = self.src / "spec" / "records" / "SWS_CORE" / ("%s.json" % OTHER)
        _json(other, {"id": OTHER, "blocks": []})
        self.other_digest = _sha1(other.read_bytes())
        _json(self.src / "ai" / "policy.json", {"version": 7, "modell": {"erklaerungen": "builtin-test-model"}})
        _json(self.src / "site.json", {"sprachen": {"ziele": ["en", "nl"]}})
        _json(self.src / "i18n" / "segments.de.json", {"aaaaaaaaaaaa": {"m": "bleibt", "n": 3, "ctx": ["chrome"]}})
        _json(self.src / "i18n" / "en" / "segments.json", {"aaaaaaaaaaaa": "keep-en"})
        _json(self.src / "i18n" / "nl" / "segments.json", {"aaaaaaaaaaaa": "keep-nl"})
        _json(self.src / "i18n" / "es" / "segments.json", {"aaaaaaaaaaaa": "keep-es"})
        self._plant()

    def tearDown(self):
        self.tmp.cleanup()

    def _plant(self):
        specs = {
            "classes/demo/rec_hit.html": (RECORD, self.digest_v1, _html(RECORD)),
            "classes/demo/rec_html_only.html": (
                OTHER,
                self.other_digest,
                _html(RECORD),
            ),
            "classes/demo/rec_%s.html" % PREFIX: (PREFIX, "b" * 40, _html(PREFIX)),
            "classes/demo/rec_%s.html" % NEAR: ("SWS_CM_00999", "c" * 40, _html("SWS_CM_00999")),
            "classes/demo/rec_other.html": (OTHER, self.other_digest, _html(OTHER)),
        }
        # html-only trace does not list the changed record, but keeps provenance.
        for rel, (record_id, digest, html) in specs.items():
            fragment = "content/ai/" + rel
            _write(self.src / fragment, html)
            extra = {}
            if rel.endswith("rec_html_only.html"):
                extra = {
                    "elemente": [],
                    "zitate": [],
                    "elemente_stand": {},
                    "seite": None,
                }
            _json(
                self.src / "ai" / "traces" / (rel[:-5] + ".json"),
                _trace(fragment, record_id, digest, **extra),
            )
        # Trace without an HTML file must not grow a new fragment.
        missing = "content/ai/classes/demo/rec_missing.html"
        _json(
            self.src / "ai" / "traces" / "classes" / "demo" / "rec_missing.json",
            _trace(missing, RECORD, self.digest_v1),
        )
        _json(
            self.src / "spec" / "feedback-inbox" / "fb-7.json",
            {
                "schema": "ai-commentary-feedback@v1",
                "feedback_id": "fb-7",
                "status": "accepted",
                "kind": "user-feedback",
                "record_id": RECORD,
                "note": "Bitte den Hinweis nachziehen.",
            },
        )
        _json(
            self.src / "spec" / "curation-queue" / "open" / "cur-7.json",
            {
                "feedback_id": "cur-7",
                "status": "accepted",
                "kind": "curator-decision",
                "record_id": RECORD,
                "actor_role": "curator",
                "decision": {"outcome": "accepted", "actor_role": "curator", "rationale": "belegt"},
            },
        )

    def _engine(self, **kwargs):
        kwargs.setdefault("now", lambda: FROZEN)
        kwargs.setdefault("generate_fn", self.pages.append)
        kwargs.setdefault("invoke_generate", False)
        return fl.FeedbackLoop(self.src, **kwargs)

    def _hit_trace(self) -> dict:
        path = self.src / "ai" / "traces" / "classes" / "demo" / "rec_hit.json"
        return json.loads(path.read_text(encoding="utf-8"))


class CausalInvalidationTests(LoopCase):
    def test_modified_record_flags_only_real_citations(self):
        before = _tree(self.src)
        report = self._engine().run(all_pending=True, regenerate=False)
        self.assertTrue(report["ok"])
        flagged = set(report["flagged"])
        self.assertIn("content/ai/classes/demo/rec_hit.html", flagged)
        self.assertIn("content/ai/classes/demo/rec_html_only.html", flagged)
        self.assertIn("content/ai/classes/demo/rec_missing.html", flagged)
        for untouched in (
            "content/ai/classes/demo/rec_%s.html" % PREFIX,
            "content/ai/classes/demo/rec_%s.html" % NEAR,
            "content/ai/classes/demo/rec_other.html",
        ):
            self.assertNotIn(untouched, flagged)

        hit = self._hit_trace()
        self.assertEqual(fl.invalidation_schema_errors(hit, RECORD), [])
        self.assertEqual(hit["curator_note"], "keep-me")
        self.assertEqual(hit["wissen"][0]["aussage"], "bestehend")
        self.assertEqual(hit["status"], "veraltet")

        html_only = json.loads(
            (self.src / "ai" / "traces" / "classes" / "demo" / "rec_html_only.json").read_text(encoding="utf-8")
        )
        self.assertEqual(html_only["curator_note"], "keep-me")
        self.assertTrue(html_only["stale"])
        self.assertIn(RECORD, html_only["elemente"])

        after = _tree(self.src)
        for rel in (
            "content/ai/classes/demo/rec_hit.html",
            "content/ai/classes/demo/rec_%s.html" % PREFIX,
            "content/ai/classes/demo/rec_%s.html" % NEAR,
            "content/ai/classes/demo/rec_other.html",
            "spec/records/SWS_CM/%s.json" % RECORD,
            "spec/feedback-inbox/fb-7.json",
        ):
            self.assertEqual(after[rel], before[rel], rel)
        self.assertFalse((self.src / "content" / "ai" / "classes" / "demo" / "rec_missing.html").exists())
        # A second pending scan must not rewrite the flagged traces again.
        stable = (self.src / "ai" / "traces" / "classes" / "demo" / "rec_hit.json").read_bytes()
        again = self._engine().run(all_pending=True, regenerate=False)
        self.assertEqual(again["triggers"], [])
        self.assertEqual(
            (self.src / "ai" / "traces" / "classes" / "demo" / "rec_hit.json").read_bytes(),
            stable,
        )

    def test_malformed_trace_is_not_overwritten(self):
        broken = self.src / "ai" / "traces" / "classes" / "demo" / "rec_broken.json"
        html = self.src / "content" / "ai" / "classes" / "demo" / "rec_broken.html"
        _write(broken, "{not-json")
        _write(html, _html(RECORD))
        before_trace = broken.read_bytes()
        before_html = html.read_bytes()
        report = self._engine().run(record_id=RECORD)
        self.assertIn("content/ai/classes/demo/rec_broken.html", report["flagged"])
        self.assertNotIn("content/ai/classes/demo/rec_broken.html", report["regenerated"])
        self.assertEqual(broken.read_bytes(), before_trace)
        self.assertEqual(html.read_bytes(), before_html)
        self.assertFalse(report["events"][0]["complete"])

    def test_missing_record_file_is_not_treated_as_a_change(self):
        # Accepted decisions are a separate trigger. This test isolates hash
        # drift: a stand hash with no record file must not wipe commentaries.
        self.record_path.unlink()
        for rel in ("spec/feedback-inbox", "spec/curation-queue"):
            path = self.src / rel
            if path.exists():
                for child in path.rglob("*"):
                    if child.is_file():
                        child.unlink()
        before = _tree(self.src)
        report = self._engine().run(all_pending=True, regenerate=False)
        self.assertEqual(report["flagged"], [])
        self.assertEqual(report["triggers"], [])
        self.assertEqual(_tree(self.src), before)
        self.assertFalse(self.record_path.exists())

    def test_explicit_record_id_does_not_create_a_spec_file(self):
        self.record_path.unlink()
        report = self._engine().run(record_id=RECORD, regenerate=False)
        self.assertIn("content/ai/classes/demo/rec_hit.html", report["flagged"])
        self.assertFalse(self.record_path.exists())

    def test_score_id_does_not_match_a_longer_id(self):
        fragment = "content/ai/classes/demo/rec_score.html"
        longer = SCORE + ".extra"
        _write(self.src / fragment, '<div class="ai"><p class="ai-note">n</p><p>[%s]</p></div>' % SCORE)
        _write(
            self.src / "content" / "ai" / "classes" / "demo" / "rec_score_longer.html",
            '<div class="ai"><p class="ai-note">n</p><p>[%s]</p></div>' % longer,
        )
        report = self._engine().run(record_id=SCORE, regenerate=False)
        self.assertEqual(report["flagged"], [fragment])
        self.assertFalse((self.src / "spec" / "records").joinpath("ECLIPSE").exists())

    def test_token_boundary_unit(self):
        self.assertTrue(fl._contains_id("[%s]" % RECORD, RECORD))
        self.assertFalse(fl._contains_id(PREFIX, RECORD))
        self.assertFalse(fl._contains_id("rec_%s.html" % NEAR, RECORD))
        self.assertFalse(fl._contains_id(SCORE + ".extra", SCORE))
        self.assertTrue(fl._contains_id(SCORE, SCORE))


class RegenerationTests(LoopCase):
    def test_regeneration_writes_schema_valid_trace_and_keeps_history(self):
        spec_before = self.record_path.read_bytes()
        feedback_before = (self.src / "spec" / "feedback-inbox" / "fb-7.json").read_bytes()
        old_html = (self.src / "content" / "ai" / "classes" / "demo" / "rec_hit.html").read_bytes()
        report = self._engine().run(feedback_id="fb-7")
        self.assertTrue(report["ok"])
        self.assertIn("content/ai/classes/demo/rec_hit.html", report["regenerated"])
        trace = self._hit_trace()
        self.assertEqual(fl.trace_schema_errors(trace, RECORD), [])
        self.assertEqual(trace["modell"], "builtin-test-model")
        self.assertEqual(trace["modell_meta"]["synthesis"], "builtin-contextual")
        self.assertEqual(trace["policy_version"], 7)
        self.assertEqual(trace["trigger"]["feedback_id"], "fb-7")
        self.assertEqual(trace["trigger"]["timestamp"], "2026-09-29T22:48:22Z")
        self.assertIn(RECORD, trace["prompt"])
        self.assertEqual(trace["curator_note"], "keep-me")
        self.assertEqual(trace["quellen"], ["dok-1"])
        self.assertEqual(trace["annahmen"][0]["annahme"], "a")
        self.assertEqual(trace["diagramme"]["content/ai/classes/demo/keep.dot"]["entscheidung"], "keep")
        self.assertEqual(trace["laeufe"][0]["transkript"], "legacy")
        self.assertEqual(len(trace["laeufe"]), 2)
        self.assertEqual(trace["wissen"][0]["aussage"], "bestehend")
        self.assertTrue(any(item.get("aussage") == "version-two" for item in trace["wissen"]))
        self.assertEqual(trace["elemente_stand"][RECORD], self.digest_v2)
        self.assertNotIn("invalidiert", trace)
        self.assertEqual(trace["invalidierungen"][-1]["state"], "invalidated")

        html = (self.src / "content" / "ai" / "classes" / "demo" / "rec_hit.html").read_text(encoding="utf-8")
        self.assertIn('class="ai usage"', html)
        self.assertIn("ai-note", html)
        self.assertIn("[%s]" % RECORD, html)
        self.assertNotIn("Alttext.", html)
        self.assertNotIn("\u27e6", html)
        backup = self.src / trace["laeufe"][-1]["previous_fragment_backup"]
        self.assertEqual(backup.read_bytes(), old_html)
        self.assertEqual(self.record_path.read_bytes(), spec_before)
        self.assertEqual((self.src / "spec" / "feedback-inbox" / "fb-7.json").read_bytes(), feedback_before)
        self.assertFalse((self.src / "content" / "ai" / "classes" / "demo" / "rec_missing.html").exists())

        self.assertEqual(self.pages, ["classes/demo.html"])
        preview = (self.src / "output" / "feedback-loop-pages" / "classes" / "demo.html").read_text(encoding="utf-8")
        self.assertIn("python3 _src/generate.py classes/demo.html", preview)
        self.assertIn("neu erzeugt", preview)
        self.assertEqual(report["events"][0]["rebuild"][0]["command"], "python3 _src/generate.py classes/demo.html")

    def test_rebuild_failure_keeps_the_regenerated_fragment(self):
        def boom(_page):
            raise RuntimeError("generate failed")

        report = self._engine(generate_fn=boom).run(record_id=RECORD)
        trace = self._hit_trace()
        self.assertEqual(trace["status"], "aktuell")
        self.assertIn("neu erzeugt", (self.src / "content" / "ai" / "classes" / "demo" / "rec_hit.html").read_text(encoding="utf-8"))
        self.assertEqual(report["events"][0]["rebuild"][0]["status"], "failed")
        self.assertFalse(report["events"][0]["complete"])
        self.assertEqual(self.record_path.read_bytes(), self.v2)

    def test_corrupt_policy_is_not_rewritten(self):
        policy = self.src / "ai" / "policy.json"
        policy.write_bytes(b"{policy")
        self._engine().run(record_id=RECORD)
        self.assertEqual(policy.read_bytes(), b"{policy")
        self.assertEqual(self._hit_trace()["modell"], fl.BUILTIN_MODEL)


class LedgerTests(LoopCase):
    def test_ledger_appends_valid_receipt_without_rewriting_history(self):
        ledger = self.src / "output" / "feedback-loop-ledger.jsonl"
        ledger.parent.mkdir(parents=True)
        original = b'{"a": 1}'
        ledger.write_bytes(original)
        corrupt = self.src / "output" / "also.jsonl"
        # The real ledger is the one the engine appends to. Seed a corrupt
        # line there after proving a missing newline is not glued.
        report = self._engine().run(feedback_id="fb-7")
        raw = ledger.read_bytes()
        self.assertEqual(raw.splitlines()[0], original)
        event = json.loads(raw.splitlines()[-1])
        self.assertEqual(event["schema_version"], fl.LEDGER_SCHEMA)
        self.assertEqual(event["event"], "regenerated")
        self.assertEqual(event["feedback_id"], "fb-7")
        self.assertEqual(event["record_id"], RECORD)
        self.assertEqual(event["record_sha1"], self.digest_v2)
        self.assertFalse(event["spec_records_mutated"])
        self.assertEqual(event["receipt_hash"], fl.receipt_hash(event))
        self.assertTrue(event["receipt_hash"].startswith("sha256:"))
        self.assertTrue(event["complete"])
        self.assertTrue(report["events"][0]["regenerated"])

        prefix = ledger.read_bytes()
        html = (self.src / "content" / "ai" / "classes" / "demo" / "rec_hit.html").read_bytes()
        laeufe = len(self._hit_trace()["laeufe"])
        again = self._engine().run(feedback_id="fb-7")
        self.assertTrue(again["events"][0]["noop"])
        self.assertTrue(ledger.read_bytes().startswith(prefix))
        self.assertEqual((self.src / "content" / "ai" / "classes" / "demo" / "rec_hit.html").read_bytes(), html)
        self.assertEqual(len(self._hit_trace()["laeufe"]), laeufe)
        second = json.loads(ledger.read_bytes().splitlines()[-1])
        self.assertEqual(second["receipt_hash"], fl.receipt_hash(second))
        self.assertNotEqual(second["receipt_hash"], event["receipt_hash"])
        self.assertFalse(corrupt.exists())

    def test_corrupt_ledger_prefix_is_preserved(self):
        ledger = self.src / "output" / "feedback-loop-ledger.jsonl"
        ledger.parent.mkdir(parents=True)
        ledger.write_bytes(b"{not json\n")
        self._engine().run(record_id=RECORD)
        raw = ledger.read_bytes()
        self.assertTrue(raw.startswith(b"{not json\n"))
        json.loads(raw.splitlines()[-1])


class I18nTests(LoopCase):
    def test_mock_segments_do_not_fall_back_and_keep_existing_keys(self):
        es_before = (self.src / "i18n" / "es" / "segments.json").read_bytes()
        de_before = json.loads((self.src / "i18n" / "segments.de.json").read_text(encoding="utf-8"))
        self._engine().run(record_id=RECORD)
        german = json.loads((self.src / "i18n" / "segments.de.json").read_text(encoding="utf-8"))
        english = json.loads((self.src / "i18n" / "en" / "segments.json").read_text(encoding="utf-8"))
        dutch = json.loads((self.src / "i18n" / "nl" / "segments.json").read_text(encoding="utf-8"))
        self.assertEqual(german["aaaaaaaaaaaa"], de_before["aaaaaaaaaaaa"])
        self.assertEqual(english["aaaaaaaaaaaa"], "keep-en")
        self.assertEqual(dutch["aaaaaaaaaaaa"], "keep-nl")
        self.assertEqual((self.src / "i18n" / "es" / "segments.json").read_bytes(), es_before)
        fresh = [sid for sid in german if sid != "aaaaaaaaaaaa"]
        self.assertTrue(fresh)
        for sid in fresh:
            masked = german[sid]["m"]
            self.assertIn("ai", german[sid]["ctx"])
            self.assertNotEqual(english[sid], masked)
            self.assertNotEqual(dutch[sid], masked)
            self.assertNotIn("Erklärung", english[sid])
            self.assertNotIn("Erklärung", dutch[sid])
            self.assertTrue(english[sid].startswith("Regenerated commentary"))

    def test_corrupt_translation_file_is_not_overwritten(self):
        english = self.src / "i18n" / "en" / "segments.json"
        english.write_bytes(b"{broken")
        report = self._engine().run(record_id=RECORD)
        self.assertEqual(english.read_bytes(), b"{broken")
        self.assertTrue(report["events"][0]["i18n_errors"])
        self.assertFalse(report["events"][0]["complete"])
        # The German fragment is still the regenerated one.
        self.assertIn("neu erzeugt", (self.src / "content" / "ai" / "classes" / "demo" / "rec_hit.html").read_text(encoding="utf-8"))


class RefusalTests(LoopCase):
    def test_rejected_and_conflicting_feedback_write_nothing(self):
        _json(self.src / "spec" / "feedback-inbox" / "nope.json", {
            "feedback_id": "nope",
            "status": "rejected",
            "kind": "user-feedback",
            "record_id": RECORD,
        })
        _json(self.src / "spec" / "feedback-inbox" / "clash.json", {
            "feedback_id": "clash",
            "status": "rejected",
            "outcome": "accepted",
            "record_id": RECORD,
        })
        _json(self.src / "spec" / "curation-queue" / "ai.json", {
            "feedback_id": "ai-1",
            "status": "accepted",
            "kind": "curator-decision",
            "actor_role": "ai",
            "record_id": RECORD,
        })
        # A spec record that merely contains an accepted status is not a decision.
        _json(self.record_path, {
            "id": RECORD,
            "status": "accepted",
            "blocks": _record("version-two")["blocks"],
        })
        before = _tree(self.src)
        for feedback_id in ("nope", "clash", "ai-1"):
            with self.assertRaises(fl.FeedbackLoopError):
                self._engine().run(feedback_id=feedback_id)
        self.assertEqual(_tree(self.src), before)

    def test_unknown_feedback_and_usage_write_nothing(self):
        before = _tree(self.src)
        with self.assertRaises(fl.FeedbackLoopError) as unknown:
            self._engine().run(feedback_id="missing")
        self.assertEqual(unknown.exception.code, 1)
        with self.assertRaises(fl.FeedbackLoopError) as usage:
            self._engine().run()
        self.assertEqual(usage.exception.code, 2)
        with self.assertRaises(fl.FeedbackLoopError):
            self._engine().run(record_id="SWS_CM_00701/../../secret")
        self.assertEqual(_tree(self.src), before)

    def test_dry_run_writes_nothing(self):
        before = _tree(self.src)
        report = self._engine().run(record_id=RECORD, dry_run=True)
        self.assertTrue(report["dry_run"])
        self.assertIn("content/ai/classes/demo/rec_hit.html", report["flagged"])
        self.assertEqual(report["regenerated"], [])
        self.assertEqual(self.pages, [])
        self.assertEqual(_tree(self.src), before)

    def test_feedback_record_mismatch_writes_nothing(self):
        before = _tree(self.src)
        with self.assertRaises(fl.FeedbackLoopError):
            self._engine().run(feedback_id="fb-7", record_id=OTHER)
        self.assertEqual(_tree(self.src), before)

    def test_cli_on_a_temp_tree(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = fl.main([
                "run", "--record-id", RECORD, "--src", str(self.src),
                "--no-generate", "--no-regenerate",
            ])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out.getvalue())["ok"])
        self.assertEqual(self._hit_trace()["status"], "veraltet")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(fl.main(["run"]), 2)
            self.assertEqual(fl.main(["run", "--feedback-id", "missing", "--src", str(self.src)]), 1)
        self.assertFalse((REAL_SRC / "output" / "feedback-loop-ledger.jsonl").exists())


def _component(record_id: str, desc: str) -> dict:
    return {
        "id": record_id,
        "blocks": [
            {"t": "html", "html": '<h3 class="recname"><span class="kind">component</span> %s</h3>' % record_id},
            {"t": "html", "html": '<div class="desc"><p>%s</p></div>' % desc},
        ],
    }


def _bare_html() -> str:
    return '<div class="ai usage"><p class="ai-note">alt</p><p>Alttext ohne Beleg.</p></div>'


class UniverseCase(unittest.TestCase):
    """Classic and S-Core loops stay inside a temp tree.

    ``src`` is ``<temp>/_src`` so the mutation audit's repository root is the
    temp directory and neither ledger can land in the real checkout.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.src = self.root / "_src"
        self.pages = []

    def tearDown(self):
        self.tmp.cleanup()

    def _engine(self, **kwargs):
        kwargs.setdefault("now", lambda: FROZEN)
        kwargs.setdefault("generate_fn", self.pages.append)
        kwargs.setdefault("invoke_generate", False)
        return fl.FeedbackLoop(self.src, **kwargs)

    def _trace_path(self, fragment: str) -> Path:
        stem = fragment[len("content/ai/"):-len(".html")]
        return self.src / "ai" / "traces" / (stem + ".json")

    def _plant(self, record_id: str, feedback_id: str, desc: str) -> str:
        node = fl.causal_dependency_graph()[record_id]
        fragment = node["ai_fragment"]
        _write(self.src / fragment, _bare_html())
        _json(
            self._trace_path(fragment),
            _trace(
                fragment,
                record_id,
                "0" * 40,
                seite=None,
                elemente=[],
                zitate=[],
                elemente_stand={},
            ),
        )
        record_rel = node["record_path"]
        stored_id = "CP_MEM" if record_id == "CP_NVRAM" else record_id
        _json(self.src / record_rel, _component(stored_id, desc))
        _json(
            self.src / "spec" / "feedback-inbox" / ("%s.json" % feedback_id),
            {
                "schema": "ai-commentary-feedback@v1",
                "feedback_id": feedback_id,
                "status": "accepted",
                "kind": "user-feedback",
                "record_id": record_id,
                "note": "Bitte den Hinweis nachziehen.",
            },
        )
        return fragment

    def _audit(self):
        tools = str(REAL_SRC / "tools")
        if tools not in sys.path:
            sys.path.insert(0, tools)
        import mutation_ledger as ml
        return ml.read_mutation_entries(root=self.root)

    def test_dependency_graph_names_classic_and_score_without_writing(self):
        engine = fl.FeedbackLoopEngine()
        rte = engine.dependency_graph["CP_RTE"]
        score = engine.dependency_graph["SCORE_CORE"]
        self.assertEqual(rte["universe"], "classic")
        self.assertEqual(rte["ai_src"], "_src/content/ai/classic/rec_CP_RTE_01.html")
        self.assertEqual(rte["page"], "classic/rte.html")
        self.assertEqual(score["universe"], "score")
        self.assertEqual(score["ai_src"], "_src/content/ai/score/rec_SCORE_CORE_01.html")
        self.assertEqual(score["page"], "score/core.html")
        self.assertIsNone(engine.dependency_graph["SCORE_SAFETY"]["page"])
        self.assertEqual(
            engine.dependency_graph["CP_NVRAM"]["ai_fragment"],
            engine.dependency_graph["CP_MEM"]["ai_fragment"],
        )
        self.assertEqual(fl.record_filename("CP_RTE"), "spec/records/classic/CP_RTE.json")
        self.assertEqual(fl.record_filename("SCORE_CORE"), "spec/records/score/SCORE_CORE.json")
        self.assertEqual(fl.record_filename(RECORD), "spec/records/SWS_CM/SWS_CM_00701.json")
        self.assertIsNone(fl.record_filename(SCORE))
        self.assertFalse((REAL_SRC / "output" / "feedback-loop-ledger.jsonl").exists())
        self.assertEqual(REAL_AI_CLASSIC.exists(), REAL_AI_CLASSIC_EXISTS)

    def test_classic_feedback_invalidates_only_its_commentary(self):
        rte = self._plant("CP_RTE", "fb-rte", "RTE Read/Write APIs")
        other = self._plant("CP_OS", "fb-os", "Activate a task")
        score = self._plant("SCORE_CORE", "fb-core", "Execution environment")
        decoy = "content/ai/classic/rec_decoy.html"
        _write(self.src / decoy, '<div class="ai"><p class="ai-note">n</p><p>CP_RTE_EXTRA CP_RTE2</p></div>')
        before_html = (self.src / rte).read_bytes()
        before_other = (self.src / other).read_bytes()
        before_score = (self.src / score).read_bytes()
        before_spec = (self.src / "spec" / "records" / "classic" / "CP_RTE.json").read_bytes()
        report = self._engine().run(feedback_id="fb-rte", regenerate=False)
        self.assertEqual(report["flagged"], [rte])
        self.assertEqual(report["regenerated"], [])
        trace = json.loads(self._trace_path(rte).read_text(encoding="utf-8"))
        self.assertEqual(fl.invalidation_schema_errors(trace, "CP_RTE"), [])
        self.assertEqual(trace["universe"], "classic")
        self.assertEqual(trace["provenance"]["state"], "invalidated")
        self.assertEqual(trace["provenance"]["page"], "classic/rte.html")
        self.assertEqual(trace["curator_note"], "keep-me")
        self.assertEqual((self.src / rte).read_bytes(), before_html)
        self.assertEqual((self.src / other).read_bytes(), before_other)
        self.assertEqual((self.src / score).read_bytes(), before_score)
        self.assertEqual((self.src / "spec" / "records" / "classic" / "CP_RTE.json").read_bytes(), before_spec)
        self.assertEqual(json.loads(self._trace_path(other).read_text(encoding="utf-8"))["status"], "aktuell")
        actions = [entry["action"] for entry in self._audit()]
        self.assertEqual(actions, ["feedback-loop-invalidation"])
        self.assertEqual(self._audit()[0]["details"]["record_id"], "CP_RTE")
        self.assertEqual(self._audit()[0]["status"], "ok")

    def test_score_feedback_invalidates_only_its_commentary(self):
        score = self._plant("SCORE_CORE", "fb-core", "Execution environment")
        sibling = self._plant("SCORE_COM", "fb-com", "Zero-copy IPC")
        classic = self._plant("CP_RTE", "fb-rte", "RTE Read/Write APIs")
        before_sibling = (self.src / sibling).read_bytes()
        before_classic = (self.src / classic).read_bytes()
        before_spec = (self.src / "spec" / "records" / "score" / "SCORE_CORE.json").read_bytes()
        report = self._engine().run(feedback_id="fb-core", regenerate=False)
        self.assertEqual(report["flagged"], [score])
        trace = json.loads(self._trace_path(score).read_text(encoding="utf-8"))
        self.assertEqual(fl.invalidation_schema_errors(trace, "SCORE_CORE"), [])
        self.assertEqual(trace["universe"], "score")
        self.assertEqual(trace["provenance"]["ai_src"], "_src/content/ai/score/rec_SCORE_CORE_01.html")
        self.assertEqual((self.src / sibling).read_bytes(), before_sibling)
        self.assertEqual((self.src / classic).read_bytes(), before_classic)
        self.assertEqual((self.src / "spec" / "records" / "score" / "SCORE_CORE.json").read_bytes(), before_spec)
        self.assertEqual([entry["action"] for entry in self._audit()], ["feedback-loop-invalidation"])

    def test_closed_loop_regenerates_classic_trace_and_audit(self):
        _json(self.src / "ai" / "policy.json", {"version": 7, "modell": {"erklaerungen": "builtin-test-model"}})
        _json(self.src / "site.json", {"sprachen": {"ziele": ["en", "nl"]}})
        rte = self._plant("CP_RTE", "fb-rte", "RTE Read/Write APIs")
        other = self._plant("CP_OS", "fb-os", "Activate a task")
        score = self._plant("SCORE_CORE", "fb-core", "Execution environment")
        adaptive = "content/ai/classes/demo/rec_hit.html"
        _write(self.src / adaptive, _html(RECORD))
        _json(self._trace_path(adaptive), _trace(adaptive, RECORD, "d" * 40))
        spec_path = self.src / "spec" / "records" / "classic" / "CP_RTE.json"
        spec_before = spec_path.read_bytes()
        digest = _sha1(spec_before)
        old_html = (self.src / rte).read_bytes()
        other_before = (self.src / other).read_bytes()
        score_before = (self.src / score).read_bytes()
        adaptive_before = (self.src / adaptive).read_bytes()
        feedback_before = (self.src / "spec" / "feedback-inbox" / "fb-rte.json").read_bytes()
        report = self._engine().run(feedback_id="fb-rte")
        self.assertTrue(report["ok"])
        self.assertEqual(report["regenerated"], [rte])
        self.assertIn("classic/rte.html", report["events"][0]["pages"])
        trace = json.loads(self._trace_path(rte).read_text(encoding="utf-8"))
        self.assertEqual(fl.trace_schema_errors(trace, "CP_RTE"), [])
        self.assertEqual(trace["universe"], "classic")
        self.assertEqual(trace["seite"], "classic/rte.html")
        self.assertEqual(trace["provenance"]["state"], "regenerated")
        self.assertEqual(trace["provenance"]["ai_src"], "_src/content/ai/classic/rec_CP_RTE_01.html")
        self.assertEqual(trace["modell"], "builtin-test-model")
        self.assertEqual(trace["policy_version"], 7)
        self.assertEqual(trace["trigger"]["feedback_id"], "fb-rte")
        self.assertEqual(trace["elemente_stand"]["CP_RTE"], digest)
        self.assertEqual(trace["curator_note"], "keep-me")
        self.assertTrue(any(item.get("aussage") == "RTE Read/Write APIs" for item in trace["wissen"]))
        html = (self.src / rte).read_text(encoding="utf-8")
        self.assertIn("neu erzeugt", html)
        self.assertIn("[CP_RTE]", html)
        self.assertNotIn("Alttext", html)
        backup = self.src / trace["laeufe"][-1]["previous_fragment_backup"]
        self.assertEqual(backup.read_bytes(), old_html)
        self.assertEqual(spec_path.read_bytes(), spec_before)
        self.assertEqual((self.src / other).read_bytes(), other_before)
        self.assertEqual((self.src / score).read_bytes(), score_before)
        self.assertEqual((self.src / adaptive).read_bytes(), adaptive_before)
        self.assertEqual((self.src / "spec" / "feedback-inbox" / "fb-rte.json").read_bytes(), feedback_before)
        self.assertFalse((self.root / "classic" / "rte.html").exists())
        preview = self.src / "output" / "feedback-loop-pages" / "classic" / "rte.html"
        self.assertIn("python3 _src/generate.py classic/rte.html", preview.read_text(encoding="utf-8"))
        entries = self._audit()
        self.assertEqual([entry["action"] for entry in entries], [
            "feedback-loop-invalidation",
            "feedback-loop-regeneration",
        ])
        tools = str(REAL_SRC / "tools")
        if tools not in sys.path:
            sys.path.insert(0, tools)
        import mutation_ledger as ml
        for entry in entries:
            self.assertEqual(entry["details"]["record_id"], "CP_RTE")
            self.assertEqual(entry["status"], "ok")
            self.assertEqual(entry["operator"], "feedback-loop")
            self.assertTrue(ml.verify_receipt(entry))
        primary, mirror = ml.ledger_paths(self.root)
        self.assertEqual(primary.read_bytes(), mirror.read_bytes())
        stable_html = (self.src / rte).read_bytes()
        stable_runs = len(trace["laeufe"])
        again = self._engine().run(feedback_id="fb-rte")
        self.assertTrue(again["events"][0]["noop"])
        self.assertEqual((self.src / rte).read_bytes(), stable_html)
        self.assertEqual(len(json.loads(self._trace_path(rte).read_text(encoding="utf-8"))["laeufe"]), stable_runs)
        self.assertEqual(len(self._audit()), 2)
        self.assertEqual(spec_path.read_bytes(), spec_before)

    def test_score_regeneration_updates_provenance(self):
        _json(self.src / "ai" / "policy.json", {"version": 7, "modell": {"erklaerungen": "builtin-test-model"}})
        score = self._plant("SCORE_CORE", "fb-core", "Execution environment")
        spec_path = self.src / "spec" / "records" / "score" / "SCORE_CORE.json"
        spec_before = spec_path.read_bytes()
        report = self._engine().run(feedback_id="fb-core")
        self.assertIn(score, report["regenerated"])
        trace = json.loads(self._trace_path(score).read_text(encoding="utf-8"))
        self.assertEqual(fl.trace_schema_errors(trace, "SCORE_CORE"), [])
        self.assertEqual(trace["universe"], "score")
        self.assertEqual(trace["seite"], "score/core.html")
        self.assertEqual(trace["provenance"]["page"], "score/core.html")
        self.assertEqual(trace["elemente_stand"]["SCORE_CORE"], _sha1(spec_before))
        self.assertIn("[SCORE_CORE]", (self.src / score).read_text(encoding="utf-8"))
        self.assertEqual(spec_path.read_bytes(), spec_before)
        self.assertEqual(
            [entry["action"] for entry in self._audit()],
            ["feedback-loop-invalidation", "feedback-loop-regeneration"],
        )

    def test_missing_commentary_is_not_created(self):
        _json(self.src / "spec" / "feedback-inbox" / "fb-rte.json", {
            "feedback_id": "fb-rte",
            "status": "accepted",
            "kind": "user-feedback",
            "record_id": "CP_RTE",
        })
        report = self._engine().run(feedback_id="fb-rte")
        self.assertEqual(report["flagged"], [])
        self.assertEqual(report["regenerated"], [])
        self.assertFalse((self.src / "content" / "ai" / "classic" / "rec_CP_RTE_01.html").exists())
        self.assertFalse((self.src / "spec" / "records" / "classic" / "CP_RTE.json").exists())
        self.assertFalse((self.src / "ai" / "traces" / "classic" / "rec_CP_RTE_01.json").exists())

    def test_malformed_classic_trace_is_not_overwritten(self):
        fragment = self._plant("CP_RTE", "fb-rte", "RTE Read/Write APIs")
        broken = self._trace_path(fragment)
        broken.write_bytes(b"{not-json")
        html = self.src / fragment
        before_trace = broken.read_bytes()
        before_html = html.read_bytes()
        report = self._engine().run(feedback_id="fb-rte")
        self.assertIn(fragment, report["flagged"])
        self.assertNotIn(fragment, report["regenerated"])
        self.assertEqual(broken.read_bytes(), before_trace)
        self.assertEqual(html.read_bytes(), before_html)
        self.assertFalse(report["events"][0]["complete"])

    def test_dry_run_and_rejected_feedback_write_nothing(self):
        fragment = self._plant("SCORE_CORE", "fb-core", "Execution environment")
        _json(self.src / "spec" / "feedback-inbox" / "nope.json", {
            "feedback_id": "nope",
            "status": "rejected",
            "kind": "user-feedback",
            "record_id": "SCORE_CORE",
        })
        before = _tree(self.src)
        report = self._engine().run(feedback_id="fb-core", dry_run=True)
        self.assertEqual(report["flagged"], [fragment])
        self.assertEqual(report["regenerated"], [])
        self.assertEqual(_tree(self.src), before)
        self.assertFalse((self.root / "docs").exists())
        with self.assertRaises(fl.FeedbackLoopError):
            self._engine().run(feedback_id="nope")
        self.assertEqual(_tree(self.src), before)
        self.assertEqual(self._audit(), [])

    def test_memory_alias_uses_the_cp_mem_record(self):
        fragment = self._plant("CP_MEM", "fb-mem", "NVRAM block write")
        self.assertEqual(fragment, "content/ai/classic/rec_CP_NVRAM_01.html")
        spec_path = self.src / "spec" / "records" / "classic" / "CP_MEM.json"
        digest = _sha1(spec_path.read_bytes())
        report = self._engine().run(feedback_id="fb-mem", regenerate=False)
        self.assertEqual(report["flagged"], [fragment])
        self.assertEqual(report["events"][0]["record_sha1"], digest)
        self.assertFalse((self.src / "spec" / "records" / "classic" / "CP_NVRAM.json").exists())

    def test_safety_feedback_does_not_invent_a_page(self):
        fragment = self._plant("SCORE_SAFETY", "fb-safety", "Watchdog")
        report = self._engine().run(feedback_id="fb-safety", regenerate=False)
        self.assertEqual(report["flagged"], [fragment])
        self.assertEqual(report["events"][0]["pages"], [])
        self.assertFalse((self.root / "score").exists())
        self.assertFalse((self.src / "score" / "safety.html").exists())

    def test_rebuild_failure_keeps_the_fragment_and_the_spec(self):
        fragment = self._plant("CP_RTE", "fb-rte", "RTE Read/Write APIs")
        spec_path = self.src / "spec" / "records" / "classic" / "CP_RTE.json"
        spec_before = spec_path.read_bytes()

        def boom(_page):
            raise RuntimeError("generate failed")

        report = self._engine(generate_fn=boom).run(feedback_id="fb-rte")
        self.assertIn("neu erzeugt", (self.src / fragment).read_text(encoding="utf-8"))
        self.assertEqual(report["events"][0]["rebuild"][0]["status"], "failed")
        self.assertFalse(report["events"][0]["complete"])
        self.assertEqual(spec_path.read_bytes(), spec_before)
        self.assertTrue(all(entry["status"] == "error" for entry in self._audit()))

    def test_audit_failure_does_not_roll_back_the_commentary(self):
        fragment = self._plant("CP_RTE", "fb-rte", "RTE Read/Write APIs")
        tools = str(REAL_SRC / "tools")
        if tools not in sys.path:
            sys.path.insert(0, tools)
        import mutation_ledger as ml
        original = ml.record_mutation

        def boom(*_args, **_kwargs):
            raise RuntimeError("ledger down")

        ml.record_mutation = boom
        try:
            report = self._engine().run(feedback_id="fb-rte")
        finally:
            ml.record_mutation = original
        self.assertTrue(report["ok"])
        self.assertIn("neu erzeugt", (self.src / fragment).read_text(encoding="utf-8"))
        self.assertEqual(self._audit(), [])

    def test_corrupt_audit_prefix_is_preserved(self):
        self._plant("SCORE_CORE", "fb-core", "Execution environment")
        tools = str(REAL_SRC / "tools")
        if tools not in sys.path:
            sys.path.insert(0, tools)
        import mutation_ledger as ml
        primary, _mirror = ml.ledger_paths(self.root)
        primary.parent.mkdir(parents=True, exist_ok=True)
        primary.write_bytes(b"{not json\n")
        self._engine().run(feedback_id="fb-core", regenerate=False)
        raw = primary.read_bytes()
        self.assertTrue(raw.startswith(b"{not json\n"))
        self.assertGreaterEqual(len(self._audit()), 1)


class SentinelTests(unittest.TestCase):
    def test_real_corpus_sentinel_is_unchanged(self):
        self.assertEqual(SENTINEL.read_bytes(), SENTINEL_BYTES)
        self.assertEqual(_bytes_or_none(REAL_MUTATION), REAL_MUTATION_BYTES)
        self.assertEqual(_bytes_or_none(REAL_MIRROR), REAL_MIRROR_BYTES)
        self.assertEqual(_bytes_or_none(REAL_RTE_PAGE), REAL_RTE_BYTES)
        self.assertEqual(_bytes_or_none(REAL_SCORE_PAGE), REAL_SCORE_BYTES)
        self.assertEqual(REAL_AI_CLASSIC.exists(), REAL_AI_CLASSIC_EXISTS)
        self.assertEqual(REAL_AI_SCORE.exists(), REAL_AI_SCORE_EXISTS)
        self.assertFalse((REAL_SRC / "output" / "feedback-loop-ledger.jsonl").exists())


def tearDownModule():
    if (REAL_SRC / "output" / "feedback-loop-ledger.jsonl").exists():
        raise AssertionError("real feedback-loop ledger was created")
    if SENTINEL.read_bytes() != SENTINEL_BYTES:
        raise AssertionError("real sentinel trace was modified")
    if _bytes_or_none(REAL_MUTATION) != REAL_MUTATION_BYTES:
        raise AssertionError("real mutation audit ledger was modified")
    if _bytes_or_none(REAL_MIRROR) != REAL_MIRROR_BYTES:
        raise AssertionError("real mutation audit mirror was modified")
    if _bytes_or_none(REAL_RTE_PAGE) != REAL_RTE_BYTES:
        raise AssertionError("real classic RTE page was modified")
    if _bytes_or_none(REAL_SCORE_PAGE) != REAL_SCORE_BYTES:
        raise AssertionError("real S-Core page was modified")
    if REAL_AI_CLASSIC.exists() != REAL_AI_CLASSIC_EXISTS or REAL_AI_SCORE.exists() != REAL_AI_SCORE_EXISTS:
        raise AssertionError("real AI commentary directories changed")


if __name__ == "__main__":
    unittest.main()
