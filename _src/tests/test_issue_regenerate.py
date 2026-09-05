"""Recovery tests for the executable issue regeneration surface.

AE binding:
- baseline: 744b3f0b9fc02cc1f6526927ff8d4e78c93319f7 (commands absent)
- candidate: the carrying commit containing this test (commands executable)
- falsification: ``test_full_write_then_check_is_idempotent`` is red on the
  baseline because ``issue_regenerate.py`` and ``issuectl regenerate`` do not
  exist there, and green on the candidate.
- adjacent cases: stale declared bytes, unexplained output, rejected path
  aliases, and output-root collisions are distinct neighboring dimensions.
- property evidence: ``test_topological_order_exhaustive_property`` enumerates
  64 dependency masks; the path/root matrices execute 15 and 27 cases.
"""
from __future__ import annotations

import importlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import threading
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
        self.assertFalse((self.base / ".generated-shadow.issue-regeneration.lock").exists())
        self.assertEqual(self.execute(write=False)["status"], "PASS")

    def test_output_root_lock_has_stable_collision_and_preserves_tree(self):
        """AE concurrency: one generation owns the root; a peer fails IR1034."""
        entered = threading.Event()
        release = threading.Event()
        original = self.handlers[STAGES[0]]

        def blocking(ctx, stage):
            if threading.current_thread().name == "regeneration-owner":
                entered.set()
                self.assertTrue(release.wait(5))
            return original(ctx, stage)

        handlers = dict(self.handlers)
        handlers[STAGES[0]] = blocking
        failures = []

        def owner():
            try:
                with mock.patch.dict(regen.HANDLERS, handlers, clear=True):
                    regen.execute(repo=self.repo, output_root=self.target, dag_path=self.dag, write=True)
            except Exception as exc:  # pragma: no cover - asserted below
                failures.append(exc)

        thread = threading.Thread(target=owner, name="regeneration-owner")
        thread.start()
        self.assertTrue(entered.wait(5))
        try:
            with self.assertRaises(regen.RegenerateError) as raised:
                self.execute(write=True)
            self.assertEqual(raised.exception.code, "IR1034")
            self.assertEqual(str(raised.exception), f"IR1034: regeneration collision at {self.target}")
        finally:
            release.set()
            thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual(self.execute(write=False)["status"], "PASS")

    def test_output_root_cas_detects_uncoordinated_change_before_promotion(self):
        self.execute(write=True)
        prior = regen.tree_manifest(self.target)
        changed_path = self.target / _manifest()["stages"][0]["outputs"][0]
        original = self.handlers[STAGES[0]]

        def interfering(ctx, stage):
            changed_path.write_text("external-change\n", encoding="utf-8")
            return original(ctx, stage)

        handlers = dict(self.handlers)
        handlers[STAGES[0]] = interfering
        with mock.patch.dict(regen.HANDLERS, handlers, clear=True):
            with self.assertRaises(regen.RegenerateError) as raised:
                regen.execute(repo=self.repo, output_root=self.target, dag_path=self.dag, write=True)
        self.assertEqual(raised.exception.code, "IR1035")
        self.assertNotEqual(regen.tree_manifest(self.target), prior)
        self.assertEqual(changed_path.read_text(encoding="utf-8"), "external-change\n")

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


class RealManifestContractTests(RegenerationFixture):
    def _literal_repo(self, name: str) -> Path:
        repo = self.base / name
        (repo / "issues/_schema").mkdir(parents=True)
        (repo / "provenance").mkdir()
        (repo / "docs/pipeline").mkdir(parents=True)
        (repo / "_src/tools").mkdir(parents=True)
        selector = {
            "schema": "agent-workflow-bootstrap@v1",
            "authority_profile": "legacy-lists",
            "authority_epoch": "legacy-writable",
            "write_phase": "legacy-writable",
        }
        (repo / "agent-workflow.json").write_text(regen.canonical_json(selector), encoding="utf-8")
        copies = (
            "docs/pipeline/issue-derived-artifacts-v1.json",
            "issues/_schema/issue-item-v1.schema.json",
            "issues/_schema/issue-catalog-v1.schema.json",
            "issues/_schema/issue-dependency-graph-v1.schema.json",
            "_src/tools/issue_store.py",
            "_src/tools/issue_views.py",
        )
        for relative in copies:
            destination = repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        return repo

    def _run(self, repo: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            argv,
            cwd=ROOT,
            env=dict(os.environ, ISSUECTL_REPO=str(repo)),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def _prime(self, repo: Path) -> None:
        completed = self._run(
            repo,
            ["python3", "_src/tools/issuectl.py", "regenerate", "--all", "--write"],
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def _stages(self, repo: Path) -> list[dict[str, object]]:
        path = repo / "docs/pipeline/issue-derived-artifacts-v1.json"
        return json.loads(path.read_text(encoding="utf-8"))["stages"]

    def test_every_literal_manifest_argv_is_implicit_check_without_mutation(self):
        """All seven literal argv arrays check a complete disposable tree."""
        repo = self._literal_repo("literal-contract")
        target = repo / "generated-issues"
        fixture = ROOT / "_src/tests/fixtures/0037-11.01/generated/run-manifest.json"
        fixture_before = fixture.read_bytes()
        index_before = (ROOT / "index.html").read_bytes()

        help_run = self._run(repo, ["python3", "_src/tools/generate.py", "--help"])
        self.assertEqual(help_run.returncode, 0, help_run.stderr)
        self.assertIn("--issues", help_run.stdout)
        self.assertFalse(target.exists())

        self._prime(repo)
        stages = self._stages(repo)
        expected_paths = {path for stage in stages for path in stage["outputs"]}
        self.assertEqual(set(regen.tree_manifest(target)), expected_paths)
        for stage in stages:
            before = regen.tree_manifest(target)
            completed = self._run(repo, list(stage["argv"]))
            self.assertEqual(completed.returncode, 0, f"{stage['id']}: {completed.stderr}")
            self.assertEqual(regen.tree_manifest(target), before)
            self.assertLessEqual(len(completed.stdout.splitlines()), 1)
            self.assertLessEqual(len(completed.stderr.splitlines()), 1)

        self.assertEqual(len(expected_paths), 17)
        self.assertEqual(fixture.read_bytes(), fixture_before)
        self.assertEqual((ROOT / "index.html").read_bytes(), index_before)
        self.assertFalse((ROOT / "generated-issues").exists())

    def test_generate_implicit_write_check_and_dry_run_tree_manifests(self):
        stage_id = "render-html"
        cases = (("implicit", [], False), ("write", ["--write"], True), ("check", ["--check"], False), ("dry", ["--dry-run"], False))
        for label, flags, writes in cases:
            with self.subTest(mode=label):
                repo = self._literal_repo(f"generate-{label}")
                self._prime(repo)
                stage = next(item for item in self._stages(repo) if item["id"] == stage_id)
                target = repo / "generated-issues"
                missing = target / str(stage["outputs"][0])
                missing.unlink()
                before = regen.tree_manifest(target)
                completed = self._run(repo, list(stage["argv"]) + flags)
                after = regen.tree_manifest(target)
                if writes:
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertNotEqual(after, before)
                    self.assertTrue(missing.is_file())
                else:
                    self.assertEqual(completed.returncode, 1, completed.stderr)
                    self.assertEqual(json.loads(completed.stdout)["status"], "STALE")
                    self.assertEqual(after, before)
                    self.assertFalse(missing.exists())

    def test_render_and_report_check_modes_preserve_missing_output_trees(self):
        for stage_id in ("build-internal-catalog", "render-reports"):
            for flag in ("--check", "--dry-run"):
                with self.subTest(stage=stage_id, flag=flag):
                    repo = self._literal_repo(f"{stage_id}-{flag[2:]}")
                    self._prime(repo)
                    stage = next(item for item in self._stages(repo) if item["id"] == stage_id)
                    target = repo / "generated-issues"
                    for relative in stage["outputs"]:
                        (target / str(relative)).unlink()
                    before = regen.tree_manifest(target)
                    completed = self._run(repo, list(stage["argv"]) + [flag])
                    self.assertEqual(completed.returncode, 1, completed.stderr)
                    self.assertEqual(json.loads(completed.stdout)["status"], "STALE")
                    self.assertEqual(regen.tree_manifest(target), before)


class HermeticRelatedSuiteTests(unittest.TestCase):
    def test_issue_lists_suite_uses_disposable_golden_and_preserves_fixture(self):
        """Regression guard for the historical run-manifest fixture leak."""
        module = importlib.import_module("_src.tests.test_issue_lists")
        fixture = ROOT / "_src/tests/fixtures/0037-11.01/generated/run-manifest.json"
        before = fixture.read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            golden = Path(temporary) / "generated"
            shutil.copytree(module.GOLDEN, golden)
            with mock.patch.object(module, "GOLDEN", golden):
                suite = unittest.defaultTestLoader.loadTestsFromTestCase(module.IssueListsTest)
                stream = io.StringIO()
                result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
            self.assertTrue(result.wasSuccessful(), stream.getvalue())
        self.assertEqual(fixture.read_bytes(), before)


class BootstrapRefreshTests(RegenerationFixture):
    def test_refresh_checks_all_three_shared_projections_without_persistent_write(self):
        # DEC-0037-037: the lists-side catalog item is REQUIRED to carry a
        # "labels" field (views omits it by design); self.repo/"issues" is
        # empty here so the independently-derived canonical labels default
        # to [] for every id, matching this fixture's [] below.
        catalog = {"items": [{"id": "0037", "state": "open"}], "generation_id": "sha256:x"}
        list_catalog = {"items": [{"id": "0037", "state": "open", "labels": []}], "generation_id": "sha256:x"}
        graph = {"nodes": [{"id": "0037"}], "edges": [], "generation_id": "sha256:y"}
        groups = {"open": [catalog["items"][0]], "blocked": []}
        documents = {
            key: f"{key}\n"
            for key in ("todo", "done", "open", "blocked", "unclear", "owners")
        }
        validation = {"exit_code": 0, "item_count": 1, "diagnostics": []}
        with mock.patch.object(regen.views, "render", return_value=(catalog, graph)), \
             mock.patch.object(regen.lists, "render_lists", return_value=(list_catalog, groups, documents)), \
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


class BootstrapCatalogAgreementTests(RegenerationFixture):
    """DEC-0037-037: representation-correct IR1030 comparison.

    AE binding:
    - baseline: eeb4dafc8f12c80e2d656f058e00ae2ace8bca0f (naive `!=` compare
      on full item dicts; raises IR1030 on any labels-only difference)
    - candidate: the carrying commit containing this test (exact ordered
      identity/membership/multiplicity check, non-label field equality, and
      independently-derived canonical-label equality for both sides)
    - falsification: ``test_labels_only_difference_red_on_baseline_green_on_candidate``
      loads the real baseline source via `git show` and proves it raises
      IR1030 on a fixture whose only difference is a "labels" key, while the
      candidate does not.
    - adjacent cases: wrong label content, missing/extra/duplicate/reordered
      identity, non-label field disagreement, a list item missing the
      required labels field, a view item whose own (defensively present)
      labels disagree with canonical, canonical-absence treated as [], and
      input immutability -- eight distinct neighboring dimensions.
    """

    def _basic_catalogs(self, view_extra=None, list_extra=None, canonical_by_id=None):
        view_item = {"id": "X", "state": "open", "title": "T"}
        if view_extra:
            view_item.update(view_extra)
        list_item = {"id": "X", "state": "open", "title": "T", "labels": []}
        if list_extra:
            list_item.update(list_extra)
        catalog = {"items": [view_item]}
        rendered_catalog = {"items": [list_item]}
        return catalog, rendered_catalog

    def _load_store_returning(self, canonical_by_id):
        parsed = [{"item": {"id": item_id, "labels": labels}} for item_id, labels in canonical_by_id.items()]
        return mock.patch.object(regen.views, "load_store", return_value=(parsed, [], []))

    def test_labels_only_difference_red_on_baseline_green_on_candidate(self):
        # Extract the whole _src/tools/ tree as it existed at the pre-repair
        # baseline commit (not just the single file) so the baseline
        # module's own internal _load("issue_validate", ...) sibling
        # lookups resolve against real, contemporaneous sibling sources
        # rather than a bare, dependency-less copy.
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp:
            temp_path = Path(temp)
            archive = subprocess.run(
                ["git", "archive", "eeb4dafc8f12c80e2d656f058e00ae2ace8bca0f", "_src/tools"],
                cwd=ROOT, capture_output=True, check=True,
            ).stdout
            extract = subprocess.run(
                ["tar", "-x", "-C", str(temp_path)], input=archive, capture_output=True, check=True,
            )
            self.assertEqual(extract.returncode, 0)
            baseline_path = temp_path / "_src/tools/issue_regenerate.py"
            self.assertTrue(baseline_path.is_file())
            spec = importlib.util.spec_from_file_location("issue_regenerate_baseline", baseline_path)
            old_regen = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(old_regen)

        view_catalog = {"items": [{"id": "X", "state": "open"}]}
        list_catalog = {"items": [{"id": "X", "state": "open", "labels": []}]}
        validation = {"exit_code": 0, "item_count": 1, "diagnostics": []}
        documents = {key: "" for key in ("todo", "done", "open", "blocked", "unclear", "owners")}
        groups = {"open": [], "blocked": []}

        with mock.patch.object(old_regen.views, "render", return_value=(view_catalog, {})), \
             mock.patch.object(old_regen.lists, "render_lists", return_value=(list_catalog, groups, documents)), \
             mock.patch.object(old_regen, "_validate_payload", return_value=validation):
            with self.assertRaises(old_regen.RegenerateError) as raised:
                old_regen.bootstrap_refresh(repo=self.repo, output_root=None, write=False)
            self.assertEqual(raised.exception.code, "IR1030")

        with mock.patch.object(regen.views, "render", return_value=(view_catalog, {})), \
             mock.patch.object(regen.lists, "render_lists", return_value=(list_catalog, groups, documents)), \
             mock.patch.object(regen, "_validate_payload", return_value=validation):
            result = regen.bootstrap_refresh(repo=self.repo, output_root=None, write=False)
        self.assertEqual(result["status"], "PASS")

    def test_wrong_label_content_on_list_side_blocks(self):
        catalog, rendered_catalog = self._basic_catalogs(list_extra={"labels": ["wrong"]})
        with self._load_store_returning({"X": []}):
            with self.assertRaises(regen.RegenerateError) as raised:
                regen._verify_bootstrap_catalog_agreement(catalog, rendered_catalog, self.repo / "issues", self.repo)
            self.assertEqual(raised.exception.code, "IR1030")

    def test_missing_extra_duplicate_reordered_identity_blocks(self):
        base_view = {"items": [{"id": "A", "state": "open"}, {"id": "B", "state": "open"}]}
        base_list = {"items": [
            {"id": "A", "state": "open", "labels": []},
            {"id": "B", "state": "open", "labels": []},
        ]}
        cases = {
            "missing": {"items": base_list["items"][:1]},
            "extra": {"items": base_list["items"] + [{"id": "C", "state": "open", "labels": []}]},
            "duplicate": {"items": [base_list["items"][0], base_list["items"][0]]},
            "reordered": {"items": list(reversed(base_list["items"]))},
        }
        with self._load_store_returning({"A": [], "B": [], "C": []}):
            for name, rendered_catalog in cases.items():
                with self.subTest(case=name):
                    with self.assertRaises(regen.RegenerateError) as raised:
                        regen._verify_bootstrap_catalog_agreement(base_view, rendered_catalog, self.repo / "issues", self.repo)
                    self.assertEqual(raised.exception.code, "IR1030")

    def test_non_label_field_disagreement_blocks(self):
        catalog, rendered_catalog = self._basic_catalogs(list_extra={"state": "closed"})
        with self._load_store_returning({"X": []}):
            with self.assertRaises(regen.RegenerateError) as raised:
                regen._verify_bootstrap_catalog_agreement(catalog, rendered_catalog, self.repo / "issues", self.repo)
            self.assertEqual(raised.exception.code, "IR1030")

    def test_list_item_missing_required_labels_field_blocks(self):
        catalog = {"items": [{"id": "X", "state": "open"}]}
        rendered_catalog = {"items": [{"id": "X", "state": "open"}]}  # no "labels" key at all
        with self._load_store_returning({"X": []}):
            with self.assertRaises(regen.RegenerateError) as raised:
                regen._verify_bootstrap_catalog_agreement(catalog, rendered_catalog, self.repo / "issues", self.repo)
            self.assertEqual(raised.exception.code, "IR1030")

    def test_view_side_labels_when_present_must_also_match_canonical(self):
        catalog, rendered_catalog = self._basic_catalogs(view_extra={"labels": ["wrong"]})
        with self._load_store_returning({"X": []}):
            with self.assertRaises(regen.RegenerateError) as raised:
                regen._verify_bootstrap_catalog_agreement(catalog, rendered_catalog, self.repo / "issues", self.repo)
            self.assertEqual(raised.exception.code, "IR1030")
        # A view that correctly carries the SAME labels as canonical must not block.
        catalog2, rendered_catalog2 = self._basic_catalogs(view_extra={"labels": ["a"]}, list_extra={"labels": ["a"]})
        with self._load_store_returning({"X": ["a"]}):
            regen._verify_bootstrap_catalog_agreement(catalog2, rendered_catalog2, self.repo / "issues", self.repo)

    def test_canonical_absence_is_treated_as_empty_list(self):
        catalog, rendered_catalog = self._basic_catalogs()
        with mock.patch.object(regen.views, "load_store", return_value=([{"item": {"id": "X"}}], [], [])):
            regen._verify_bootstrap_catalog_agreement(catalog, rendered_catalog, self.repo / "issues", self.repo)

    def test_comparison_does_not_mutate_inputs(self):
        catalog, rendered_catalog = self._basic_catalogs()
        import copy
        before_catalog = copy.deepcopy(catalog)
        before_rendered = copy.deepcopy(rendered_catalog)
        with self._load_store_returning({"X": []}):
            regen._verify_bootstrap_catalog_agreement(catalog, rendered_catalog, self.repo / "issues", self.repo)
        self.assertEqual(catalog, before_catalog)
        self.assertEqual(rendered_catalog, before_rendered)


class BootstrapCatalogLabelOracleHelpers:
    """Independent oracle for DEC-0037-037, derived from the decision text
    (not from `_verify_bootstrap_catalog_agreement`'s own code path)."""

    @staticmethod
    def expected_outcome(canonical, observed_list_labels, view_has_labels, shared_state):
        if shared_state != "same":
            return "IR1030"
        if list(observed_list_labels) != list(canonical):
            return "IR1030"
        # view_has_labels is deliberately constructed to always mirror
        # canonical exactly (see the test's construction of view_item
        # below); its role in this oracle is only to prove presence of a
        # *correct* view-side labels array never blocks, independent of the
        # observed-vs-canonical mismatch already covered by the dimension
        # above. It never contributes an IR1030 outcome by itself.
        return "PASS"


class BootstrapCatalogLabelOracleTests(unittest.TestCase):
    def test_exhaustive_392_case_label_and_shared_field_oracle(self):
        """AE-5: 7 canonical-label arrays x 7 observed-label variants x 2
        view-label-presence states x 4 shared-field states = 392 real,
        independently-oracled, executed cases."""
        canonicals = [
            [], ["a"], ["a", "b"], ["b", "a"], ["a", "a"], ["a", "b", "c"], ["owner-tom"],
        ]

        def observed_variants(canonical):
            same = list(canonical)
            empty = []
            reordered = list(reversed(canonical)) if len(canonical) > 1 else list(canonical)
            missing_one = canonical[:-1] if canonical else []
            extra_one = canonical + ["extra"]
            duplicated = canonical + canonical[:1] if canonical else ["dup"]
            disjoint = ["zzz_different"]
            return [same, empty, reordered, missing_one, extra_one, duplicated, disjoint]

        view_states = (False, True)
        shared_states = ("same", "value_diff", "missing_key", "extra_key")

        case_count = 0
        for canonical in canonicals:
            with mock.patch.object(regen.views, "load_store", return_value=([{"item": {"id": "X", "labels": canonical}}], [], [])):
                for observed in observed_variants(canonical):
                    for view_has_labels in view_states:
                        for shared_state in shared_states:
                            case_count += 1
                            base_view = {"id": "X", "state": "open", "title": "T"}
                            base_list = dict(base_view)
                            if shared_state == "value_diff":
                                base_list["state"] = "closed"
                            elif shared_state == "missing_key":
                                del base_list["title"]
                            elif shared_state == "extra_key":
                                base_list["extra_field"] = "surprise"
                            view_item = dict(base_view)
                            if view_has_labels:
                                view_item["labels"] = list(canonical)
                            list_item = dict(base_list)
                            list_item["labels"] = list(observed)
                            catalog = {"items": [view_item]}
                            rendered_catalog = {"items": [list_item]}

                            expected = BootstrapCatalogLabelOracleHelpers.expected_outcome(
                                canonical, observed, view_has_labels, shared_state,
                            )
                            with self.subTest(canonical=canonical, observed=observed,
                                               view_has_labels=view_has_labels, shared_state=shared_state):
                                if expected == "IR1030":
                                    with self.assertRaises(regen.RegenerateError) as raised:
                                        regen._verify_bootstrap_catalog_agreement(
                                            catalog, rendered_catalog, Path("/nonexistent-unused"), Path("/nonexistent-unused"),
                                        )
                                    self.assertEqual(raised.exception.code, "IR1030")
                                else:
                                    regen._verify_bootstrap_catalog_agreement(
                                        catalog, rendered_catalog, Path("/nonexistent-unused"), Path("/nonexistent-unused"),
                                    )
        self.assertEqual(case_count, 392)


class RealFrozenBaselineBootstrapTests(unittest.TestCase):
    def test_frozen_real_551_item_baseline_labels_only_difference_progresses_to_real_ir1031(self):
        """Real (unmocked) views.render/lists.render_lists/_validate_payload
        against this worktree's actual frozen issues/ tree: the genuine,
        real, labels-only IR1030 difference no longer blocks, and execution
        correctly reaches the real (still-red) IR1031 canonical validation."""
        with self.assertRaises(regen.RegenerateError) as raised:
            regen.bootstrap_refresh(repo=ROOT, output_root=None, write=False)
        self.assertEqual(raised.exception.code, "IR1031")

    def test_frozen_real_241_multiset_equals_244_multiset_minus_exactly_three_iv0901(self):
        """Independently reproduces the DEC-0037-037 technical justification
        by content (multiset equality with multiplicity), not by trusting an
        externally-recorded, undocumented-serialization digest literal."""
        from dataclasses import asdict
        from collections import Counter

        diag_244, _ = regen.iv.validate(
            repo=ROOT, source="working-tree", root=ROOT / "issues",
            compare_head=False, provenance_root=ROOT / "provenance",
        )
        diag_241, _ = regen.iv.validate(
            repo=ROOT, source="working-tree", root=ROOT / "issues",
            compare_head=False, provenance_root=None,
        )
        self.assertEqual(len(diag_244), 244)
        self.assertEqual(len(diag_241), 241)

        def key(d):
            return json.dumps(asdict(d), sort_keys=True)

        d244 = [asdict(d) for d in diag_244]
        iv0901 = [d for d in d244 if d["rule"] == "IV0901"]
        self.assertEqual(len(iv0901), 3)

        c244 = Counter(json.dumps(d, sort_keys=True) for d in d244)
        c_iv0901 = Counter(json.dumps(d, sort_keys=True) for d in iv0901)
        c241 = Counter(key(d) for d in diag_241)

        expected_241 = c244.copy()
        expected_241.subtract(c_iv0901)
        expected_241 = +expected_241  # drop zero/negative counts
        self.assertEqual(expected_241, c241)


class AuthorityMatrixTests(RegenerationFixture):
    def test_phase_and_inside_outside_root_matrix(self):
        """AE root matrix: 3 phases × 3 safe/unsafe target classes = 27 checks."""
        phases = (
            ("legacy-lists", "legacy-writable"),
            ("issue-store", "issue-store-frozen"),
            ("issue-store", "issue-store-writable"),
        )
        allowed = (
            self.repo / "generated-shadow",
            self.repo / "check-issues",
            self.base / "generated-external",
        )
        rejected = (
            self.repo / "unsafe",
            self.repo / "ordinary" / "generated-shadow",
            self.base / "ordinary-existing",
            self.repo,
            self.repo.parent,
            Path.home(),
        )
        (self.base / "ordinary-existing").mkdir()
        for profile, phase in phases:
            self._selector(profile, phase)
            selector = regen.load_selector(self.repo)
            for target in allowed:
                with self.subTest(profile=profile, phase=phase, target=target):
                    self.assertEqual(regen.authorize_output_root(self.repo, target, selector), target.resolve())
            for target in rejected:
                with self.subTest(profile=profile, phase=phase, target=target):
                    with self.assertRaises(regen.RegenerateError):
                        regen.authorize_output_root(self.repo, target, selector)

    def test_authority_alias_and_symlink_roots_rejected(self):
        selector = regen.load_selector(self.repo)
        aliases = (
            self.repo / "generated-shadow" / "..",
            Path("/private/tmp") / "ordinary" / ".." / "generated-alias",
            self.repo / "issues" / "generated-shadow",
            self.repo / "docs" / "pipeline" / "generated-shadow",
            self.repo / "generated-shadow" / "TODO.md",
        )
        for target in aliases:
            with self.subTest(target=target):
                with self.assertRaises(regen.RegenerateError):
                    regen.authorize_output_root(self.repo, target, selector)
        link = self.base / "generated-link"
        link.symlink_to(self.repo / "generated-shadow", target_is_directory=True)
        with self.assertRaises(regen.RegenerateError) as raised:
            regen.authorize_output_root(self.repo, link, selector)
        self.assertEqual(raised.exception.code, "IR1005")


class ManifestContainmentTests(RegenerationFixture):
    def test_invalid_output_and_derived_paths_create_no_bytes(self):
        """AE containment matrix: 15 invalid spellings fail before staging/lock."""
        invalid = ("", "/abs", "C:/drive", ".", "..", "a/../b", "a/./b", "a//b", "a/", " a", "a ", "a\\b", "C:\\drive", "a\x00b", "//host/share")
        before = set(self.base.rglob("*"))
        for value in invalid:
            for field in ("output", "derived"):
                manifest = _manifest()
                if field == "output":
                    manifest["stages"][0]["outputs"] = [value]
                else:
                    produced = manifest["stages"][0]["outputs"][0]
                    manifest["stages"][1]["inputs"] = [{"kind": "derived", "glob": value}]
                    if value == produced:
                        continue
                self.dag.write_text(regen.canonical_json(manifest), encoding="utf-8")
                with self.subTest(value=repr(value), field=field):
                    with self.assertRaises(regen.RegenerateError):
                        self.execute(write=True)
                    self.assertFalse(self.target.exists())
                    self.assertFalse((self.base / ".generated-shadow.issue-regeneration.lock").exists())
        after = set(self.base.rglob("*"))
        self.assertEqual(after, before)

    def test_symlinked_output_parent_cannot_create_outside_bytes(self):
        staging = self.base / "staging"
        outside = self.base / "outside"
        staging.mkdir()
        outside.mkdir()
        (staging / "generated").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(regen.RegenerateError) as raised:
            regen._write(staging, "generated/escape.json", b"{}\n")
        self.assertEqual(raised.exception.code, "IR1019")
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_derived_input_is_rejected_without_reading_alias(self):
        staging = self.base / "derived-staging"
        outside = self.base / "derived-outside"
        staging.mkdir()
        outside.mkdir()
        (outside / "catalog.json").write_text("{}\n", encoding="utf-8")
        (staging / "data").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(regen.RegenerateError) as raised:
            regen.derived_input_under(staging, "data/catalog.json")
        self.assertEqual(raised.exception.code, "IR1019")


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
