#!/usr/bin/env python3
"""Hermetic tests for the fail-closed legacy runner transaction adapter."""

from __future__ import annotations

import contextlib
import copy
import hashlib
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
from _src.tools import legacy_task_editor as lte


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
        pointer = json.loads((self.fixture.root / "output" / "logs" / "0038-01" / "current.json").read_text(encoding="utf-8"))
        self.assertEqual(pointer["verdict"], "failed")
        self.assertEqual(pointer["request_id"], REQUEST_ID)
        self.assertEqual(runner._current_pointer_status(self.fixture.root, "0038-01")["status"], "valid")

        fresh_request_id = "fixture-runner-transaction-fresh-001"
        fresh_owner_token = "agent:test:0038-01:fixture-runner-transaction-fresh-001"
        fresh_claim_path = "TODO-test-0038-01-fixture-runner-transaction-fresh-001.md"
        fresh_manifest_path = "fresh-request.json"
        next_manifest = json.loads(self.fixture.manifest().read_text(encoding="utf-8"))
        next_manifest["identity"].update({
            "request_id": fresh_request_id,
            "owner_token": fresh_owner_token,
            "claim_path": fresh_claim_path,
            "manifest_path": fresh_manifest_path,
        })
        fresh_claim = (self.fixture.root / CLAIM_PATH).read_text(encoding="utf-8")
        fresh_claim = fresh_claim.replace(REQUEST_ID, fresh_request_id).replace(OWNER_TOKEN, fresh_owner_token)
        for key, expected in runner.claim_contract_fields(next_manifest).items():
            fresh_claim = re.sub(
                rf"^{re.escape(key)}: .+$",
                lambda _match, key=key, expected=expected: f"{key}: {expected}",
                fresh_claim,
                flags=re.MULTILINE,
            )
        (self.fixture.root / fresh_claim_path).write_text(fresh_claim, encoding="utf-8")
        fresh_path = self.fixture.root / fresh_manifest_path
        fresh_path.write_text(json.dumps(next_manifest, indent=2), encoding="utf-8")
        fresh_manifest = runner.load_manifest(fresh_path)
        runner.Transaction(self.fixture.root, fresh_manifest).preflight()

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
        result_path = self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID / "result.json"
        pointer_path = self.fixture.root / "output" / "logs" / "0038-01" / "current.json"
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        self.assertEqual(pointer["result_path"], result_path.relative_to(self.fixture.root).as_posix())
        self.assertEqual(pointer["result_sha256"], hashlib.sha256(result_path.read_bytes()).hexdigest())
        self.assertEqual(pointer["verdict"], "passed")
        self.assertEqual(runner._current_pointer_status(self.fixture.root, "0038-01")["status"], "valid")

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
        recovery = runner.recover_transaction(self.fixture.root, REQUEST_ID)
        self.assertEqual(recovery["status"], "terminal-failure-recorded")

    def test_result_precedes_current_pointer_and_crash_keeps_pointer_unmoved(self) -> None:
        self._change_source("pointer-order")
        status, output = self.fixture.execute(inject_failure="before-current-pointer")
        self.assertEqual(status, runner.EXIT_INTERNAL, output)
        result_path = self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID / "result.json"
        pointer_path = self.fixture.root / "output" / "logs" / "0038-01" / "current.json"
        self.assertTrue(result_path.exists())
        self.assertFalse(pointer_path.exists())
        self.assertEqual(json.loads(result_path.read_text(encoding="utf-8"))["verdict"], "passed")
        journal = json.loads((result_path.parent / "transaction-journal.json").read_text(encoding="utf-8"))
        self.assertEqual(journal["state"], "result-persisted-pointer-pending")
        doctor = runner.doctor(self.fixture.root)
        self.assertEqual(doctor["current_pointers"], [{"path": "output/logs/0038-01/current.json", "status": "missing"}])

    def test_current_pointer_rejects_tampered_immutable_result(self) -> None:
        self._change_source("tamper-pointer")
        status, output = self.fixture.execute()
        self.assertEqual(status, 0, output)
        result_path = self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID / "result.json"
        result_path.write_text('{"tampered":true}\n', encoding="utf-8")
        status = runner._current_pointer_status(self.fixture.root, "0038-01")
        self.assertEqual(status["status"], "invalid")
        self.assertIn("digest", status["error"])
        recovery = runner.recover_transaction(self.fixture.root, REQUEST_ID)
        self.assertEqual(recovery["status"], "pointer-invalid")

    def test_immutable_results_survive_fresh_retry_pointer_update(self) -> None:
        retry_manifest = copy.deepcopy(runner.load_manifest(self.fixture.manifest()))
        self._change_source("first-attempt")
        status, output = self.fixture.execute()
        self.assertEqual(status, 0, output)
        first_result = self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID / "result.json"
        first_bytes = first_result.read_bytes()
        retry_id = "fixture-runner-transaction-retry-002"
        retry_manifest["identity"]["request_id"] = retry_id
        retry = runner.Transaction(self.fixture.root, retry_manifest)
        retry.observed_base = self.fixture.base
        retry.observed_authority = dict(AUTHORITY)
        retry.substantive_commit = self.fixture.base
        retry.published = True
        retry.claim_finalized = True
        retry._begin_phase("recovery")
        retry._finish_phase("failed", runner.EXIT_ACTION, detail="RTX-RETRY-FIXTURE")
        retry_error = runner.TransactionError("RTX-RETRY-FIXTURE", "fixture retry failure", "recovery", runner.EXIT_ACTION)
        retry.persist_terminal_result(retry.result("failed", retry_error))
        self.assertEqual(first_result.read_bytes(), first_bytes)
        pointer = json.loads((self.fixture.root / "output" / "logs" / "0038-01" / "current.json").read_text(encoding="utf-8"))
        self.assertEqual(pointer["request_id"], retry_id)
        self.assertEqual(pointer["result_path"], f"output/logs/0038-01/{retry_id}/result.json")
        self.assertTrue((self.fixture.root / pointer["result_path"]).exists())
        recovery = runner.recover_transaction(self.fixture.root, REQUEST_ID)
        self.assertEqual(recovery["status"], "pointer-journal-mismatch")

    def test_timeout_persists_failed_result_and_current_pointer(self) -> None:
        manifest_path = self.fixture.manifest()
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_data["actions"][0]["timeout_seconds"] = 1
        manifest = runner.load_manifest(self.fixture.store_manifest(manifest_data))
        sleeper = runner.ActionSpec(
            action_id="generate-site",
            phase="generate",
            argv=(sys.executable, "-c", "import time; time.sleep(2)"),
        )
        output = io.StringIO()
        with mock.patch.dict(runner.ACTION_REGISTRY, {"generate-site": sleeper}), contextlib.redirect_stdout(output):
            status = runner.Transaction(self.fixture.root, manifest).execute()
        self.assertEqual(status, runner.EXIT_ACTION, output.getvalue())
        result = self._result()
        self.assertEqual(result["error"]["rule"], "RTX-ACTION-TIMEOUT")
        self.assertEqual(result["actions"], [
            {
                "id": "generate-site",
                "phase": "generate",
                "status": "timed_out",
                "exit_code": None,
                "duration_ms": result["actions"][0]["duration_ms"],
                "stdout": result["actions"][0]["stdout"],
                "stderr": result["actions"][0]["stderr"],
                "reports": [],
            }
        ])
        self.assertGreaterEqual(result["actions"][0]["duration_ms"], 1000)
        pointer = json.loads((self.fixture.root / "output" / "logs" / "0038-01" / "current.json").read_text(encoding="utf-8"))
        self.assertEqual(pointer["verdict"], "failed")

    def test_post_publication_crash_recovers_claim_result_and_pointer(self) -> None:
        self._change_source("post-cas-crash")
        transaction = runner.Transaction(self.fixture.root, runner.load_manifest(self.fixture.manifest()))

        def crash(point: str) -> None:
            if point == "after-publish":
                raise KeyboardInterrupt("simulated hard crash")

        transaction._inject = crash
        with self.assertRaises(KeyboardInterrupt):
            transaction.execute()
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())
        self.assertFalse(transaction.result_path.exists())
        self.assertTrue(runner.finalize_claim_standalone(self.fixture.root, "0038-01", REQUEST_ID))
        self.assertFalse((self.fixture.root / CLAIM_PATH).exists())
        self.assertEqual(runner._current_pointer_status(self.fixture.root, "0038-01")["status"], "valid")
        journal = json.loads(transaction.journal_path.read_text(encoding="utf-8"))
        self.assertEqual(journal["state"], "complete")

    def test_same_request_rerun_preserves_interrupted_attempt_evidence(self) -> None:
        self._change_source("same-request-rerun")
        manifest = runner.load_manifest(self.fixture.manifest())
        transaction = runner.Transaction(self.fixture.root, manifest)

        def crash(point: str) -> None:
            if point == "after-publish":
                raise KeyboardInterrupt("simulated hard crash")

        transaction._inject = crash
        with self.assertRaises(KeyboardInterrupt):
            transaction.execute()
        journal_before = transaction.journal_path.read_bytes()
        self.assertFalse(transaction.result_path.exists())
        self.assertFalse(transaction.current_pointer_path.exists())

        rerun = runner.Transaction(self.fixture.root, manifest)
        status = rerun.execute()
        self.assertEqual(status, runner.EXIT_PREFLIGHT)
        self.assertEqual(transaction.journal_path.read_bytes(), journal_before)
        self.assertFalse(transaction.result_path.exists())
        self.assertFalse(transaction.current_pointer_path.exists())
        self.assertTrue(runner.finalize_claim_standalone(self.fixture.root, "0038-01", REQUEST_ID))

    def test_claim_archival_crash_recovers_result_and_pointer(self) -> None:
        self._change_source("claim-archive-crash")
        transaction = runner.Transaction(self.fixture.root, runner.load_manifest(self.fixture.manifest()))
        with mock.patch.object(transaction, "persist_terminal_result", side_effect=KeyboardInterrupt("simulated hard crash")):
            with self.assertRaises(KeyboardInterrupt):
                transaction.execute()
        self.assertFalse((self.fixture.root / CLAIM_PATH).exists())
        self.assertTrue((transaction.log_dir / "finalized-claim.md").exists())
        self.assertFalse(transaction.result_path.exists())
        self.assertFalse(runner.finalize_claim_standalone(self.fixture.root, "0038-01", REQUEST_ID))
        self.assertEqual(runner._current_pointer_status(self.fixture.root, "0038-01")["status"], "valid")
        journal = json.loads(transaction.journal_path.read_text(encoding="utf-8"))
        self.assertEqual(journal["state"], "complete")

    def test_tampered_prepared_result_blocks_recovery_before_claim_move(self) -> None:
        self._change_source("prepared-tamper")
        transaction = runner.Transaction(self.fixture.root, runner.load_manifest(self.fixture.manifest()))

        def crash(point: str) -> None:
            if point == "after-publish":
                raise KeyboardInterrupt("simulated hard crash")

        transaction._inject = crash
        with self.assertRaises(KeyboardInterrupt):
            transaction.execute()
        prepared_path = transaction.log_dir / "prepared-result.json"
        prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
        del prepared["phases"]
        prepared_path.write_text(json.dumps(prepared), encoding="utf-8")
        with self.assertRaisesRegex(runner.TransactionError, "missing required fields"):
            runner.finalize_claim_standalone(self.fixture.root, "0038-01", REQUEST_ID)
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())
        self.assertFalse(transaction.result_path.exists())
        self.assertFalse(transaction.current_pointer_path.exists())

    def test_tampered_claim_archive_blocks_recovery_before_result_write(self) -> None:
        self._change_source("archive-tamper")
        transaction = runner.Transaction(self.fixture.root, runner.load_manifest(self.fixture.manifest()))
        with mock.patch.object(transaction, "persist_terminal_result", side_effect=KeyboardInterrupt("simulated hard crash")):
            with self.assertRaises(KeyboardInterrupt):
                transaction.execute()
        archive = transaction.log_dir / "finalized-claim.md"
        archive.write_text(archive.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
        with self.assertRaisesRegex(runner.TransactionError, "preimage digest"):
            runner.finalize_claim_standalone(self.fixture.root, "0038-01", REQUEST_ID)
        self.assertFalse(transaction.result_path.exists())
        self.assertFalse(transaction.current_pointer_path.exists())

    def test_invalid_current_pointer_blocks_a_fresh_attempt(self) -> None:
        next_manifest = copy.deepcopy(runner.load_manifest(self.fixture.manifest()))
        self._change_source("pointer-preflight")
        status, output = self.fixture.execute()
        self.assertEqual(status, 0, output)
        result_path = self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID / "result.json"
        result_path.write_text('{"tampered":true}\n', encoding="utf-8")
        next_manifest["identity"]["request_id"] = "fixture-runner-transaction-fresh-003"
        next_manifest["identity"]["expected_base"] = self.fixture.base
        with self.assertRaisesRegex(runner.TransactionError, "current pointer"):
            runner.Transaction(self.fixture.root, next_manifest).preflight()

    def test_result_write_refuses_symlinked_runtime_parent(self) -> None:
        manifest = runner.load_manifest(self.fixture.manifest())
        transaction = runner.Transaction(self.fixture.root, manifest)
        external = self.fixture.root.parent / f"{self.fixture.root.name}-runtime-escape"
        external.mkdir()
        self.addCleanup(lambda: shutil.rmtree(external, ignore_errors=True))
        (self.fixture.root / "output").symlink_to(external, target_is_directory=True)
        error = runner.TransactionError("RTX-FIXTURE", "fixture", "result", runner.EXIT_INTERNAL)
        with self.assertRaisesRegex(runner.TransactionError, "symlinks are forbidden"):
            transaction.write_result(transaction.result("failed", error))
        self.assertEqual(list(external.iterdir()), [])

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
        original_create = runner._atomic_create

        def flaky_create(path: Path, data: bytes, mode: Optional[int] = None) -> None:
            if path.name == "result.json":
                value = json.loads(data.decode("utf-8"))
                if value["verdict"] in {"passed", "failed"}:
                    raise OSError("injected result storage failure")
            original_create(path, data, mode)

        output = io.StringIO()
        with mock.patch.object(runner, "_atomic_create", side_effect=flaky_create), contextlib.redirect_stdout(output):
            status = transaction.execute()
        self.assertEqual(status, runner.EXIT_BOOKKEEPING)
        self.assertTrue((self.fixture.root / CLAIM_PATH).exists())
        self.assertFalse(transaction.result_path.exists())
        journal = json.loads(transaction.journal_path.read_text(encoding="utf-8"))
        self.assertEqual(journal["state"], "writing-terminal-result")
        self.assertFalse(journal["claim_finalized"])

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
        with self.assertRaisesRegex(runner.TransactionError, "requires at least one output path"):
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
        self.assertEqual(transaction.execute(), runner.EXIT_PREFLIGHT)
        self.assertFalse(transaction.journal_path.exists())
        self.assertFalse(transaction.result_path.exists())
        self.assertFalse(transaction.current_pointer_path.exists())
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
        self.assertEqual(journal["state"], "complete")
        self.assertEqual(result["verdict"], "failed")
        self.assertEqual(result["error"]["rule"], "RTX-TERMINATED-SIGNAL")
        pointer = json.loads(transaction.current_pointer_path.read_text(encoding="utf-8"))
        self.assertEqual(pointer["request_id"], REQUEST_ID)
        self.assertEqual(pointer["verdict"], "failed")

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

    def _write_recovery_journal(self, *, published: bool, state: str = "outputs-promoted") -> Path:
        log_dir = self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / "transaction-journal.json"
        path.write_text(
            json.dumps(
                {
                    "schema": runner.TRANSACTION_JOURNAL_SCHEMA,
                    "state": state,
                    "task_id": "0038-01",
                    "request_id": REQUEST_ID,
                    "owner_token": OWNER_TOKEN,
                    "claim_path": CLAIM_PATH,
                    "manifest_path": "request.json",
                    "manifest_sha256": "1" * 64,
                    "contract_sha256": "2" * 64,
                    "claim_preimage_sha256": hashlib.sha256((self.fixture.root / CLAIM_PATH).read_bytes()).hexdigest(),
                    "expected_base": self.fixture.base,
                    "branch_ref": "refs/heads/main",
                    "substantive_commit": self.fixture.base,
                    "bookkeeping_commit": None,
                    "published": published,
                    "claim_finalized": False,
                }
            ),
            encoding="utf-8",
        )
        if published:
            result_path = log_dir / "result.json"
            result = {
                "schema": runner.RESULT_SCHEMA,
                "task_id": "0038-01",
                "request_id": REQUEST_ID,
                "owner_token": OWNER_TOKEN,
                "expected_base": self.fixture.base,
                "base_observed": self.fixture.base,
                "authority_observed": dict(AUTHORITY),
                "manifest_path": "request.json",
                "manifest_sha256": "1" * 64,
                "contract_sha256": "2" * 64,
                "started_at": "2026-08-19T00:00:00Z",
                "finished_at": "2026-08-19T00:00:01Z",
                "verdict": "passed",
                "lifecycle_state": "complete",
                "phase": "complete",
                "phases": [],
                "actions": [],
                "findings": [],
                "substantive_commit": self.fixture.base,
                "bookkeeping_commit": None,
                "published": True,
                "claim_finalized": True,
                "paths": {"counts": {}, "preflight": {}, "promoted": {}},
                "commits": {"substantive": self.fixture.base, "bookkeeping": None, "final": self.fixture.base},
                "cleanup": {"claim_finalized": True, "journal_state": "complete"},
                "evidence": {"journal": "output/logs/0038-01/fixture-runner-transaction-001/transaction-journal.json"},
                "changed_path_count": 0,
                "promotion_backups_retained": False,
                "error": None,
                "recovery": "none",
            }
            result_bytes = runner._json_bytes(result)
            runner._atomic_write(result_path, result_bytes, 0o600)
            pointer = {
                "schema": runner.CURRENT_POINTER_SCHEMA,
                "task_id": "0038-01",
                "request_id": REQUEST_ID,
                "result_path": result_path.relative_to(self.fixture.root).as_posix(),
                "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
                "verdict": "passed",
                "lifecycle_state": "complete",
                "updated_at": "2026-08-19T00:00:00Z",
            }
            runner._atomic_write(log_dir.parent / "current.json", runner._json_bytes(pointer), 0o600)
        return path

    def test_recover_reports_deterministic_unpublished_plan(self) -> None:
        self._write_recovery_journal(published=False)
        recovery = runner.recover_transaction(self.fixture.root, REQUEST_ID)
        self.assertEqual(recovery["status"], "retry-required")
        self.assertEqual(recovery["prior_state"], "outputs-promoted")
        self.assertEqual(recovery["claim_path"], CLAIM_PATH)
        self.assertIn("fresh request ID", recovery["recommendation"])

    def test_recover_rejects_ambiguous_request_journals(self) -> None:
        journal = self._write_recovery_journal(published=False)
        duplicate = self.fixture.root / "output" / "logs" / "0038-99" / REQUEST_ID / "transaction-journal.json"
        duplicate.parent.mkdir(parents=True)
        shutil.copyfile(journal, duplicate)
        with self.assertRaisesRegex(runner.TransactionError, "multiple transaction journals"):
            runner.recover_transaction(self.fixture.root, REQUEST_ID)

    def test_finalize_claim_standalone_archives_only_exact_published_claim(self) -> None:
        journal = self._write_recovery_journal(published=True, state="published-pending-finalization")
        claim = self.fixture.root / CLAIM_PATH
        competing = self.fixture.root / "TODO-other-0038-01-other-request.md"
        competing.write_text(
            "task_id: 0038-01\nrequest_id: other-request\nowner_token: other-owner\n",
            encoding="utf-8",
        )
        self.assertTrue(runner.finalize_claim_standalone(self.fixture.root, "0038-01", REQUEST_ID))
        archive = journal.parent / "finalized-claim.md"
        self.assertFalse(claim.exists())
        self.assertTrue(archive.exists())
        self.assertTrue(competing.exists())
        updated = json.loads(journal.read_text(encoding="utf-8"))
        self.assertTrue(updated["claim_finalized"])
        self.assertEqual(updated["state"], "complete")
        self.assertFalse(runner.finalize_claim_standalone(self.fixture.root, "0038-01", REQUEST_ID))

    def test_finalize_claim_refuses_unpublished_or_locked_request(self) -> None:
        self._write_recovery_journal(published=False)
        with self.assertRaisesRegex(runner.TransactionError, "does not prove successful"):
            runner.finalize_claim_standalone(self.fixture.root, "0038-01", REQUEST_ID)
        self._write_recovery_journal(published=True)
        git_dir = Path(self.fixture.git_text("rev-parse", "--git-dir"))
        if not git_dir.is_absolute():
            git_dir = self.fixture.root / git_dir
        lock = git_dir / "autodocs-runner-transaction.lock"
        claim_before = (self.fixture.root / CLAIM_PATH).read_bytes()
        journal_before = (self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID / "transaction-journal.json").read_bytes()
        pointer_before = (self.fixture.root / "output" / "logs" / "0038-01" / "current.json").read_bytes()
        lock.write_text(json.dumps({"pid": os.getpid(), "request_id": REQUEST_ID}), encoding="utf-8")
        with self.assertRaisesRegex(runner.TransactionError, "never deletes or bypasses"):
            runner.finalize_claim_standalone(self.fixture.root, "0038-01", REQUEST_ID)
        self.assertEqual((self.fixture.root / CLAIM_PATH).read_bytes(), claim_before)
        self.assertEqual((self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID / "transaction-journal.json").read_bytes(), journal_before)
        self.assertEqual((self.fixture.root / "output" / "logs" / "0038-01" / "current.json").read_bytes(), pointer_before)

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
        with self.assertRaisesRegex(runner.TransactionError, "found 1 match"):
            runner.render_task_closure(
                "## Feature: 0038 — Fixture\n\n"
                "- [ ] **0038-01** Not active.\n  - **Definition of Done:** No.\n",
                "0038-01",
                "1" * 40,
                REQUEST_ID,
                "No closure.",
            )

    def test_structural_closure_rejects_duplicate_task_id(self) -> None:
        with self.assertRaisesRegex(runner.TransactionError, "found 2 match"):
            runner.render_task_closure(
                "## Feature: 0038 — Fixture\n\n"
                "- [p] **0038-01** First copy.\n  - **Definition of Done:** One.\n\n"
                "- [p] **0038-01** Second copy.\n  - **Definition of Done:** Two.\n",
                "0038-01",
                "1" * 40,
                REQUEST_ID,
                "No closure.",
            )

    def test_structural_closure_uses_backlog_parser_not_a_second_regex(self) -> None:
        # The renderer now delegates Task/Feature/section boundary detection
        # to legacy_task_editor.parse_backlog (Task 0038-05.01) instead of a
        # duplicate ad hoc regex Task-boundary detector.
        revised = runner.render_task_closure(
            "## Feature: 0038 — Fixture\n\n"
            "- [p] **0038-01** Exercise the transaction.\n"
            "  - **Acceptance criteria:** Fail closed.\n"
            "  - **Definition of Done:** Two commits and exact cleanup.\n\n"
            "- [ ] **0038-02** Preserve this neighboring Task.\n"
            "  - **Definition of Done:** It remains separate.\n",
            "0038-01",
            "2" * 40,
            REQUEST_ID,
            "The fixture transaction completed all fail-closed gates.",
        )
        self.assertIn("- [x] **0038-01**", revised)
        self.assertIn(f"REF: {'2' * 40}", revised)
        self.assertIn("- [ ] **0038-02**", revised)
        self.assertNotIn("- [p] **0038-01**", revised)

    # ------------------------------------------------------------------
    # verify-and-commit-v1 profile tests
    # ------------------------------------------------------------------

    def _verify_and_commit_manifest(self) -> Path:
        """Minimal verify-and-commit-v1 manifest with required Task bookkeeping."""
        base = self.fixture.base
        value: Dict[str, Any] = {
            "schema": runner.MANIFEST_SCHEMA,
            "profile": runner.VERIFY_AND_COMMIT_PROFILE,
            "identity": {
                "task_id": "0038-01",
                "request_id": REQUEST_ID,
                "owner_token": OWNER_TOKEN,
                "claim_path": CLAIM_PATH,
                "manifest_path": "request.json",
                "expected_base": base,
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
                "output_paths": [],
                "substantive_paths": ["source.txt"],
            },
            "actions": [
                {"id": "validate-project", "timeout_seconds": 30, "reports": []},
            ],
            "commit": {
                "substantive_message": (
                    "feat(0038-01): verify-and-commit fixture\n\n"
                    "User-Prompt-Provenance:\n"
                    "Exercise the verify-and-commit-v1 profile."
                )
            },
            "bookkeeping": {
                "todo_path": "TODO.md",
                "closure_text": "The verify-and-commit fixture completed all fail-closed gates.",
                "commit_message": "docs(todo): close verify-and-commit fixture Task 0038-01",
            },
        }
        # Also update the claim file's profile field to the new profile so
        # claim_contract_fields matches what's written to disk.
        claim_path = self.fixture.root / CLAIM_PATH
        claim_text = claim_path.read_text(encoding="utf-8")
        claim_text = claim_text.replace(
            f"transaction_profile: {runner.PROFILE}",
            f"transaction_profile: {runner.VERIFY_AND_COMMIT_PROFILE}",
        )
        claim_path.write_text(claim_text, encoding="utf-8")
        return self.fixture.store_manifest(value)

    def test_verify_and_commit_requires_bookkeeping_and_synchronizes_worktree(self) -> None:
        """verify-and-commit-v1 closes the Task and matches declared paths to published commits."""
        base = self.fixture.base
        path = self._verify_and_commit_manifest()
        manifest = runner.load_manifest(path)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = runner.Transaction(self.fixture.root, manifest).execute()
        self.assertEqual(status, 0, output.getvalue())
        new_head = self.fixture.base
        self.assertNotEqual(new_head, base)
        # A substantive commit and parented bookkeeping commit must be published.
        commit_count = int(
            self.fixture.git_text("rev-list", "--count", f"{base}..{new_head}")
        )
        self.assertEqual(commit_count, 2)
        todo_after = (self.fixture.root / "TODO.md").read_text(encoding="utf-8")
        self.assertIn("- [x] **0038-01**", todo_after)
        self.assertEqual(
            self.fixture.git_text("show", f"{new_head}:source.txt"),
            (self.fixture.root / "source.txt").read_text(encoding="utf-8").rstrip("\n"),
        )
        self.assertEqual(
            self.fixture.git_text("show", f"{new_head}:TODO.md"),
            todo_after.rstrip("\n"),
        )
        # Claim must have been finalized (moved to log dir, not in worktree).
        self.assertFalse((self.fixture.root / CLAIM_PATH).exists())
        result_path = self.fixture.root / "output" / "logs" / "0038-01" / REQUEST_ID / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual(result["verdict"], "passed")
        self.assertIsNotNone(result["substantive_commit"])
        self.assertRegex(result["bookkeeping_commit"], r"^[0-9a-f]{40}$")

    def test_verify_and_commit_profile_rejects_omitted_bookkeeping(self) -> None:
        """A Task-closing verify profile must never publish without marker bookkeeping."""
        path = self._verify_and_commit_manifest()
        value = json.loads(path.read_text(encoding="utf-8"))
        value.pop("bookkeeping")
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(runner.TransactionError) as cm:
            runner.load_manifest(path)
        self.assertEqual(cm.exception.rule, "RTX-SCHEMA-TYPE")
        self.assertIn("bookkeeping must be an object", cm.exception.message)

    def test_verify_and_commit_profile_rejects_missing_commit(self) -> None:
        """verify-and-commit-v1 without a commit block must fail manifest validation."""
        base = self.fixture.base
        value: Dict[str, Any] = {
            "schema": runner.MANIFEST_SCHEMA,
            "profile": runner.VERIFY_AND_COMMIT_PROFILE,
            "identity": {
                "task_id": "0038-01",
                "request_id": REQUEST_ID,
                "owner_token": OWNER_TOKEN,
                "claim_path": CLAIM_PATH,
                "manifest_path": "request.json",
                "expected_base": base,
            },
            "authority": {
                "selector_path": "agent-workflow.json",
                "authority_epoch": AUTHORITY["authority_epoch"],
                "authority_profile": AUTHORITY["authority_profile"],
                "write_phase": AUTHORITY["write_phase"],
                "runner_protocol": AUTHORITY["runner_protocol"],
            },
            "scope": {
                "read_paths": [],
                "input_paths": ["source.txt"],
                "output_paths": [],
                "substantive_paths": ["source.txt"],
            },
            "actions": [
                {"id": "validate-project", "timeout_seconds": 30, "reports": []},
            ],
            # No "commit" key — must be rejected.
        }
        path = self.fixture.root / "request.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(runner.TransactionError) as cm:
            runner.load_manifest(path)
        self.assertEqual(cm.exception.rule, "RTX-SCHEMA-TYPE")
        self.assertIn("commit must be an object", cm.exception.message)


EDITOR_TASK_ID = "0038-01"
EDITOR_FEATURE_ID = "0038"
EDITOR_REQUEST_ID = "fixture-editor-transaction-001"
EDITOR_OWNER_TOKEN = f"agent:test:{EDITOR_TASK_ID}:{EDITOR_REQUEST_ID}"
EDITOR_RUNNER_CLAIM_PATH = f"TODO-test-{EDITOR_TASK_ID}-{EDITOR_REQUEST_ID}.md"
TARGET_CLAIM_PATH = f"TODO-alpha-{EDITOR_TASK_ID}-req-alpha-001.md"
TARGET_CLAIM_OWNER = f"agent:alpha:{EDITOR_TASK_ID}:req-alpha-001"
TARGET_CLAIM_BASE = "b" * 40
TARGET_TASK_REF = "a" * 40
ARCHIVE_PATH = "logs/claims/0038-01-final.md"


class EditorFixtureRepo:
    """A second, independent fixture Git repository exercising the new
    ``legacy-editor-candidate-v1`` profile: a real ``claim-finalization``
    operation planned and written to a candidate directory by the actual
    ``legacy_task_editor.py`` (Task 0038-05.01) code, then promoted by
    ``runner_transaction.py`` (Task 0038-05.02) through the same
    journal/lock/promote/rollback machinery as every other profile.
    """

    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="runner-transaction-editor-test-")
        # Resolved once, here, outside any adversarial context: on macOS the
        # OS temp root itself (/var) is a symlink to /private/var, and
        # legacy_task_editor's nofollow directory walk (by design) refuses to
        # traverse *any* symlink component, including that benign OS mount
        # alias. Resolving our own fixture root once is exactly what
        # Transaction.__init__ already does for the real repository root.
        self.root = Path(self.temporary.name).resolve()
        self._create_repository()

    def close(self) -> None:
        self.temporary.cleanup()

    def git(self, *args: str, check: bool = True, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess[bytes]:
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
        self.git("config", "user.name", "Editor Transaction Test")
        self.git("config", "user.email", "editor-transaction@example.invalid")
        (self.root / ".gitignore").write_text("output/\n", encoding="utf-8")
        (self.root / "agent-workflow.json").write_text(json.dumps(AUTHORITY), encoding="utf-8")
        self.todo_text = (
            "# TODO\n\n"
            "## Feature: 0038 — Fixture\n\n"
            f"- [x] **{EDITOR_TASK_ID}** Exercise the editor transaction. REF: {TARGET_TASK_REF}\n"
            "  - **Acceptance criteria:** Fail closed.\n"
            "  - **Definition of Done:** Two commits and exact cleanup.\n"
            f"  - **Claim (2026-08-17):** Claimed via `{TARGET_CLAIM_PATH}`, "
            f"`owner_token: {TARGET_CLAIM_OWNER}`, base `{TARGET_CLAIM_BASE}`.\n\n"
            "- [ ] **0038-02** Preserve this neighboring Task.\n"
            "  - **Definition of Done:** It remains separate.\n"
        )
        (self.root / "TODO.md").write_text(self.todo_text, encoding="utf-8")
        self.target_claim_text = (
            f"# {TARGET_CLAIM_PATH} — active claim\n\n"
            f"task_id: {EDITOR_TASK_ID}\n"
            "request_id: req-alpha-001\n"
            f"owner_token: {TARGET_CLAIM_OWNER}\n"
            f"base_commit: {TARGET_CLAIM_BASE}\n"
            "capability_class: sandboxed/grunt\n"
            "state: [p]\n"
        )
        (self.root / TARGET_CLAIM_PATH).write_text(self.target_claim_text, encoding="utf-8")
        (self.root / EDITOR_RUNNER_CLAIM_PATH).write_text(
            "# Fixture runner claim\n\n"
            f"task_id: {EDITOR_TASK_ID}\n"
            f"request_id: {EDITOR_REQUEST_ID}\n"
            f"owner_token: {EDITOR_OWNER_TOKEN}\n"
            "base_commit: PLACEHOLDER\n"
            f"transaction_profile: {runner.EDITOR_PROFILE}\n"
            "transaction_manifest: PLACEHOLDER_MANIFEST\n"
            "transaction_actions_json: PLACEHOLDER_ACTIONS\n"
            "transaction_authority_json: PLACEHOLDER_AUTHORITY\n"
            "transaction_commit_message_json: PLACEHOLDER_COMMIT_MESSAGE\n"
            "transaction_read_paths_json: PLACEHOLDER_READS\n"
            "transaction_write_paths_json: PLACEHOLDER_WRITES\n"
            "capability_class: sandboxed/grunt\n"
            "state: [p]\n",
            encoding="utf-8",
        )
        self.git(
            "add", "--",
            ".gitignore", "agent-workflow.json", "TODO.md", TARGET_CLAIM_PATH, EDITOR_RUNNER_CLAIM_PATH,
        )
        self.git("commit", "-m", "fixture: initial editor state")
        base = self.base
        claim = (self.root / EDITOR_RUNNER_CLAIM_PATH).read_text(encoding="utf-8").replace("PLACEHOLDER", base)
        (self.root / EDITOR_RUNNER_CLAIM_PATH).write_text(claim, encoding="utf-8")
        # Left uncommitted deliberately, matching FixtureRepo: the runner's own
        # coordination claim is live working-tree state, not a committed blob.

    def build_candidate(self, *, archive_path: str = ARCHIVE_PATH, tamper_todo: bool = False, tamper_claim: bool = False) -> Dict[str, Any]:
        """Plan and write a real claim-finalization candidate via legacy_task_editor."""
        sources = {
            "TODO.md": self.todo_text.encode("utf-8"),
            TARGET_CLAIM_PATH: self.target_claim_text.encode("utf-8"),
        }
        document = lte.parse_backlog("TODO.md", sources["TODO.md"])
        feature, task = lte._unique_task(document, EDITOR_FEATURE_ID, EDITOR_TASK_ID)
        feature_bytes = document.text[feature.span.start:feature.span.end].encode("utf-8")
        task_bytes = document.text[task.span.start:task.span.end].encode("utf-8")
        claim = lte.parse_claim(TARGET_CLAIM_PATH, sources[TARGET_CLAIM_PATH])
        operation_data = {
            "schema": lte.OPERATION_SCHEMA,
            "operation_id": "fixture-editor-finalize-001",
            "kind": "claim-finalization",
            "recorded_at": "2026-08-20T00:00:00Z",
            "subject": {"feature_id": EDITOR_FEATURE_ID, "task_id": EDITOR_TASK_ID},
            "actor": {"request_id": "req-alpha-001", "owner_token": TARGET_CLAIM_OWNER},
            "backlog": {
                "path": "TODO.md",
                "expected_document_sha256": lte._sha256(sources["TODO.md"]),
                "expected_feature_sha256": lte._sha256(feature_bytes),
                "expected_task_sha256": lte._sha256(task_bytes),
                "expected_marker": "x",
            },
            "claim": {
                "path": TARGET_CLAIM_PATH,
                "expected_document_sha256": lte._sha256(sources[TARGET_CLAIM_PATH]),
                "expected_task_id": claim.task_id,
                "expected_request_id": claim.request_id,
                "expected_owner_token": claim.owner_token,
                "expected_state": claim.state,
            },
            "payload": {"archive_path": archive_path},
        }
        raw = (json.dumps(operation_data, sort_keys=True) + "\n").encode("utf-8")
        operation = lte.load_operation(raw)
        # Use the exact same source-gathering primitive verify_candidate_for_promotion
        # will use on re-plan (it globs every TODO-*.md, including the runner's
        # own coordination claim), so the candidate's embedded read_set matches
        # byte-for-byte what a fresh re-verification will observe.
        sources = lte._load_sources(self.root, operation)
        plan = lte.plan_operation(operation, sources)
        candidate_dir = self.root / "output" / "editor-candidates" / "fixture-editor-finalize-001"
        receipt = lte.write_candidate(plan, candidate_dir)
        operation_path = self.root / "output" / "editor-candidates" / "fixture-editor-finalize-001.operation.json"
        operation_path.write_bytes(raw)
        if tamper_todo:
            (self.root / "TODO.md").write_text(self.todo_text + "\nUnrelated concurrent note.\n", encoding="utf-8")
        if tamper_claim:
            (self.root / TARGET_CLAIM_PATH).write_text(self.target_claim_text + "\nUnrelated concurrent note.\n", encoding="utf-8")
        return {
            "operation_path": operation_path.relative_to(self.root).as_posix(),
            "candidate_dir": candidate_dir.relative_to(self.root).as_posix(),
            "candidate_manifest_path": (candidate_dir / receipt.manifest_path).relative_to(self.root).as_posix(),
            "expected_candidate_sha256": receipt.manifest_sha256,
            "output_paths": sorted({change.path for change in plan.changes}),
        }

    def _manifest_value(self, editor_info: Dict[str, Any], *, output_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        resolved_output_paths = output_paths if output_paths is not None else editor_info["output_paths"]
        return {
            "schema": runner.MANIFEST_SCHEMA,
            "profile": runner.EDITOR_PROFILE,
            "identity": {
                "task_id": EDITOR_TASK_ID,
                "request_id": EDITOR_REQUEST_ID,
                "owner_token": EDITOR_OWNER_TOKEN,
                "claim_path": EDITOR_RUNNER_CLAIM_PATH,
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
                "read_paths": [],
                "input_paths": [],
                "output_paths": resolved_output_paths,
                "substantive_paths": resolved_output_paths,
            },
            "actions": [],
            "commit": {
                "substantive_message": (
                    f"chore({EDITOR_TASK_ID}): fixture editor-candidate promotion\n\n"
                    "User-Prompt-Provenance:\n"
                    "Exercise the legacy-editor-candidate-v1 transaction fixture verbatim."
                )
            },
            "editor": {
                "operation_path": editor_info["operation_path"],
                "candidate_dir": editor_info["candidate_dir"],
                "candidate_manifest_path": editor_info["candidate_manifest_path"],
                "expected_candidate_sha256": editor_info["expected_candidate_sha256"],
            },
        }

    def _sync_runner_claim(self, value: Dict[str, Any]) -> None:
        """Sync the runner's own coordination claim's contract fields.

        This must happen before ``build_candidate`` plans anything, because
        the candidate's embedded read_set is checked byte-for-byte against a
        fresh ``legacy_task_editor._load_sources`` glob of every ``TODO-*.md``
        file — including this repo's own coordination claim.
        ``claim_contract_fields`` never reads the manifest's ``editor`` block,
        so this sync only needs identity/authority/scope/commit to already be
        final; a structurally-correct placeholder ``editor`` block is enough.
        """
        claim_path = self.root / EDITOR_RUNNER_CLAIM_PATH
        claim = claim_path.read_text(encoding="utf-8")
        for key, expected in runner.claim_contract_fields(value).items():
            claim = re.sub(
                rf"^{re.escape(key)}: .+$",
                lambda _match, key=key, expected=expected: f"{key}: {expected}",
                claim,
                flags=re.MULTILINE,
            )
        claim_path.write_text(claim, encoding="utf-8")

    def write_manifest(self, editor_info: Dict[str, Any]) -> Path:
        """Write a request.json for schema-only tests that never execute a
        real Transaction (so the runner claim need not be pre-synced)."""
        path = self.root / "request.json"
        path.write_text(json.dumps(self._manifest_value(editor_info), indent=2), encoding="utf-8")
        return path

    def prepare(self, *, output_paths: Optional[List[str]] = None, **build_kwargs: Any) -> Dict[str, Any]:
        """Sync the runner's own claim to its final contract fields for the
        given declared output_paths, THEN plan the candidate -- so the
        candidate's embedded read_set matches exactly what a fresh
        re-verification will observe. Order matters here: see
        ``_sync_runner_claim``.
        """
        resolved_output_paths = output_paths if output_paths is not None else sorted({"TODO.md", TARGET_CLAIM_PATH, ARCHIVE_PATH})
        placeholder_editor_info = {
            "operation_path": "output/editor-candidates/fixture-editor-finalize-001.operation.json",
            "candidate_dir": "output/editor-candidates/fixture-editor-finalize-001",
            "candidate_manifest_path": "output/editor-candidates/fixture-editor-finalize-001/candidate.json",
            "expected_candidate_sha256": "0" * 64,
            "output_paths": resolved_output_paths,
        }
        self._sync_runner_claim(self._manifest_value(placeholder_editor_info, output_paths=output_paths))
        return self.build_candidate(**build_kwargs)

    def execute(
        self,
        *,
        editor_info: Optional[Dict[str, Any]] = None,
        output_paths: Optional[List[str]] = None,
        inject_failure: Optional[str] = None,
    ) -> tuple[int, str, Dict[str, Any]]:
        if editor_info is None:
            editor_info = self.prepare(output_paths=output_paths)
        path = self.root / "request.json"
        path.write_text(json.dumps(self._manifest_value(editor_info, output_paths=output_paths), indent=2), encoding="utf-8")
        manifest = runner.load_manifest(path)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = runner.Transaction(self.root, manifest, inject_failure=inject_failure).execute()
        return status, output.getvalue(), editor_info


class EditorCandidateTransactionTests(unittest.TestCase):
    """Failure-injection coverage for the legacy-editor-candidate-v1 profile:
    the fixed typed action/contract that integrates 0038-05.01's structural
    editor candidate promotion into the 0038-02 durable transaction
    coordinator's journal/lock/promote/rollback guarantees.
    """

    _fixture: Optional[EditorFixtureRepo] = None

    @property
    def fixture(self) -> EditorFixtureRepo:
        assert self._fixture is not None
        return self._fixture

    def setUp(self) -> None:
        self._fixture = EditorFixtureRepo()
        self.addCleanup(self.fixture.close)

    def _result(self) -> Dict[str, Any]:
        path = self.fixture.root / "output" / "logs" / EDITOR_TASK_ID / EDITOR_REQUEST_ID / "result.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_success_promotes_todo_and_claim_archive_delete_in_one_commit(self) -> None:
        base = self.fixture.base
        status, output, _info = self.fixture.execute()
        self.assertEqual(status, 0, output)
        new_head = self.fixture.base
        self.assertNotEqual(new_head, base)
        commit_count = int(self.fixture.git_text("rev-list", "--count", f"{base}..{new_head}"))
        self.assertEqual(commit_count, 1, "editor-candidate transactions land exactly one substantive commit")

        todo_after = (self.fixture.root / "TODO.md").read_text(encoding="utf-8")
        self.assertNotIn(f"Claimed via `{TARGET_CLAIM_PATH}`", todo_after)
        self.assertIn("Claim finalized", todo_after)
        self.assertIn(f"- [x] **{EDITOR_TASK_ID}**", todo_after)
        self.assertFalse((self.fixture.root / TARGET_CLAIM_PATH).exists(), "the finalized claim must be deleted")
        self.assertTrue((self.fixture.root / ARCHIVE_PATH).exists(), "the archive copy must be created")
        self.assertEqual(
            (self.fixture.root / ARCHIVE_PATH).read_bytes(),
            self.fixture.target_claim_text.encode("utf-8"),
        )
        # The runner's own coordination claim is archived after success too.
        self.assertFalse((self.fixture.root / EDITOR_RUNNER_CLAIM_PATH).exists())

        result = self._result()
        self.assertEqual(result["verdict"], "passed")
        self.assertIsNotNone(result["substantive_commit"])
        self.assertIsNone(result["bookkeeping_commit"])
        # The CAS-guarded current pointer must validate against the immutable result.
        pointer = json.loads((self.fixture.root / "output" / "logs" / EDITOR_TASK_ID / "current.json").read_text(encoding="utf-8"))
        self.assertEqual(pointer["verdict"], "passed")
        self.assertEqual(runner._current_pointer_status(self.fixture.root, EDITOR_TASK_ID)["status"], "valid")

    def test_manifest_rejects_actions_for_editor_profile(self) -> None:
        editor_info = self.fixture.build_candidate()
        path = self.fixture.write_manifest(editor_info)
        value = json.loads(path.read_text(encoding="utf-8"))
        value["actions"] = [{"id": "validate-project", "timeout_seconds": 30, "reports": []}]
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(runner.TransactionError) as cm:
            runner.load_manifest(path)
        self.assertEqual(cm.exception.rule, "RTX-EDITOR-ACTIONS")

    def test_manifest_rejects_bookkeeping_for_editor_profile(self) -> None:
        editor_info = self.fixture.build_candidate()
        path = self.fixture.write_manifest(editor_info)
        value = json.loads(path.read_text(encoding="utf-8"))
        value["bookkeeping"] = {
            "todo_path": "TODO.md",
            "commit_message": "docs(todo): close",
            "closure_text": "Closed.",
        }
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(runner.TransactionError) as cm:
            runner.load_manifest(path)
        self.assertEqual(cm.exception.rule, "RTX-EDITOR-BOOKKEEPING")

    def test_manifest_rejects_substantive_output_mismatch(self) -> None:
        editor_info = self.fixture.build_candidate()
        path = self.fixture.write_manifest(editor_info)
        value = json.loads(path.read_text(encoding="utf-8"))
        value["scope"]["substantive_paths"] = value["scope"]["substantive_paths"][:-1]
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(runner.TransactionError) as cm:
            runner.load_manifest(path)
        self.assertEqual(cm.exception.rule, "RTX-SCOPE-SUBSTANTIVE-MISMATCH")

    def test_editor_field_rejected_for_other_profiles(self) -> None:
        editor_info = self.fixture.build_candidate()
        path = self.fixture.write_manifest(editor_info)
        value = json.loads(path.read_text(encoding="utf-8"))
        value["profile"] = runner.VERIFY_AND_COMMIT_PROFILE
        value["actions"] = [{"id": "validate-project", "timeout_seconds": 30, "reports": []}]
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(runner.TransactionError) as cm:
            runner.load_manifest(path)
        self.assertEqual(cm.exception.rule, "RTX-EDITOR-UNEXPECTED")

    def test_preflight_rejects_tampered_candidate_digest(self) -> None:
        editor_info = self.fixture.prepare()
        editor_info["expected_candidate_sha256"] = "1" * 64
        status, output, _info = self.fixture.execute(editor_info=editor_info)
        self.assertEqual(status, runner.EXIT_PREFLIGHT)
        self.assertIn("RTX-EDITOR-LTE-CANDIDATE-TAMPERED", output)
        self.assertTrue((self.fixture.root / TARGET_CLAIM_PATH).exists(), "no candidate file may be touched before a rejected preflight")
        self.assertFalse((self.fixture.root / ARCHIVE_PATH).exists())

    def test_preflight_rejects_todo_drift_after_candidate_was_planned(self) -> None:
        editor_info = self.fixture.prepare(tamper_todo=True)
        status, output, _info = self.fixture.execute(editor_info=editor_info)
        self.assertEqual(status, runner.EXIT_PREFLIGHT)
        self.assertIn("RTX-EDITOR-LTE-", output)
        self.assertTrue((self.fixture.root / TARGET_CLAIM_PATH).exists())
        self.assertFalse((self.fixture.root / ARCHIVE_PATH).exists())

    def test_preflight_rejects_claim_drift_after_candidate_was_planned(self) -> None:
        editor_info = self.fixture.prepare(tamper_claim=True)
        status, output, _info = self.fixture.execute(editor_info=editor_info)
        self.assertEqual(status, runner.EXIT_PREFLIGHT)
        self.assertIn("RTX-EDITOR-LTE-", output)
        self.assertFalse((self.fixture.root / ARCHIVE_PATH).exists())

    def test_preflight_rejects_declared_scope_narrower_than_candidate(self) -> None:
        narrowed = sorted({"TODO.md", TARGET_CLAIM_PATH, ARCHIVE_PATH} - {ARCHIVE_PATH})
        editor_info = self.fixture.prepare(output_paths=narrowed)
        status, output, _info = self.fixture.execute(editor_info=editor_info, output_paths=narrowed)
        self.assertEqual(status, runner.EXIT_PREFLIGHT)
        self.assertIn("RTX-EDITOR-SCOPE-MISMATCH", output)
        self.assertTrue((self.fixture.root / TARGET_CLAIM_PATH).exists())
        self.assertFalse((self.fixture.root / ARCHIVE_PATH).exists())

    def test_injected_failure_before_materialize_leaves_root_untouched(self) -> None:
        status, output, _info = self.fixture.execute(inject_failure="before-editor-materialize")
        self.assertEqual(status, runner.EXIT_INTERNAL)
        self.assertIn("RTX-INJECTED-FAILURE", output)
        self.assertTrue((self.fixture.root / TARGET_CLAIM_PATH).exists())
        self.assertEqual((self.fixture.root / TARGET_CLAIM_PATH).read_bytes(), self.fixture.target_claim_text.encode("utf-8"))
        self.assertFalse((self.fixture.root / ARCHIVE_PATH).exists())
        self.assertEqual((self.fixture.root / "TODO.md").read_text(encoding="utf-8"), self.fixture.todo_text)
        self.assertTrue((self.fixture.root / EDITOR_RUNNER_CLAIM_PATH).exists(), "the runner's own claim must survive an unpublished failure")

    def test_injected_failure_during_promote_rolls_back_the_files_promoted_so_far(self) -> None:
        # "during-promote" fires right after the first (alphabetically
        # earliest) output is written, before the rest of the loop runs.
        status, output, _info = self.fixture.execute(inject_failure="during-promote")
        self.assertEqual(status, runner.EXIT_INTERNAL)
        self.assertIn("RTX-INJECTED-FAILURE", output)
        self.assertEqual((self.fixture.root / "TODO.md").read_text(encoding="utf-8"), self.fixture.todo_text)
        self.assertTrue((self.fixture.root / TARGET_CLAIM_PATH).exists())
        self.assertEqual((self.fixture.root / TARGET_CLAIM_PATH).read_bytes(), self.fixture.target_claim_text.encode("utf-8"))
        self.assertFalse((self.fixture.root / ARCHIVE_PATH).exists(), "a partially promoted create must be rolled back")
        self.assertTrue((self.fixture.root / EDITOR_RUNNER_CLAIM_PATH).exists(), "no partial claim state may be exposed on rollback")
        journal_path = (
            self.fixture.root / "output" / "logs" / EDITOR_TASK_ID / EDITOR_REQUEST_ID / "promotion-journal.json"
        )
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        self.assertEqual(journal["status"], "rolled-back")

    def test_injected_failure_after_promote_rolls_back_every_file(self) -> None:
        # "after-promote" fires once ALL three outputs (TODO.md replace, the
        # target claim delete, the archive create) have already been written
        # to the root worktree but before the substantive commit exists, so
        # this proves the multi-file rollback covers every touched path, not
        # just the first one.
        status, output, _info = self.fixture.execute(inject_failure="after-promote")
        self.assertEqual(status, runner.EXIT_INTERNAL)
        self.assertIn("RTX-INJECTED-FAILURE", output)
        self.assertEqual((self.fixture.root / "TODO.md").read_text(encoding="utf-8"), self.fixture.todo_text)
        self.assertTrue((self.fixture.root / TARGET_CLAIM_PATH).exists())
        self.assertEqual((self.fixture.root / TARGET_CLAIM_PATH).read_bytes(), self.fixture.target_claim_text.encode("utf-8"))
        self.assertFalse((self.fixture.root / ARCHIVE_PATH).exists(), "the fully-promoted create must still be rolled back")
        self.assertTrue((self.fixture.root / EDITOR_RUNNER_CLAIM_PATH).exists(), "no partial claim state may be exposed on rollback")
        journal_path = (
            self.fixture.root / "output" / "logs" / EDITOR_TASK_ID / EDITOR_REQUEST_ID / "promotion-journal.json"
        )
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        self.assertEqual(journal["status"], "rolled-back")
        self.assertEqual({entry["path"] for entry in journal["entries"]}, {"TODO.md", TARGET_CLAIM_PATH, ARCHIVE_PATH})
        result_path = self.fixture.root / "output" / "logs" / EDITOR_TASK_ID / EDITOR_REQUEST_ID / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertNotEqual(result["verdict"], "passed")

    def test_injected_failure_after_publish_retains_claim_for_recovery(self) -> None:
        # "after-publish" fires once the substantive commit is already the
        # exact CAS-guarded branch tip: files are not rolled back (the
        # commit is real), but the runner's own claim must survive for
        # deterministic recovery instead of being finalized/archived.
        base = self.fixture.base
        status, output, _info = self.fixture.execute(inject_failure="after-publish")
        self.assertEqual(status, runner.EXIT_INTERNAL)
        self.assertIn("RTX-INJECTED-FAILURE", output)
        self.assertNotEqual(self.fixture.base, base)
        self.assertTrue((self.fixture.root / EDITOR_RUNNER_CLAIM_PATH).exists())
        self.assertFalse((self.fixture.root / TARGET_CLAIM_PATH).exists(), "the promoted claim-finalization itself is already committed")


# ---------------------------------------------------------------------------
# branch-merge-v1: base-branch / merge-prereqs typed actions (Task 0038-20,
# implementing the docs/pipeline/branch-merge-actions.md contract from Task
# 0038-19 on top of this file's existing lock/journal/commit machinery).
# ---------------------------------------------------------------------------


class BranchMergeFixtureRepo:
    """A real Git repository with a Feature branch and two prerequisite branches.

    Topology: ``main`` == Feature branch ``9000`` == commit R. Two prerequisite
    branches, ``9000-02`` (adds ``work-02.txt``) and ``9000-03`` (adds
    ``work-03.txt``), are branched off ``9000``. Individual tests create their
    own item branch (typically ``9000-01``) off ``9000`` and exercise
    ``base-branch``/``merge-prereqs`` against it.
    """

    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="runner-transaction-bma-test-")
        self.root = Path(self.temporary.name)
        self._create_repository()

    def close(self) -> None:
        self.temporary.cleanup()

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        env = os.environ.copy()
        env["GIT_EDITOR"] = "true"
        return subprocess.run(
            ["git", "--no-pager", *args],
            cwd=str(self.root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )

    def git_text(self, *args: str) -> str:
        return self.git(*args).stdout.decode("utf-8", "replace").strip()

    def tip(self, branch: str) -> str:
        return self.git_text("rev-parse", f"refs/heads/{branch}")

    def current_branch(self) -> str:
        return self.git_text("symbolic-ref", "--quiet", "HEAD")

    def sha256(self, relative: str) -> str:
        return hashlib.sha256((self.root / relative).read_bytes()).hexdigest()

    def _write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _create_repository(self) -> None:
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Runner Transaction Branch Test")
        self.git("config", "user.email", "runner-transaction-branch@example.invalid")
        self._write(".gitignore", "output/\n")
        self._write("agent-workflow.json", json.dumps(AUTHORITY))
        self._write(
            "TODO.md",
            "# TODO\n\n"
            "## Feature: 9000 — BMA fixture\n\n"
            "- [ ] **9000** BMA fixture Feature.\n\n"
            "- [p] **9000-01** BMA fixture Task.\n\n"
            "- [x] **9000-02** BMA fixture prerequisite one.\n\n"
            "- [x] **9000-03** BMA fixture prerequisite two.\n",
        )
        self._write("unrelated.txt", "unrelated-base\n")
        self.git(
            "add", "--",
            ".gitignore", "agent-workflow.json", "TODO.md", "unrelated.txt",
        )
        self.git("commit", "-m", "fixture: initial state")
        self.root_tip = self.git_text("rev-parse", "HEAD")

        self.git("branch", "9000")

        self.git("checkout", "-b", "9000-02", "9000")
        self._write("work-02.txt", "work-02\n")
        self.git("add", "--", "work-02.txt")
        self.git("commit", "-m", "fixture: prerequisite 9000-02 work product")

        self.git("checkout", "9000")
        self.git("checkout", "-b", "9000-03", "9000")
        self._write("work-03.txt", "work-03\n")
        self.git("add", "--", "work-03.txt")
        self.git("commit", "-m", "fixture: prerequisite 9000-03 work product")

        self.git("checkout", "9000")

    # -- manifest/claim helpers -------------------------------------------------

    @staticmethod
    def claim_template() -> str:
        return (
            "# Fixture claim\n\n"
            "task_id: PLACEHOLDER\n"
            "request_id: PLACEHOLDER\n"
            "owner_token: PLACEHOLDER\n"
            "base_commit: PLACEHOLDER\n"
            "transaction_profile: PLACEHOLDER\n"
            "transaction_manifest: PLACEHOLDER\n"
            "transaction_actions_json: PLACEHOLDER\n"
            "transaction_authority_json: PLACEHOLDER\n"
            "transaction_read_paths_json: PLACEHOLDER\n"
            "transaction_write_paths_json: PLACEHOLDER\n"
            "transaction_branch_json: PLACEHOLDER\n"
            "capability_class: unprivileged\n"
            "state: [p]\n"
        )

    def write_claim(self, claim_path: str, manifest: Dict[str, Any]) -> None:
        lines = []
        expected_fields = runner.claim_contract_fields(manifest)
        for line in self.claim_template().splitlines():
            match = re.match(r"^([A-Za-z0-9_]+): ", line)
            if match and match.group(1) in expected_fields:
                lines.append(f"{match.group(1)}: {expected_fields[match.group(1)]}")
            else:
                lines.append(line)
        (self.root / claim_path).write_text("\n".join(lines) + "\n", encoding="utf-8")

    def base_branch_manifest(
        self,
        *,
        item_id: str,
        parent_branch: str,
        expected_base: str,
        request_id: str,
        claim_path: str,
    ) -> Dict[str, Any]:
        return {
            "schema": runner.MANIFEST_SCHEMA,
            "profile": runner.BRANCH_MERGE_PROFILE,
            "identity": {
                "task_id": item_id,
                "request_id": request_id,
                "owner_token": f"agent:test:{item_id}:{request_id}",
                "claim_path": claim_path,
                "manifest_path": f"branch-request-{request_id}.json",
                "expected_base": expected_base,
            },
            "authority": {
                "selector_path": "agent-workflow.json",
                "authority_epoch": AUTHORITY["authority_epoch"],
                "authority_profile": AUTHORITY["authority_profile"],
                "write_phase": AUTHORITY["write_phase"],
                "runner_protocol": AUTHORITY["runner_protocol"],
            },
            "scope": {"read_paths": [], "input_paths": [], "output_paths": [], "substantive_paths": []},
            "actions": [],
            "branch": {
                "typed_action": runner.TYPED_ACTION_BASE_BRANCH,
                "item_id": item_id,
                "target_branch": item_id,
                "capability_class": "unprivileged",
                "idempotence_key": f"base-branch:{item_id}:{expected_base[:12]}",
                "parent_branch": parent_branch,
                "sources": [],
            },
        }

    def merge_prereqs_manifest(
        self,
        *,
        item_id: str,
        expected_base: str,
        request_id: str,
        claim_path: str,
        sources: list,
        substantive_paths: list,
        capability_class: str = "unprivileged",
        target_branch: Optional[str] = None,
    ) -> Dict[str, Any]:
        suffix = "-".join(source["dependency"] for source in sources) or "none"
        return {
            "schema": runner.MANIFEST_SCHEMA,
            "profile": runner.BRANCH_MERGE_PROFILE,
            "identity": {
                "task_id": item_id,
                "request_id": request_id,
                "owner_token": f"agent:test:{item_id}:{request_id}",
                "claim_path": claim_path,
                "manifest_path": f"branch-request-{request_id}.json",
                "expected_base": expected_base,
            },
            "authority": {
                "selector_path": "agent-workflow.json",
                "authority_epoch": AUTHORITY["authority_epoch"],
                "authority_profile": AUTHORITY["authority_profile"],
                "write_phase": AUTHORITY["write_phase"],
                "runner_protocol": AUTHORITY["runner_protocol"],
            },
            "scope": {
                "read_paths": [],
                "input_paths": [],
                "output_paths": [],
                "substantive_paths": sorted(substantive_paths),
            },
            "actions": [],
            "branch": {
                "typed_action": runner.TYPED_ACTION_MERGE_PREREQS,
                "item_id": item_id,
                "target_branch": target_branch or item_id,
                "capability_class": capability_class,
                "idempotence_key": f"merge-prereqs:{item_id}:{suffix}",
                "sources": [
                    {"dependency": s["dependency"], "branch": s["branch"], "tip": s["tip"]} for s in sources
                ],
            },
        }

    def write_manifest(self, manifest: Dict[str, Any]) -> Path:
        path = self.root / manifest["identity"]["manifest_path"]
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return path

    def prepare(self, manifest: Dict[str, Any]) -> Path:
        """Write both the manifest and a matching claim file, return the manifest path.

        The claim's contract fields must match what ``load_manifest`` actually
        produces (e.g. it adds an explicit ``parent_branch: null`` to a
        normalized ``merge-prereqs`` branch block, which must never appear in
        the *written* manifest since its presence there is itself rejected).
        Load the manifest once here to compute the claim from the normalized
        shape, exactly as the real transaction's preflight will.
        """
        path = self.write_manifest(manifest)
        normalized = runner.load_manifest(path)
        self.write_claim(manifest["identity"]["claim_path"], normalized)
        return path


class BranchMergeTransactionTests(unittest.TestCase):
    _fixture: Optional[BranchMergeFixtureRepo] = None

    @property
    def fixture(self) -> BranchMergeFixtureRepo:
        assert self._fixture is not None
        return self._fixture

    def setUp(self) -> None:
        self._fixture = BranchMergeFixtureRepo()
        self.addCleanup(self.fixture.close)

    def _execute(self, manifest_path: Path, *, inject_failure: Optional[str] = None) -> tuple[int, str]:
        loaded = runner.load_manifest(manifest_path)
        transaction = runner.build_transaction(self.fixture.root, loaded, inject_failure=inject_failure)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = transaction.execute()
        return status, output.getvalue()

    def _result(self, task_id: str, request_id: str) -> Dict[str, Any]:
        path = self.fixture.root / "output" / "logs" / task_id / request_id / "result.json"
        return json.loads(path.read_text(encoding="utf-8"))

    # -- base-branch ------------------------------------------------------------

    def test_base_branch_off_parent(self) -> None:
        fixture = self.fixture
        self.assertEqual(fixture.current_branch(), "refs/heads/9000")
        expected_base = fixture.tip("9000")
        request_id = "bma-base-01"
        claim_path = f"TODO-agent-9000-01-{request_id}.md"
        manifest = fixture.base_branch_manifest(
            item_id="9000-01",
            parent_branch="9000",
            expected_base=expected_base,
            request_id=request_id,
            claim_path=claim_path,
        )
        path = fixture.prepare(manifest)
        status, output = self._execute(path)
        self.assertEqual(status, 0, output)
        self.assertEqual(fixture.tip("9000-01"), expected_base)
        # base-branch never moves HEAD off the checked-out parent branch.
        self.assertEqual(fixture.current_branch(), "refs/heads/9000")
        result = self._result("9000-01", request_id)
        self.assertEqual(result["verdict"], "passed")
        self.assertEqual(result["branch"]["typed_action"], "base-branch")
        self.assertIn(f"ref:refs/heads/9000-01@{expected_base}", result["branch"]["outputs"])

    def test_base_branch_rejects_stale_parent_tip(self) -> None:
        fixture = self.fixture
        real_base = fixture.tip("9000")
        stale_base = "a" * 40
        request_id = "bma-base-stale-01"
        claim_path = f"TODO-agent-9000-01-{request_id}.md"
        manifest = fixture.base_branch_manifest(
            item_id="9000-01",
            parent_branch="9000",
            expected_base=stale_base,
            request_id=request_id,
            claim_path=claim_path,
        )
        path = fixture.prepare(manifest)
        # expected_base is checked against HEAD before branch-specific logic
        # (the base Transaction requires HEAD == identity.expected_base), so a
        # stale value is rejected as a generic base mismatch, never published.
        status, output = self._execute(path)
        self.assertNotEqual(status, 0)
        self.assertFalse((fixture.root / "refs" / "heads" / "9000-01").exists())
        completed = fixture.git("rev-parse", "--verify", "--quiet", "refs/heads/9000-01", check=False)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(fixture.tip("9000"), real_base)

    # -- merge-prereqs: positive -------------------------------------------------

    def test_merge_prereqs_single_source(self) -> None:
        fixture = self.fixture
        fixture.git("checkout", "-b", "9000-01", "9000")
        expected_base = fixture.tip("9000-01")
        unrelated_before = fixture.sha256("unrelated.txt")
        request_id = "bma-merge-single-01"
        claim_path = f"TODO-agent-9000-01-{request_id}.md"
        manifest = fixture.merge_prereqs_manifest(
            item_id="9000-01",
            expected_base=expected_base,
            request_id=request_id,
            claim_path=claim_path,
            sources=[{"dependency": "9000-02", "branch": "9000-02", "tip": fixture.tip("9000-02")}],
            substantive_paths=["work-02.txt"],
        )
        path = fixture.prepare(manifest)
        status, output = self._execute(path)
        self.assertEqual(status, 0, output)
        self.assertEqual((fixture.root / "work-02.txt").read_text(encoding="utf-8"), "work-02\n")
        new_tip = fixture.tip("9000-01")
        self.assertNotEqual(new_tip, expected_base)
        parents = fixture.git_text("rev-list", "--parents", "-n", "1", new_tip).split()
        self.assertEqual(len(parents), 3)
        self.assertEqual(parents[1], expected_base)
        self.assertEqual(parents[2], fixture.tip("9000-02"))
        # Unrelated tracked bytes are preserved exactly.
        self.assertEqual(fixture.sha256("unrelated.txt"), unrelated_before)
        # The claim carries append-only merged-tip evidence.
        claim_text = (fixture.root / claim_path).read_text(encoding="utf-8")
        self.assertIn("Merged prerequisite branches", claim_text)
        self.assertIn(f"merge-commit {new_tip}", claim_text)
        result = self._result("9000-01", request_id)
        self.assertEqual(len(result["branch"]["merge_steps"]), 1)
        self.assertEqual(result["branch"]["final_branch_tip"], new_tip)


if __name__ == "__main__":
    unittest.main()
