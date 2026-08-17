#!/usr/bin/env python3
"""Hermetic tests for the fail-closed legacy runner transaction adapter."""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
from typing import Any, Dict, Optional


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _src.tools import runner_transaction as runner


AUTHORITY = {
    "schema": "agent-workflow-bootstrap@v1",
    "authority_epoch": "legacy-writable",
    "authority_profile": "legacy-lists",
    "write_phase": "legacy-writable",
    "runner_protocol": "runner-request@v1",
}
REQUEST_ID = "fixture-runner-transaction-001"
OWNER_TOKEN = "agent:test:0038-01:fixture-runner-transaction-001"
CLAIM_PATH = "TODO-test-0038-01-fixture-runner-transaction-001.md"


class FixtureRepo:
    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="runner-transaction-test-")
        self.root = Path(self.temporary.name)
        self._create_repository()

    def close(self) -> None:
        self.temporary.cleanup()

    def git(
        self,
        *args: str,
        check: bool = True,
        env: Optional[Dict[str, str]] = None,
    ) -> subprocess.CompletedProcess[bytes]:
        process_env = os.environ.copy()
        process_env["GIT_EDITOR"] = "true"
        if env:
            process_env.update(env)
        return subprocess.run(
            ["git", "--no-pager", *args],
            cwd=str(self.root),
            env=process_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )

    def git_text(self, *args: str) -> str:
        return self.git(*args).stdout.decode("utf-8", "replace").strip()

    @property
    def base(self) -> str:
        return self.git_text("rev-parse", "HEAD")

    def _create_repository(self) -> None:
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Runner Transaction Test")
        self.git("config", "user.email", "runner-transaction@example.invalid")
        (self.root / ".gitignore").write_text("output/\n", encoding="utf-8")
        (self.root / "agent-workflow.json").write_text(json.dumps(AUTHORITY), encoding="utf-8")
        (self.root / "TODO.md").write_text(
            "# TODO\n\n"
            "## Feature: 0038 — Fixture\n\n"
            "- [p] **0038-01** Exercise the transaction.\n"
            "  - **Acceptance criteria:** Fail closed.\n"
            "  - **Definition of Done:** Two commits and exact cleanup.\n\n"
            "- [ ] **0038-02** Preserve this neighboring Task.\n"
            "  - **Definition of Done:** It remains separate.\n",
            encoding="utf-8",
        )
        (self.root / CLAIM_PATH).write_text(
            "# Fixture claim\n\n"
            "task_id: 0038-01\n"
            f"request_id: {REQUEST_ID}\n"
            f"owner_token: {OWNER_TOKEN}\n"
            "base_commit: PLACEHOLDER\n"
            f"transaction_profile: {runner.PROFILE}\n"
            "transaction_manifest: PLACEHOLDER_MANIFEST\n"
            "transaction_actions_json: PLACEHOLDER_ACTIONS\n"
            "transaction_authority_json: PLACEHOLDER_AUTHORITY\n"
            "transaction_commit_message_json: PLACEHOLDER_COMMIT_MESSAGE\n"
            "transaction_bookkeeping_json: PLACEHOLDER_BOOKKEEPING\n"
            "transaction_read_paths_json: PLACEHOLDER_READS\n"
            "transaction_write_paths_json: PLACEHOLDER_WRITES\n"
            "capability_class: sandboxed/grunt\n"
            "state: [p]\n",
            encoding="utf-8",
        )
        (self.root / "source.txt").write_text("base\n", encoding="utf-8")
        (self.root / "generated.txt").write_text("generated:base\n", encoding="utf-8")
        (self.root / "unrelated.txt").write_text("unrelated-base\n", encoding="utf-8")
        scripts = self.root / "_src"
        scripts.mkdir()
        (scripts / "generate.py").write_text(
            "from pathlib import Path\n"
            "import json\n"
            "import sys\n"
            "value = Path('source.txt').read_text(encoding='utf-8').strip()\n"
            "if value == 'generate-fail':\n"
            "    print('generator failed deliberately', file=sys.stderr)\n"
            "    raise SystemExit(3)\n"
            "if value == 'mutate-input':\n"
            "    Path('source.txt').write_text('mutated-by-generator\\n', encoding='utf-8')\n"
            "Path('generated.txt').write_text('generated:' + value + '\\n', encoding='utf-8')\n"
            "Path('output').mkdir(exist_ok=True)\n"
            "report = {'success': True, 'exit_code': 0, 'findings': []}\n"
            "if value == 'structured-error':\n"
            "    report['findings'].append({'severity': 'error', 'message': 'deliberate'})\n"
            "Path('output/report.json').write_text(json.dumps(report), encoding='utf-8')\n",
            encoding="utf-8",
        )
        (scripts / "validate.py").write_text(
            "from pathlib import Path\n"
            "import sys\n"
            "value = Path('source.txt').read_text(encoding='utf-8').strip()\n"
            "Path('output').mkdir(exist_ok=True)\n"
            "Path('output/validate-ran').write_text('yes', encoding='utf-8')\n"
            "if value == 'validate-fail':\n"
            "    print('validator failed deliberately', file=sys.stderr)\n"
            "    raise SystemExit(4)\n"
            "if value == 'validate-mutates':\n"
            "    Path('generated.txt').write_text('mutated-by-validator\\n', encoding='utf-8')\n"
            "    raise SystemExit(0)\n"
            "expected = 'generated:' + value\n"
            "if Path('generated.txt').read_text(encoding='utf-8').strip() != expected:\n"
            "    print('generated output mismatch', file=sys.stderr)\n"
            "    raise SystemExit(5)\n",
            encoding="utf-8",
        )
        self.git("add", "--", ".gitignore", "agent-workflow.json", "TODO.md", CLAIM_PATH, "source.txt", "generated.txt", "unrelated.txt", "_src/generate.py", "_src/validate.py")
        self.git("commit", "-m", "fixture: initial state")
        base = self.base
        claim = (self.root / CLAIM_PATH).read_text(encoding="utf-8").replace("PLACEHOLDER", base)
        (self.root / CLAIM_PATH).write_text(claim, encoding="utf-8")
        self.git("add", "--", CLAIM_PATH)
        self.git("commit", "-m", "fixture: bind claim to base")
        # The expected base is the commit containing its own predecessor value in
        # the claim in real workflows. For this fixture, bind once more and amend
        # the test manifest expectation to the resulting HEAD by updating the
        # claim through a final ordinary commit.
        base = self.base
        claim = (self.root / CLAIM_PATH).read_text(encoding="utf-8")
        claim = re.sub(r"^base_commit: [0-9a-f]{40}$", f"base_commit: {base}", claim, flags=re.MULTILINE)
        (self.root / CLAIM_PATH).write_text(claim, encoding="utf-8")
        self.git("add", "--", CLAIM_PATH)
        self.git("commit", "-m", "fixture: finalize base marker")
        # Claims normally record the discovery base while later non-substantive
        # coordination commits can advance HEAD. The transaction requires exact
        # HEAD, so use a detached fixture rewrite with commit-tree semantics by
        # replacing the field in the working claim and committing it once, then
        # reading that commit as the expected base in make_manifest().
        final = self.base
        claim = (self.root / CLAIM_PATH).read_text(encoding="utf-8")
        claim = re.sub(r"^base_commit: [0-9a-f]{40}$", f"base_commit: {final}", claim, flags=re.MULTILINE)
        (self.root / CLAIM_PATH).write_text(claim, encoding="utf-8")
        # Leave this exact claim update uncommitted. Real active claims are often
        # untracked or modified coordination state; preflight compares the field
        # to current HEAD, not the blob in HEAD.

    def manifest(self) -> Path:
        value: Dict[str, Any] = {
            "schema": runner.MANIFEST_SCHEMA,
            "profile": runner.PROFILE,
            "identity": {
                "task_id": "0038-01",
                "request_id": REQUEST_ID,
                "owner_token": OWNER_TOKEN,
                "claim_path": CLAIM_PATH,
                "manifest_path": "request.json",
                "expected_base": self.base,
            },
            "authority": {
                "selector_path": "agent-workflow.json",
                "authority_epoch": AUTHORITY["authority_epoch"],
                "authority_profile": AUTHORITY["authority_profile"],
                "write_phase": AUTHORITY["write_phase"],
                "runner_protocol": AUTHORITY["runner_protocol"],
            },
            "scope": {
                "read_paths": ["_src/generate.py", "_src/validate.py", "agent-workflow.json"],
                "input_paths": ["source.txt"],
                "output_paths": ["generated.txt"],
                "substantive_paths": ["source.txt", "generated.txt"],
            },
            "actions": [
                {"id": "generate-site", "timeout_seconds": 30, "reports": ["output/report.json"]},
                {"id": "validate-project", "timeout_seconds": 30, "reports": []},
            ],
        }
        value["commit"] = {
            "substantive_message": (
                "feat(0038-01): fixture transaction\n\n"
                "User-Prompt-Provenance:\n"
                "Exercise the fail-closed transaction fixture verbatim."
            )
        }
        value["bookkeeping"] = {
            "todo_path": "TODO.md",
            "closure_text": "The fixture transaction completed all fail-closed gates.",
            "commit_message": "docs(todo): close fixture Task 0038-01",
        }
        return self.store_manifest(value)

    def store_manifest(self, value: Dict[str, Any]) -> Path:
        path = self.root / "request.json"
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
        claim_path = self.root / CLAIM_PATH
        claim = claim_path.read_text(encoding="utf-8")
        for key, expected in runner.claim_contract_fields(value).items():
            claim = re.sub(
                rf"^{re.escape(key)}: .+$",
                lambda _match, key=key, expected=expected: f"{key}: {expected}",
                claim,
                flags=re.MULTILINE,
            )
        claim_path.write_text(claim, encoding="utf-8")
        return path

    def execute(self, *, inject_failure: Optional[str] = None, dry_run: bool = False) -> tuple[int, str]:
        manifest = runner.load_manifest(self.manifest())
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = runner.Transaction(
                self.root,
                manifest,
                dry_run=dry_run,
                inject_failure=inject_failure,
            ).execute()
        return status, output.getvalue()


class RunnerTransactionTests(unittest.TestCase):
    _fixture: Optional[FixtureRepo] = None

    @property
    def fixture(self) -> FixtureRepo:
        assert self._fixture is not None
        return self._fixture

    def setUp(self) -> None:
        self._fixture = FixtureRepo()
        self.addCleanup(self.fixture.close)

    def _change_source(self, value: str) -> None:
        (self.fixture.root / "source.txt").write_text(value + "\n", encoding="utf-8")

    def _result(self) -> Dict[str, Any]:
        path = self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID / "result.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_rejects_arbitrary_action(self) -> None:
        path = self.fixture.manifest()
        value = json.loads(path.read_text(encoding="utf-8"))
        value["actions"][0]["id"] = "shell"
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(runner.TransactionError, "unknown action ID"):
            runner.load_manifest(path)

    def test_generator_failure_stops_validation_and_preserves_real_state(self) -> None:
        base = self.fixture.base
        original_generated = (self.fixture.root / "generated.txt").read_bytes()
        self._change_source("generate-fail")
        status, output = self.fixture.execute()
        self.assertEqual(status, runner.EXIT_ACTION)
        self.assertIn("RTX-ACTION-NONZERO", output)
        self.assertEqual(self.fixture.base, base)
        self.assertEqual((self.fixture.root / "generated.txt").read_bytes(), original_generated)
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())
        self.assertIn("- [p] **0038-01**", (self.fixture.root / "TODO.md").read_text(encoding="utf-8"))
        result = self._result()
        self.assertEqual(result["verdict"], "failed")
        self.assertEqual([item["id"] for item in result["actions"]], ["generate-site"])

    def test_validator_failure_does_not_promote_generated_output(self) -> None:
        base = self.fixture.base
        original_generated = (self.fixture.root / "generated.txt").read_bytes()
        self._change_source("validate-fail")
        status, output = self.fixture.execute()
        self.assertEqual(status, runner.EXIT_ACTION)
        self.assertEqual([item["id"] for item in self._result()["actions"]], ["generate-site", "validate-project"])
        self.assertEqual(self.fixture.base, base)
        self.assertEqual((self.fixture.root / "generated.txt").read_bytes(), original_generated)
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())

    def test_exit_zero_structured_error_is_a_failed_gate(self) -> None:
        base = self.fixture.base
        original_generated = (self.fixture.root / "generated.txt").read_bytes()
        self._change_source("structured-error")
        status, output = self.fixture.execute()
        self.assertEqual(status, runner.EXIT_ACTION)
        self.assertIn("RTX-REPORT-ERROR", output)
        self.assertEqual(self.fixture.base, base)
        self.assertEqual((self.fixture.root / "generated.txt").read_bytes(), original_generated)
        self.assertEqual([item["id"] for item in self._result()["actions"]], ["generate-site"])

    def test_generator_cannot_mutate_declared_input(self) -> None:
        base = self.fixture.base
        original_generated = (self.fixture.root / "generated.txt").read_bytes()
        self._change_source("mutate-input")
        status, output = self.fixture.execute()
        self.assertEqual(status, runner.EXIT_SCOPE)
        self.assertIn("RTX-GENERATE-MUTATED-INPUT", output)
        self.assertEqual(self.fixture.base, base)
        self.assertEqual((self.fixture.root / "generated.txt").read_bytes(), original_generated)
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())

    def test_validator_cannot_mutate_prepared_tree(self) -> None:
        base = self.fixture.base
        original_generated = (self.fixture.root / "generated.txt").read_bytes()
        self._change_source("validate-mutates")
        status, output = self.fixture.execute()
        self.assertEqual(status, runner.EXIT_SCOPE)
        self.assertIn("RTX-VALIDATE-MUTATED-TREE", output)
        self.assertEqual(self.fixture.base, base)
        self.assertEqual((self.fixture.root / "generated.txt").read_bytes(), original_generated)

    def test_injected_promotion_failure_rolls_back_output(self) -> None:
        base = self.fixture.base
        original_generated = (self.fixture.root / "generated.txt").read_bytes()
        self._change_source("promotion-failure")
        status, output = self.fixture.execute(inject_failure="during-promote")
        self.assertEqual(status, runner.EXIT_INTERNAL)
        self.assertIn("RTX-INJECTED-FAILURE", output)
        self.assertEqual(self.fixture.base, base)
        self.assertEqual((self.fixture.root / "generated.txt").read_bytes(), original_generated)
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())

    def test_dirty_shared_todo_is_rejected_before_actions(self) -> None:
        base = self.fixture.base
        self.fixture.manifest()
        todo = self.fixture.root / "TODO.md"
        todo.write_text(todo.read_text(encoding="utf-8") + "\nUnrelated concurrent note.\n", encoding="utf-8")
        status, output = self.fixture.execute()
        self.assertEqual(status, runner.EXIT_PREFLIGHT)
        self.assertIn("RTX-BOOKKEEPING-DIRTY", output)
        self.assertEqual(self.fixture.base, base)
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())

    def test_success_uses_two_commits_and_preserves_unrelated_index(self) -> None:
        base = self.fixture.base
        self._change_source("accepted")
        (self.fixture.root / "unrelated.txt").write_text("unrelated-staged\n", encoding="utf-8")
        self.fixture.git("add", "--", "unrelated.txt")
        status, output = self.fixture.execute()
        result = self._result()
        self.assertEqual(status, 0, f"{output}\n{json.dumps(result, indent=2)}")
        substantive = result["substantive_commit"]
        bookkeeping = result["bookkeeping_commit"]
        self.assertRegex(substantive, r"^[0-9a-f]{40}$")
        self.assertRegex(bookkeeping, r"^[0-9a-f]{40}$")
        self.assertEqual(self.fixture.base, bookkeeping)
        self.assertEqual(self.fixture.git_text("rev-parse", f"{substantive}^"), base)
        self.assertEqual(self.fixture.git_text("rev-parse", f"{bookkeeping}^"), substantive)
        substantive_paths = set(self.fixture.git_text("diff-tree", "--no-commit-id", "--name-only", "-r", substantive).splitlines())
        bookkeeping_paths = set(self.fixture.git_text("diff-tree", "--no-commit-id", "--name-only", "-r", bookkeeping).splitlines())
        self.assertEqual(substantive_paths, {"source.txt", "generated.txt"})
        self.assertEqual(bookkeeping_paths, {"TODO.md", CLAIM_PATH})
        todo = (self.fixture.root / "TODO.md").read_text(encoding="utf-8")
        self.assertIn("- [x] **0038-01**", todo)
        self.assertIn(f"REF: {substantive}", todo)
        self.assertIn("- [ ] **0038-02**", todo)
        self.assertFalse((self.fixture.root / CLAIM_PATH).exists())
        self.assertEqual(self.fixture.git_text("diff", "--cached", "--name-only"), "unrelated.txt")
        self.assertEqual((self.fixture.root / "generated.txt").read_text(encoding="utf-8"), "generated:accepted\n")
        self.assertIn("User-Prompt-Provenance:", self.fixture.git_text("show", "-s", "--format=%B", substantive))

    def test_prepublication_injection_boundaries_roll_back_and_retain_claim(self) -> None:
        for point in ("after-promote", "after-substantive-commit", "after-bookkeeping-commit", "before-cas"):
            with self.subTest(point=point):
                fixture = FixtureRepo()
                self.addCleanup(fixture.close)
                base = fixture.base
                original_generated = (fixture.root / "generated.txt").read_bytes()
                (fixture.root / "source.txt").write_text(f"boundary:{point}\n", encoding="utf-8")
                status, output = fixture.execute(inject_failure=point)
                self.assertEqual(status, runner.EXIT_INTERNAL, output)
                self.assertIn("RTX-INJECTED-FAILURE", output)
                self.assertEqual(fixture.base, base)
                self.assertEqual((fixture.root / "generated.txt").read_bytes(), original_generated)
                self.assertTrue((fixture.root / CLAIM_PATH).exists())
                result_path = fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID / "result.json"
                result = json.loads(result_path.read_text(encoding="utf-8"))
                self.assertNotEqual(result["verdict"], "passed")

    def test_failure_after_atomic_publication_retains_claim_for_recovery(self) -> None:
        base = self.fixture.base
        self._change_source("published-recovery")
        status, output = self.fixture.execute(inject_failure="after-publish")
        self.assertEqual(status, runner.EXIT_INTERNAL)
        self.assertIn("RTX-INJECTED-FAILURE", output)
        self.assertNotEqual(self.fixture.base, base)
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())
        self.assertIn("- [x] **0038-01**", (self.fixture.root / "TODO.md").read_text(encoding="utf-8"))
        result = self._result()
        self.assertTrue(result["published"])
        self.assertFalse(result["claim_finalized"])

    def test_competing_branch_update_wins_and_transaction_rolls_back(self) -> None:
        base = self.fixture.base
        original_generated = (self.fixture.root / "generated.txt").read_bytes()
        self._change_source("cas-loser")
        manifest = runner.load_manifest(self.fixture.manifest())
        transaction = runner.Transaction(self.fixture.root, manifest)
        competing_commit: list[str] = []

        def inject(point: str) -> None:
            if point == "before-cas":
                competitor = self.fixture.root / "competitor.txt"
                competitor.write_text("winner\n", encoding="utf-8")
                self.fixture.git("add", "--", "competitor.txt")
                self.fixture.git("commit", "-m", "fixture: competing winner")
                competing_commit.append(self.fixture.base)

        transaction._inject = inject
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = transaction.execute()
        self.assertEqual(status, runner.EXIT_COMMIT, output.getvalue())
        self.assertEqual(self.fixture.base, competing_commit[0])
        self.assertNotEqual(self.fixture.base, base)
        self.assertEqual((self.fixture.root / "generated.txt").read_bytes(), original_generated)
        self.assertIn("- [p] **0038-01**", (self.fixture.root / "TODO.md").read_text(encoding="utf-8"))
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())
        result = self._result()
        for prepared in (result["substantive_commit"], result["bookkeeping_commit"]):
            ancestry = self.fixture.git("merge-base", "--is-ancestor", prepared, self.fixture.base, check=False)
            self.assertEqual(ancestry.returncode, 1)

    def test_claim_binding_rejects_removed_report_gate(self) -> None:
        path = self.fixture.manifest()
        manifest = runner.load_manifest(path)
        value = json.loads(path.read_text(encoding="utf-8"))
        value["actions"][0]["reports"] = []
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
        # Load the changed bytes, but deliberately leave the claim bound to the
        # original report requirement.
        changed = runner.load_manifest(path)
        with self.assertRaisesRegex(runner.TransactionError, "transaction_actions_json"):
            runner.Transaction(self.fixture.root, changed, dry_run=True).execute()
        self.assertNotEqual(runner.contract_digest(manifest), runner.contract_digest(changed))

    def test_manifest_replacement_after_parse_is_rejected(self) -> None:
        path = self.fixture.manifest()
        manifest = runner.load_manifest(path)
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(runner.TransactionError, "manifest bytes changed"):
            runner.Transaction(self.fixture.root, manifest, dry_run=True).execute()

    def test_prepublication_rollback_failure_is_explicit_and_journaled(self) -> None:
        self._change_source("rollback-incomplete")
        transaction = runner.Transaction(
            self.fixture.root,
            runner.load_manifest(self.fixture.manifest()),
            inject_failure="before-cas",
        )
        rollback_error = runner.TransactionError(
            "RTX-FIXTURE-ROLLBACK",
            "injected rollback storage failure",
            "rollback",
            runner.EXIT_PROMOTION,
        )
        output = io.StringIO()
        with mock.patch.object(transaction, "rollback_outputs", side_effect=rollback_error), contextlib.redirect_stdout(output):
            status = transaction.execute()
        self.assertEqual(status, runner.EXIT_PROMOTION)
        result = self._result()
        self.assertEqual(result["error"]["rule"], "RTX-ROLLBACK-INCOMPLETE")
        self.assertTrue(result["promotion_backups_retained"])
        self.assertIn("- [x] **0038-01**", (self.fixture.root / "TODO.md").read_text(encoding="utf-8"))
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())

    def test_concurrent_claim_replacement_preserves_both_versions(self) -> None:
        self._change_source("claim-conflict")
        manifest = runner.load_manifest(self.fixture.manifest())
        original_claim = (self.fixture.root / CLAIM_PATH).read_bytes()
        transaction = runner.Transaction(self.fixture.root, manifest)

        def inject(point: str) -> None:
            if point == "before-claim-move":
                replacement = self.fixture.root / "replacement-claim.tmp"
                replacement.write_bytes(original_claim + b"\nnewer concurrent note\n")
                os.replace(str(replacement), str(self.fixture.root / CLAIM_PATH))

        transaction._inject = inject
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = transaction.execute()
        self.assertEqual(status, runner.EXIT_BOOKKEEPING, output.getvalue())
        self.assertEqual((self.fixture.root / CLAIM_PATH).read_bytes(), original_claim)
        conflicts = list((self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID).glob("claim-archive-conflict-*.md"))
        self.assertEqual(len(conflicts), 1)
        self.assertIn(b"newer concurrent note", conflicts[0].read_bytes())
        self.assertNotEqual(self._result()["verdict"], "passed")

    def test_final_result_failure_restores_claim_and_leaves_nonpassing_result(self) -> None:
        self._change_source("result-write-failure")
        manifest = runner.load_manifest(self.fixture.manifest())
        transaction = runner.Transaction(self.fixture.root, manifest)
        original_write = runner._atomic_write

        def flaky_write(path: Path, data: bytes, mode: Optional[int] = None) -> None:
            if path.name == "result.json":
                value = json.loads(data.decode("utf-8"))
                if value["verdict"] in {"passed", "failed"}:
                    raise OSError("injected result storage failure")
            original_write(path, data, mode)

        output = io.StringIO()
        with mock.patch.object(runner, "_atomic_write", side_effect=flaky_write), contextlib.redirect_stdout(output):
            status = transaction.execute()
        self.assertEqual(status, runner.EXIT_BOOKKEEPING)
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())
        result = self._result()
        self.assertEqual(result["verdict"], "published-pending-finalization")
        self.assertFalse(result["claim_finalized"])

    def test_committed_candidate_symlink_is_rejected_before_input_copy(self) -> None:
        external = self.fixture.root.parent / f"{self.fixture.root.name}-escape-target"
        external.mkdir()
        self.addCleanup(lambda: shutil.rmtree(external, ignore_errors=True))
        prefix = self.fixture.root / "prefix"
        prefix.symlink_to(external, target_is_directory=True)
        self.fixture.git("add", "--", "prefix")
        self.fixture.git("commit", "-m", "fixture: committed candidate symlink")
        base = self.fixture.base
        claim_path = self.fixture.root / CLAIM_PATH
        claim = re.sub(
            r"^base_commit: [0-9a-f]{40}$",
            f"base_commit: {base}",
            claim_path.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
        claim_path.write_text(claim, encoding="utf-8")
        prefix.unlink()
        prefix.mkdir()
        (prefix / "source.txt").write_text("safe-real-worktree-input\n", encoding="utf-8")
        path = self.fixture.manifest()
        value = json.loads(path.read_text(encoding="utf-8"))
        value["scope"]["input_paths"] = ["prefix/source.txt"]
        value["scope"]["substantive_paths"] = ["prefix/source.txt", "generated.txt"]
        path = self.fixture.store_manifest(value)
        transaction = runner.Transaction(self.fixture.root, runner.load_manifest(path))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = transaction.execute()
        self.assertEqual(status, runner.EXIT_PREFLIGHT)
        self.assertIn("RTX-PATH-SYMLINK", output.getvalue())
        self.assertFalse((external / "source.txt").exists())
        self.assertEqual(self.fixture.base, base)
        self.assertTrue(claim_path.exists())

    def test_runtime_evidence_paths_cannot_alias_substantive_outputs(self) -> None:
        path = self.fixture.manifest()
        value = json.loads(path.read_text(encoding="utf-8"))
        runtime_output = f"output/logs/0038-01/{REQUEST_ID}/result.json"
        value["scope"]["output_paths"] = [runtime_output]
        value["scope"]["substantive_paths"] = ["source.txt", runtime_output]
        path = self.fixture.store_manifest(value)
        transaction = runner.Transaction(self.fixture.root, runner.load_manifest(path), dry_run=True)
        with self.assertRaisesRegex(runner.TransactionError, "reserved transaction runtime root"):
            transaction.execute()

    def test_dry_run_is_read_only(self) -> None:
        base = self.fixture.base
        self._change_source("dry-run")
        self.fixture.manifest()
        before_status = self.fixture.git_text("status", "--porcelain=v1", "--untracked-files=all")
        status, output = self.fixture.execute(dry_run=True)
        self.assertEqual(status, 0, output)
        self.assertIn("dry-run=true mutation=none", output)
        self.assertEqual(self.fixture.base, base)
        self.assertEqual(self.fixture.git_text("status", "--porcelain=v1", "--untracked-files=all"), before_status)
        self.assertFalse((self.fixture.root / "output").exists())

    def test_closure_profile_cannot_omit_commit_or_bookkeeping(self) -> None:
        path = self.fixture.manifest()
        value = json.loads(path.read_text(encoding="utf-8"))
        value["commit"] = None
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(runner.TransactionError, "commit must be an object"):
            runner.load_manifest(path)
        value = json.loads(self.fixture.manifest().read_text(encoding="utf-8"))
        value["actions"] = [value["actions"][1]]
        path = self.fixture.store_manifest(value)
        with self.assertRaisesRegex(runner.TransactionError, "requires generation followed by validation"):
            runner.load_manifest(path)
        value = json.loads(self.fixture.manifest().read_text(encoding="utf-8"))
        value["scope"]["output_paths"] = []
        value["scope"]["substantive_paths"] = ["source.txt"]
        path = self.fixture.store_manifest(value)
        with self.assertRaisesRegex(runner.TransactionError, "requires at least one generated output"):
            runner.load_manifest(path)

    def test_doctor_reports_stale_lock_without_mutating_it(self) -> None:
        git_dir = Path(self.fixture.git_text("rev-parse", "--git-dir"))
        if not git_dir.is_absolute():
            git_dir = self.fixture.root / git_dir
        lock = git_dir / "autodocs-runner-transaction.lock"
        stale = {"pid": 99999999, "start_time": 0.0, "request_id": "stale-request"}
        lock.write_text(json.dumps(stale), encoding="utf-8")
        report = runner.doctor(self.fixture.root)
        self.assertTrue(report["lock"]["exists"])
        self.assertTrue(report["lock"]["stale"])
        self.assertEqual(json.loads(lock.read_text(encoding="utf-8")), stale)

    def test_acquire_lock_replaces_verified_stale_holder(self) -> None:
        manifest = runner.load_manifest(self.fixture.manifest())
        transaction = runner.Transaction(self.fixture.root, manifest)
        git_dir = Path(self.fixture.git_text("rev-parse", "--git-dir"))
        if not git_dir.is_absolute():
            git_dir = self.fixture.root / git_dir
        lock = git_dir / "autodocs-runner-transaction.lock"
        lock.write_text(json.dumps({"pid": 99999999, "start_time": 0.0}), encoding="utf-8")
        transaction.acquire_lock()
        self.addCleanup(transaction.release_lock)
        self.assertEqual(json.loads(lock.read_text(encoding="utf-8")), transaction.lock_dict)

    def test_live_lock_and_missing_recovery_journal_fail_closed(self) -> None:
        manifest = runner.load_manifest(self.fixture.manifest())
        transaction = runner.Transaction(self.fixture.root, manifest)
        git_dir = Path(self.fixture.git_text("rev-parse", "--git-dir"))
        if not git_dir.is_absolute():
            git_dir = self.fixture.root / git_dir
        lock = git_dir / "autodocs-runner-transaction.lock"
        lock.write_text(json.dumps({"pid": os.getpid(), "start_time": time.time()}), encoding="utf-8")
        with self.assertRaisesRegex(runner.TransactionError, "transaction lock is held"):
            transaction.acquire_lock()
        with self.assertRaisesRegex(runner.TransactionError, "no transaction journal found"):
            runner.recover_transaction(self.fixture.root, "no-such-request")

    def test_sigterm_persists_failure_journal_result_and_releases_lock(self) -> None:
        manifest = runner.load_manifest(self.fixture.manifest())
        transaction = runner.Transaction(self.fixture.root, manifest)
        handlers: Dict[int, Any] = {}
        with mock.patch.object(runner.signal, "signal", side_effect=lambda sig, handler: handlers.__setitem__(sig, handler)):
            transaction.acquire_lock()
        assert transaction.lock_path is not None
        lock = transaction.lock_path
        with self.assertRaises(SystemExit) as exited:
            handlers[runner.signal.SIGTERM](runner.signal.SIGTERM, None)
        self.assertEqual(exited.exception.code, runner.EXIT_INTERNAL)
        self.assertFalse(lock.exists())
        journal = json.loads(transaction.journal_path.read_text(encoding="utf-8"))
        result = json.loads(transaction.result_path.read_text(encoding="utf-8"))
        self.assertEqual(journal["state"], "killed-by-signal-SIGTERM")
        self.assertEqual(journal["error"], "RTX-TERMINATED-SIGNAL")
        self.assertEqual(result["verdict"], "failed")
        self.assertEqual(result["error"]["rule"], "RTX-TERMINATED-SIGNAL")

    def test_rollback_drift_retains_backup_and_recovery_journals(self) -> None:
        manifest = runner.load_manifest(self.fixture.manifest())
        transaction = runner.Transaction(self.fixture.root, manifest)
        destination = self.fixture.root / "generated.txt"
        previous = runner._read_state(destination)
        backup_root = transaction.log_dir / "promotion-backups"
        backup_root.mkdir(parents=True)
        backup = backup_root / "0000.backup"
        shutil.copyfile(destination, backup)
        destination.write_text("promoted output\n", encoding="utf-8")
        promoted = runner._read_state(destination)
        transaction.promotion_backup_root = backup_root
        transaction.promotion_journal = [runner.PromotionRecord("generated.txt", previous, backup, promoted)]
        destination.write_text("newer external edit\n", encoding="utf-8")
        with self.assertRaisesRegex(runner.TransactionError, "refusing to overwrite a newer edit"):
            transaction.rollback_outputs()
        self.assertEqual(destination.read_text(encoding="utf-8"), "newer external edit\n")
        self.assertTrue(backup.exists())
        promotion = json.loads((transaction.log_dir / "promotion-journal.json").read_text(encoding="utf-8"))
        journal = json.loads(transaction.journal_path.read_text(encoding="utf-8"))
        self.assertEqual(promotion["status"], "rollback-blocked-by-drift")
        self.assertEqual(journal["state"], "rollback-blocked-by-drift")

    def test_recover_reports_interrupted_journal_state(self) -> None:
        log_dir = self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID
        log_dir.mkdir(parents=True)
        (log_dir / "transaction-journal.json").write_text(
            json.dumps({"state": "outputs-promoted", "request_id": REQUEST_ID}),
            encoding="utf-8",
        )
        recovery = runner.recover_transaction(self.fixture.root, REQUEST_ID)
        self.assertEqual(recovery["status"], "reconciled")
        self.assertEqual(recovery["prior_state"], "outputs-promoted")
        self.assertIn("finalize claim", recovery["recommendation"])

    def test_finalize_claim_standalone_archives_matching_claim(self) -> None:
        claim = self.fixture.root / CLAIM_PATH
        self.assertTrue(runner.finalize_claim_standalone(self.fixture.root, "0038-01", REQUEST_ID))
        archive = self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID / "finalized-claim.md"
        self.assertFalse(claim.exists())
        self.assertTrue(archive.exists())
        self.assertFalse(runner.finalize_claim_standalone(self.fixture.root, "0038-01", REQUEST_ID))

    def test_envelope_renderer_rejects_shell_metacharacters(self) -> None:
        for hostile in (
            "output/request $(touch owned).json",
            "output/request;touch-owned.json",
            "output/`touch-owned`.json",
            "output/request|cat.json",
            "output/request\tbad.json",
        ):
            with self.subTest(hostile=hostile), self.assertRaises(runner.TransactionError):
                runner.render_envelope(hostile)

    def test_envelope_linter_accepts_only_thin_transaction_wrapper(self) -> None:
        safe = self.fixture.root / "safe.sh"
        safe.write_text(runner.render_envelope("output/requests/0038-01/request.json"), encoding="utf-8")
        self.assertEqual(runner.lint_envelope(safe), [])
        unsafe = self.fixture.root / "unsafe.sh"
        unsafe.write_text(
            "#!/bin/bash\nset -euo pipefail\ncd /tmp/autodocs\n"
            "python3 _src/generate.py\npython3 _src/validate.py\n"
            "rm -f TODO-agent-*.md\ngit add TODO.md\ngit commit -m done\n",
            encoding="utf-8",
        )
        findings = runner.lint_envelope(unsafe)
        rules = {finding.split(":", 1)[0] for finding in findings}
        self.assertTrue({"RTX-ENV-EXEC", "RTX-ENV-DELETE", "RTX-ENV-GIT", "RTX-ENV-DIRECT-PHASE"} <= rules)

    def test_structural_closure_rejects_missing_or_duplicate_task(self) -> None:
        with self.assertRaisesRegex(runner.TransactionError, "exactly one"):
            runner.render_task_closure(
                "- [ ] **0038-01** Not active.\n  - **Definition of Done:** No.\n",
                "0038-01",
                "1" * 40,
                REQUEST_ID,
                "No closure.",
            )


if __name__ == "__main__":
    unittest.main()
