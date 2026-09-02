"""Recovery tests for the executable issue regeneration surface.

AE binding:
- baseline: 744b3f0b9fc02cc1f6526927ff8d4e78c93319f7 (commands absent)
- candidate: the carrying commit containing this test (commands executable)
- falsification: ``test_full_write_then_check_is_idempotent`` is red on the
  baseline because ``issue_regenerate.py`` and ``issuectl regenerate`` do not
  exist there, and green on the candidate.
- adjacent cases: stale declared bytes and an unexplained extra output are
  distinct neighboring output-set dimensions with different expected results.
- property evidence: ``test_topological_order_exhaustive_property`` enumerates
  64 dependency masks and asserts dependency precedence plus exact membership.
"""
from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "_src/tools/issue_regenerate.py"


def _load():
    spec = importlib.util.spec_from_file_location("issue_regenerate_recovery_test", PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


regen = _load()
STAGES = tuple(regen.iv.REQUIRED_STAGE_IDS)


def _manifest() -> dict[str, object]:
    stages = []
    for index, stage_id in enumerate(STAGES):
        stages.append({
            "id": stage_id,
            "argv": ["python3", "tool.py", stage_id],
            "depends_on": [] if index == 0 else [STAGES[index - 1]],
            "inputs": [],
            "outputs": [f"generated/{index:02d}-{stage_id}.json"],
        })
    return {"schema": "issue-regeneration-dag@v1", "stages": stages}


def _handler(stage_id):
    def run(ctx, stage):
        relative = stage["outputs"][0]
        return [regen._write_json(ctx["staging"], relative, {"stage": stage_id})]
    return run


class RegenerationFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        (self.repo / "issues").mkdir()
        (self.repo / "provenance").mkdir()
        self.dag = self.repo / "dag.json"
        self.dag.write_text(regen.canonical_json(_manifest()), encoding="utf-8")
        self.target = self.base / "generated-shadow"
        self.handlers = {stage_id: _handler(stage_id) for stage_id in STAGES}
        self._selector("legacy-lists", "legacy-writable")

    def tearDown(self):
        self.temp.cleanup()

    def _selector(self, profile, phase):
        (self.repo / "agent-workflow.json").write_text(regen.canonical_json({
            "schema": "agent-workflow-bootstrap@v1",
            "authority_profile": profile,
            "authority_epoch": phase,
            "write_phase": phase,
        }), encoding="utf-8")

    def execute(self, **overrides):
        values = {
            "repo": self.repo,
            "output_root": self.target,
            "dag_path": self.dag,
            "write": False,
        }
        values.update(overrides)
        with mock.patch.dict(regen.HANDLERS, self.handlers, clear=True):
            return regen.execute(**values)


class RegenerationExecutionTests(RegenerationFixture):
    def test_full_write_then_check_is_idempotent(self):
        first = self.execute(write=True)
        before = regen.tree_manifest(self.target)
        second = self.execute(write=True)
        check = self.execute(write=False)
        self.assertEqual(first["stage_order"], list(STAGES))
        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])
        self.assertEqual(before, regen.tree_manifest(self.target))
        self.assertEqual(check["status"], "PASS")
        self.assertEqual(check["counts"]["missing"], 0)
        self.assertEqual(check["counts"]["stale"], 0)
        self.assertEqual(check["counts"]["unexplained"], 0)
        self.assertEqual(first["run_id"], second["run_id"])

    def test_stage_failure_preserves_prior_promoted_tree(self):
        self.execute(write=True)
        before = regen.tree_manifest(self.target)
        with self.assertRaises(regen.RegenerateError) as raised:
            self.execute(write=True, fail_stage="build-graphs")
        self.assertIn("IR1099", str(raised.exception))
        self.assertEqual(regen.tree_manifest(self.target), before)

    def test_stale_declared_output_is_detected(self):
        """AE adjacent case 1: same declared path, wrong bytes => stale only."""
        self.execute(write=True)
        path = self.target / _manifest()["stages"][0]["outputs"][0]
        path.write_text("stale\n", encoding="utf-8")
        result = self.execute(write=False)
        self.assertEqual(result["status"], "STALE")
        self.assertEqual(result["counts"]["stale"], 1)
        self.assertEqual(result["counts"]["unexplained"], 0)

    def test_unexplained_output_is_detected_and_blocks_write(self):
        """AE adjacent case 2: undeclared path => unexplained and fail closed."""
        self.execute(write=True)
        extra = self.target / "generated/unexplained.json"
        extra.write_text("{}\n", encoding="utf-8")
        result = self.execute(write=False)
        self.assertEqual(result["counts"]["unexplained"], 1)
        with self.assertRaises(regen.RegenerateError) as raised:
            self.execute(write=True)
        self.assertIn("IR1028", str(raised.exception))
        self.assertTrue(extra.is_file())

    def test_bounded_machine_result_and_human_report(self):
        result = self.execute(write=True)
        self.assertEqual(result["schema"], regen.RESULT_SCHEMA)
        self.assertEqual(set(result["counts"]), {"stages", "outputs", "missing", "stale", "unexplained"})
        self.assertLessEqual(len(result["diff"]["missing"]), regen.MAX_FINDINGS)
        output = io.StringIO()
        with redirect_stdout(output):
            code = regen.emit(result, "human")
        self.assertEqual(code, 0)
        self.assertLessEqual(len(output.getvalue().splitlines()), 1)


class BootstrapRefreshTests(RegenerationFixture):
    def test_refresh_checks_all_three_shared_projections_without_persistent_write(self):
        catalog = {"items": [{"id": "0037", "state": "open"}], "generation_id": "sha256:x"}
        graph = {"nodes": [{"id": "0037"}], "edges": [], "generation_id": "sha256:y"}
        groups = {"open": [catalog["items"][0]], "blocked": []}
        documents = {
            key: f"{key}\n"
            for key in ("todo", "done", "open", "blocked", "unclear", "owners")
        }
        validation = {"exit_code": 0, "item_count": 1, "diagnostics": []}
        with mock.patch.object(regen.views, "render", return_value=(catalog, graph)), \
             mock.patch.object(regen.lists, "render_lists", return_value=(catalog, groups, documents)), \
             mock.patch.object(regen, "_validate_payload", return_value=validation):
            result = regen.bootstrap_refresh(repo=self.repo, output_root=None, write=False)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["counts"]["items"], 1)
        self.assertEqual(result["counts"]["outputs"], 8)
        self.assertFalse(self.target.exists())

    def test_refresh_write_is_idempotent_and_never_targets_legacy_root(self):
        catalog = {"items": [], "generation_id": "sha256:x"}
        graph = {"nodes": [], "edges": [], "generation_id": "sha256:y"}
        groups = {"open": [], "blocked": []}
        documents = {
            key: f"{key}\n"
            for key in ("todo", "done", "open", "blocked", "unclear", "owners")
        }
        validation = {"exit_code": 0, "item_count": 0, "diagnostics": []}
        patches = (
            mock.patch.object(regen.views, "render", return_value=(catalog, graph)),
            mock.patch.object(regen.lists, "render_lists", return_value=(catalog, groups, documents)),
            mock.patch.object(regen, "_validate_payload", return_value=validation),
        )
        with patches[0], patches[1], patches[2]:
            first = regen.bootstrap_refresh(repo=self.repo, output_root=self.target, write=True)
            second = regen.bootstrap_refresh(repo=self.repo, output_root=self.target, write=True)
        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])
        self.assertTrue((self.target / "lists/TODO.md").is_file())
        self.assertFalse((self.repo / "TODO.md").exists())


class AuthorityMatrixTests(RegenerationFixture):
    def test_legacy_frozen_writable_matrix(self):
        cases = (
            ("legacy-lists", "legacy-writable", self.repo / "unsafe", False),
            ("legacy-lists", "legacy-writable", self.repo / "generated-shadow", True),
            ("issue-store", "issue-store-frozen", self.repo / "derived", True),
            ("issue-store", "issue-store-writable", self.repo / "derived", True),
        )
        for profile, phase, target, allowed in cases:
            with self.subTest(profile=profile, phase=phase, target=target.name):
                self._selector(profile, phase)
                selector = regen.load_selector(self.repo)
                if allowed:
                    regen.authorize_output_root(self.repo, target, selector)
                else:
                    with self.assertRaises(regen.RegenerateError):
                        regen.authorize_output_root(self.repo, target, selector)
                for canonical in (self.repo / "issues", self.repo / "provenance"):
                    with self.assertRaises(regen.RegenerateError):
                        regen.authorize_output_root(self.repo, canonical, selector)


class DagPropertyTests(unittest.TestCase):
    def test_topological_order_exhaustive_property(self):
        """AE-5 exhaustive domain: 64 masks, exact set and dependency precedence."""
        nodes = ("a", "b", "c", "d")
        possible = (("b", "a"), ("c", "a"), ("c", "b"), ("d", "a"), ("d", "b"), ("d", "c"))
        case_count = 0
        for mask in range(1 << len(possible)):
            by_id = {node: {"depends_on": []} for node in nodes}
            selected = []
            for bit, (child, parent) in enumerate(possible):
                if mask & (1 << bit):
                    by_id[child]["depends_on"].append(parent)
                    selected.append((child, parent))
            order = regen.topological_order(by_id, nodes)
            positions = {node: index for index, node in enumerate(order)}
            self.assertEqual(set(order), set(nodes))
            self.assertEqual(len(order), len(nodes))
            for child, parent in selected:
                self.assertLess(positions[parent], positions[child])
            case_count += 1
        self.assertEqual(case_count, 64)

    def test_cycle_and_output_owner_fail_closed(self):
        by_id = {"a": {"depends_on": ["b"]}, "b": {"depends_on": ["a"]}}
        with self.assertRaises(regen.RegenerateError):
            regen.topological_order(by_id)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "dag.json"
            manifest = _manifest()
            manifest["stages"][1]["outputs"] = list(manifest["stages"][0]["outputs"])
            path.write_text(regen.canonical_json(manifest), encoding="utf-8")
            with self.assertRaises(regen.RegenerateError) as raised:
                regen.load_manifest(path)
            self.assertIn("IR1013", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
