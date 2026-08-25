"""Command-contract tests for issuectl query surfaces (Task 0037-10.04)."""
from __future__ import annotations

import importlib.util
import io
import json
import shutil
import sys
import hashlib
import os
import tempfile
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


if __name__ == "__main__":
    unittest.main()
