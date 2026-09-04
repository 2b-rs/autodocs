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
AUTHORITY_COMMIT = "89470b3b2aa804786eb525a9682410c783b77453"
AUTHORITY_PATH = "docs/dossiers/dec-0037-007-legacy-migration-dispositions.md"
AUTHORITY_BLOB_DIGEST = "sha256:54e5eeeaeea38620192dc0049a5f89fa71538fd159ec46009e7fd302ece633ee"
AUTHORITY_PRINCIPAL = "obrien@deepspace9.starfleet.network"


def _authority_material():
    return {
        "scheme": "git-ssh-commit-v1",
        "commit": AUTHORITY_COMMIT,
        "path": AUTHORITY_PATH,
        "blob_digest": AUTHORITY_BLOB_DIGEST,
        "principal": AUTHORITY_PRINCIPAL,
    }


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
            "migration-dispositions-v1.schema.json",
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
            f"    - **Criterion evidence AC-001:** `commit:{ref}`\n"
            f"    - **Criterion evidence AC-002:** `commit:{ref}`\n"
            "- [w] **0099-02** Wontfix import target.\n"
            "  - **Acceptance criteria:** Investigate.\n"
            "  - **Definition of Done:** Disposition recorded.\n"
            "  - **Reason:** Non-reproducible under the retained probe.\n"
            "  - **Acceptance:** ✓\n"
            "    - **Disposition:** `wontfix`\n"
            "    - **Accepted by:** `reviewer:test`\n"
            "    - **Accepted at:** `2026-09-02T10:01:00Z`\n"
            f"    - **Carrying commit:** `{ref}`\n"
            f"    - **Criterion evidence AC-001:** `commit:{ref}`\n",
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

    def test_missing_criterion_bound_evidence_blocks_closure(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp))
            todo = repo / "TODO.md"
            todo.write_text(
                "\n".join(
                    line for line in todo.read_text(encoding="utf-8").splitlines()
                    if "Criterion evidence" not in line
                ) + "\n",
                encoding="utf-8",
            )
            source = self._commit(repo, "remove criterion evidence")
            result = self._run(
                repo, Path(tmp) / "history", "shadow-no-criterion-evidence-0001", source
            )
            self.assertEqual(result["state"]["status"], "rejected")
            self.assertIn(
                "IMP-CLOSURE-CRITERION-EVIDENCE-MISSING",
                {finding["rule"] for finding in result["report"]["findings"]},
            )
            self.assertEqual(result["state"]["counts"]["closures"], 0)

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

    def _production_dispositions(self, repo: Path, source: str, parent: Path):
        probe = IMP.import_legacy(
            repo=repo, root=parent / "probe", source_commit=source, emit_closures=True,
        )
        _, blobs = IMP._source_identity(repo, source, None)
        entries = [
            _entry_for(finding, blobs, source)
            for finding in probe["findings"]
            if finding["severity"] == "blocking"
        ]
        for key in ("user.signingkey", "gpg.format", "gpg.ssh.allowedSignersFile"):
            value = subprocess.check_output(
                ["git", "config", "--get", key], cwd=ROOT, text=True,
            ).strip()
            if key == "gpg.ssh.allowedSignersFile":
                value = str((ROOT / value).resolve())
            subprocess.run(["git", "config", key, value], cwd=repo, check=True)
        subprocess.run(["git", "config", "commit.gpgsign", "true"], cwd=repo, check=True)
        _bind_authority(repo, entries)
        path = repo / "authority/production-dispositions.json"
        path.write_text(
            IMP._canonical_json({"schema": IMP.DISPOSITION_SCHEMA, "entries": entries}),
            encoding="utf-8",
        )
        return path, entries

    def test_production_dispositions_cover_and_promote_without_credit(self):
        """AE-3: production omits dispositions on the baseline and promotes with exact coverage."""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            repo, source, _ = self._production_repo(parent, placeholder=True)
            path, entries = self._production_dispositions(repo, source, parent)
            history = repo / "_src/output/issue-migration"
            result = self._run(
                repo, history, "shadow-dispositions-green-0001", source,
                dispositions=path,
            )
            self.assertEqual(result["state"]["status"], "promoted")
            self.assertEqual(result["state"]["finding_summary"]["blocking"], 0)
            coverage = result["report"]["disposition_coverage"]
            self.assertEqual(len(coverage["pairs"]), len(entries))
            self.assertFalse(coverage["credit_granted"])
            self.assertFalse(coverage["closure_json_synthesized"])
            self.assertFalse(list((history / "shadow-dispositions-green-0001").rglob("closure.json")))
            self.assertIn("disposition-coverage", {finding["code"] for finding in result["state"]["findings"]})

    def test_adjacent_production_disposition_drift_is_retained_rejection(self):
        """AE-4 identity neighbor: a byte change after preflight fails the disposition CAS."""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            repo, source, _ = self._production_repo(parent, placeholder=True)
            path, _ = self._production_dispositions(repo, source, parent)

            def drift(_staging):
                path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

            result = self._run(
                repo, repo / "_src/output/issue-migration",
                "shadow-dispositions-drift-0001", source,
                dispositions=path, before_compare=drift,
            )
            self.assertEqual(result["state"]["status"], "rejected")
            self.assertIn(
                "IMP-DISPOSITION-DRIFT",
                {finding["rule"] for finding in result["report"]["findings"]},
            )

    def test_adjacent_production_disposition_symlink_alias_is_rejected(self):
        """AE-4 path neighbor: repository aliases cannot select production authority input."""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            repo, source, _ = self._production_repo(parent, placeholder=True)
            path, _ = self._production_dispositions(repo, source, parent)
            alias = repo / "authority/alias.json"
            alias.symlink_to(path.name)
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                self._run(
                    repo, repo / "_src/output/issue-migration",
                    "shadow-dispositions-alias-0001", source, dispositions=alias,
                )
            self.assertEqual(ctx.exception.code, "IMP-DISPOSITION-PATH")

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

    def test_dirty_source_drift_staged_unstaged_and_untracked_is_retained(self):
        for mode in ("unstaged", "staged", "untracked"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                repo, source, _ = self._production_repo(Path(tmp))
                history = Path(tmp) / "history"

                def dirty_source(_staging):
                    if mode == "untracked":
                        (repo / "TODO-new-claim.md").write_text("untracked\n", encoding="utf-8")
                    else:
                        with (repo / "TODO.md").open("a", encoding="utf-8") as stream:
                            stream.write("\npost-preparation drift\n")
                        if mode == "staged":
                            subprocess.run(["git", "add", "TODO.md"], cwd=repo, check=True)

                result = self._run(
                    repo, history, f"shadow-dirty-{mode}-0001", source,
                    before_compare=dirty_source,
                )
                self.assertEqual(result["state"]["status"], "rejected")
                self.assertIn(
                    "IMP-DIRTY-LEGACY-SOURCE-DRIFT",
                    {finding["rule"] for finding in result["report"]["findings"]},
                )
                self.assertFalse(result["state"]["source"]["working_tree_clean"])

    def test_report_write_drift_is_caught_by_immediate_pre_promotion_cas(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp))
            history = Path(tmp) / "history"
            real_atomic_write = IMP.atomic_write
            report_writes = 0

            def drift_after_report_write(path, data, root):
                nonlocal report_writes
                real_atomic_write(path, data, root)
                if path.name in {"migration-state.json", "migration-report.json"}:
                    report_writes += 1
                    if report_writes == 2:
                        with (repo / "TODO.md").open("a", encoding="utf-8") as stream:
                            stream.write("\nlate report-write drift\n")

            with mock.patch.object(IMP, "atomic_write", side_effect=drift_after_report_write):
                result = self._run(repo, history, "shadow-late-cas-drift-0001", source)
            self.assertEqual(result["state"]["status"], "rejected")
            self.assertIn(
                "IMP-DIRTY-LEGACY-SOURCE-DRIFT",
                {finding["rule"] for finding in result["report"]["findings"]},
            )
            self.assertFalse(result["state"]["candidate"]["promotable"])

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

    def test_post_reservation_failure_retains_interrupted_state_without_partial_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp))
            history = Path(tmp) / "history"
            with mock.patch.object(IMP, "import_legacy", side_effect=RuntimeError("injected")):
                result = self._run(repo, history, "shadow-atomic-fail-0001", source)
            run = history / "shadow-atomic-fail-0001"
            self.assertEqual(result["state"]["status"], "interrupted")
            self.assertTrue((run / "reports/migration-state.json").is_file())
            self.assertFalse((run / "issues").exists())
            self.assertFalse(list(history.glob(".shadow-atomic-fail-0001.staging-*")))
            self.assertFalse((history / ".shadow-atomic-fail-0001.lock").exists())

    def test_candidate_disappearance_retains_interrupted_report_only_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp))
            history = Path(tmp) / "history"

            def remove_candidate(staging):
                (staging / "issues/issues/0099/0099-01/index.md").unlink()

            result = self._run(
                repo, history, "shadow-candidate-missing-0001", source,
                before_compare=remove_candidate,
            )
            run = history / "shadow-candidate-missing-0001"
            self.assertEqual(result["state"]["status"], "interrupted")
            self.assertIn("candidate-drift", {f["code"] for f in result["state"]["findings"]})
            self.assertFalse((run / "issues").exists())
            self.assertTrue((run / "reports/migration-report.json").is_file())

    def test_mixed_acceptance_history_excludes_noncurrent_base_and_unrelated_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, evidence = self._production_repo(Path(tmp))
            (repo / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
            unrelated = self._commit(repo, "unrelated reachable commit")
            block = (
                "- [x] **0099-01** Mixed history.\n"
                "  - **Acceptance criteria:** Bound criterion.\n"
                "  - **Acceptance:** rejected\n"
                f"    - **Review REF:** `{unrelated}`\n"
                "  - **Acceptance:** ✓\n"
                "    - **Disposition:** `completed`\n"
                "    - **Accepted by:** `reviewer:test`\n"
                "    - **Accepted at:** `2026-09-02T10:00:00Z`\n"
                f"    - **Base-Ref:** `{source}`\n"
                f"    - **Rejected commit:** `{unrelated}`\n"
                f"    - **Carrying commit:** `{evidence}`\n"
                f"    - **Criterion evidence AC-001:** `commit:{evidence}`\n"
            )
            findings = []
            closure = IMP.closure_from_legacy(
                repo=repo, source_commit=unrelated,
                item={"id": "0099-01", "marker": "x"}, block=block,
                criteria_count=1, findings=findings, locator="TODO.md:1",
            )
            self.assertEqual(closure["commit_refs"], [evidence])
            self.assertEqual(closure["criteria"][0]["evidence"], [f"commit:{evidence}"])
            self.assertNotIn(source, closure["commit_refs"])
            self.assertNotIn(unrelated, closure["commit_refs"])

            noncurrent = block + "  - **Acceptance:** inconclusive\n"
            findings = []
            self.assertIsNone(
                IMP.closure_from_legacy(
                    repo=repo, source_commit=unrelated,
                    item={"id": "0099-01", "marker": "x"}, block=noncurrent,
                    criteria_count=1, findings=findings, locator="TODO.md:1",
                )
            )
            self.assertIn("IMP-CLOSURE-ACCEPTANCE-MISSING", {f["rule"] for f in findings})

    def test_deterministic_production_rerun_and_path_containment(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp))
            first = self._run(repo, Path(tmp) / "history-a", "shadow-deterministic-0001", source)
            second = self._run(repo, Path(tmp) / "history-b", "shadow-deterministic-0001", source)
            self.assertEqual(first["state"], second["state"])
            self.assertEqual(first["report"], second["report"])
            canonical = repo / "_src/output/issue-migration"
            self.assertEqual(IMP._history_root(canonical, repo), canonical.resolve())
            repo_alias = Path(tmp) / "repo-alias"
            repo_alias.symlink_to(repo, target_is_directory=True)
            alias_canonical = repo_alias / "_src/output/issue-migration"
            rejected_alias = _live_root_alias_importer()
            with self.assertRaises(rejected_alias.ImportErrorClosed) as red:
                rejected_alias._history_root(alias_canonical, repo_alias)
            self.assertEqual(red.exception.code, "IMP-LIVE-ROOT")
            self.assertEqual(IMP._history_root(alias_canonical, repo_alias), canonical.resolve())
            outside = Path(tmp) / "outside-history"
            self.assertEqual(IMP._history_root(outside, repo), outside.resolve())
            forbidden = [
                repo,
                repo / "docs",
                repo / "_src/tools",
                repo / "issues",
                repo / "provenance",
                repo / ".runner",
            ]
            for index, root in enumerate(forbidden):
                with self.subTest(root=root), self.assertRaises(IMP.ImportErrorClosed) as ctx:
                    IMP._history_root(root, repo)
                self.assertEqual(ctx.exception.code, "IMP-LIVE-ROOT")
            canonical.mkdir(parents=True)
            alias = repo / "migration-alias"
            alias.symlink_to(canonical, target_is_directory=True)
            with self.assertRaises(IMP.ImportErrorClosed) as internal_alias:
                IMP._history_root(alias, repo)
            self.assertEqual(internal_alias.exception.code, "IMP-LIVE-ROOT")
            outside_alias = Path(tmp) / "outside-alias"
            outside_alias.symlink_to(canonical, target_is_directory=True)
            with self.assertRaises(IMP.ImportErrorClosed) as external_alias:
                IMP._history_root(outside_alias, repo)
            self.assertEqual(external_alias.exception.code, "IMP-LIVE-ROOT")
            outside.mkdir()
            safe_outside_alias = Path(tmp) / "safe-outside-alias"
            safe_outside_alias.symlink_to(outside, target_is_directory=True)
            self.assertEqual(IMP._history_root(safe_outside_alias, repo), outside.resolve())

    def test_reserved_canonical_staging_capability_is_conjunctive(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            history = repo / "_src/output/issue-migration"
            history.mkdir(parents=True)
            history = history.resolve()
            run_id = "0037-31-post-delta-7dbc94db-r2"
            lock = history / f".{run_id}.lock"
            lock.write_text("", encoding="utf-8")
            staging = Path(tempfile.mkdtemp(prefix=f".{run_id}.staging-", dir=history)).resolve()
            issues = staging / "issues"
            capability = IMP._ReservedStagingCapability(
                repo.resolve(), history, staging, issues, lock, run_id
            )
            self.assertEqual(
                issues.resolve(),
                IMP.resolve_disposable_root(issues, repo, _reserved_staging=capability),
            )
            mutations = (
                capability._replace(repo=Path(tmp)),
                capability._replace(history=repo / "_src/output"),
                capability._replace(staging=history / "sibling"),
                capability._replace(issues=staging / "reports"),
                capability._replace(lock=history / ".wrong.lock"),
                capability._replace(run_id="wrong-run-id"),
            )
            for mutated in mutations:
                with self.subTest(mutated=mutated), self.assertRaises(IMP.ImportErrorClosed) as ctx:
                    IMP.resolve_disposable_root(issues, repo, _reserved_staging=mutated)
                self.assertEqual("IMP-LIVE-ROOT", ctx.exception.code)
            with self.assertRaises(IMP.ImportErrorClosed):
                IMP.resolve_disposable_root(issues, repo)

    def test_canonical_run_uses_only_internal_reserved_staging(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, source, _ = self._production_repo(Path(tmp))
            history = repo / "_src/output/issue-migration"
            result = self._run(repo, history, "0037-31-post-delta-7dbc94db-r2", source)
            self.assertEqual("promoted", result["state"]["status"])
            self.assertTrue((history / "0037-31-post-delta-7dbc94db-r2/issues").is_dir())

    def test_property_positive_acceptance_ref_membership_exhaustive_64_cases(self):
        """AE-5: exhaustive typed-field subsets; only three positive current bindings are members."""
        fields = [
            ("Carrying commit", "1" * 40, True),
            ("Review-decision commit", "2" * 40, True),
            ("Review REF", "3" * 40, True),
            ("Base-Ref", "4" * 40, False),
            ("Rejected commit", "5" * 40, False),
            ("Unrelated commit", "6" * 40, False),
        ]
        cases = 0
        for membership in itertools.product((False, True), repeat=len(fields)):
            section = "\n".join(
                f"- **{name}:** `{value}`"
                for include, (name, value, _allowed) in zip(membership, fields)
                if include
            )
            expected = sorted(
                value
                for include, (_name, value, allowed) in zip(membership, fields)
                if include and allowed
            )
            self.assertEqual(IMP._positive_acceptance_ref_values(section), expected)
            cases += 1
        self.assertEqual(cases, 64)

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


def _tree_blobs(tree: Path):
    blobs = {}
    for path in tree.rglob("*"):
        if path.is_file():
            blobs[path.relative_to(tree).as_posix()] = (path.read_bytes(), None)
    return blobs


def _pin_tree(parent: Path, tree: Path) -> tuple[Path, str]:
    repo = parent / "pinned"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "disp@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Disposition"], cwd=repo, check=True)
    for path in tree.rglob("*"):
        if path.is_file():
            dest = repo / path.relative_to(tree)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, dest)
    inventory = repo / "provenance/migrations/issue-store/tools"
    inventory.mkdir(parents=True)
    shutil.copy(
        ROOT / "provenance/migrations/issue-store/tools/issue_legacy_inventory.py",
        inventory / "issue_legacy_inventory.py",
    )
    tools = repo / "_src/tools"
    tools.mkdir(parents=True)
    shutil.copy(ROOT / "_src/tools/issue_import_legacy.py", tools / "issue_import_legacy.py")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "pin"], cwd=repo, check=True, capture_output=True)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
    subprocess.run(["git", "fetch", str(ROOT), AUTHORITY_COMMIT], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "gpg.ssh.allowedSignersFile", str(ROOT / "issues/_policy/allowed_signers")],
        cwd=repo, check=True, capture_output=True,
    )
    return repo, sha


def _baseline_importer():
    raw = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "cfe67e988f9ccff7d9a2d08457fbc65b4bdd9cab:_src/tools/issue_import_legacy.py"]
    )
    path = Path(tempfile.mkdtemp()) / "issue_import_legacy_cfe67e988f.py"
    path.write_bytes(raw)
    spec = importlib.util.spec_from_file_location("issue_import_legacy_cfe67e988f", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rejected_importer():
    raw = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "eaab94cfc077fa826af3f47d7702a7e2e47816d1:_src/tools/issue_import_legacy.py"]
    )
    path = Path(tempfile.mkdtemp()) / "issue_import_legacy_eaab94cfc0.py"
    path.write_bytes(raw)
    spec = importlib.util.spec_from_file_location("issue_import_legacy_eaab94cfc0", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _unbound_authority_importer():
    raw = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "2765459ce6a787bc2000b437af62b3db80f13f42:_src/tools/issue_import_legacy.py"]
    )
    path = Path(tempfile.mkdtemp()) / "issue_import_legacy_2765459ce6.py"
    path.write_bytes(raw)
    spec = importlib.util.spec_from_file_location("issue_import_legacy_2765459ce6", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _live_root_alias_importer():
    raw = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", "f22686fb6985c0371ac38f9a8325714d04147257:_src/tools/issue_import_legacy.py"]
    )
    path = Path(tempfile.mkdtemp()) / "issue_import_legacy_f22686fb69.py"
    path.write_bytes(raw)
    spec = importlib.util.spec_from_file_location("issue_import_legacy_f22686fb69", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _entry_for(finding, blobs, commit, kind=None):
    rule = finding["rule"]
    if kind is None:
        if rule in IMP.DISPOSITION_MALFORMED_RULES:
            kind = "archive-excluded-from-active-migration"
        elif rule in {
            "IMP-REF-NO-EVIDENCE-CREDIT", "IMP-REF-PENDING",
            "IMP-REF-LOCAL-PLACEHOLDER", "IMP-CLOSURE-EVIDENCE-PLACEHOLDER",
        }:
            kind = "retain-provenance-no-evidence-credit"
        elif rule in {
            "IMP-CLOSURE-ACCEPTANCE-MISSING", "IMP-CLOSURE-EVIDENCE-MISSING",
            "IMP-CLOSURE-CRITERION-EVIDENCE-MISSING",
        }:
            kind = "import-open-legacy-terminal-unverified"
        elif rule == "IMP-MARKER-UNDEFINED":
            kind = "import-open-undefined-marker-investigate"
        else:
            kind = "retain-provenance-no-active-lease"
    blob_digest, field_digest = IMP.expected_finding_digests(finding, blobs)
    entry = {
        "finding_id": finding["id"],
        "finding_rule": rule,
        "source_locator": finding["locator"],
        "item": finding["item"],
        "source_commit": commit,
        "kind": kind,
        "reason": "Hermetic bounded disposition; grants no closure or evidence credit.",
        "deciding_identity": "authority:supervisor",
        "deciding_role": "Management",
        "authority_ref": "DEC-0037-007",
        "decided_at": "2026-09-03T01:00:00Z",
        "evidence_refs": ["hermetic:test"],
        "signature_material": _authority_material(),
        "signature_verified": True,
    }
    if field_digest is not None:
        entry["referenced_field_digest"] = field_digest
    else:
        entry["source_blob_digest"] = blob_digest
    if kind == "archive-excluded-from-active-migration":
        entry["archive_retention_justification"] = "Byte-exact archival retention is safe because the malformed header is stored unmodified."
        entry["parser_independent_archival_safe"] = True
        entry["cannot_participate_in_active_state_reason"] = "Malformed structural syntax cannot be parsed into active issue state."
    entry["payload_digest"] = IMP.disposition_payload_digest(entry)
    return entry


def _bind_authority(repo: Path, entries) -> dict:
    records = [
        {
            "authority_ref": entry["authority_ref"],
            "deciding_identity": entry["deciding_identity"],
            "deciding_role": entry["deciding_role"],
            "payload_digest": entry["payload_digest"],
        }
        for entry in entries
    ]
    authority_path = repo / "authority/migration-dispositions.json"
    authority_path.parent.mkdir(parents=True, exist_ok=True)
    authority_path.write_text(
        IMP._canonical_json({"schema": "migration-disposition-authority@v1", "entries": records}),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", authority_path.relative_to(repo)], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "authorize migration dispositions"], cwd=repo, check=True, capture_output=True)
    authority_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
    principal = subprocess.check_output(
        ["git", "show", "-s", "--format=%GS", authority_commit], cwd=repo
    ).decode().strip()
    material = {
        "scheme": "git-ssh-commit-v1",
        "commit": authority_commit,
        "path": authority_path.relative_to(repo).as_posix(),
        "blob_digest": IMP._digest_prefixed(authority_path.read_bytes()),
        "principal": principal,
    }
    for entry in entries:
        entry["signature_material"] = material
    return material


class DispositionContractTests(unittest.TestCase):
    BASELINE = "998dba844591db2aca9f51957de41b236b4b08c4"

    def test_ae3_red_baseline_blocks_and_green_dispositions_cover(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "red"
            red = IMP.import_legacy(repo=ROOT, root=dest, source_tree=FIXTURE_13)
            self.assertTrue(red["blocking"])
            self.assertIsNone(red.get("disposition_coverage"))
            rules = {finding["rule"] for finding in red["findings"]}
            self.assertTrue(
                {
                    "IMP-CLAIM-OPAQUE",
                    "IMP-REF-PENDING",
                    "IMP-REF-NO-EVIDENCE-CREDIT",
                    "IMP-FEATURE-HEADER-MALFORMED",
                    "IMP-TASK-HEADER-MALFORMED",
                    "IMP-MARKER-UNDEFINED",
                }.issubset(rules)
            )
            blobs = _tree_blobs(FIXTURE_13)
            repo, commit = _pin_tree(Path(tmp) / "pin", FIXTURE_13)
            entries = [
                _entry_for(finding, blobs, commit)
                for finding in red["findings"]
                if finding["severity"] == "blocking"
            ]
            _bind_authority(repo, entries)
            manifest_path = Path(tmp) / "dispositions.json"
            document = {"schema": IMP.DISPOSITION_SCHEMA, "entries": entries}
            manifest_path.write_text(IMP._canonical_json(document), encoding="utf-8")
            green_root = Path(tmp) / "green"
            green = IMP.import_legacy(
                repo=repo, root=green_root, source_commit=commit, source_tree=FIXTURE_13, dispositions=manifest_path,
            )
            self.assertFalse(green["blocking"])
            self.assertFalse(green["closure_json_emitted"])
            self.assertFalse(list(green_root.rglob("closure.json")))
            self.assertEqual(green["disposition_coverage"]["credit_granted"], False)
            self.assertEqual(len(green["disposition_coverage"]["pairs"]), len(entries))
            red_claims = sorted(p for p in red["written"] if p.startswith("legacy-claims/"))
            green_claims = sorted(p for p in green["written"] if p.startswith("legacy-claims/"))
            self.assertEqual(red_claims, green_claims)
            for rel in red_claims:
                self.assertEqual((dest / rel).read_bytes(), (green_root / rel).read_bytes())

    def test_dec_0037_008_q4_terminal_becomes_open_without_closure(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "src"
            tree.mkdir()
            (tree / "TODO.md").write_text(
                "# none\n",
                encoding="utf-8",
            )
            (tree / "DONE.md").write_text(
                "## Feature: 0099 — Mini\n\n"
                "- [x] **0099-01** Terminal without acceptance.\n"
                "  - **Acceptance criteria:** Evidence exists.\n",
                encoding="utf-8",
            )
            blobs = _tree_blobs(tree)
            repo, commit = _pin_tree(Path(tmp) / "pin", tree)
            red = IMP.import_legacy(
                repo=repo, root=Path(tmp) / "red", source_commit=commit,
                source_tree=tree, emit_closures=True,
            )
            target = [f for f in red["findings"] if f["rule"] == "IMP-CLOSURE-ACCEPTANCE-MISSING"]
            self.assertEqual(len(target), 1)
            entries = [_entry_for(f, blobs, commit) for f in red["findings"] if f["severity"] == "blocking"]
            _bind_authority(repo, entries)
            path = Path(tmp) / "d.json"
            path.write_text(IMP._canonical_json({"schema": IMP.DISPOSITION_SCHEMA, "entries": entries}))
            out = Path(tmp) / "green"
            green = IMP.import_legacy(
                repo=repo, root=out, source_commit=commit, source_tree=tree,
                emit_closures=True, dispositions=path,
            )
            item = next(value for value in green["items"] if value["id"] == "0099-01")
            self.assertEqual(item["state"], "open")
            self.assertIn("legacy-terminal-unverified", (out / item["path"]).read_text())
            self.assertFalse(green["closure_json_emitted"])
            self.assertFalse(list(out.rglob("closure.json")))

    def test_dec_0037_008_q5_undefined_marker_is_open_investigation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "src"
            tree.mkdir()
            (tree / "TODO.md").write_text(
                "## Feature: 0099 — Mini\n\n- [~] **0099-01** Unknown legacy marker.\n",
                encoding="utf-8",
            )
            (tree / "DONE.md").write_text("# none\n", encoding="utf-8")
            red = IMP.import_legacy(repo=ROOT, root=Path(tmp) / "red", source_tree=tree)
            marker = next(f for f in red["findings"] if f["rule"] == "IMP-MARKER-UNDEFINED")
            blobs = _tree_blobs(tree)
            repo, commit = _pin_tree(Path(tmp) / "pin", tree)
            entry = _entry_for(marker, blobs, commit)
            _bind_authority(repo, [entry])
            path = Path(tmp) / "d.json"
            path.write_text(IMP._canonical_json({"schema": IMP.DISPOSITION_SCHEMA, "entries": [entry]}))
            out = Path(tmp) / "green"
            green = IMP.import_legacy(repo=repo, root=out, source_commit=commit, source_tree=tree, dispositions=path)
            item = next(value for value in green["items"] if value["id"] == "0099-01")
            self.assertEqual(item["state"], "open")
            self.assertIn("investigation-required", (out / item["path"]).read_text())

    def test_generator_binds_exact_finding_and_authority_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            probe = IMP.import_legacy(repo=ROOT, root=Path(tmp) / "probe", source_tree=FIXTURE_13)
            finding = next(f for f in probe["findings"] if f["rule"] == "IMP-CLAIM-OPAQUE")
            entry = IMP.generate_disposition_entry(
                finding=finding, blobs=_tree_blobs(FIXTURE_13), source_commit="0" * 40,
                kind="retain-provenance-no-active-lease", reason="bounded",
                deciding_identity="authority:supervisor:management", deciding_role="Management",
                authority_ref="DEC-0037-008", decided_at="2026-09-03T12:46:17Z",
                evidence_refs=["commit:51be4db07c"], signature_material=_authority_material(),
            )
            self.assertEqual(entry["payload_digest"], IMP.disposition_payload_digest(entry))
            self.assertEqual(IMP.generate_authority_record(entry), {
                "authority_ref": "DEC-0037-008",
                "deciding_identity": "authority:supervisor:management",
                "deciding_role": "Management",
                "payload_digest": entry["payload_digest"],
            })

    def test_signed_retain_kinds_cannot_cover_another_retain_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            probe = IMP.import_legacy(repo=ROOT, root=Path(tmp) / "probe", source_tree=FIXTURE_13)
            blobs = _tree_blobs(FIXTURE_13)
            repo, commit = _pin_tree(Path(tmp) / "pin", FIXTURE_13)
            blocking = [finding for finding in probe["findings"] if finding["severity"] == "blocking"]
            cases = (
                (
                    next(f for f in blocking if f["rule"] == "IMP-CLAIM-OPAQUE"),
                    "retain-provenance-no-evidence-credit",
                ),
                (
                    next(f for f in blocking if f["rule"] == "IMP-REF-NO-EVIDENCE-CREDIT"),
                    "retain-provenance-no-active-lease",
                ),
            )
            for finding, wrong_kind in cases:
                with self.subTest(rule=finding["rule"], kind=wrong_kind):
                    entry = _entry_for(finding, blobs, commit, kind=wrong_kind)
                    _bind_authority(repo, [entry])
                    with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                        IMP.apply_dispositions(
                            document={"schema": IMP.DISPOSITION_SCHEMA, "entries": [entry]},
                            findings=probe["findings"], blobs=blobs,
                            source_commit=commit, repo=repo,
                        )
                    self.assertEqual(ctx.exception.code, "DISP-WRONG-KIND")

    def test_ae5_exhaustive_real_watermark_identity_domain(self):
        """AE-5 exhaustive domain: every finding identity in the pinned 910/911 runs."""
        evidence_commit = "51be4db07c26bf48aa1eb00ff8cdbcea8fc81b45"
        runs = (
            ("real-7eebde81ec-0001", 910),
            ("real-2554eac3ea-0002", 911),
        )
        family_rules = set().union(*IMP.DISPOSITION_KIND_RULES.values(), IMP.DISPOSITION_MALFORMED_RULES)
        executed = 0
        for run_id, expected_count in runs:
            path = f"_src/output/issue-migration/{run_id}/issues/import-findings.json"
            raw = subprocess.check_output(["git", "show", f"{evidence_commit}:{path}"], cwd=ROOT)
            findings = json.loads(raw)
            self.assertEqual(len(findings), expected_count)
            identities = {
                (f["id"], f["rule"], f["locator"], str(f["item"]))
                for f in findings
            }
            self.assertEqual(len(identities), expected_count)
            self.assertTrue(all(f["rule"] in family_rules for f in findings))
            executed += len(identities)
        self.assertEqual(executed, 1821)

    def test_adjacent_wrong_digest_and_unmatched_remain_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            probe = IMP.import_legacy(repo=ROOT, root=Path(tmp) / "probe", source_tree=FIXTURE_13)
            blobs = _tree_blobs(FIXTURE_13)
            repo, commit = _pin_tree(Path(tmp) / "pin", FIXTURE_13)
            blocking = [f for f in probe["findings"] if f["severity"] == "blocking"]
            entries = [_entry_for(f, blobs, commit) for f in blocking]
            entries[0]["source_blob_digest"] = "sha256:" + ("ab" * 32)
            if "referenced_field_digest" in entries[0]:
                entries[0].pop("source_blob_digest", None)
                entries[0]["referenced_field_digest"] = "sha256:" + ("ab" * 32)
            entries[0]["payload_digest"] = IMP.disposition_payload_digest(entries[0])
            _bind_authority(repo, entries)
            path = Path(tmp) / "bad-digest.json"
            path.write_text(IMP._canonical_json({"schema": IMP.DISPOSITION_SCHEMA, "entries": entries}))
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                IMP.import_legacy(repo=repo, root=Path(tmp) / "out", source_commit=commit, source_tree=FIXTURE_13, dispositions=path)
            self.assertEqual(ctx.exception.code, "DISP-WRONG-DIGEST")
            extra = dict(_entry_for(blocking[0], blobs, commit))
            extra["finding_id"] = "IMP-" + ("a" * 16)
            extra["payload_digest"] = IMP.disposition_payload_digest(extra)
            unmatched_entries = [_entry_for(f, blobs, commit) for f in blocking] + [extra]
            _bind_authority(repo, unmatched_entries)
            path2 = Path(tmp) / "unmatched.json"
            path2.write_text(IMP._canonical_json({"schema": IMP.DISPOSITION_SCHEMA, "entries": unmatched_entries}))
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                IMP.import_legacy(repo=repo, root=Path(tmp) / "out2", source_commit=commit, source_tree=FIXTURE_13, dispositions=path2)
            self.assertEqual(ctx.exception.code, "DISP-UNMATCHED")

    def test_ae5_entry_order_and_missing_field_property(self):
        rng_seed = 37029
        with tempfile.TemporaryDirectory() as tmp:
            probe = IMP.import_legacy(repo=ROOT, root=Path(tmp) / "probe", source_tree=FIXTURE_13)
            blobs = _tree_blobs(FIXTURE_13)
            repo, commit = _pin_tree(Path(tmp) / "pin", FIXTURE_13)
            blocking = [f for f in probe["findings"] if f["severity"] == "blocking"]
            entries = [_entry_for(f, blobs, commit) for f in blocking]
            _bind_authority(repo, entries)
            cases = 0
            for permutation in itertools.permutations(entries[:3]):
                document = {"schema": IMP.DISPOSITION_SCHEMA, "entries": list(permutation) + entries[3:]}
                coverage = IMP.apply_dispositions(
                    document=document, findings=probe["findings"], blobs=blobs, source_commit=commit, repo=repo,
                )
                self.assertEqual(len(coverage["pairs"]), len(blocking))
                self.assertEqual([p["finding_id"] for p in coverage["pairs"]], sorted(e["finding_id"] for e in entries))
                cases += 1
            self.assertEqual(cases, 6)
            missing_cases = 0
            for field in ("reason", "authority_ref", "signature_material"):
                broken = dict(entries[0])
                broken.pop(field)
                with self.assertRaises(IMP.ImportErrorClosed):
                    IMP.validate_disposition_document({"schema": IMP.DISPOSITION_SCHEMA, "entries": [broken] + entries[1:]})
                missing_cases += 1
            self.assertEqual(missing_cases, 3)
            self.assertEqual(rng_seed, 37029)

    def test_schema_fixtures_parity(self):
        root = ROOT / "issues/_schema/fixtures/migration-dispositions-v1"
        index = json.loads((root / "manifest.json").read_text())
        for rel in index["valid"]:
            value = json.loads((root / rel).read_text())
            IMP.validate_disposition_document(value)
        for rel in index["invalid"]:
            value = json.loads((root / rel).read_text())
            with self.assertRaises(IMP.ImportErrorClosed):
                IMP.validate_disposition_document(value)

    def test_rework_two_three_runtime_type_falsification_cases(self):
        """AE-3: eaab94cfc0 accepts all three records; this candidate rejects each targeted field."""
        rejected = _rejected_importer()
        good = {
            "finding_id": "IMP-aaaaaaaaaaaaaaaa",
            "finding_rule": "IMP-CLAIM-OPAQUE",
            "source_locator": "TODO-example.md",
            "item": "0099-01",
            "source_commit": "0" * 40,
            "source_blob_digest": "sha256:" + ("0" * 64),
            "kind": "retain-provenance-no-active-lease",
            "reason": "bounded",
            "deciding_identity": "authority:supervisor",
            "deciding_role": "Management",
            "authority_ref": "DEC-0037-007",
            "decided_at": "2026-09-03T01:00:00Z",
            "evidence_refs": ["hermetic:test"],
            "signature_verified": True,
        }
        good["payload_digest"] = rejected.disposition_payload_digest(good)
        good["signature_material"] = rejected.derived_signature_material(good)
        cases = (
            ("signature_verified", False, "DISP-UNVERIFIABLE"),
            ("reason", 7, "DISP-MALFORMED"),
            ("evidence_refs", [7], "DISP-MALFORMED"),
        )
        for field, value, code in cases:
            broken = dict(good)
            broken[field] = value
            broken["payload_digest"] = rejected.disposition_payload_digest(broken)
            broken["signature_material"] = rejected.derived_signature_material(broken)
            rejected.validate_disposition_document({"schema": rejected.DISPOSITION_SCHEMA, "entries": [broken]})
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                IMP.validate_disposition_document({"schema": IMP.DISPOSITION_SCHEMA, "entries": [broken]})
            self.assertEqual(ctx.exception.code, code)

    def test_unsigned_and_archive_on_non_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "d"
            probe = IMP.import_legacy(repo=ROOT, root=dest, source_tree=FIXTURE_13)
            blobs = _tree_blobs(FIXTURE_13)
            repo, commit = _pin_tree(Path(tmp) / "pin", FIXTURE_13)
            opaque = next(f for f in probe["findings"] if f["rule"] == "IMP-CLAIM-OPAQUE")
            entry = _entry_for(opaque, blobs, commit)
            entry["kind"] = "archive-excluded-from-active-migration"
            entry["archive_retention_justification"] = "x"
            entry["parser_independent_archival_safe"] = True
            entry["cannot_participate_in_active_state_reason"] = "y"
            entry["payload_digest"] = IMP.disposition_payload_digest(entry)
            others = [
                _entry_for(f, blobs, commit)
                for f in probe["findings"]
                if f["severity"] == "blocking" and f["id"] != opaque["id"]
            ]
            _bind_authority(repo, [entry] + others)
            path = Path(tmp) / "arch.json"
            path.write_text(IMP._canonical_json({"schema": IMP.DISPOSITION_SCHEMA, "entries": [entry] + others}))
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                IMP.import_legacy(repo=repo, root=Path(tmp) / "out", source_commit=commit, source_tree=FIXTURE_13, dispositions=path)
            self.assertEqual(ctx.exception.code, "DISP-MALFORMED")
            unsigned = _entry_for(opaque, blobs, commit)
            unsigned["signature_material"] = "arbitrary-self-asserted"
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                IMP.validate_disposition_document({"schema": IMP.DISPOSITION_SCHEMA, "entries": [unsigned]})
            self.assertEqual(ctx.exception.code, "DISP-UNVERIFIABLE")

    def test_authority_material_verifies_signed_source_and_rejects_adjacent_mismatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, commit = _pin_tree(Path(tmp) / "pin", FIXTURE_13)
            entry = {
                "finding_id": "IMP-aaaaaaaaaaaaaaaa",
                "finding_rule": "IMP-CLAIM-OPAQUE",
                "source_locator": "TODO-example.md",
                "item": "0099-01",
                "source_commit": commit,
                "source_blob_digest": "sha256:" + ("0" * 64),
                "kind": "retain-provenance-no-active-lease",
                "reason": "bounded",
                "deciding_identity": "authority:supervisor",
                "deciding_role": "Management",
                "authority_ref": "DEC-0037-007",
                "decided_at": "2026-09-03T01:00:00Z",
                "evidence_refs": ["hermetic:test"],
            }
            entry["payload_digest"] = IMP.disposition_payload_digest(entry)
            _bind_authority(repo, [entry])
            IMP.verify_authority_material(entry, repo)
            architecture_only = dict(entry)
            architecture_only["signature_material"] = _authority_material()
            unbound = _unbound_authority_importer()
            unbound.verify_authority_material(architecture_only, ROOT)
            contradictory = dict(architecture_only, reason="opposite disposition rationale")
            contradictory["payload_digest"] = unbound.disposition_payload_digest(contradictory)
            unbound.verify_authority_material(contradictory, ROOT)
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                IMP.verify_authority_material(architecture_only, ROOT)
            self.assertEqual(ctx.exception.code, "DISP-UNVERIFIABLE")
            for field, value in (
                ("finding_id", "IMP-bbbbbbbbbbbbbbbb"),
                ("kind", "retain-provenance-no-evidence-credit"),
                ("reason", "contradictory"),
                ("evidence_refs", ["hermetic:other"]),
                ("decided_at", "2026-09-03T01:00:01Z"),
                ("source_commit", "1" * 40),
            ):
                replay = dict(entry)
                replay[field] = value
                replay["payload_digest"] = IMP.disposition_payload_digest(replay)
                with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                    IMP.verify_authority_material(replay, repo)
                self.assertEqual(ctx.exception.code, "DISP-UNVERIFIABLE")
            wrong_principal = dict(entry)
            wrong_principal["signature_material"] = dict(entry["signature_material"], principal="mallory@example.invalid")
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                IMP.verify_authority_material(wrong_principal, repo)
            self.assertEqual(ctx.exception.code, "DISP-UNVERIFIABLE")
            wrong_blob = dict(entry)
            wrong_blob["signature_material"] = dict(entry["signature_material"], blob_digest="sha256:" + ("0" * 64))
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                IMP.verify_authority_material(wrong_blob, repo)
            self.assertEqual(ctx.exception.code, "DISP-UNVERIFIABLE")

    def test_local_placeholder_family_is_coverable(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "src"
            tree.mkdir()
            (tree / "TODO.md").write_text(
                "## Feature: 0099 — Mini\n\n"
                "- [ ] **0099-01** Task with local placeholder.\n"
                "  - **Acceptance criteria:** A.\n"
                "  - **REF:** `local-test-placeholder`\n",
                encoding="utf-8",
            )
            (tree / "DONE.md").write_text("# none\n", encoding="utf-8")
            dest = Path(tmp) / "red"
            red = IMP.import_legacy(repo=ROOT, root=dest, source_tree=tree)
            self.assertTrue(any(f["rule"] == "IMP-REF-LOCAL-PLACEHOLDER" for f in red["findings"]))
            blobs = _tree_blobs(tree)
            repo, commit = _pin_tree(Path(tmp) / "pin", tree)
            entries = [_entry_for(f, blobs, commit) for f in red["findings"] if f["severity"] == "blocking"]
            _bind_authority(repo, entries)
            path = Path(tmp) / "d.json"
            path.write_text(IMP._canonical_json({"schema": IMP.DISPOSITION_SCHEMA, "entries": entries}))
            green = IMP.import_legacy(repo=repo, root=Path(tmp) / "green", source_commit=commit, source_tree=tree, dispositions=path)
            self.assertFalse(green["blocking"])

    def test_rework_four_gaps_red_on_cfe67e988f_green_on_candidate(self):
        """AE-3: each Geordi gap is accepted on cfe67e988f and rejected here."""
        baseline = _baseline_importer()
        with tempfile.TemporaryDirectory() as tmp:
            probe = IMP.import_legacy(repo=ROOT, root=Path(tmp) / "probe", source_tree=FIXTURE_13)
            blobs = _tree_blobs(FIXTURE_13)
            opaque = next(f for f in probe["findings"] if f["rule"] == "IMP-CLAIM-OPAQUE" and f["severity"] == "blocking")
            good = _entry_for(opaque, blobs, "0" * 40)
            role = dict(good)
            role["deciding_role"] = 7
            role["payload_digest"] = IMP.disposition_payload_digest(role)
            baseline.validate_disposition_document({"schema": IMP.DISPOSITION_SCHEMA, "entries": [role]})
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                IMP.validate_disposition_document({"schema": IMP.DISPOSITION_SCHEMA, "entries": [role]})
            self.assertEqual(ctx.exception.code, "DISP-MALFORMED")
            forged = dict(good)
            forged["signature_material"] = "arbitrary"
            forged["signature_verified"] = True
            baseline.validate_disposition_document({"schema": IMP.DISPOSITION_SCHEMA, "entries": [forged]})
            with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                IMP.validate_disposition_document({"schema": IMP.DISPOSITION_SCHEMA, "entries": [forged]})
            self.assertEqual(ctx.exception.code, "DISP-UNVERIFIABLE")
            repaired = dict(good)
            repaired["kind"] = "source-repaired"
            repaired["payload_digest"] = IMP.disposition_payload_digest(repaired)
            others = [
                _entry_for(
                    f, blobs, "0" * 40,
                    kind="retain-provenance-no-active-lease"
                    if f["rule"] == "IMP-MARKER-UNDEFINED" else None,
                )
                for f in probe["findings"]
                if f["severity"] == "blocking" and f["id"] != opaque["id"]
            ]
            baseline.apply_dispositions(
                document={"schema": IMP.DISPOSITION_SCHEMA, "entries": [repaired] + others},
                findings=probe["findings"], blobs=blobs, source_commit=None,
            )
            with mock.patch.object(IMP, "verify_authority_material", return_value=None):
                with self.assertRaises(IMP.ImportErrorClosed) as ctx:
                    IMP.apply_dispositions(
                        document={"schema": IMP.DISPOSITION_SCHEMA, "entries": [repaired] + others},
                        findings=probe["findings"], blobs=blobs, source_commit="0" * 40, repo=ROOT,
                    )
            self.assertEqual(ctx.exception.code, "DISP-UNPROVEN-REPAIR")
            missing = Path(tmp) / "one.json"
            missing.write_text(IMP._canonical_json({"schema": IMP.DISPOSITION_SCHEMA, "entries": [good]}))
            with self.assertRaises(IMP.ImportErrorClosed) as ctx2:
                IMP.import_legacy(repo=ROOT, root=Path(tmp) / "skip2", source_tree=FIXTURE_13, dispositions=missing)
            self.assertEqual(ctx2.exception.code, "DISP-WRONG-COMMIT")
            cases = 0
            for role_value in (7, True, 3.14, {"r": "x"}):
                bad = dict(good)
                bad["deciding_role"] = role_value
                with self.assertRaises(IMP.ImportErrorClosed):
                    IMP.validate_disposition_document({"schema": IMP.DISPOSITION_SCHEMA, "entries": [bad]})
                cases += 1
            self.assertEqual(cases, 4)

    def test_imp_live_root_history_alias_is_reported_not_weakened(self):
        """Geordi IMP-LIVE-ROOT: in-repo history alias stays fail-closed; not a disposition gate."""
        with self.assertRaises(IMP.ImportErrorClosed) as ctx:
            IMP._history_root(ROOT / "issues", ROOT)
        self.assertEqual(ctx.exception.code, "IMP-LIVE-ROOT")


if __name__ == "__main__":
    unittest.main()
