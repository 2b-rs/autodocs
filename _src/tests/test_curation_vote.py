#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_curation_vote.py — Tests for mini-curation vote API and ingest."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
TOOLS_DIR = SRC_DIR / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import dependency_graph as dg
import curation_flags as cf
import curation_ingest as ci
import context_distributor as cd


class CurationVoteTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # Patch graph root
        self._orig_graph_root = dg.GRAPH_ROOT
        self._orig_edges = dg.EDGES_FILE
        self._orig_dismissed = dg.DISMISSED_FILE
        dg.GRAPH_ROOT = self.root / "spec" / "graph"
        dg.EDGES_FILE = dg.GRAPH_ROOT / "edges.jsonl"
        dg.DISMISSED_FILE = dg.GRAPH_ROOT / "dismissed.jsonl"

        # Patch queue dirs
        self._orig_queue = cf.QUEUE
        self._orig_open = cf.OPEN_DIR
        self._orig_done = cf.DONE_DIR
        cf.QUEUE = self.root / "spec" / "curation-queue"
        cf.OPEN_DIR = cf.QUEUE / "open"
        cf.DONE_DIR = cf.QUEUE / "done"
        cf._ensure_dirs()

    def tearDown(self):
        dg.GRAPH_ROOT = self._orig_graph_root
        dg.EDGES_FILE = self._orig_edges
        dg.DISMISSED_FILE = self._orig_dismissed
        cf.QUEUE = self._orig_queue
        cf.OPEN_DIR = self._orig_open
        cf.DONE_DIR = self._orig_done
        self._tmp.cleanup()

    def test_confirm_and_dismiss_edges(self):
        # 1. Confirm edge
        edge_confirm = dg.add_edge("reviewer:alice", "SNIP_LinIf_01", "confirms", meta={"rationale": "Valid"})
        self.assertEqual(edge_confirm["edge_type"], "confirms")
        self.assertEqual(edge_confirm["to"], "SNIP_LinIf_01")
        self.assertFalse(dg.is_dismissed("SNIP_LinIf_01"))

        # 2. Dismiss edge and node dismissal
        dg.dismiss_node("SNIP_LinIf_02", reason="Not applicable to LinIf")
        self.assertTrue(dg.is_dismissed("SNIP_LinIf_02"))
        self.assertFalse(dg.can_derive_from("SNIP_LinIf_02"))

        edge_dismiss = dg.add_edge("reviewer:bob", "SNIP_LinIf_02", "dismisses", meta={"rationale": "Misleading"})
        self.assertEqual(edge_dismiss["edge_type"], "dismisses")

        # 3. Read back edges
        edges = dg.list_edges()
        self.assertEqual(len(edges), 2)

    def test_ingest_queue_snippets(self):
        # Create an open curation flag for a snippet
        flag_path = cf.OPEN_DIR / "discuss-SNIP_LinIf_03.json"
        flag_data = {
            "schema": "curation-flag@v1",
            "id": "discuss-SNIP_LinIf_03",
            "target_record": "SNIP_LinIf_03",
            "item_kind": "evidence-snippet",
            "outcome": "proposed_change",
            "rationale": "Verified as invalid in discussion",
            "created": "2026-10-01T12:00:00Z",
        }
        flag_path.write_text(json.dumps(flag_data, ensure_ascii=False), encoding="utf-8")

        # Dry run check
        dry = ci.ingest_queue_snippets(apply=False)
        self.assertEqual(dry["status"], "ok")
        self.assertEqual(dry["snippets_processed"], 1)
        self.assertEqual(dry["ergebnisse"][0]["action"], "would_dismiss")
        self.assertTrue(flag_path.exists())
        self.assertFalse(dg.is_dismissed("SNIP_LinIf_03"))

        # Apply run
        applied = ci.ingest_queue_snippets(apply=True)
        self.assertEqual(applied["status"], "ok")
        self.assertEqual(applied["snippets_processed"], 1)
        self.assertEqual(applied["ergebnisse"][0]["action"], "dismissed_and_completed")
        self.assertFalse(flag_path.exists())  # moved to done
        self.assertTrue(dg.is_dismissed("SNIP_LinIf_03"))

    def test_http_vote_endpoints(self):
        import serve
        import threading
        import urllib.request
        orig_dg_root = serve.DG.GRAPH_ROOT
        orig_dg_edges = serve.DG.EDGES_FILE
        orig_dg_dismissed = serve.DG.DISMISSED_FILE
        serve.DG.GRAPH_ROOT = self.root / "spec" / "graph"
        serve.DG.EDGES_FILE = serve.DG.GRAPH_ROOT / "edges.jsonl"
        serve.DG.DISMISSED_FILE = serve.DG.GRAPH_ROOT / "dismissed.jsonl"
        server = serve.build_server(self.root, "127.0.0.1", 0)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        try:
            # 1. POST confirm vote
            data = json.dumps({"snippet_id": "SNIP_Test_01", "vote": "confirm", "reviewer": "alice"}).encode("utf-8")
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/curation/vote", data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(res["ok"])
            self.assertEqual(res["vote"], "confirm")

            # 2. POST dismiss vote
            data = json.dumps({"snippet_id": "SNIP_Test_02", "vote": "dismiss", "reviewer": "bob", "rationale": "Irrelevant"}).encode("utf-8")
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/curation/vote", data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(res["ok"])
            self.assertTrue(res["is_dismissed"])

            # 2b. POST dismiss vote on constituting spec record
            data = json.dumps({"record_id": "SWS_LinIf_00198", "vote": "dismiss", "reviewer": "carol", "rationale": "Nicht konstituierend"}).encode("utf-8")
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/curation/vote", data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(res["ok"])
            self.assertTrue(res["is_dismissed"])

            # 3. GET votes
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/curation/votes")
            with urllib.request.urlopen(req, timeout=5) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(res["ok"])
            self.assertEqual(res["votes"]["SNIP_Test_01"]["confirms"], 1)
            self.assertEqual(res["votes"]["SNIP_Test_02"]["dismisses"], 1)
            self.assertTrue(res["votes"]["SNIP_Test_02"]["is_dismissed"])
            self.assertEqual(res["votes"]["SWS_LinIf_00198"]["dismisses"], 1)
            self.assertTrue(res["votes"]["SWS_LinIf_00198"]["is_dismissed"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            serve.DG.GRAPH_ROOT = orig_dg_root
            serve.DG.EDGES_FILE = orig_dg_edges
            serve.DG.DISMISSED_FILE = orig_dg_dismissed

    def test_dossier_modal_and_spec_record_links(self):
        """Verifies that the dossier is rendered as a clean modal dialog, not in the body text flow, and spec records are linkified."""
        import context_distributor as cd
        dossier_file = SRC_DIR / "ai" / "dossiers" / "classic" / "modules" / "linif.json"
        self.assertTrue(dossier_file.exists())
        with open(dossier_file, "r", encoding="utf-8") as f:
            dossier = json.load(f)

        html = cd.generiere_dossier_html(dossier)
        # 1. Must be a <dialog> modal, NOT an inline <div>
        self.assertTrue(html.strip().startswith('<dialog id="dossier-modal-linif"'))
        self.assertNotIn('<div class="ai-context-dossier"', html)

        # 2. Must contain clickable record links
        self.assertIn('class="rec-jump-link record-item-chip"', html)
        self.assertIn('href="#SWS_LinIf_00198"', html)
        self.assertIn('href="#SWS_LinIf_00201"', html)

        # 3. Must linkify cross-module references in snippets
        self.assertIn('href="linsm.html#SWS_LinSM_00079"', html)
        self.assertIn('href="lin.html#SWS_Lin_00098"', html)
        self.assertIn('href="#SWS_LinIf_00503"', html)

        # 4. Constituting records must be fulltext cards with syntax, desc, and curation toolbar
        self.assertIn('class="snippet-card constituting-record-card', html)
        self.assertIn('data-is-constituting="true"', html)
        self.assertIn('data-snippet-id="SWS_LinIf_00198"', html)
        self.assertIn('data-name="LinIf_Init"', html)
        self.assertIn('data-action="discuss" data-snippet="SWS_LinIf_00198"', html)
        self.assertIn('data-action="confirm" data-snippet="SWS_LinIf_00198"', html)
        self.assertIn('data-action="dismiss" data-snippet="SWS_LinIf_00198"', html)

        # 4b. Filter- & Ansichts-Toolbar (Live-Suche, Pills, View-Toggles, Chevrons)
        self.assertIn('id="dossier-toolbar"', html)
        self.assertIn('id="dossier-search-input"', html)
        self.assertIn('data-filter-kind="all"', html)
        self.assertIn('data-filter-status="all"', html)
        self.assertIn('id="btn-view-compact"', html)
        self.assertIn('id="btn-view-detailed"', html)
        self.assertIn('id="btn-toggle-all-expand"', html)
        self.assertIn('id="dossier-visible-count"', html)
        self.assertIn('class="card-chevron"', html)

        # 5. Workbench two-pane layout: viewer pane + companion chat pane (geometry preserved)
        self.assertIn('class="dossier-workbench-layout"', html)
        self.assertIn('class="dossier-viewer-pane"', html)
        self.assertIn('class="dossier-chat-pane" id="dossier-chat-pane"', html)
        self.assertIn('class="btn-toggle-workbench-chat"', html)
        self.assertIn('id="chat-attached-chips"', html)
        self.assertIn('id="btn-clear-attached"', html)
        self.assertIn('id="chat-pane-form"', html)

        # 6. No inline chat panel inside individual cards (destroys geometry)
        self.assertNotIn('class="snippet-discuss-panel"', html)

    def test_browser_store_curation_package_and_github_issue_ingest(self):
        """Validates that curation requests stored in the browser store (ara-review-package-v1)
        strictly comply with the review-package@v1 schema and are ingested into curation-queue/open."""
        package_payload = {
            "schema": "review-package@v1",
            "identity": "self_declared",
            "submitted_at": "2026-10-01T18:30:00Z",
            "decisions": [
                {
                    "id": "SWS_LinIf_00004",
                    "kind": "curation_request",
                    "outcome": "reject",
                    "decided_by": "Curator",
                    "identity": "self_declared",
                    "decided_at": "2026-10-01T18:30:00Z",
                    "rationale": "Nicht konstituierend für LinIf; gehört in Treiber-Abstraktion.",
                    "decision_basis": {
                        "target_module": "LinIf",
                        "item_id": "SWS_LinIf_00004",
                        "source_name": "LinIf_GetVersionInfo",
                        "source_document": "AUTOSAR_SWS_LINInterface.pdf",
                        "is_constituting": True,
                        "proposal": "[STATUS: EXCLUDE_CONSTITUTING]"
                    }
                },
                {
                    "id": "SNIP_LinIf_LinSM_ScheduleRequest_01",
                    "kind": "curation_request",
                    "outcome": "reject",
                    "decided_by": "Curator",
                    "identity": "self_declared",
                    "decided_at": "2026-10-01T18:30:00Z",
                    "rationale": "Veralteter Schnittstellenbezug; Schedule-Wechsel erfolgt über LinSM-Task.",
                    "decision_basis": {
                        "target_module": "LinIf",
                        "item_id": "SNIP_LinIf_LinSM_ScheduleRequest_01",
                        "source_element": "SWS_LinSM_00079",
                        "source_document": "AUTOSAR_SWS_LINStateManager",
                        "is_constituting": False,
                        "proposal": "[STATUS: EXCLUDE_OR_REVISE]"
                    }
                }
            ]
        }

        # 1. Package validation
        errors = ci.validate_package(package_payload)
        self.assertEqual(errors, [], f"Validierungsfehler im Paket: {errors}")

        # 2. Ingest via JSON file export
        pkg_file = self.root / "curation_package.json"
        pkg_file.write_text(json.dumps(package_payload, indent=2), encoding="utf-8")

        res = ci.ingest(pkg_file, apply=True, from_issue_body=False)
        self.assertEqual(res["fehler"], [])
        self.assertEqual(len(res["ergebnisse"]), 2)
        self.assertEqual(res["ergebnisse"][0]["status"], "ok")
        self.assertEqual(res["ergebnisse"][1]["status"], "ok")

        # Verify curation flags written to open queue
        flag1 = cf.OPEN_DIR / "SWS_LinIf_00004.json"
        flag2 = cf.OPEN_DIR / "SNIP_LinIf_LinSM_ScheduleRequest_01.json"
        self.assertTrue(flag1.exists(), f"Flag {flag1} wurde nicht angelegt")
        self.assertTrue(flag2.exists(), f"Flag {flag2} wurde nicht angelegt")

        # 3. Ingest via GitHub Issue Body
        issue_body = f"""### Curation Review Submission

Die folgenden Entscheidungen wurden im Browser getroffen:

```json
{json.dumps(package_payload, indent=2)}
```

Bitte prüfen und in die Queue überführen.
"""
        issue_file = self.root / "issue-42.md"
        issue_file.write_text(issue_body, encoding="utf-8")

        # Clean flags for re-ingest test
        flag1.unlink()
        flag2.unlink()

        res_issue = ci.ingest(issue_file, apply=True, from_issue_body=True)
        self.assertEqual(len(res_issue["ergebnisse"]), 2)
        self.assertEqual(res_issue["ergebnisse"][0]["status"], "ok")
        self.assertTrue(flag1.exists())
        self.assertTrue(flag2.exists())

    def test_fold_js_curation_and_dismiss_invariants(self):
        """Ensures that in fold.js:
        1. Dismiss button does NOT open the chat window.
        2. Chat close / toggle clears attached discussion items and resets badges.
        3. Workbench submit stores into ara-review-package-v1."""
        fold_js = (SRC_DIR.parent / "fold.js").read_text(encoding="utf-8")

        # 1. Dismiss button handler must not call openDiscussionForItem
        dismiss_block = fold_js[fold_js.find('data-action="dismiss"'):fold_js.find('data-action="discuss"')]
        self.assertNotIn("openDiscussionForItem", dismiss_block, "Dismiss button darf den Chat nicht öffnen!")

        # 2. Closing or toggling chat must reset discussion
        self.assertIn('attachedDiscussionItems.clear()', fold_js)
        self.assertIn('btn-close-chat-pane', fold_js)
        self.assertIn('btn-toggle-workbench-chat', fold_js)

        # 3. Must use browser review store ara-review-package-v1
        self.assertIn('"ara-review-package-v1"', fold_js)
        self.assertIn('kind: "curation_request"', fold_js)

    def test_undismiss_node_and_reset_vote(self):
        """Ensures that undismiss_node restores a node and clears dismissed status."""
        dg.dismiss_node("SNIP_LinIf_03", reason="Temporary objection")
        self.assertTrue(dg.is_dismissed("SNIP_LinIf_03"))
        
        # Undismiss
        undismissed = dg.undismiss_node("SNIP_LinIf_03")
        self.assertTrue(undismissed)
        self.assertFalse(dg.is_dismissed("SNIP_LinIf_03"))

    def test_ai_discuss_justification_enforcement(self):
        """Ensures that empty/unsubstantiated criticism does not generate a proposal suggestion,
        while a substantive technical explanation does."""
        import ai_discuss as ad
        context = {
            "record_id": "SNIP_LinIf_01",
            "found": True,
            "is_snippet": True,
            "module": "LinIf",
            "snippet_meta": {
                "source_element": "SWS_LinSM_00079",
                "source_document": "AUTOSAR_SWS_LINStateManager",
                "source_page": 27,
                "category": "inbound",
                "relevance_rationale": "ScheduleRequest",
            }
        }

        # 1. Unsubstantiated criticism -> No suggestion offered
        empty_crit = ad.contextual_reply("Das ist falsch!", context)
        self.assertIsNone(empty_crit["suggestion"], "Unbegründete Beanstandung darf keinen Kurationsvorschlag auslösen")
        self.assertIn("stichhaltige technische Begründung benötigt", empty_crit["reply"])

        # 2. Substantiated technical explanation -> AI accepts and offers proposal
        subst_crit = ad.contextual_reply(
            "Ich beanstande dieses Snippet, weil die Schichtentrennung zwischen BSW und Treiber verletzt ist und der Aufruf redundant ist.",
            context
        )
        self.assertIsNotNone(subst_crit["suggestion"], "Fachlich begründete Beanstandung muss einen Kurationsvorschlag erhalten")
        self.assertIn("STATUS: EXCLUDE", subst_crit["suggestion"])

    def test_dossier_views_and_multiselection(self):
        """Ensures that generiere_dossier_html contains:
        1. View Mode Switcher with 'raw' mode as default active tab.
        2. Plain text prompt in raw view container.
        3. Multiselection action bar with batch buttons.
        4. Both Exit 1 (queue) and Exit 2 (direct local marking) in proposal box."""
        import context_distributor as cd
        sample_dossier = {
            "schema_version": "1.0",
            "target_module": "LinIf",
            "dossier_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "reproducibility": {
                "display_name": "Gemini 3.8 Flash (High)",
                "thinking_effort": "high",
                "temperature": 0.0,
                "source_documents": ["AUTOSAR_SWS_LINInterface.pdf"]
            },
            "spec_records": [
                {
                    "id": "SWS_LinIf_00004",
                    "blocks": [
                        {"t": "html", "html": '<h3 class="recname"><span class="kind">api function</span> LinIf_Init <a href="...">[SWS_LinIf_00004]</a></h3>'},
                        {"t": "html", "html": '<pre class="syntax">void LinIf_Init(const LinIf_ConfigType* ConfigPtr)</pre>'},
                        {"t": "html", "html": '<div class="desc"><p>Initializes the LIN Interface.</p></div>'}
                    ]
                }
            ],
            "inbound_snippets": [
                {
                    "id": "SNIP_LinIf_01",
                    "source_element": "SWS_LinSM_00079",
                    "source_document": "AUTOSAR_SWS_LINStateManager",
                    "source_page": 27,
                    "category": "inbound",
                    "relevance_score": 0.95,
                    "relevance_rationale": "ScheduleRequest",
                    "verbatim_text": "LinSM calls LinIf_ScheduleRequest."
                }
            ]
        }

        html = cd.generiere_dossier_html(sample_dossier)

        # 1. View Mode Switcher & Default Prompt mode (1:1 LLM Prompt) + Output & Vergleich tab + Editor
        self.assertIn('class="dossier-mode-switcher"', html)
        self.assertIn('data-view-mode="prompt" role="tab" aria-selected="true"', html)
        self.assertIn('data-view-mode="output"', html)
        self.assertIn('data-view-mode="editor"', html)
        self.assertIn('id="dossier-view-prompt"', html)
        self.assertIn('id="dossier-view-output"', html)
        self.assertIn('id="raw-prompt-textarea"', html)
        self.assertIn('[SYSTEM PROMPT]', html)
        self.assertIn('[USER PROMPT]', html)
        self.assertIn('FOLGENDE RICHTLINIEN SIND STRIKT BINDEND', html)
        self.assertIn('class="raw-subtab-bar"', html)
        self.assertIn('id="subtab-btn-current"', html)
        self.assertIn('id="subtab-preview-1"', html)
        self.assertIn('id="raw-tab-link-badge"', html)
        self.assertIn('id="raw-pane-compare-diff"', html)

        # 2. Multiselection Bar
        self.assertIn('id="dossier-selection-bar"', html)
        self.assertIn('id="btn-batch-confirm"', html)
        self.assertIn('id="btn-batch-dismiss"', html)
        self.assertIn('id="btn-batch-discuss"', html)
        self.assertIn('class="card-select-checkbox"', html)

        # 3. Two Exits in Proposal Box
        self.assertIn('id="btn-submit-workbench-proposal"', html)
        self.assertIn('Exit 1: In Curation-Queue einreihen', html)
        self.assertIn('id="btn-apply-justified-locally"', html)
        self.assertIn('Exit 2: Direkt als „begründet“ im Dossier vermerken', html)
        self.assertIn('id="btn-dismiss-proposal"', html)

        # 4. Check fold.js contract for multiselection, clearable badges, 3-subtab diff engine and proposal exits
        fold_js = (SRC_DIR.parent / "fold.js").read_text(encoding="utf-8")
        self.assertIn('selectedSnippetIds', fold_js)
        self.assertIn('btn-clear-badge', fold_js)
        self.assertIn('applyProposalLocallyJustified', fold_js)
        self.assertIn('switchDossierViewMode', fold_js)
        self.assertIn('renderSideBySideDiff', fold_js)
        self.assertIn('getDiffOpcodes', fold_js)
        self.assertIn('computeWordDiff', fold_js)
        self.assertIn('rawWorkbenchState', fold_js)
        self.assertIn('startPreviewGeneration', fold_js)
        self.assertIn('linkCompareTabs', fold_js)
        self.assertIn('exitCompareMode', fold_js)

    def test_ai_execute_prompt_endpoint(self):
        """Verifies that POST /api/ai/execute_prompt returns diffable generated HTML and parsed results."""
        import serve
        import threading
        import urllib.request
        server = serve.build_server(self.root, "127.0.0.1", 0)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            req_data = json.dumps({
                "prompt": "Test Option A Prompt",
                "mock": True,
                "module": "LinIf"
            }).encode("utf-8")
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/ai/execute_prompt",
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(res["ok"])
            self.assertEqual(res["provider"], "mock")
            self.assertEqual(res["model"], "mock-generator-v1")
            self.assertIn("generated_html", res)
            self.assertIn("original_html", res)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_ai_execute_prompt_streaming_4hz(self):
        """Verifies that POST /api/ai/execute_prompt with stream=True streams incremental events at >= 4Hz."""
        import serve
        import threading
        import urllib.request
        server = serve.build_server(self.root, "127.0.0.1", 0)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            req_data = json.dumps({
                "prompt": "Test Streaming 4Hz",
                "mock": True,
                "module": "LinIf",
                "stream": True
            }).encode("utf-8")
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/ai/execute_prompt",
                data=req_data,
                headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                self.assertIn("text/event-stream", resp.headers.get("Content-Type", ""))
                events = []
                for line in resp:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: "):
                        events.append(json.loads(line_str[6:].strip()))

            self.assertGreaterEqual(len(events), 4)
            complete_ev = next((e for e in events if e.get("event") == "complete"), None)
            self.assertIsNotNone(complete_ev)
            self.assertTrue(complete_ev["ok"])
            self.assertEqual(complete_ev["effective_hz"], 4.0)
            self.assertIn("generated_html", complete_ev)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


    def test_lin_cluster_guide_and_dossier_modal(self):
        """Verifies that the LIN cluster guide, SVG diagram, and cluster dossier workbench modal are fully generated and valid."""
        cluster_dossier_file = SRC_DIR / "ai" / "dossiers" / "classic" / "clusters" / "lin.json"
        self.assertTrue(cluster_dossier_file.exists(), "LIN cluster dossier file should exist")

        with open(cluster_dossier_file, "r", encoding="utf-8") as f:
            dossier = json.load(f)

        self.assertEqual(dossier.get("target_cluster"), "LIN")
        self.assertTrue(dossier.get("is_cluster"))
        self.assertEqual(len(dossier.get("cluster_modules", [])), 4)

        # 75 constituent records across all 4 LIN modules
        extracted_records = dossier.get("extracted_records", [])
        self.assertEqual(len(extracted_records), 75)
        mod_counts = {}
        for r in extracted_records:
            mod_counts[r["module"]] = mod_counts.get(r["module"], 0) + 1
        self.assertEqual(mod_counts.get("Lin"), 17)
        self.assertEqual(mod_counts.get("LinIf"), 35)
        self.assertEqual(mod_counts.get("LinSM"), 12)
        self.assertEqual(mod_counts.get("LinTrcv"), 11)

        # 8 pinned inbound snippets
        snippets = dossier.get("inbound_snippets", [])
        self.assertEqual(len(snippets), 8)

        # Render cluster dossier workbench HTML
        html = cd.generiere_dossier_html(dossier)
        self.assertTrue(html.strip().startswith('<dialog id="dossier-modal-cluster-lin"'))
        self.assertIn('Agenten-Kontext &amp; Nachweis-Dossier (Cluster LIN)', html)
        self.assertIn('Konstituierende Spezifikations-Records des Clusters (75 APIs &amp; Typen aus 4 Modulen)', html)

        # Cross-module jump links from cluster page
        self.assertIn('href="modules/lin.html#SWS_Lin_00098"', html)
        self.assertIn('href="modules/linif.html#SWS_LinIf_00198"', html)
        self.assertIn('href="modules/linsm.html#SWS_LinSM_00079"', html)
        self.assertIn('href="modules/lintrcv.html#SWS_LinTrcv_00015"', html)
        self.assertIn('class="chip-module"', html)

        # Verify page generation on classic/lin.html
        lin_html_file = SRC_DIR.parent / "classic" / "lin.html"
        self.assertTrue(lin_html_file.exists())
        lin_html = lin_html_file.read_text(encoding="utf-8")
        self.assertIn('id="ai-cluster-guide-lin"', lin_html)
        self.assertIn('Cluster Guide', lin_html)
        self.assertIn('data-dossier-target="dossier-modal-cluster-lin"', lin_html)
        self.assertIn('id="diag-01"', lin_html)
        self.assertIn('<svg', lin_html)
        self.assertIn('id="dossier-modal-cluster-lin"', lin_html)


if __name__ == "__main__":
    unittest.main()


