import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "environment_doctor.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "environment_doctor"
SCHEMA_PATH = ROOT / "issues" / "_schema" / "prepared-environment-v1.schema.json"
SPEC = importlib.util.spec_from_file_location("environment_doctor", TOOL)
assert SPEC and SPEC.loader
doctor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = doctor
SPEC.loader.exec_module(doctor)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


DATA = load_json(FIXTURES / "cases.json")
CASES = {item["name"]: item for item in DATA["cases"]}


def merge(base, patch):
    result = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class Fixture:
    def __init__(self, case="ready"):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "docs/pipeline/agent-instructions/legacy").mkdir(parents=True)
        self.bootstrap = {
            "schema": "agent-workflow-bootstrap@v1", "workflow_version": "1.0.0",
            "authority_epoch": "legacy-writable", "authority_profile": "legacy-lists",
            "write_phase": "legacy-writable", "required_capability": "privileged",
            "runner_protocol": "runner-request@v1",
            "selector_digest": "sha256:" + "a" * 64,
            "instruction_bundle": "docs/pipeline/agent-instructions/legacy/index.md",
        }
        self.requirements = merge(DATA["requirements"], CASES[case].get("patch", {}).get("requirements", {}))
        self.profile = merge(DATA["profile"], CASES[case].get("patch", {}).get("profile", {}))
        self.observations = merge(DATA["observations"], CASES[case].get("patch", {}).get("observations", {}))
        self.bootstrap_path = self.root / "agent-workflow.json"
        self.requirements_path = self.root / "requirements.json"
        self.profile_path = self.root / "profile.json"
        self.instructions_path = self.root / self.bootstrap["instruction_bundle"]
        self.write_inputs()

    def write_inputs(self):
        self.bootstrap_path.write_text(json.dumps(self.bootstrap, separators=(",", ":")), encoding="utf-8")
        self.requirements_path.write_text(json.dumps(self.requirements, separators=(",", ":")), encoding="utf-8")
        self.profile_path.write_text(json.dumps(self.profile, separators=(",", ":")), encoding="utf-8")
        self.instructions_path.write_text("fixture instruction bundle\n", encoding="utf-8")

    def scan(self, **kwargs):
        kwargs.setdefault("now", 10000)
        return doctor.scan_environment(self.root, self.requirements_path, self.profile_path, observations=self.observations, **kwargs)

    def close(self):
        self.temporary.cleanup()


def simple_schema_validate(instance, schema, root=None, path="$" ):
    """Small stdlib validator for the schema vocabulary used by this fixture."""
    root = schema if root is None else root
    if "$ref" in schema:
        target = root
        for part in schema["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        return simple_schema_validate(instance, target, root, path)
    if "const" in schema:
        assert instance == schema["const"], path
    if "enum" in schema:
        assert instance in schema["enum"], path
    if "oneOf" in schema:
        matches = 0
        for branch in schema["oneOf"]:
            try:
                simple_schema_validate(instance, branch, root, path)
                matches += 1
            except AssertionError:
                pass
        assert matches == 1, path
    kind = schema.get("type")
    if kind == "object":
        assert isinstance(instance, dict), path
        for required in schema.get("required", []):
            assert required in instance, path + "." + required
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                simple_schema_validate(value, properties[key], root, path + "." + key)
            elif isinstance(additional, dict):
                simple_schema_validate(value, additional, root, path + "." + key)
            else:
                assert additional is True, path + "." + key
    elif kind == "array":
        assert isinstance(instance, list), path
        assert len(instance) >= schema.get("minItems", 0), path
        assert len(instance) <= schema.get("maxItems", 10**9), path
        for index, value in enumerate(instance):
            simple_schema_validate(value, schema.get("items", {}), root, f"{path}[{index}]")
    elif kind == "string":
        assert isinstance(instance, str), path
        if "maxLength" in schema:
            assert len(instance) <= schema["maxLength"], path
        if "pattern" in schema:
            import re
            assert re.search(schema["pattern"], instance), path
    elif kind == "integer":
        assert isinstance(instance, int) and not isinstance(instance, bool), path
        assert instance >= schema.get("minimum", instance), path
    elif kind == "boolean":
        assert isinstance(instance, bool), path
    elif kind == "null":
        assert instance is None, path
    for branch in schema.get("allOf", []):
        condition = branch.get("if")
        applies = True
        if condition:
            try:
                simple_schema_validate(instance, condition, root, path)
            except AssertionError:
                applies = False
        if applies and "then" in branch:
            simple_schema_validate(instance, branch["then"], root, path)


class EnvironmentDoctorFixtureTests(unittest.TestCase):
    def test_manifest_and_case_names(self):
        manifest = load_json(FIXTURES / "manifest.json")
        self.assertEqual(manifest["schema"], "environment-doctor-fixture-manifest@v1")
        self.assertEqual(set(manifest["cases"]), set(CASES))
        self.assertEqual(DATA["schema"], "environment-doctor-fixtures@v1")

    def test_all_status_fixtures_and_fixed_first_gate(self):
        for name, case in sorted(CASES.items()):
            with self.subTest(case=name):
                fixture = Fixture(name)
                self.addCleanup(fixture.close)
                report = fixture.scan()
                self.assertEqual(report["aggregate"], case["aggregate"])
                observed = report["first_actionable"]["id"] if report["first_actionable"] else None
                self.assertEqual(observed, case["first"])
                self.assertEqual(report["exit_code"], {"PREPARED": 0, "BLOCKED": 1, "INCOMPLETE": 2}[case["aggregate"]])

    def test_ready_report_validates_schema_manually(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        report = fixture.scan()
        schema = doctor.strict_json_bytes(SCHEMA_PATH.read_bytes(), "schema")
        simple_schema_validate(report, schema)

    def test_status_vocabulary_is_complete(self):
        schema = load_json(SCHEMA_PATH)
        self.assertEqual(set(schema["$defs"]["status"]["enum"]), set(doctor.STATUSES))

    def test_summary_is_deterministic_and_at_most_ten_lines(self):
        fixture = Fixture("missing-tool")
        self.addCleanup(fixture.close)
        first, second = fixture.scan(), fixture.scan()
        self.assertEqual(doctor.canonical_json(first), doctor.canonical_json(second))
        self.assertLessEqual(len(first["summary"]), 10)
        self.assertTrue(all("\n" not in line for line in first["summary"]))

    def test_order_is_independent_of_observation_member_order(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        first = fixture.scan()
        fixture.observations = dict(reversed(list(fixture.observations.items())))
        second = fixture.scan()
        self.assertEqual(first["environment_id"], second["environment_id"])
        self.assertEqual([gate["id"] for gate in first["gates"]], list(doctor.GATE_ORDER))


class EnvironmentDoctorFingerprintTests(unittest.TestCase):
    def test_each_identity_change_changes_fingerprint(self):
        mutations = (
            ("path", lambda f: f.observations["platform"].update(path_entries=["/different/bin"])),
            ("version", lambda f: f.observations["tools"][0].update(version="git 9")),
            ("font", lambda f: f.observations["fonts"][0].update(identity="font-digest-2")),
            ("browser", lambda f: f.observations["browser"].update(identity="webkit-2")),
            ("profile", lambda f: f.profile.update(minimum_cpu=3)),
            ("bootstrap", lambda f: f.bootstrap.update(workflow_version="1.0.1")),
            ("cross-bind", lambda f: f.profile.update(write_phase="legacy-frozen")),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                fixture = Fixture()
                self.addCleanup(fixture.close)
                before = fixture.scan()["environment_id"]
                mutate(fixture)
                fixture.write_inputs()
                after = fixture.scan()["environment_id"]
                self.assertNotEqual(before, after)

    def test_volatile_fields_do_not_change_fingerprint(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        fixture.observations["resources"].update(pid=1, duration_ms=4, disk_free_mb=4096)
        first = fixture.scan()["environment_id"]
        fixture.observations["resources"].update(pid=999, duration_ms=999, disk_free_mb=999999)
        second = fixture.scan()["environment_id"]
        self.assertEqual(first, second)

    def test_paths_are_aliased_and_private_root_never_appears(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        fixture.observations["tools"][0]["path"] = str(fixture.root / "Users/alice/private/git")
        rendered = doctor.canonical_json(fixture.scan())
        self.assertNotIn(str(fixture.root), rendered)
        self.assertNotIn("alice/private", rendered)
        self.assertIn('"class":"repository"', rendered)


class EnvironmentDoctorPrivacyAndInputTests(unittest.TestCase):
    def test_duplicate_keys_are_rejected(self):
        with self.assertRaises(doctor.ContractError):
            doctor.strict_json_bytes(b'{"schema":"x","schema":"y"}', "duplicate")

    def test_secret_fields_values_pem_bearer_and_userinfo_are_rejected_before_hash(self):
        bad = [
            {"password": "x"},
            {"note": "-----BEGIN PRIVATE KEY-----"},
            {"note": "Bearer abcdefghijklmnop"},
            {"note": "https://user:pass@example.invalid/path"},
            {"note": "ghp_abcdefghijklmnopqrstuvwxyz"},
        ]
        for value in bad:
            with self.subTest(value=value):
                with self.assertRaises(doctor.ContractError):
                    doctor._privacy_check(value)

    def test_secret_observation_fails_closed_without_digesting_it(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        fixture.observations["credential"]["auth_token"] = "ghp_abcdefghijklmnopqrstuvwxyz"
        with mock.patch.object(doctor, "_fingerprint_payload", side_effect=AssertionError("must not hash")):
            with self.assertRaises(doctor.ContractError):
                fixture.scan()

    def test_unknown_contract_members_are_rejected(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        fixture.observations["environment_dump"] = {}
        with self.assertRaises(doctor.ContractError):
            fixture.scan()

    def test_malformed_inputs_return_canonical_error_json(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        fixture.profile_path.write_text("{\"schema\":\"environment-doctor-profile@v1\",\"minimum_cpu\":{}}", encoding="utf-8")
        with mock.patch.object(sys, "argv", ["environment_doctor.py"]):
            with mock.patch.object(sys, "stdout") as stdout, mock.patch.object(sys, "stderr"):
                stdout.write = mock.Mock()
                exit_code = doctor.main(["--root", str(fixture.root), "--requirements", str(fixture.requirements_path), "--profile", str(fixture.profile_path)])
        self.assertEqual(exit_code, 2)

    def test_symlink_and_nonregular_inputs_are_rejected(self):
        for kind in ("symlink", "directory"):
            with self.subTest(kind=kind):
                fixture = Fixture()
                self.addCleanup(fixture.close)
                fixture.requirements_path.unlink()
                if kind == "symlink":
                    fixture.requirements_path.symlink_to(fixture.profile_path)
                else:
                    fixture.requirements_path.mkdir()
                with self.assertRaises(doctor.ContractError):
                    fixture.scan()

    def test_input_change_during_scan_fails_closed(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        def mutate():
            fixture.profile["minimum_cpu"] = 99
            fixture.profile_path.write_text(json.dumps(fixture.profile), encoding="utf-8")
        with self.assertRaisesRegex(doctor.ContractError, "changed during scan"):
            fixture.scan(verify_hook=mutate)


class EnvironmentDoctorCacheTests(unittest.TestCase):
    def test_cold_write_and_warm_reuse_mutate_only_one_member(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        cache = fixture.root / "cache"
        cache.mkdir()
        before = sorted(cache.iterdir())
        cold = fixture.scan(cache_root=cache, write_cache=True)
        after = sorted(cache.iterdir())
        self.assertEqual(before, [])
        self.assertEqual(len(after), 1)
        self.assertEqual(after[0].name, cold["environment_id"].removeprefix("sha256:") + ".json")
        warm = fixture.scan(cache_root=cache)
        self.assertTrue(warm["cache"]["reused"])
        self.assertEqual(warm["environment_id"], cold["environment_id"])
        self.assertEqual(sorted(cache.iterdir()), after)

    def test_negative_cache_reuse_preserves_blocked_result(self):
        fixture = Fixture("missing-tool")
        self.addCleanup(fixture.close)
        cache = fixture.root / "cache"
        cache.mkdir()
        cold = fixture.scan(cache_root=cache, write_cache=True)
        warm = fixture.scan(cache_root=cache)
        self.assertEqual((cold["aggregate"], warm["aggregate"]), ("BLOCKED", "BLOCKED"))
        self.assertTrue(warm["cache"]["reused"])

    def test_tamper_partial_and_stale_cache_are_not_reused(self):
        for mode in ("tamper", "partial", "stale"):
            with self.subTest(mode=mode):
                fixture = Fixture()
                self.addCleanup(fixture.close)
                cache = fixture.root / "cache"
                cache.mkdir()
                report = fixture.scan(cache_root=cache, write_cache=True)
                member = cache / (report["environment_id"].removeprefix("sha256:") + ".json")
                if mode == "partial":
                    member.write_text("{", encoding="utf-8")
                else:
                    envelope = json.loads(member.read_text(encoding="utf-8"))
                    if mode == "tamper":
                        # Keep the forged member internally self-consistent,
                        # but make it disagree with freshly reconstructed truth.
                        envelope["report"]["observations"]["platform"]["machine"] = "forged-machine"
                        envelope["report"]["summary"] = list(doctor.render_summary(envelope["report"]))
                        envelope["report"]["content_digest"] = doctor._report_digest(envelope["report"])
                        envelope["report_digest"] = doctor._report_digest(envelope["report"])
                    else:
                        envelope["created_at"] = 0
                    member.write_text(json.dumps(envelope), encoding="utf-8")
                observed = fixture.scan(cache_root=cache, now=20000 if mode == "stale" else 10000)
                self.assertFalse(observed["cache"]["reused"])
                self.assertEqual(observed["cache"]["status"], "ERROR" if mode != "stale" else "STALE")

    def test_forged_cache_cannot_overrule_fresh_result(self):
        fixture = Fixture("missing-tool")
        self.addCleanup(fixture.close)
        cache = fixture.root / "cache"
        cache.mkdir()
        cold = fixture.scan(cache_root=cache, write_cache=True)
        member = cache / (cold["environment_id"].removeprefix("sha256:") + ".json")
        envelope = json.loads(member.read_text(encoding="utf-8"))
        envelope["report"]["aggregate"] = "PREPARED"
        envelope["report"]["exit_code"] = 0
        envelope["report"]["first_actionable"] = None
        envelope["report"]["counts"]["blocking"] = 0
        envelope["report"]["summary"] = list(doctor.render_summary(envelope["report"]))
        envelope["report"]["content_digest"] = doctor._report_digest(envelope["report"])
        envelope["report_digest"] = doctor._report_digest(envelope["report"])
        member.write_text(json.dumps(envelope), encoding="utf-8")
        warm = fixture.scan(cache_root=cache)
        self.assertEqual(warm["aggregate"], "BLOCKED")
        self.assertFalse(warm["cache"]["reused"])
        self.assertEqual(warm["cache"]["status"], "ERROR")

    def test_changed_inputs_select_a_different_member_not_mutable_current(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        cache = fixture.root / "cache"
        cache.mkdir()
        first = fixture.scan(cache_root=cache, write_cache=True)
        fixture.profile["minimum_cpu"] = 3
        fixture.write_inputs()
        second = fixture.scan(cache_root=cache, write_cache=True)
        self.assertNotEqual(first["environment_id"], second["environment_id"])
        self.assertEqual(len(list(cache.iterdir())), 2)
        self.assertFalse((cache / "current.json").exists())

    def test_missing_or_global_cache_root_is_never_created_or_repaired(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        missing = fixture.root / "missing-cache"
        report = fixture.scan(cache_root=missing, write_cache=True)
        self.assertFalse(missing.exists())
        self.assertEqual(report["cache"]["status"], "FORBIDDEN")
        with mock.patch.object(doctor, "_cache_root_safe", return_value=False):
            report = fixture.scan(cache_root=Path("/root/.cache"), write_cache=True)
        self.assertEqual(report["cache"]["status"], "FORBIDDEN")
        self.assertEqual(report["first_actionable"]["id"], "cache_write")

    def test_eperm_write_cleans_partial_file(self):
        fixture = Fixture()
        self.addCleanup(fixture.close)
        cache = fixture.root / "cache"
        cache.mkdir()
        with mock.patch.object(doctor.os, "replace", side_effect=PermissionError("EPERM")):
            report = fixture.scan(cache_root=cache, write_cache=True)
        self.assertEqual(report["cache"]["status"], "UNAVAILABLE")
        self.assertEqual(list(cache.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
