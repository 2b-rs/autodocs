"""End-to-end checks for the local demonstration server.

The suite starts ``_src/serve.py`` on an ephemeral port and a temporary
repository. Queue writes must stay inside that repository. Canonical
sentinel files are compared by exact bytes after every mutating call.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import tempfile
import threading
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import urlencode
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("demo_serve", ROOT / "_src" / "serve.py")
SERVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SERVE)


class UniverseInventoryTest(unittest.TestCase):
    def test_real_repository_reports_all_three_universes_present(self):
        rows = {row["id"]: row for row in SERVE.universe_rows(ROOT)}
        self.assertEqual(set(rows), {"adaptive", "classic", "score"})
        self.assertTrue(rows["adaptive"]["present"])
        self.assertTrue(rows["score"]["present"])
        self.assertTrue(rows["classic"]["present"])
        self.assertIsNone(rows["classic"]["note"])
        self.assertTrue((ROOT / "index.html").is_file())
        self.assertTrue((ROOT / "eclipse-score-v0.6.0-curation-review" / "index.html").is_file())
        self.assertTrue((ROOT / "classic" / "index.html").is_file())


class ExperienceServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self._plant()
        self.httpd = SERVE.build_server(self.repo, "127.0.0.1", 0)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise RuntimeError("demonstration server thread did not stop")
        self.tmp.cleanup()

    def _plant(self):
        (self.repo / "index.html").write_text("ADAPTIVE-SENTINEL\n", encoding="utf-8")
        (self.repo / "modules").mkdir()
        (self.repo / "modules" / "core.html").write_text("CORE-SENTINEL\n", encoding="utf-8")
        score = self.repo / "eclipse-score-v0.6.0-curation-review"
        score.mkdir()
        (score / "index.html").write_text("SCORE-SENTINEL\n", encoding="utf-8")
        (self.repo / "guide.md").write_text("# Hello\n\nbody\n", encoding="utf-8")
        queue = self.repo / "_src" / "spec" / "curation-queue" / "open"
        queue.mkdir(parents=True)
        (queue / "one.json").write_text("{}\n", encoding="utf-8")
        (queue / "two.json").write_text("{}\n", encoding="utf-8")
        (queue / "note.txt").write_text("not-json\n", encoding="utf-8")
        records = self.repo / "_src" / "spec" / "records"
        records.mkdir(parents=True)
        (records / "keep.json").write_text("KEEP\n", encoding="utf-8")
        shutil.copyfile(ROOT / "demo.html", self.repo / "demo.html")

    def _feedback(self, **overrides):
        payload = {
            "target_agent": "curator",
            "observed_baseline": "workspace",
            "feedback_text": "Die Beschreibung von ara::core sollte den Stereotyp foundation nennen.",
            "category": "general",
            "attribution": "identified",
            "submitter": "demo-visitor",
            "consent_visibility": "private",
            "page": "modules/core.html",
            "universe": "adaptive",
            "component_id": "core",
        }
        payload.update(overrides)
        return payload

    def _request(self, method, path, payload=None, content_type="application/json", raw=None):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=15)
        try:
            headers = {}
            body = None
            if raw is not None:
                body = raw
                headers["Content-Type"] = content_type
                headers["Content-Length"] = str(len(body))
            elif payload is not None:
                body = json.dumps(payload).encode("utf-8")
                headers["Content-Type"] = content_type
                headers["Content-Length"] = str(len(body))
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            data = response.read()
            parsed = None
            if "application/json" in (response.getheader("Content-Type") or ""):
                parsed = json.loads(data.decode("utf-8"))
            return response.status, parsed, data
        finally:
            connection.close()

    def _sentinels(self):
        return (
            (self.repo / "index.html").read_text(encoding="utf-8"),
            (self.repo / "modules" / "core.html").read_text(encoding="utf-8"),
            (self.repo / "_src" / "spec" / "records" / "keep.json").read_text(encoding="utf-8"),
        )

    def _queue(self, *parts):
        return self.repo.joinpath("_src", "spec", "feedback-queue", *parts)

    def _json_names(self, directory: Path):
        if not directory.exists():
            return []
        return sorted(
            path.name
            for path in directory.iterdir()
            if path.is_file() and path.suffix == ".json" and not path.name.startswith(".")
        )

    def test_status_counts_universes_feedback_and_curation_queue(self):
        status, body, _ = self._request("GET", "/api/status")
        self.assertEqual(status, 200)
        rows = {row["id"]: row for row in body["universes"]}
        self.assertTrue(rows["adaptive"]["present"])
        self.assertTrue(rows["score"]["present"])
        self.assertFalse(rows["classic"]["present"])
        self.assertEqual(body["pending_feedback"], 0)
        self.assertEqual(body["curation_queue"], {"open": 2, "quarantine": 0})
        self.assertFalse(body["canonical_mutation"])

    def test_markdown_preview_still_renders(self):
        status, _, data = self._request("GET", "/guide.md")
        text = data.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn("<h1>Hello</h1>", text)
        self.assertNotIn("ADAPTIVE-SENTINEL", text)

    def test_demo_page_exposes_six_pillars(self):
        status, _, data = self._request("GET", "/demo.html")
        text = data.decode("utf-8")
        self.assertEqual(status, 200)
        for marker in (
            'id="universe-switcher"',
            'data-universe="classic"',
            'id="theme-toggle"',
            'id="density-toggle"',
            'id="trace-graph"',
            'id="trace-table"',
            'id="component-inspector"',
            'id="feedback-form"',
            'id="receipt-dialog"',
            'id="discuss-prompt"',
            'id="run-loop"',
            ">Explore<",
            ">Trace<",
            ">Curate<",
            ">Review<",
            ">Work<",
            ">Reports<",
        ):
            self.assertIn(marker, text)

    def test_feedback_writes_receipt_and_replay_does_not_duplicate(self):
        before = self._sentinels()
        status, body, _ = self._request("POST", "/api/feedback", self._feedback())
        self.assertEqual(status, 201)
        self.assertTrue(body["envelope_id"])
        self.assertFalse(body["idempotent_replay"])
        self.assertFalse(body["canonical_mutation"])
        stored = self.repo / body["path"]
        self.assertTrue(stored.is_file())
        on_disk = json.loads(stored.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["feedback_text"], self._feedback()["feedback_text"])
        self.assertEqual(on_disk["demo_context"]["page"], "modules/core.html")
        self.assertEqual(on_disk["schema"], "agent-profile-feedback@v1")

        again, replay, _ = self._request("POST", "/api/feedback", self._feedback())
        self.assertEqual(again, 200)
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(replay["envelope_id"], body["envelope_id"])
        self.assertEqual(self._json_names(self._queue("open")), [stored.name])
        self.assertEqual(self._sentinels(), before)

        clash, rejected, _ = self._request(
            "POST",
            "/api/feedback",
            self._feedback(page="modules/com.html"),
        )
        self.assertEqual(clash, 409)
        self.assertEqual(rejected["envelope_id"], body["envelope_id"])
        reread = json.loads(stored.read_text(encoding="utf-8"))
        self.assertEqual(reread["demo_context"]["page"], "modules/core.html")
        self.assertEqual(self._json_names(self._queue("open")), [stored.name])

    def test_feedback_boundaries(self):
        anonymous, body, _ = self._request(
            "POST",
            "/api/feedback",
            self._feedback(attribution="anonymous", submitter=None, feedback_text="Anonyme Korrektur an ara::core."),
        )
        self.assertEqual(anonymous, 201, body)
        stored = json.loads((self.repo / body["path"]).read_text(encoding="utf-8"))
        self.assertIsNone(stored["submitter"])
        self.assertFalse(stored["policy_result"]["approval_authority"])

        missing, rejected, _ = self._request(
            "POST",
            "/api/feedback",
            self._feedback(submitter=None, feedback_text="Ohne Absender."),
        )
        self.assertEqual(missing, 400)
        self.assertIn("submitter", rejected["error"].lower())

        nulled, _, _ = self._request(
            "POST",
            "/api/feedback",
            self._feedback(feedback_text="kaputt\u0000text"),
        )
        self.assertEqual(nulled, 400)
        self.assertEqual(len(self._json_names(self._queue("open"))), 1)

        encoded = urlencode(self._feedback(feedback_text="Formular ohne JavaScript zu ara::log.")).encode("utf-8")
        form_status, form_body, _ = self._request(
            "POST",
            "/api/feedback",
            raw=encoded,
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(form_status, 201, form_body)
        self.assertEqual(len(self._json_names(self._queue("open"))), 2)

        method, _, _ = self._request("GET", "/api/feedback")
        self.assertEqual(method, 405)
        huge = b'{"feedback_text":"' + (b"a" * (SERVE.MAX_BODY_BYTES + 50)) + b'"}'
        oversized, _, _ = self._request("POST", "/api/feedback", raw=huge)
        self.assertEqual(oversized, 413)

    def test_curate_envelopes_do_not_change_canonical_bytes(self):
        before = self._sentinels()
        status, body, _ = self._request(
            "POST",
            "/api/curate",
            {
                "decision": "change_stereotype",
                "target_id": "core",
                "stereotype": "protocol",
                "rationale": "nur die Führung",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["effect"], "envelope-only")
        self.assertFalse(body["canonical_mutation"])
        record = json.loads((self.repo / body["path"]).read_text(encoding="utf-8"))
        self.assertEqual(record["stereotype"], "protocol")
        self.assertEqual(record["decision"], "change_stereotype")

        unbound, unbound_body, _ = self._request(
            "POST",
            "/api/curate",
            {"decision": "delete_mapping", "target_id": "core", "rationale": "lösen"},
        )
        self.assertEqual(unbound, 200, unbound_body)
        self.assertEqual(self._sentinels(), before)
        self.assertEqual((self.repo / "_src" / "spec" / "records" / "keep.json").read_text(encoding="utf-8"), "KEEP\n")

        rejected, _, _ = self._request(
            "POST",
            "/api/curate",
            {"decision": "delete_mapping", "target_id": "../index.html"},
        )
        self.assertEqual(rejected, 400)
        unknown, _, _ = self._request(
            "POST",
            "/api/curate",
            {"decision": "archive", "target_id": "core"},
        )
        self.assertEqual(unknown, 400)
        missing_stereotype, _, _ = self._request(
            "POST",
            "/api/curate",
            {"decision": "change_stereotype", "target_id": "core"},
        )
        self.assertEqual(missing_stereotype, 400)
        self.assertEqual(len(self._json_names(self._queue("decisions"))), 2)
        self.assertEqual(self._sentinels(), before)

    def test_discuss_is_local_and_requires_a_prompt(self):
        before = self._sentinels()
        empty, _, _ = self._request("POST", "/api/discuss", {"prompt": "  ", "context": {}})
        self.assertEqual(empty, 400)
        listed, _, _ = self._request("POST", "/api/discuss", {"prompt": "Hallo", "context": ["core"]})
        self.assertEqual(listed, 400)
        status, body, _ = self._request(
            "POST",
            "/api/discuss",
            {
                "prompt": "Bitte ara::core nur aus diesem Kontext beschreiben.",
                "context": {"component_id": "core", "page": "modules/core.html", "universe": "adaptive"},
            },
        )
        self.assertEqual(status, 200)
        self.assertIsNone(body["model"])
        self.assertEqual(body["generator"], "local-context-proposer")
        self.assertIn("ara::core", body["reply"])
        self.assertIn("kein externes Modell", body["reply"])
        self.assertIn("ara::core", body["proposal"]["text"])
        self.assertTrue((self.repo / body["path"]).is_file())
        self.assertEqual(self._sentinels(), before)

    def test_feedback_loop_rebuilds_comments_without_touching_pages(self):
        before = self._sentinels()
        created, receipt, _ = self._request(
            "POST",
            "/api/feedback",
            self._feedback(page="../../index.html", feedback_text="Bitte ara::core vorsichtig formulieren."),
        )
        self.assertEqual(created, 201, receipt)
        changed, _, _ = self._request(
            "POST",
            "/api/curate",
            {"decision": "change_stereotype", "target_id": "core", "stereotype": "protocol"},
        )
        self.assertEqual(changed, 200)
        discussed, _, _ = self._request(
            "POST",
            "/api/discuss",
            {"prompt": "Kommentar zu ara::core vorschlagen.", "context": {"component_id": "core"}},
        )
        self.assertEqual(discussed, 200)
        (self._queue("open") / "bad.json").write_text("not-json", encoding="utf-8")

        status, body, _ = self._request("POST", "/api/feedback-loop/run", {})
        self.assertEqual(status, 200, body)
        summary = body["summary"]
        self.assertTrue(summary["ok"])
        self.assertFalse(summary["canonical_mutation"])
        self.assertGreaterEqual(summary["comments_written"], 2)
        self.assertGreaterEqual(summary["processed_feedback"], 1)
        self.assertGreaterEqual(summary["processed_proposals"], 1)
        self.assertTrue(summary["errors"])
        self.assertTrue(any(item["path"] == "bad.json" for item in summary["errors"]))
        for relative in summary["pages_rebuilt"]:
            self.assertTrue(relative.startswith("_src/spec/feedback-queue/rendered/"))
            page = self.repo / relative
            self.assertTrue(page.is_file())
            self.assertNotEqual(page.resolve(), (self.repo / "index.html").resolve())
        comment_files = list((self._queue("comments")).glob("*.json"))
        self.assertGreaterEqual(len(comment_files), 1)
        core_comments = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in comment_files
            if json.loads(path.read_text(encoding="utf-8")).get("component_id") == "core"
        ]
        self.assertTrue(any(item["stereotype"] == "protocol" for item in core_comments))
        hostile = [item for item in core_comments if item.get("page") == "../../index.html"]
        self.assertEqual(len(hostile), 1)
        self.assertIn("Diese Datei wurde nicht verändert", hostile[0]["text"])
        self.assertEqual(self._sentinels(), before)
        self.assertEqual((self.repo / "index.html").read_text(encoding="utf-8"), "ADAPTIVE-SENTINEL\n")

    def test_reject_suppresses_rendered_page_and_delete_mapping_keeps_files(self):
        before = self._sentinels()
        created, _, _ = self._request(
            "POST",
            "/api/feedback",
            self._feedback(component_id="log", feedback_text="Anmerkung zu ara::log."),
        )
        self.assertEqual(created, 201)
        rejected, _, _ = self._request(
            "POST",
            "/api/curate",
            {"decision": "reject", "target_id": "log", "rationale": "nicht übernehmen"},
        )
        self.assertEqual(rejected, 200)
        status, body, _ = self._request("POST", "/api/feedback-loop/run", {})
        self.assertEqual(status, 200, body)
        self.assertEqual(len(body["summary"]["suppressed"]), 1)
        comments = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in (self._queue("comments")).glob("*.json")
        ]
        matched = [item for item in comments if item.get("component_id") == "log"]
        self.assertEqual(len(matched), 1)
        self.assertFalse(matched[0]["published"])
        rendered = list((self._queue("rendered")).glob("*.html")) if (self._queue("rendered")).exists() else []
        self.assertEqual(rendered, [])
        self.assertEqual(self._sentinels(), before)

        created_core, _, _ = self._request(
            "POST",
            "/api/feedback",
            self._feedback(feedback_text="Zuordnung von ara::core prüfen."),
        )
        self.assertEqual(created_core, 201)
        unbound, _, _ = self._request(
            "POST",
            "/api/curate",
            {"decision": "delete_mapping", "target_id": "core"},
        )
        self.assertEqual(unbound, 200)
        rerun, rerun_body, _ = self._request("POST", "/api/feedback-loop/run", {})
        self.assertEqual(rerun, 200, rerun_body)
        core = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in (self._queue("comments")).glob("*.json")
            if json.loads(path.read_text(encoding="utf-8")).get("component_id") == "core"
        ]
        self.assertTrue(core)
        self.assertTrue(all(item["mapping"] == "unbound" for item in core))
        self.assertTrue(all(item["canonical_mutation"] is False for item in core))
        self.assertTrue(list((self._queue("rendered")).glob("*.html")))
        self.assertEqual(self._sentinels(), before)

    def test_symlink_queue_is_refused(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        outside_path = Path(outside.name)
        queue = self._queue()
        queue.parent.mkdir(parents=True, exist_ok=True)
        queue.symlink_to(outside_path, target_is_directory=True)
        status, body, _ = self._request("POST", "/api/feedback", self._feedback())
        self.assertEqual(status, 500, body)
        self.assertEqual(list(outside_path.iterdir()), [])
        loop_status, loop_body, _ = self._request("POST", "/api/feedback-loop/run", {})
        self.assertEqual(loop_status, 500, loop_body)
        self.assertEqual(list(outside_path.iterdir()), [])
        self.assertEqual((self.repo / "index.html").read_text(encoding="utf-8"), "ADAPTIVE-SENTINEL\n")

    def test_open_queue_as_file_does_not_get_rewritten(self):
        open_path = self._queue("open")
        open_path.parent.mkdir(parents=True, exist_ok=True)
        open_path.write_text("do-not-clobber\n", encoding="utf-8")
        status, body, _ = self._request("POST", "/api/feedback-loop/run", {})
        self.assertEqual(status, 500, body)
        self.assertEqual(open_path.read_text(encoding="utf-8"), "do-not-clobber\n")

    def _plant_record(self, record_id, text, folder):
        path = self.repo / "_src" / "spec" / "records" / folder / f"{record_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "id": record_id,
            "blocks": [{"t": "html", "html": '<div class="desc"><p>' + text + "</p></div>"}],
        }
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        return path

    def _ledger(self):
        return SERVE.MUTATION.read_mutation_entries(root=self.repo)

    def test_demo_page_guided_tour_keeps_adaptive_steps(self):
        status, _, data = self._request("GET", "/demo.html")
        text = data.decode("utf-8")
        self.assertEqual(status, 200)
        for marker in (
            "Universe switching",
            "Classic Layered Architecture",
            "S-Core Component Directory",
            "Component Inspector node unbinding",
            "AI commentaries and AI Discuss",
            "Classic feedback without PAT",
            "Report landscape",
            'data-switch-universe="adaptive"',
            'data-switch-universe="classic"',
            'data-switch-universe="score"',
            'data-graph-filter="all"',
            'data-graph-filter="adaptive"',
            'data-graph-filter="classic"',
            'data-graph-filter="score"',
            'data-open-discuss="CP_OS"',
            'data-open-discuss="SCORE_CORE"',
            'id="ai-discuss-sidecar"',
            'id="classic-feedback-form"',
            'id="classic-run-loop"',
            'href="curation-report.html"',
            'href="extraction-reports.html"',
            'href="mutation-ledger.html"',
            'id="unbind-component"',
            'data-id="core"',
            "ara::core",
            'id="feedback-form"',
            'id="discuss-prompt"',
        ):
            self.assertIn(marker, text)
        self.assertNotIn('name="pat"', text)
        self.assertNotIn('name="github_token"', text)
        self.assertNotIn("github_pat_", text)

    def test_prompt_discuss_names_classic_and_score_ids(self):
        before = self._sentinels()
        status, body, _ = self._request(
            "POST",
            "/api/discuss",
            {
                "prompt": "Bitte CP_OS und SCORE_CORE nur aus diesem Kontext beschreiben.",
                "context": {
                    "component_id": "CP_OS",
                    "universe": "classic",
                    "page": "classic/os.html",
                },
            },
        )
        self.assertEqual(status, 200, body)
        self.assertEqual(body["generator"], "local-context-proposer")
        self.assertIsNone(body["model"])
        self.assertIn("CP_OS", body["proposal"]["identifiers"])
        self.assertIn("SCORE_CORE", body["proposal"]["identifiers"])
        self.assertFalse(body["canonical_mutation"])
        recorded = [item for item in self._ledger() if item["action"] == "discuss-proposal-recorded"]
        self.assertEqual(len(recorded), 1)
        self.assertEqual(self._sentinels(), before)

    def test_sidecar_chat_reads_classic_and_score_without_writing(self):
        classic_page = self.repo / "classic" / "os.html"
        classic_page.parent.mkdir()
        classic_page.write_text("CLASSIC-OS-SENTINEL\n", encoding="utf-8")
        score_page = self.repo / "score" / "core.html"
        score_page.parent.mkdir()
        score_page.write_text("SCORE-CORE-SENTINEL\n", encoding="utf-8")
        classic_record = self._plant_record("CP_OS", "Activate a task", "classic")
        score_record = self._plant_record("SCORE_CORE", "S-Core Core Execution Environment", "score")
        classic_bytes = classic_record.read_bytes()
        score_bytes = score_record.read_bytes()
        queue_one = (self.repo / "_src" / "spec" / "curation-queue" / "open" / "one.json").read_bytes()
        before = self._sentinels()

        rejected, rejected_body, _ = self._request(
            "POST",
            "/api/discuss",
            {"action": "chat", "record_id": "../CP_OS", "message": "Erkläre"},
        )
        self.assertEqual(rejected, 400, rejected_body)
        empty, _, _ = self._request(
            "POST",
            "/api/discuss",
            {"action": "chat", "record_id": "CP_OS", "message": "  "},
        )
        self.assertEqual(empty, 400)

        for record_id, snippet in (
            ("CP_OS", "Activate a task"),
            ("SCORE_CORE", "S-Core Core Execution Environment"),
        ):
            got, body, _ = self._request("GET", "/api/discuss?record_id=" + record_id)
            self.assertEqual(got, 200, body)
            self.assertTrue(body["ok"])
            self.assertEqual(body["context"]["record_id"], record_id)
            self.assertTrue(body["context"]["found"])
            self.assertIn(snippet, body["context"]["requirement_text"])
            self.assertFalse(body["canonical_mutation"])
            posted, reply, _ = self._request(
                "POST",
                "/api/discuss",
                {
                    "action": "chat",
                    "record_id": record_id,
                    "message": "Erkläre diese Anforderung einfach",
                },
            )
            self.assertEqual(posted, 200, reply)
            self.assertIn(record_id, reply["reply"])
            self.assertIn(snippet, reply["reply"])
            self.assertFalse(reply["canonical_mutation"])

        self.assertEqual(self._ledger(), [])
        self.assertEqual(classic_record.read_bytes(), classic_bytes)
        self.assertEqual(score_record.read_bytes(), score_bytes)
        self.assertEqual(classic_page.read_text(encoding="utf-8"), "CLASSIC-OS-SENTINEL\n")
        self.assertEqual(score_page.read_text(encoding="utf-8"), "SCORE-CORE-SENTINEL\n")
        self.assertEqual(
            (self.repo / "_src" / "spec" / "curation-queue" / "open" / "one.json").read_bytes(),
            queue_one,
        )
        self.assertFalse(self._queue("proposals").exists())
        self.assertEqual(self._sentinels(), before)

    def test_discuss_submit_appends_ledger_and_keeps_record_bytes(self):
        classic_record = self._plant_record("CP_OS", "Activate a task", "classic")
        before_bytes = classic_record.read_bytes()
        queue_one = (self.repo / "_src" / "spec" / "curation-queue" / "open" / "one.json").read_text(encoding="utf-8")
        queue_two = (self.repo / "_src" / "spec" / "curation-queue" / "open" / "two.json").read_text(encoding="utf-8")
        before = self._sentinels()

        status, body, _ = self._request(
            "POST",
            "/api/discuss",
            {
                "action": "submit",
                "record_id": "CP_OS",
                "suggestion": "Activate a task\n\nPrüfungshinweis: nur ergänzen, wenn die Verweise es decken.",
                "rationale": "Prüfungshinweis ohne Freigabe.",
            },
        )
        self.assertEqual(status, 200, body)
        self.assertFalse(body["proposal"]["auto_accepted"])
        self.assertEqual(body["proposal"]["status"], "proposed")
        self.assertFalse(body["canonical_mutation"])
        self.assertTrue((self.repo / body["path"]).is_file())
        self.assertEqual(classic_record.read_bytes(), before_bytes)
        self.assertEqual(
            (self.repo / "_src" / "spec" / "curation-queue" / "open" / "one.json").read_text(encoding="utf-8"),
            queue_one,
        )
        self.assertEqual(
            (self.repo / "_src" / "spec" / "curation-queue" / "open" / "two.json").read_text(encoding="utf-8"),
            queue_two,
        )
        recorded = [item for item in self._ledger() if item["action"] == "discuss-proposal-submitted"]
        self.assertEqual(len(recorded), 1)
        self.assertEqual(recorded[0]["details"]["record_id"], "CP_OS")
        self.assertEqual(self._sentinels(), before)

    def test_classic_feedback_without_pat_records_ledger_and_regenerates(self):
        classic_page = self.repo / "classic" / "os.html"
        classic_page.parent.mkdir()
        classic_page.write_text("CLASSIC-OS-SENTINEL\n", encoding="utf-8")
        score_record = self._plant_record("SCORE_CORE", "S-Core Core Execution Environment", "score")
        classic_record = self._plant_record("CP_OS", "Activate a task", "classic")
        classic_bytes = classic_record.read_bytes()
        score_bytes = score_record.read_bytes()
        before = self._sentinels()
        payload = self._feedback(
            feedback_text="Die Classic-Anforderung CP_OS sollte ActivateTask als Task-Aktivierung beschreiben.",
            page="classic/os.html",
            universe="classic",
            component_id="CP_OS",
            category="factual_correction",
        )

        rejected, _, _ = self._request(
            "POST",
            "/api/feedback",
            self._feedback(
                submitter=None,
                feedback_text="Ohne Absender zu CP_OS.",
                page="classic/os.html",
                universe="classic",
                component_id="CP_OS",
            ),
        )
        self.assertEqual(rejected, 400)
        self.assertEqual(self._ledger(), [])

        status, body, _ = self._request("POST", "/api/feedback", payload)
        self.assertEqual(status, 201, body)
        stored = json.loads((self.repo / body["path"]).read_text(encoding="utf-8"))
        self.assertEqual(stored["demo_context"]["component_id"], "CP_OS")
        self.assertEqual(stored["demo_context"]["universe"], "classic")
        self.assertNotIn("pat", stored)
        self.assertNotIn("github_token", stored)
        self.assertNotIn("authorization", stored)

        again, replay, _ = self._request("POST", "/api/feedback", payload)
        self.assertEqual(again, 200, replay)
        self.assertTrue(replay["idempotent_replay"])
        feedback_entries = [item for item in self._ledger() if item["action"] == "user-feedback-received"]
        self.assertEqual(len(feedback_entries), 1)
        self.assertEqual(feedback_entries[0]["details"]["component_id"], "CP_OS")
        self.assertEqual(feedback_entries[0]["details"]["universe"], "classic")

        changed, changed_body, _ = self._request(
            "POST",
            "/api/curate",
            {
                "decision": "change_stereotype",
                "target_id": "CP_OS",
                "stereotype": "protocol",
                "rationale": "nur Envelope",
            },
        )
        self.assertEqual(changed, 200, changed_body)
        unbound, _, _ = self._request(
            "POST",
            "/api/curate",
            {"decision": "delete_mapping", "target_id": "SCORE_CORE", "rationale": "lösen"},
        )
        self.assertEqual(unbound, 200)
        self.assertEqual(classic_record.read_bytes(), classic_bytes)
        self.assertEqual(score_record.read_bytes(), score_bytes)
        self.assertTrue(score_record.is_file())

        loop_status, loop_body, _ = self._request("POST", "/api/feedback-loop/run", {})
        self.assertEqual(loop_status, 200, loop_body)
        summary = loop_body["summary"]
        self.assertTrue(summary["ok"])
        self.assertFalse(summary["canonical_mutation"])
        self.assertGreaterEqual(summary["comments_written"], 1)
        matched = []
        for path in self._queue("comments").glob("*.json"):
            item = json.loads(path.read_text(encoding="utf-8"))
            if item.get("component_id") == "CP_OS":
                matched.append(item)
        self.assertTrue(matched)
        self.assertTrue(any(item["stereotype"] == "protocol" for item in matched))
        self.assertIn("CP_OS", matched[0]["text"])
        self.assertTrue(all(item["canonical_mutation"] is False for item in matched))
        regenerated = [item for item in self._ledger() if item["action"] == "feedback-loop-regenerated"]
        self.assertEqual(len(regenerated), 1)
        self.assertEqual(classic_page.read_text(encoding="utf-8"), "CLASSIC-OS-SENTINEL\n")
        self.assertEqual(classic_record.read_bytes(), classic_bytes)
        self.assertEqual(score_record.read_bytes(), score_bytes)
        self.assertEqual(self._sentinels(), before)


class PublishedTreeTest(unittest.TestCase):
    """Read-only checks against the real publication tree."""

    watched = (
        "_src/output/mutation-audit-ledger.jsonl",
        "docs/evidence/mutation-audit-ledger.jsonl",
        "_src/spec/records/classic/CP_OS.json",
        "_src/spec/records/score/SCORE_CORE.json",
        "classic/os.html",
        "classic/index.html",
        "score/index.html",
        "score/core.html",
        "mutation-ledger.html",
        "curation-report.html",
        "extraction-reports.html",
    )

    @classmethod
    def setUpClass(cls):
        cls.httpd = SERVE.build_server(ROOT, "127.0.0.1", 0)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.before = cls._fingerprints()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)
        if cls.thread.is_alive():
            raise RuntimeError("published-tree server thread did not stop")

    @classmethod
    def _fingerprints(cls):
        digest = {}
        for relative in cls.watched:
            path = ROOT / relative
            if path.is_file():
                digest[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            else:
                digest[relative] = None
        return digest

    def _request(self, method, path, payload=None):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=20)
        try:
            headers = {}
            body = None
            if payload is not None:
                body = json.dumps(payload).encode("utf-8")
                headers["Content-Type"] = "application/json"
                headers["Content-Length"] = str(len(body))
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            data = response.read()
            parsed = None
            if "application/json" in (response.getheader("Content-Type") or ""):
                parsed = json.loads(data.decode("utf-8"))
            return response.status, parsed, data
        finally:
            connection.close()

    def _assert_untouched(self):
        self.assertEqual(self._fingerprints(), self.before)

    def test_universes_render_shell_chrome_and_active_state(self):
        cases = (
            ("/adaptive/index.html", 'class="cur" href="../adaptive/index.html"', ">Adaptive</a>"),
            ("/classic/index.html", 'class="cur" href="../classic/index.html"', ">Classic</a>"),
            ("/score/index.html", 'class="cur" href="../score/index.html"', ">S-Core</a>"),
        )
        for path, current, label in cases:
            status, _, data = self._request("GET", path)
            text = data.decode("utf-8")
            self.assertEqual(status, 200, path)
            self.assertIn('class="shell"', text, path)
            self.assertIn("shell-domains", text, path)
            self.assertIn("shell-universe", text, path)
            self.assertIn(current, text, path)
            self.assertIn(label, text, path)
            self.assertIn("data-theme-toggle", text, path)
            self.assertIn("data-density-toggle", text, path)
        self._assert_untouched()

    def test_classic_score_and_ledger_pages_are_served(self):
        pages = (
            "/classic/os.html",
            "/classic/rte.html",
            "/classic/com.html",
            "/score/core.html",
            "/score/communication.html",
            "/score/process.html",
            "/mutation-ledger.html",
        )
        for path in pages:
            status, _, data = self._request("GET", path)
            self.assertEqual(status, 200, path)
            self.assertIn(b"<html", data[:400], path)
        classic, _, classic_body = self._request("GET", "/classic/os.html")
        self.assertEqual(classic, 200)
        self.assertIn(b'id="CP_OS"', classic_body)
        self.assertIn(b"discuss.js", classic_body)
        score, _, score_body = self._request("GET", "/score/index.html")
        self.assertEqual(score, 200)
        self.assertIn(b'id="SCORE_CORE"', score_body)
        self.assertIn(b"discuss.js", score_body)
        missing, _, missing_body = self._request("GET", "/classic/../../etc/passwd")
        self.assertEqual(missing, 404)
        self.assertNotIn(b"root:x:", missing_body)
        self._assert_untouched()

    def test_eleven_languages_have_dir_attributes(self):
        languages = ("de", "en", "es", "pt", "fr", "ru", "ar", "hi", "ko", "zh", "nl")
        self.assertEqual(len(languages), 11)
        for lang in languages:
            prefix = "" if lang == "de" else "/" + lang
            for kind in ("classic", "score"):
                path = prefix + "/" + kind + "/index.html"
                status, _, data = self._request("GET", path)
                text = data.decode("utf-8")
                self.assertEqual(status, 200, path)
                tag = re.search(r"<html\b[^>]*>", text)
                self.assertIsNotNone(tag, path)
                html_tag = tag.group(0)
                self.assertIn('lang="' + lang + '"', html_tag, path)
                if lang == "ar":
                    self.assertIn('dir="rtl"', html_tag, path)
                else:
                    self.assertNotIn('dir="rtl"', html_tag, path)
                    if "dir=" in html_tag:
                        self.assertIn('dir="ltr"', html_tag, path)
        self._assert_untouched()

    def test_restyled_reports_have_shell_and_theme_switches(self):
        for path in ("/curation-report.html", "/extraction-reports.html", "/mutation-ledger.html"):
            status, _, data = self._request("GET", path)
            text = data.decode("utf-8")
            self.assertEqual(status, 200, path)
            self.assertIn("shell-domains", text, path)
            self.assertIn("data-theme-toggle", text, path)
            self.assertIn("data-density-toggle", text, path)
            self.assertIn('data-theme="light"', text, path)
            self.assertIn('data-density="comfortable"', text, path)
        self._assert_untouched()

    def test_live_discuss_sidecar_for_classic_and_score_ids_is_read_only(self):
        status, body, _ = self._request("GET", "/api/status")
        self.assertEqual(status, 200, body)
        rows = {row["id"]: row for row in body["universes"]}
        self.assertTrue(rows["adaptive"]["present"])
        self.assertTrue(rows["classic"]["present"])
        self.assertTrue(rows["score"]["present"])
        self.assertFalse(body["canonical_mutation"])

        for record_id, snippet in (
            ("CP_OS", "This service determines the OS - Application"),
            ("SCORE_CORE", "S-Core Core Execution Environment"),
        ):
            got, context, _ = self._request("GET", "/api/discuss?record_id=" + record_id)
            self.assertEqual(got, 200, context)
            self.assertTrue(context["context"]["found"], record_id)
            self.assertEqual(context["context"]["record_id"], record_id)
            self.assertIn(snippet, context["context"]["requirement_text"])
            self.assertFalse(context["canonical_mutation"])
            posted, reply, _ = self._request(
                "POST",
                "/api/discuss",
                {
                    "action": "chat",
                    "record_id": record_id,
                    "message": "Erkläre diese Anforderung einfach",
                },
            )
            self.assertEqual(posted, 200, reply)
            self.assertIn(record_id, reply["reply"])
            self.assertIn(snippet, reply["reply"])
            self.assertFalse(reply["canonical_mutation"])
        self._assert_untouched()


if __name__ == "__main__":
    unittest.main()
