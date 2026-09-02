#!/usr/bin/env python3
"""Tests for Task 0037-14 issue_import_legacy."""
from __future__ import annotations

import importlib.util
import itertools
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "issue_import_legacy",
    Path(os.environ.get("ISSUE_IMPORT_LEGACY_TOOL", ROOT / "_src/tools/issue_import_legacy.py")),
)
IMP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMP)
FIXTURE_13 = ROOT / "provenance/migrations/issue-store/fixtures/0037-13"


def assert_closed_schema_shape(test, value, schema, root_schema):
    if "$ref" in schema:
        target = root_schema
        for component in schema["$ref"].removeprefix("#/").split("/"):
            target = target[component]
        return assert_closed_schema_shape(test, value, target, root_schema)
    if schema.get("type") == "object":
        test.assertIsInstance(value, dict)
        test.assertTrue(set(schema.get("required", ())).issubset(value))
        if schema.get("additionalProperties") is False:
            test.assertFalse(set(value) - set(schema.get("properties", {})))
        for key, child in schema.get("properties", {}).items():
            if key in value:
                assert_closed_schema_shape(test, value[key], child, root_schema)
    elif schema.get("type") == "array":
        test.assertIsInstance(value, list)
        for item in value:
            assert_closed_schema_shape(test, item, schema.get("items", {}), root_schema)


class ImportLegacyTests(unittest.TestCase):
    maxDiff = None

    def _import_fixture(self, dest: Path):
        return IMP.import_legacy(repo=ROOT, root=dest, source_tree=FIXTURE_13)

    def _commit(self, repo: Path, message: str) -> str:
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True)
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()

    def _production_repo(self, parent: Path, *, placeholder: bool = False):
        repo = parent / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Importer Test"], cwd=repo, check=True)
        inventory = repo / "provenance/migrations/issue-store/tools"
        inventory.mkdir(parents=True)
        shutil.copy(
            ROOT / "provenance/migrations/issue-store/tools/issue_legacy_inventory.py",
            inventory / "issue_legacy_inventory.py",
        )
        tools = repo / "_src/tools"
        tools.mkdir(parents=True)
        shutil.copy(ROOT / "_src/tools/issue_import_legacy.py", tools / "issue_import_legacy.py")
        schemas = repo / "issues/_schema"
        schemas.mkdir(parents=True)
        for name in (
            "issue-item-v1.schema.json",
            "issue-closure-v1.schema.json",
            "migration-state-v1.schema.json",
        ):
            shutil.copy(ROOT / "issues/_schema" / name, schemas / name)
        (repo / "TODO.md").write_text(
            "## Feature: 0099 — Import\n\n- [ ] **0099-00** Seed.\n"
            "  - **Acceptance criteria:** Seed.\n  - **Definition of Done:** Seeded.\n",
            encoding="utf-8",
        )
        (repo / "DONE.md").write_text("# DONE\n", encoding="utf-8")
        evidence = self._commit(repo, "evidence")
        ref = "pending" if placeholder else evidence
        (repo / "TODO.md").write_text(
            "## Feature: 0099 — Import\n\n"
            "- [x] **0099-01** Completed import target.\n"
            "  - **Acceptance criteria:** First requirement; second requirement.\n"
            "  - **Definition of Done:** Complete.\n"
            "  - **Acceptance:** ✓\n"
            "    - **Disposition:** `completed`\n"
            "    - **Accepted by:** `reviewer:test`\n"
            "    - **Accepted at:** `2026-09-02T10:00:00Z`\n"
            f"    - **Carrying commit:** `{ref}`\n"
            "- [w] **0099-02** Wontfix import target.\n"
            "  - **Acceptance criteria:** Investigate.\n"
            "  - **Definition of Done:** Disposition recorded.\n"
            "  - **Reason:** Non-reproducible under the retained probe.\n"
            "  - **Acceptance:** ✓\n"
            "    - **Disposition:** `wontfix`\n"
            "    - **Accepted by:** `reviewer:test`\n"
            "    - **Accepted at:** `2026-09-02T10:01:00Z`\n"
            f"    - **Carrying commit:** `{ref}`\n",
            encoding="utf-8",
        )
        source = self._commit(repo, "terminal source")
        return repo, source, evidence

    def _run(self, repo: Path, history: Path, run_id: str, source: str, **kwargs):
        return IMP.run_migration(
            repo=repo,
            history_root=history,
            run_id=run_id,
            source_revision=source,
            source_ref=kwargs.pop("source_ref", source),
            baseline_commit=kwargs.pop("baseline_commit", source),
            **kwargs,
        )

    def test_repeated_imports_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a"
            b = Path(tmp) / "b"
            first = self._import_fixture(a)
            second = self._import_fixture(b)
            self.assertEqual(first["tree_digest"], second["tree_digest"])
            written = first["written"]
            self.assertTrue(written)
            for rel in written:
                self.assertEqual((a / rel).read_bytes(), (b / rel).read_bytes())
            self.assertEqual((a / "import-findings.json").read_bytes(), (b / "import-findings.json").read_bytes())
            # Manifest includes absolute disposable_root; compare minus that field.
            ma = json.loads((a / "import-manifest.json").read_text(encoding="utf-8"))
            mb = json.loads((b / "import-manifest.json").read_text(encoding="utf-8"))
            ma.pop("disposable_root")
            mb.pop("disposable_root")
            self.assertEqual(ma, mb)

    def test_ac_ids_by_document_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "root"
            tree = Path(tmp) / "src"
            tree.mkdir()
            (tree / "TODO.md").write_text(
                "# t\n\n## Feature: 0099 — Order\n\n"
                "- [ ] **0099-01** Example legacy task.\n"
                "  - **Acceptance criteria:** First stated requirement; second stated requirement; third\n"
                "    stated requirement.\n"
                "  - **Definition of Done:** Done.\n",
                encoding="utf-8",
            )
            (tree / "DONE.md").write_text("# empty\n", encoding="utf-8")
            IMP.import_legacy(repo=ROOT, root=dest, source_tree=tree)
            body = (dest / "issues/0099/0099-01/index.md").read_text(encoding="utf-8")
            self.assertIn("- **AC-001** First stated requirement", body)
            self.assertIn("- **AC-002** second stated requirement", body)
            self.assertIn("- **AC-003** third stated requirement", body)

    def test_states_refs_and_0021(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "root"
            manifest = self._import_fixture(dest)
            by_id = {i["id"]: i for i in manifest["items"]}
            self.assertEqual(by_id["0037-06"]["state"], "closed")
            self.assertEqual(by_id["0037-13"]["state"], "in_progress")
            self.assertEqual(by_id["0037"]["state"], "open")
            self.assertEqual(by_id["0021"]["state"], "closed")
            text_0021 = (dest / "issues/0021/index.md").read_text(encoding="utf-8")
            self.assertIn("archived-not-accepted", text_0021)
            rules = {f["rule"] for f in manifest["findings"]}
            self.assertIn("IMP-REF-NO-EVIDENCE-CREDIT", rules)
            self.assertIn("IMP-ID-DUPLICATE", rules)
            self.assertIn("IMP-MARKER-UNDEFINED", rules)
            self.assertIn("IMP-TASK-HEADER-MALFORMED", rules)
            self.assertIn("IMP-REF-PENDING", rules)
            placeholder_findings = [
                finding
                for finding in manifest["findings"]
                if finding["rule"] in {"IMP-REF-PENDING", "IMP-REF-LOCAL-PLACEHOLDER"}
            ]
            self.assertTrue(placeholder_findings)
            self.assertTrue(all(finding["severity"] == "blocking" for finding in placeholder_findings))
            self.assertFalse(manifest["claim_json_emitted"])
            self.assertFalse(manifest["closure_json_emitted"])
            self.assertTrue(any(p.startswith("legacy-claims/") for p in manifest["written"]))
            self.assertFalse(list(dest.rglob("claim.json")))
            self.assertFalse(list(dest.rglob("closure.json")))

    def test_refuse_live_roots(self):
        with self.assertRaises(IMP.ImportErrorClosed) as ctx:
            IMP.resolve_disposable_root(ROOT / "issues", ROOT)
        self.assertEqual(ctx.exception.code, "IMP-LIVE-ROOT")
        with self.assertRaises(IMP.ImportErrorClosed):
            IMP.resolve_disposable_root(ROOT / "provenance", ROOT)
        with self.assertRaises(IMP.ImportErrorClosed):
            IMP.resolve_disposable_root(ROOT, ROOT)

    def test_path_confusion_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "root"
            dest.mkdir()
            outside = Path(tmp) / "outside"
            outside.mkdir()
            (outside / "secret").write_text("nope\n", encoding="utf-8")
            trap = dest / "issues"
            trap.symlink_to(outside)
            with self.assertRaises(IMP.ImportErrorClosed):
                IMP.atomic_write(dest / "issues" / "0037" / "index.md", b"x\n", dest.resolve())

    def test_malformed_fixture_does_not_write_bad_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "root"
            manifest = self._import_fixture(dest)
            ids = {i["id"] for i in manifest["items"]}
            self.assertNotIn("not-an-id", ids)
            self.assertTrue(manifest["blocking"])

    def test_git_commit_source_and_named_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
            (repo / "TODO.md").write_text(
                "## Feature: 0001 — One\n\n- [ ] **0001-01** Task.\n  - **Acceptance criteria:** A.\n",
                encoding="utf-8",
            )
            (repo / "DONE.md").write_text("# none\n", encoding="utf-8")
            (repo / "TODO-agent.md").write_text("- item: 0001-01\n- owner_token: agent:x:0001-01:1\n", encoding="utf-8")
            # copy inventory tool so importer can load it
            dest_tool = repo / "provenance/migrations/issue-store/tools"
            dest_tool.mkdir(parents=True)
            shutil.copy(
                ROOT / "provenance/migrations/issue-store/tools/issue_legacy_inventory.py",
                dest_tool / "issue_legacy_inventory.py",
            )
            (repo / "_src/tools").mkdir(parents=True)
            shutil.copy(ROOT / "_src/tools/issue_import_legacy.py", repo / "_src/tools/issue_import_legacy.py")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "src"], cwd=repo, check=True, capture_output=True)
            sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
            out = Path(tmp) / "out"
            manifest = IMP.import_legacy(
                repo=repo,
                root=out,
                source_commit=sha,
                named_files=["TODO.md", "DONE.md", "TODO-agent.md"],
            )
            self.assertIn("issues/0001/0001-01/index.md", manifest["written"])
            self.assertEqual(manifest["source_commit"], sha)

    def test_mutation_guard_all_writes_under_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "root"
            manifest = self._import_fixture(dest)
            root = dest.resolve()
            for rel in manifest["written"] + ["import-manifest.json", "import-findings.json"]:
                path = (dest / rel).resolve()
                path.relative_to(root)

    def test_production_contract_falsification_success_and_closures(self):
        """AE-3 falsification: baseline lacks run_migration; candidate promotes evidence-complete x/w."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, evidence = self._production_repo(Path(tmp))
            history = Path(tmp) / "history"
            result = self._run(repo, history, "shadow-success-0001", source)
            state = result["state"]
            self.assertEqual(state["status"], "promoted")
            self.assertEqual(state["counts"]["closures"], 2)
            completed = json.loads(
                (history / "shadow-success-0001/issues/issues/0099/0099-01/closure.json").read_text()
            )
            wontfix = json.loads(
                (history / "shadow-success-0001/issues/issues/0099/0099-02/closure.json").read_text()
            )
            self.assertEqual(completed["disposition"], "completed")
            self.assertEqual(wontfix["disposition"], "wontfix")
            self.assertEqual(completed["commit_refs"], [evidence])
            self.assertEqual(wontfix["reason"], "Non-reproducible under the retained probe.")
            state_schema = json.loads(
                (repo / "issues/_schema/migration-state-v1.schema.json").read_text()
            )
            assert_closed_schema_shape(self, state, state_schema, state_schema)
            closure_schema = json.loads(
                (repo / "issues/_schema/issue-closure-v1.schema.json").read_text()
            )
            assert_closed_schema_shape(self, completed, closure_schema, closure_schema)
            assert_closed_schema_shape(self, wontfix, closure_schema, closure_schema)

    def test_production_cli_mode_writes_immutable_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp))
            history = Path(tmp) / "history"
            result = subprocess.run(
                [
                    "python3",
                    str(repo / "_src/tools/issue_import_legacy.py"),
                    "--repo",
                    str(repo),
                    "--root",
                    str(history),
                    "--run-id",
                    "shadow-cli-success-0001",
                    "--source-commit",
                    source,
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "promoted")
            self.assertTrue(
                (history / "shadow-cli-success-0001/reports/migration-report.json").is_file()
            )

    def test_adjacent_missing_placeholder_evidence_is_retained_rejection(self):
        """AE-4 adjacent evidence dimension: placeholder vs reachable ref => rejected, no closure."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp), placeholder=True)
            history = Path(tmp) / "history"
            result = self._run(repo, history, "shadow-placeholder-0001", source)
            self.assertEqual(result["state"]["status"], "rejected")
            rules = {finding["rule"] for finding in result["report"]["findings"]}
            self.assertIn("IMP-CLOSURE-EVIDENCE-PLACEHOLDER", rules)
            self.assertFalse(list((history / "shadow-placeholder-0001/issues").rglob("closure.json")))

    def test_adjacent_stale_source_is_retained_and_not_promotable(self):
        """AE-4 adjacent identity dimension: watched ref drift => retained rejected state."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp))
            history = Path(tmp) / "history"

            def advance_source(_staging):
                with (repo / "TODO.md").open("a", encoding="utf-8") as stream:
                    stream.write("\n- [ ] **0099-03** Later source item.\n")
                self._commit(repo, "advance source")

            result = self._run(
                repo,
                history,
                "shadow-stale-source-0001",
                source,
                source_ref="main",
                before_compare=advance_source,
            )
            self.assertEqual(result["state"]["status"], "rejected")
            self.assertFalse(result["state"]["candidate"]["promotable"])
            self.assertTrue((history / "shadow-stale-source-0001/reports/migration-state.json").is_file())
            self.assertIn("stale-candidate", {f["code"] for f in result["state"]["findings"]})

    def test_candidate_and_schema_drift_are_compare_and_swap_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp))
            history = Path(tmp) / "history"

            def mutate_candidate(staging):
                target = staging / "issues/issues/0099/0099-01/index.md"
                target.write_text(target.read_text() + "drift\n", encoding="utf-8")

            candidate = self._run(
                repo,
                history,
                "shadow-candidate-drift-0001",
                source,
                before_compare=mutate_candidate,
            )
            self.assertEqual(candidate["state"]["status"], "rejected")
            self.assertIn("candidate-drift", {f["code"] for f in candidate["state"]["findings"]})

            def mutate_schema(_staging):
                schema = repo / "issues/_schema/issue-item-v1.schema.json"
                schema.write_text(schema.read_text() + "\n", encoding="utf-8")

            schema = self._run(
                repo,
                history,
                "shadow-schema-drift-0001",
                source,
                before_compare=mutate_schema,
            )
            self.assertEqual(schema["state"]["status"], "rejected")
            self.assertIn("importer-identity-drift", {f["code"] for f in schema["state"]["findings"]})

    def test_increasing_watermarks_and_tool_rerun_are_separately_addressable(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, first_source, _ = self._production_repo(Path(tmp))
            history = Path(tmp) / "history"
            first = self._run(repo, history, "shadow-watermark-0001", first_source)
            with (repo / "TODO.md").open("a", encoding="utf-8") as stream:
                stream.write("\n- [ ] **0099-03** Increasing watermark.\n")
            second_source = self._commit(repo, "new legacy watermark")
            second = self._run(
                repo,
                history,
                "shadow-watermark-0002",
                second_source,
                baseline_commit=first_source,
            )
            tool = repo / "_src/tools/issue_import_legacy.py"
            tool.write_text(tool.read_text() + "\n# identity rerun\n", encoding="utf-8")
            self._commit(repo, "tool identity rerun")
            third = self._run(
                repo,
                history,
                "shadow-tool-rerun-0003",
                second_source,
                baseline_commit=first_source,
            )
            self.assertEqual(first["state"]["history"]["sequence"], 1)
            self.assertEqual(second["state"]["history"]["sequence"], 2)
            self.assertEqual(third["state"]["history"]["sequence"], 3)
            self.assertEqual(third["state"]["source"]["commit"], second_source)
            self.assertNotEqual(
                second["state"]["importer"]["digest"], third["state"]["importer"]["digest"]
            )
            for run_id in ("shadow-watermark-0001", "shadow-watermark-0002", "shadow-tool-rerun-0003"):
                self.assertTrue((history / run_id / "reports/migration-state.json").is_file())

    def test_atomic_failure_leaves_no_partial_final_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp))
            history = Path(tmp) / "history"
            with mock.patch.object(IMP, "import_legacy", side_effect=RuntimeError("injected")):
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    self._run(repo, history, "shadow-atomic-fail-0001", source)
            self.assertFalse((history / "shadow-atomic-fail-0001").exists())
            self.assertFalse(list(history.glob(".shadow-atomic-fail-0001.staging-*")))
            self.assertFalse((history / ".shadow-atomic-fail-0001.lock").exists())

    def test_deterministic_production_rerun_and_path_containment(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp))
            first = self._run(repo, Path(tmp) / "history-a", "shadow-deterministic-0001", source)
            second = self._run(repo, Path(tmp) / "history-b", "shadow-deterministic-0001", source)
            self.assertEqual(first["state"], second["state"])
            self.assertEqual(first["report"], second["report"])
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                self._run(repo, repo / "issues", "shadow-path-escape-0001", source)
            self.assertEqual(ctx.exception.code, "IMP-LIVE-ROOT")

    def test_property_candidate_digest_set_and_sequence_invariant_24_cases(self):
        """AE-5: exhaustive 4-path permutations; oracle is order-invariant exact membership digest."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = ["a", "b", "c", "d"]
            for path in paths:
                (root / path).write_text(path, encoding="utf-8")
            oracle = IMP._candidate_digest(root, paths)
            cases = 0
            for permutation in itertools.permutations(paths):
                self.assertEqual(IMP._candidate_digest(root, permutation), oracle)
                cases += 1
            self.assertEqual(cases, 24)
            (root / "e").write_text("e", encoding="utf-8")
            self.assertNotEqual(IMP._candidate_digest(root, paths + ["e"]), oracle)


if __name__ == "__main__":
    unittest.main()
