from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src/tools/agent_bootstrap.py"
FIXTURES = ROOT / "issues/_schema/fixtures/agent-workflow-bootstrap-v2"
SPEC = importlib.util.spec_from_file_location("agent_bootstrap", TOOL)
assert SPEC and SPEC.loader
BOOTSTRAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOOTSTRAP)


class AgentBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        (self.repo / "_src/tools").mkdir(parents=True)
        shutil.copy2(TOOL, self.repo / "_src/tools/agent_bootstrap.py")
        self._install_bundle("legacy")
        self._install_bundle("future")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _install_bundle(self, profile: str) -> None:
        source = ROOT / f"docs/pipeline/agent-instructions/{profile}/index.md"
        target = self.repo / f"docs/pipeline/agent-instructions/{profile}/index.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    def _fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def _write(self, selector: dict, *, repair_digest: bool = True) -> dict:
        value = copy.deepcopy(selector)
        if repair_digest:
            value["selector_digest"] = BOOTSTRAP.selector_digest(value)
        (self.repo / "agent-workflow.json").write_text(
            json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8"
        )
        return value

    def _doctor(self, selector: dict, *, repair_digest: bool = True, epoch=None, profile=None, version=None):
        value = self._write(selector, repair_digest=repair_digest)
        return BOOTSTRAP.doctor(
            self.repo, epoch or value.get("authority_epoch", "legacy-writable"),
            profile or value.get("authority_profile", "legacy-lists"),
            version or value.get("workflow_version", "2.0.0"),
        )

    def _ids(self, result):
        return [item["id"] for item in result["diagnostics"]]

    def test_valid_v2_legacy_and_issue_store_profiles(self):
        for name in ("valid/legacy-lists.json", "valid/issue-store.json"):
            with self.subTest(name=name):
                result = self._doctor(self._fixture(name), repair_digest=False)
                self.assertEqual("ready", result["status"])
                self.assertEqual([], result["diagnostics"])
                self.assertEqual("ready", result["direct_capability"]["status"])

    def test_v2_fixtures_have_canonical_digest_and_manifest_is_complete(self):
        manifest = self._fixture("manifest.json")
        for relative in manifest["valid"] + manifest["invalid"]:
            self.assertTrue((FIXTURES / relative).is_file(), relative)
        for relative in manifest["valid"]:
            value = self._fixture(relative)
            self.assertEqual(value["selector_digest"], BOOTSTRAP.selector_digest(value))

    def test_legacy_v1_is_readable_but_not_direct_ready(self):
        selector = json.loads((ROOT / "issues/_schema/fixtures/agent-workflow-bootstrap-v1/valid/legacy.json").read_text())
        result = self._doctor(selector, repair_digest=False, version="1.0.0")
        self.assertEqual("agent-workflow-bootstrap@v1", result["selector"]["schema"])
        self.assertIn("AB021_LEGACY_TRANSPORT", self._ids(result))
        self.assertEqual("legacy-runner", result["direct_capability"]["execution_model"])

    def test_missing_corrupt_and_non_object_selector(self):
        missing = BOOTSTRAP.doctor(self.repo, "legacy-writable", "legacy-lists", "2.0.0")
        self.assertIn("AB001_SELECTOR_MISSING", self._ids(missing))
        (self.repo / "agent-workflow.json").write_text("{", encoding="utf-8")
        self.assertIn("AB002_SELECTOR_JSON", self._ids(BOOTSTRAP.doctor(self.repo, "e", "p", "v")))
        (self.repo / "agent-workflow.json").write_text("[]", encoding="utf-8")
        self.assertIn("AB003_SELECTOR_SHAPE", self._ids(BOOTSTRAP.doctor(self.repo, "e", "p", "v")))

    def test_unknown_and_missing_fields_are_rejected(self):
        selector = self._fixture("valid/legacy-lists.json")
        selector["operational_role"] = "Runner"
        del selector["execution_model"]
        result = self._doctor(selector)
        self.assertIn("AB005_UNKNOWN_FIELD", self._ids(result))
        self.assertIn("AB006_MISSING_FIELD", self._ids(result))

    def test_unsupported_schema_version_execution_and_capability(self):
        selector = self._fixture("valid/legacy-lists.json")
        selector["schema"] = "agent-workflow-bootstrap@v3"
        self.assertIn("AB004_SCHEMA_UNSUPPORTED", self._ids(self._doctor(selector)))
        selector = self._fixture("valid/legacy-lists.json")
        selector["workflow_version"] = "two"
        selector["execution_model"] = "queue"
        selector["required_capability"] = "runner"
        ids = self._ids(self._doctor(selector, version="two"))
        self.assertIn("AB007_WORKFLOW_VERSION", ids)
        self.assertIn("AB009_EXECUTION_MODEL", ids)
        self.assertIn("AB010_CAPABILITY", ids)

    def test_placeholder_self_digest_and_digest_mismatch_are_rejected(self):
        selector = self._fixture("invalid/placeholder-digest.json")
        ids = self._ids(self._doctor(selector, repair_digest=False))
        self.assertIn("AB012_DIGEST_PLACEHOLDER", ids)
        self.assertIn("AB013_DIGEST_MISMATCH", ids)
        selector = self._fixture("valid/legacy-lists.json")
        selector["authority_epoch"] = "legacy-frozen"
        result = self._doctor(selector, repair_digest=False, epoch="legacy-frozen")
        self.assertIn("AB013_DIGEST_MISMATCH", self._ids(result))

    def test_contradictory_policy_is_rejected(self):
        result = self._doctor(self._fixture("invalid/contradictory-policy.json"))
        self.assertIn("AB008_AUTHORITY_CONTRADICTION", self._ids(result))

    def test_expected_identity_mismatches_are_ordered_and_stable(self):
        selector = self._fixture("valid/legacy-lists.json")
        result = self._doctor(selector, epoch="issue-store-writable", profile="issue-store", version="9.0.0")
        ids = self._ids(result)
        self.assertEqual(["AB017_EXPECTED_EPOCH", "AB018_EXPECTED_PROFILE", "AB019_EXPECTED_VERSION"], ids)

    def test_instruction_member_drift_and_missing_bundle(self):
        selector = self._fixture("valid/legacy-lists.json")
        path = self.repo / "docs/pipeline/agent-instructions/legacy/index.md"
        path.write_text(path.read_text() + "drift\n", encoding="utf-8")
        self.assertIn("AB022_BUNDLE_MEMBER_DRIFT", self._ids(self._doctor(selector)))
        path.unlink()
        self.assertIn("AB015_BUNDLE_MISSING", self._ids(self._doctor(selector)))

    def test_linked_instruction_members_are_digest_bound(self):
        path = self.repo / "docs/pipeline/agent-instructions/legacy/index.md"
        member = path.parent / "rules.md"
        member.write_text("rules\n", encoding="utf-8")
        path.write_text("[rules](rules.md)\n", encoding="utf-8")
        selector = self._fixture("valid/legacy-lists.json")
        selector["instruction_bundle"]["members"] = {
            "docs/pipeline/agent-instructions/legacy/index.md": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
            "docs/pipeline/agent-instructions/legacy/rules.md": "sha256:" + hashlib.sha256(member.read_bytes()).hexdigest(),
        }
        result = self._doctor(selector)
        self.assertEqual("ready", result["status"])
        member.write_text("changed\n", encoding="utf-8")
        self.assertIn("AB022_BUNDLE_MEMBER_DRIFT", self._ids(self._doctor(selector)))

    def test_rebootstrap_command_absence_is_rejected(self):
        (self.repo / "_src/tools/agent_bootstrap.py").unlink()
        result = self._doctor(self._fixture("valid/legacy-lists.json"))
        self.assertIn("AB020_REBOOTSTRAP_COMMAND_MISSING", self._ids(result))

    def test_exact_literal_rebootstrap_argv(self):
        result = self._doctor(self._fixture("valid/legacy-lists.json"))
        self.assertEqual([
            "python3", "_src/tools/agent_bootstrap.py", "doctor", "--repo", str(self.repo),
            "--expected-epoch", "legacy-writable", "--expected-profile", "legacy-lists",
            "--expected-workflow-version", "2.0.0", "--json",
        ], result["rebootstrap_argv"])

    def test_repeated_api_output_is_byte_identical(self):
        selector = self._fixture("valid/legacy-lists.json")
        first = self._doctor(selector)
        second = BOOTSTRAP.doctor(self.repo, "legacy-writable", "legacy-lists", "2.0.0")
        encode = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(encode(first), encode(second))

    def test_cli_ready_invalid_and_usage_exit_codes(self):
        selector = self._fixture("valid/legacy-lists.json")
        self._write(selector)
        argv = ["python3", str(TOOL), "doctor", "--repo", str(self.repo),
                "--expected-epoch", "legacy-writable", "--expected-profile", "legacy-lists",
                "--expected-workflow-version", "2.0.0", "--json"]
        ready = subprocess.run(argv, text=True, capture_output=True, check=False)
        self.assertEqual(0, ready.returncode, ready.stderr)
        self.assertEqual("agent-bootstrap-doctor@v1", json.loads(ready.stdout)["schema"])
        stale_argv = list(argv)
        stale_argv[stale_argv.index("--expected-profile") + 1] = "issue-store"
        stale = subprocess.run(stale_argv, text=True, capture_output=True, check=False)
        self.assertEqual(2, stale.returncode)
        usage = subprocess.run(["python3", str(TOOL), "doctor"], text=True, capture_output=True, check=False)
        self.assertEqual(3, usage.returncode)

    def test_doctor_has_no_repository_mutation(self):
        selector = self._fixture("valid/legacy-lists.json")
        self._write(selector)
        before = {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        BOOTSTRAP.doctor(self.repo, "legacy-writable", "legacy-lists", "2.0.0")
        after = {p.relative_to(self.repo).as_posix(): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_schema_declares_closed_v2_direct_contract(self):
        schema = json.loads((ROOT / "issues/_schema/agent-workflow-bootstrap-v2.schema.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual("direct", schema["properties"]["execution_model"]["const"])
        self.assertEqual(["unprivileged", "privileged"], schema["properties"]["required_capability"]["enum"])
        self.assertTrue(schema["properties"]["instruction_bundle"]["properties"]["members"]["minProperties"])


if __name__ == "__main__":
    unittest.main()
