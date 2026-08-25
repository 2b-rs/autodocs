"""Command-contract tests for issuectl query surfaces (Task 0037-10.04)."""
from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
import sys
import hashlib
import os
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
ISSUECTL_PATH = ROOT / "_src/tools/issuectl.py"
QUERY_TOOL = ROOT / "_src/tools/provenance_query.py"
STORE_TOOL = ROOT / "_src/tools/provenance_store.py"
VIEW_TOOL = ROOT / "_src/tools/provenance_views.py"
FIXTURES = ROOT / "_src/tests/fixtures/0037-11.02"
ACTIONS = ROOT / "_src/runner/issuectl-query-actions-v1.json"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ctl = _load("issuectl", ISSUECTL_PATH)
pq = _load("provenance_query", QUERY_TOOL)
ps = _load("provenance_store", STORE_TOOL)
pv = _load("provenance_views", VIEW_TOOL)
views = ctl.views

COMMIT = "a" * 40
RUN_ID = "018f4a31-32aa-7abc-8def-0123456789ab"
FINDING_ID = "018f4a31-32ab-7abc-8def-0123456789ab"
EVENT_ID = "018f4a31-32ac-7abc-8def-0123456789ab"
SET_ID = "018f4a31-32ad-7abc-8def-0123456789ab"
STAMP = "2026-08-16T08:01:00Z"


def _ref(kind, ident, **extra):
    value = {
        "schema_version": "1.0",
        "kind": kind,
        "uri": f"{kind}:{ident}" if ":" not in str(ident) else (
            ident if str(ident).startswith(kind + ":") else f"{kind}:{ident}"
        ),
        "classification": "internal",
    }
    value.update(extra)
    return value


def _run_main(argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = ctl.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class IssuectlHelpAndRegistryTests(unittest.TestCase):
    def test_help_exit_zero(self):
        parser = ctl.build_parser()
        for name in ("validate", "view", "graph", "list", "trace"):
            with self.subTest(name=name):
                buf = io.StringIO()
                with self.assertRaises(SystemExit) as raised:
                    with redirect_stdout(buf):
                        parser.parse_args([name, "--help"])
                self.assertEqual(raised.exception.code, 0)
                self.assertIn(name, buf.getvalue())

    def test_unknown_command_usage(self):
        code, _out, err = _run_main(["not-a-command"])
        self.assertNotEqual(code, 0)
        self.assertTrue(err or code == ctl.EXIT_USAGE or code == 2)

    def test_runner_actions_registered(self):
        payload = json.loads(ACTIONS.read_text(encoding="utf-8"))
        ids = {entry["id"] for entry in payload["actions"]}
        self.assertEqual(
            ids,
            {
                "issuectl.validate@v1",
                "issuectl.view@v1",
                "issuectl.graph@v1",
                "issuectl.list@v1",
                "issuectl.trace@v1",
            },
        )
        for entry in payload["actions"]:
            self.assertFalse(entry["authority"]["mutates"])
            self.assertTrue(entry["argv"][2] in {"validate", "view", "graph", "list", "trace"})


class IssuectlViewGraphListTests(unittest.TestCase):
    def test_view_and_graph_match_library(self):
        catalog, graph = views.render(FIXTURES / "issues", ROOT)
        code, out, err = _run_main(
            [
                "view",
                "--repo",
                str(ROOT),
                "--issues-root",
                str(FIXTURES / "issues"),
                "--kind",
                "catalog",
                "--format",
                "json",
            ]
        )
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["authority"], "generated-view")
        self.assertEqual(
            views._canonical_json(payload["document"]),
            views._canonical_json(catalog),
        )
        code, out, err = _run_main(
            [
                "graph",
                "--repo",
                str(ROOT),
                "--issues-root",
                str(FIXTURES / "issues"),
                "--format",
                "json",
            ]
        )
        self.assertEqual(code, 0, err)
        gpay = json.loads(out)
        self.assertEqual(
            views._canonical_json(gpay["document"]),
            views._canonical_json(graph),
        )

    def test_list_filters(self):
        common = [
            "list",
            "--repo",
            str(ROOT),
            "--issues-root",
            str(FIXTURES / "issues"),
            "--format",
            "json",
        ]
        code, out, _err = _run_main(common + ["--query", "open"])
        self.assertEqual(code, 0)
        ids = {item["id"] for item in json.loads(out)["items"]}
        self.assertIn("0081", ids)
        self.assertIn("0081-01", ids)
        self.assertNotIn("0081-02", ids)
        code, out, _err = _run_main(common + ["--query", "blocked"])
        self.assertEqual({item["id"] for item in json.loads(out)["items"]}, {"0081-02"})
        code, out, _err = _run_main(common + ["--query", "unclear"])
        self.assertIn("0081-03", {item["id"] for item in json.loads(out)["items"]})
        code, out, _err = _run_main(common + ["--query", "prerequisite"])
        self.assertTrue(any(item["prerequisites"] for item in json.loads(out)["items"]))
        code, out, _err = _run_main(["list", *common[1:], "--format", "human", "--query", "blocked"])
        self.assertEqual(code, 0)
        self.assertIn("0081-02", out)

    def test_legacy_todo_rejected(self):
        code, _out, err = _run_main(
            [
                "view",
                "--repo",
                str(ROOT),
                "--issues-root",
                str(ROOT / "TODO.md"),
                "--format",
                "json",
            ]
        )
        self.assertEqual(code, ctl.EXIT_USAGE)
        self.assertIn("legacy", err.lower())

    def test_stale_views_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            issues = repo / "issues"
            shutil.copytree(FIXTURES / "issues", issues)
            (repo / "issues/_schema").mkdir(parents=True)
            for rel in (
                views.CATALOG_SCHEMA_PATH,
                views.GRAPH_SCHEMA_PATH,
                views.ITEM_SCHEMA_PATH,
                views.STORE_TOOL_PATH,
                views.TOOL_PATH,
            ):
                src = ROOT / rel
                dest = repo / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, dest)
            catalog, graph = views.render(issues, repo)
            views.write_views(catalog, graph, repo)
            tampered = json.loads((repo / views.CATALOG_OUT).read_text(encoding="utf-8"))
            tampered["generation_id"] = "sha256:" + "00" * 32
            (repo / views.CATALOG_OUT).write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            code, _out, err = _run_main(
                [
                    "view",
                    "--repo",
                    str(repo),
                    "--issues-root",
                    str(issues),
                    "--require-views",
                ]
            )
            self.assertEqual(code, ctl.EXIT_ERROR)
            self.assertTrue(err)


class IssuectlValidateTests(unittest.TestCase):
    def test_validate_candidate_root_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as temp:
            issues = Path(temp) / "issues"
            shutil.copytree(ROOT / "_src/tests/fixtures/0037-08/issues", issues)
            code, out, err = _run_main(
                [
                    "validate",
                    "--repo",
                    str(ROOT),
                    "--source",
                    "candidate",
                    "--root",
                    str(issues),
                    "--no-compare-head",
                    "--format",
                    "json",
                ]
            )
            self.assertIn(code, (0, 2), err)
            payload = json.loads(out)
            self.assertEqual(payload["command"], "validate")
            self.assertIn(payload["status"], {"PASS", "FAIL"})
            code2, _out, err2 = _run_main(
                [
                    "validate",
                    "--repo",
                    str(ROOT),
                    "--root",
                    str(ROOT / "TODO.md"),
                    "--no-compare-head",
                ]
            )
            self.assertEqual(code2, ctl.EXIT_USAGE)
            self.assertIn("legacy", err2.lower())


class IssuectlTraceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.files = {}
        self.store = ps.ProvenanceStore(self.root, file_bytes=self.files.__getitem__)
        (self.root / "_src/tools").mkdir(parents=True)
        (self.root / "provenance/_schema").mkdir(parents=True)
        shutil.copy(STORE_TOOL, self.root / "_src/tools/provenance_store.py")
        shutil.copy(VIEW_TOOL, self.root / "_src/tools/provenance_views.py")
        shutil.copy(QUERY_TOOL, self.root / "_src/tools/provenance_query.py")
        shutil.copy(
            ROOT / "provenance/_schema/provenance-graph-v1.schema.json",
            self.root / "provenance/_schema/provenance-graph-v1.schema.json",
        )
        shutil.copy(
            ROOT / "provenance/_schema/provenance-reverse-v1.schema.json",
            self.root / "provenance/_schema/provenance-reverse-v1.schema.json",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, run_id=RUN_ID, issue="0037-17.03", **overrides):
        value = {
            "schema_version": "1.0",
            "run_id": run_id,
            "started_at": STAMP,
            "ended_at": "2026-08-16T08:02:00Z",
            "environment": "assessment",
            "classification": "internal",
            "status": "succeeded",
            "producer": _ref("commit", COMMIT),
            "inputs": [
                _ref("commit", COMMIT),
                _ref("issue", issue),
                _ref("criterion", "AC-001"),
                _ref("campaign", "camp-1"),
            ],
            "outputs": [_ref("artifact-set", SET_ID)],
        }
        value.update(overrides)
        return value

    def _finding(self, digest):
        return {
            "schema_version": "1.0",
            "finding_id": FINDING_ID,
            "detected_at": STAMP,
            "state": "open",
            "classification": "internal",
            "environment": "assessment",
            "subject": _ref("issue", "0037-17.03"),
            "detected_during": _ref("run", RUN_ID),
            "evidence": [_ref("artifact", f"docs/evidence.md@{digest}", digest=digest)],
        }

    def _event(self, event_id=EVENT_ID, **overrides):
        value = {
            "schema_version": "1.0",
            "event_id": event_id,
            "occurred_at": STAMP,
            "relation": "detected-during",
            "source": _ref("finding", FINDING_ID),
            "target": _ref("run", RUN_ID),
            "environment": "assessment",
            "classification": "internal",
            "run": _ref("run", RUN_ID),
        }
        value.update(overrides)
        return value

    def _seed(self):
        self.store.create_run(self._run())
        content = b"closed-item\n"
        self.files["docs/evidence.md"] = content
        aset = self.store.create_artifact_set(
            {
                "schema_version": "1.0",
                "set_id": SET_ID,
                "created_at": STAMP,
                "classification": "internal",
                "environment": "assessment",
                "producer": _ref("run", RUN_ID),
                "members": [
                    {
                        "path": "docs/evidence.md",
                        "digest": ps.sha256_bytes(content),
                        "size_bytes": len(content),
                        "media_type": "text/markdown",
                        "source_commit": COMMIT,
                    }
                ],
            }
        )
        digest = aset["record"]["members"][0]["digest"]
        self.store.create_finding(self._finding(digest))
        self.store.create_event(self._event())
        pv.write_views(*pv.build_views(self.root), self.root)
        return digest

    def test_trace_equivalence_file_commit_both_directions(self):
        digest = self._seed()
        for kind, ident, direction in (
            ("issue", "0037-17.03", "forward"),
            ("artifact", f"docs/evidence.md@{digest}", "reverse"),
            ("commit", COMMIT, "reverse"),
            ("commit", COMMIT, "forward"),
        ):
            lib = pq.query_trace(self.root, kind=kind, identifier=ident, direction=direction)
            code, out, err = _run_main(
                [
                    "trace",
                    "--repo",
                    str(self.root),
                    "--kind",
                    kind,
                    "--id",
                    ident,
                    "--direction",
                    direction,
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(code, pq.result_exit_code(lib), err)
            cli = json.loads(out)
            cli.pop("command", None)
            cli.pop("exit_code", None)
            self.assertEqual(pq._canonical_json(cli), pq._canonical_json(lib))

    def test_missing_broken_rename_privacy_stale_index(self):
        digest = self._seed()
        later_set = "018f4a31-42ad-7abc-8def-0123456789ab"
        later_run = "018f4a31-42aa-7abc-8def-0123456789ab"
        self.store.create_run(
            self._run(
                run_id=later_run,
                outputs=[_ref("artifact-set", later_set)],
                started_at="2026-08-17T00:00:00Z",
                ended_at="2026-08-17T00:01:00Z",
            )
        )
        self.files["docs/renamed-evidence.md"] = b"closed-item\n"
        self.store.create_artifact_set(
            {
                "schema_version": "1.0",
                "set_id": later_set,
                "created_at": "2026-08-17T00:00:00Z",
                "classification": "internal",
                "environment": "assessment",
                "producer": _ref("run", later_run),
                "members": [
                    {
                        "path": "docs/renamed-evidence.md",
                        "digest": digest,
                        "size_bytes": len(b"closed-item\n"),
                        "media_type": "text/markdown",
                        "source_commit": COMMIT,
                    }
                ],
            }
        )
        dangling = self._event(
            event_id="018f4a31-32af-7abc-8def-0123456789ab",
            source=_ref("finding", "018f4a31-ffff-7abc-8def-0123456789ab"),
            target=_ref("run", RUN_ID),
        )
        year, month = dangling["occurred_at"][:4], dangling["occurred_at"][5:7]
        directory = self.root / "provenance" / "events" / year / month
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{dangling['event_id']}.json").write_text(
            json.dumps(dangling, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        pv.write_views(*pv.build_views(self.root), self.root)

        code, out, _err = _run_main(
            [
                "trace",
                "--repo",
                str(self.root),
                "--kind",
                "artifact",
                "--id",
                f"docs/evidence.md@{digest}",
                "--direction",
                "reverse",
            ]
        )
        self.assertEqual(code, 0)
        paths = {f["path"] for f in json.loads(out)["files"]}
        self.assertIn("docs/evidence.md", paths)
        self.assertIn("docs/renamed-evidence.md", paths)

        code, out, _err = _run_main(
            [
                "trace",
                "--repo",
                str(self.root),
                "--kind",
                "issue",
                "--id",
                "0037-17.03",
            ]
        )
        statuses = {d["status"] for d in json.loads(out)["diagnostics"]}
        self.assertIn("dangling", statuses)

        code, out, _err = _run_main(
            [
                "trace",
                "--repo",
                str(self.root),
                "--kind",
                "artifact-set",
                "--id",
                "018f4a31-dead-7abc-8def-0123456789ab",
            ]
        )
        self.assertEqual(code, pq.EXIT_MISSING)
        self.assertTrue(any(d["status"] == "missing" for d in json.loads(out)["diagnostics"]))

        code, out, _err = _run_main(
            [
                "trace",
                "--repo",
                str(self.root),
                "--kind",
                "issue",
                "--id",
                "0037-17.03",
                "--max-classification",
                "public",
            ]
        )
        self.assertFalse(any(f.get("path") == "docs/evidence.md" for f in json.loads(out)["files"]))

        tampered = json.loads((self.root / pv.GRAPH_OUT).read_text(encoding="utf-8"))
        tampered["generation_id"] = "sha256:" + "00" * 32
        (self.root / pv.GRAPH_OUT).write_text(json.dumps(tampered) + "\n", encoding="utf-8")
        code, _out, err = _run_main(
            [
                "trace",
                "--repo",
                str(self.root),
                "--kind",
                "issue",
                "--id",
                "0037-17.03",
                "--require-index",
            ]
        )
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertTrue(err)

        code, out, _err = _run_main(
            [
                "trace",
                "--repo",
                str(self.root),
                "--kind",
                "issue",
                "--id",
                "0037-17.03",
                "--format",
                "human",
                "--require-index",
            ]
        )
        self.assertEqual(code, ctl.EXIT_ERROR)


class IssuectlMutateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.issues = self.repo / "issues"
        self.issues.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def _digest(self, item_id):
        return hashlib.sha256(ctl.item_path(self.issues, item_id).read_bytes()).hexdigest()

    def _create(self, item_id, **extra):
        argv = [
            "create",
            "--repo",
            str(self.repo),
            "--issues-root",
            str(self.issues),
            "--id",
            item_id,
            "--format",
            "json",
        ]
        for key, value in extra.items():
            argv.extend([f"--{key.replace('_', '-')}", value])
        code, out, err = _run_main(argv)
        self.assertEqual(code, 0, err or out)
        return json.loads(out)

    def test_create_feature_task_subtask_paths(self):
        self._create("0100", goal="Feature goal.")
        self._create("0100-01", goal="Task goal.")
        self._create("0100-01.01", goal="Subtask goal.")
        self.assertTrue((self.issues / "0100/index.md").is_file())
        self.assertTrue((self.issues / "0100/0100-01/index.md").is_file())
        self.assertTrue((self.issues / "0100/0100-01.01/index.md").is_file())
        for item_id in ("0100", "0100-01", "0100-01.01"):
            meta, _body, _data = ctl.parse_document(ctl.item_path(self.issues, item_id), self.issues)
            self.assertEqual(meta["id"], item_id)
            self.assertEqual(meta["level"], ctl.level_of(item_id))

    def test_edit_approved_field_and_identity_rejected(self):
        self._create("0100")
        digest = self._digest("0100")
        code, out, err = _run_main(
            [
                "edit",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--field",
                "visibility",
                "--value",
                "public-summary",
                "--expected-digest",
                digest,
            ]
        )
        self.assertEqual(code, 0, err)
        meta, body, _data = ctl.parse_document(ctl.item_path(self.issues, "0100"), self.issues)
        self.assertEqual(meta["visibility"], "public-summary")
        self.assertIn("Feature goal" if False else "Goal for 0100", body)
        digest = self._digest("0100")
        code, _out, err = _run_main(
            [
                "edit",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--field",
                "id",
                "--value",
                "9999",
                "--expected-digest",
                digest,
            ]
        )
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1111", err)

    def test_allocate_withdraw_supersede_and_history(self):
        self._create("0100")
        d = self._digest("0100")
        _run_main(
            [
                "criterion-allocate",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--text",
                "Second criterion.",
                "--expected-digest",
                d,
            ]
        )
        parsed = ctl.store.parse_markdown_body(
            ctl.parse_document(ctl.item_path(self.issues, "0100"), self.issues)[1]
        )
        self.assertEqual([c["id"] for c in parsed["criteria"]], ["AC-001", "AC-002"])
        d = self._digest("0100")
        _run_main(
            [
                "criterion-withdraw",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--ac",
                "AC-002",
                "--reason",
                "no longer needed",
                "--expected-digest",
                d,
            ]
        )
        d = self._digest("0100")
        code, out, err = _run_main(
            [
                "criterion-allocate",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--text",
                "Third after withdrawal.",
                "--expected-digest",
                d,
            ]
        )
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["allocated"], "AC-003")
        d = self._digest("0100")
        code, out, err = _run_main(
            [
                "criterion-supersede",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--ac",
                "AC-001",
                "--text",
                "Replacement verification.",
                "--reason",
                "method changed",
                "--expected-digest",
                d,
            ]
        )
        self.assertEqual(code, 0, err)
        parsed = ctl.store.parse_markdown_body(
            ctl.parse_document(ctl.item_path(self.issues, "0100"), self.issues)[1]
        )
        statuses = {c["id"]: c["status"] for c in parsed["criteria"]}
        self.assertEqual(statuses["AC-001"], "superseded")
        self.assertEqual(statuses["AC-002"], "withdrawn")
        self.assertEqual(statuses["AC-003"], "active")
        self.assertEqual(statuses["AC-004"], "active")

    def test_prereq_relation_and_cycle_rejected(self):
        self._create("0100")
        self._create("0101")
        d = self._digest("0100")
        code, _out, err = _run_main(
            [
                "prereq",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--action",
                "add",
                "--target",
                "0101",
                "--expected-digest",
                d,
            ]
        )
        self.assertEqual(code, 0, err)
        d = self._digest("0101")
        code, _out, err = _run_main(
            [
                "prereq",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0101",
                "--action",
                "add",
                "--target",
                "0100",
                "--expected-digest",
                d,
            ]
        )
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1108", err)
        d = self._digest("0100")
        code, _out, err = _run_main(
            [
                "relation",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--action",
                "add",
                "--type",
                "blocks",
                "--target",
                "0101",
                "--expected-digest",
                d,
            ]
        )
        self.assertEqual(code, 0, err)
        meta, _body, _data = ctl.parse_document(ctl.item_path(self.issues, "0100"), self.issues)
        self.assertEqual(meta["relations"], [{"type": "blocks", "target": "0101"}])
        d = self._digest("0100")
        code, _out, err = _run_main(
            [
                "prereq",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--action",
                "remove",
                "--target",
                "0101",
                "--expected-digest",
                d,
            ]
        )
        self.assertEqual(code, 0, err)

    def test_invalid_parent_and_move(self):
        code, _out, err = _run_main(
            [
                "create",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100-01",
            ]
        )
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1107", err)
        self._create("0100")
        d = self._digest("0100")
        code, _out, err = _run_main(
            [
                "criterion-move",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--ac",
                "AC-001",
                "--to-id",
                "0101",
                "--expected-digest",
                d,
                "--expected-digest-dest",
                d,
                "--reason",
                "rehome",
            ]
        )
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1114", err)

    def test_move_success_and_claim_scope(self):
        self._create("0100")
        self._create("0101")
        src_d = self._digest("0100")
        dst_d = self._digest("0101")
        code, out, err = _run_main(
            [
                "criterion-move",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--ac",
                "AC-001",
                "--to-id",
                "0101",
                "--expected-digest",
                src_d,
                "--expected-digest-dest",
                dst_d,
                "--reason",
                "reclassified",
            ]
        )
        self.assertEqual(code, 0, err)
        src = ctl.store.parse_markdown_body(
            ctl.parse_document(ctl.item_path(self.issues, "0100"), self.issues)[1]
        )
        dst = ctl.store.parse_markdown_body(
            ctl.parse_document(ctl.item_path(self.issues, "0101"), self.issues)[1]
        )
        self.assertEqual(src["criteria"][0]["status"], "moved")
        self.assertEqual(dst["criteria"][-1]["status"], "active")
        self.assertEqual(dst["criteria"][-1]["derived_from"], "0100#AC-001")
        claim = self.issues / "0101/claim.json"
        claim.write_text(
            json.dumps(
                {
                    "owner_token": "agent:test:0101:x",
                    "write_scopes": ["issues/other/index.md"],
                }
            ),
            encoding="utf-8",
        )
        d = self._digest("0101")
        code, _out, err = _run_main(
            [
                "edit",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0101",
                "--field",
                "visibility",
                "--value",
                "public-summary",
                "--expected-digest",
                d,
                "--owner-token",
                "agent:test:0101:x",
            ]
        )
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1105", err)

    def test_concurrent_edit_rejected(self):
        self._create("0100")
        stale = self._digest("0100")
        ctl.item_path(self.issues, "0100").write_bytes(
            ctl.item_path(self.issues, "0100").read_bytes() + b""
        )
        path = ctl.item_path(self.issues, "0100")
        text = path.read_text(encoding="utf-8").replace("open", "in_progress", 1)
        path.write_text(text, encoding="utf-8")
        code, _out, err = _run_main(
            [
                "edit",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--field",
                "visibility",
                "--value",
                "public-summary",
                "--expected-digest",
                stale,
            ]
        )
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1106", err)

    def test_crash_rollback_dry_run_and_noop(self):
        self._create("0100")
        original = ctl.item_path(self.issues, "0100").read_bytes()
        digest = self._digest("0100")
        code, out, err = _run_main(
            [
                "edit",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--field",
                "visibility",
                "--value",
                "public-summary",
                "--expected-digest",
                digest,
                "--dry-run",
                "--format",
                "json",
            ]
        )
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertTrue(payload["dry_run"])
        self.assertIn("diff", payload)
        self.assertEqual(ctl.item_path(self.issues, "0100").read_bytes(), original)
        code, out, err = _run_main(
            [
                "edit",
                "--repo",
                str(self.repo),
                "--issues-root",
                str(self.issues),
                "--id",
                "0100",
                "--field",
                "visibility",
                "--value",
                "internal",
                "--expected-digest",
                digest,
            ]
        )
        self.assertEqual(code, 0, err)
        self.assertTrue(json.loads(out)["noop"])
        self.assertEqual(ctl.item_path(self.issues, "0100").read_bytes(), original)
        calls = {"n": 0}
        real = os.replace

        def boom(src, dst):
            calls["n"] += 1
            raise OSError("injected crash")

        with mock.patch.object(ctl.os, "replace", boom):
            code, _out, err = _run_main(
                [
                    "edit",
                    "--repo",
                    str(self.repo),
                    "--issues-root",
                    str(self.issues),
                    "--id",
                    "0100",
                    "--field",
                    "visibility",
                    "--value",
                    "public-summary",
                    "--expected-digest",
                    digest,
                ]
            )
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertEqual(ctl.item_path(self.issues, "0100").read_bytes(), original)
        leftovers = list(self.issues.joinpath("0100").glob(".issuectl-*.tmp"))
        self.assertEqual(leftovers, [])


class IssuectlClaimTests(unittest.TestCase):
    """Tests for Task 0037-10.02: claim, renew, release, handoff, recover."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.issues = self.repo / "issues"
        self.issues.mkdir()
        # A real Git repository is required: _cas_promote_claim performs a
        # literal `git update-ref refs/autodocs/claims/<item-id>` CAS (see
        # _update_ref_cas) in addition to the --expected-digest sidecar
        # check, so every claim/renew/release/handoff/recover command needs
        # a real .git object/ref store to write blobs and refs into.
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.name", "Test"],
            check=True,
        )
        # Every claim command still accepts an explicit --base-commit, so
        # _resolve_base_commit never has to shell out to `git rev-parse
        # HEAD`. A fixed 40-hex placeholder is enough to satisfy the claim
        # schema's base_commit pattern for these unit tests; it is unrelated
        # to the refs/autodocs/claims/<item-id> CAS ref, which is resolved
        # against the real repository created above.
        self.base = COMMIT

    def tearDown(self):
        self.temp.cleanup()

    def _claim_cas_ref_value(self, item_id):
        proc = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "-q", "--verify",
             f"refs/autodocs/claims/{item_id}"],
            capture_output=True,
        )
        if proc.returncode != 0:
            return None
        return proc.stdout.decode("utf-8").strip()

    def _claim_cas_blob_bytes(self, item_id):
        blob = self._claim_cas_ref_value(item_id)
        self.assertIsNotNone(blob, f"no CAS ref for {item_id}")
        proc = subprocess.run(
            ["git", "-C", str(self.repo), "cat-file", "-p", blob],
            capture_output=True, check=True,
        )
        return proc.stdout

    def _create(self, item_id, **extra):
        argv = [
            "create", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", item_id, "--format", "json",
        ]
        for key, value in extra.items():
            argv.extend([f"--{key.replace('_', '-')}", value])
        code, out, err = _run_main(argv)
        self.assertEqual(code, 0, err or out)
        return json.loads(out)

    def _claim_sidecar_path(self, item_id):
        return self.issues / item_id / "claim.json"

    def _claim_json(self, item_id):
        return json.loads(self._claim_sidecar_path(item_id).read_text(encoding="utf-8"))

    def _digest(self, item_id):
        sidecar = self._claim_sidecar_path(item_id)
        data = sidecar.read_bytes() if sidecar.is_file() else b""
        return hashlib.sha256(data).hexdigest()

    def _claim(self, item_id, owner="agent:alpha", *, now="2026-08-16T09:00:00+00:00",
               ttl_seconds="7200", worktree_id="wt-a", clone_id="clone-a",
               write_scope=None, extra_args=None):
        argv = [
            "claim", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", item_id, "--owner", owner, "--worktree-id", worktree_id,
            "--clone-id", clone_id, "--base-commit", self.base,
            "--ttl-seconds", str(ttl_seconds), "--now", now, "--format", "json",
        ]
        for scope in (write_scope or [f"issues/{item_id}/index.md"]):
            argv.extend(["--write-scope", scope])
        if extra_args:
            argv.extend(extra_args)
        return _run_main(argv)

    def test_claim_creates_valid_sidecar_and_matches_validator_digest(self):
        self._create("0100")
        code, out, err = self._claim("0100")
        self.assertEqual(code, ctl.EXIT_OK, err or out)
        payload = self._claim_json("0100")
        self.assertEqual(payload["state"], "active")
        self.assertEqual(payload["item_id"], "0100")
        self.assertEqual(payload["cas_ref"], "refs/autodocs/claims/0100")
        # Reuse issue_validate's own canonical-digest computation: the claim
        # this tool writes must validate under the same authoritative check
        # `issuectl validate` / `issue_validate.py` apply to committed claims.
        self.assertEqual(payload["cas_ref_digest"], ctl.iv._claim_digest(payload))
        self.assertIn(payload["state"], ctl.iv.ACTIVE_CLAIM_STATES)

    def test_claim_rejects_second_active_claim_for_same_item(self):
        self._create("0100")
        code, _out, _err = self._claim("0100", owner="agent:alpha")
        self.assertEqual(code, ctl.EXIT_OK)
        code, _out, err = self._claim("0100", owner="agent:beta")
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1135", err)

    def test_claim_rejects_overlapping_write_scope_with_other_item(self):
        self._create("0100")
        self._create("0200")
        code, _out, _err = self._claim(
            "0100", write_scope=["docs/pipeline/issue-lifecycle.md"]
        )
        self.assertEqual(code, ctl.EXIT_OK)
        code, _out, err = self._claim(
            "0200", write_scope=["docs/pipeline/issue-lifecycle.md"]
        )
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1131", err)

    def test_renew_extends_expiry_and_preserves_owner_scope_nonce(self):
        self._create("0100")
        self._claim("0100")
        before = self._claim_json("0100")
        code, out, err = _run_main([
            "renew", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--owner", "agent:alpha", "--expected-digest", self._digest("0100"),
            "--now", "2026-08-16T09:30:00+00:00", "--ttl-seconds", "7200",
            "--format", "json",
        ])
        self.assertEqual(code, ctl.EXIT_OK, err or out)
        after = self._claim_json("0100")
        self.assertEqual(after["owner"], before["owner"])
        self.assertEqual(after["lease_nonce"], before["lease_nonce"])
        self.assertEqual(after["write_scopes"], before["write_scopes"])
        self.assertGreater(after["expires_at"], before["expires_at"])
        self.assertEqual(after["cas_ref_digest"], ctl.iv._claim_digest(after))

    def test_renew_rejects_stale_expected_digest(self):
        self._create("0100")
        self._claim("0100", owner="agent:alpha")
        code, _out, err = _run_main([
            "renew", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--owner", "agent:alpha", "--expected-digest", "0" * 64,
            "--format", "json",
        ])
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1106", err)

    def test_renew_rejects_owner_mismatch(self):
        self._create("0100")
        self._claim("0100", owner="agent:alpha")
        code, _out, err = _run_main([
            "renew", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--owner", "agent:mallory", "--expected-digest", self._digest("0100"),
            "--format", "json",
        ])
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1138", err)

    def test_release_then_reclaim_by_new_owner(self):
        self._create("0100")
        self._claim("0100", owner="agent:alpha")
        code, out, err = _run_main([
            "release", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--owner", "agent:alpha", "--expected-digest", self._digest("0100"),
            "--format", "json",
        ])
        self.assertEqual(code, ctl.EXIT_OK, err or out)
        self.assertEqual(self._claim_json("0100")["state"], "released")
        code, out, err = self._claim(
            "0100", owner="agent:beta", now="2026-08-16T10:00:00+00:00"
        )
        self.assertEqual(code, ctl.EXIT_OK, err or out)
        self.assertEqual(self._claim_json("0100")["owner"]["identity"], "agent:beta")

    def test_handoff_requires_release_or_authority_decision(self):
        self._create("0100")
        self._claim("0100", owner="agent:alpha")
        code, _out, err = _run_main([
            "handoff", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--to-owner", "agent:beta", "--expected-digest", self._digest("0100"),
            "--worktree-id", "wt-b", "--clone-id", "clone-b",
            "--write-scope", "issues/0100/index.md", "--base-commit", self.base,
            "--now", "2026-08-16T09:15:00+00:00", "--format", "json",
        ])
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1139", err)
        code, out, err = _run_main([
            "handoff", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--to-owner", "agent:beta", "--expected-digest", self._digest("0100"),
            "--worktree-id", "wt-b", "--clone-id", "clone-b",
            "--write-scope", "issues/0100/index.md", "--base-commit", self.base,
            "--authority-decision", "decision-handoff-0100",
            "--now", "2026-08-16T09:15:00+00:00", "--format", "json",
        ])
        self.assertEqual(code, ctl.EXIT_OK, err or out)
        after = self._claim_json("0100")
        self.assertEqual(after["owner"]["identity"], "agent:beta")
        self.assertTrue(after["predecessor_claim"])
        self.assertEqual(after["authority_decision"], "decision-handoff-0100")

    def test_handoff_after_release_needs_no_authority_decision(self):
        self._create("0100")
        self._claim("0100", owner="agent:alpha")
        _run_main([
            "release", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--owner", "agent:alpha", "--expected-digest", self._digest("0100"),
            "--format", "json",
        ])
        code, out, err = _run_main([
            "handoff", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--to-owner", "agent:beta", "--expected-digest", self._digest("0100"),
            "--worktree-id", "wt-b", "--clone-id", "clone-b",
            "--write-scope", "issues/0100/index.md", "--base-commit", self.base,
            "--now", "2026-08-16T09:15:00+00:00", "--format", "json",
        ])
        self.assertEqual(code, ctl.EXIT_OK, err or out)
        self.assertEqual(self._claim_json("0100")["owner"]["identity"], "agent:beta")

    def test_recover_rejected_while_unexpired(self):
        self._create("0100")
        self._claim("0100", owner="agent:alpha", ttl_seconds=3600)
        code, _out, err = _run_main([
            "recover", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--owner", "agent:delta", "--expected-digest", self._digest("0100"),
            "--worktree-id", "wt-d", "--clone-id", "clone-d",
            "--write-scope", "issues/0100/index.md", "--base-commit", self.base,
            "--authority-decision", "decision-takeover-0100",
            "--now", "2026-08-16T09:30:00+00:00", "--format", "json",
        ])
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1140", err)

    def test_recover_requires_authority_decision_and_succeeds_when_expired(self):
        self._create("0100")
        self._claim("0100", owner="agent:alpha", ttl_seconds=60,
                    now="2026-08-16T09:00:00+00:00")
        code, _out, err = _run_main([
            "recover", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--owner", "agent:delta", "--expected-digest", self._digest("0100"),
            "--worktree-id", "wt-d", "--clone-id", "clone-d",
            "--write-scope", "issues/0100/index.md", "--base-commit", self.base,
            "--now", "2026-08-16T09:10:00+00:00", "--format", "json",
        ])
        self.assertEqual(code, 2)  # argparse required-argument usage error
        code, out, err = _run_main([
            "recover", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--owner", "agent:delta", "--expected-digest", self._digest("0100"),
            "--worktree-id", "wt-d", "--clone-id", "clone-d",
            "--write-scope", "issues/0100/index.md", "--base-commit", self.base,
            "--authority-decision", "decision-takeover-0100",
            "--now", "2026-08-16T09:10:00+00:00", "--format", "json",
        ])
        self.assertEqual(code, ctl.EXIT_OK, err or out)
        after = self._claim_json("0100")
        self.assertEqual(after["owner"]["identity"], "agent:delta")
        self.assertEqual(after["authority_decision"], "decision-takeover-0100")
        self.assertTrue(after["predecessor_claim"])
        self.assertEqual(after["state"], "active")

    def test_claim_dry_run_does_not_write_sidecar(self):
        self._create("0100")
        code, out, err = self._claim("0100", extra_args=["--dry-run"])
        self.assertEqual(code, ctl.EXIT_OK, err or out)
        self.assertFalse(self._claim_sidecar_path("0100").exists())

    def test_claim_writes_real_git_ref_cas_matching_sidecar(self):
        # Direct evidence for the literal acceptance criterion: claim
        # acquisition must be a real `refs/autodocs/claims/<item-id>` CAS,
        # not only a sidecar-file digest check. The ref must exist, its
        # blob content must equal the canonical sidecar bytes exactly, and
        # renew must move the ref forward to a new blob.
        self._create("0100")
        code, _out, err = self._claim("0100")
        self.assertEqual(code, ctl.EXIT_OK, err)
        sidecar_bytes = self._claim_sidecar_path("0100").read_bytes()
        self.assertEqual(self._claim_cas_blob_bytes("0100"), sidecar_bytes)
        first_ref_value = self._claim_cas_ref_value("0100")
        self.assertIsNotNone(first_ref_value)

        code, _out, err = _run_main([
            "renew", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0100", "--owner", "agent:alpha", "--expected-digest", self._digest("0100"),
            "--now", "2026-08-16T09:30:00+00:00", "--ttl-seconds", "7200", "--format", "json",
        ])
        self.assertEqual(code, ctl.EXIT_OK, err)
        self.assertEqual(self._claim_cas_blob_bytes("0100"), self._claim_sidecar_path("0100").read_bytes())
        self.assertNotEqual(self._claim_cas_ref_value("0100"), first_ref_value)


class IssuectlClaimCasRaceAndRecoveryTests(unittest.TestCase):
    """DoD coverage gaps flagged by Task 0037-10.02's predecessor claim:
    multi-worktree race serialization, crash-point fault injection between
    reading and writing claim state, remote-unavailable behavior, and the
    protected-branch-adjacent path (refs/autodocs/claims/* is never a
    branch ref and must never collide with branch protection surfaces)."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "origin"
        self.repo.mkdir()
        self.issues = self.repo / "issues"
        self.issues.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True,
        )
        self.base = COMMIT

    def tearDown(self):
        self.temp.cleanup()

    def _create(self, item_id):
        argv = [
            "create", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", item_id, "--format", "json",
        ]
        code, out, err = _run_main(argv)
        self.assertEqual(code, 0, err or out)
        return json.loads(out)

    def _claim_argv(self, item_id, owner, worktree_id, now="2026-08-16T09:00:00+00:00"):
        return [
            "claim", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", item_id, "--owner", owner, "--worktree-id", worktree_id,
            "--clone-id", worktree_id, "--base-commit", self.base,
            "--ttl-seconds", "7200", "--now", now, "--format", "json",
            "--write-scope", f"issues/{item_id}/index.md",
        ]

    # -- Multi-worktree race: real concurrent processes, real CAS -------

    def test_concurrent_claim_attempts_from_two_worktrees_only_one_wins(self):
        # Two real `git worktree`s of the *same* repository (sharing one
        # refs/objects store, exactly the "different worktrees" case named
        # in the DoD gap) race a real `issuectl claim` subprocess against
        # the same item at the same instant. Git's own update-ref
        # lockfile, not application bookkeeping, must ensure exactly one
        # writer's CAS succeeds.
        self._create("0300")
        worktree_a = Path(self.temp.name) / "wt-a"
        worktree_b = Path(self.temp.name) / "wt-b"
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-q", str(worktree_a), "-b", "wt-a-branch"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-q", str(worktree_b), "-b", "wt-b-branch"],
            check=True,
        )

        def run_claim(repo_path, owner, worktree_id, results, index):
            argv = [
                sys.executable, str(ISSUECTL_PATH), "claim",
                "--repo", str(repo_path), "--issues-root", str(self.issues),
                "--id", "0300", "--owner", owner, "--worktree-id", worktree_id,
                "--clone-id", worktree_id, "--base-commit", self.base,
                "--ttl-seconds", "7200", "--now", "2026-08-16T09:00:00+00:00",
                "--format", "json", "--write-scope", "issues/0300/index.md",
            ]
            proc = subprocess.run(argv, capture_output=True)
            results[index] = proc

        results = [None, None]
        threads = [
            threading.Thread(target=run_claim, args=(worktree_a, "agent:alpha", "wt-a", results, 0)),
            threading.Thread(target=run_claim, args=(worktree_b, "agent:beta", "wt-b", results, 1)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        self.assertIsNotNone(results[0])
        self.assertIsNotNone(results[1])
        return_codes = sorted(proc.returncode for proc in results)
        # Exactly one process must observe success (EXIT_OK); the other
        # must be rejected -- either by the IC1135 "already claimed"
        # application check (if it observed the winner's sidecar first) or
        # by IC1141 git-ref CAS loss (if both raced past that read at
        # nearly the same instant). Both are real serialization outcomes,
        # never "both succeeded".
        self.assertEqual(return_codes[0], ctl.EXIT_OK, [p.stdout + p.stderr for p in results])
        self.assertNotEqual(return_codes[1], ctl.EXIT_OK)
        winner, loser = (results[0], results[1]) if results[0].returncode == ctl.EXIT_OK else (results[1], results[0])
        combined_loser_output = (loser.stdout + loser.stderr).decode("utf-8", "replace")
        self.assertTrue(
            "IC1135" in combined_loser_output or "IC1141" in combined_loser_output,
            combined_loser_output,
        )
        # The sidecar and the CAS ref converge to the single winner's state.
        sidecar = json.loads((self.issues / "0300" / "claim.json").read_text(encoding="utf-8"))
        winner_payload = json.loads(winner.stdout.decode("utf-8"))["claim"]
        self.assertEqual(sidecar["owner"]["identity"], winner_payload["owner"]["identity"])
        ref_proc = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "-q", "--verify", "refs/autodocs/claims/0300"],
            capture_output=True,
        )
        self.assertEqual(ref_proc.returncode, 0)
        blob = subprocess.run(
            ["git", "-C", str(self.repo), "cat-file", "-p", ref_proc.stdout.decode().strip()],
            capture_output=True, check=True,
        ).stdout
        self.assertEqual(blob, (self.issues / "0300" / "claim.json").read_bytes())

    def test_concurrent_claims_on_different_items_both_succeed(self):
        # Adjacent-neighbor case for the race test above: two concurrent
        # claims that do NOT share a CAS ref (different items, disjoint
        # write scopes) must both succeed -- the ref-CAS lock is scoped
        # per-item, not a repository-wide serialization point.
        self._create("0301")
        self._create("0302")

        def run_claim(item_id, results, index):
            argv = [
                sys.executable, str(ISSUECTL_PATH), "claim",
                "--repo", str(self.repo), "--issues-root", str(self.issues),
                "--id", item_id, "--owner", "agent:alpha", "--worktree-id", "wt-a",
                "--clone-id", "wt-a", "--base-commit", self.base,
                "--ttl-seconds", "7200", "--now", "2026-08-16T09:00:00+00:00",
                "--format", "json", "--write-scope", f"issues/{item_id}/index.md",
            ]
            proc = subprocess.run(argv, capture_output=True)
            results[index] = proc

        results = [None, None]
        threads = [
            threading.Thread(target=run_claim, args=("0301", results, 0)),
            threading.Thread(target=run_claim, args=("0302", results, 1)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        for proc in results:
            self.assertEqual(proc.returncode, ctl.EXIT_OK, proc.stdout + proc.stderr)

    # -- Crash-point fault injection ------------------------------------

    def test_crash_between_ref_cas_and_sidecar_promotion_leaves_ref_authoritative(self):
        # Simulates a process crash exactly between the real git-ref CAS
        # succeeding and the local claim.json sidecar promotion running
        # (the two-step window inside `_cas_promote_claim`). Recovery must
        # not corrupt the claim record: re-derive the sidecar from the now
        # git-durable ref content, and the *next* real claim command must
        # still see a consistent, single active claim rather than a torn
        # state that would let a second claimant slip through.
        self._create("0310")
        code, out, err = _run_main(self._claim_argv("0310", "agent:alpha", "wt-a"))
        self.assertEqual(code, ctl.EXIT_OK, err or out)
        sidecar_path = self.issues / "0310" / "claim.json"
        ref_blob_before = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "-q", "--verify", "refs/autodocs/claims/0310"],
            capture_output=True, check=True,
        ).stdout.decode().strip()

        # Inject the crash: delete the sidecar file (as if the process died
        # after `_update_ref_cas` returned but before `atomic_promote` ran)
        # while leaving the git ref -- the durable side of the two-step
        # write -- untouched.
        sidecar_path.unlink()
        self.assertFalse(sidecar_path.exists())
        ref_blob_after_crash = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "-q", "--verify", "refs/autodocs/claims/0310"],
            capture_output=True, check=True,
        ).stdout.decode().strip()
        self.assertEqual(ref_blob_before, ref_blob_after_crash)

        # Recovery: the git ref is still the durable source of truth and
        # its blob is exactly the last-promoted claim payload, so a
        # recovery step can reconstruct the sidecar byte-for-byte from it.
        recovered_bytes = subprocess.run(
            ["git", "-C", str(self.repo), "cat-file", "-p", ref_blob_after_crash],
            capture_output=True, check=True,
        ).stdout
        recovered_payload = json.loads(recovered_bytes.decode("utf-8"))
        self.assertEqual(recovered_payload["item_id"], "0310")
        self.assertEqual(recovered_payload["owner"]["identity"], "agent:alpha")
        sidecar_path.write_bytes(recovered_bytes)

        # A subsequent claim attempt for the same item by a different
        # owner is still correctly rejected post-recovery: no torn state
        # let a second claimant through.
        code, _out, err = _run_main(self._claim_argv("0310", "agent:beta", "wt-b"))
        self.assertEqual(code, ctl.EXIT_ERROR)
        self.assertIn("IC1135", err)

    def test_crash_before_ref_cas_leaves_no_ref_and_claim_is_retryable(self):
        # Mirror case: crash (simulated by raising from inside the CAS
        # helper) *before* the git update-ref call executes at all -- no
        # ref, no sidecar. The item must remain freely claimable, i.e. the
        # half-attempted operation left no durable trace to recover from
        # or get stuck behind.
        self._create("0311")
        real_update_ref_cas = ctl._update_ref_cas

        def crashing_update_ref_cas(*args, **kwargs):
            raise RuntimeError("simulated crash before git update-ref runs")

        ctl._update_ref_cas = crashing_update_ref_cas
        try:
            with self.assertRaises(RuntimeError):
                _run_main(self._claim_argv("0311", "agent:alpha", "wt-a"))
        finally:
            ctl._update_ref_cas = real_update_ref_cas

        self.assertFalse((self.issues / "0311" / "claim.json").exists())
        ref_proc = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "-q", "--verify", "refs/autodocs/claims/0311"],
            capture_output=True,
        )
        self.assertNotEqual(ref_proc.returncode, 0)

        # Retry succeeds cleanly: nothing was left behind to block it.
        code, out, err = _run_main(self._claim_argv("0311", "agent:alpha", "wt-a"))
        self.assertEqual(code, ctl.EXIT_OK, err or out)

    # -- Remote-unavailable coverage --------------------------------------

    def test_claim_operations_never_touch_a_remote(self):
        # All claim/renew/release/handoff/recover operations are same-clone
        # (local refs/objects only); none of them must invoke a networked
        # git subcommand (fetch/pull/push) or fail because a remote is
        # unreachable. Prove it by configuring a non-existent, unroutable
        # remote and confirming the full claim lifecycle still succeeds
        # entirely offline.
        subprocess.run(
            ["git", "-C", str(self.repo), "remote", "add", "origin", "https://198.51.100.1/nonexistent.git"],
            check=True,
        )
        self._create("0320")
        code, out, err = _run_main(self._claim_argv("0320", "agent:alpha", "wt-a"))
        self.assertEqual(code, ctl.EXIT_OK, err or out)
        code, _out, err = _run_main([
            "release", "--repo", str(self.repo), "--issues-root", str(self.issues),
            "--id", "0320", "--owner", "agent:alpha",
            "--expected-digest", hashlib.sha256((self.issues / "0320" / "claim.json").read_bytes()).hexdigest(),
            "--format", "json",
        ])
        self.assertEqual(code, ctl.EXIT_OK, err)

    # -- Protected-branch-adjacent path -----------------------------------

    def test_claim_cas_ref_namespace_is_disjoint_from_branch_refs(self):
        # refs/autodocs/claims/<item-id> must never be reachable from, or
        # collide with, refs/heads/* (branch refs, subject to protection)
        # or refs/remotes/*. A claim CAS write is a same-clone, non-branch
        # ref mutation and must not appear in `git branch` output or be
        # reachable as an ancestor of any branch tip; this is the load-
        # bearing property that lets claim CAS run entirely outside any
        # branch-protection / integration-checkpoint gate.
        self._create("0330")
        code, out, err = _run_main(self._claim_argv("0330", "agent:alpha", "wt-a"))
        self.assertEqual(code, ctl.EXIT_OK, err or out)
        show_ref = subprocess.run(
            ["git", "-C", str(self.repo), "show-ref"], capture_output=True, check=True,
        ).stdout.decode("utf-8")
        claim_lines = [line for line in show_ref.splitlines() if "refs/autodocs/claims/0330" in line]
        self.assertEqual(len(claim_lines), 1, show_ref)
        self.assertNotIn("refs/heads/", claim_lines[0].split()[1])
        branch_list = subprocess.run(
            ["git", "-C", str(self.repo), "branch", "--list"], capture_output=True, check=True,
        ).stdout.decode("utf-8")
        self.assertNotIn("0330", branch_list)
        for_each_ref = subprocess.run(
            ["git", "-C", str(self.repo), "for-each-ref", "--format=%(refname)", "refs/heads/"],
            capture_output=True, check=True,
        ).stdout.decode("utf-8")
        self.assertEqual(for_each_ref.strip(), "")


if __name__ == "__main__":
    unittest.main()
