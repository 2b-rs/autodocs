import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "task_validation.py"
SCHEMA = ROOT / "issues" / "_schema" / "task-validation-profile-v1.schema.json"
SPEC = importlib.util.spec_from_file_location("task_validation", TOOL)
assert SPEC and SPEC.loader
validation = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validation
SPEC.loader.exec_module(validation)


class TaskValidationTests(unittest.TestCase):
    def profile(self, *, baseline_allowed=False):
        return {
            "schema": validation.PROFILE_SCHEMA,
            "profile_id": "four-url-v1",
            "required_stages": [{"id": "probe", "inputs": ["urls.json"], "outputs": ["probe-report.json"], "canary_id": "probe-ran"}],
            "freshness": {"fields": ["base_commit", "environment_id"], "expected": {"base_commit": "abc", "environment_id": "env-1"}, "max_age_seconds": 3600},
            "canaries": [{"id": "probe-ran", "stage": "probe"}],
            "limits": {"max_duration_ms": 5000},
            "baseline_allowed": baseline_allowed,
            "allowed_mutations": [],
        }

    def make_run(self, **changes):
        stage = {"id": "probe", "status": "PASS", "exit_code": 0, "inputs": ["urls.json"], "outputs": ["probe-report.json"], "findings": [], "coverage": {"checks_run": 4, "canaries": ["probe-ran"]}, "duration_ms": 20}
        result = {"schema": validation.RUN_SCHEMA, "run_id": "run-1", "freshness": {"base_commit": "abc", "environment_id": "env-1"}, "stages": [stage], "baseline_only": False, "deterministic": True, "mutations": [], "metadata": {}, "mixed_inputs": False, "stale": False}
        result.update(changes)
        return result

    def test_four_url_probe_passes_and_is_digest_bound(self):
        report = validation.evaluate(validation._validate_profile(self.profile()), validation._validate_run(self.make_run()))
        self.assertEqual(report["aggregate"], "PASS")
        self.assertEqual(report["exit_code"], 0)
        self.assertTrue(report["report_digest"].startswith("sha256:"))
        self.assertEqual(validation.canonical_json(report), validation.canonical_json(validation.evaluate(validation._validate_profile(self.profile()), validation._validate_run(self.make_run()))))

    def test_baseline_only_determinism_can_pass_when_profile_allows_it(self):
        report = validation.evaluate(validation._validate_profile(self.profile(baseline_allowed=True)), validation._validate_run(self.make_run(baseline_only=True)))
        self.assertEqual(report["aggregate"], "PASS")

    def test_baseline_only_run_fails_without_explicit_profile_permission(self):
        report = validation.evaluate(validation._validate_profile(self.profile()), validation._validate_run(self.make_run(baseline_only=True)))
        self.assertEqual(report["aggregate"], "FAIL")
        self.assertIn("baseline-only", {finding["code"] for finding in report["findings"]})

    def test_mixed_and_stale_runs_are_not_green(self):
        report = validation.evaluate(validation._validate_profile(self.profile()), validation._validate_run(self.make_run(mixed_inputs=True, stale=True)))
        self.assertEqual(report["aggregate"], "FAIL")
        self.assertEqual({"mixed-run", "stale-run"} & {finding["code"] for finding in report["findings"]}, {"mixed-run", "stale-run"})

    def test_missing_stage_is_inconclusive_even_with_zero_exit(self):
        run = self.make_run(stages=[])
        report = validation.evaluate(validation._validate_profile(self.profile()), validation._validate_run(run))
        self.assertEqual(report["aggregate"], "FAIL")
        self.assertIn("missing-stage", {finding["code"] for finding in report["findings"]})

    def test_zero_coverage_and_missing_canary_fail(self):
        run = self.make_run()
        run["stages"][0]["coverage"] = {"checks_run": 0, "canaries": []}
        report = validation.evaluate(validation._validate_profile(self.profile()), validation._validate_run(run))
        codes = {finding["code"] for finding in report["findings"]}
        self.assertEqual(report["aggregate"], "FAIL")
        self.assertTrue({"zero-coverage", "missing-canary"}.issubset(codes))

    def test_structured_error_finding_fails_even_on_zero_exit(self):
        run = self.make_run()
        run["stages"][0]["findings"] = [{"severity": "error", "message": "detector failed"}]
        report = validation.evaluate(validation._validate_profile(self.profile()), validation._validate_run(run))
        self.assertEqual(report["aggregate"], "FAIL")
        self.assertIn("stage-finding", {finding["code"] for finding in report["findings"]})

    def test_freshness_mismatch_is_inconclusive(self):
        run = self.make_run()
        run["freshness"]["environment_id"] = "env-old"
        report = validation.evaluate(validation._validate_profile(self.profile()), validation._validate_run(run))
        self.assertEqual(report["aggregate"], "FAIL")
        self.assertIn("freshness-mismatch", {finding["code"] for finding in report["findings"]})

    def test_malformed_cli_input_returns_canonical_json(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / "profile.json"
            run = Path(directory) / "run.json"
            profile.write_text("{", encoding="utf-8")
            run.write_text("{}", encoding="utf-8")
            self.assertEqual(validation.main(["--profile", str(profile), "--run", str(run)]), 2)

    def test_profile_schema_has_closed_contract(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema"]["const"], validation.PROFILE_SCHEMA)
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
