import ast
import copy
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "legacy_scope_planner"

DOCTOR_SPEC = importlib.util.spec_from_file_location("legacy_task_doctor", TOOLS / "legacy_task_doctor.py")
assert DOCTOR_SPEC is not None and DOCTOR_SPEC.loader is not None
doctor = importlib.util.module_from_spec(DOCTOR_SPEC)
sys.modules[DOCTOR_SPEC.name] = doctor
DOCTOR_SPEC.loader.exec_module(doctor)
PLANNER_SPEC = importlib.util.spec_from_file_location("legacy_scope_planner", TOOLS / "legacy_scope_planner.py")
assert PLANNER_SPEC is not None and PLANNER_SPEC.loader is not None
planner = importlib.util.module_from_spec(PLANNER_SPEC)
sys.modules[PLANNER_SPEC.name] = planner
PLANNER_SPEC.loader.exec_module(planner)

DATA = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))
CASES = {case["name"]: case for case in DATA["cases"]}
DAG_RAW = (ROOT / planner.DAG_PATH).read_bytes()
DAG = json.loads(DAG_RAW)
GIT_HEAD = DATA["constants"]["git_head"]
INDEX_TREE = DATA["constants"]["index_tree"]
WORKTREE_DIGEST = DATA["constants"]["worktree_digest"]
RUNNER_SNAPSHOT_ID = DATA["constants"]["runner_snapshot_id"]


def scope_pairs(values):
    return [{"path": path, "kind": kind} for path, kind in values]


def participant(raw):
    actions = []
    for source in raw.get("actions", []):
        actions.append({
            "id": source["id"],
            "type": source["type"],
            "outputs": scope_pairs(source.get("outputs", [])),
            "prefixes": scope_pairs(source.get("prefixes", [])),
            "promotion_group": source.get("promotion_group"),
        })
    return {
        "id": raw["id"],
        "actor": {"id": "actor:" + raw["id"]},
        "reads": scope_pairs(raw.get("reads", [])),
        "writes": scope_pairs(raw.get("writes", [])),
        "sources": scope_pairs(raw.get("sources", [])),
        "actions": actions,
        "after": raw.get("after", []),
    }


def request_for(case):
    return {
        "schema": planner.REQUEST_SCHEMA,
        "participants": [participant(item) for item in case["participants"]],
        "snapshots": {
            "git": {"head": GIT_HEAD, "index_tree": INDEX_TREE, "worktree_digest": WORKTREE_DIGEST, "dirty": scope_pairs(case.get("git_dirty", []))},
            "runner": {
                "snapshot_id": RUNNER_SNAPSHOT_ID,
                "reads": scope_pairs(case.get("runner_reads", [])),
                "writes": scope_pairs(case.get("runner_writes", [])),
            },
        },
    }


def doctor_report(claims=None, verdict="CLEAN", findings=None):
    return {
        "schema": doctor.REPORT_SCHEMA,
        "verdict": verdict,
        "inputs": [{"path": "TODO.md", "bytes": 1, "sha256": "a" * 64}],
        "normalized": {"claims": claims or []},
        "findings": findings or [],
    }


def injected_plan(root, request, **kwargs):
    kwargs.setdefault("doctor_report", doctor_report())
    kwargs.setdefault("dag_value", DAG)
    return planner.plan_request(root, request, injected_inputs=True, **kwargs)


def snapshot_tree(root):
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            result[relative] = ("symlink", stat.S_IMODE(info.st_mode), os.readlink(path))
        elif path.is_file():
            result[relative] = ("file", stat.S_IMODE(info.st_mode), path.read_bytes())
        else:
            result[relative] = ("directory", stat.S_IMODE(info.st_mode), None)
    return result


class LegacyScopePlannerFixtureTests(unittest.TestCase):
    def test_fixture_manifest_is_complete_and_versioned(self):
        manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(DATA["schema"], "legacy-scope-planner-fixtures@v1")
        self.assertEqual(manifest["schema"], "legacy-scope-planner-fixture-manifest@v1")
        self.assertEqual(set(manifest["cases"]), set(CASES))

    def test_all_collision_and_plan_cases(self):
        for name, case in sorted(CASES.items()):
            with self.subTest(case=name):
                result = injected_plan(ROOT, request_for(case), dag_raw=DAG_RAW)
                self.assertEqual(result["verdict"], case["verdict"])
                classes = {item["class"] for item in result["collisions"]}
                self.assertTrue(set(case["classes"]).issubset(classes), (name, classes))
                if result["verdict"] == "BLOCK":
                    self.assertEqual(result["plan"]["strategy"], "block")
                    self.assertTrue(result["plan"]["safe_serialization_order"])
                for token in case.get("chain_contains", []):
                    chains = [value for collision in result["collisions"] for chain in collision["producer_chains"] for value in chain]
                    self.assertIn(token, chains)

    def test_deterministic_result_and_digest_bindings(self):
        request = request_for(CASES["issue-dag-transitive"])
        raw = planner._canonical_bytes(request)
        report = doctor_report()
        first = injected_plan(ROOT, request, doctor_report=report, request_raw=raw, dag_raw=DAG_RAW)
        second = injected_plan(ROOT, request, doctor_report=report, request_raw=raw, dag_raw=DAG_RAW)
        self.assertEqual(planner._canonical_bytes(first), planner._canonical_bytes(second))
        self.assertEqual(first["bindings"]["request"], "sha256:" + hashlib.sha256(raw).hexdigest())
        self.assertEqual(first["bindings"]["dag"], "sha256:" + hashlib.sha256(DAG_RAW).hexdigest())
        self.assertIsNone(first["bindings"]["dag_path"])
        self.assertEqual(first["bindings"]["dag_source"], "injected")
        self.assertEqual(first["bindings"]["doctor_source"], "injected")
        self.assertEqual(first["bindings"]["snapshots"], request["snapshots"])
        self.assertEqual(first["bindings"]["doctor_inputs"], "sha256:" + hashlib.sha256(planner._canonical_bytes(report)).hexdigest())
        changed_report = copy.deepcopy(report)
        changed_report["verdict"] = "FINDINGS"
        changed = injected_plan(ROOT, request, doctor_report=changed_report, request_raw=raw, dag_raw=DAG_RAW)
        self.assertNotEqual(first["bindings"]["doctor_inputs"], changed["bindings"]["doctor_inputs"])


class LegacyScopePlannerClaimTests(unittest.TestCase):
    def test_scan_repository_is_reused_for_active_claims(self):
        request = request_for(CASES["disjoint-page-locale"])
        with mock.patch.object(planner.legacy_task_doctor, "scan_repository", return_value=doctor_report()) as scan, mock.patch.object(planner, "_read_regular", return_value=DAG_RAW) as read:
            result = planner.plan_request(ROOT, request)
        scan.assert_called_once_with(ROOT.resolve())
        read.assert_called_once_with(ROOT / planner.DAG_PATH, "authoritative DAG", planner.MAX_DAG_BYTES)
        self.assertEqual(result["bindings"]["dag_path"], planner.DAG_PATH)
        self.assertEqual(result["bindings"]["dag_source"], "authoritative-root")

    def test_missing_or_malformed_foreign_scope_is_incomplete(self):
        base = {"path": "TODO-foreign-1000-01-claim.md", "state": "p", "owner_token": "agent:foreign:1000-01:claim-id"}
        for scopes in ([], ["../escape.py"], ["missing/nonexistent.py"]):
            with self.subTest(scopes=scopes):
                claim = dict(base, scopes=scopes)
                result = injected_plan(ROOT, request_for(CASES["disjoint-page-locale"]), doctor_report=doctor_report([claim]), dag_raw=DAG_RAW)
                self.assertEqual(result["verdict"], "INCOMPLETE")
                self.assertEqual(result["collisions"][0]["class"], "unknown-incomplete-scope")
        claim = dict(base, scopes=["_src/tools/legacy_scope_planner.py"])
        finding = {"path": claim["path"], "rule": "LTD-CLAIM-SCOPE-INVALID"}
        result = injected_plan(ROOT, request_for(CASES["disjoint-page-locale"]), doctor_report=doctor_report([claim], verdict="FINDINGS", findings=[finding]), dag_raw=DAG_RAW)
        self.assertEqual(result["verdict"], "INCOMPLETE")

    def test_supplied_claim_identity_and_scope_must_match_exactly(self):
        raw = participant({"id": "mine", "writes": [["_src/tools/legacy_scope_planner.py", "file"]]})
        raw["actor"] = {"id": "agent:me:1000-01:claim-id", "owner_token": "agent:me:1000-01:claim-id", "claim_path": "TODO-me-1000-01-claim.md"}
        request = request_for(CASES["disjoint-page-locale"])
        request["participants"] = [raw]
        claim = {"path": "TODO-me-1000-01-claim.md", "state": "p", "owner_token": "agent:me:1000-01:claim-id", "scopes": ["_src/tools/legacy_scope_planner.py"]}
        result = injected_plan(ROOT, request, doctor_report=doctor_report([claim]), dag_raw=DAG_RAW)
        self.assertEqual(result["verdict"], "PARALLEL")
        tampered = copy.deepcopy(request)
        tampered["participants"][0]["actor"]["owner_token"] = "agent:other:1000-01:claim-id"
        result = injected_plan(ROOT, tampered, doctor_report=doctor_report([claim]), dag_raw=DAG_RAW)
        self.assertEqual(result["verdict"], "INCOMPLETE")

    def test_foreign_canonical_write_expands_and_collides_with_derived_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "issues" / "foreign.md"
            source.parent.mkdir(parents=True)
            source.write_text("fixture\n", encoding="utf-8")
            request = request_for(CASES["disjoint-page-locale"])
            request["participants"] = [participant({"id": "proposed", "actions": [{"id": "publish-foreign", "type": "publication", "outputs": [["en/issues/index.html", "file"]]}]})]
            claim = {"path": "TODO-foreign-1000-01-claim.md", "state": "p", "owner_token": "agent:foreign:1000-01:claim-id", "scopes": ["issues/foreign.md"]}
            result = injected_plan(root, request, doctor_report=doctor_report([claim]), dag_raw=DAG_RAW)
            self.assertEqual(result["verdict"], "BLOCK")
            collision = next(item for item in result["collisions"] if item["class"] == "source-vs-derived")
            self.assertIn("claim:TODO-foreign-1000-01-claim.md", collision["participants"])
            self.assertTrue(any("issues/foreign.md" in chain for chain in collision["producer_chains"]))

    def test_foreign_directory_sources_expand_segment_safely(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in ("issues", "issues/nested", "issues-archive"):
                (root / relative).mkdir(parents=True, exist_ok=True)
            for relative, expected in (("issues", "BLOCK"), ("issues/nested", "BLOCK"), ("issues-archive", "PARALLEL")):
                with self.subTest(directory=relative):
                    request = request_for(CASES["disjoint-page-locale"])
                    request["participants"] = [participant({"id": "proposed", "actions": [{"id": "publish-directory", "type": "publication", "outputs": [["en/issues/index.html", "file"]]}]})]
                    claim = {"path": "TODO-foreign-1000-01-directory.md", "state": "p", "owner_token": "agent:foreign:1000-01:directory-claim", "scopes": [relative]}
                    result = injected_plan(root, request, doctor_report=doctor_report([claim]), dag_raw=DAG_RAW)
                    self.assertEqual(result["verdict"], expected)
                    if expected == "BLOCK":
                        collision = next(item for item in result["collisions"] if item["class"] == "source-vs-derived")
                        chains = [value for chain in collision["producer_chains"] for value in chain]
                        self.assertIn(relative, chains)
                        self.assertIn("render-html", chains)
                        self.assertIn("en/issues/index.html", chains)
                    else:
                        self.assertEqual(result["collisions"], [])

    def test_duplicate_synthesized_claim_ids_fail_closed_after_merge(self):
        claim = {"path": "TODO-foreign-1000-01-claim.md", "state": "p", "owner_token": "agent:foreign:1000-01:claim-id", "scopes": ["_src/tools/legacy_scope_planner.py"]}
        result = injected_plan(ROOT, request_for(CASES["disjoint-page-locale"]), doctor_report=doctor_report([claim, dict(claim)]), dag_raw=DAG_RAW)
        self.assertEqual(result["verdict"], "INCOMPLETE")
        self.assertIn("not unique", result["collisions"][0]["explanation"])


class LegacyScopePlannerContractTests(unittest.TestCase):
    def setUp(self):
        self.request = request_for(CASES["disjoint-page-locale"])

    def test_duplicate_unknown_unsafe_and_oversized_requests_fail_closed(self):
        duplicate = b'{"schema":"legacy-scope-planner-request@v1","schema":"legacy-scope-planner-request@v1"}'
        with self.assertRaises(planner.DuplicateKeyError):
            planner._load_json(duplicate, "request", planner.MAX_REQUEST_BYTES)
        unknown = copy.deepcopy(self.request)
        unknown["unexpected"] = True
        with self.assertRaisesRegex(planner.ContractError, "unknown fields"):
            injected_plan(ROOT, unknown)
        unsafe = copy.deepcopy(self.request)
        unsafe["participants"][0]["writes"] = [{"path": "run.sh", "kind": "file"}]
        with self.assertRaisesRegex(planner.ContractError, "run.sh"):
            injected_plan(ROOT, unsafe)
        unsafe["participants"][0]["writes"] = [{"path": "run.sh/candidate", "kind": "file"}]
        with self.assertRaisesRegex(planner.ContractError, "run.sh"):
            injected_plan(ROOT, unsafe)
        unsafe["participants"][0]["writes"] = [{"path": "src/control\n.py", "kind": "file"}]
        with self.assertRaisesRegex(planner.ContractError, "control"):
            injected_plan(ROOT, unsafe)
        glob_write = copy.deepcopy(self.request)
        glob_write["participants"][0]["writes"] = [{"path": "src/*.py", "kind": "file"}]
        with self.assertRaisesRegex(planner.ContractError, "glob"):
            injected_plan(ROOT, glob_write)
        with self.assertRaisesRegex(planner.ContractError, "exceeds"):
            injected_plan(ROOT, self.request, request_raw=b"x" * (planner.MAX_REQUEST_BYTES + 1))

    def test_snapshot_freshness_contract_is_required_closed_and_valid(self):
        for container, field in (("git", "head"), ("git", "index_tree"), ("git", "worktree_digest"), ("runner", "snapshot_id")):
            request = copy.deepcopy(self.request)
            del request["snapshots"][container][field]
            with self.subTest(missing=field), self.assertRaisesRegex(planner.ContractError, "missing fields"):
                injected_plan(ROOT, request)
        invalid = copy.deepcopy(self.request)
        invalid["snapshots"]["git"]["head"] = "abc123"
        with self.assertRaisesRegex(planner.ContractError, "full lowercase commit"):
            injected_plan(ROOT, invalid)
        invalid = copy.deepcopy(self.request)
        invalid["snapshots"]["git"]["index_tree"] = "abc123"
        with self.assertRaisesRegex(planner.ContractError, "tree OID"):
            injected_plan(ROOT, invalid)
        unknown = copy.deepcopy(self.request)
        unknown["snapshots"]["runner"]["nonce"] = "unexpected"
        with self.assertRaisesRegex(planner.ContractError, "unknown fields"):
            injected_plan(ROOT, unknown)

    def test_injected_data_requires_explicit_mode_and_never_claims_root_authority(self):
        with self.assertRaisesRegex(planner.ContractError, "injected_inputs=True"):
            planner.plan_request(ROOT, self.request, doctor_report=doctor_report(), dag_value=DAG)
        with self.assertRaisesRegex(planner.ContractError, "requires both"):
            planner.plan_request(ROOT, self.request, dag_value=DAG, injected_inputs=True)
        result = injected_plan(ROOT, self.request)
        self.assertIsNone(result["bindings"]["dag_path"])
        self.assertEqual(result["bindings"]["dag_source"], "injected")
        with self.assertRaisesRegex(planner.ContractError, "request_raw"):
            injected_plan(ROOT, self.request, request_raw=planner._canonical_bytes(request_for(CASES["exact-file"])))
        changed_dag = copy.deepcopy(DAG)
        changed_dag["generation_id_rule"] += " changed"
        with self.assertRaisesRegex(planner.ContractError, "dag_raw"):
            injected_plan(ROOT, self.request, dag_value=changed_dag, dag_raw=DAG_RAW)

    def test_sources_must_match_dag_and_duplicate_write_source_expands_once(self):
        unmatched = copy.deepcopy(self.request)
        unmatched["participants"][0]["sources"] = [{"path": "legacy/source.txt", "kind": "file"}]
        result = injected_plan(ROOT, unmatched)
        self.assertEqual(result["verdict"], "INCOMPLETE")
        self.assertIn("matches no authoritative", result["collisions"][0]["explanation"])
        write_only = request_for(CASES["write-auto-derived"])
        duplicated = copy.deepcopy(write_only)
        duplicated["participants"][0]["sources"] = [{"path": "issues/a.md", "kind": "file"}]
        first = injected_plan(ROOT, write_only)
        second = injected_plan(ROOT, duplicated)
        self.assertEqual(first["collisions"], second["collisions"])

    def test_reserved_participant_ids_and_empty_actions_are_rejected(self):
        for participant_id in ("claim:forged", "@runner"):
            request = copy.deepcopy(self.request)
            request["participants"][0]["id"] = participant_id
            with self.subTest(participant_id=participant_id), self.assertRaisesRegex(planner.ContractError, "reserved prefix"):
                injected_plan(ROOT, request)
        request = copy.deepcopy(self.request)
        request["participants"][0]["actions"][0]["outputs"] = []
        request["participants"][0]["actions"][0]["prefixes"] = []
        with self.assertRaisesRegex(planner.ContractError, "output or prefix"):
            injected_plan(ROOT, request)

    def test_tampered_dag_duplicate_writer_cycle_and_derived_input_fail(self):
        duplicate = copy.deepcopy(DAG)
        duplicate["stages"][1]["outputs"].append(duplicate["stages"][0]["outputs"][0])
        cycle = copy.deepcopy(DAG)
        cycle["stages"][0]["depends_on"] = ["render-reports"]
        missing = copy.deepcopy(DAG)
        missing["stages"][2]["inputs"][0]["glob"] = "data/not-produced.json"
        for value, message in ((duplicate, "multiple sole writers"), (cycle, "cycle"), (missing, "no exact producer")):
            with self.subTest(message=message), self.assertRaisesRegex(planner.ContractError, message):
                injected_plan(ROOT, self.request, dag_value=value)

    def test_all_ids_and_ordering_edges_are_unique_and_acyclic(self):
        duplicate = copy.deepcopy(self.request)
        duplicate["participants"].append(copy.deepcopy(duplicate["participants"][0]))
        with self.assertRaisesRegex(planner.ContractError, "duplicate participant"):
            injected_plan(ROOT, duplicate)
        duplicate_actor = copy.deepcopy(self.request)
        duplicate_actor["participants"][1]["actor"] = copy.deepcopy(duplicate_actor["participants"][0]["actor"])
        with self.assertRaisesRegex(planner.ContractError, "duplicate actor"):
            injected_plan(ROOT, duplicate_actor)
        duplicate_action = request_for(CASES["disjoint-page-locale"])
        duplicate_action["participants"][1]["actions"][0]["id"] = duplicate_action["participants"][0]["actions"][0]["id"]
        with self.assertRaisesRegex(planner.ContractError, "duplicate action"):
            injected_plan(ROOT, duplicate_action)
        cycle = request_for(CASES["explicit-order"])
        cycle["participants"][0]["after"] = ["b"]
        with self.assertRaisesRegex(planner.ContractError, "cycle"):
            injected_plan(ROOT, cycle)

    def test_block_serialization_respects_order_and_snapshot_blockers(self):
        request = request_for(CASES["exact-file"])
        request["participants"][1]["after"] = ["a"]
        request["snapshots"]["runner"]["reads"] = [{"path": "src/a.py", "kind": "file"}]
        result = injected_plan(ROOT, request)
        self.assertEqual(result["verdict"], "BLOCK")
        self.assertEqual(result["plan"]["safe_serialization_order"], ["@runner", "a", "b"])


class LegacyScopePlannerFilesystemSafetyTests(unittest.TestCase):
    def _request_with_write(self, path, kind):
        request = request_for(CASES["disjoint-page-locale"])
        request["participants"] = [participant({"id": "writer", "writes": [[path, kind]]})]
        return request

    def test_requested_symlink_target_and_ancestor_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "real").mkdir()
            (root / "real" / "file.txt").write_text("x", encoding="utf-8")
            (root / "alias").symlink_to(root / "real", target_is_directory=True)
            (root / "link.txt").symlink_to(root / "real" / "file.txt")
            for path in ("alias/file.txt", "link.txt"):
                with self.subTest(path=path), self.assertRaisesRegex(planner.ContractError, "symlink"):
                    injected_plan(root, self._request_with_write(path, "file"))

    def test_existing_target_type_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "folder").mkdir()
            (root / "file.txt").write_text("x", encoding="utf-8")
            for path, kind in (("folder", "file"), ("file.txt", "directory")):
                with self.subTest(path=path, kind=kind), self.assertRaisesRegex(planner.ContractError, "type mismatches"):
                    injected_plan(root, self._request_with_write(path, kind))

    def test_foreign_symlink_scope_is_incomplete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "real.txt").write_text("x", encoding="utf-8")
            (root / "alias.txt").symlink_to(root / "real.txt")
            claim = {"path": "TODO-foreign-1000-01-claim.md", "state": "p", "owner_token": "agent:foreign:1000-01:claim-id", "scopes": ["alias.txt"]}
            result = injected_plan(root, request_for(CASES["disjoint-page-locale"]), doctor_report=doctor_report([claim]))
            self.assertEqual(result["verdict"], "INCOMPLETE")
            self.assertIn("unknown or malformed", result["collisions"][0]["explanation"])


class LegacyScopePlannerReadOnlyTests(unittest.TestCase):
    def _write_minimal_repository(self, root):
        files = {
            "AGENTS.md": "# Agents\n",
            "DONE.md": "# Done\n",
            "PRIVILEGED.md": "# Privileged\n",
            "SANDBOX.md": "# Sandbox\n",
            "TODO.md": "# TODO — Open Point List\n\n## Feature: 1000 — Fixture\n\n- [ ] **1000-01** Open.\n",
            "agent-workflow.json": json.dumps({
                "schema": "agent-workflow-bootstrap@v1", "workflow_version": "1.0.0",
                "authority_epoch": "legacy-writable", "authority_profile": "legacy-lists",
                "write_phase": "legacy-writable", "required_capability": "sandboxed-grunt",
                "runner_protocol": "runner-request@v1",
                "selector_digest": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                "instruction_bundle": "docs/pipeline/agent-instructions/legacy/index.md",
            }) + "\n",
            "docs/pipeline/agent-instructions/legacy/index.md": "# Legacy\n",
            planner.DAG_PATH: DAG_RAW.decode("utf-8"),
            "unrelated.bin": "preserve-me\u0000exactly",
        }
        for relative, text in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))

    def test_production_planner_has_no_filesystem_mutation_api(self):
        tree = ast.parse((TOOLS / "legacy_scope_planner.py").read_text(encoding="utf-8"))
        forbidden = {"chmod", "hardlink_to", "mkdir", "rename", "rmdir", "symlink_to", "touch", "unlink", "write_bytes", "write_text"}
        calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertEqual(calls & forbidden, set())
        self.assertNotIn("subprocess", {node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)})

    def test_library_planning_mutates_no_unrelated_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "unrelated.bin").write_bytes(b"\x00\xffpreserve")
            before = snapshot_tree(root)
            injected_plan(root, request_for(CASES["disjoint-page-locale"]), dag_raw=DAG_RAW)
            self.assertEqual(snapshot_tree(root), before)

    def test_cli_is_read_only_and_emits_closed_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_minimal_repository(root)
            request_path = root / "request.json"
            request_path.write_bytes(planner._canonical_bytes(request_for(CASES["disjoint-page-locale"])))
            before = snapshot_tree(root)
            completed = subprocess.run(
                [sys.executable, str(TOOLS / "legacy_scope_planner.py"), "--root", str(root), "--request", str(request_path), "--json"],
                check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
            result = json.loads(completed.stdout)
            self.assertEqual(result["schema"], planner.RESULT_SCHEMA)
            self.assertEqual(result["verdict"], "PARALLEL")
            self.assertEqual(result["bindings"]["dag_path"], planner.DAG_PATH)
            self.assertEqual(result["bindings"]["dag_source"], "authoritative-root")
            self.assertEqual(result["bindings"]["doctor_source"], "authoritative-scan")
            self.assertEqual(result["bindings"]["snapshots"], request_for(CASES["disjoint-page-locale"])["snapshots"])
            self.assertEqual(snapshot_tree(root), before)

    def test_cli_invalid_request_is_incomplete_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_minimal_repository(root)
            request_path = root / "request.json"
            request_path.write_text('{"schema":"wrong"}\n', encoding="utf-8")
            before = snapshot_tree(root)
            completed = subprocess.run(
                [sys.executable, str(TOOLS / "legacy_scope_planner.py"), "--root", str(root), "--request", str(request_path), "--json"],
                check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(json.loads(completed.stdout)["verdict"], "INCOMPLETE")
            self.assertEqual(snapshot_tree(root), before)


if __name__ == "__main__":
    unittest.main()
